"""Output writers for different formats."""

import csv
import json
from pathlib import Path

from src.output.formatters import FormattedTrade
from src.utils.logging import colored, get_logger, hyperlink

log = get_logger(__name__)


def write_stdout(trade: FormattedTrade) -> None:
    """Print trade to stdout with colors and links."""
    tx_link = hyperlink(
        f"https://polygonscan.com/tx/{trade.tx_hash}",
        trade.tx_hash[:10] + "...",
    )
    wallet_link = hyperlink(
        f"https://polygonscan.com/address/{trade.wallet}",
        trade.wallet[:10] + "...",
    )
    side = colored("BUY", "GREEN") if trade.side == "BUY" else colored("SELL", "RED")

    log.info(
        "Trade",
        wallet=wallet_link,
        side=side,
        tokens=f"{trade.tokens:.0f}",
        price=f"${trade.price:.3f}",
        total=f"${trade.total_usdc:.2f}",
        tx=tx_link,
    )


CSV_FIELDNAMES = [
    "block_number",
    "tx_hash",
    "wallet",
    "side",
    "tokens",
    "price",
    "total_usdc",
]


def _trade_to_dict(trade: FormattedTrade) -> dict:
    """Convert FormattedTrade to dict for writing."""
    return {
        "block_number": trade.block_number,
        "tx_hash": trade.tx_hash,
        "wallet": trade.wallet,
        "side": trade.side,
        "tokens": trade.tokens,
        "price": trade.price,
        "total_usdc": trade.total_usdc,
    }


def write_csv(trades: list[FormattedTrade], output: Path) -> None:
    """Write trades to CSV file.

    Args:
        trades: List of formatted trades
        output: Output file path
    """
    with open(output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for trade in trades:
            writer.writerow(_trade_to_dict(trade))


def append_csv(trades: list[FormattedTrade], output: Path) -> None:
    """Append trades to CSV file, creating with header if needed.

    Args:
        trades: List of formatted trades to append
        output: Output file path
    """
    write_header = not output.exists()

    with open(output, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        if write_header:
            writer.writeheader()
        for trade in trades:
            writer.writerow(_trade_to_dict(trade))


def write_json(trades: list[FormattedTrade], output: Path) -> None:
    """Write trades to JSON file.

    Args:
        trades: List of formatted trades
        output: Output file path
    """
    data = [_trade_to_dict(trade) for trade in trades]

    with open(output, "w") as f:
        json.dump(data, f, indent=2)


def append_jsonl(trades: list[FormattedTrade], output: Path) -> None:
    """Append trades to JSON Lines file (one JSON object per line).

    Args:
        trades: List of formatted trades to append
        output: Output file path
    """
    with open(output, "a") as f:
        for trade in trades:
            f.write(json.dumps(_trade_to_dict(trade)) + "\n")
