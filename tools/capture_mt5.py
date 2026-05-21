"""Capture MT5 window screenshot using win32 API."""
import win32gui
import win32ui
import win32con
from PIL import Image
import time

def find_mt5():
    """Find MT5 terminal window."""
    result = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if '650898' in title or 'OxSecurities' in title or 'terminal64' in title:
                result.append((hwnd, title))
        return True
    win32gui.EnumWindows(callback, None)
    return result

def capture_window(hwnd, filename):
    """Capture a specific window."""
    # Get window rect
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top
    
    print(f"Window rect: {rect}, size: {width}x{height}")
    
    # Bring to front
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.5)
    
    # Create DC
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    
    # Create bitmap
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
    saveDC.SelectObject(saveBitMap)
    
    # Copy
    saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
    
    # Save
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    im = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1
    )
    im.save(filename)
    
    # Cleanup
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)
    
    print(f"Saved to {filename}")

windows = find_mt5()
if windows:
    for hwnd, title in windows:
        print(f"Found: {title} (HWND {hwnd})")
        capture_window(hwnd, r'C:\Users\wifik\Desktop\projects\larger-lab\tools\mt5_capture.png')
else:
    print("MT5 not found")
