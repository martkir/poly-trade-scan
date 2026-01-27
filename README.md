# poly-trade-scan

Track Polymarket trades in real-time by listening to Polygon blocks via WebSocket. Monitor all trades or filter by specific wallets.

Unlike polling-based approaches, WebSocket block streaming provides lower latency. And unlike the Polymarket API which requires polling each wallet separately, decoding blocks directly scales to any number of wallets.

![poly-trade-scan demo](assets/exmple.gif)

## Setup

### Create Virtual Environment

```bash
uv venv --python 3.12
source .venv/bin/activate
```

### Install Dependencies

```bash
uv pip install -r requirements.txt
```

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

## Running

```bash
cd poly-trade-scan
source .venv/bin/activate
python -m src.services.trade_monitor.run
```
