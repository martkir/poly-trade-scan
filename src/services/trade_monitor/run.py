"""Entry point for the trade monitor service."""
import asyncio
import os
from pathlib import Path

from src.constants import DEFAULT_WALLETS_FILE
from src.services.trade_monitor.monitor import TradeMonitor
from src.utils.logging import colored, get_logger, hyperlink

log = get_logger(__name__)


def load_wallets_from_file(filepath: Path) -> list[str]:
    """Load wallet addresses from a text file.

    Args:
        filepath: Path to wallets file (one address per line)

    Returns:
        List of wallet addresses (lowercased, deduplicated).
        Empty list if file is missing or empty (tracks all wallets).
    """
    if not filepath.exists():
        return []  # Track all wallets

    wallets = []
    with open(filepath) as f:
        for line in f:
            # Strip whitespace and skip comments/empty lines
            line = line.strip()
            if line and not line.startswith("#"):
                wallets.append(line.lower())

    # Deduplicate while preserving order
    return list(dict.fromkeys(wallets))


def on_trade(trade) -> None:
    """Handle detected trade."""
    tx_hash = trade.transaction_hash
    tx_link = hyperlink(
        f"https://polygonscan.com/tx/{tx_hash}",
        tx_hash[:10] + "...",
    )
    wallet_link = hyperlink(
        f"https://polygonscan.com/address/{trade.wallet}",
        trade.wallet[:10] + "...",
    )
    is_buy = trade.side == 0
    side = colored("BUY", "GREEN") if is_buy else colored("SELL", "RED")
    log.info(
        "Trade",
        wallet=wallet_link,
        side=side,
        maker_amount=trade.maker_amount,
        taker_amount=trade.taker_amount,
        tx=tx_link,
    )


async def main() -> None:
    wallets_file_env = os.environ.get("WALLETS_FILE")
    wallets_file = Path(wallets_file_env) if wallets_file_env else DEFAULT_WALLETS_FILE
    wallets = load_wallets_from_file(wallets_file)

    if wallets:
        log.info("Tracking specific wallets", count=len(wallets))
        for wallet in wallets:
            log.info("Watching wallet", wallet=wallet[:10] + "...")
    else:
        log.info("Tracking ALL Polymarket trades (no wallet filter)")

    monitor = TradeMonitor()

    monitor.on("transaction", on_trade)
    monitor.on("error", lambda e: log.error("Error", error=str(e)))
    monitor.on("close", lambda d: log.warning("Connection closed", details=d))

    await monitor.start(wallets)


if __name__ == "__main__":
    asyncio.run(main())
