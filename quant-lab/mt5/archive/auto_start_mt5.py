"""
MT5 Auto-Start & Management Utility
Handles starting MT5 terminal so the Python API can connect without user intervention.

Usage:
  python auto_start_mt5.py          # Start MT5 if not running
  python auto_start_mt5.py --check  # Just check status
  python auto_start_mt5.py --stop   # Stop MT5

MT5 auto-login is configured in:
  C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\<profile>\config\common.ini
    Login=1114712
    Server=OxSecurities-Demo

So terminal64.exe will auto-connect to the demo account on launch.
"""
import sys, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5

MT5_EXE = r"C:\Program Files\Ox Securities MetaTrader 5\terminal64.exe"

def check_running():
    r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal64.exe'], capture_output=True, text=True)
    return 'terminal64' in r.stdout

def start():
    if check_running():
        print("MT5 already running")
        return True
    
    print(f"Starting MT5: {MT5_EXE}")
    subprocess.Popen([MT5_EXE], shell=True)
    
    for i in range(30):
        time.sleep(1)
        if check_running():
            print(f"MT5 started ({i+1}s)")
            time.sleep(5)  # Wait for full init + auto-login
            return True
    
    print("ERROR: MT5 didn't start within 30s")
    return False

def stop():
    if check_running():
        print("Stopping MT5...")
        subprocess.run(['taskkill', '/IM', 'terminal64.exe', '/F'])
        time.sleep(2)
        print("Stopped")
    else:
        print("MT5 not running")

def status():
    if not check_running():
        print("MT5: NOT RUNNING")
        return False
    
    if not mt5.initialize():
        print(f"MT5: RUNNING but API connect failed ({mt5.last_error()})")
        return False
    
    account = mt5.account_info()
    if account:
        print(f"MT5: CONNECTED ✓")
        print(f"  Login:    {account.login}")
        print(f"  Server:   {account.server}")
        print(f"  Balance:  {account.balance} {account.currency}")
        print(f"  Leverage: 1:{account.leverage}")
        print(f"  Trade OK:  {account.trade_allowed and account.trade_expert}")
    else:
        print("MT5: RUNNING but no account info")
    
    mt5.shutdown()
    return True

def ensure():
    """Ensure MT5 is running and connected (for use by other scripts)"""
    if not check_running():
        if not start():
            return False
    
    if not mt5.initialize():
        return False
    
    # Don't shutdown — caller will use the connection
    return True

if __name__ == '__main__':
    if '--check' in sys.argv:
        status()
    elif '--stop' in sys.argv:
        stop()
    else:
        if start():
            status()
