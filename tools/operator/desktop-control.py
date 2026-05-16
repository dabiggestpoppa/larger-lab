"""
OCE Desktop Control Layer — Phase A
=====================================
Windows-native desktop control: screen capture, input simulation, vision-based UI detection.

Uses:
- Pillow (PIL) for screen capture
- ctypes (SendInput) for mouse/keyboard simulation
- OpenCV for template matching / UI element detection
- Our existing image tool (vision model) for high-level UI understanding

All Windows-native. No external dependencies beyond what's already installed.
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

# SendInput constants
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

# Mouse event flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_ABSOLUTE = 0x8000

# Keyboard event flags
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# Virtual key codes (common ones)
VK_CODES = {
    "backspace": 0x08, "tab": 0x09, "enter": 0x0D, "shift": 0x10,
    "control": 0x11, "ctrl": 0x11, "alt": 0x12, "escape": 0x1B,
    "space": 0x20, "pageup": 0x21, "pagedown": 0x22, "end": 0x23,
    "home": 0x24, "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "delete": 0x2E, "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77, "f9": 0x78,
    "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
}

# Map printable characters to VK codes
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
    element_type: str  # "button", "text_field", "menu", "icon", "window", etc.

@dataclass
class ScreenshotResult:
    path: str
    width: int
    height: int
    timestamp: str
    region: Optional[ScreenRegion] = None


# ─── Screen Capture ──────────────────────────────────────────────────────────

class ScreenCapture:
    """Windows screen capture using ctypes + GDI (no pyautogui needed)."""

    def __init__(self, screenshot_dir: Optional[str] = None):
        self.screenshot_dir = screenshot_dir or os.path.join(
            os.path.dirname(__file__), "..", "..", ".openclaw", "screenshots"
        )
        os.makedirs(self.screenshot_dir, exist_ok=True)

        # Load GDI32 and User32
        self.gdi32 = ctypes.windll.gdi32
        self.user32 = ctypes.windll.user32

    def get_screen_size(self) -> Tuple[int, int]:
        """Get primary screen resolution."""
        width = self.user32.GetSystemMetrics(0)
        height = self.user32.GetSystemMetrics(1)
        return width, height

    def capture(self, region: Optional[ScreenRegion] = None) -> ScreenshotResult:
        """
        Capture screen or a region. Returns ScreenshotResult with file path.
        Uses GDI BitBlt for fast capture.
        """
        from PIL import Image

        screen_w, screen_h = self.get_screen_size()

        if region:
            x, y, w, h = region.x, region.y, region.width, region.height
        else:
            x, y, w, h = 0, 0, screen_w, screen_h

        # GDI screen capture
        hdc_screen = self.user32.GetDC(0)
        hdc_mem = self.gdi32.CreateCompatibleDC(hdc_screen)
        hbitmap = self.gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
        self.gdi32.SelectObject(hdc_mem, hbitmap)
        self.gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_screen, x, y, 0x00CC0020)  # SRCCOPY

        # Convert to PIL Image
        bmp_info = ctypes.create_string_buffer(40)
        ctypes.memmove(bmp_info, bytes([40, 0, 0, 0]), 4)
        self.gdi32.GetDIBits(hdc_mem, hbitmap, 0, h, None, bmp_info, 0)

        # Get bitmap info
        bi = ctypes.cast(bmp_info, ctypes.POINTER(ctypes.c_int32))
        bmp_w = bi[1]
        bmp_h = bi[2]
        bit_count = bi[4] & 0xFFFF

        # Read pixel data
        row_size = ((bmp_w * bit_count + 31) // 32) * 4
        buffer_size = row_size * abs(bmp_h)
        buffer = ctypes.create_string_buffer(buffer_size)
        self.gdi32.GetDIBits(hdc_mem, hbitmap, 0, abs(bmp_h), buffer, bmp_info, 0)

        # Create PIL image (BGR -> RGB)
        img = Image.frombuffer("RGB", (bmp_w, abs(bmp_h)), buffer, "raw", "BGRX", 0, 1)

        # Save
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(self.screenshot_dir, filename)
        img.save(filepath)

        # Cleanup
        self.gdi32.DeleteObject(hbitmap)
        self.gdi32.DeleteDC(hdc_mem)
        self.user32.ReleaseDC(0, hdc_screen)

        return ScreenshotResult(
            path=filepath,
            width=img.width,
            height=img.height,
            timestamp=datetime.now(timezone.utc).isoformat(),
            region=region,
        )

    def capture_to_pil(self, region: Optional[ScreenRegion] = None):
        """Capture screen and return PIL Image directly (no file save)."""
        from PIL import Image

        screen_w, screen_h = self.get_screen_size()
        if region:
            x, y, w, h = region.x, region.y, region.width, region.height
        else:
            x, y, w, h = 0, 0, screen_w, screen_h

        hdc_screen = self.user32.GetDC(0)
        hdc_mem = self.gdi32.CreateCompatibleDC(hdc_screen)
        hbitmap = self.gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
        self.gdi32.SelectObject(hdc_mem, hbitmap)
        self.gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_screen, x, y, 0x00CC0020)

        bmp_info = ctypes.create_string_buffer(40)
        ctypes.memmove(bmp_info, bytes([40, 0, 0, 0]), 4)
        self.gdi32.GetDIBits(hdc_mem, hbitmap, 0, h, None, bmp_info, 0)

        bi = ctypes.cast(bmp_info, ctypes.POINTER(ctypes.c_int32))
        bmp_w = bi[1]
        bmp_h = bi[2]
        bit_count = bi[4] & 0xFFFF
        row_size = ((bmp_w * bit_count + 31) // 32) * 4
        buffer_size = row_size * abs(bmp_h)
        buffer = ctypes.create_string_buffer(buffer_size)
        self.gdi32.GetDIBits(hdc_mem, hbitmap, 0, abs(bmp_h), buffer, bmp_info, 0)

        img = Image.frombuffer("RGB", (bmp_w, abs(bmp_h)), buffer, "raw", "BGRX", 0, 1)

        self.gdi32.DeleteObject(hbitmap)
        self.gdi32.DeleteDC(hdc_mem)
        self.user32.ReleaseDC(0, hdc_screen)

        return img


# ─── Input Simulation ────────────────────────────────────────────────────────

class InputSimulator:
    """Windows input simulation using SendInput API."""

    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.screen_w = self.user32.GetSystemMetrics(0)
        self.screen_h = self.user32.GetSystemMetrics(1)

    def _send_input(self, *inputs):
        """Send input events via SendInput."""
        n_inputs = len(inputs)
        input_array = (INPUT * n_inputs)(*inputs)
        self.user32.SendInput(n_inputs, ctypes.byref(input_array), ctypes.sizeof(INPUT))

    def _absolute_coords(self, x: int, y: int) -> Tuple[int, int]:
        """Convert pixel coordinates to SendInput absolute coordinates (0-65535)."""
        abs_x = int(x * 65535 / (self.screen_w - 1))
        abs_y = int(y * 65535 / (self.screen_h - 1))
        return abs_x, abs_y

    # ── Mouse ──

    def mouse_move(self, x: int, y: int):
        """Move mouse to absolute screen coordinates."""
        abs_x, abs_y = self._absolute_coords(x, y)
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi = MOUSEINPUT(abs_x, abs_y, 0, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, 0, None)
        self._send_input(inp)

    def mouse_click(self, x: int, y: int, button: str = "left", double: bool = False):
        """Click at screen coordinates."""
        self.mouse_move(x, y)
        time.sleep(0.05)

        if button == "left":
            down_flag = MOUSEEVENTF_LEFTDOWN
            up_flag = MOUSEEVENTF_LEFTUP
        elif button == "right":
            down_flag = MOUSEEVENTF_RIGHTDOWN
            up_flag = MOUSEEVENTF_RIGHTUP
        elif button == "middle":
            down_flag = MOUSEEVENTF_MIDDLEDOWN
            up_flag = MOUSEEVENTF_MIDDLEUP
        else:
            raise ValueError(f"Unknown button: {button}")

        abs_x, abs_y = self._absolute_coords(x, y)

        # Click down
        inp_down = INPUT()
        inp_down.type = INPUT_MOUSE
        inp_down.union.mi = MOUSEINPUT(abs_x, abs_y, 0, down_flag | MOUSEEVENTF_ABSOLUTE, 0, None)

        # Click up
        inp_up = INPUT()
        inp_up.type = INPUT_MOUSE
        inp_up.union.mi = MOUSEINPUT(abs_x, abs_y, 0, up_flag | MOUSEEVENTF_ABSOLUTE, 0, None)

        self._send_input(inp_down, inp_up)

        if double:
            time.sleep(0.05)
            self._send_input(inp_down, inp_up)

    def mouse_scroll(self, direction: str = "down", amount: int = 3, x: int = None, y: int = None):
        """Scroll mouse wheel. direction: 'up' or 'down'."""
        if x is not None and y is not None:
            self.mouse_move(x, y)
            time.sleep(0.05)

        # Scroll: positive = up, negative = down
        scroll_amount = amount * 120 * (1 if direction == "up" else -1)

        abs_x, abs_y = self._absolute_coords(
            x or self.screen_w // 2, y or self.screen_h // 2
        )

        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi = MOUSEINPUT(
            abs_x, abs_y, scroll_amount,
            0x0800 | MOUSEEVENTF_ABSOLUTE, 0, None  # MOUSEEVENTF_WHEEL = 0x0800
        )
        self._send_input(inp)

    def mouse_drag(self, from_x: int, from_y: int, to_x: int, to_y: int, duration: float = 0.5):
        """Drag from one point to another."""
        self.mouse_move(from_x, from_y)
        time.sleep(0.05)

        abs_fx, abs_fy = self._absolute_coords(from_x, from_y)
        abs_tx, abs_ty = self._absolute_coords(to_x, to_y)

        # Mouse down
        inp_down = INPUT()
        inp_down.type = INPUT_MOUSE
        inp_down.union.mi = MOUSEINPUT(abs_fx, abs_fy, 0, MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_ABSOLUTE, 0, None)
        self._send_input(inp_down)

        # Smooth move
        steps = max(10, int(duration * 60))
        for i in range(1, steps + 1):
            t = i / steps
            mx = int(from_x + (to_x - from_x) * t)
            my = int(from_y + (to_y - from_y) * t)
            abs_mx, abs_my = self._absolute_coords(mx, my)
            inp_move = INPUT()
            inp_move.type = INPUT_MOUSE
            inp_move.union.mi = MOUSEINPUT(abs_mx, abs_my, 0, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, 0, None)
            self._send_input(inp_move)
            time.sleep(duration / steps)

        # Mouse up
        inp_up = INPUT()
        inp_up.type = INPUT_MOUSE
        inp_up.union.mi = MOUSEINPUT(abs_tx, abs_ty, 0, MOUSEEVENTF_LEFTUP | MOUSEEVENTF_ABSOLUTE, 0, None)
        self._send_input(inp_up)

    # ── Keyboard ──

    def key_press(self, key: str):
        """Press a single key."""
        vk = VK_CODES.get(key.lower())
        if vk is None:
            raise ValueError(f"Unknown key: {key}. Available: {list(VK_CODES.keys())}")

        inp_down = INPUT()
        inp_down.type = INPUT_KEYBOARD
        inp_down.union.ki = KEYBDINPUT(vk, 0, KEYEVENTF_KEYDOWN, 0, None)

        inp_up = INPUT()
        inp_up.type = INPUT_KEYBOARD
        inp_up.union.ki = KEYBDINPUT(vk, 0, KEYEVENTF_KEYUP, 0, None)

        self._send_input(inp_down, inp_up)

    def key_combo(self, *keys: str):
        """Press a key combination (e.g., key_combo('control', 's'))."""
        vk_codes = []
        for key in keys:
            vk = VK_CODES.get(key.lower())
            if vk is None:
                raise ValueError(f"Unknown key: {key}")
            vk_codes.append(vk)

        inputs = []
        # Press all keys down
        for vk in vk_codes:
            inp = INPUT()
            inp.type = INPUT_KEYBOARD
            inp.union.ki = KEYBDINPUT(vk, 0, KEYEVENTF_KEYDOWN, 0, None)
            inputs.append(inp)

        # Release all keys in reverse
        for vk in reversed(vk_codes):
            inp = INPUT()
            inp.type = INPUT_KEYBOARD
            inp.union.ki = KEYBDINPUT(vk, 0, KEYEVENTF_KEYUP, 0, None)
            inputs.append(inp)

        self._send_input(*inputs)

    def type_text(self, text: str, interval: float = 0.02):
        """Type a string character by character using scan codes."""
        for char in text:
            if char == '\n':
                self.key_press('enter')
            elif char == '\t':
                self.key_press('tab')
            elif char.isalpha() or char.isdigit() or char == ' ':
                self.key_press(char.lower())
            else:
                # For special characters, use Unicode input
                inp_down = INPUT()
                inp_down.type = INPUT_KEYBOARD
                inp_down.union.ki = KEYBDINPUT(0, ord(char), KEYEVENTF_UNICODE, 0, None)

                inp_up = INPUT()
                inp_up.type = INPUT_KEYBOARD
                inp_up.union.ki = KEYBDINPUT(0, ord(char), KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, None)

                self._send_input(inp_down, inp_up)
            time.sleep(interval)


# ─── UI Element Detection ───────────────────────────────────────────────────

class UIElementDetector:
    """
    Detect UI elements on screen using OpenCV template matching.
    For high-level understanding, use the vision model (image tool).
    """

    def __init__(self):
        self.capturer = ScreenCapture()

    def find_template(
        self, template_path: str, threshold: float = 0.8, region: Optional[ScreenRegion] = None
    ) -> List[Dict[str, Any]]:
        """
        Find a template image on screen using OpenCV template matching.
        Returns list of matches with coordinates and confidence.
        """
        import cv2
        import numpy as np

        # Capture screen
        screen_img = self.capturer.capture_to_pil(region)
        screen = cv2.cvtColor(np.array(screen_img), cv2.COLOR_RGB2BGR)

        # Load template
        template = cv2.imread(template_path)
        if template is None:
            raise FileNotFoundError(f"Template not found: {template_path}")

        h, w = template.shape[:2]

        # Match
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)

        matches = []
        for pt_y, pt_x in zip(*locations[::-1] if len(locations) == 2 else zip(*locations)):
            offset_x = region.x if region else 0
            offset_y = region.y if region else 0
            matches.append({
                "x": int(pt_x) + offset_x,
                "y": int(pt_y) + offset_y,
                "width": w,
                "height": h,
                "confidence": float(result[pt_y, pt_x]),
            })

        # Non-maximum suppression (remove overlapping matches)
        if matches:
            matches = self._nms(matches, overlap_thresh=0.5)

        return matches

    def _nms(self, boxes: List[Dict], overlap_thresh: float = 0.5) -> List[Dict]:
        """Non-maximum suppression for overlapping detections."""
        if not boxes:
            return []

        boxes_sorted = sorted(boxes, key=lambda b: b["confidence"], reverse=True)
        keep = []

        while boxes_sorted:
            best = boxes_sorted.pop(0)
            keep.append(best)
            boxes_sorted = [
                b for b in boxes_sorted
                if self._iou(best, b) < overlap_thresh
            ]

        return keep

    @staticmethod
    def _iou(a: Dict, b: Dict) -> float:
        """Intersection over Union."""
        x1 = max(a["x"], b["x"])
        y1 = max(a["y"], b["y"])
        x2 = min(a["x"] + a["width"], b["x"] + b["width"])
        y2 = min(a["y"] + a["height"], b["y"] + b["height"])

        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area_a = a["width"] * a["height"]
        area_b = b["width"] * b["height"]
        union = area_a + area_b - intersection

        return intersection / union if union > 0 else 0


# ─── Window Manager ──────────────────────────────────────────────────────────

class WindowManager:
    """Manage Windows: find, focus, move, resize."""

    def __init__(self):
        self.user32 = ctypes.windll.user32

    def get_foreground_window(self) -> Dict[str, Any]:
        """Get info about the currently focused window."""
        hwnd = self.user32.GetForegroundWindow()
        length = self.user32.GetWindowTextLengthW(hwnd) + 1
        buf = ctypes.create_unicode_buffer(length)
        self.user32.GetWindowTextW(hwnd, buf, length)

        rect = ctypes.wintypes.RECT()
        self.user32.GetWindowRect(hwnd, ctypes.byref(rect))

        return {
            "hwnd": hwnd,
            "title": buf.value,
            "x": rect.left,
            "y": rect.top,
            "width": rect.right - rect.left,
            "height": rect.bottom - rect.top,
        }

    def find_window(self, title_substring: str) -> Optional[Dict[str, Any]]:
        """Find a window by title substring."""
        results = []
        WNDENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.c_ulong, ctypes.POINTER(ctypes.c_int)
        )

        def enum_callback(hwnd, _lparam):
            length = self.user32.GetWindowTextLengthW(hwnd) + 1
            buf = ctypes.create_unicode_buffer(length)
            self.user32.GetWindowTextW(hwnd, buf, length)
            if title_substring.lower() in buf.value.lower():
                rect = ctypes.wintypes.RECT()
                self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                results.append({
                    "hwnd": hwnd,
                    "title": buf.value,
                    "x": rect.left,
                    "y": rect.top,
                    "width": rect.right - rect.left,
                    "height": rect.bottom - rect.top,
                })
            return True

        self.user32.EnumWindows(WNDENUMPROC(enum_callback), 0)
        return results[0] if results else None

    def focus_window(self, hwnd: int):
        """Bring a window to the foreground."""
        self.user32.SetForegroundWindow(hwnd)

    def move_window(self, hwnd: int, x: int, y: int, width: int, height: int):
        """Move and resize a window."""
        self.user32.MoveWindow(hwnd, x, y, width, height, True)

    def list_windows(self) -> List[Dict[str, Any]]:
        """List all visible windows."""
        results = []
        WNDENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.c_ulong, ctypes.POINTER(ctypes.c_int)
        )

        def enum_callback(hwnd, _lparam):
            if self.user32.IsWindowVisible(hwnd):
                length = self.user32.GetWindowTextLengthW(hwnd) + 1
                buf = ctypes.create_unicode_buffer(length)
                self.user32.GetWindowTextW(hwnd, buf, length)
                if buf.value:
                    rect = ctypes.wintypes.RECT()
                    self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    results.append({
                        "hwnd": hwnd,
                        "title": buf.value,
                        "x": rect.left,
                        "y": rect.top,
                        "width": rect.right - rect.left,
                        "height": rect.bottom - rect.top,
                    })
            return True

        self.user32.EnumWindows(WNDENUMPROC(enum_callback), 0)
        return results


# ─── High-Level Desktop Controller ──────────────────────────────────────────

class DesktopController:
    """
    High-level desktop control combining screen capture, input simulation,
    window management, and vision-based UI understanding.
    """

    def __init__(self):
        self.screen = ScreenCapture()
        self.input = InputSimulator()
        self.windows = WindowManager()
        self.detector = UIElementDetector()

    def screenshot(self, region: Optional[Dict] = None) -> ScreenshotResult:
        """Take a screenshot. Pass region as {x, y, width, height} dict."""
        r = ScreenRegion(**region) if region else None
        return self.screen.capture(r)

    def click(self, x: int, y: int, button: str = "left", double: bool = False):
        """Click at coordinates."""
        self.input.mouse_click(x, y, button, double)

    def type(self, text: str, interval: float = 0.02):
        """Type text."""
        self.input.type_text(text, interval)

    def hotkey(self, *keys: str):
        """Press a keyboard shortcut."""
        self.input.key_combo(*keys)

    def scroll(self, direction: str = "down", amount: int = 3):
        """Scroll the mouse wheel."""
        self.input.mouse_scroll(direction, amount)

    def drag(self, from_x: int, from_y: int, to_x: int, to_y: int, duration: float = 0.5):
        """Drag from one point to another."""
        self.input.mouse_drag(from_x, from_y, to_x, to_y, duration)

    def find_window(self, title: str) -> Optional[Dict]:
        """Find a window by title."""
        return self.windows.find_window(title)

    def focus_window(self, title: str) -> bool:
        """Find and focus a window by title."""
        win = self.windows.find_window(title)
        if win:
            self.windows.focus_window(win["hwnd"])
            return True
        return False

    def list_windows(self) -> List[Dict]:
        """List all visible windows."""
        return self.windows.list_windows()

    def find_on_screen(self, template_path: str, threshold: float = 0.8) -> List[Dict]:
        """Find a template image on screen."""
        return self.detector.find_template(template_path, threshold)


# ─── CLI Interface ───────────────────────────────────────────────────────────

def main():
    """CLI for desktop control."""
    import argparse

    parser = argparse.ArgumentParser(description="OCE Desktop Control Layer")
    subparsers = parser.add_subparsers(dest="command")

    # Screenshot
    p_ss = subparsers.add_parser("screenshot", help="Take a screenshot")
    p_ss.add_argument("--region", help="Region: x,y,w,h")
    p_ss.add_argument("--output", help="Output path override")

    # Click
    p_click = subparsers.add_parser("click", help="Click at coordinates")
    p_click.add_argument("x", type=int)
    p_click.add_argument("y", type=int)
    p_click.add_argument("--button", default="left")
    p_click.add_argument("--double", action="store_true")

    # Type
    p_type = subparsers.add_parser("type", help="Type text")
    p_type.add_argument("text")

    # Hotkey
    p_hotkey = subparsers.add_parser("hotkey", help="Press key combo")
    p_hotkey.add_argument("keys", nargs="+")

    # Scroll
    p_scroll = subparsers.add_parser("scroll", help="Scroll")
    p_scroll.add_argument("--direction", default="down")
    p_scroll.add_argument("--amount", type=int, default=3)

    # Window
    p_win = subparsers.add_parser("window", help="Window operations")
    p_win.add_argument("action", choices=["list", "find", "focus"])
    p_win.add_argument("--title", help="Window title substring")

    # Find template
    p_find = subparsers.add_parser("find", help="Find template on screen")
    p_find.add_argument("template", help="Path to template image")
    p_find.add_argument("--threshold", type=float, default=0.8)

    args = parser.parse_args()
    dc = DesktopController()

    if args.command == "screenshot":
        region = None
        if args.region:
            parts = [int(p) for p in args.region.split(",")]
            region = {"x": parts[0], "y": parts[1], "width": parts[2], "height": parts[3]}
        result = dc.screenshot(region)
        print(json.dumps(asdict(result), indent=2))

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
            windows = dc.list_windows()
            for w in windows:
                print(f"  {w['title']!r} @ ({w['x']},{w['y']}) {w['width']}x{w['height']}")
        elif args.action == "find":
            if not args.title:
                print("Need --title")
                sys.exit(1)
            win = dc.find_window(args.title)
            if win:
                print(json.dumps(win, indent=2, default=str))
            else:
                print(f"Window not found: {args.title}")
        elif args.action == "focus":
            if not args.title:
                print("Need --title")
                sys.exit(1)
            ok = dc.focus_window(args.title)
            print(f"Focused: {ok}")

    elif args.command == "find":
        matches = dc.find_on_screen(args.template, args.threshold)
        print(json.dumps(matches, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
