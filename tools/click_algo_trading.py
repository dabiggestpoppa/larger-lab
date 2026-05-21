"""Click the Algo Trading button in MT5 to toggle AutoTrading."""
import win32gui
import win32con
import win32api
import time
import ctypes

def find_mt5():
    result = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if '650898' in title or 'OxSecurities' in title:
                result.append((hwnd, title))
        return True
    win32gui.EnumWindows(callback, None)
    return result

windows = find_mt5()
if not windows:
    print("MT5 not found!")
    exit(1)

hwnd, title = windows[0]
print(f"MT5: {title}")

# Bring MT5 to foreground using ctypes (more reliable)
ctypes.windll.user32.SetForegroundWindow(hwnd)
time.sleep(1)

# Click on the Algo Trading button at approximately (258, 48)
# This is in the toolbar area
x, y = 258, 48

# Convert to LPARAM
lparam = win32api.MAKELONG(x, y)

# Send mouse events
win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
time.sleep(0.1)
win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)

print(f"Clicked at ({x}, {y})")
time.sleep(2)

# Verify by checking terminal info
import MetaTrader5 as mt5
mt5.initialize()
info = mt5.terminal_info()
print(f"AutoTrading: {info.trade_allowed}")
mt5.shutdown()
