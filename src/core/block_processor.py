"""Block processing for trade extraction."""
from typing import Optional

from src.api.polygon import PolygonClient
from src.core.abi import CTF_MATCH_ORDERS_SELECTOR, NEGRISK_MATCH_ORDERS_SELECTOR
from src.core.decoder import TransactionDecoder
from src.core.models import TradeData
from src.core.wallet_filter import WalletFilter
from src.utils.logging import get_logger

log = get_logger(__name__)

# Known Polymarket contract addresses
POLYMARKET_CONTRACTS = {
    "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e",  # CTF Exchange
    "0xc5d563a36ae78145c45a50134d48a1215220f80a",  # NegRisk CTF Exchange
    "0x56c79347e95530c01a2fc76e732f9566da16e113",  # NegRisk Operator
}


class BlockProcessor:
    """Processes blocks and extracts matching trades."""

    def __init__(
        self,
        client: PolygonClient,
        decoder: TransactionDecoder,
        wallet_filter: WalletFilter,
    ) -> None:
        self.client = client
        self.decoder = decoder
        self.filter = wallet_filter

    async def process_block(self, block_number: int) -> list[TradeData]:
        """Process all transactions in a block."""
        trades = []
        block = await self.client.get_block_with_transactions(block_number)
        receipts = await self.client.get_block_receipts(block_number)

        # Build receipt lookup by tx hash
        receipt_map = {r["transactionHash"]: r for r in receipts}

        log.info("Processing block", block=block_number, txs=len(block["transactions"]))

        # Debug: check for Polymarket transactions
        ctf_selector = "0x" + CTF_MATCH_ORDERS_SELECTOR.hex()
        negrisk_selector = "0x" + NEGRISK_MATCH_ORDERS_SELECTOR.hex()

        for tx in block["transactions"]:
            tx_input = tx.get("input", "")
            tx_to = (tx.get("to") or "").lower()

            # Check if this is a Polymarket contract
            if tx_to in POLYMARKET_CONTRACTS:
                selector = tx_input[:10] if len(tx_input) >= 10 else "none"
                log.info(
                    "Found Polymarket contract tx",
                    to=tx_to[:10],
                    selector=selector,
                    matches_ctf=(selector == ctf_selector),
                    matches_negrisk=(selector == negrisk_selector),
                )

            receipt = receipt_map.get(tx["hash"])
            trade = self._process_transaction(tx, block_number, receipt)
            if trade:
                trades.append(trade)

        return trades

    def _process_transaction(
        self, tx: dict, block_number: int, receipt: Optional[dict]
    ) -> Optional[TradeData]:
        """Process single transaction and return TradeData if matching."""
        orders = self.decoder.decode(tx["input"])
        if not orders:
            return None

        matching_order = self.filter.filter(orders, receipt)
        if not matching_order:
            return None

        return TradeData(
            block_number=block_number,
            transaction_hash=tx["hash"],
            wallet=matching_order.maker,
            token_id=matching_order.token_id,
            side=matching_order.side,
            maker_amount=matching_order.maker_amount,
            taker_amount=matching_order.taker_amount,
        )
