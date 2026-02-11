"""CLI for Polymarket trade scanner."""

import asyncio
from pathlib import Path
from typing import Optional

import typer

from src.constants import DEFAULT_WALLETS_FILE
from src.downloader import TradeDownloader
from src.monitor import TradeMonitor
from src.output.formatters import format_trade
from src.output.writers import append_csv, append_jsonl, write_stdout
from src.utils.logging import get_logger, hyperlink

app = typer.Typer(
    name="poly",
    help="Polymarket trade scanner - listen to real-time or download historical trades",
)

log = get_logger(__name__)


def load_wallets(filepath: Optional[Path]) -> list[str]:
    """Load wallet addresses from file.

    Args:
        filepath: Path to wallets file (one address per line)

    Returns:
        List of wallet addresses (lowercased, deduplicated)
    """
    if filepath is None or not filepath.exists():
        return []

    wallets = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                wallets.append(line.lower())

    return list(dict.fromkeys(wallets))


@app.command()
def listen(
    wallets: Optional[Path] = typer.Option(
        None,
        "--wallets",
        "-w",
        help="Path to wallets file (one address per line)",
    ),
    all_trades: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Track all Polymarket trades (ignore wallet filter)",
    ),
) -> None:
    """Listen to real-time trades via WebSocket."""
    if wallets is None and not all_trades:
        # Try default wallets file
        wallets = DEFAULT_WALLETS_FILE

    wallet_list = [] if all_trades else load_wallets(wallets)

    if wallet_list:
        log.info("Tracking specific wallets", count=len(wallet_list))
        for w in wallet_list:
            log.info("Watching wallet", wallet=w[:10] + "...")
    else:
        log.info("Tracking ALL Polymarket trades (no wallet filter)")

    asyncio.run(_listen(wallet_list))


async def _listen(wallets: list[str]) -> None:
    """Async implementation of listen command."""
    monitor = TradeMonitor()

    def on_trade(trade) -> None:
        formatted = format_trade(trade)
        write_stdout(formatted)

    monitor.on("transaction", on_trade)
    monitor.on("error", lambda e: log.error("Error", error=str(e)))
    monitor.on("close", lambda d: log.warning("Connection closed", details=d))

    await monitor.start(wallets)


@app.command()
def download(
    blocks: int = typer.Option(
        1000,
        "--blocks",
        "-b",
        help="Number of recent blocks to scan",
    ),
    start_block: Optional[int] = typer.Option(
        None,
        "--start",
        help="Start block number (overrides --blocks calculation)",
    ),
    end_block: Optional[int] = typer.Option(
        None,
        "--end",
        help="End block number (default: current block)",
    ),
    output: Path = typer.Option(
        Path("trades.csv"),
        "--output",
        "-o",
        help="Output file path (.csv or .json)",
    ),
    max_rps: int = typer.Option(
        5,
        "--max-rps",
        "-r",
        help="Maximum RPC requests per second",
    ),
) -> None:
    """Download historical trades from the blockchain.

    By default, downloads all trades in the last 1000 blocks.
    """
    if output.suffix not in {".csv", ".json"}:
        raise typer.BadParameter(
            f"Unsupported file extension '{output.suffix}'. Use .csv or .json"
        )

    _download(
        blocks=blocks,
        start_block=start_block,
        end_block=end_block,
        output=output,
        max_rps=max_rps,
    )


def _download(
    blocks: int,
    start_block: Optional[int],
    end_block: Optional[int],
    output: Path,
    max_rps: int,
) -> None:
    """Run download command."""
    downloader = TradeDownloader(max_rps=max_rps)

    # Clear output file if it exists (fresh start)
    if output.exists():
        output.unlink()

    write_fn = append_csv if output.suffix == ".csv" else append_jsonl

    file_link = hyperlink(f"file://{output.resolve()}", str(output))
    log.info("Saving trades to", file=file_link)

    def on_trades(raw_trades: list) -> None:
        """Stream trades to file."""
        formatted = [format_trade(t) for t in raw_trades]
        write_fn(formatted, output)

    try:
        downloader.download(
            start_block=start_block,
            end_block=end_block,
            max_blocks=blocks,
            on_trades=on_trades,
        )
        file_link = hyperlink(f"file://{output.resolve()}", str(output))
        log.info("Trades written", file=file_link)

    finally:
        downloader.close()


if __name__ == "__main__":
    app()
