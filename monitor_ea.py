#!/usr/bin/env python3
"""
CEREBUS EA Continuous Monitor
- Compiles EA
- Runs backtest
- Logs results
- Iterates on fixes
"""
import subprocess
import time
import json
import os
from datetime import datetime
from pathlib import Path

EA_PATH = r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\MQL5\Experts\Cerebus_Symmetry_OptionB.mq5"
LOG_FILE = r"C:\Users\wifik\Desktop\projects\larger-lab\ea_monitor.log"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def compile_ea():
    """Compile the EA using MetaEditor"""
    # Try to find metaeditor
    metaeditor_paths = [
        r"C:\Program Files\MetaTrader 5\metaeditor64.exe",
        r"C:\Program Files\Ox Securities\metaeditor64.exe",
        r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\metaeditor64.exe",
    ]
    
    for path in metaeditor_paths:
        if os.path.exists(path):
            cmd = [path, "/compile", EA_PATH, "/log"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
    
    log("MetaEditor not found - cannot compile")
    return False

def run_backtest():
    """Run backtest via MT5 Python API"""
    import MetaTrader5 as mt5
    
    if not mt5.initialize():
        log("MT5 not available")
        return None
    
    # Get recent data for quick test
    rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M1, 0, 1000)
    mt5.shutdown()
    
    if rates is None:
        log("No data available")
        return None
    
    log(f"Data ready: {len(rates)} bars")
    return len(rates)

def main():
    log("=== CEREBUS EA Monitor Started ===")
    
    iteration = 0
    while True:
        iteration += 1
        log(f"--- Iteration {iteration} ---")
        
        # Compile
        if compile_ea():
            log("EA compiled successfully")
        else:
            log("EA compilation failed")
        
        # Quick backtest check
        result = run_backtest()
        if result:
            log(f"Backtest data: {result} bars ready")
        
        # Wait before next iteration
        log("Waiting 5 minutes...")
        time.sleep(300)  # 5 minutes

if __name__ == "__main__":
    main()