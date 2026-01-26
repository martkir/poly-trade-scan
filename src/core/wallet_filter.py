"""Wallet filtering for trade monitoring."""
from typing import Optional

from src.core.models import DecodedOrder


class WalletFilter:
    """Filters transactions by target wallet addresses."""

    def __init__(self, target_wallets: list[str]) -> None:
        # Empty list means track all wallets
        self.target_wallets = (
            {w.lower() for w in target_wallets} if target_wallets else None
        )

    @property
    def is_tracking_all(self) -> bool:
        """Return True if tracking all wallets (no filter)."""
        return self.target_wallets is None

    def filter(
        self, orders: list[DecodedOrder], receipt: Optional[dict]
    ) -> Optional[DecodedOrder]:
        """Find matching order and verify transaction success."""
        # Verify transaction was successful
        if not self._is_successful(receipt):
            return None

        for order in orders:
            if self._matches_wallet(order):
                return order

        return None

    def _matches_wallet(self, order: DecodedOrder) -> bool:
        """Check if order maker matches any target wallet (or all if no filter)."""
        if self.target_wallets is None:
            return True  # Track all wallets
        return order.maker.lower() in self.target_wallets

    def _is_successful(self, receipt: Optional[dict]) -> bool:
        """Check if receipt indicates successful transaction."""
        return receipt is not None and int(receipt["status"], 16) == 1
