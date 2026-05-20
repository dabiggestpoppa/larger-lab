# MT5 Connector Architecture — CEREBUS FX Trading System

> **Version:** 1.0 | **Date:** 2026-05-19 | **Author:** MT5 Integration Engineer
> **Status:** Design Complete — Ready for Implementation
> **Classification:** PROPRIETARY

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Connection Method](#3-connection-method)
4. [Architecture Components](#4-architecture-components)
5. [Data Flow: CEREBUS Signals → MT5 Execution](#5-data-flow-cerebus-signals--mt5-execution)
6. [DMR Strategy on MT6](#6-dmr-strategy-on-mt5)
7. [Risk Management Integration](#7-risk-management-integration)
8. [Error Handling & Recovery](#8-error-handling--recovery)
9. [How to Run DMR Backtest on MT5](#9-how-to-run-dmr-backtest-on-mt5)
10. [File-Based Fallback](#10-file-based-fallback)
11. [Implementation Roadmap](#11-implementation-roadmap)
12. [Appendix: MT5 API Reference](#12-appendix-mt5-api-reference)

---

## 1. Executive Summary

This document describes the architecture for connecting the CEREBUS FX quantitative trading system to MetaTrader 5 (MT5) for backtesting and live trading. The connector enables:

- **Automated backtesting** of the DMR (Deep Mean Reversion) strategy on MT5 historical data
- **Signal bridging** from CEREBUS Python optimizer → MT5 execution engine
- **Risk management** integration (position sizing, daily limits, kill switches)
- **Dual verification** — compare MT5 backtest results with Python optimizer results

**Key Decision:** We use the **MetaTrader5 Python package** (official API) as the primary connection method, with a **file-based signal fallback** for environments where the API is unavailable.

---

## 2. System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CEREBUS FX Trading System                       │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────────────┐  │
│  │  Optimizer   │    │  Strategy    │    │  Risk Management      │  │
│  │  (Python)    │───▶│  Engine      │───▶│  Layer                │  │
│  │              │    │  (Python)    │    │  (0.12% per signal)   │  │
│  └──────────────┘    └──────┬───────┘    └───────────┬───────────┘  │
│                             │                        │              │
│                             ▼                        ▼              │
│                    ┌──────────────────────────────────────┐         │
│                    │        MT5 Connector (Python)         │         │
│                    │  ┌────────────┐  ┌────────────────┐  │         │
│                    │  │ MT5 API    │  │ File Fallback  │  │         │
│                    │  │ (Primary)  │  │ (Secondary)    │  │         │
│                    │  └─────┬──────┘  └───────┬────────┘  │         │
│                    └────────┼─────────────────┼───────────┘         │
│                             │                 │                     │
└─────────────────────────────┼─────────────────┼─────────────────────┘
                              │                 │
                              ▼                 ▼
                    ┌──────────────────────────────────┐
                    │       MetaTrader 5 Terminal       │
                    │  ┌────────────┐  ┌─────────────┐  │
                    │  │ Strategy   │  │ Historical  │  │
                    │  │ Tester     │  │ Data        │  │
                    │  └────────────┘  └─────────────┘  │
                    │  ┌────────────┐  ┌─────────────┐  │
                    │  │ Live       │  │ Demo        │  │
                    │  │ Execution  │  │ Account     │  │
                    │  └────────────┘  └─────────────┘  │
                    └──────────────────────────────────┘
```

### Current Environment

| Component | Status | Details |
|-----------|--------|---------|
| MT5 Terminal | ✅ Running | terminal64.exe (PID 25096), Build 5836 |
| MT5 Python API | ✅ Installed | MetaTrader5 v5.0.5735, CP311, Win64 |
| TV Bridge | ✅ Running | TradingView signal copier — DO NOT CLOSE |
| Python Optimizer | ✅ Complete | DMR: 91.8% WR, PF 111.96, MaxDD 0.05% |
| Data | ✅ Available | EUR/USD M5, Jan 2022 – Apr 2026, 315K+ candles |

---

## 3. Connection Method

### Primary: MetaTrader5 Python API (Direct)

The `MetaTrader5` Python package provides direct access to the MT5 terminal running on the same machine.

**Connection Flow:**
```python
import MetaTrader5 as mt5

# Initialize MT5 terminal connection
if not mt5.initialize():
    raise ConnectionError(f"MT5 init failed: {mt5.last_error()}")

# Verify connection
account = mt5.account_info()
print(f"Connected: {account.login} @ {account.server} ({account.company})")
```

**Advantages:**
- Real-time market data (ticks, bars)
- Direct order placement and modification
- Position and trade history access
- No intermediate files or services needed
- Low latency (< 10ms for local operations)

**Limitations:**
- MT5 terminal must be running and logged in
- Windows-only (MT5 terminal is Windows)
- Single terminal instance per process

### Secondary: File-Based Signal Passing (Fallback)

When the API is unavailable (e.g., MT5 on a different machine, API issues), signals are written to CSV/JSON files that an MT5 EA reads.

**Flow:**
```
Python writes signals → MQL5/Files/signals/ → MT5 EA reads → Executes trades
MT5 EA writes results → MQL5/Files/results/ → Python reads → Analyzes
```

### Not Used: ZeroMQ / TCP Socket

ZeroMQ adds complexity without benefit for a single-machine setup. The direct API is faster and simpler. If distributed trading is needed in the future, ZeroMQ can be added.

---

## 4. Architecture Components

### 4.1 MT5Client — Low-Level API Wrapper

Wraps the MetaTrader5 Python package with error handling, reconnection, and logging.

**Responsibilities:**
- Initialize/shutdown MT5 connection
- Fetch account info, symbol info, ticks, historical bars
- Place/modify/cancel orders
- Query positions and trade history
- Error handling and automatic reconnection

**Key Methods:**
| Method | Purpose |
|--------|---------|
| `connect()` | Initialize MT5, verify login |
| `disconnect()` | Shutdown MT5 connection |
| `get_bars(symbol, timeframe, count)` | Fetch historical bars |
| `get_ticks(symbol, count)` | Fetch recent ticks |
| `place_order(symbol, volume, order_type, price, sl, tp)` | Submit order |
| `modify_order(ticket, sl, tp)` | Modify existing order |
| `close_position(ticket)` | Close position by ticket |
| `get_positions()` | List open positions |
| `get_history_deals(from_date, to_date)` | Fetch deal history |

### 4.2 DMRStrategy — Strategy Implementation

Implements the Deep Mean Reversion (DMR) strategy logic for MT5.

**DMR Strategy Parameters (from optimizer):**
| Parameter | Value |
|-----------|-------|
| Strategy | Deep_Mean_Reversion |
| Pair | EUR/USD |
| Win Rate | 91.8% |
| Profit Factor | 111.96 |
| Max Drawdown | 0.05% |
| Total Trades | 764 |
| Avg Win | 12.59 pips |
| Avg Loss | -1.25 pips |
| Kelly Fraction | 0.3183 |
| Annual Return | 28.6% |

**DMR Logic (from CEREBUS Manual):**
1. Measure Asian Range (00:00-08:00 UTC)
2. Classify Tier (T1/T2/T3/NO-GO)
3. Detect P90 candle (body threshold by time window)
4. Enter on P90 close outside Asian band
5. SL at 80% of P90 body from entry
6. TP at -50% of Asian Range extension
7. Hard exit at 12:00 PM EST
8. 132% Kill Switch

### 4.3 MT5BacktestEngine — Backtest Controller

Runs DMR strategy on MT5 historical data and collects results.

**Responsibilities:**
- Fetch historical bars from MT5
- Simulate DMR strategy bar-by-bar
- Track trades, P&L, drawdown
- Export results in optimizer-compatible format
- Compare with Python optimizer results

### 4.4 SignalBridge — File-Based Fallback

Writes/reads signals to/from files for environments where the API is unavailable.

**Signal Format (JSON):**
```json
{
  "timestamp": "2026-05-19T07:30:00",
  "symbol": "EURUSD",
  "direction": "BUY",
  "volume": 0.1,
  "entry_price": 1.08520,
  "stop_loss": 1.08480,
  "take_profit": 1.08700,
  "strategy": "DMR",
  "tier": "T1",
  "asian_range_pips": 15.3
}
```

### 4.5 RiskManager — Risk Controls

Enforces risk limits on all trading operations.

**Risk Parameters (from CEREBUS Manual):**
| Parameter | Value |
|-----------|-------|
| Risk Per Activation | 0.12% of equity |
| Max Concurrent Risk | 0.36% (3 signals) |
| Daily Loss Limit | 0.40% (hard stop) |
| Personal Daily Limit | 0.50% |
| Max Position Size | 0.50 lots (initial) |
| Correlation Rule | EUR/USD + GBP/USD = 1 position |

---

## 5. Data Flow: CEREBUS Signals → MT5 Execution

### Backtest Flow

```
1. Python Optimizer produces DMR parameters
         │
         ▼
2. MT5BacktestEngine fetches historical bars from MT5
         │
         ▼
3. DMRStrategy processes each bar:
   a. Calculate Asian Range (00:00-08:00 UTC)
   b. Detect P90 candles (2:00-11:00 AM EST)
   c. Generate entry signals
   d. Apply risk management
         │
         ▼
4. MT5BacktestEngine simulates execution:
   a. Track entry/exit prices
   b. Calculate P&L per trade
   c. Compute drawdown curve
         │
         ▼
5. Results exported as JSON (optimizer-compatible format)
         │
         ▼
6. Comparison: MT5 results vs Python optimizer results
```

### Live Trading Flow

```
1. CEREBUS strategy engine generates signal
         │
         ▼
2. RiskManager validates signal:
   a. Check daily loss limit
   b. Check concurrent risk
   c. Check correlation rules
   d. Calculate position size
         │
         ▼
3. MT5Client.place_order():
   a. Map signal → MT5 order request
   b. Submit via mt5.order_send()
   c. Verify execution
         │
         ▼
4. Monitor position:
   a. Track SL/TP hits
   b. Apply trailing stops if needed
   c. Enforce 12:00 PM hard exit
         │
         ▼
5. Log results → Update performance database
```

---

## 6. DMR Strategy on MT5

### Strategy Parameters for MT5 Implementation

Based on the optimizer results and CEREBUS manual:

**Entry Conditions:**
- Asian Range < 30 pips (T1 or T2)
- P90 candle closes outside Asian High/Low
- P90 body >= threshold for time window (4.1-6.2 pips)
- Time: 2:00 AM - 11:00 AM EST
- No major news within 4 hours

**Position Sizing:**
- T1 (Asian < 20p): 100% size
- T2 (Asian 20-30p): 75% size
- T3 (Asian 30-45p): 50% size
- Base size: 0.1 lots per 0.12% risk

**Exit Conditions:**
- TP: -50% of Asian Range extension from Asian band
- SL: 80% of P90 body from entry price
- Hard Exit: 12:00 PM EST (close ALL)
- Kill Switch: 132% of Asian Range violation

**Expected Performance (from Python optimizer):**
| Metric | Value |
|--------|-------|
| Win Rate | 91.8% |
| Profit Factor | 111.96 |
| Max Drawdown | 0.05% |
| Total Trades | 764 |
| Avg Win | 12.59 |
| Avg Loss | -1.25 |
| Expectancy | 11.447 |

---

## 7. Risk Management Integration

### Pre-Trade Checks

Every signal must pass ALL of these before execution:

```python
def validate_signal(signal, account_info, positions):
    # 1. Daily loss limit
    if daily_pnl <= -account_info.equity * 0.004:
        return False, "Daily loss limit hit"
    
    # 2. Concurrent risk limit
    current_risk = sum(pos.risk_pct for pos in positions)
    if current_risk + signal.risk_pct > 0.0036:
        return False, "Concurrent risk limit"
    
    # 3. Correlation check
    if signal.symbol in ["EURUSD", "GBPUSD"]:
        correlated = [p for p in positions if p.symbol in ["EURUSD", "GBPUSD"]]
        if correlated and correlated[0].direction != signal.direction:
            return False, "Correlation conflict"
    
    # 4. Tier filter
    if signal.tier == "NO_GO":
        return False, "NO-GO tier"
    
    # 5. Time filter
    if not (2 <= signal.est_hour < 11):
        return False, "Outside entry window"
    
    # 6. News filter (manual — requires news calendar integration)
    # if news_within_4_hours(signal.timestamp):
    #     return False, "News filter"
    
    return True, "OK"
```

### Position Sizing Formula

```python
def calculate_position_size(account_equity, risk_pct, sl_pips, pip_value=10.0):
    """
    Calculate lot size based on risk parameters.
    
    For EUR/USD: 1 lot = $10/pip, 0.1 lot = $1/pip, 0.01 lot = $0.1/pip
    """
    risk_amount = account_equity * risk_pct
    lot_size = risk_amount / (sl_pips * pip_value)
    return round(lot_size, 2)  # Round to 0.01 lot
```

---

## 8. Error Handling & Recovery

### Error Classification

| Error Type | Examples | Recovery Action |
|------------|----------|-----------------|
| Connection | MT5 not running, login failed | Auto-reconnect (3 attempts, 5s delay) |
| Order Reject | Insufficient margin, invalid price | Log, skip signal, alert operator |
| Timeout | Order not filled in 5 seconds | Cancel and retry once |
| Data Error | Missing bars, invalid ticks | Re-fetch data, skip if persistent |
| System | Python crash, OS error | Log state, restart from last checkpoint |

### Reconnection Logic

```python
async def reconnect(max_attempts=3, delay=5):
    for attempt in range(max_attempts):
        mt5.shutdown()
        await asyncio.sleep(delay)
        if mt5.initialize():
            return True
    return False
```

### State Persistence

All trading state is persisted to `quant-lab/mt5/state.json` after every trade:
- Open positions (ticket, symbol, direction, entry, SL, TP)
- Daily P&L
- Signal history
- Error log

On restart, the connector reads state.json and reconciles with actual MT5 positions.

---

## 9. How to Run DMR Backtest on MT5

### Prerequisites

1. ✅ MT5 terminal running and logged in
2. ✅ MetaTrader5 Python package installed (`pip install MetaTrader5`)
3. ✅ Historical data available in MT5 (EUR/USD M5, Jan 2022+)
4. ✅ Sufficient history loaded (check via Tools → History Center)

### Step-by-Step

**Step 1: Verify MT5 Connection**
```bash
cd quant-lab/mt5
python -c "import MetaTrader5 as mt5; mt5.initialize(); print(mt5.account_info()); mt5.shutdown()"
```

**Step 2: Run DMR Backtest**
```bash
python dmr_mt5_backtest.py --symbol EURUSD --timeframe M5 --start 2022.01.01 --end 2026.04.30
```

**Step 3: Review Results**
```bash
# Results saved to quant-lab/mt5/results/
cat results/dmr_mt5_backtest_YYYYMMDD_HHMMSS.json
```

**Step 4: Compare with Python Optimizer**
```bash
python compare_results.py \
    --mt5 results/dmr_mt5_backtest_YYYYMMDD_HHMMSS.json \
    --python ../results/optimizer_v4b_20260517_193302.json
```

### Expected Output Format

```json
{
  "strategy": "Deep_Mean_Reversion",
  "source": "MT5_Backtest",
  "symbol": "EURUSD",
  "timeframe": "M5",
  "period": "2022.01.01 - 2026.04.30",
  "total_trades": 764,
  "wins": 701,
  "losses": 63,
  "win_rate": 91.8,
  "total_pnl": 8745.68,
  "avg_win": 12.59,
  "avg_loss": -1.25,
  "max_dd": -5.02,
  "max_dd_pct": 0.05,
  "profit_factor": 111.96,
  "expectancy": 11.447,
  "by_exit": {
    "tp": 700,
    "sl": 63,
    "end_data": 1
  }
}
```

---

## 10. File-Based Fallback

When the MT5 Python API is unavailable (e.g., MT5 on a different machine), use file-based signal passing.

### Directory Structure

```
MT5 Terminal/MQL5/Files/
├── signals/
│   ├── signal_YYYYMMDD_HHMMSS.json   (Python → MT5)
│   └── ...
├── results/
│   ├── trade_YYYYMMDD_HHMMSS.json    (MT5 → Python)
│   └── ...
└── status/
    ├── connector_status.json         (Heartbeat)
    └── ea_status.json                (EA state)
```

### Signal File Format

```json
{
  "id": "DMR_20260519_073000",
  "timestamp": "2026-05-19T07:30:00-05:00",
  "symbol": "EURUSD",
  "action": "BUY",
  "volume": 0.1,
  "entry_type": "MARKET",
  "entry_price": null,
  "stop_loss": 1.08480,
  "take_profit": 1.08700,
  "strategy": "DMR",
  "metadata": {
    "tier": "T1",
    "asian_range_pips": 15.3,
    "p90_body_pips": 5.2,
    "asian_high": 1.08500,
    "asian_low": 1.08347
  }
}
```

### MT5 EA for File Reading

An MQL5 EA (`CEREBus_Signal_Reader.mq5`) runs on a chart and:
1. Polls `signals/` directory every 5 seconds
2. Reads new signal files
3. Executes trades via `OrderSend()`
4. Writes trade results to `results/`
5. Deletes processed signal files

---

## 11. Implementation Roadmap

### Phase 1: Foundation (This Sprint)
- ✅ MT5 connection verified
- ✅ Architecture document complete
- ⬜ MT5Client class implementation
- ⬜ DMR backtest script
- ⬜ Results comparison tool

### Phase 2: Backtest Validation
- Run DMR backtest on MT5
- Compare with Python optimizer results
- Tune MT5 parameters to match Python results
- Document any discrepancies

### Phase 3: Forward Testing
- Deploy signal reader EA on MT5 demo account
- Run paper trading for 2 weeks
- Monitor execution quality (slippage, fill rates)
- Validate risk management

### Phase 4: Live Trading
- Connect to live demo account
- Start with minimum position size (0.01 lots)
- Monitor for 1 week
- Scale up gradually

### Phase 5: ML Refinement
- Apply ML to underperforming strategies (see ML_REFINEMENT_PLAN.md)
- NOT applied to DMR or Composite_Alpha (already high-performing)
- Target: Blind_Structural_Chain, Fractal_Resolution, Two_Plays, P90P_Distribution

---

## 12. Appendix: MT5 API Reference

### Key MT5 Python API Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `mt5.initialize()` | Connect to MT5 terminal | bool |
| `mt5.shutdown()` | Disconnect | None |
| `mt5.version()` | Get MT5 version | (build, build_date, version_string) |
| `mt5.account_info()` | Account details | AccountInfo namedtuple |
| `mt5.symbol_info(symbol)` | Symbol details | SymbolInfo namedtuple |
| `mt5.symbol_info_tick(symbol)` | Current tick | Tick namedtuple |
| `mt5.copy_rates_from_pos(symbol, tf, pos, count)` | Historical bars | numpy array |
| `mt5.copy_rates_range(symbol, tf, from, to)` | Historical bars by date | numpy array |
| `mt5.order_send(request)` | Submit order | TradeRequest result |
| `mt5.positions_get(symbol=None)` | Open positions | tuple of Position |
| `mt5.history_orders_get(date_from, date_to)` | Order history | tuple of Order |
| `mt5.history_deals_get(date_from, date_to)` | Deal history | tuple of Deal |
| `mt5.last_error()` | Last error code | dict |

### Order Request Structure

```python
request = {
    "action": mt5.TRADE_ACTION_DEAL,        # Immediate execution
    "symbol": "EURUSD",
    "volume": 0.1,
    "type": mt5.ORDER_TYPE_BUY,             # or ORDER_TYPE_SELL
    "price": 1.08520,                        # Current ask for BUY
    "sl": 1.08480,                          # Stop loss
    "tp": 1.08700,                          # Take profit
    "deviation": 10,                         # Slippage tolerance (points)
    "magic": 123456,                         # Magic number (strategy ID)
    "comment": "DMR_T1",
    "type_time": mt5.ORDER_TIME_GTC,        # Good till cancel
    "type_filling": mt5.ORDER_FILLING_IOC,  # Immediate or cancel
}
```

### Timeframe Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `mt5.TIMEFRAME_M1` | 1 | 1 minute |
| `mt5.TIMEFRAME_M5` | 5 | 5 minutes |
| `mt5.TIMEFRAME_M15` | 15 | 15 minutes |
| `mt5.TIMEFRAME_M30` | 30 | 30 minutes |
| `mt5.TIMEFRAME_H1` | 16408 | 1 hour |
| `mt5.TIMEFRAME_H4` | 16412 | 4 hours |
| `mt5.TIMEFRAME_D1` | 16416 | 1 day |

---

*Document Version 1.0 — MT5 Integration Engineer — 2026-05-19*
*Next Review: After Phase 1 implementation complete*
