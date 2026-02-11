"""Historical trade downloader via HTTP RPC."""

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional

import requests

from src.constants import (
    POLYGON_WSS_URL,
    RPC_MAX_RETRIES,
    RPC_RETRY_DELAY_SECONDS,
    RPC_TIMEOUT_SECONDS,
)
from src.core.decoder import TransactionDecoder
from src.core.models import TradeData
from src.utils.logging import get_logger

log = get_logger(__name__)


class TradeDownloader:
    """Downloads historical trades via HTTP RPC with concurrent requests."""

    def __init__(self, max_rps: int = 50) -> None:
        """Initialize downloader.

        Args:
            max_rps: Maximum concurrent RPC workers (default 50)
        """
        # Convert WSS URL to HTTPS for RPC
        self.http_url = POLYGON_WSS_URL.replace("wss://", "https://").rstrip("/")
        self.decoder = TransactionDecoder()
        self._session = requests.Session()
        self._request_id = 0
        self._max_rps = max_rps

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _rpc_call(self, method: str, params: list) -> dict:
        """Make HTTP RPC call with retries.

        Retries up to RPC_MAX_RETRIES times with exponential backoff.
        Raises on final failure to abort the download.
        """
        last_error: Optional[Exception] = None

        for attempt in range(1, RPC_MAX_RETRIES + 1):
            payload = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": method,
                "params": params,
            }
            try:
                resp = self._session.post(
                    self.http_url,
                    json=payload,
                    timeout=RPC_TIMEOUT_SECONDS,
                )

                if resp.status_code == 429:
                    raise Exception("Rate limited (HTTP 429)")

                if resp.status_code != 200:
                    raise Exception(f"HTTP {resp.status_code}: {resp.reason}")

                result = resp.json()

                if "error" in result:
                    error = result["error"]
                    message = (
                        error.get("message")
                        if isinstance(error, dict)
                        else str(error)
                    )
                    raise Exception(f"RPC error: {message}")

                return result["result"]

            except Exception as e:
                last_error = e
                if attempt < RPC_MAX_RETRIES:
                    log.warning(
                        "RPC call failed, retrying",
                        method=method,
                        attempt=f"{attempt}/{RPC_MAX_RETRIES}",
                        error=str(e) or type(e).__name__,
                    )
                    time.sleep(RPC_RETRY_DELAY_SECONDS * (2 ** (attempt - 1)))

        log.error(
            "RPC call failed after all retries",
            method=method,
            attempts=RPC_MAX_RETRIES,
            error=str(last_error) or type(last_error).__name__,
        )
        raise last_error  # type: ignore[misc]

    def _fetch_block(self, block_number: int) -> tuple[dict, list[dict]]:
        """Fetch block and receipts sequentially."""
        hex_block = hex(block_number)
        block = self._rpc_call("eth_getBlockByNumber", [hex_block, True])
        receipts = self._rpc_call("eth_getBlockReceipts", [hex_block])
        return block, receipts or []

    def _process_block(
        self,
        block_number: int,
    ) -> tuple[list[TradeData], int]:
        """Fetch and process a single block.

        Returns:
            Tuple of (trades found, transaction count in block)
        """
        block, receipts = self._fetch_block(block_number)
        receipt_map = {r["transactionHash"]: r for r in receipts}
        transactions = block["transactions"]

        trades = []
        for tx in transactions:
            orders = self.decoder.decode(tx.get("input", ""))
            if not orders:
                continue

            receipt = receipt_map.get(tx["hash"])
            if not receipt or receipt.get("status") != "0x1":
                continue

            order = orders[0]
            trades.append(TradeData(
                block_number=block_number,
                transaction_hash=tx["hash"],
                wallet=order.maker,
                token_id=order.token_id,
                side=order.side,
                maker_amount=order.maker_amount,
                taker_amount=order.taker_amount,
            ))
        return trades, len(transactions)

    def download(
        self,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
        max_blocks: int = 1000,
        on_trades: Optional[Callable[[list[TradeData]], None]] = None,
    ) -> None:
        """Download trades from historical blocks using thread pool concurrency.

        Processes blocks in batches for bounded memory and guaranteed ascending
        block order. Within each batch, blocks are fetched concurrently via a
        thread pool, then trades are sorted and delivered via callback.

        Args:
            start_block: Starting block (default: current - max_blocks)
            end_block: Ending block (default: current block)
            max_blocks: Maximum blocks to scan
            on_trades: Callback receiving trades per batch in ascending block order
        """
        if end_block is None:
            result = self._rpc_call("eth_blockNumber", [])
            end_block = int(result, 16)

        if start_block is None:
            start_block = max(0, end_block - max_blocks)

        all_blocks = list(range(start_block, end_block + 1))
        total_blocks = len(all_blocks)
        batch_size = self._max_rps * 2

        log.info(
            "Downloading trades",
            start_block=start_block,
            end_block=end_block,
            total_blocks=total_blocks,
            batch_size=batch_size,
            max_rps=self._max_rps,
        )

        start_time = time.monotonic()
        total_txs = 0
        total_trades = 0
        completed = 0

        with ThreadPoolExecutor(max_workers=self._max_rps) as executor:
            for i in range(0, total_blocks, batch_size):
                batch = all_blocks[i : i + batch_size]
                futures = [
                    executor.submit(self._process_block, b) for b in batch
                ]

                batch_trades: list[TradeData] = []
                for future in futures:
                    trades, tx_count = future.result()
                    batch_trades.extend(trades)
                    total_txs += tx_count

                completed += len(batch)

                if batch_trades:
                    total_trades += len(batch_trades)
                    if on_trades:
                        on_trades(batch_trades)

                elapsed = time.monotonic() - start_time
                bps = completed / elapsed if elapsed > 0 else 0
                rps = bps * 2
                log.info(
                    "Progress",
                    blocks=f"{completed}/{total_blocks}",
                    trades_found=total_trades,
                    trades_saved=len(batch_trades),
                    bps=f"{bps:.1f}",
                    rps=f"{rps:.0f}",
                )

        elapsed = time.monotonic() - start_time
        bps = total_blocks / elapsed if elapsed > 0 else 0
        rps = bps * 2
        log.info(
            "Download complete",
            total_trades=total_trades,
            total_txs=total_txs,
            elapsed=f"{elapsed:.1f}s",
            bps=f"{bps:.1f}",
            rps=f"{rps:.0f}",
        )

    def close(self) -> None:
        """Clean up HTTP session."""
        self._session.close()
