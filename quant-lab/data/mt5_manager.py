"""
MT5 Manager — Auto-start, connect, check status
Handles launching MT5 terminal and connecting via Python API.
No user intervention required if common.ini has auto-login configured.
"""
import sys, os, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5
from pathlib import Path

MT5_EXE = r"C:\Program Files\Ox Securities MetaTrader 5\terminal64.exe"
MT5_PROCESS = "terminal64"

def is_mt5_running():
    """Check if MT5 terminal is already running"""
    result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {MT5_PROCESS}.exe'],
                          capture_output=True, text=True)
    return MT5_PROCESS in result.stdout

def start_mt5(timeout=30):
    """Launch MT5 terminal and wait for it to initialize"""
    # Start without /portable — uses the standard profile with auto-login
    subprocess.Popen([MT5_EXE], shell=True)
    print(f"Starting MT5: {MT5_EXE}")
    
    # Wait for it to come online
    for i in range(timeout):
        time.sleep(1)
        if is_mt5_running():
            print(f"MT5 process started (等了 {i+1}s)")
            time.sleep(3)  # Extra time for full init
            return True
    print(f"ERROR: MT5 didn't start within {timeout}s")
    return False

def connect_mt5():
    """Initialize MT5 Python API connection"""
    if not mt5.initialize():
        error = mt5.last_error()
        print(f"MT5 init failed: {error}")
        return False
    return True

def ensure_connected():
    """Ensure MT5 is running and connected. Auto-start if needed."""
    if is_mt5_running():
        print("MT5 already running")
        return connect_mt5()
    
    print("MT5 not running, starting...")
    if start_mt5():
        return connect_mt5()
    return False

def get_account_info():
    """Get account details"""
    if not ensure_connected():
        return None
    info = mt5.account_info()
    mt5.shutdown()
    if info:
        return {
            'login': info.login,
            'server': info.server,
            'balance': info.balance,
            'currency': info.currency,
            'leverage': info.leverage,
            'name': info.name,
            'company': info.company,
            'trade_allowed': info.trade_allowed,
            'trade_expert': info.trade_expert,
        }
    return None

def shutdown():
    mt5.shutdown()

if __name__ == '__main__':
    print("=== MT5 Manager ===")
    info = get_account_info()
    if info:
        print(f"Connected: {info['login']} @ {info['server']}")
        print(f"Balance: {info['balance']} {info['currency']}")
        print(f"Trade Allowed: {info['trade_allowed']}")
    else:
        print("Failed to connect")
