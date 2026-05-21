"""Force MT5 to foreground and click AutoTrading button."""
import ctypes
import ctypes.wintypes
import time
import sys

# Load libraries
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Constants
SW_RESTORE = 9
SW_MINIMIZE = 6
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001

# Find MT5 window
def find_mt5():
    results = []
    def enum_callback(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value
            if '650898' in title or 'OxSecurities' in title:
                results.append(hwnd)
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    user32.EnumWindows(WNDENUMPROC(enum_callback), 0)
    return results

mt5_list = find_mt5()
if not mt5_list:
    print("ERROR: MT5 not found")
    sys.exit(1)

hwnd = mt5_list[0]
print(f"MT5 HWND: {hwnd}")

# Get window info
rect = ctypes.wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(rect))
width = rect.right - rect.left
height = rect.bottom - rect.top
print(f"Window: {width}x{height} at ({rect.left},{rect.top})")

# Step 1: Minimize Telegram (current foreground)
fg = user32.GetForegroundWindow()
print(f"Current foreground: {fg}")
user32.ShowWindow(fg, SW_MINIMIZE)
time.sleep(0.5)

# Step 2: Restore MT5 if minimized
if user32.IsIconic(hwnd):
    user32.ShowWindow(hwnd, SW_RESTORE)
    time.sleep(0.5)

# Step 3: Force foreground using thread attachment
# Get thread IDs
fg2 = user32.GetForegroundWindow()
fg_thread = user32.GetWindowThreadProcessId(fg2, None)
current_thread = kernel32.GetCurrentThreadId()

print(f"FG thread: {fg_thread}, Current thread: {current_thread}")

# Attach and set foreground
user32.AttachThreadInput(current_thread, fg_thread, True)
result = user32.SetForegroundWindow(hwnd)
user32.AttachThreadInput(current_thread, fg_thread, False)
print(f"SetForegroundWindow result: {result}")
time.sleep(1)

# Verify
fg3 = user32.GetForegroundWindow()
print(f"New foreground: {fg3}")

# Step 4: Take screenshot to see what we're working with
import win32gui
import win32ui
import win32con
from PIL import Image

# Full screen screenshot
screen_w = user32.GetSystemMetrics(0)
screen_h = user32.GetSystemMetrics(1)
hwndDC = user32.GetDC(0)
mfcDC = win32ui.CreateDCFromHandle(hwndDC)
saveDC = mfcDC.CreateCompatibleDC()
saveBitMap = win32ui.CreateBitmap()
saveBitMap.CreateCompatibleBitmap(mfcDC, screen_w, screen_h)
saveDC.SelectObject(saveBitMap)
saveDC.BitBlt((0, 0), (screen_w, screen_h), mfcDC, (0, 0), win32con.SRCCOPY)
bmpinfo = saveBitMap.GetInfo()
bmpstr = saveBitMap.GetBitmapBits(True)
im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
im.save(r'C:\Users\wifik\Desktop\projects\larger-lab\tools\screen_fg.png')
win32gui.DeleteObject(saveBitMap.GetHandle())
saveDC.DeleteDC()
mfcDC.DeleteDC()
user32.ReleaseDC(0, hwndDC)
print("Screenshot saved")

# Step 5: Click the Algo Trading button
# Based on MT5 toolbar layout, the Algo Trading button is in the second row
# Approximately at x=258, y=48 (relative to screen since MT5 is fullscreen at 0,0)
x, y = 258, 48
print(f"Clicking at ({x}, {y})")

# Move cursor
user32.SetCursorPos(x, y)
time.sleep(0.3)

# Click
user32.mouse_event(0x0002, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
time.sleep(0.1)
user32.mouse_event(0x0004, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP
time.sleep(2)

# Step 6: Take after screenshot
hwndDC2 = user32.GetDC(0)
mfcDC2 = win32ui.CreateDCFromHandle(hwndDC2)
saveDC2 = mfcDC2.CreateCompatibleDC()
saveBitMap2 = win32ui.CreateBitmap()
saveBitMap2.CreateCompatibleBitmap(mfcDC2, screen_w, screen_h)
saveDC2.SelectObject(saveBitMap2)
saveDC2.BitBlt((0, 0), (screen_w, screen_h), mfcDC2, (0, 0), win32con.SRCCOPY)
bmpinfo2 = saveBitMap2.GetInfo()
bmpstr2 = saveBitMap2.GetBitmapBits(True)
im2 = Image.frombuffer('RGB', (bmpinfo2['bmWidth'], bmpinfo2['bmHeight']), bmpstr2, 'raw', 'BGRX', 0, 1)
im2.save(r'C:\Users\wifik\Desktop\projects\larger-lab\tools\screen_after_click.png')
win32gui.DeleteObject(saveBitMap2.GetHandle())
saveDC2.DeleteDC()
mfcDC2.DeleteDC()
user32.ReleaseDC(0, hwndDC2)
print("After-click screenshot saved")

# Step 7: Check AutoTrading status
try:
    import MetaTrader5 as mt5
    from pathlib import Path
    import json
    CONFIG_FILE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_config.json")
    with open(CONFIG_FILE) as f:
        cfg = json.load(f)
    mt5.initialize()
    mt5.login(login=cfg['login'], password=cfg['password'], server=cfg['server'])
    info = mt5.terminal_info()
    print(f"AutoTrading: {info.trade_allowed}")
    mt5.shutdown()
except Exception as e:
    print(f"Could not check MT5 status: {e}")
