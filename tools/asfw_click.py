"""Use AllowSetForegroundWindow to enable MT5 activation."""
import ctypes
import ctypes.wintypes
import time
import sys

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Allow ANY process to set foreground (ASFW_ANY = -1)
user32.AllowSetForegroundWindow(-1)
print("AllowSetForegroundWindow(-1) called")

# Find MT5
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

# Find all visible windows for debugging
def list_windows():
    results = []
    def enum_callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                results.append((hwnd, buff.value))
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    user32.EnumWindows(WNDENUMPROC(enum_callback), 0)
    return results

windows = list_windows()
print("Visible windows:")
for hwnd, title in windows:
    print(f"  {hwnd}: {title}")

mt5_list = find_mt5()
if not mt5_list:
    print("ERROR: MT5 not found")
    sys.exit(1)

hwnd = mt5_list[0]
print(f"\nMT5 HWND: {hwnd}")

# Try to set foreground now
result = user32.SetForegroundWindow(hwnd)
print(f"SetForegroundWindow result: {result}")
time.sleep(1)

fg = user32.GetForegroundWindow()
print(f"Foreground: {fg}")

# If that didn't work, try simulating Alt+Tab
if fg != hwnd:
    print("\nTrying Alt+Tab approach...")
    # Press Alt
    user32.keybd_event(0x12, 0, 0, 0)  # VK_MENU (Alt)
    time.sleep(0.1)
    # Press Tab
    user32.keybd_event(0x09, 0, 0, 0)  # VK_TAB
    time.sleep(0.1)
    user32.keybd_event(0x09, 0, 2, 0)  # KEYEVENTF_KEYUP
    time.sleep(0.1)
    # Release Alt
    user32.keybd_event(0x12, 0, 2, 0)  # KEYEVENTF_KEYUP
    time.sleep(1)
    
    fg2 = user32.GetForegroundWindow()
    print(f"After Alt+Tab foreground: {fg2}")
    
    # Check if we got MT5
    if fg2 != hwnd:
        # Try more Alt+Tab cycles
        for i in range(5):
            user32.keybd_event(0x12, 0, 0, 0)
            time.sleep(0.05)
            user32.keybd_event(0x09, 0, 0, 0)
            time.sleep(0.05)
            user32.keybd_event(0x09, 0, 2, 0)
            time.sleep(0.05)
            user32.keybd_event(0x12, 0, 2, 0)
            time.sleep(0.5)
            fg3 = user32.GetForegroundWindow()
            print(f"  Alt+Tab {i+1}: foreground = {fg3}")
            if fg3 == hwnd:
                print("  Got MT5!")
                break

# Final check
fg_final = user32.GetForegroundWindow()
print(f"\nFinal foreground: {fg_final}")
print(f"Is MT5: {fg_final == hwnd}")

# Take screenshot
import win32gui as w32gui
import win32ui as w32ui
import win32con as w32con
from PIL import Image

screen_w = user32.GetSystemMetrics(0)
screen_h = user32.GetSystemMetrics(1)
hwndDC = user32.GetDC(0)
mfcDC = w32ui.CreateDCFromHandle(hwndDC)
saveDC = mfcDC.CreateCompatibleDC()
saveBitMap = w32ui.CreateBitmap()
saveBitMap.CreateCompatibleBitmap(mfcDC, screen_w, screen_h)
saveDC.SelectObject(saveBitMap)
saveDC.BitBlt((0, 0), (screen_w, screen_h), mfcDC, (0, 0), w32con.SRCCOPY)
bmpinfo = saveBitMap.GetInfo()
bmpstr = saveBitMap.GetBitmapBits(True)
im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
im.save(r'C:\Users\wifik\Desktop\projects\larger-lab\tools\screen_asfw.png')
w32gui.DeleteObject(saveBitMap.GetHandle())
saveDC.DeleteDC()
mfcDC.DeleteDC()
user32.ReleaseDC(0, hwndDC)
print("Screenshot saved")
