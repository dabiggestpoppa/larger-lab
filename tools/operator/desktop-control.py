"""
OCE Desktop Control Layer — Phase A
=====================================
Windows-native desktop control: screen capture, input simulation, vision-based UI detection.

Uses:
- Pillow (PIL) for screen capture via ImageGrab
- ctypes (SendInput) for mouse/keyboard simulation
- OpenCV for template matching / UI element detection
- Our existing image tool (vision model) for high-level UI understanding
"""

import ctypes
import ctypes.wintypes
import time
import json
import os
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

# ─── Windows API Constants ───────────────────────────────────────────────────

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000

KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

VK_CODES = {
    "backspace": 0x08, "tab": 0x09, "enter": 0x0D, "shift": 0x10,
    "control": 0x11, "ctrl": 0x11, "alt": 0x12, "escape": 0x1B, "esc": 0x1B,
    "space": 0x20, "pageup": 0x21, "pagedown": 0x22, "end": 0x23,
    "home": 0x24, "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "delete": 0x2E, "del": 0x2E,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77, "f9": 0x78,
    "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
}
for i in range(26):
    VK_CODES[chr(ord('a') + i)] = 0x41 + i
for i in range(10):
    VK_CODES[str(i)] = 0x30 + i


# ─── Windows API Structures ──────────────────────────────────────────────────

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("union", INPUT_UNION)]


# ─── Data Models ─────────────────────────────────────────────────────────────

@dataclass
class ScreenRegion:
    x: int
    y: int
    width: int
    height: int

@dataclass
class UIElement:
    label: str
    x: int
    y: int
    width: int
    height: int
    confidence: float
    element_type: str = "unknown"

@dataclass
class ScreenshotResult:
    path: str
    width: int
    height: int
    timestamp: str
    region: Optional[ScreenRegion] = None


# ─── Screen Capture ──────────────────────────────────────────────────────────

class ScreenCapture:
    """Screen capture using Pillow ImageGrab (reliable on Windows)."""

    def __init__(self, screenshot_dir: Optional[str] = None):
        self.screenshot_dir = screenshot_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", ".openclaw", "screenshots"
        )
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.user32 = ctypes.windll.user32

    def get_screen_size(self) -> Tuple[int, int]:
        width = self.user32.GetSystemMetrics(0)
        height = self.user32.GetSystemMetrics(1)
        return width, height

    def capture(self, region: Optional[ScreenRegion] = None) -> ScreenshotResult:
        from PIL import ImageGrab
        if region:
            bbox = (region.x, region.y, region.x + region.width, region.y + region.height)
        else:
            bbox = None
        img = ImageGrab.grab(bbox=bbox)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(self.screenshot_dir, filename)
        img.save(filepath)
        return ScreenshotResult(
            path=filepath, width=img.width, height=img.height,
            timestamp=datetime.now(timezone.utc).isoformat(), region=region,
        )

    def capture_to_pil(self, region: Optional[ScreenRegion] = None):
        from PIL import ImageGrab
        if region:
            bbox = (region.x, region.y, region.x + region.width, region.y + region.height)
        else:
            bbox = None
        return ImageGrab.grab(bbox=bbox)


# ─── Input Simulation ────────────────────────────────────────────────────────

class InputSimulator:
    """Windows input simulation using SendInput API."""

    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.screen_w = self.user32.GetSystemMetrics(0)
        self.screen_h = self.user32.GetSystemMetrics(1)

    def _send_input(self, *inputs):
        n = len(inputs)
        arr = (INPUT * n)(*inputs)
        self.user32.SendInput(n, ctypes.byref(arr), ctypes.sizeof(INPUT))

    def _abs(self, x: int, y: int) -> Tuple[int, int]:
        return (int(x * 65535 / (self.screen_w - 1)), int(y * 65535 / (self.screen_h - 1)))

    def mouse_move(self, x: int, y: int):
        ax, ay = self._abs(x, y)
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi = MOUSEINPUT(ax, ay, 0, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, 0, None)
        self._send_input(inp)

    def mouse_click(self, x: int, y: int, button: str = "left", double: bool = False):
        self.mouse_move(x, y)
        time.sleep(0.05)
        btn_map = {"left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
                   "right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
                   "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP)}
        if button not in btn_map:
            raise ValueError(f"Unknown button: {button}")
        down_f, up_f = btn_map[button]
        ax, ay = self._abs(x, y)
        d = INPUT(); d.type = INPUT_MOUSE; d.union.mi = MOUSEINPUT(ax, ay, 0, down_f | MOUSEEVENTF_ABSOLUTE, 0, None)
        u = INPUT(); u.type = INPUT_MOUSE; u.union.mi = MOUSEINPUT(ax, ay, 0, up_f | MOUSEEVENTF_ABSOLUTE, 0, None)
        self._send_input(d, u)
        if double:
            time.sleep(0.05)
            self._send_input(d, u)

    def mouse_scroll(self, direction: str = "down", amount: int = 3):
        amt = amount * 120 * (1 if direction == "up" else -1)
        ax, ay = self._abs(self.screen_w // 2, self.screen_h // 2)
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi = MOUSEINPUT(ax, ay, amt, MOUSEEVENTF_WHEEL | MOUSEEVENTF_ABSOLUTE, 0, None)
        self._send_input(inp)

    def mouse_drag(self, from_x: int, from_y: int, to_x: int, to_y: int, duration: float = 0.5):
        self.mouse_move(from_x, from_y)
        time.sleep(0.05)
        ax, ay = self._abs(from_x, from_y)
        d = INPUT(); d.type = INPUT_MOUSE; d.union.mi = MOUSEINPUT(ax, ay, 0, MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_ABSOLUTE, 0, None)
        self._send_input(d)
        steps = max(10, int(duration * 60))
        for i in range(1, steps + 1):
            t = i / steps
            mx = int(from_x + (to_x - from_x) * t)
            my = int(from_y + (to_y - from_y) * t)
            ax, ay = self._abs(mx, my)
            m = INPUT(); m.type = INPUT_MOUSE; m.union.mi = MOUSEINPUT(ax, ay, 0, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, 0, None)
            self._send_input(m)
            time.sleep(duration / steps)
        ax, ay = self._abs(to_x, to_y)
        u = INPUT(); u.type = INPUT_MOUSE; u.union.mi = MOUSEINPUT(ax, ay, 0, MOUSEEVENTF_LEFTUP | MOUSEEVENTF_ABSOLUTE, 0, None)
        self._send_input(u)

    def key_press(self, key: str):
        vk = VK_CODES.get(key.lower())
        if vk is None:
            raise ValueError(f"Unknown key: {key}")
        d = INPUT(); d.type = INPUT_KEYBOARD; d.union.ki = KEYBDINPUT(vk, 0, KEYEVENTF_KEYDOWN, 0, None)
        u = INPUT(); u.type = INPUT_KEYBOARD; u.union.ki = KEYBDINPUT(vk, 0, KEYEVENTF_KEYUP, 0, None)
        self._send_input(d, u)

    def key_combo(self, *keys: str):
        vks = []
        for k in keys:
            vk = VK_CODES.get(k.lower())
            if vk is None:
                raise ValueError(f"Unknown key: {k}")
            vks.append(vk)
        inputs = []
        for vk in vks:
            inp = INPUT(); inp.type = INPUT_KEYBOARD; inp.union.ki = KEYBDINPUT(vk, 0, KEYEVENTF_KEYDOWN, 0, None)
            inputs.append(inp)
        for vk in reversed(vks):
            inp = INPUT(); inp.type = INPUT_KEYBOARD; inp.union.ki = KEYBDINPUT(vk, 0, KEYEVENTF_KEYUP, 0, None)
            inputs.append(inp)
        self._send_input(*inputs)

    def type_text(self, text: str, interval: float = 0.02):
        for char in text:
            if char == '\n':
                self.key_press('enter')
            elif char == '\t':
                self.key_press('tab')
            elif char.isalpha() or char.isdigit() or char == ' ':
                self.key_press(char.lower())
            else:
                d = INPUT(); d.type = INPUT_KEYBOARD; d.union.ki = KEYBDINPUT(0, ord(char), KEYEVENTF_UNICODE, 0, None)
                u = INPUT(); u.type = INPUT_KEYBOARD; u.union.ki = KEYBDINPUT(0, ord(char), KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, None)
                self._send_input(d, u)
            time.sleep(interval)


# ─── UI Element Detection ───────────────────────────────────────────────────

class UIElementDetector:
    """Detect UI elements using OpenCV template matching."""

    def __init__(self):
        self.capturer = ScreenCapture()

    def find_template(self, template_path: str, threshold: float = 0.8,
                      region: Optional[ScreenRegion] = None) -> List[Dict[str, Any]]:
        import cv2
        import numpy as np
        screen_img = self.capturer.capture_to_pil(region)
        screen = cv2.cvtColor(np.array(screen_img), cv2.COLOR_RGB2BGR)
        template = cv2.imread(template_path)
        if template is None:
            raise FileNotFoundError(f"Template not found: {template_path}")
        h, w = template.shape[:2]
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        locs = np.where(result >= threshold)
        matches = []
        for pt_y, pt_x in zip(*locs[::-1] if len(locs) == 2 else zip(*locs)):
            ox = region.x if region else 0
            oy = region.y if region else 0
            matches.append({"x": int(pt_x) + ox, "y": int(pt_y) + ox, "width": w, "height": h,
                            "confidence": float(result[pt_y, pt_x])})
        return matches


# ─── Window Manager ──────────────────────────────────────────────────────────

class WindowManager:
    """Manage Windows: find, focus, list."""

    def __init__(self):
        self.user32 = ctypes.windll.user32

    def get_foreground_window(self) -> Dict[str, Any]:
        hwnd = self.user32.GetForegroundWindow()
        length = self.user32.GetWindowTextLengthW(hwnd) + 1
        buf = ctypes.create_unicode_buffer(length)
        self.user32.GetWindowTextW(hwnd, buf, length)
        rect = ctypes.wintypes.RECT()
        self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return {"hwnd": hwnd, "title": buf.value,
                "x": rect.left, "y": rect.top,
                "width": rect.right - rect.left, "height": rect.bottom - rect.top}

    def find_window(self, title_substring: str) -> Optional[Dict[str, Any]]:
        results = []
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong, ctypes.POINTER(ctypes.c_int))
        def cb(hwnd, _):
            length = self.user32.GetWindowTextLengthW(hwnd) + 1
            buf = ctypes.create_unicode_buffer(length)
            self.user32.GetWindowTextW(hwnd, buf, length)
            if title_substring.lower() in buf.value.lower():
                rect = ctypes.wintypes.RECT()
                self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                results.append({"hwnd": hwnd, "title": buf.value,
                                "x": rect.left, "y": rect.top,
                                "width": rect.right - rect.left, "height": rect.bottom - rect.top})
            return True
        self.user32.EnumWindows(WNDENUMPROC(cb), 0)
        return results[0] if results else None

    def focus_window(self, hwnd: int):
        self.user32.SetForegroundWindow(hwnd)

    def list_windows(self) -> List[Dict[str, Any]]:
        results = []
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong, ctypes.POINTER(ctypes.c_int))
        def cb(hwnd, _):
            if self.user32.IsWindowVisible(hwnd):
                length = self.user32.GetWindowTextLengthW(hwnd) + 1
                buf = ctypes.create_unicode_buffer(length)
                self.user32.GetWindowTextW(hwnd, buf, length)
                if buf.value:
                    rect = ctypes.wintypes.RECT()
                    self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    results.append({"hwnd": hwnd, "title": buf.value,
                                    "x": rect.left, "y": rect.top,
                                    "width": rect.right - rect.left, "height": rect.bottom - rect.top})
            return True
        self.user32.EnumWindows(WNDENUMPROC(cb), 0)
        return results


# ─── High-Level Desktop Controller ──────────────────────────────────────────

class DesktopController:
    def __init__(self):
        self.screen = ScreenCapture()
        self.input = InputSimulator()
        self.windows = WindowManager()
        self.detector = UIElementDetector()

    def screenshot(self, region: Optional[Dict] = None) -> ScreenshotResult:
        r = ScreenRegion(**region) if region else None
        return self.screen.capture(r)

    def click(self, x: int, y: int, button: str = "left", double: bool = False):
        self.input.mouse_click(x, y, button, double)

    def type(self, text: str, interval: float = 0.02):
        self.input.type_text(text, interval)

    def hotkey(self, *keys: str):
        self.input.key_combo(*keys)

    def scroll(self, direction: str = "down", amount: int = 3):
        self.input.mouse_scroll(direction, amount)

    def drag(self, from_x: int, from_y: int, to_x: int, to_y: int, duration: float = 0.5):
        self.input.mouse_drag(from_x, from_y, to_x, to_y, duration)

    def find_window(self, title: str) -> Optional[Dict]:
        return self.windows.find_window(title)

    def focus_window(self, title: str) -> bool:
        win = self.windows.find_window(title)
        if win:
            self.windows.focus_window(win["hwnd"])
            return True
        return False

    def list_windows(self) -> List[Dict]:
        return self.windows.list_windows()

    def find_on_screen(self, template_path: str, threshold: float = 0.8) -> List[Dict]:
        return self.detector.find_template(template_path, threshold)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="OCE Desktop Control Layer")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("screenshot")
    p.add_argument("--region", help="x,y,w,h")

    p = sub.add_parser("click")
    p.add_argument("x", type=int); p.add_argument("y", type=int)
    p.add_argument("--button", default="left"); p.add_argument("--double", action="store_true")

    p = sub.add_parser("type")
    p.add_argument("text")

    p = sub.add_parser("hotkey")
    p.add_argument("keys", nargs="+")

    p = sub.add_parser("scroll")
    p.add_argument("--direction", default="down"); p.add_argument("--amount", type=int, default=3)

    p = sub.add_parser("window")
    p.add_argument("action", choices=["list", "find", "focus"])
    p.add_argument("--title")

    p = sub.add_parser("find")
    p.add_argument("template")
    p.add_argument("--threshold", type=float, default=0.8)

    args = parser.parse_args()
    dc = DesktopController()

    if args.command == "screenshot":
        region = None
        if args.region:
            parts = [int(p) for p in args.region.split(",")]
            region = {"x": parts[0], "y": parts[1], "width": parts[2], "height": parts[3]}
        r = dc.screenshot(region)
        print(json.dumps(asdict(r), indent=2))
    elif args.command == "click":
        dc.click(args.x, args.y, args.button, args.double)
        print(f"Clicked ({args.x}, {args.y})")
    elif args.command == "type":
        dc.type(args.text)
        print(f"Typed: {args.text}")
    elif args.command == "hotkey":
        dc.hotkey(*args.keys)
        print(f"Pressed: {'+'.join(args.keys)}")
    elif args.command == "scroll":
        dc.scroll(args.direction, args.amount)
        print(f"Scrolled {args.direction} {args.amount}")
    elif args.command == "window":
        if args.action == "list":
            for w in dc.list_windows():
                print(f"  {w['title']!r} @ ({w['x']},{w['y']}) {w['width']}x{w['height']}")
        elif args.action == "find":
            if not args.title:
                print("Need --title"); sys.exit(1)
            w = dc.find_window(args.title)
            print(json.dumps(w, indent=2, default=str) if w else f"Not found: {args.title}")
        elif args.action == "focus":
            if not args.title:
                print("Need --title"); sys.exit(1)
            print(f"Focused: {dc.focus_window(args.title)}")
    elif args.command == "find":
        matches = dc.find_on_screen(args.template, args.threshold)
        print(json.dumps(matches, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
