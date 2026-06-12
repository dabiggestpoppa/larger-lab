---
name: "cli-anything-tradelocker-studio"
description: "CLI harness for TradeLocker Studio — write bot code, run backtests, read results. Use when asked to create a bot on TradeLocker, run a backtest, write strategy code, or interact with TradeLocker Studio."
---

# TradeLocker Studio CLI

Write bot code directly into TradeLocker Studio's Monaco editor, run backtests via the Studio engine API, and read results — all from the command line.

## Prerequisites

- TradeLocker Desktop running (spawns the Studio engine on `localhost:53163`)
- Python 3.11+
- `cli-anything-tradelocker-studio` installed: `pip install -e .`

## Quick Start

```bash
# Login to TradeLocker
tl-studio auth login

# List existing bot projects
tl-studio project list

# Create a new bot project
tl-studio project create --name "My Strategy"

# Write bot code to a project
tl-studio code write <file-id> --code "strategy('My Bot')"

# Or write from a file
tl-studio code write <file-id> --file my_strategy.tl

# Configure backtest parameters
tl-studio config set <project-id> --symbol AUDCAD --resolution 1h --margin 1000

# Run a backtest and wait for results
tl-studio backtest run <project-id> --wait

# Read backtest results
tl-studio backtest results <project-id> <process-id>
```

## Command Reference

### Auth
- `tl-studio auth login` — Authenticate and save credentials
- `tl-studio auth status` — Check current auth status
- `tl-studio auth accounts` — List all TradeLocker accounts

### Projects
- `tl-studio project list` — List all bot projects
- `tl-studio project create --name "X"` — Create new project
- `tl-studio project get <id>` — Get project details
- `tl-studio project rename <id> --name "X"` — Rename
- `tl-studio project clone <id>` — Clone
- `tl-studio project delete <id>` — Delete

### Code (Bot Scripts)
- `tl-studio code read <file-id>` — Read current bot code
- `tl-studio code write <file-id> --code "..."` — Write bot code
- `tl-studio code write <file-id> --file path.tl` — Write from file
- `tl-studio code edit <file-id>` — Open in $EDITOR

### Backtest
- `tl-studio backtest run <project-id>` — Start backtest
- `tl-studio backtest run <project-id> --wait` — Start and wait
- `tl-studio backtest results <project-id> <process-id>` — Get results
- `tl-studio backtest stop <project-id> <process-id>` — Stop running backtest
- `tl-studio backtest issue <project-id> <process-id>` — Get diagnostics

### Config (Backtest Parameters)
- `tl-studio config get <project-id>` — Get current config
- `tl-studio config set <project-id> --symbol X --resolution 1h` — Update config

### Chat (AI)
- `tl-studio chat send <conversation-id> --message "..."` — Send to AI
- `tl-studio chat history <conversation-id>` — Read chat history

### Status
- `tl-studio status` — Engine health + rate limits

## Agent-Specific Guidance

- Always use `--json-output` for machine-readable output
- The Studio engine runs at `http://127.0.0.1:53163` (set `TRADELOCKER_STUDIO_HOST` to override)
- Credentials are stored in `~/.tradelocker-studio/config.json`
- Backtest results include: `total_trades`, `roi_percent`, `absolute_profit`, `drawdown`, `returns`
- The `code write` command is the primary way to inject strategy code into Studio
- After writing code, use `backtest run --wait` to execute and get results
- Strategy code is TradeLocker's proprietary language (similar to Pine Script)
