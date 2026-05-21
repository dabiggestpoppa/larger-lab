"""Activate MT5 window and click AutoTrading button."""
import subprocess
import time
import sys

# First, use PowerShell to minimize Telegram and other windows
# Then activate MT5 and click the button

# Method: Use nircmd if available, otherwise use PowerShell
# Let's try a direct approach with ctypes in Python

import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Find MT5 window
def find_mt5():
    result = []
    def callback(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value
            if '650898' in title or 'OxSecurities' in title or 'terminal64' in title:
                result.append((hwnd, title))
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return result

windows = find_mt5()
if not windows:
    print("ERROR: MT5 not found")
    sys.exit(1)

hwnd, title = windows[0]
    hwnd = hwnd if isinstance(hwnd, int) else int(hwnd)
    print(f"Found MT5: {title} (HWND {hwnd})")

# Get current foreground
fg = user32.GetForegroundWindow()
print(f"Current foreground: {fg}")

# Use Alt+Esc to cycle windows - press Alt, then Esc multiple times
# This is a reliable way to bring a window to front
# Actually, let's use a simpler approach: just minimize the foreground window first

# Minimize current foreground (likely Telegram)
user32.ShowWindow(fg, 6)  # SW_MINIMIZE
time.sleep(0.5)

# Now try to activate MT5
SW_RESTORE = 9
if user32.IsIconic(hwnd):
    user32.ShowWindow(hwnd, SW_RESTORE)
    time.sleep(0.5)

# Set foreground
user32.SetForegroundWindow(hwnd)
time.sleep(1)

# Verify
fg2 = user32.GetForegroundWindow()
print(f"New foreground: {fg2}")

# Take screenshot
import win32gui
import win32ui
import win32con
from PIL import Image

rect = win32gui.GetWindowRect(hwnd)
left, top, right, bottom = rect
width = right - left
height = bottom - top
print(f"Window: {width}x{height} at ({left},{top})")

hwndDC = win32gui.GetWindowDC(hwnd)
mfcDC = win32ui.CreateDCFromHandle(hwndDC)
saveDC = mfcDC.CreateCompatibleDC()
saveBitMap = win32ui.CreateBitmap()
saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
saveDC.SelectObject(saveBitMap)
saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)

bmpinfo = saveBitMap.GetInfo()
bmpstr = saveBitMap.GetBitmapBits(True)
im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
im.save(r'C:\Users\wifik\Desktop\projects\larger-lab\tools\mt5_activated.png')

win32gui.DeleteObject(saveBitMap.GetHandle())
saveDC.DeleteDC()
mfcDC.DeleteDC()
win32gui.ReleaseDC(hwnd, hwndDC)
print("Screenshot saved")
