# Symmetry Trap — Canonical Call Graph

## Source of Truth
**Canonical Backtest Engine:** `quant-lab/engines/symmetry_trap_backtest.py`
- Class: `SymmetryTrapBacktest`
- Method: `run(bars)` → `BacktestResult`
- Method: `run_from_csv(filepath)` → `BacktestResult`
- Method: `run_multi_pair(filepaths)` → `Dict[str, BacktestResult]`

## Core Engine (Shared)
**File:** `quant-lab/engines/symmetry_trap.py`
- Class: `SymmetryTrapEngine`
- Method: `initialize_session(asian_high, asian_low)` — session init
- Method: `process_bar(bar)` → `TradeSignal` — main state machine
- Method: `_find_asian_range(day_bars)` — Asian Range calculation
- Method: `_classify_tier_by_impulse()` — tier classification by impulse size
- Method: `_reset_state_keep_loop()` — state reset after trade
- Method: `_reset_state()` — full state reset

## Data Structures
- `Bar` — timestamp, open, high, low, close
- `TradeSignal` — event, direction, entry_price, sl_price, tp_price, au_used, timestamp, reason, loop_count
- `TradeRecord` — entry/exit times, direction, prices, result, pnl_pips, ar_pips, tier, au_pips, impulse_size_pips, est_hour, loop_count
- `BacktestResult` — aggregated statistics

## Canonical Backtest Flow

```
load_m5_csv(filepath)
    ↓
bars = List[Bar] (sorted by timestamp)
    ↓
group by EST date → Dict[date, List[Bar]]
    ↓
for each session_date:
    day_bars = sorted bars for that date
    asian_high, asian_low = _find_asian_range(day_bars)
    engine.initialize_session(asian_high, asian_low)
    if not engine.session_active: continue
    
    for bar in day_bars:
        bar_est_h = _get_est_hour(bar.timestamp)
        if bar_est_h >= 19 or bar_est_h < 3: continue  # Skip Asian hours
        if bar_est_h >= 16 and engine.state == SEARCH: break  # 4PM cutoff
        
        signal = engine.process_bar(bar)
        
        if signal is None:
            if active_trade and engine.entry_price is None:
                # trade closed without signal
                record trade
            continue
            
        if signal.event == "ENTRY":
            create TradeRecord with signal data
        elif signal.event in ("TP_HIT", "SL_HIT"):
            close active_trade with signal prices
            apply_costs_to_pnl()
            record trade
        elif signal.event == "KILL_SWITCH":
            close active_trade if exists
            record kill
```

## Key Canonical Logic Points

### 1. Asian Range Calculation (`_find_asian_range`)
```python
def _find_asian_range(self, day_bars: List[Bar]) -> Tuple[float, float]:
    ah, al = 0.0, 99999.0
    for b in day_bars:
        h = self._get_est_hour(b.timestamp)
        if h >= 19 or h < 3:  # 19:00-03:00 EST
            ah = max(ah, b.high)
            al = min(al, b.low)
    return ah, al
```

### 2. Session Initialization (`initialize_session`)
```python
def initialize_session(self, asian_high: float, asian_low: float):
    self.asian_high = asian_high
    self.asian_low = asian_low
    self.asian_range_pips = (asian_high - asian_low) / self.pip_size
    
    # AR gate: session filter only (ar_max=60 for all tiers)
    ar_max = self.tier_config.get("T1", {}).get("ar_max", 60.0)
    if self.asian_range_pips > ar_max:
        self.tier_name = "NO_GO"
        self.session_active = False
    else:
        self.tier_name = "T1"  # Default, reclassified by impulse
        cfg = self.tier_config.get("T1", {"au": 10.0, "trigger": 12.0})
        self.au_pips = cfg["au"]
        self.trigger_pips = cfg["trigger"]
        self.session_active = True
    
    self.active_au = self.au_pips * self.pip_size
    # Reset state machine
    self.state = EngineState.SEARCH
    self.swing_origin = None
    self.impulse_direction = TradeDirection.FLAT
    self.impulse_extreme = 0.0
    self.impulse_size_pips = 0.0
    self.kill_switch_level = 0.0
    self.entry_price = None
    self.sl_price = None
    self.tp_price = None
    self.loop_count = 1
    self.loop_start_time = None
    self.cascade_bias = None
```

### 3. Tier Classification (`_classify_tier_by_impulse`)
```python
def _classify_tier_by_impulse(self):
    t1_cfg = self.tier_config.get("T1", {})
    t2_cfg = self.tier_config.get("T2", {})
    t3_cfg = self.tier_config.get("T3", {})
    t2_trigger = t2_cfg.get("trigger", 30.0)
    t3_trigger = t3_cfg.get("trigger", 45.0)
    
    if self.impulse_size_pips < t2_trigger:
        tier_name = "T1"
    elif self.impulse_size_pips <= t3_trigger:
        tier_name = "T2"
    else:
        tier_name = "T3"
    
    cfg = self.tier_config.get(tier_name, t1_cfg)
    self.tier_name = tier_name
    self.au_pips = cfg["au"]
    self.trigger_pips = cfg["trigger"]
    self.active_au = self.au_pips * self.pip_size
```

### 4. State Machine (`process_bar`)
**SEARCH** → impulse breach ≥ trigger → set impulse_extreme, classify tier → **WAIT_RETRACE**
**WAIT_RETRACE** → pullback ≥ 1 AU OR 20-50% fib → **WAIT_OCC**
**WAIT_OCC** → OCC candle close in impulse direction → set entry/sl/tp → **IN_TRADE**
**IN_TRADE** → TP hit (wick or close) OR SL hit (wick-based) → reset state, increment loop

### 5. SL/TP Logic
- **SL** = `self.impulse_extreme` (exact impulse bar high/low, zero-buffer, wick-based)
- **TP** = entry ± 1 AU (single target, no ladder)
- **Kill Switch** = REMOVED (dead code per June 4 optimization)

### 6. Cost Application
```python
from trading_costs import apply_costs_to_pnl
net_pnl = apply_costs_to_pnl(gross_pnl_pips, symbol, direction, lot_size)
```

### 7. Time Handling
```python
def _get_est_hour(self, dt: datetime) -> int:
    return (dt.hour + self.est_offset) % 24  # est_offset = -5
```

## Live Wrapper Path (Current)

```
mt5/symmetry_trap_executor_multi.py (orchestration)
    ↓ run_live_scan()
engines/symmetry_trap_live.py (SymmetryTrapLiveEngine)
    ↓ refresh_data()
engines/mt5_data_feed.py
    ↓ fetch_m5_bars() → List[Bar]
    ↓ build_today_bars() → today_bars, today_est, yesterday_est
    ↓ calculate_asian_range() → asian_high, asian_low, ar_pips
    ↓ filter_trading_bars() → trading_bars
    ↓
SymmetryTrapLiveEngine.backtest_engine.engine.initialize_session()
    ↓
for bar in trading_bars:
    signal = engine.process_bar(bar)
    ↓
collect signal
```

## Critical Divergence Points to Audit

| # | Component | Backtest | Live Wrapper | Risk |
|---|-----------|----------|--------------|------|
| 1 | Time source | Bar timestamps only | `get_current_est_hour()` from latest bar | HIGH |
| 2 | Asian Range | `_find_asian_range()` in backtest | `calculate_asian_range()` in data feed (duplicate) | HIGH |
| 3 | Session init | Once per session day | Each scan cycle | HIGH |
| 4 | State reset | Canonical `_reset_state_keep_loop()` | Same engine, but init differs | MEDIUM |
| 5 | Pip value | `config["pip_value"]` | `get_symbol_pip_size()` → same source | LOW |
| 6 | Costs | `apply_costs_to_pnl()` | Same function | LOW |
| 7 | Bar objects | `Bar` from CSV | `Bar` from MT5 rates | MEDIUM |
| 8 | Session date | `est_dt.date()` from bar | `build_today_bars()` logic | HIGH |
| 9 | Trading window | 2-11 EST, 4PM cutoff | Same constants | LOW |
| 10 | Signal loop | All day_bars sequentially | Only trading_bars (2-11 EST) | MEDIUM |

## Required Artifacts for Parity Test

1. `artifacts/symmetry_trap/parity_baseline.json` ✅ (file hashes)
2. `artifacts/symmetry_trap/canonical_call_graph.md` ✅ (this document)
3. `artifacts/symmetry_trap/backtest_trace.csv` — to generate
4. `artifacts/symmetry_trap/live_trace.csv` — to generate
5. `artifacts/symmetry_trap/parity_diff.csv` — to generate
6. `artifacts/symmetry_trap/timezone_parity.csv` — to generate
7. `artifacts/symmetry_trap/config_parity.json` — to generate