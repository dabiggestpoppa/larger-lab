#!/usr/bin/env python3
"""
OWL Overnight Monitor — DMR Forward Test + System Health
Runs every 30 minutes during 2-11 AM EST P90 window.
"""
import subprocess, json, os, sys
from datetime import datetime, timezone

STATE_FILE = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_forward_test_state.json"
LOG_FILE = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_forward_test_log.csv"
REPORT_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports"

def get_est_hour():
    utc_now = datetime.now(timezone.utc)
    return (utc_now.hour - 5 + 24) % 24

def check_forward_test():
    """Check if forward test script is running and get state."""
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        return state
    except:
        return None

def run_forward_test():
    """Start the forward test script."""
    script = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_mt5_forward_test.py"
    try:
        subprocess.Popen(
            [sys.executable, script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        return True
    except Exception as e:
        print(f"Failed to start forward test: {e}")
        return False

def main():
    est_h = get_est_hour()
    now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    
    print(f"[{now_utc}] Overnight Monitor — EST hour: {est_h}")
    
    # Check forward test state
    state = check_forward_test()
    if state:
        print(f"  Forward test state: {state['total_trades']} trades, {state['wins']}W/{state['losses']}L, PnL={state['pnl']}")
        
        # If we're in P90 window (2-11 AM) and no trade placed yet, make sure script is running
        if 2 <= est_h < 11 and not state.get('trade_placed', False):
            print("  In P90 window, no trade placed — ensuring forward test is running")
            run_forward_test()
        elif state.get('trade_placed', False):
            print("  Trade already placed today — monitoring")
    else:
        print("  No state file found — starting forward test")
        if 2 <= est_h < 11:
            run_forward_test()
    
    # System health
    import shutil
    total, used, free = shutil.disk_usage("C:\\")
    print(f"  Disk: {free // (2**30)}GB free / {total // (2**30)}GB total")
    
    print("  Done.")

if __name__ == "__main__":
    main()
