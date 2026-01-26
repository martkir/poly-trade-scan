"""Polygon blockchain client."""
import asyncio
import json
import ssl
from typing import Any, Awaitable, Callable, Optional

import aiohttp
import websockets

from src.constants import POLYGON_WSS_URL
from src.utils.logging import get_logger

log = get_logger(__name__)


class PolygonClient:
    """Manages WebSocket connection to Polygon blockchain via JSON-RPC."""

    RECONNECT_DELAY_SECONDS = 5
    RPC_RETRY_DELAY_SECONDS = 1

    def __init__(self, wss_url: str = POLYGON_WSS_URL) -> None:
        self.wss_url = wss_url
        self.http_url = wss_url.replace("wss://", "https://").rstrip("/")
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._request_id = 0

    def _next_id(self) -> int:
        """Generate next JSON-RPC request ID."""
        self._request_id += 1
        return self._request_id

    async def connect(self) -> None:
        """Establish WebSocket connection."""
        log.info("Connecting to WebSocket", url=self.wss_url[:50] + "...")
        try:
            # Create SSL context for compatibility
            ssl_context = ssl.create_default_context()

            self._ws = await websockets.connect(
                self.wss_url,
                ping_interval=30,
                ping_timeout=10,
                ssl=ssl_context,
            )
            log.info("WebSocket connected")
        except Exception as e:
            log.error("WebSocket connection failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Close WebSocket and HTTP connections."""
        if self._ws:
            await self._ws.close()
            self._ws = None
        if self._http_session:
            await self._http_session.close()
            self._http_session = None

    async def _get_http_session(self) -> aiohttp.ClientSession:
        """Get or create reusable HTTP session."""
        if self._http_session is None or self._http_session.closed:
            self._http_session = aiohttp.ClientSession()
        return self._http_session

    async def _rpc_call(self, method: str, params: list | None = None) -> Any:
        """Make JSON-RPC call over HTTP with retry until success.

        Retries indefinitely until the RPC response does not contain an error.
        """
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or [],
        }

        session = await self._get_http_session()

        while True:
            try:
                async with session.post(
                    self.http_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    result = await resp.json()

                    if "error" in result:
                        log.warning(
                            "RPC error, retrying",
                            method=method,
                            error=result["error"].get(
                                "message", str(result["error"])
                            ),
                        )
                        await asyncio.sleep(self.RPC_RETRY_DELAY_SECONDS)
                        continue

                    return result["result"]

            except aiohttp.ClientError as e:
                log.warning("RPC request failed, retrying", method=method, error=str(e))
                await asyncio.sleep(self.RPC_RETRY_DELAY_SECONDS)

    async def subscribe_blocks(
        self, callback: Callable[[int], Awaitable[None]]
    ) -> None:
        """Subscribe to new block headers via WebSocket."""
        if not self._ws:
            await self.connect()

        # Subscribe to newHeads
        subscribe_msg = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "eth_subscribe",
            "params": ["newHeads"],
        }
        await self._ws.send(json.dumps(subscribe_msg))
        await self._ws.recv()  # subscription confirmation

        # Listen for new blocks
        async for message in self._ws:
            data = json.loads(message)
            if "params" in data:
                block_number = int(data["params"]["result"]["number"], 16)
                await callback(block_number)

    async def get_block_with_transactions(self, block_number: int) -> dict:
        """Fetch full block with all transactions."""
        hex_block = hex(block_number)
        return await self._rpc_call("eth_getBlockByNumber", [hex_block, True])

    async def get_transaction_receipt(self, tx_hash: str) -> Optional[dict]:
        """Fetch transaction receipt."""
        return await self._rpc_call("eth_getTransactionReceipt", [tx_hash])

    async def get_block_receipts(self, block_number: int) -> list[dict]:
        """Fetch all transaction receipts for a block in one call."""
        hex_block = hex(block_number)
        result = await self._rpc_call("eth_getBlockReceipts", [hex_block])
        return result or []
