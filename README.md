# poly-trade-scan

Track Polymarket trades in real-time by listening to Polygon blocks via WebSocket. Monitor all trades or filter by specific wallets.

Unlike polling-based approaches, WebSocket block streaming provides lower latency. And unlike the Polymarket API which requires polling each wallet separately, decoding blocks directly scales to any number of wallets.

![poly-trade-scan demo](assets/exmple.gif)

## Table of Contents

- [Setup](#setup)
  - [Create Virtual Environment](#create-virtual-environment)
  - [Install Package](#install-package)
- [Configuration](#configuration)
  - [RPC Endpoint](#rpc-endpoint)
  - [Wallet Tracking](#wallet-tracking)
- [CLI Usage](#cli-usage)
  - [Listen to Real-Time Trades](#listen-to-real-time-trades)
  - [Download Historical Trades](#download-historical-trades)
  - [Timeouts & Retries](#timeouts--retries)

## Setup

### Create Virtual Environment

```bash
uv venv --python 3.12
source .venv/bin/activate
```

### Install Package

```bash
uv pip install -e .
```

This installs the `poly` CLI command.

## Configuration

### RPC Endpoint

Copy the example environment file and configure your Polygon WSS endpoint:

```bash
cp .env.example .env
```

Edit `.env` and set your WebSocket RPC URL:

```
POLYGON_WSS_URL=wss://polygon.drpc.org
```

You can use a public RPC for testing. Find available endpoints at: https://chainlist.org/?chain=137&search=polygon

### Wallet Tracking

To track specific wallets, add their addresses to `config/wallets.txt` (one per line):

```
0x1234567890abcdef1234567890abcdef12345678
0xabcdef1234567890abcdef1234567890abcdef12
```

Lines starting with `#` are treated as comments.

If `config/wallets.txt` is empty or doesn't exist, all Polymarket trades will be tracked.

## CLI Usage

### Listen to Real-Time Trades

Stream trades as they happen via WebSocket:

```bash
poly listen [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--wallets PATH` | `-w` | Path to wallets file (one address per line) |
| `--all` | `-a` | Track all Polymarket trades (ignore wallet filter) |

**Examples:**

```bash
# Track wallets from default config/wallets.txt
poly listen

# Track wallets from custom file
poly listen -w my_wallets.txt

# Track all Polymarket trades
poly listen --all
```

### Download Historical Trades

Fetch historical trades from the blockchain:

```bash
poly download [OPTIONS]
```

By default, downloads all trades in the last 1000 blocks.

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--blocks` | `-b` | 1000 | Number of recent blocks to scan |
| `--start` | | current - blocks | Start block number |
| `--end` | | current | End block number |
| `--output` | `-o` | `trades.csv` | Output file path (`.csv` or `.json`) |
| `--max-rps` | `-r` | 50 | Maximum RPC requests per second |

**Examples:**

```bash
# Default: last 1000 blocks → trades.csv
poly download

# Last 5000 blocks
poly download -b 5000

# Specific block range
poly download --start 80000000 --end 80001000

# Output as JSON Lines
poly download -o trades.json

# Higher throughput (if RPC allows)
poly download -b 100 --max-rps 100
```

### Timeouts & Retries

Each RPC request has a 1-second timeout. Not all RPC providers return HTTP 429 when rate limited — some simply hang indefinitely. A healthy RPC should never take more than 1 second to return a block or receipts, so a timeout is a reliable signal that something is wrong.

Failed requests are retried up to 3 times with a short delay between attempts. If a request still fails after all retries, the download aborts immediately. A healthy endpoint operating within its rate limit should never need more than 3 attempts — persistent failures indicate a deeper issue (bad endpoint, network problems, or rate limit misconfiguration).
