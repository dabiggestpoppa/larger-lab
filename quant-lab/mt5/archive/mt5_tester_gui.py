"""
MT5 Strategy Tester GUI Automation
Opens Strategy Tester, loads DMR_FULL_BACKTEST, runs a short backtest, captures results.
"""
import sys, os, time, subprocess, glob, shutil
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

import pyautogui

MT5_EXE = r"C:\Program Files\Ox Securities MetaTrader 5\terminal64.exe"
TESTER_LOGS = r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\Tester\logs"
TESTER_CACHE = r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\Tester\cache"
SCREENSHOTS = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\screenshots"

pyautogui.PAUSE = 0.3
pyautogui.FAILSAFE = True

os.makedirs(SCREENSHOTS, exist_ok=True)

def screenshot(name):
    path = os.path.join(SCREENSHOTS, f"{name}_{int(time.time())}.png")
    pyautogui.screenshot(path)
    print(f"  [Screenshot] {name}")
    return path

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def kill_mt5():
    subprocess.run(['taskkill', '/IM', 'terminal64.exe', '/F'], capture_output=True)
    time.sleep(3)

def start_mt5():
    subprocess.Popen([MT5_EXE], cwd=os.path.dirname(MT5_EXE))
    log("MT5 launched, waiting for window...")

def wait_for_mt5(timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            wins = pyautogui.getWindowsWithTitle("Ox Securities")
            if wins:
                w = wins[0]
                log(f"MT5 window: {w.title} ({w.width}x{w.height}) at ({w.left},{w.top})")
                return w
        except Exception:
            pass
        time.sleep(1)
    log("ERROR: MT5 window not found")
    return None

def main():
    log("="*60)
    log("MT5 Strategy Tester GUI Automation")
    log("="*60)

    # Step 1: Kill existing MT5
    log("Step 1: Clean start...")
    kill_mt5()

    # Step 2: Launch MT5
    log("Step 2: Launching MT5...")
    start_mt5()
    win = wait_for_mt5(timeout=30)
    if not win:
        log("FAILED: MT5 didn't start")
        sys.exit(1)

    time.sleep(5)  # Wait for login
    screenshot("mt5_main")

    # Step 3: Open Strategy Tester
    # Try Ctrl+R first, then menu approach
    log("Step 3: Opening Strategy Tester...")

    # Press Ctrl+R (standard MT5 shortcut for Strategy Tester)
    pyautogui.hotkey('ctrl', 'r')
    time.sleep(3)
    screenshot("ctrl_r")

    # Check if Strategy Tester panel appeared
    screen_h = pyautogui.size()[1]
    screenshot("after_ctrl_r")

    # If Ctrl+R didn't work, try menu: View -> Strategy Tester
    # Menu bar is at top-left of MT5 window
    if win:
        # Click "View" menu
        menu_y = win.top + 30  # Approximate menu bar height

        # Use Alt+V to open View menu, then S for Strategy Tester
        pyautogui.hotkey('alt', 'v')
        time.sleep(0.5)
        screenshot("alt_v")

        # Look for Strategy Tester menu item and click it
        try:
            # Try to find "Strategy Tester" text on screen
            # Use keyboard navigation: Strategy Tester is usually under View
            loc = pyautogui.locateOnScreen(None, confidence=0.8)  # Can't use this without reference images
        except Exception:
            pass

        # Just type 's' to select Strategy Tester from View menu
        pyautogui.press('s')
        time.sleep(2)
        screenshot("view_strategy_tester")

    # Step 4: Configure Strategy Tester
    log("Step 4: Configuring Strategy Tester...")

    if not win:
        win = wait_for_mt5(timeout=5)
    if win:
        # Get fresh window info
        try:
            wins = pyautogui.getWindowsWithTitle("Ox Securities")
            if wins:
                win = wins[0]
        except Exception:
            pass

        # The Strategy Tester panel is at the bottom of the MT5 window
        # Typical layout: panel starts ~200px from bottom

        panel_y = win.height - 150  # Bottom panel area

        # Click on "Expert Advisor" dropdown
        # It's typically at the left side of the Strategy Tester panel
        ea_dropdown_x = win.left + 100
        ea_dropdown_y = win.top + panel_y

        log(f"  Clicking EA dropdown at ({ea_dropdown_x}, {ea_dropdown_y})")
        pyautogui.click(ea_dropdown_x, ea_dropdown_y)
        time.sleep(1)
        screenshot("ea_dropdown")

        # Clear field and type EA name
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.typewrite("DMR_FULL_BACKTEST", interval=0.03)
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(1)
        screenshot("ea_selected")

        # Now set dates
        # From date field is typically to the right of the EA dropdown
        # Let's tab through fields
        # Actually, MT5 tester remembers last used dates, so let's just check

        # Click the Start button (green triangle)
        # Start button is at bottom-right of Strategy Tester panel
        start_btn_x = win.left + win.width - 80
        start_btn_y = win.top + panel_y

        log(f"  Clicking Start at ({start_btn_x}, {start_btn_y})")
        screenshot("before_start")
        pyautogui.click(start_btn_x, start_btn_y)
        time.sleep(2)
        screenshot("after_start")

    # Step 5: Wait for test and collect results
    log("Step 5: Waiting for test completion...")

    max_wait = 300  # 5 min for short test
    interval = 10
    elapsed = 0

    while elapsed < max_wait:
        time.sleep(interval)
        elapsed += interval

        # Check if MT5 still running
        r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal64.exe'],
                           capture_output=True, text=True)
        if 'terminal64' not in r.stdout:
            log(f"MT5 closed after {elapsed}s")
            break

        # Check for new DMR cache files
        dmr_files = glob.glob(os.path.join(TESTER_CACHE, "*DMR*"))
        if dmr_files:
            log(f"  DMR cache files found: {len(dmr_files)}")
            for f in dmr_files:
                log(f"    {os.path.basename(f)} ({os.path.getsize(f)} bytes)")
            break

        # Check for new logs
        if os.path.exists(TESTER_LOGS):
            logs = glob.glob(os.path.join(TESTER_LOGS, "*"))
            recent = [f for f in logs if os.path.getmtime(f) > time.time() - interval]
            if recent:
                log(f"  New log files: {len(recent)}")

        if elapsed % 30 == 0:
            log(f"  [{elapsed}s] Still running...")
            screenshot(f"progress_{elapsed}s")

    # Step 6: Collect results
    log("Step 6: Collecting results...")

    # Screenshot final state
    screenshot("final")

    # Copy any HTML/XML reports
    reports_dir = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\reports"
    os.makedirs(reports_dir, exist_ok=True)

    if os.path.exists(TESTER_LOGS):
        for f in glob.glob(os.path.join(TESTER_LOGS, "*")):
            if os.path.getmtime(f) > time.time() - 600:  # Last 10 min
                dst = os.path.join(reports_dir, f"mt5_tester_{os.path.basename(f)}")
                shutil.copy2(f, dst)
                log(f"  Copied: {os.path.basename(f)}")

    log("Done.")

if __name__ == '__main__':
    main()
