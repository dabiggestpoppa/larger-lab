"""
MT5 Strategy Tester Runner - Window-focused approach
"""
import sys, os, time, subprocess, glob, shutil
from datetime import datetime
import ctypes

sys.stdout.reconfigure(encoding='utf-8')

import pyautogui
import pygetwindow as gw

MT5_EXE     = r"C:\Program Files\Ox Securities MetaTrader 5\terminal64.exe"
TESTER_LOGS = r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\Tester\logs"
TESTER_CACHE= r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\Tester\cache"
REPORTS     = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\reports"
SHOTS       = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\screenshots"

pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True
os.makedirs(SHOTS, exist_ok=True)
os.makedirs(REPORTS, exist_ok=True)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def snap(name):
    p = os.path.join(SHOTS, f"{name}.png")
    pyautogui.screenshot(p)
    log(f"Screenshot saved: {name}.png ({os.path.getsize(p)//1024}KB)")
    return p

def kill_mt5():
    subprocess.run(['taskkill', '/IM', 'terminal64.exe', '/F'], capture_output=True)
    time.sleep(3)

def find_and_activate_mt5(timeout=45):
    """Find MT5 window and bring to foreground"""
    for i in range(timeout):
        try:
            # MT5 title starts with account number: "1114712 - OxSecurities-Demo:..."
            all_titles = gw.getAllTitles()
            mt5_title = None
            for t in all_titles:
                if t.strip() and 'OxSecurities' in t:
                    mt5_title = t
                    break
            if mt5_title:
                wins = gw.getWindowsWithTitle(mt5_title)
                if wins:
                    w = wins[0]
                    if w.isMinimized:
                        w.restore()
                    w.activate()
                    time.sleep(1)
                    # Re-fetch after activate
                    all_titles = gw.getAllTitles()
                    for t in all_titles:
                        if t.strip() and 'OxSecurities' in t:
                            wins = gw.getWindowsWithTitle(t)
                            if wins:
                                w = wins[0]
                                log(f"MT5 found: '{w.title[:60]}...' at ({w.left},{w.top}) {w.width}x{w.height}")
                                return w
        except Exception as e:
            log(f"  Window search error: {e}")
        time.sleep(1)
    return None

def main():
    log("="*60)
    log("MT5 Strategy Tester - Fidelity Validation Run")
    log("Config: DMR_FULL_BACKTEST | EURUSD.PRO M5 | 2024-01-01 to 2024-01-31")
    log("="*60)

    # Clean start
    kill_mt5()

    # Launch MT5
    log("Launching MT5...")
    subprocess.Popen([MT5_EXE], cwd=os.path.dirname(MT5_EXE))

    # Find and activate MT5 window
    win = find_and_activate_mt5(timeout=45)
    if not win:
        log("FATAL: MT5 window not found after 45s")
        sys.exit(1)

    time.sleep(5)  # Wait for login/data load
    snap("01_mt5_ready")

    # Now open Strategy Tester
    log("Opening Strategy Tester (Ctrl+R)...")
    pyautogui.hotkey('ctrl', 'r')
    time.sleep(3)

    # Re-find window (may have changed size)
    win = find_and_activate_mt5(timeout=10)

    snap("02_tester_open")

    # Now take a detailed screenshot and analyze the layout
    log(f"Window: {win.width}x{win.height} at ({win.left},{win.top})")

    # From the terminal.ini, the Strategy Tester panel (bottom panel) is at:
    # DockedTop=854, DockedBottom=949 => ~95px tall
    # Screen: 1920x1080 (from terminal.ini: Bottom=1032 with taskbar)
    # The panel is at the bottom of the client area

    # Strategy Tester controls (standard MT5 layout):
    # Left side: Expert dropdown (combo box), Symbol, Period
    # Middle: Date from/to, Spread, etc.
    # Right side: green Start button (▶)

    # Let me try to find the Start button visually
    # The Start button in MT5 is typically:
    # - A green triangle icon
    # - Located at the right side of the Strategy Tester panel
    # - Panel is at the bottom ~100px of the window

    # Click on the Strategy Tester panel to ensure focus
    panel_y = win.top + win.height - 50  # Panel center Y
    panel_x = win.left + win.width // 2

    log(f"Clicking Strategy Tester panel at ({panel_x}, {panel_y})")
    pyautogui.click(panel_x, panel_y)
    time.sleep(0.5)

    # Take screenshot AFTER focusing on tester
    win = find_and_activate_mt5(timeout=5)
    snap("03_tester_focused")

    # The Start button is at the right side of the Strategy Tester panel
    # In MT5, it's typically ~40-60px from the right edge
    # And ~30-50px from the bottom of the window
    start_btn_x = win.left + win.width - 60
    start_btn_y = win.top + win.height - 50

    log(f"Clicking Start button at ({start_btn_x}, {start_btn_y})")
    snap("04_before_start")
    pyautogui.click(start_btn_x, start_btn_y)
    time.sleep(3)
    snap("05_after_start")

    # Check if a dialog appeared (confirmation, error, etc.)
    time.sleep(2)
    snap("06_check_dialog")

    # Check for tester activity
    initial_cache = set(glob.glob(os.path.join(TESTER_CACHE, "*")))
    log(f"Initial cache files: {len(initial_cache)}")

    # Wait for test to run
    max_wait = 600
    interval = 15
    elapsed = 0
    running = False

    while elapsed < max_wait:
        time.sleep(interval)
        elapsed += interval

        # Check if MT5 still exists
        try:
            all_t = gw.getAllTitles()
            mt5_found = any('OxSecurities' in t for t in all_t if t.strip())
            if not mt5_found:
                log(f"MT5 closed after {elapsed}s")
                break
        except Exception:
            log("MT5 process gone")
            break

        # Check for DMR cache files
        current_cache = set(glob.glob(os.path.join(TESTER_CACHE, "*")))
        new_files = current_cache - initial_cache
        dmr_new = [f for f in new_files if "DMR" in os.path.basename(f).upper()]

        if dmr_new:
            if not running:
                running = True
                log(f"  ✓ Test STARTED - new DMR cache files: {len(dmr_new)}")
            for f in dmr_new[:3]:
                log(f"    {os.path.basename(f)} ({os.path.getsize(f)} bytes)")

        if running:
            all_dmr = [f for f in current_cache if "DMR" in os.path.basename(f).upper()]
            total_size = sum(os.path.getsize(f) for f in all_dmr) / (1024*1024)
            log(f"  [{elapsed}s] Running... DMR cache: {len(all_dmr)} files, {total_size:.1f}MB")

            # Check if done (no new growth for 2 intervals)
            if elapsed > 60:
                time.sleep(interval)
                elapsed += interval
                later_cache = set(glob.glob(os.path.join(TESTER_CACHE, "*")))
                later_dmr = [f for f in later_cache if "DMR" in os.path.basename(f).upper()]
                if len(all_dmr) == len(later_dmr) and len(dmr_new) == 0:
                    log("  Cache stable - test appears complete")
                    break
        else:
            if elapsed % 30 == 0:
                log(f"  [{elapsed}s] Waiting for test to begin...")
                snap(f"07_wait_{elapsed}")

    # Collect results
    log("Collecting MT5 Strategy Tester results...")
    snap("08_final")

    # Copy any new files
    if os.path.exists(TESTER_LOGS):
        for f in glob.glob(os.path.join(TESTER_LOGS, "*")):
            if os.path.isfile(f) and os.path.getmtime(f) > time.time() - max(elapsed + 120, 600):
                dst = os.path.join(REPORTS, f"mt5_{os.path.basename(f)}")
                shutil.copy2(f, dst)
                log(f"  Copied: {os.path.basename(f)} ({os.path.getsize(f)} bytes)")

    # Check for report files in parent dir
    term_dir = os.path.dirname(TESTER_LOGS)
    for pat in ["*.htm", "*.html", "*.xml"]:
        for f in glob.glob(os.path.join(term_dir, pat)):
            if os.path.getmtime(f) > time.time() - max(elapsed + 120, 600):
                dst = os.path.join(REPORTS, f"mt5_{os.path.basename(f)}")
                shutil.copy2(f, dst)
                log(f"  Report: {os.path.basename(f)}")

    # Summary of DMR cache
    all_dmr = [f for f in glob.glob(os.path.join(TESTER_CACHE, "*"))
               if "DMR" in os.path.basename(f).upper()]
    log(f"DMR cache files: {len(all_dmr)}")
    for f in all_dmr:
        log(f"  {os.path.basename(f)} ({os.path.getsize(f)} bytes)")

    # Also check terminal log for results
    term_logs_dir = r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\logs"
    if os.path.exists(term_logs_dir):
        log_files = [f for f in glob.glob(os.path.join(term_logs_dir, "*.log"))
                     if os.path.getmtime(f) > time.time() - max(elapsed + 120, 600)]
        for lf in log_files:
            log(f"  Terminal log: {os.path.basename(lf)}")
            with open(lf, 'r', errors='replace') as f:
                lines = f.readlines()
            # Look for DMR results in last 30 lines
            for line in lines[-30:]:
                if 'DMR' in line or 'result' in line.lower() or 'trade' in line.lower():
                    log(f"    >> {line.strip()[:120]}")

    log("MT5 test run complete.")

if __name__ == '__main__':
    main()
