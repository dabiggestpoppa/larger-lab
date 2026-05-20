#!/usr/bin/env python3
"""
Click the Start button in MT5 Strategy Tester to begin the backtest.
Uses win32gui to find the button and send a click message.
"""
import ctypes
import ctypes.wintypes as wintypes
import time
import sys

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Constants
WM_COMMAND = 0x0111
BM_CLICK = 0x00F5
GW_CHILD = 5
GW_HWNDNEXT = 2

def find_window_by_title(title):
    """Find a window by its exact title."""
    return user32.FindWindowW(None, title)

def find_window_partial(title_part):
    """Find a window whose title contains the given string."""
    result = []
    def callback(hwnd, extra):
        text = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, text, 256)
        if title_part.lower() in text.value.lower():
            result.append((hwnd, text.value))
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return result

def find_child_windows(parent_hwnd):
    """Find all child windows of a given window."""
    children = []
    def callback(hwnd, extra):
        text = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, text, 256)
        class_name = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, class_name, 256)
        children.append((hwnd, text.value, class_name.value))
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    user32.EnumChildWindows(parent_hwnd, WNDENUMPROC(callback), 0)
    return children

def find_button_by_text(parent_hwnd, button_text):
    """Find a button with specific text."""
    children = find_child_windows(parent_hwnd)
    for hwnd, text, class_name in children:
        if button_text.lower() in text.lower() and 'button' in class_name.lower():
            return hwnd
    return None

def click_button(hwnd):
    """Send a BM_CLICK message to a button."""
    user32.SendMessageW(hwnd, BM_CLICK, 0, 0)

def main():
    print("=" * 50)
    print("MT5 Strategy Tester - Auto Start")
    print("=" * 50)
    
    # Step 1: Find MT5 main window
    print("\n1. Looking for MT5 windows...")
    
    # Try various title patterns
    mt5_hwnd = None
    for title in ["MetaTrader 5", "MetaTrader 5 - OxSecurities-Demo", "MetaTrader 5 - [OxSecurities-Demo]"]:
        mt5_hwnd = find_window_by_title(title)
        if mt5_hwnd:
            print(f"   Found: '{title}' (HWND {mt5_hwnd})")
            break
    
    if not mt5_hwnd:
        # Try partial match
        windows = find_window_partial("MetaTrader")
        if windows:
            mt5_hwnd = windows[0][0]
            print(f"   Found (partial): '{windows[0][1]}' (HWND {mt5_hwnd})")
        else:
            print("   ❌ MT5 window not found!")
            print("   All windows:")
            all_windows = find_window_partial("")
            for hwnd, title in all_windows[:20]:
                if title:
                    print(f"     HWND {hwnd}: {title}")
            return False
    
    # Step 2: Find Strategy Tester window/tab
    print("\n2. Looking for Strategy Tester...")
    
    # The Strategy Tester is a panel within MT5, not a separate window
    # We need to find the "Start" button within the MT5 window
    
    # First, let's enumerate all child windows
    children = find_child_windows(mt5_hwnd)
    print(f"   Found {len(children)} child windows")
    
    # Look for buttons
    buttons = [(hwnd, text, cls) for hwnd, text, cls in children if 'button' in cls.lower()]
    print(f"   Found {len(buttons)} buttons:")
    for hwnd, text, cls in buttons:
        print(f"     HWND {hwnd}: '{text}' ({cls})")
    
    # Look for "Start" button
    start_btn = None
    for hwnd, text, cls in buttons:
        if text.lower() in ['start', 'play', '▶', 'run']:
            start_btn = hwnd
            print(f"   ✅ Found Start button: HWND {hwnd} '{text}'")
            break
    
    if not start_btn:
        # Try deeper search - Strategy Tester might be in a nested panel
        print("   Searching deeper for Start button...")
        for hwnd, text, cls in children:
            sub_children = find_child_windows(hwnd)
            for sub_hwnd, sub_text, sub_cls in sub_children:
                if 'button' in sub_cls.lower() and sub_text.lower() in ['start', 'play', '▶', 'run']:
                    start_btn = sub_hwnd
                    print(f"   ✅ Found Start button (nested): HWND {sub_hwnd} '{sub_text}'")
                    break
            if start_btn:
                break
    
    if not start_btn:
        print("   ❌ Start button not found!")
        print("   Trying to find any clickable element with 'Start' text...")
        
        # Last resort: search ALL windows
        all_windows = find_window_partial("")
        for hwnd, title in all_windows:
            if 'start' in title.lower():
                print(f"     Found window with 'Start': HWND {hwnd} '{title}'")
        
        return False
    
    # Step 3: Click the Start button
    print(f"\n3. Clicking Start button (HWND {start_btn})...")
    
    # Bring MT5 to foreground first
    user32.SetForegroundWindow(mt5_hwnd)
    time.sleep(1)
    
    # Click the button
    click_button(start_btn)
    print("   ✅ Click sent!")
    
    # Wait and verify
    time.sleep(5)
    print("\n4. Waiting for test to begin...")
    print("   Check MT5 for progress bar in Strategy Tester panel")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
