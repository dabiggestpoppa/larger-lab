"""Find MT5 window using raw Win32 API"""
import ctypes, time
from ctypes import wintypes

user32 = ctypes.windll.user32

def find_mt5():
    results = []
    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    def enum_cb(hwnd, lParam):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value
            if 'OxSecurities' in title or 'MetaTrader' in title:
                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                results.append({
                    'hwnd': hwnd,
                    'title': title,
                    'left': rect.left, 'top': rect.top,
                    'right': rect.right, 'bottom': rect.bottom,
                })
        return True
    user32.EnumWindows(enum_cb, 0)
    return results

def activate_window(hwnd):
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.5)

if __name__ == '__main__':
    wins = find_mt5()
    print(f"Found {len(wins)} MT5 windows")
    for w in wins:
        print(f"  Title: {w['title'][:70]}")
        print(f"  Pos: ({w['left']},{w['top']}) Size: {w['right']-w['left']}x{w['bottom']-w['top']}")
        activate_window(w['hwnd'])
        print("  Activated!")
