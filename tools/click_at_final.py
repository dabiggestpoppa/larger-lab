"""Final attempt: Use AllowSetForegroundWindow + SetForegroundWindow + click."""
import ctypes
import ctypes.wintypes
import time
import sys

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Step 1: Allow any process to set foreground
user32.AllowSetForegroundWindow(-1)
print("ASFW called")

# Find MT5
def find_mt5():
    results = []
    def enum_callback(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            if '650898' in buff.value or 'OxSecurities' in buff.value:
                results.append(hwnd)
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    user32.EnumWindows(WNDENUMPROC(enum_callback), 0)
    return results

mt5_list = find_mt5()
if not mt5_list:
    print("MT5 not found"); sys.exit(1)

hwnd = mt5_list[0]
print(f"MT5: {hwnd}")

# Step 2: Set foreground
result = user32.SetForegroundWindow(hwnd)
print(f"SetForeground: {result}")
time.sleep(1)

fg = user32.GetForegroundWindow()
print(f"Foreground: {fg}, IsMT5: {fg == hwnd}")

# Step 3: Take screenshot to see current state
import win32gui as w32g
import win32ui as w32u
import win32con as w32c
from PIL import Image

screen_w = user32.GetSystemMetrics(0)
screen_h = user32.GetSystemMetrics(1)

def save_screenshot(filename):
    hwndDC = user32.GetDC(0)
    mfcDC = w32u.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    saveBitMap = w32u.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, screen_w, screen_h)
    saveDC.SelectObject(saveBitMap)
    saveDC.BitBlt((0, 0), (screen_w, screen_h), mfcDC, (0, 0), w32c.SRCCOPY)
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
    im.save(filename)
    w32g.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    user32.ReleaseDC(0, hwndDC)

save_screenshot(r'C:\Users\wifik\Desktop\projects\larger-lab\tools\at_step1.png')
print("Screenshot 1 saved")

# Step 4: Click Algo Trading button at (258, 48)
# This is based on MT5 toolbar: second row, Algo Trading button
x, y = 258, 48
user32.SetCursorPos(x, y)
time.sleep(0.3)
user32.mouse_event(0x0002, 0, 0, 0, 0)
time.sleep(0.1)
user32.mouse_event(0x0004, 0, 0, 0, 0)
print(f"Clicked ({x},{y})")
time.sleep(2)

save_screenshot(r'C:\Users\wifik\Desktop\projects\larger-lab\tools\at_step2.png')
print("Screenshot 2 saved")

# Step 5: Check AutoTrading
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
    
    if not info.trade_allowed:
        # Try clicking at different positions
        # The Algo Trading button might be at a different location
        # Let's try a few positions across the toolbar
        for tx in [240, 250, 260, 270, 280, 290, 300, 310, 320]:
            for ty in [40, 45, 50, 55, 60]:
                user32.SetCursorPos(tx, ty)
                time.sleep(0.1)
                user32.mouse_event(0x0002, 0, 0, 0, 0)
                time.sleep(0.05)
                user32.mouse_event(0x0004, 0, 0, 0, 0)
                time.sleep(0.5)
                
                # Check if it worked
                mt5.shutdown()
                mt5.initialize()
                mt5.login(login=cfg['login'], password=cfg['password'], server=cfg['server'])
                info = mt5.terminal_info()
                if info.trade_allowed:
                    print(f"AutoTrading ENABLED after click at ({tx},{ty})!")
                    save_screenshot(r'C:\Users\wifik\Desktop\projects\larger-lab\tools\at_enabled.png')
                    break
            else:
                continue
            break
        else:
            print("Could not enable AutoTrading via clicking")
            save_screenshot(r'C:\Users\wifik\Desktop\projects\larger-lab\tools\at_failed.png')
    
    mt5.shutdown()
except Exception as e:
    print(f"MT5 check error: {e}")
