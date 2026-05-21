"""Capture ONLY the MT5 window using its HWND."""
import ctypes
import ctypes.wintypes
import time
import win32gui as w32g
import win32ui as w32u
import win32con as w32c
from PIL import Image

user32 = ctypes.windll.user32

# Find MT5
def find_mt5():
    results = []
    def cb(hwnd, _):
        l = user32.GetWindowTextLengthW(hwnd)
        if l > 0:
            b = ctypes.create_unicode_buffer(l + 1)
            user32.GetWindowTextW(hwnd, b, l + 1)
            if '650898' in b.value:
                results.append(hwnd)
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return results

mt5s = find_mt5()
if not mt5s:
    print("MT5 not found")
    exit(1)

hwnd = mt5s[0]
print(f"MT5 HWND: {hwnd}")

# Get window rect
rect = w32g.GetWindowRect(hwnd)
left, top, right, bottom = rect
width = right - left
height = bottom - top
print(f"Rect: {rect}, Size: {width}x{height}")

# Use PrintWindow to capture just the MT5 window
hwndDC = w32g.GetWindowDC(hwnd)
mfcDC = w32u.CreateDCFromHandle(hwndDC)
saveDC = mfcDC.CreateCompatibleDC()
saveBitMap = w32u.CreateBitmap()
saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
saveDC.SelectObject(saveBitMap)

# PrintWindow with PW_RENDERFULLCONTENT (2)
result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
print(f"PrintWindow result: {result}")

bmpinfo = saveBitMap.GetInfo()
bmpstr = saveBitMap.GetBitmapBits(True)
im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)

# Save full window
im.save(r'C:\Users\wifik\Desktop\projects\larger-lab\tools\mt5_full.png')

# Save top 150px crop
im_top = im.crop((0, 0, width, 150))
im_top.save(r'C:\Users\wifik\Desktop\projects\larger-lab\tools\mt5_top_only.png')

w32g.DeleteObject(saveBitMap.GetHandle())
saveDC.DeleteDC()
mfcDC.DeleteDC()
w32g.ReleaseDC(hwnd, hwndDC)
print(f"Saved: mt5_full.png ({width}x{height}), mt5_top_only.png ({width}x150)")
