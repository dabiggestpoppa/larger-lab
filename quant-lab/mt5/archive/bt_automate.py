"""
MT5 Strategy Tester Automation via pyautogui
Opens MT5, configures Strategy Tester from .ini, runs test, captures results.
"""
import sys, os, time, subprocess, glob, shutil
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

import pyautogui

# ── Config ─────────────────────────────────────────────────────────
MT5_EXE     = r"C:\Program Files\Ox Securities MetaTrader 5\terminal64.exe"
PROFILES    = r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\MQL5\Profiles\Tester"
EXPERTS     = r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\MQL5\Experts"
TESTER_LOGS = r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\Tester\logs"
TESTER_CACHE= r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\Tester\cache"
WORKSPACE   = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5"
REPORTS_DIR = os.path.join(WORKSPACE, "reports")

EA_NAME     = "DMR_FULL_BACKTEST"
INI_FILE    = os.path.join(PROFILES, "DMR_FULL_BACKTEST.EURUSD.PRO.M5.20240101_20240131.000.ini")

pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True

# ── Helpers ────────────────────────────────────────────────────────
def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def wait_for_window(title_keyword, timeout=30):
    """Wait for a window with title containing keyword"""
    log(f"Waiting for window: '{title_keyword}'")
    start = time.time()
    while time.time() - start < timeout:
        try:
            wins = pyautogui.getWindowsWithTitle(title_keyword)
            if wins:
                log(f"  Found: {wins[0].title}")
                return wins[0]
        except Exception:
            pass
        time.sleep(1)
    log(f"  TIMEOUT waiting for '{title_keyword}'")
    return None

def click_at(x, y, delay=0.5):
    pyautogui.click(x, y)
    time.sleep(delay)

def take_screenshot(name="screen"):
    path = os.path.join(WORKSPACE, f"{name}_{int(time.time())}.png")
    pyautogui.screenshot(path)
    log(f"Screenshot: {path}")
    return path

# ── Main Flow ──────────────────────────────────────────────────────
def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    log("="*60)
    log("MT5 Strategy Tester Automation")
    log(f"EA: {EA_NAME}")
    log("="*60)
    
    # Step 1: Kill any existing MT5
    log("Step 1: Killing existing MT5...")
    subprocess.run(['taskkill', '/IM', 'terminal64.exe', '/F'], capture_output=True)
    time.sleep(3)
    
    # Step 2: Launch MT5
    log("Step 2: Launching MT5...")
    subprocess.Popen([MT5_EXE], cwd=os.path.dirname(MT5_EXE))
    
    # Wait for MT5 main window
    win = wait_for_window("Ox Securities", timeout=30)
    if not win:
        log("ERROR: MT5 window not found!")
        sys.exit(1)
    
    time.sleep(5)  # Wait for full init + auto-login
    log("MT5 loaded and connected")
    take_screenshot("mt5_loaded")
    
    # Step 3: Open Strategy Tester
    # Method: Use keyboard shortcut Ctrl+R (standard MT5 shortcut for Strategy Tester)
    # Or: Menu -> View -> Strategy Tester
    log("Step 3: Opening Strategy Tester...")
    
    # Try Ctrl+R first
    pyautogui.hotkey('ctrl', 'r')
    time.sleep(3)
    
    # Check if Strategy Tester panel appeared
    # The Strategy Tester is a panel at the bottom of MT5
    # We need to verify it's open by looking for its controls
    take_screenshot("after_ctrl_r")
    
    # Alternative: Use menu navigation
    # View -> Strategy Tester
    # In MT5, the menu bar is at the top
    # Let's try clicking "View" menu
    # First, let's find the MT5 window position
    win = wait_for_window("Ox Securities", timeout=5)
    if win:
        log(f"Window: {win.title} at ({win.left},{win.top}) size {win.width}x{win.height}")
        
        # The Strategy Tester can also be opened from the menu bar
        # "View" menu is typically the 3rd or 4th menu item
        # Let's try the keyboard shortcut F6 (another common MT5 shortcut for Tester)
        # Actually, let's use the menu: Alt+V (View), then S (Strategy Tester)
        pyautogui.hotkey('alt', 'v')
        time.sleep(0.5)
        pyautogui.press('s')
        time.sleep(3)
        take_screenshot("after_menu_tester")
    
    # Step 4: Configure the Strategy Tester
    # We need to:
    # a) Select our EA from the dropdown
    # b) Set symbol, period, dates
    # c) Click Start
    
    log("Step 4: Configuring Strategy Tester...")
    
    # Take a screenshot to see the current state
    take_screenshot("tester_config")
    
    # The Strategy Tester panel has these controls (top to bottom):
    # - Expert Advisor dropdown
    # - Symbol dropdown  
    # - Period dropdown
    # - From/To date fields
    # - Execution mode
    # - Start button
    
    # Since GUI automation is fragile, let's use a smarter approach:
    # MT5 Strategy Tester remembers the last used settings
    # Our .ini file is already in Profiles/Tester
    # We just need to select the EA and click Start
    
    # Actually, the most reliable approach: use the .ini file that MT5 reads
    # when you select from the Strategy Tester's dropdown
    # MT5 auto-loads .ini files from Profiles/Tester into the dropdown
    
    # Let's try to find and click the EA dropdown
    # The dropdown is in the Strategy Tester panel at the bottom
    
    # For now, let's use a semi-automated approach:
    # 1. Click on the EA name field in Strategy Tester
    # 2. Type the EA name to search
    # 3. Select it
    # 4. Click Start
    
    log("Attempting to configure EA in Strategy Tester...")
    
    # Get screen size
    screen_w, screen_h = pyautogui.size()
    log(f"Screen: {screen_w}x{screen_h}")
    
    # The Strategy Tester panel is at the bottom of the MT5 window
    # The "Expert" dropdown is typically at the top-left of the panel
    # Let's click in the Strategy Tester area
    
    # First, let's bring MT5 to foreground
    try:
        win = pyautogui.getWindowsWithTitle("Ox Securities")[0]
        win.activate()
        time.sleep(1)
    except Exception as e:
        log(f"Could not activate window: {e}")
    
    take_screenshot("before_config")
    
    # Strategy Tester panel is typically at the bottom 200-300px of the terminal
    # The "Expert" field is at the top-left of that panel
    # Let's estimate: panel starts at ~60% of window height
    
    if win:
        panel_top = win.top + int(win.height * 0.6)
        # Click on Expert dropdown area (left side of panel)
        expert_x = win.left + 150
        expert_y = panel_top + 20
        log(f"Clicking Expert dropdown at ({expert_x}, {expert_y})")
        click_at(expert_x, expert_y)
        time.sleep(1)
        
        # Type the EA name
        pyautogui.typewrite(EA_NAME, interval=0.05)
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(1)
        
        take_screenshot("after_ea_select")
        
        # Now click the Start button
        # Start button is typically at the right side of the Strategy Tester panel
        start_x = win.left + win.width - 100
        start_y = panel_top + 20
        log(f"Clicking Start at ({start_x}, {start_y})")
        click_at(start_x, start_y)
        time.sleep(2)
        
        take_screenshot("after_start")
    
    # Step 5: Monitor test progress
    log("Step 5: Monitoring test progress...")
    log("Waiting for test to complete (checking every 30s)...")
    
    max_wait = 600  # 10 min
    check_interval = 30
    elapsed = 0
    last_cache_count = len(glob.glob(os.path.join(TESTER_CACHE, "*")))
    
    while elapsed < max_wait:
        time.sleep(check_interval)
        elapsed += check_interval
        
        # Check if MT5 still running
        r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal64.exe'],
                           capture_output=True, text=True)
        if 'terminal64' not in r.stdout:
            log(f"MT5 closed after {elapsed}s")
            break
        
        # Check for new cache files
        current_cache = glob.glob(os.path.join(TESTER_CACHE, "*DMR*"))
        all_cache = glob.glob(os.path.join(TESTER_CACHE, "*"))
        
        log(f"  [{elapsed}s] Cache: {len(all_cache)} files | DMR files: {len(current_cache)}")
        
        if current_cache:
            log(f"  DMR cache files found!")
            for f in current_cache:
                log(f"    {os.path.basename(f)}")
            break
    
    # Step 6: Collect results
    log("Step 6: Collecting results...")
    
    # Check for HTML/XML reports
    htm_files = glob.glob(os.path.join(TESTER_LOGS, "*.htm"))
    xml_files = glob.glob(os.path.join(TESTER_LOGS, "*.xml"))
    
    if htm_files:
        latest_htm = max(htm_files, key=os.path.getmtime)
        dst = os.path.join(REPORTS_DIR, os.path.basename(latest_htm))
        shutil.copy2(latest_htm, dst)
        log(f"HTML report: {dst}")
    
    # Check for new cache files with DMR data
    dmr_cache = glob.glob(os.path.join(TESTER_CACHE, "*DMR*"))
    if dmr_cache:
        log(f"DMR cache files: {len(dmr_cache)}")
        for f in dmr_cache:
            log(f"  {os.path.basename(f)} ({os.path.getsize(f)} bytes)")
    
    # Parse the terminal log for results
    term_logs = glob.glob(os.path.join(
        r"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\logs", "*.log"
    ))
    if term_logs:
        latest = max(term_logs, key=os.path.getmtime)
        with open(latest, 'r', errors='replace') as f:
            lines = f.readlines()
        # Look for test results in last 50 lines
        for line in lines[-50:]:
            if any(kw in line.lower() for kw in ['test', 'result', 'profit', 'deal', 'complete', 'error']):
                log(f"  LOG: {line.strip()}")
    
    take_screenshot("final_state")
    log("Automation complete.")

if __name__ == '__main__':
    main()
