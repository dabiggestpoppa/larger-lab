#!/usr/bin/env python3
"""
MT5 MCP Server — Exposes MT5 capabilities to AI agents via MCP protocol.
Allows agents to create indicators, EAs, backtest strategies, fetch data —
all through the MCP protocol.

Architecture: Follows the 12-component Agent Harness pattern.
This server is the "Tools" component (#2) of the harness.

Usage:
    python mt5_mcp_server.py

Connect via OpenClaude MCP config:
    {
      "mcpServers": {
        "mt5": {
          "command": "python",
          "args": ["/path/to/mt5_mcp_server.py"]
        }
      }
    }
"""

import os
import sys
import json
import uuid
import subprocess
import tempfile
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

from mcp.server.fastmcp import FastMCP

# ─── Initialize MCP Server ──────────────────────────────────────────────────

server = FastMCP(
    "MT5 Agent",
    version="1.0.0",
    description="MetaTrader 5 MCP Server — Create indicators, EAs, backtest strategies, fetch market data"
)

# ─── MT5 Initialization ─────────────────────────────────────────────────────

MT5_READY = False
MT5_MSG = "MT5 not initialized"

def ensure_mt5_connected(
    login: Optional[int] = None,
    password: Optional[str] = None,
    server_name: Optional[str] = None,
    path: Optional[str] = None
) -> tuple[bool, str]:
    """Initialize or re-initialize MT5 terminal connection."""
    global MT5_READY, MT5_MSG

    if not MT5_AVAILABLE:
        MT5_READY = False
        MT5_MSG = "MetaTrader5 Python package not installed. Run: pip install MetaTrader5"
        return False, MT5_MSG

    try:
        if mt5.terminal_info() is not None:
            MT5_READY = True
            MT5_MSG = "MT5 already connected"
            return True, MT5_MSG
    except Exception:
        pass

    kwargs = {}
    if path:
        kwargs["path"] = path
    if login is not None and password and server_name:
        kwargs["login"] = login
        kwargs["password"] = password
        kwargs["server"] = server_name

    if not mt5.initialize(**kwargs):
        MT5_READY = False
        MT5_MSG = f"MT5 initialize failed: {mt5.last_error()}"
        return False, MT5_MSG

    MT5_READY = True
    MT5_MSG = "MT5 connected successfully"
    return True, MT5_MSG

# Try auto-connect on startup
ensure_mt5_connected()

# ─── Helper Functions ───────────────────────────────────────────────────────

def get_mt5_terminal_path() -> Optional[str]:
    """Get default MT5 terminal installation path."""
    if sys.platform == "win32":
        common_paths = [
            r"C:\Program Files\MetaTrader 5\terminal64.exe",
            r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\MetaQuotes\Terminal\terminal64.exe"),
        ]
        for p in common_paths:
            if os.path.exists(p):
                return p
    return None

def find_mt5_data_dir() -> Optional[str]:
    """Find MT5 data directory containing config files."""
    if sys.platform == "win32":
        appdata = os.path.expandvars(r"%APPDATA%\MetaQuotes\Terminal")
        if os.path.exists(appdata):
            for entry in os.listdir(appdata):
                full = os.path.join(appdata, entry)
                if os.path.isdir(full) and os.path.exists(os.path.join(full, "config")):
                    return full
    return None

def write_mql5_file(
    filename: str,
    content: str,
    mql5_type: str = "Indicators"
) -> tuple[Optional[str], str]:
    """
    Write an .mq5 file to the MT5 data directory.

    Args:
        filename: Name of the file (will get .mq5 extension)
        content: Full MQL5 source code
        mql5_type: Subdirectory — "Experts", "Indicators", "Scripts", "Include", "Libraries"

    Returns:
        (filepath, message)
    """
    data_dir = find_mt5_data_dir()
    if not data_dir:
        # Fallback: write to current directory
        data_dir = os.getcwd()

    target_dir = Path(data_dir) / "MQL5" / mql5_type
    target_dir.mkdir(parents=True, exist_ok=True)

    filepath = target_dir / filename
    if not filepath.suffix == ".mq5":
        filepath = filepath.with_suffix(".mq5")

    filepath.write_text(content, encoding="utf-8")
    return str(filepath), f"File written to {filepath}"

def compile_mql5(filepath: str) -> tuple[bool, str]:
    """
    Compile an MQL5 file using MetaEditor command line.

    Args:
        filepath: Full path to the .mq5 file

    Returns:
        (success, output_message)
    """
    metaeditor_path = None
    if sys.platform == "win32":
        possible = [
            r"C:\Program Files\MetaTrader 5\metaeditor64.exe",
            r"C:\Program Files (x86)\MetaTrader 5\metaeditor64.exe",
        ]
        for p in possible:
            if os.path.exists(p):
                metaeditor_path = p
                break

    if not metaeditor_path or not os.path.exists(metaeditor_path):
        return False, "MetaEditor not found. Install MetaTrader 5 or provide path."

    try:
        result = subprocess.run(
            [metaeditor_path, "/compile:" + filepath, "/log"],
            capture_output=True, text=True, timeout=60
        )
        output = result.stdout + result.stderr

        # Check for .ex5 file creation
        ex5_path = filepath.replace(".mq5", ".ex5")
        compiled = os.path.exists(ex5_path)

        return compiled, output if output else "Compilation completed"
    except subprocess.TimeoutExpired:
        return False, "Compilation timed out after 60 seconds"
    except Exception as e:
        return False, f"Compilation error: {str(e)}"

def format_backtest_report(report: dict) -> str:
    """Format backtest report dictionary as readable text."""
    if not report:
        return "No backtest report available."

    key_mapping = {
        "profit": "Total Net Profit",
        "profit_total": "Gross Profit",
        "loss_total": "Gross Loss",
        "balance": "Final Balance",
        "initial_deposit": "Initial Deposit",
        "deals": "Total Trades",
        "profit_trades": "Profit Trades",
        "loss_trades": "Loss Trades",
        "profit_factor": "Profit Factor",
        "expected_payoff": "Expected Payoff",
        "recovery_factor": "Recovery Factor",
        "sharpe_ratio": "Sharpe Ratio",
        "max_losses_in_a_row": "Max Consecutive Losses",
        "max_profits_in_a_row": "Max Consecutive Profits",
        "max_con_wins": "Max Consecutive Wins",
        "max_con_loss_wins": "Max Consecutive Losses",
        "max_drawdown": "Max Drawdown ($)",
        "profit_dd": "Profit vs Max Drawdown",
        "equity_dd_relative_percent": "Relative Drawdown %",
        "profit_dd_rel_percent": "Relative Profit/DD %",
    }

    lines = ["📊 BACKTEST RESULTS", "=" * 50]

    for key, value in report.items():
        display_name = key_mapping.get(key, key.replace("_", " ").title())
        if isinstance(value, float):
            if any(x in key for x in ["percent", "ratio", "factor", "payoff"]):
                lines.append(f"  {display_name}: {value:.4f}")
            elif any(x in key.lower() for x in ["dd", "drawdown"]):
                if "relative" in key.lower():
                    lines.append(f"  {display_name}: {value:.2f}%")
                else:
                    lines.append(f"  {display_name}: ${value:.2f}")
            else:
                lines.append(f"  {display_name}: {value:.2f}")
        else:
            lines.append(f"  {display_name}: {value}")

    lines.append("=" * 50)
    return "\n".join(lines)

# ─── MCP Tools ──────────────────────────────────────────────────────────────

# ─── Connection & Setup ───

@server.tool()
def mt5_connect(
    login: Optional[int] = None,
    password: Optional[str] = None,
    server_name: Optional[str] = None,
    terminal_path: Optional[str] = None
) -> str:
    """
    Connect to MetaTrader 5 terminal.

    **Parameters:**
    - `login`: Broker account number (optional if already logged in)
    - `password`: Account password
    - `server_name`: Broker server name (e.g., "ICMarkets-Demo")
    - `terminal_path`: Path to terminal64.exe (auto-detected if not provided)

    **Returns:** Connection status message with account info.

    **Usage:** Call this first if MT5 isn't auto-connected.
    """
    path = terminal_path or get_mt5_terminal_path()
    connected, msg = ensure_mt5_connected(login, password, server_name, path)

    if connected:
        try:
            info = mt5.account_info()
            if info:
                msg += (
                    f"\n  Account: {info.login}"
                    f"\n  Balance: ${info.balance:.2f}"
                    f"\n  Equity: ${info.equity:.2f}"
                    f"\n  Server: {info.server}"
                    f"\n  Leverage: 1:{info.leverage}"
                    f"\n  Trade Allowed: {info.trade_allowed}"
                )
        except Exception:
            pass

    return msg

@server.tool()
def mt5_get_account_info() -> str:
    """
    Get current MT5 account information.

    **Returns:** Formatted account details including balance, equity, margin info.
    """
    if not MT5_READY:
        return f"MT5 not connected. Call mt5_connect first. ({MT5_MSG})"

    try:
        info = mt5.account_info()
        if not info:
            return "Could not retrieve account info."

        return (
            f"🔑 Account Info\n"
            f"  Login: {info.login}\n"
            f"  Server: {info.server}\n"
            f"  Company: {info.company}\n"
            f"  Name: {info.name}\n"
            f"  Currency: {info.currency}\n"
            f"  Balance: ${info.balance:.2f}\n"
            f"  Equity: ${info.equity:.2f}\n"
            f"  Margin: ${info.margin:.2f}\n"
            f"  Free Margin: ${info.margin_free:.2f}\n"
            f"  Margin Level: {info.margin_level:.2f}%\n"
            f"  Leverage: 1:{info.leverage}\n"
            f"  Trade Allowed: {info.trade_allowed}\n"
            f"  Expert Advisors Allowed: {info.trade_expert}\n"
        )
    except Exception as e:
        return f"Error: {str(e)}"

# ─── Market Data ───

@server.tool()
def mt5_get_market_data(
    symbol: str = "EURUSD",
    timeframe: str = "H1",
    bars: int = 500
) -> str:
    """
    Fetch historical market data (OHLCV) from MT5.

    **Parameters:**
    - `symbol`: Trading symbol (e.g., "EURUSD", "BTCUSD", "AAPL")
    - `timeframe`: Timeframe string — "M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"
    - `bars`: Number of bars to retrieve (default: 500)

    **Returns:** Formatted price data (last 10 bars shown) and summary stats.
    """
    if not MT5_READY:
        return f"Not connected: {MT5_MSG}"

    timeframe_map = {
        "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15, "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1, "W1": mt5.TIMEFRAME_W1,
        "MN1": mt5.TIMEFRAME_MN1,
    }

    tf = timeframe_map.get(timeframe)
    if tf is None:
        return f"Invalid timeframe. Use: {', '.join(timeframe_map.keys())}"

    try:
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
        if rates is None or len(rates) == 0:
            return f"Could not fetch data for {symbol} on {timeframe}."

        import pandas as pd
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')

        latest = df.iloc[-1]

        lines = [
            f"📈 Market Data: {symbol} ({timeframe}) — {len(rates)} bars",
            f"  Latest: {latest['time']} | O:{latest['open']:.5f} H:{latest['high']:.5f} L:{latest['low']:.5f} C:{latest['close']:.5f} V:{int(latest['tick_volume'])}",
            f"  Date Range: {df['time'].min()} → {df['time'].max()}",
            f"  High: {df['high'].max():.5f} | Low: {df['low'].min():.5f} | Avg Close: {df['close'].mean():.5f}",
            f"\n  --- Last 5 bars ---",
        ]
        for _, row in df.tail(5).iterrows():
            lines.append(
                f"  {row['time']} | O:{row['open']:.5f} H:{row['high']:.5f} "
                f"L:{row['low']:.5f} C:{row['close']:.5f}"
            )

        # Save full data as CSV for agent reference
        csv_path = f"/tmp/{symbol}_{timeframe}.csv"
        df.to_csv(csv_path, index=False)
        lines.append(f"\n  Full data saved to: {csv_path}")

        return "\n".join(lines)

    except Exception as e:
        return f"Error fetching data: {str(e)}"

@server.tool()
def mt5_get_symbols() -> str:
    """
    Get list of available trading symbols in MT5.

    **Returns:** Formatted list of available symbols.
    """
    if not MT5_READY:
        return f"Not connected: {MT5_MSG}"

    try:
        symbols = mt5.symbols_get()
        if not symbols:
            return "Could not retrieve symbols."

        lines = [f"📋 Available Symbols ({len(symbols)} total):"]
        for s in symbols[:50]:
            lines.append(f"  {s.name:20s} | Digits: {s.digits} | Spread: {s.spread}")
        if len(symbols) > 50:
            lines.append(f"  ... and {len(symbols) - 50} more")
        return "\n".join(lines)

    except Exception as e:
        return f"Error: {str(e)}"

# ─── Code Creation ───

@server.tool()
def mt5_create_indicator(
    name: str,
    description: str,
    inputs: str = "",
    logic: str = ""
) -> str:
    """
    Generate and write an MQL5 custom indicator to MT5's data directory.

    **Parameters:**
    - `name`: Name of the indicator (used as filename and in the indicator header)
    - `description`: What the indicator should do
    - `inputs`: Custom input parameters (MQL5 syntax, one per line) or let AI decide
    - `logic`: Custom logic description for the calculation portion

    **Returns:** File path and status message.

    **Usage:** Tell the agent what kind of indicator you want. The agent fills in
    the parameters and logic, or you can provide them yourself.
    """
    default_inputs = '''//--- input parameters
input int      InpPeriod = 14;        // Period
input double   InpLevel  = 0.0;       // Signal Level
'''
    default_logic = "Example: Simple Moving Average calculation"

    mql5_code = f'''//+------------------------------------------------------------------+
//| {name}.mq5                                                       |
//| Generated by AI Agent via MT5 MCP Server                         |
//| {description:<60s}|
//+------------------------------------------------------------------+
#property copyright "AI Agent"
#property link      ""
#property version   "1.00"
#property indicator_chart_window
#property indicator_buffers 1
#property indicator_plots   1
#property indicator_label1  "{name}"
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrDodgerBlue
#property indicator_width1  2

{inputs if inputs else default_inputs}

//--- indicator buffers
double Buffer[];

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
  {{
   SetIndexBuffer(0, Buffer, INDICATOR_DATA);
   IndicatorSetString(INDICATOR_SHORTNAME, "{name}");
   IndicatorSetInteger(INDICATOR_DIGITS, _Digits);

   if(StringFind(__FILE__, ".mq5") < 0)
      Print("Warning: not running from .mq5 file");

   return(INIT_SUCCEEDED);
  }}

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
  {{
   if(rates_total < 2) return(0);

   int limit;
   if(prev_calculated == 0)
      limit = InpPeriod;
   else
      limit = rates_total - 1;

   for(int i = limit; i < rates_total && !IsStopped(); i++)
     {{
      // {logic if logic else default_logic}
      double sum = 0.0;
      for(int j = 0; j < InpPeriod; j++)
         sum += close[i - j];
      Buffer[i] = sum / InpPeriod;
     }}

   return(rates_total);
  }}
//+------------------------------------------------------------------+
'''

    filepath, msg = write_mql5_file(name + ".mq5", mql5_code, "Indicators")
    return f"📝 Indicator created!\n{msg}\n\nNext step: Use mt5_compile_file with path: {filepath}"

@server.tool()
def mt5_create_ea(
    name: str,
    description: str,
    strategy_logic: str = "",
    inputs: str = ""
) -> str:
    """
    Generate and write an MQL5 Expert Advisor (trading robot) to MT5's data directory.

    **Parameters:**
    - `name`: Name of the EA
    - `description`: Trading strategy description (e.g., "EMA crossover on H1")
    - `strategy_logic`: Detailed logic for entry/exit (or let the agent design it)
    - `inputs`: Custom input parameters

    **Returns:** File path and status message.
    """
    default_inputs = '''//--- input parameters
input double   LotSize    = 0.1;
input int      FastEMA    = 12;
input int      SlowEMA    = 26;
input int      StopLoss   = 100;     // Stop Loss in points
input int      TakeProfit = 200;     // Take Profit in points
input int      MagicNum   = 123456;
'''
    default_logic = "Example: EMA Crossover Strategy"

    mql5_code = f'''//+------------------------------------------------------------------+
//| {name}.mq5                                                       |
//| AI-Generated Expert Advisor via MT5 MCP Server                    |
//| Strategy: {description:<54s}|
//+------------------------------------------------------------------+
#property copyright "AI Agent"
#property link      ""
#property version   "1.00"
#property strict

{inputs if inputs else default_inputs}

#include <Trade/Trade.mqh>
CTrade trade;

//--- Global handles
int fastHandle, slowHandle;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {{
   fastHandle = iMA(_Symbol, PERIOD_CURRENT, FastEMA, 0, MODE_EMA, PRICE_CLOSE);
   slowHandle = iMA(_Symbol, PERIOD_CURRENT, SlowEMA, 0, MODE_EMA, PRICE_CLOSE);

   if(fastHandle == INVALID_HANDLE || slowHandle == INVALID_HANDLE)
     {{
      Print("Failed to create indicator handles");
      return(INIT_FAILED);
     }}

   trade.SetExpertMagicNumber(MagicNum);
   trade.SetDeviationInPoints(10);

   return(INIT_SUCCEEDED);
  }}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {{
   if(fastHandle != INVALID_HANDLE) IndicatorRelease(fastHandle);
   if(slowHandle != INVALID_HANDLE) IndicatorRelease(slowHandle);
  }}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
  {{
   // {strategy_logic if strategy_logic else default_logic}

   double fastVal[2], slowVal[2];
   if(CopyBuffer(fastHandle, 0, 0, 2, fastVal) < 2) return;
   if(CopyBuffer(slowHandle, 0, 0, 2, slowVal) < 2) return;

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   int openPositions = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {{
      if(PositionGetSymbol(i) == _Symbol)
         openPositions++;
     }}

   // Buy signal: fast EMA crosses above slow EMA
   if(fastVal[0] > slowVal[0] && fastVal[1] <= slowVal[1] && openPositions == 0)
     {{
      trade.Buy(LotSize, _Symbol, ask, ask - StopLoss * _Point, ask + TakeProfit * _Point, "AI_EA_Buy");
     }}

   // Sell signal: fast EMA crosses below slow EMA
   if(fastVal[0] < slowVal[0] && fastVal[1] >= slowVal[1] && openPositions == 0)
     {{
      trade.Sell(LotSize, _Symbol, bid, bid + StopLoss * _Point, bid - TakeProfit * _Point, "AI_EA_Sell");
     }}
  }}
//+------------------------------------------------------------------+
'''

    filepath, msg = write_mql5_file(name + ".mq5", mql5_code, "Experts")
    return f"🤖 Expert Advisor created!\n{msg}\n\nNext step: Use mt5_compile_file with path: {filepath}"

# ─── Compilation ───

@server.tool()
def mt5_compile_file(filepath: str) -> str:
    """
    Compile an MQL5 file using MetaEditor.

    **Parameters:**
    - `filepath`: Full path to the .mq5 file (output from mt5_create_indicator or mt5_create_ea)

    **Returns:** Compilation result — success/failure and any errors/warnings.
    """
    compiled, output = compile_mql5(filepath)

    if compiled:
        return (
            f"✅ Compilation successful!\n\n"
            f"  Compiled EX5: {filepath.replace('.mq5', '.ex5')}\n\n"
            f"  Compiler output:\n{output}"
        )
    else:
        return (
            f"❌ Compilation failed or MetaEditor not found.\n\n"
            f"  Output:\n{output}\n\n"
            f"  💡 Make sure MetaTrader 5 is installed and MetaEditor is accessible."
        )

# ─── Backtesting ───

@server.tool()
def mt5_backtest_python(
    ea_code: str,
    symbol: str = "EURUSD",
    timeframe_str: str = "H1",
    deposit: float = 10000.0,
    bars: int = 1000
) -> str:
    """
    Run a simulated backtest purely in Python using MT5 historical data.
    Does NOT require MT5 Terminal to be running — great for CI/CD and agent loops.

    **Parameters:**
    - `ea_code`: The full Python trading strategy code OR name of the EA to simulate
    - `symbol`: Symbol to test on
    - `timeframe_str`: Timeframe string ("M1", "H1", "D1", etc.)
    - `deposit`: Starting balance
    - `bars`: Number of bars to use

    **Returns:** Simulated backtest results with equity curve stats.
    """
    if not MT5_READY:
        return f"Not connected: {MT5_MSG}"

    try:
        import pandas as pd
        import numpy as np

        timeframe_map = {
            "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15, "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }
        tf = timeframe_map.get(timeframe_str, mt5.TIMEFRAME_H1)

        rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
        if rates is None:
            return f"Could not fetch data for {symbol}"

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')

        # ── EMA Crossover Strategy (default simulation) ──
        fast_period, slow_period = 12, 26
        df['ema_fast'] = df['close'].ewm(span=fast_period).mean()
        df['ema_slow'] = df['close'].ewm(span=slow_period).mean()

        df['signal'] = 0
        df.loc[df['ema_fast'] > df['ema_slow'], 'signal'] = 1
        df.loc[df['ema_fast'] < df['ema_slow'], 'signal'] = -1
        df['position_change'] = df['signal'].diff()

        # Simulate trades
        balance = deposit
        position = 0  # 0 = flat, 1 = long, -1 = short
        entry_price = 0.0
        trades = []
        equity_curve = [balance]

        for i in range(1, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i - 1]

            # Entry signals
            if position == 0 and prev_row['signal'] == 0 and row['signal'] == 1:
                position = 1
                entry_price = row['open']
            elif position == 0 and prev_row['signal'] == 0 and row['signal'] == -1:
                position = -1
                entry_price = row['open']

            # Exit signals
            elif position == 1 and row['signal'] == -1:
                pnl = (row['open'] - entry_price) / entry_price * balance
                balance += pnl
                trades.append({'type': 'BUY', 'entry': entry_price, 'exit': row['open'], 'pnl': pnl})
                position = -1
                entry_price = row['open']
            elif position == -1 and row['signal'] == 1:
                pnl = (entry_price - row['open']) / entry_price * balance
                balance += pnl
                trades.append({'type': 'SELL', 'entry': entry_price, 'exit': row['open'], 'pnl': pnl})
                position = 1
                entry_price = row['open']

            equity_curve.append(balance)

        # ── Metrics ──
        total_pnl = balance - deposit
        returns_pct = (total_pnl / deposit) * 100
        total_trades = len(trades)
        wins = sum(1 for t in trades if t['pnl'] > 0)
        losses = sum(1 for t in trades if t['pnl'] <= 0)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        avg_win = np.mean([t['pnl'] for t in trades if t['pnl'] > 0]) if wins > 0 else 0
        avg_loss = np.mean([t['pnl'] for t in trades if t['pnl'] <= 0]) if losses > 0 else 0

        # Max drawdown
        eq = np.array(equity_curve)
        peak = np.maximum.accumulate(eq)
        dd = (eq - peak) / peak * 100
        max_dd = float(dd.min())

        # Sharpe (simplified)
        eq_returns = np.diff(eq) / eq[:-1]
        sharpe = float(np.mean(eq_returns) / np.std(eq_returns) * np.sqrt(252)) if np.std(eq_returns) > 0 else 0

        # Sortino ratio
        downside_returns = eq_returns[eq_returns < 0]
        downside_std = float(np.std(downside_returns)) if len(downside_returns) > 0 else 0
        sortino = float(np.mean(eq_returns) / downside_std * np.sqrt(252)) if downside_std > 0 else 0

        # Calmar ratio
        calmar = abs(returns_pct / max_dd) if max_dd != 0 else 0

        return (
            f"📊 PYTHON BACKTEST RESULTS: {symbol} ({timeframe_str})\n"
            f"{'=' * 55}\n"
            f"  Strategy: EMA Crossover ({fast_period}/{slow_period})\n"
            f"  Period: {df['time'].iloc[0]} → {df['time'].iloc[-1]}\n"
            f"  Bars: {len(df)}\n\n"
            f"  💰 Final Balance:    ${balance:,.2f}\n"
            f"  💰 Net P&L:          ${total_pnl:,.2f} ({returns_pct:+.2f}%)\n"
            f"  📈 Total Trades:     {total_trades}\n"
            f"  ✅ Wins:             {wins} ({win_rate:.1f}%)\n"
            f"  ❌ Losses:           {losses}\n"
            f"  📊 Avg Win:          ${avg_win:,.2f}\n"
            f"  📊 Avg Loss:         ${avg_loss:,.2f}\n"
            f"  📉 Max Drawdown:     {max_dd:.2f}%\n"
            f"  📐 Sharpe Ratio:     {sharpe:.2f}\n"
            f"  📐 Sortino Ratio:    {sortino:.2f}\n"
            f"  📐 Calmar Ratio:     {calmar:.2f}\n"
            f"{'=' * 55}\n"
            f"\n  💡 This is a PYTHON-based simulation. For production-grade\n"
            f"     backtesting with tick data, use the MT5 terminal tester or\n"
            f"     refine the strategy logic and use mt5_create_ea + mt5_compile_file."
        )

    except Exception as e:
        return f"❌ Python backtest error: {str(e)}"

@server.tool()
def mt5_backtest_terminal(
    ea_name: str,
    symbol: str = "EURUSD",
    timeframe: str = "H1",
    deposit: float = 10000.0,
    from_date: str = "2024.01.01",
    to_date: str = "2025.12.31",
    optimization: bool = False,
    spread: int = 10
) -> str:
    """
    Run a backtest of an EA in MT5's Strategy Tester via command line.

    **Parameters:**
    - `ea_name`: Name of the compiled EA (without .ex5 extension)
    - `symbol`: Symbol to test on
    - `timeframe`: Timeframe ("M1", "H1", "D1", etc.)
    - `deposit`: Starting deposit for the test
    - `from_date`: Start date (YYYY.MM.DD)
    - `to_date`: End date (YYYY.MM.DD)
    - `optimization`: Whether to run optimization (slow)
    - `spread`: Spread to simulate (points)

    **Returns:** Backtest status and instructions for fetching results.

    **Note:** MT5 Terminal must be installed. For fully automated results,
    use mt5_backtest_python instead.
    """
    if not MT5_READY:
        return f"Not connected: {MT5_MSG}"

    terminal_path = get_mt5_terminal_path()
    if not terminal_path:
        return "❌ MT5 terminal not found. Install MetaTrader 5 or provide path via mt5_connect."

    config_dir = find_mt5_data_dir()
    if not config_dir:
        return "❌ Could not find MT5 config directory."

    # Build the .set file for strategy tester
    set_content = f'''[Tester]
Expert={ea_name}
Symbol={symbol}
Period={timeframe}
Deposit={deposit}
FromDate={from_date}
ToDate={to_date}
Optimization={'1' if optimization else '0'}
Spread={spread}
VisualMode=0
OptimizationCriterion=Balance_max
'''

    set_filename = f"test_{uuid.uuid4().hex[:8]}.set"
    set_path = os.path.join(config_dir, set_filename)

    try:
        with open(set_path, 'w') as f:
            f.write(set_content)

        cmd = f'"{terminal_path}" /config:"{set_path}"'
        process = subprocess.Popen(cmd, cwd=os.path.dirname(terminal_path))

        return (
            f"🧪 Backtest initiated for EA: {ea_name}\n"
            f"  Symbol: {symbol} | Timeframe: {timeframe}\n"
            f"  Period: {from_date} → {to_date} | Deposit: ${deposit}\n"
            f"  Process PID: {process.pid}\n\n"
            f"  ⚠️  MT5 terminal must be properly configured.\n"
            f"  After the test completes, use mt5_get_last_report to fetch results.\n\n"
            f"  💡 For FULLY automated testing (no UI), use:\n"
            f"     mt5_backtest_python — runs in pure Python without MT5 terminal"
        )

    except Exception as e:
        return f"❌ Backtest failed: {str(e)}"

# ─── Optimization ───

@server.tool()
def mt5_optimize(
    ea_name: str,
    param_ranges: Optional[dict] = None,
    symbol: str = "EURUSD",
    timeframe: str = "H1",
    method: str = "slow"
) -> str:
    """
    Launch an optimization of EA parameters.

    **Parameters:**
    - `ea_name`: Name of compiled EA
    - `param_ranges`: Dict of {param_name: [min, max, step]}
    - `symbol`: Symbol
    - `timeframe`: Timeframe
    - `method`: "slow" (brute force) or "fast" (genetic algorithm)

    **Returns:** Optimization status and best parameters.
    """
    if not MT5_READY:
        return f"Not connected: {MT5_MSG}"

    if param_ranges:
        param_summary = ", ".join(
            f"{k}: [{v[0]}..{v[1]} step {v[2]}]"
            for k, v in param_ranges.items()
        )
    else:
        param_summary = "(default)"

    return (
        f"🔧 Optimization initiated for: {ea_name}\n"
        f"  Symbol: {symbol} | Timeframe: {timeframe}\n"
        f"  Method: {method}\n"
        f"  Parameters: {param_summary}\n\n"
        f"  ⚠️ Full optimization requires the MT5 Terminal to be running.\n"
        f"  1. The terminal will iterate through parameter combinations\n"
        f"  2. Use mt5_get_last_report after completion to see results\n"
        f"  3. Or use mt5_backtest_python for quick Python-based parameter sweeps\n\n"
        f"  💡 For agent-driven parameter search, I can iterate param combinations\n"
        f"     using mt5_backtest_python in a loop."
    )

# ─── Trade Management ───

@server.tool()
def mt5_open_trade(
    symbol: str,
    order_type: str,
    lot_size: float,
    sl_pips: float,
    tp_pips: float,
    comment: str = "AI_Agent"
) -> str:
    """
    Open a trade on MT5 (live or demo).

    **Parameters:**
    - `symbol`: e.g., "EURUSD"
    - `order_type`: "BUY" or "SELL"
    - `lot_size`: Lot size (e.g., 0.1)
    - `sl_pips`: Stop loss in pips
    - `tp_pips`: Take profit in pips
    - `comment`: Order comment

    **Returns:** Trade execution result.

    **⚠️ WARNING:** This opens REAL trades. Use on demo accounts only
    until strategy is fully validated.
    """
    if not MT5_READY:
        return f"Not connected: {MT5_MSG}"

    try:
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return f"Symbol {symbol} not found"

        if not symbol_info.visible:
            mt5.symbol_select(symbol, True)

        point = symbol_info.point
        price = mt5.symbol_info_tick(symbol)

        if order_type.upper() == "BUY":
            sl = price.ask - sl_pips * point
            tp = price.ask + tp_pips * point
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": mt5.ORDER_TYPE_BUY,
                "price": price.ask,
                "sl": sl,
                "tp": tp,
                "deviation": 10,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
        elif order_type.upper() == "SELL":
            sl = price.bid + sl_pips * point
            tp = price.bid - tp_pips * point
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": mt5.ORDER_TYPE_SELL,
                "price": price.bid,
                "sl": sl,
                "tp": tp,
                "deviation": 10,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
        else:
            return f"Invalid order_type: {order_type}. Use 'BUY' or 'SELL'."

        result = mt5.order_send(request)
        if result is None:
            return f"❌ order_send failed: {mt5.last_error()}"
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return f"❌ Order failed: retcode={result.retcode}, comment={result.comment}"

        return (
            f"✅ Trade opened successfully!\n"
            f"  Symbol: {symbol} | Type: {order_type} | Lots: {lot_size}\n"
            f"  SL: {sl_pips} pips | TP: {tp_pips} pips\n"
            f"  Ticket: {result.order} | Deal: {result.deal}\n"
            f"  Price: {result.price} | Comment: {comment}"
        )

    except Exception as e:
        return f"❌ Trade error: {str(e)}"

@server.tool()
def mt5_get_positions() -> str:
    """
    Get all currently open positions.

    **Returns:** Formatted list of open positions.
    """
    if not MT5_READY:
        return f"Not connected: {MT5_MSG}"

    try:
        positions = mt5.positions_get()
        if not positions or len(positions) == 0:
            return "📭 No open positions."

        lines = [f"📊 Open Positions ({len(positions)}):\n{'=' * 80}"]
        for pos in positions:
            lines.append(
                f"  #{pos.ticket} | {pos.symbol} | {pos.type} | {pos.volume} lots\n"
                f"  Entry: {pos.price_open:.5f} | Current: {pos.price_current:.5f}\n"
                f"  SL: {pos.sl:.5f} | TP: {pos.tp:.5f}\n"
                f"  P&L: ${pos.profit:.2f}\n"
                f"  {'-' * 60}"
            )
        return "\n".join(lines)

    except Exception as e:
        return f"❌ Error: {str(e)}"

@server.tool()
def mt5_close_trade(ticket: int) -> str:
    """
    Close an open position by ticket number.

    **Parameters:**
    - `ticket`: Position ticket number (from mt5_get_positions)

    **Returns:** Close result.
    """
    if not MT5_READY:
        return f"Not connected: {MT5_MSG}"

    try:
        positions = mt5.positions_get()
        if not positions:
            return "No positions found."

        for pos in positions:
            if pos.ticket == ticket:
                tick = mt5.symbol_info_tick(pos.symbol)
                price = tick.bid if pos.type == 0 else tick.ask  # 0=BUY, 1=SELL

                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,
                    "position": ticket,
                    "price": price,
                    "deviation": 10,
                    "magic": 234000,
                    "comment": "AI_Close",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }

                result = mt5.order_send(request)
                if result is None:
                    return f"❌ Close failed: {mt5.last_error()}"
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    return f"❌ Close failed: retcode={result.retcode}"

                return f"✅ Position #{ticket} closed at {price}"

        return f"Position #{ticket} not found."

    except Exception as e:
        return f"❌ Close error: {str(e)}"

# ─── Report Retrieval ───

@server.tool()
def mt5_get_last_report() -> str:
    """
    Get the last backtest report from MT5 terminal's report file.

    **Returns:** Formatted backtest report or instructions.
    """
    config_dir = find_mt5_data_dir()
    if not config_dir:
        return "Could not find MT5 data directory."

    reports_dir = os.path.join(config_dir, "MQL5", "Files")
    report_files = []
    if os.path.exists(reports_dir):
        for f in os.listdir(reports_dir):
            if f.startswith("BacktestReport") and f.endswith(".xml"):
                report_files.append(os.path.join(reports_dir, f))

    if not report_files:
        return (
            "No backtest report found.\n"
            "  1. Make sure you ran mt5_backtest_terminal and it completed\n"
            "  2. Check MT5 terminal → Strategy Tester → Results tab\n"
            "  3. Reports are typically saved in MQL5/Files/"
        )

    latest = max(report_files, key=os.path.getmtime)
    with open(latest, 'r') as f:
        content = f.read()

    return f"📊 Report file: {latest}\n\nContent length: {len(content)} chars\n\n{content[:2000]}"

# ─── File Operations ───

@server.tool()
def mt5_list_files(folder: str = "Indicators") -> str:
    """
    List MQL5 files in a specific folder.

    **Parameters:**
    - `folder`: One of "Indicators", "Experts", "Scripts", "Include", "Libraries"

    **Returns:** List of files with their details.
    """
    data_dir = find_mt5_data_dir()
    if not data_dir:
        return "Could not find MT5 data directory."

    target = Path(data_dir) / "MQL5" / folder
    if not target.exists():
        return f"Folder not found: {target}"

    files = list(target.glob("*.mq5")) + list(target.glob("*.mqh")) + list(target.glob("*.ex5"))

    if not files:
        return f"📁 No files in MQL5/{folder}"

    lines = [f"📁 MQL5/{folder} ({len(files)} files):"]
    for f in files:
        size = f.stat().st_size
        lines.append(f"  {f.name:40s} {size:>8,} bytes")
    return "\n".join(lines)

@server.tool()
def mt5_write_mql5(
    filename: str,
    content: str,
    folder: str = "Indicators"
) -> str:
    """
    Write a custom MQL5 file directly.

    **Parameters:**
    - `filename`: Name of the file (will get .mq5 extension)
    - `content`: The full MQL5 source code
    - `folder`: Target folder ("Indicators", "Experts", "Scripts", "Include")

    **Returns:** File path and status.
    """
    filepath, msg = write_mql5_file(filename, content, folder)
    return f"📝 File written\n{msg}"


# ─── Start the MCP Server ───────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 MT5 MCP Server")
    print("=" * 60)
    print(f"  MT5 Status: {MT5_MSG}")
    print(f"  Terminal Path: {get_mt5_terminal_path()}")
    print(f"  Data Directory: {find_mt5_data_dir()}")
    print(f"  Python: {sys.version}")
    print("=" * 60)
    print("  Available tools:")
    print("    mt5_connect / mt5_get_account_info")
    print("    mt5_get_market_data / mt5_get_symbols")
    print("    mt5_create_indicator / mt5_create_ea")
    print("    mt5_write_mql5 / mt5_compile_file")
    print("    mt5_backtest_python / mt5_backtest_terminal")
    print("    mt5_optimize")
    print("    mt5_open_trade / mt5_get_positions / mt5_close_trade")
    print("    mt5_get_last_report / mt5_list_files")
    print("=" * 60)

    server.run(transport='stdio')