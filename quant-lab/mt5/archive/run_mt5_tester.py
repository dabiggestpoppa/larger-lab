"""
MT5 Strategy Tester - Run backtest and capture results.
Uses pyautogui to click Start on the Strategy Tester panel.
"""
import sys, os, time, subprocess, glob, shutil
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

import pyautogui

MT5_EXE     = r"C:\Program Files\Ox Securities MetaTrader 5\terminal64.exe"
TESTER_LOGS = r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\Tester\logs"
TESTER_CACHE= r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\Tester\cache"
REPORTS     = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\reports"
SHOTS       = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\screenshots"

pyautogui.PAUSE = 0.3
pyautogui.FAILSAFE = True
os.makedirs(SHOTS, exist_ok=True)
os.makedirs(REPORTS, exist_ok=True)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def snap(name):
    p = os.path.join(SHOTS, f"{name}_{int(time.time())}.png")
    pyautogui.screenshot(p)
    log(f"Screenshot: {name}")
    return p

def kill_mt5():
    subprocess.run(['taskkill', '/IM', 'terminal64.exe', '/F'], capture_output=True)
    time.sleep(3)

def find_mt5():
    try:
        wins = pyautogui.getWindowsWithTitle("Ox Securities")
        if wins:
            return wins[0]
    except Exception:
        pass
    return None

def main():
    log("="*60)
    log("MT5 Strategy Tester - Backtest Runner")
    log("="*60)

    # Kill existing
    kill_mt5()

    # Launch MT5
    log("Launching MT5...")
    subprocess.Popen([MT5_EXE], cwd=os.path.dirname(MT5_EXE))

    # Wait for window
    win = None
    for _ in range(30):
        win = find_mt5()
        if win:
            break
        time.sleep(1)

    if not win:
        log("ERROR: MT5 window not found")
        sys.exit(1)

    log(f"MT5 window: {win.title} at ({win.left},{win.top}) size {win.width}x{win.height}")
    time.sleep(5)  # Wait for login
    snap("mt5_ready")

    # Strategy Tester panel is at the bottom of MT5 window
    # Based on terminal.ini, the tester panel (Pane-32841) is docked at:
    # DockedLeft=0, DockedTop=854, DockedRight=1904, DockedBottom=949
    # That's ~95px tall at the bottom of a 1032px window
    
    # Open Strategy Tester with Ctrl+R
    log("Opening Strategy Tester (Ctrl+R)...")
    pyautogui.hotkey('ctrl', 'r')
    time.sleep(3)
    snap("tester_open")

    # Now we need to verify the config and click Start
    # The Start button (green ▶) is in the Strategy Tester panel
    # Typical location: right side of the panel

    # Let me click on the Strategy Tester panel area first to ensure it's focused
    # Panel top is approximately at win.height - 100 from the window top
    panel_center_y = win.top + win.height - 50  # Bottom panel
    panel_center_x = win.left + win.width // 2

    pyautogui.click(panel_center_x, panel_center_y)
    time.sleep(0.5)
    snap("tester_focused")

    # Look for the Start button - it's at the right end of the panel
    # The panel is ~95px tall, Start button is at the far right
    # Button width is typically ~30px
    start_x = win.left + win.width - 50  # Far right of window
    start_y = win.top + win.height - 50  # Bottom panel

    log(f"Clicking Start button at ({start_x}, {start_y})")
    snap("before_start")
    pyautogui.click(start_x, start_y)
    time.sleep(3)
    snap("after_start_click")

    # Wait for test to start and complete
    # For 1 month of M5 every-tick, this takes several minutes
    log("Waiting for test completion...")

    # Check for the test running by looking for new cache files
    initial_cache = set(glob.glob(os.path.join(TESTER_CACHE, "*")))
    
    max_wait = 600  # 10 minutes
    check_interval = 15
    elapsed = 0
    running = False

    while elapsed < max_wait:
        time.sleep(check_interval)
        elapsed += check_interval

        # Check if MT5 still exists
        if not find_mt5():
            log(f"MT5 closed after {elapsed}s")
            break

        # Check for new DMR activity
        current_cache = set(glob.glob(os.path.join(TESTER_CACHE, "*")))
        new_files = current_cache - initial_cache
        
        dmr_files = [f for f in new_files if "DMR" in os.path.basename(f).upper()]
        
        if dmr_files and not running:
            running = True
            log(f"  Test STARTED - DMR cache files appearing: {len(dmr_files)}")
            for f in dmr_files[:3]:
                log(f"    {os.path.basename(f)}")

        if running:
            # Count all DMR cache
            all_dmr = [f for f in current_cache if "DMR" in os.path.basename(f).upper()]
            sizes = sum(os.path.getsize(f) for f in all_dmr) / (1024*1024)
            log(f"  [{elapsed}s] DMR cache: {len(all_dmr)} files, {sizes:.1f}MB")

            # Check if test completed by seeing if cache finished growing
            if elapsed > 60 and len(dmr_files) == 0:
                # No new files in this interval - test might be done
                all_dmr_now = [f for f in set(glob.glob(os.path.join(TESTER_CACHE, "*"))) if "DMR" in os.path.basename(f).upper()]
                time.sleep(check_interval)
                all_dmr_later = [f for f in set(glob.glob(os.path.join(TESTER_CACHE, "*"))) if "DMR" in os.path.basename(f).upper()]
                if len(all_dmr_now) == len(all_dmr_later):
                    log(f"  Cache stable - test likely complete")
                    break

        elif elapsed % 30 == 0:
            log(f"  [{elapsed}s] Waiting for test to start...")
            snap(f"waiting_{elapsed}")

    # Collect results
    log("Collecting results...")
    
    # Screenshot final state
    snap("final_state")

    # Check for HTML/XML reports
    if os.path.exists(TESTER_LOGS):
        recent_logs = [f for f in glob.glob(os.path.join(TESTER_LOGS, "*"))
                       if os.path.isfile(f) and os.path.getmtime(f) > time.time() - max(elapsed + 60, 600)]
        log(f"Recent log files: {len(recent_logs)}")
        for f in recent_logs:
            size = os.path.getsize(f)
            log(f"  {os.path.basename(f)} ({size} bytes)")
            dst = os.path.join(REPORTS, f"mt5_{os.path.basename(f)}")
            shutil.copy2(f, dst)
            log(f"    Copied to reports/")

    # Check DMR cache files
    all_dmr = [f for f in glob.glob(os.path.join(TESTER_CACHE, "*"))
               if "DMR" in os.path.basename(f).upper()]
    log(f"DMR cache files: {len(all_dmr)}")
    for f in all_dmr:
        log(f"  {os.path.basename(f)} ({os.path.getsize(f)} bytes)")

    # Check for report files in the terminal directory
    term_dir = os.path.dirname(TESTER_LOGS)
    for pattern in ["*.htm", "*.html", "*.xml", "*.csv"]:
        for f in glob.glob(os.path.join(term_dir, pattern)):
            if os.path.getmtime(f) > time.time() - max(elapsed + 60, 600):
                dst = os.path.join(REPORTS, f"mt5_{os.path.basename(f)}")
                shutil.copy2(f, dst)
                log(f"Report: {os.path.basename(f)}")

    log("Done. Check reports/ directory for results.")

if __name__ == '__main__':
    main()
