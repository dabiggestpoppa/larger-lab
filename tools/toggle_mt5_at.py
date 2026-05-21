"""
Toggle MT5 AutoTrading using the MT5 Python API.
The terminal_info().trade_allowed flag reflects the AutoTrading state.
We can't directly toggle it via Python API, but we can use UI automation.
"""
import subprocess
import time

# Method 1: Try using MT5's built-in command via terminal
# MT5 doesn't have a direct Python API to toggle AutoTrading
# We need to use UI automation

# Method 2: Use pyautogui to click the AutoTrading button
try:
    import pyautogui
    import win32gui
    import win32con
    
    # Find MT5 window
    def find_mt5_window():
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if '650898' in title or 'OxSecurities' in title or 'terminal64' in title:
                    windows.append(hwnd)
            return True
        windows = []
        win32gui.EnumWindows(callback, windows)
        return windows
    
    mt5_windows = find_mt5_window()
    if mt5_windows:
        hwnd = mt5_windows[0]
        print(f"Found MT5 window: {win32gui.GetWindowText(hwnd)}")
        
        # Bring to front
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(1)
        
        # Take screenshot to see the current state
        screenshot = pyautogui.screenshot()
        screenshot.save(r"C:\Users\wifik\Desktop\projects\larger-lab\tools\mt5_screenshot.png")
        print("Screenshot saved")
        
        # The AutoTrading button is typically in the toolbar
        # Common location: top toolbar, looks like a green/red play button
        # We need to find it visually
        
        # Try common keyboard shortcut: Ctrl+Shift+A (some MT5 builds)
        # Or look for the button in the toolbar
        
        # Get window rect
        rect = win32gui.GetWindowRect(hwnd)
        print(f"Window rect: {rect}")
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        print(f"Window size: {width}x{height}")
        
        # The AutoTrading button is usually in the top toolbar area
        # Typically around x=300-400, y=30-50 from the window top-left
        # But this varies by MT5 skin/theme
        
        # Let's try to find it by looking for the button area
        # Common MT5 toolbar: File, View, Insert, Charts, Tools, Window, Help
        # AutoTrading button is usually between the main toolbar and the symbol list
        
        print("Attempting to find AutoTrading button...")
        
        # Try clicking common AutoTrading button positions
        # Position 1: Standard toolbar area
        for x_offset in [350, 380, 410, 440, 470, 500]:
            y_offset = 35
            x = rect[0] + x_offset
            y = rect[1] + y_offset
            print(f"  Trying position ({x}, {y})...")
        
        print("\nUI automation approach needs visual identification.")
        print("Will use browser/screenshot approach instead.")
        
    else:
        print("MT5 window not found")
        
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install pyautogui pywin32")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
