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
- [Feedback & Contact](#feedback--contact)

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

**Sample output:**

```
block_number  timestamp                     tx_hash       wallet        token_id          side  tokens    price  total_usdc
82889791      2026-02-12T12:33:25+00:00     0xd87db9...   0x72406a...   1779687064754...  BUY   50.0      0.93   46.5
82889791      2026-02-12T12:33:25+00:00     0x427ada...   0x298e2a...   4157632245133...  BUY   5.0       0.69   3.45
82889791      2026-02-12T12:33:25+00:00     0x52a9bf...   0xd7b58d...   1076833326307...  SELL  0.37      0.59   0.2183
82889792      2026-02-12T12:33:27+00:00     0xa87f97...   0x56bad0...   4157632245133...  BUY   15.826    0.69   10.92
82889792      2026-02-12T12:33:27+00:00     0xa01b26...   0xe041d0...   1076833326307...  SELL  36.0      0.16   5.76
```

### Timeouts & Retries

Each RPC request has a 1-second timeout. Not all RPC providers return HTTP 429 when rate limited — some simply hang indefinitely. A healthy RPC should never take more than 1 second to return a block or receipts, so a timeout is a reliable signal that something is wrong.

Failed requests are retried up to 3 times with a short delay between attempts. If a request still fails after all retries, the download aborts immediately. A healthy endpoint operating within its rate limit should never need more than 3 attempts — persistent failures indicate a deeper issue (bad endpoint, network problems, or rate limit misconfiguration).

## Feedback & Contact

If you have any questions, ideas on how to extend the code, or suggestions for new features, I'd love to hear them.

If you're working on something similar (prediction markets, trading infrastructure, backtesting systems, data pipelines, etc.) and need help, want to collaborate, or just want to exchange ideas, feel free to reach out.

You can message me on Twitter: [@martkiro_](https://twitter.com/martkiro)
Or email me directly at: [martinvkirov@gmail.com](mailto:martinvkirov@gmail.com)

And if nothing else, just say hi 🙂

