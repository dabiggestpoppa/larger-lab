#!/usr/bin/env python3
"""
Algo Trading Readiness Check — Final verification before tomorrow's trading day.
"""
import json
import sqlite3
import subprocess
import urllib.request
import socket
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
DB_FILE = BASE / "quant-lab" / "mt5" / "dmr_live.db"
STATE_FILE = BASE / "quant-lab" / "mt5" / "dmr_live_state.json"
CONFIG_FILE = BASE / "quant-lab" / "mt5" / "dmr_config.json"
REPORT_FILE = BASE / "quant-lab" / "reports" / "ALGO_READINESS_REPORT.md"

REPORT_FILE.parent.mkdir(exist_ok=True)

import sys
sys.stdout.reconfigure(encoding='utf-8')

report = []
def rpt(msg):
    report.append(msg)
    try:
        print(msg)
    except:
        pass

def check_port(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        result = s.connect_ex(('127.0.0.1', port))
        s.close()
        return result == 0
    except:
        return False

rpt("# ALGO TRADING READINESS REPORT")
rpt(f"**Generated:** {datetime.now(timezone.utc).isoformat()}")
rpt(f"**Trading Day:** Tomorrow (May 21, 2026)")
rpt("")

# 1. DMR Live Process
rpt("## 1. DMR Live Process")
try:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -match 'dmr_live'} | Select-Object Id, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}} | Format-List"],
        capture_output=True, text=True, timeout=10
    )
    if result.stdout.strip():
        rpt(f"✅ DMR Live RUNNING: {result.stdout.strip()}")
    else:
        rpt("❌ DMR Live NOT RUNNING — CRITICAL!")
except:
    rpt("⚠️ Could not check DMR process")

# 2. MT5 Connection & AutoTrading
rpt("")
rpt("## 2. MT5 Connection & AutoTrading")
if DB_FILE.exists():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT timestamp, level, message, details FROM system_log WHERE category='MT5' ORDER BY id DESC LIMIT 5")
        mt5_logs = c.fetchall()
        conn.close()
        for ts, level, msg, details in mt5_logs:
            icon = "✅" if level == "INFO" else "⚠️" if level == "WARN" else "❌"
            rpt(f"  {icon} [{level}] {msg}")
            if details:
                rpt(f"     Details: {details}")
    except Exception as e:
        rpt(f"  ⚠️ DB Error: {e}")

# 3. Config Verification
rpt("")
rpt("## 3. Trading Configuration")
if CONFIG_FILE.exists():
    with open(CONFIG_FILE) as f:
        cfg = json.load(f)
    rpt(f"  Account: {cfg.get('login')} | Server: {cfg.get('server')}")
    rpt(f"  Enabled: {cfg.get('enabled')}")
    rpt(f"  Symbols: {cfg.get('symbols')}")
    rpt(f"  Lot Size: {cfg.get('lot_size')}")
    rpt(f"  Max Daily Trades/Symbol: {cfg.get('max_daily_trades_per_symbol')}")
    rpt(f"  Hard Exit Hour (EST): {cfg.get('hard_exit_hour_est')}")
    rpt(f"  Deep Mult: {cfg.get('deep_mult')} | Kill Mult: {cfg.get('kill_mult')}")
    rpt(f"  Magic Number: {cfg.get('magic_number')}")
    
    # Validate config
    issues = []
    if not cfg.get('enabled'):
        issues.append("Trading is DISABLED in config")
    if not cfg.get('symbols'):
        issues.append("No symbols configured")
    if cfg.get('lot_size', 0) <= 0:
        issues.append("Invalid lot size")
    if cfg.get('hard_exit_hour_est', 0) < 12 or cfg.get('hard_exit_hour_est', 0) > 23:
        issues.append("Hard exit hour should be between 12-23")
    
    if issues:
        rpt(f"  ⚠️ Config Issues:")
        for i in issues:
            rpt(f"    - {i}")
    else:
        rpt(f"  ✅ Config looks valid")

# 4. State Verification
rpt("")
rpt("## 4. Trading State")
if STATE_FILE.exists():
    with open(STATE_FILE) as f:
        state = json.load(f)
    rpt(f"  Today: {state.get('today')}")
    rpt(f"  Trading Enabled (state): {state.get('trading_enabled', 'not set')}")
    rpt(f"  Total Trades: {state.get('total_trades', 0)}")
    rpt(f"  Wins: {state.get('wins', 0)} | Losses: {state.get('losses', 0)}")
    rpt(f"  PnL: ${state.get('pnl', 0)}")
    rpt(f"  Found P90s: {len(state.get('found_p90s', []))}")

# 5. Database Stats
rpt("")
rpt("## 5. Database Statistics")
if DB_FILE.exists():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM trades")
        rpt(f"  Total Trades: {c.fetchone()[0]}")
        c.execute("SELECT COUNT(*) FROM p90_events")
        rpt(f"  Total P90 Events: {c.fetchone()[0]}")
        c.execute("SELECT COUNT(*) FROM system_log")
        rpt(f"  System Log Entries: {c.fetchone()[0]}")
        c.execute("SELECT COUNT(*) FROM account_snapshots")
        rpt(f"  Account Snapshots: {c.fetchone()[0]}")
        
        # Today's P90 breakdown by symbol
        c.execute("SELECT symbol, COUNT(*) FROM p90_events WHERE date = date('now') GROUP BY symbol")
        today_p90s = c.fetchall()
        if today_p90s:
            rpt(f"  Today's P90s by Symbol:")
            for sym, count in today_p90s:
                rpt(f"    {sym}: {count}")
        
        conn.close()
    except Exception as e:
        rpt(f"  ⚠️ DB Error: {e}")

# 6. Dashboard Status
rpt("")
rpt("## 6. Dashboard Status")
dashboard_up = check_port(8002)
rpt(f"  Dashboard (:8002): {'✅ UP' if dashboard_up else '❌ DOWN'}")

# 7. Server Status
rpt("")
rpt("## 7. Server Status")
servers = {
    8000: "OCE Backend",
    8001: "SRRA API",
    3000: "OCE Frontend",
    3001: "SRRA Frontend",
    18790: "OpenClaw Gateway",
}
for port, name in servers.items():
    up = check_port(port)
    rpt(f"  {name} (:{port}): {'✅' if up else '❌'}")

# 8. Readiness Checklist
rpt("")
rpt("## 8. Pre-Trading Checklist")
rpt("")
checklist = []

# Check DMR process
try:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -match 'dmr_live'}"],
        capture_output=True, text=True, timeout=10
    )
    dmr_running = bool(result.stdout.strip())
except:
    dmr_running = False
checklist.append(("DMR Live process running", dmr_running))

# Check config enabled
cfg_enabled = cfg.get('enabled', False) if CONFIG_FILE.exists() else False
checklist.append(("Trading enabled in config", cfg_enabled))

# Check symbols configured
has_symbols = bool(cfg.get('symbols', [])) if CONFIG_FILE.exists() else False
checklist.append(("Symbols configured", has_symbols))

# Check dashboard
checklist.append(("Dashboard accessible", dashboard_up))

# Check MT5 logs for AutoTrading
autotrading_ok = True
if DB_FILE.exists():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT message FROM system_log WHERE category='MT5' ORDER BY id DESC LIMIT 1")
        last_mt5 = c.fetchone()
        conn.close()
        if last_mt5 and 'DISABLED' in last_mt5[0]:
            autotrading_ok = False
    except:
        pass
checklist.append(("MT5 AutoTrading enabled", autotrading_ok))

# Check ports
for port, name in servers.items():
    up = check_port(port)
    checklist.append((f"{name} (:{port})", up))

all_pass = True
for item, status in checklist:
    icon = "✅" if status else "❌"
    if not status:
        all_pass = False
    rpt(f"  {icon} {item}")

rpt("")
if all_pass:
    rpt("## ✅ SYSTEM READY FOR TOMORROW'S TRADING DAY")
else:
    rpt("## ⚠️ ISSUES FOUND — REVIEW BEFORE TRADING")

rpt("")
rpt("---")
rpt(f"*Report generated by Algo Readiness Check*")

# Write report
with open(REPORT_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))

rpt(f"\nReport saved to: {REPORT_FILE}")
