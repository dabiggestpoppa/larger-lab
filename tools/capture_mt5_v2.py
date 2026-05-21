"""Capture MT5 window using PrintWindow API."""
import win32gui
import win32ui
import win32con
import win32api
from PIL import Image
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

def capture_window(hwnd, filename):
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top
    print(f"Window: {width}x{height} at ({left},{top})")
    
    # Use PrintWindow which works even if window is not foreground
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
    saveDC.SelectObject(saveBitMap)
    
    # PrintWindow with PW_RENDERFULLCONTENT
    result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
    print(f"PrintWindow result: {result}")
    
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    im = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1
    )
    im.save(filename)
    
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)
    print(f"Saved to {filename}")

windows = find_mt5()
if windows:
    for hwnd, title in windows:
        print(f"Found: {title}")
        capture_window(hwnd, r'C:\Users\wifik\Desktop\projects\larger-lab\tools\mt5_capture.png')
else:
    print("MT5 not found")
