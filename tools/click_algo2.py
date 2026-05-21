"""Click the Algo Trading button at the correct position (340, 106)."""
import ctypes
import time

user32 = ctypes.windll.user32

# Click Algo Trading button at the correct position
x, y = 340, 106
print(f"Clicking Algo Trading at ({x}, {y})")

user32.SetCursorPos(x, y)
time.sleep(0.3)
user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
time.sleep(0.1)
user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
time.sleep(2)

# Take screenshot
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
im.save(r'C:\Users\wifik\Desktop\projects\larger-lab\tools\at_clicked2.png')
w32g.DeleteObject(saveBitMap.GetHandle())
saveDC.DeleteDC()
mfcDC.DeleteDC()
user32.ReleaseDC(0, hwndDC)
print("Screenshot saved")

# Check AutoTrading status
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

if info.trade_allowed:
    print("SUCCESS! AutoTrading is now ENABLED!")
else:
    print("Still disabled. The button might need a different interaction.")
    # Check the terminal for any messages
    import sqlite3
    conn = sqlite3.connect(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db')
    c = conn.cursor()
    c.execute('SELECT timestamp, message FROM system_log ORDER BY id DESC LIMIT 5')
    print("\nRecent DMR log:")
    for ts, msg in c.fetchall():
        print(f"  {ts}: {msg}")
    conn.close()

mt5.shutdown()
