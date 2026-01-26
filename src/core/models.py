"""Data models for trade monitoring."""
from dataclasses import dataclass


@dataclass
class DecodedOrder:
    """Represents a decoded order from the blockchain transaction."""

    salt: int
    maker: str
    signer: str
    taker: str
    token_id: str
    maker_amount: int
    taker_amount: int
    expiration: int
    nonce: int
    fee_rate_bps: int
    side: int  # 0 = BUY, 1 = SELL
    signature_type: int
    signature: bytes


@dataclass
class TradeData:
    """Trade data emitted when a matching transaction is found."""

    block_number: int
    transaction_hash: str
    wallet: str  # The wallet address that made the trade
    token_id: str
    side: int  # 0 = BUY, 1 = SELL
    maker_amount: int
    taker_amount: int
