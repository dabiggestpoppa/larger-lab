import ctypes
import time
import win32gui as w32g
import win32ui as w32u
import win32con as w32c
from PIL import Image

user32 = ctypes.windll.user32

# Find MT5 and bring to front
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
if mt5s:
    hwnd = mt5s[0]
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)
    time.sleep(1)
    
    # Get window rect
    rect = w32g.GetWindowRect(hwnd)
    print(f"MT5 rect: {rect}")
    
    # Capture just the top 120 pixels of MT5
    left, top, right, bottom = rect
    width = right - left
    crop_height = 120
    
    hwndDC = user32.GetDC(0)
    mfcDC = w32u.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    saveBitMap = w32u.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, width, crop_height)
    saveDC.SelectObject(saveBitMap)
    saveDC.BitBlt((0, 0), (width, crop_height), mfcDC, (left, top), w32c.SRCCOPY)
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
    im.save(r'C:\Users\wifik\Desktop\projects\larger-lab\tools\mt5_top.png')
    w32g.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    user32.ReleaseDC(0, hwndDC)
    print(f"Saved top crop: {width}x{crop_height}")
else:
    print("MT5 not found")
