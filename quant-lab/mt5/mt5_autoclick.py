#!/usr/bin/env python3
"""Auto-click Start in MT5 Strategy Tester"""
import ctypes
import time
import sys

user32 = ctypes.windll.user32

def find_mt5():
    for title in ['MetaTrader 5', 'MetaTrader 5 - OxSecurities-Demo', 'MetaTrader 5 - [OxSecurities-Demo]']:
        hwnd = user32.FindWindowW(None, title)
        if hwnd:
            return hwnd, title
    results = []
    def cb(hwnd, _):
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, buf, 256)
        if 'MetaTrader' in buf.value:
            results.append((hwnd, buf.value))
        return True
    WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    user32.EnumWindows(WNDPROC(cb), 0)
    return results[0] if results else (None, None)

def find_children(parent):
    children = []
    def cb(hwnd, _):
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, buf, 256)
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        children.append((hwnd, buf.value, cls.value))
        return True
    WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    user32.EnumChildWindows(parent, WNDPROC(cb), 0)
    return children

hwnd, title = find_mt5()
if not hwnd:
    print("MT5 not found!")
    sys.exit(1)

print(f"Found: {title} (HWND {hwnd})")

# Bring to front
user32.SetForegroundWindow(hwnd)
time.sleep(1)

# Enumerate ALL child windows recursively
def find_all_children(parent, depth=0):
    results = []
    children = find_children(parent)
    for hwnd_c, text, cls in children:
        indent = "  " * depth
        results.append((hwnd_c, text, cls, depth))
        if depth < 3:
            results.extend(find_all_children(hwnd_c, depth + 1))
    return results

all_children = find_all_children(hwnd)
print(f"Total child windows: {len(all_children)}")

# Find buttons
buttons = [(h, t, c, d) for h, t, c, d in all_children if 'button' in c.lower()]
print(f"\nButtons found: {len(buttons)}")
for h, t, c, d in buttons:
    print(f"  {'  ' * d}HWND {h}: '{t}' ({c})")

# Find Start button
start_hwnd = None
for h, t, c, d in buttons:
    if t.strip().lower() in ['start', 'play', 'run', 'go', '']:
        # Check if it might be the Start button by position or context
        print(f"  Potential Start: HWND {h} '{t}' ({c})")
        if not start_hwnd:
            start_hwnd = h

if start_hwnd:
    print(f"\nClicking Start button (HWND {start_hwnd})...")
    user32.SendMessageW(start_hwnd, 0x00F5, 0, 0)  # BM_CLICK
    print("Clicked!")
else:
    print("\nNo Start button found. Listing all non-empty text windows:")
    for h, t, c, d in all_children:
        if t.strip():
            print(f"  {'  ' * d}HWND {h}: '{t}' ({c})")
