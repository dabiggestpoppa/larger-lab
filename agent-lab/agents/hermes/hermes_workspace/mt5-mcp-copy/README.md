# MT5 MCP Server — Quick Start Guide

## Prerequisites

1. **MetaTrader 5 Terminal** — Installed and logged in (must be running for live data/trading)
2. **Python 3.11+** with uv or pip
3. **MT5 MCP Server** — This repo

## Setup (3 minutes)

### 1. Install dependencies

```bash
cd mt5-mcp
pip install -r requirements.txt
# Or with uv:
uv pip install -r requirements.txt
```

### 2. Verify MT5 is running

```python
python -c "import MetaTrader5 as mt5; print(mt5.terminal_info())"
```

If this returns `None`, launch MetaTrader 5 manually first.

### 3. Start the MCP server

```bash
python mt5_mcp_server.py
```

You should see:
```
============================================================
🚀 MT5 MCP Server
============================================================
  MT5 Status: MT5 connected successfully
  Terminal Path: C:\Program Files\MetaTrader 5\terminal64.exe
  Data Directory: C:\Users\...\AppData\Roaming\MetaQuotes\Terminal\XXXXX
============================================================
```

### 4. Connect your AI agent

Your MT5 MCP server is now available to any MCP-compatible client. Configure your agent:

#### Option A: Stdio (local, recommended for Claude Code / Cursor)

Create `mcp-config.json` in your project root:
```json
{
  "mcpServers": {
    "mt5": {
      "command": "python",
      "args": ["C:/path/to/larger-lab/mt5-mcp/mt5_mcp_server.py"]
    }
  }
}
```

#### Option B: SSE (remote/headless, for Hermes or OpenClaw)

Start with SSE transport:
```bash
python mt5_mcp_server.py --transport sse --port 50051
```

Then connect via:
```json
{
  "mcpServers": {
    "mt5": {
      "url": "http://localhost:50051/mcp"
    }
  }
}
```
```

### 5. Try it!

Ask your agent:

```
Create an EMA crossover Expert Advisor for EURUSD on H1 timeframe.
Backtest it for 2024 and show me the results.
```

The agent will:
1. Create the EA code → `mt5_create_ea`
2. Compile it → `mt5_compile_file`
3. Run a Python backtest → `mt5_backtest_python`
4. Return formatted results with P&L, win rate, drawdown, Sharpe ratio

## Full Workflow Example

```
User: "Build me a mean reversion strategy for EURUSD on M15"

Agent:
  1. mt5_get_market_data(symbol="EURUSD", timeframe="M15", bars=2000)
     → Studies price structure
  
  2. mt5_create_ea(
       name="MeanReversion_M15",
       description="Mean reversion on M15 with Bollinger Bands and RSI confirmation",
       inputs="input double BB_StdDev = 2.0; input int RSI_Period = 14;",
       strategy_logic="Enter when price touches lower/upper Bollinger Band
                        with RRSI confirming oversold/overbought"
     )
     → Writes MQL5 file
  
  3. mt5_compile_file(filepath=".../MeanReversion_M15.mq5")
     → Compiles to EX5
  
  4. mt5_backtest_python(
       ea_code="MeanReversion_M15",
       symbol="EURUSD",
       timeframe_str="M15",
       deposit=10000,
       bars=5000
     )
     → Returns backtest results
  
  5. Reports: "Strategy shows 62% win rate, 1.35 Sharpe, 8% max drawdown"
```

## Available Tools

| Tool | Purpose | Requires MT5 Running? |
|------|---------|----------------------|
| `mt5_connect` | Connect to MT5 terminal | Yes |
| `mt5_get_account_info` | Account details | Yes |
| `mt5_get_market_data` | OHLCV candle data | Yes |
| `mt5_get_symbols` | List available symbols | Yes |
| `mt5_create_indicator` | Generate MQL5 indicator | No (writes file) |
| `mt5_create_ea` | Generate MQL5 Expert Advisor | No (writes file) |
| `mt5_write_mql5` | Write raw MQL5 code | No (writes file) |
| `mt5_compile_file` | Compile via MetaEditor | Yes (MetaEditor) |
| `mt5_backtest_python` | Python simulation | Yes (data only) |
| `mt5_backtest_terminal` | Full MT5 Strategy Tester | Yes (terminal) |
| `mt5_optimize` | Parameter optimization | Yes (terminal) |
| `mt5_open_trade` | Open live/demo trade | Yes (terminal) |
| `mt5_get_positions` | View open positions | Yes |
| `mt5_close_trade` | Close a position | Yes |
| `mt5_get_last_report` | Fetch backtest report | Yes |
| `mt5_list_files` | List MQL5 files | Yes |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "MT5 not initialized" | Launch MetaTrader 5 manually, then restart server |
| "MetaEditor not found" | Install MetaTrader 5 or update path in code |
| "Symbol not found" | Use `mt5_get_symbols()` to find exact symbol name |
| Compilation errors | Check MQL5 syntax; MetaEditor output has details |
| No backtest data | Ensure symbol has history downloaded in MT5 |
| `pip install MetaTrader5` fails | Use `pip install MetaTrader5 --only-binary :all:` |

## Architecture

This server follows the **Agent Harness** pattern:
- **Tools layer** (this server) — MCP tools for MT5 operations
- **Orchestration** — Agent coordinates the workflow
- **Memory** — Results persist via MEMORY.md and vector store
- **Skills** — Reusable strategy patterns via SKILL.md
- **Verification** — QA agent validates backtest results