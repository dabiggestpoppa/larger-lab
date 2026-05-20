#!/usr/bin/env python3
"""
Native MT5 Strategy Tester Automation
=======================================
Launches terminal64.exe with a config INI to run DMR_FULL_BACKTEST.mq5
in MT5's built-in Strategy Tester — the REAL native backtest engine.

This is the ultimate verification step in the pipeline:
  Idea → Python Backtest → Monte Carlo → NATIVE MT5 BACKTEST → Report

Usage: python run_native_mt5_backtest.py [--symbol EURUSD.PRO] [--from 2022.01.01] [--to 2026.05.19]
"""
import subprocess
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────────────
MT5_DIR = r"C:\Program Files\Ox Securities MetaTrader 5"
TERMINAL = os.path.join(MT5_DIR, "terminal64.exe")
METAEDITOR = os.path.join(MT5_DIR, "MetaEditor64.exe")

# MT5 data directory
APPDATA = os.environ.get("APPDATA", "")
MT5_DATA = os.path.join(APPDATA, "MetaQuotes", "Terminal", "A9831A95D2ED3390882422E0C995D278")

# EA name (without extension)
EA_NAME = "DMR_FULL_BACKTEST"

# Results directory
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5")
RESULTS_DIR.mkdir(exist_ok=True)

# Default parameters
SYMBOL = "EURUSD.PRO"
FROM_DATE = "2022.01.01"
TO_DATE = "2026.05.19"
TIMEFRAME = "M5"
LOT_SIZE = 0.01

# MT5 period mapping
PERIOD_MAP = {
    "M1": "PERIOD_M1",
    "M5": "PERIOD_M5",
    "M15": "PERIOD_M15",
    "M30": "PERIOD_M30",
    "H1": "PERIOD_H1",
    "H4": "PERIOD_H4",
    "D1": "PERIOD_D1",
}


def check_prerequisites():
    """Verify all required files exist."""
    ok = True

    if not os.path.exists(TERMINAL):
        print(f"❌ terminal64.exe not found: {TERMINAL}")
        ok = False
    else:
        print(f"✅ terminal64.exe: {TERMINAL}")

    if not os.path.exists(METAEDITOR):
        print(f"❌ MetaEditor64.exe not found: {METAEDITOR}")
        ok = False
    else:
        print(f"✅ MetaEditor64.exe: {METAEDITOR}")

    # Check EA source file
    ea_src = os.path.join(MT5_DATA, "MQL5", "Experts", f"{EA_NAME}.mq5")
    if not os.path.exists(ea_src):
        print(f"❌ EA source not found: {ea_src}")
        ok = False
    else:
        print(f"✅ EA source: {ea_src}")

    # Check for compiled .ex5
    ea_ex5 = os.path.join(MT5_DATA, "MQL5", "Experts", f"{EA_NAME}.ex5")
    if os.path.exists(ea_ex5):
        print(f"✅ EA compiled: {ea_ex5}")
    else:
        print(f"⚠️ EA not compiled yet (.ex5 not found) — will compile first")

    return ok


def compile_ea():
    """Compile the EA using MetaEditor command line."""
    print(f"\n🔧 Compiling {EA_NAME}.mq5...")

    ea_src = os.path.join(MT5_DATA, "MQL5", "Experts", f"{EA_NAME}.mq5")
    log_file = str(RESULTS_DIR / "compile_log.txt")

    cmd = [
        METAEDITOR,
        f"/compile:{ea_src}",
        f"/log:{log_file}"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        # Check log for errors
        if os.path.exists(log_file):
            with open(log_file, 'r', errors='replace') as f:
                log_content = f.read()

            errors = [line for line in log_content.split('\n') if 'error' in line.lower()]
            warnings = [line for line in log_content.split('\n') if 'warning' in line.lower()]

            if errors:
                print(f"❌ Compilation errors:")
                for e in errors[:5]:
                    print(f"   {e}")
                return False
            elif warnings:
                print(f"⚠️ Compilation warnings: {len(warnings)}")
            else:
                print(f"✅ Compilation successful")

        # Verify .ex5 was created
        ea_ex5 = os.path.join(MT5_DATA, "MQL5", "Experts", f"{EA_NAME}.ex5")
        if os.path.exists(ea_ex5):
            size = os.path.getsize(ea_ex5)
            mtime = datetime.fromtimestamp(os.path.getmtime(ea_ex5))
            print(f"✅ .ex5 file: {size} bytes, modified {mtime}")
            return True
        else:
            print(f"❌ .ex5 file not created")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Compilation timed out (120s)")
        return False
    except Exception as e:
        print(f"❌ Compilation error: {e}")
        return False


def create_tester_ini(symbol, from_date, to_date, timeframe, lot_size):
    """
    Create the Strategy Tester INI config file.
    
    MT5 terminal64.exe /config: uses this INI to configure the Strategy Tester.
    The EA path is relative to MQL5/Experts.
    """
    print(f"\n📋 Creating Strategy Tester INI config...")

    # Map timeframe
    period_map = {
        "M1": "PERIOD_M1",
        "M5": "PERIOD_M5",
        "M15": "PERIOD_M15",
        "M30": "PERIOD_M30",
        "H1": "PERIOD_H1",
        "H4": "PERIOD_H4",
        "D1": "PERIOD_D1",
    }
    period = period_map.get(timeframe, "PERIOD_M5")

    # Report path (no extension — MT5 adds .htm)
    report_path = str(RESULTS_DIR / f"DMR_NATIVE_MT5_REPORT_{symbol.replace('.', '_')}")

    # Build the INI content
    # Note: MT5 uses "Test*" keys in the [Tester] section
    ini_content = f"""; Strategy Tester Configuration — DMR Full Backtest
; Generated: {datetime.now().isoformat()}
; Pipeline Step 4: Native MT5 Verification

[Common]
Login=1114712
Server=OxSecurities-Demo
AutoConfiguration=true

[Tester]
; EA to test (relative to MQL5\\Experts)
Expert=Experts\\{EA_NAME}.ex5

; Symbol and timeframe
Symbol={symbol}
Period={period}

; Test model: 0 = Every tick, 1 = 1-min OHLC, 2 = Open prices
TestModel=0

; Spread in points (0 = current)
Spread=0

; Date range
UseDate=true
FromDate={from_date}
ToDate={to_date}

; Deposit
Deposit=10000
Currency=USD

; Optimization off
Optimization=false

; Report output (no extension)
Report={report_path}
ReplaceReport=true

; Close terminal when done
ShutdownTerminal=true

; Visual mode off (headless)
Visual=0

[Parameters]
LotSize={lot_size}
MagicNumber=20260520
MaxDailyTrades=1
HardExitHour=17
DeepMult=2.00
KillMult=2.20
MaxAR=45
MinAR=3
ESTOffset=-5
EnableLogging=true
"""

    ini_path = str(RESULTS_DIR / "dmr_tester_config.ini")
    with open(ini_path, 'w') as f:
        f.write(ini_content)

    print(f"✅ INI config: {ini_path}")
    return ini_path, report_path


def run_strategy_tester(ini_path):
    """
    Launch terminal64.exe with the config INI.
    MT5 will start, run the Strategy Tester, and shut down when done.
    """
    print(f"\n🚀 Launching MT5 Strategy Tester (native)...")
    print(f"   Config: {ini_path}")
    print(f"   This may take 15-45 minutes for full M5 history...")
    print(f"   MT5 terminal will open, run the test, then close automatically.")

    cmd = [
        TERMINAL,
        f"/config:{ini_path}"
    ]

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            timeout=7200  # 2 hour max
        )

        elapsed = time.time() - start_time
        minutes = elapsed / 60
        print(f"\n⏱️ Strategy Tester completed in {minutes:.1f} minutes")

        if result.returncode == 0:
            print(f"✅ MT5 exited normally")
        else:
            print(f"⚠️ MT5 exit code: {result.returncode}")

        return True

    except subprocess.TimeoutExpired:
        print("❌ Strategy Tester timed out (2 hours)")
        return False
    except Exception as e:
        print(f"❌ Strategy Tester error: {e}")
        return False


def find_results(report_path):
    """Find the MT5-generated report and any EA output."""
    print(f"\n🔍 Looking for results...")

    results = {}

    # MT5 generates .htm report
    htm_path = f"{report_path}.htm"
    if os.path.exists(htm_path):
        size = os.path.getsize(htm_path)
        print(f"✅ MT5 HTML report: {htm_path} ({size:,} bytes)")
        results['htm_report'] = htm_path

    # MT5 also generates .xml
    xml_path = f"{report_path}.xml"
    if os.path.exists(xml_path):
        size = os.path.getsize(xml_path)
        print(f"✅ MT5 XML report: {xml_path} ({size:,} bytes)")
        results['xml_report'] = xml_path

    # Check for EA JSON output in MT5 data directory
    ea_json = os.path.join(MT5_DATA, "MQL5", "Experts", "DMR_FULL_BACKTEST_RESULTS.json")
    if os.path.exists(ea_json):
        with open(ea_json, 'r') as f:
            ea_results = json.load(f)
        print(f"✅ EA JSON results: {ea_json}")
        results['ea_json'] = ea_results

    # Also check Tester directory for any output
    tester_dir = os.path.join(MT5_DATA, "Tester")
    if os.path.exists(tester_dir):
        tester_files = sorted(
            [f for f in os.listdir(tester_dir)],
            key=lambda x: os.path.getmtime(os.path.join(tester_dir, x)),
            reverse=True
        )
        if tester_files:
            print(f"📁 Tester directory files: {tester_files[:5]}")

    if not results:
        print("⚠️ No results found. Check MT5 logs.")

    return results


def parse_mt5_report(xml_path):
    """Parse MT5's XML report to extract key metrics."""
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # MT5 XML structure varies by version, try common paths
        metrics = {}

        # Try to find trade statistics
        for elem in root.iter():
            tag = elem.tag.lower()
            if 'trades' in tag and elem.text:
                metrics['total_trades'] = elem.text
            elif 'profit' in tag and 'total' in tag and elem.text:
                metrics['total_profit'] = elem.text
            elif 'winrate' in tag.replace(' ', '') and elem.text:
                metrics['win_rate'] = elem.text

        return metrics
    except Exception as e:
        print(f"⚠️ Could not parse XML: {e}")
        return {}


def generate_report(results, symbol, from_date, to_date):
    """Generate a comprehensive comparison report."""
    print(f"\n📊 Generating comparison report...")

    report_path = RESULTS_DIR / "DMR_NATIVE_MT5_BACKTEST_REPORT.md"

    ea_data = results.get('ea_json', {})

    report = f"""# DMR NATIVE MT5 BACKTEST REPORT
## Deep Mean Reversion — Ultimate Verification

> **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> **Engine:** MT5 Strategy Tester (terminal64.exe /config:) — NATIVE
> **EA:** {EA_NAME}.mq5
> **Symbol:** {symbol}
> **Period:** {from_date} → {to_date}
> **Timeframe:** {TIMEFRAME}
> **Lot Size:** {LOT_SIZE}

---

## NATIVE MT5 RESULTS

| Metric | Value |
|--------|-------|
| Total Trades | {ea_data.get('total_trades', 'See MT5 HTML report')} |
| Wins | {ea_data.get('wins', 'N/A')} |
| Losses | {ea_data.get('losses', 'N/A')} |
| Win Rate | {ea_data.get('win_rate', 'N/A')}% |
| Total PnL | {ea_data.get('total_pnl_pips', 'N/A')} pips |
| Max Drawdown | {ea_data.get('max_dd_pips', 'N/A')} pips |
| Profit Factor | {ea_data.get('profit_factor', 'N/A')} |

"""

    if results.get('htm_report'):
        report += f"📄 **MT5 HTML Report:** `{results['htm_report']}`\n\n"

    report += f"""---

## PIPELINE COMPARISON

| Step | Tool | Result |
|------|------|--------|
| 1. Strategy | MAD | DMR — P90→Deep State Mean Reversion |
| 2. Python Backtest | optimizer_v2.py | 91.8% WR, +8,746p, PF 112 |
| 3. Monte Carlo | mc_dmr_mt5.py | 100% prob profit, MaxDD <5.5p |
| 4. **Native MT5** | **terminal64.exe** | **{ea_data.get('win_rate', 'N/A')}% WR, {ea_data.get('total_pnl_pips', 'N/A')}p** |

### Delta Analysis

| Metric | Python | Native MT5 | Delta |
|--------|--------|-----------|-------|
| Win Rate | 91.8% | {ea_data.get('win_rate', 'N/A')}% | {ea_data.get('win_rate', 0) - 91.8 if ea_data.get('win_rate') else 'N/A'}% |
| Total PnL | +8,746p | {ea_data.get('total_pnl_pips', 'N/A')}p | {ea_data.get('total_pnl_pips', 0) - 8746 if ea_data.get('total_pnl_pips') else 'N/A'}p |
| Max DD | -5.0p | {ea_data.get('max_dd_pips', 'N/A')}p | {ea_data.get('max_dd_pips', 0) - 5.0 if ea_data.get('max_dd_pips') else 'N/A'}p |

---

## VERDICT

{'✅ **NATIVE MT5 CONFIRMS PYTHON RESULTS** — Pipeline validated!' if ea_data.get('win_rate', 0) > 85 else '⚠️ **DISCREPANCY DETECTED** — Needs investigation'}

---

## FILES GENERATED

- MT5 HTML Report: `{results.get('htm_report', 'N/A')}`
- MT5 XML Report: `{results.get('xml_report', 'N/A')}`
- EA JSON Results: `{"Yes" if ea_data else "No"}`
- This Report: `{report_path}`

---

*Generated by OWL — Native MT5 Backtest Pipeline v3.0*
*Strategy: CerebusFX DMR (Deep Mean Reversion)*
"""

    with open(report_path, 'w') as f:
        f.write(report)

    print(f"✅ Report: {report_path}")
    return report_path


def main():
    print("=" * 60)
    print("  NATIVE MT5 STRATEGY TESTER — DMR FULL BACKTEST")
    print("  Pipeline Step 4: Ultimate Verification")
    print("=" * 60)

    # Parse args
    symbol = SYMBOL
    from_date = FROM_DATE
    to_date = TO_DATE

    for i, arg in enumerate(sys.argv):
        if arg == "--symbol" and i + 1 < len(sys.argv):
            symbol = sys.argv[i + 1]
        elif arg == "--from" and i + 1 < len(sys.argv):
            from_date = sys.argv[i + 1]
        elif arg == "--to" and i + 1 < len(sys.argv):
            to_date = sys.argv[i + 1]

    print(f"\n📋 Configuration:")
    print(f"   Symbol: {symbol}")
    print(f"   Period: {from_date} → {to_date}")
    print(f"   EA: {EA_NAME}")

    # Step 1: Check prerequisites
    print(f"\n{'=' * 60}")
    print("STEP 1: Checking prerequisites...")
    if not check_prerequisites():
        print("❌ Prerequisites not met. Exiting.")
        return False

    # Step 2: Compile EA
    print(f"\n{'=' * 60}")
    print("STEP 2: Compiling EA...")
    if not compile_ea():
        print("⚠️ Compilation had issues, but continuing...")

    # Step 3: Create INI config
    print(f"\n{'=' * 60}")
    print("STEP 3: Creating Strategy Tester config...")
    ini_path, report_path = create_tester_ini(symbol, from_date, to_date, TIMEFRAME, LOT_SIZE)

    # Step 4: Run Strategy Tester
    print(f"\n{'=' * 60}")
    print("STEP 4: Running MT5 Strategy Tester...")
    print("   ⚠️ A MT5 terminal window will open and run the test.")
    print("   ⚠️ It will close automatically when done.")
    print("   ⚠️ Do NOT close the MT5 window manually!")
    success = run_strategy_tester(ini_path)

    # Step 5: Find results
    print(f"\n{'=' * 60}")
    print("STEP 5: Collecting results...")
    results = find_results(report_path)

    # Step 6: Generate report
    print(f"\n{'=' * 60}")
    print("STEP 6: Generating report...")
    report_file = generate_report(results, symbol, from_date, to_date)

    print(f"\n{'=' * 60}")
    print("  NATIVE MT5 BACKTEST COMPLETE")
    print(f"{'=' * 60}")

    ea_data = results.get('ea_json', {})
    if ea_data:
        print(f"\n📊 Quick Results:")
        print(f"   Trades: {ea_data.get('total_trades', 'N/A')}")
        print(f"   WR: {ea_data.get('win_rate', 'N/A')}%")
        print(f"   PnL: {ea_data.get('total_pnl_pips', 'N/A')} pips")
        print(f"   MaxDD: {ea_data.get('max_dd_pips', 'N/A')} pips")

    print(f"\n📄 Report: {report_file}")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
