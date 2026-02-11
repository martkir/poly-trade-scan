"""Trade formatting utilities."""

from dataclasses import dataclass

from src.core.models import TradeData


@dataclass
class FormattedTrade:
    """Human-readable trade data."""

    wallet: str
    side: str  # "BUY" or "SELL"
    tokens: float
    price: float
    total_usdc: float
    tx_hash: str
    block_number: int


def format_trade(trade: TradeData) -> FormattedTrade:
    """Convert raw TradeData to human-readable format.

    Args:
        trade: Raw trade data from blockchain

    Returns:
        Formatted trade with calculated amounts
    """
    is_buy = trade.side == 0
    if is_buy:
        usdc = trade.maker_amount / 1_000_000
        tokens = trade.taker_amount / 1_000_000
    else:
        usdc = trade.taker_amount / 1_000_000
        tokens = trade.maker_amount / 1_000_000

    price = usdc / tokens if tokens > 0 else 0

    return FormattedTrade(
        wallet=trade.wallet,
        side="BUY" if is_buy else "SELL",
        tokens=tokens,
        price=price,
        total_usdc=usdc,
        tx_hash=trade.transaction_hash,
        block_number=trade.block_number,
    )
