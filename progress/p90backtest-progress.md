# P90 Backtest Engine — Progress

**Date:** 2026-05-29  
**Status:** COMPLETE  
**File:** `quant-lab/engines/p90_backtest.py`

## Deliverables

### Created Files
- `quant-lab/engines/p90_backtest.py` — Full backtest harness (331 lines)

### Features Implemented

1. **CSV Loading** (`load_bars_csv`)
   - Flexible column matching (timestamp/time/date, open/Open/OPEN, etc.)
   - Auto-detects 11+ timestamp formats (ISO 8601, US, EU, etc.)
   - UTF-8 BOM handling, sorted output

2. **Session Grouping** (`group_by_session`)
   - Asian session: 19:00-03:00 EST (UTC-5)
   - Trading window: 03:00-12:00 EST
   - Session date assignment: evening bars roll to next day

3. **Backtest Pipeline** (`run_backtest`)
   - Per-session: calc Asian Range → `engine.initialize_session()` → feed bars
   - Collects `P90Signal` events from `engine.signal_log`

4. **Statistics** (`compute_stats`)
   - Total trades, wins, losses, win rate %
   - Gross profit, gross loss, profit factor
   - Max drawdown (pip-based equity curve)
   - Average trade (pips)
   - Per-variant breakdown: INITIAL / CASCADE / STALL_HARVEST (trade count + WR + PnL)

5. **Reporting** (`print_report`)
   - Formatted console output with per-variant table

6. **CLI** (`argparse`)
   - `--csv` (required): path to M5 CSV
   - `--symbol` (default: EURUSD)
   - `--pip-size` (default: 0.0001)

## Verification

```
SYNTAX OK: python ast.parse() — PASS
IMPORT OK: from p90_backtest import run_backtest — PASS
LOAD OK: load_bars_csv with 18-bar test data — PASS
SESSIONS OK: group_by_session identifies session boundaries — PASS
PIPELINE OK: run_backtest executes end-to-end — PASS
```

## Import Path Note
The backtest uses `from p90_engine import (...)` (sibling import within `quant-lab/engines/`).
This works when run from `quant-lab/engines/` or with `quant-lab/engines/` on `PYTHONPATH`.
Consistent with the existing pattern used by `run_backtest.py` in the same project.
