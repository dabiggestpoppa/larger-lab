"""Click Algo Trading at the correct position (231, 46)."""
import ctypes
import time

user32 = ctypes.windll.user32

# First, make sure MT5 is still foreground
fg = user32.GetForegroundWindow()
length = user32.GetWindowTextLengthW(fg)
buff = ctypes.create_unicode_buffer(length + 1)
user32.GetWindowTextW(fg, buff, length + 1)
print(f"Foreground: {buff.value}")

# If not MT5, bring it to front
if '650898' not in buff.value and 'OxSecurities' not in buff.value:
    print("MT5 not foreground, finding it...")
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
        user32.ShowWindow(mt5s[0], 9)
        user32.SetForegroundWindow(mt5s[0])
        time.sleep(1)
        print("MT5 brought to front")

# Click Algo Trading button
x, y = 231, 46
print(f"Clicking at ({x}, {y})")

user32.SetCursorPos(x, y)
time.sleep(0.3)
user32.mouse_event(0x0002, 0, 0, 0, 0)
time.sleep(0.15)
user32.mouse_event(0x0004, 0, 0, 0, 0)
time.sleep(2)

# Screenshot
import win32gui as w32g
import win32ui as w32u
import win32con as w32c
from PIL import Image

screen_w = user32.GetSystemMetrics(0)
screen_h = user32.GetSystemMetrics(1)
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
im.save(r'C:\Users\wifik\Desktop\projects\larger-lab\tools\at_clicked3.png')
w32g.DeleteObject(saveBitMap.GetHandle())
saveDC.DeleteDC()
mfcDC.DeleteDC()
user32.ReleaseDC(0, hwndDC)
print("Screenshot saved")

# Check status
import MetaTrader5 as mt5
from pathlib import Path
import json

CONFIG_FILE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_config.json")
with open(CONFIG_FILE) as f:
    cfg = json.load(f)

mt5.initialize()
mt5.login(login=cfg['login'], password=cfg['password'], server=cfg['server'])
info = mt5.terminal_info()
at = info.trade_allowed
print(f"AutoTrading: {at}")

if at:
    print("SUCCESS!")
else:
    print("Still disabled. Trying a grid of positions around the button...")
    # Try a grid around the estimated position
    found = False
    for dx in range(-20, 21, 4):
        for dy in range(-10, 11, 4):
            tx, ty = 231 + dx, 46 + dy
            user32.SetCursorPos(tx, ty)
            time.sleep(0.05)
            user32.mouse_event(0x0002, 0, 0, 0, 0)
            time.sleep(0.05)
            user32.mouse_event(0x0004, 0, 0, 0, 0)
            time.sleep(0.3)
            
            mt5.shutdown()
            mt5.initialize()
            mt5.login(login=cfg['login'], password=cfg['password'], server=cfg['server'])
            info = mt5.terminal_info()
            if info.trade_allowed:
                print(f"SUCCESS at ({tx},{ty})!")
                found = True
                break
        if found:
            break
    
    if not found:
        print("Could not enable AutoTrading via clicking. May need manual toggle.")
    
    mt5.shutdown()
