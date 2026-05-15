---
name: mt5-strategy-builder
description: >
  Activate for building, backtesting, and deploying MetaTrader 5 trading strategies.
  Use when the user wants to create an MT5 indicator, Expert Advisor, backtest a strategy,
  or optimize trading parameters. Works with the MT5 MCP server.
version: 1.0.0
author: agent
platforms: [linux, macos, windows]
---

# MT5 Strategy Builder Skill

## Overview

This skill provides a structured workflow for building MT5 trading strategies using the
MT5 MCP server. It follows the 6-step agent pipeline: Research → Design → Code → Test →
Optimize → Report.

## Prerequisites

- MT5 MCP server running (`python mt5_mcp_server.py`)
- MetaTrader 5 Terminal installed and logged in
- MCP client configured to connect to the MT5 server (Hermes, Claude Code, or OpenClaw)

## Workflow

### Step 1: Research & Validate
```
- Fetch market data: mt5_get_market_data(symbol, timeframe, bars)
- Get available symbols: mt5_get_symbols()
- Check account: mt5_get_account_info()
- Research strategy logic (web, docs, existing strategies)
```

### Step 2: Design the Strategy
```
- Define the trading logic (indicator signals, entry/exit rules)
- Specify input parameters (periods, thresholds, lot sizes)
- Define success criteria (minimum win rate, max drawdown, Sharpe > 1.0)
- Choose risk management (stop loss, take profit, position sizing)
```

### Step 3: Generate Code
```
- For indicators: mt5_create_indicator(name, description, inputs, logic)
- For EAs: mt5_create_ea(name, description, strategy_logic, inputs)
- For custom code: mt5_write_mql5(filename, content, folder)
```

### Step 4: Compile
```
- mt5_compile_file(filepath)
- Check for errors
- If errors: fix code → recompile
```

### Step 5: Backtest
```
Fast path (no MT5 terminal needed):
  - mt5_backtest_python(ea_code, symbol, timeframe, deposit, bars)

Full path (production-grade):
  - mt5_backtest_terminal(ea_name, symbol, timeframe, deposit, from_date, to_date)
  - mt5_get_last_report()
```

### Step 6: Optimize & Validate
```
- mt5_optimize(ea_name, param_ranges, symbol, timeframe, method)
- Analyze results: Sharpe ratio, max drawdown, win rate, profit factor
- Check for overfitting: test on out-of-sample data
- Verify with QA agent (Rule 9: tests verify intent, not just behavior)
```

### Step 7: Deploy (Optional)
```
- mt5_open_trade(symbol, order_type, lot_size, sl_pips, tp_pips)
- mt5_get_positions() — monitor open trades
- mt5_close_trade(ticket) — close when needed
```

## Prompt Template

```
You are an MT5 strategy builder. When given a trading idea:

1. Research the market and validate the concept
2. Design the strategy with clear entry/exit rules
3. Generate MQL5 code using mt5_create_ea or mt5_create_indicator
4. Compile with mt5_compile_file
5. Backtest with mt5_backtest_python (quick) or mt5_backtest_terminal (full)
6. Analyze results: Sharpe, drawdown, win rate, profit factor
7. Optimize parameters if needed
8. Report findings with go/no-go recommendation

Always:
- Define success criteria BEFORE building
- Use risk management (SL/TP on every trade)
- Test on out-of-sample data to check for overfitting
- Follow the 12-rule CLAUDE.md behavioral contract
```

## Example Prompts

- "Build an RSI divergence strategy on EURUSD H4 with confirmation from volume"
- "Create a mean-reversion EA for GBPUSD M15 with Bollinger Bands"
- "Backtest a moving average crossover on BTCUSD H1 and tell me if it's viable"
- "Optimize the lot size and stop loss for my existing EA 'TrendFollower'"
- "Analyze my last backtest report and suggest improvements"

## Safety Rules

- NEVER open live trades without explicit user confirmation
- Always use demo accounts for testing
- Set maximum lot size limits
- Define maximum drawdown thresholds
- Report all risks clearly before any trade execution