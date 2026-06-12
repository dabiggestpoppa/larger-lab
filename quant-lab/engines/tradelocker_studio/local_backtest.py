"""
Local backtest using TradeLocker's official Python SDK.
Fetches historical data from TradeLocker REST API and runs our
CEREBUS Symmetry Trap strategy against it.

This is the RELIABLE approach — no CDP, no DOM scraping.
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# Ensure repo root is on path
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

os.environ["PYTHONIOENCODING"] = "utf-8"

from tradelocker import TLAPI

# ── Config ──
EMAIL = "kemettrucking@gmail.com"
# We need the password — check .env file
env_file = Path(__file__).parent.parent.parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.startswith("TL_PASSWORD="):
            PASSWORD = line.split("=", 1)[1].strip()
            break
    else:
        PASSWORD = None
else:
    PASSWORD = None

if not PASSWORD:
    print("ERROR: No password found. Set TL_PASSWORD in .env file")
    print("Or run: $env:TL_PASSWORD='your_password'; python local_backtest.py")
    PASSWORD = os.environ.get("TL_PASSWORD", "")

if not PASSWORD:
    print("ERROR: No password available. Set TL_PASSWORD environment variable.")
    sys.exit(1)

SERVER = "AQUA"
ENVIRONMENT = "https://demo.tradelocker.com"

# ── Connect ──
print("Connecting to TradeLocker API...")
tl = TLAPI(
    environment=ENVIRONMENT,
    username=EMAIL,
    password=PASSWORD,
    server=SERVER,
)
print(f"  Connected! Account: {tl}")

# ── Get instruments ──
print("\nFetching instruments...")
instruments = tl.get_all_instruments()
print(f"  Found {len(instruments)} instruments")

# Find EURUSD
eurusd_id = None
for inst in instruments:
    if inst.get("symbolName") == "EURUSD" or inst.get("name") == "EURUSD":
        eurusd_id = inst.get("tradableInstrumentId") or inst.get("id")
        break

if not eurusd_id:
    # Try from symbol name
    eurusd_id = tl.get_instrument_id_from_symbol_name("EURUSD")

print(f"  EURUSD instrument ID: {eurusd_id}")

# ── Fetch historical data ──
print("\nFetching EURUSD M5 history...")
try:
    # Get 30 days of M5 data
    history = tl.get_price_history(
        eurusd_id,
        resolution="5m",
        start_timestamp=0,
        end_timestamp=0,
        lookback_period="30D",
    )
    print(f"  Fetched {len(history)} M5 bars")
    if len(history) > 0:
        print(f"  First bar: {history[0]}")
        print(f"  Last bar: {history[-1]}")
except Exception as e:
    print(f"  Error fetching history: {e}")
    # Try alternative resolution
    try:
        history = tl.get_price_history(
            eurusd_id,
            resolution="1D",
            start_timestamp=0,
            end_timestamp=0,
            lookback_period="365D",
        )
        print(f"  Fetched {len(history)} D1 bars (fallback)")
    except Exception as e2:
        print(f"  Fallback error: {e2}")
        sys.exit(1)

# ── Convert to our Bar format ──
from engines.symmetry_trap import Bar

bars = []
for h in history:
    # TradeLocker bar format: check actual keys
    if isinstance(h, dict):
        ts = h.get("t") or h.get("timestamp") or h.get("date") or h.get("datetime")
        o = h.get("o") or h.get("open")
        hi = h.get("h") or h.get("high")
        lo = h.get("l") or h.get("low")
        c = h.get("c") or h.get("close")
        
        if ts and o and hi and lo and c:
            if isinstance(ts, (int, float)):
                dt = datetime.utcfromtimestamp(ts / 1000 if ts > 1e12 else ts)
            else:
                dt = datetime.strptime(str(ts)[:19], "%Y-%m-%d %H:%M:%S")
            
            bars.append(Bar(
                timestamp=dt,
                open=float(o),
                high=float(hi),
                low=float(lo),
                close=float(c),
            ))

print(f"  Converted {len(bars)} bars to internal format")

if len(bars) < 100:
    print("ERROR: Not enough data for backtest")
    sys.exit(1)

# ── Run Symmetry Trap backtest ──
print("\n" + "=" * 70)
print("RUNNING CEREBUS SYMMETRY TRAP BACKTEST")
print("=" * 70)

from engines.symmetry_trap_backtest import SymmetryTrapBacktest

bt = SymmetryTrapBacktest(
    pip_size=0.0001,
    symbol="EURUSD",
)

result = bt.run(bars)

# ── Print results ──
from engines.symmetry_trap_backtest import format_report
print(format_report(result))

# ── Save results ──
output_path = Path("quant-lab/engines/tradelocker_studio/backtest_results.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
results = {
    "source": "TradeLocker REST API",
    "symbol": "EURUSD",
    "engine": "CEREBUS Symmetry Trap v4.0",
    "total_trades": result.total_trades,
    "win_rate": result.win_rate,
    "pnl_pips": result.total_pnl_pips,
    "profit_factor": result.profit_factor,
    "sharpe_ratio": result.sharpe_ratio,
    "max_drawdown_pips": result.max_drawdown_pips,
    "tier_stats": result.tier_stats,
    "hourly_stats": result.hourly_stats,
    "data_bars": len(bars),
    "data_days": result.data_days,
}
output_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
print(f"\nResults saved to {output_path}")

print("\n" + "=" * 70)
print("BACKTEST COMPLETE")
print("=" * 70)
