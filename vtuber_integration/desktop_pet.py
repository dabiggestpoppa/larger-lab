"""
Desktop Pet — Transparent always-on-top VTuber overlay using pywebview.
Loads the Open-LLM-VTuber frontend from localhost:12393 in a frameless,
transparent window that floats above all other windows.

Controls:
  Alt+V  — Toggle visibility
  Alt+Q  — Close pet
  Alt+R  — Reload page
  Alt+P  — Toggle always-on-top
  Double-click title bar — Toggle visibility
"""

import sys
import os
import json
import ctypes
import threading
import time
import logging
from pathlib import Path

import webview

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VTUBER_URL = os.getenv("VTUBER_URL", "http://localhost:12393")
WINDOW_WIDTH = int(os.getenv("PET_WIDTH", "320"))
WINDOW_HEIGHT = int(os.getenv("PET_HEIGHT", "480"))
ALWAYS_ON_TOP = os.getenv("PET_ALWAYS_ON_TOP", "1") == "1"
TRANSPARENCY = float(os.getenv("PET_TRANSPARENCY", "0.95"))  # 0.0-1.0
WINDOW_X = int(os.getenv("PET_X", "-1"))  # -1 = center
WINDOW_Y = int(os.getenv("PET_Y", "-1"))  # -1 = center (offset up)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            Path(__file__).parent / "logs" / "desktop_pet.log",
            encoding="utf-8",
        ),
    ],
)
log = logging.getLogger("desktop_pet")

# ---------------------------------------------------------------------------
# Win32 helpers for always-on-top and transparency
# ---------------------------------------------------------------------------
try:
    import win32con
    import win32gui
    import win32api
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    log.warning("pywin32 not available — some features will be limited")


def set_always_on_top(hwnd, on_top=True):
    """Set window always-on-top using Win32 API."""
    if not WIN32_AVAILABLE:
        return
    try:
        z_order = win32con.HWND_TOPMOST if on_top else win32con.HWND_NOTOPMOST
        flags = z_order | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        win32gui.SetWindowPos(hwnd, z_order, 0, 0, 0, 0, flags)
    except Exception as e:
        log.debug(f"set_always_on_top error: {e}")


def set_window_transparency(hwnd, alpha=250):
    """Set window transparency (0-255) using Win32 layered window."""
    if not WIN32_AVAILABLE:
        return
    try:
        win32gui.SetWindowLong(
            hwnd, win32con.GWL_EXSTYLE,
            win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            | win32con.WS_EX_LAYERED
        )
        win32gui.SetLayeredWindowAttributes(hwnd, 0, alpha, win32con.LWA_ALPHA)
    except Exception as e:
        log.debug(f"set_window_transparency error: {e}")


def get_window_rect(hwnd):
    """Get window rect tuple (x, y, w, h)."""
    if not WIN32_AVAILABLE:
        return (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    try:
        rect = win32gui.GetWindowRect(hwnd)
        return (rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1])
    except Exception:
        return (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)


# ---------------------------------------------------------------------------
# Pet State (persisted to disk)
# ---------------------------------------------------------------------------
class PetState:
    """Persistent pet state stored to JSON."""

    def __init__(self, state_file: str = "pet_state.json"):
        self.state_file = Path(__file__).parent / state_file
        self._data = {
            "x": -1,
            "y": -1,
            "width": WINDOW_WIDTH,
            "height": WINDOW_HEIGHT,
            "visible": True,
            "always_on_top": ALWAYS_ON_TOP,
            "transparency": TRANSPARENCY,
            "last_url": VTUBER_URL,
        }
        self.load()

    def load(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data.update(saved)
                log.info(f"Loaded pet state from {self.state_file}")
            except Exception as e:
                log.warning(f"Failed to load pet state: {e}")

    def save(self):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            log.warning(f"Failed to save pet state: {e}")

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()


# ---------------------------------------------------------------------------
# API exposed to JS frontend
# ---------------------------------------------------------------------------
class PetApi:
    """API bridge between JS and Python."""

    def __init__(self, pet_state: PetState, window):
        self.pet_state = pet_state
        self.window = window

    def get_status(self):
        """Return pet status."""
        return {
            "visible": self.pet_state.get("visible", True),
            "always_on_top": self.pet_state.get("always_on_top", True),
            "transparency": self.pet_state.get("transparency", 0.95),
            "vtuber_url": self.pet_state.get("last_url", VTUBER_URL),
            "vtuber_online": False,
        }

    def toggle_visibility(self):
        visible = not self.pet_state.get("visible", True)
        self.pet_state.set("visible", visible)
        if self.window:
            self.window.visibility = "visible" if visible else "hidden"
        return {"visible": visible}

    def set_position(self, x, y):
        self.pet_state.set("x", x)
        self.pet_state.set("y", y)
        if self.window:
            self.window.move(x, y)
        return {"x": x, "y": y}

    def set_always_on_top(self, on_top):
        self.pet_state.set("always_on_top", on_top)
        if self.window and WIN32_AVAILABLE:
            hwnd = self._get_hwnd()
            if hwnd:
                set_always_on_top(hwnd, on_top)
        return {"always_on_top": on_top}

    def set_transparency(self, alpha):
        """Set transparency (0.0-1.0)."""
        self.pet_state.set("transparency", alpha)
        if self.window and WIN32_AVAILABLE:
            hwnd = self._get_hwnd()
            if hwnd:
                set_window_transparency(hwnd, int(alpha * 255))
        return {"transparency": alpha}

    def reload_vtuber(self):
        """Reload the VTuber iframe."""
        if self.window:
            self.window.load_url(VTUBER_URL)
        return {"status": "reloaded"}

    def check_vtuber_health(self):
        """Check if VTuber server is responding."""
        import urllib.request
        try:
            req = urllib.request.Request(f"{VTUBER_URL}/", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return {"online": resp.status == 200}
        except Exception as e:
            return {"online": False, "error": str(e)}


# ---------------------------------------------------------------------------
# HTML/CSS/JS for the pet wrapper
# ---------------------------------------------------------------------------
PET_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>VTuber Pet</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: transparent;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    user-select: none;
    -webkit-user-select: none;
  }

  /* Title Bar */
  #titlebar {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 28px;
    background: linear-gradient(135deg, rgba(30,30,40,0.6), rgba(20,20,30,0.4));
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 8px;
    z-index: 1000;
    cursor: move;
    border-bottom: 1px solid rgba(255,255,255,0.08);
  }
  #titlebar:hover {
    background: linear-gradient(135deg, rgba(40,40,55,0.7), rgba(30,30,45,0.5));
  }
  #titlebar-title {
    color: rgba(255,255,255,0.85);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  #titlebar-title .dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #4ade80;
    display: inline-block;
    animation: pulse 2s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }
  #titlebar-title .dot.offline { background: #f87171; animation: none; }
  #titlebar-title .dot.loading { background: #fbbf24; }

  #titlebar-controls {
    display: flex;
    gap: 4px;
  }
  .ctrl-btn {
    width: 20px; height: 20px;
    border: none;
    border-radius: 6px;
    background: rgba(255,255,255,0.08);
    color: rgba(255,255,255,0.7);
    font-size: 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s;
  }
  .ctrl-btn:hover { background: rgba(255,255,255,0.2); color: #fff; }
  .ctrl-btn.active { background: rgba(99,102,241,0.4); color: #fff; }

  /* Status Bar */
  #statusbar {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 22px;
    background: rgba(20,20,30,0.4);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 8px;
    z-index: 1000;
    font-size: 10px;
    color: rgba(255,255,255,0.5);
    border-top: 1px solid rgba(255,255,255,0.06);
  }

  /* VTuber iframe */
  #vtuber-frame {
    position: absolute;
    top: 28px; left: 0;
    width: 100%;
    height: calc(100% - 50px);
    border: none;
    background: transparent;
    pointer-events: auto;
  }

  /* Resize Handle */
  #resize-handle {
    position: absolute;
    bottom: 22px; right: 0;
    width: 16px; height: 16px;
    cursor: nwse-resize;
    z-index: 1001;
  }
  #resize-handle::after {
    content: '';
    position: absolute;
    bottom: 3px; right: 3px;
    width: 8px; height: 8px;
    border-right: 2px solid rgba(255,255,255,0.3);
    border-bottom: 2px solid rgba(255,255,255,0.3);
  }
</style>
</head>
<body>
  <div id="titlebar">
    <div id="titlebar-title">
      <span class="dot loading" id="status-dot"></span>
      <span>VTuber Pet</span>
    </div>
    <div id="titlebar-controls">
      <button class="ctrl-btn" id="btn-pin" title="Always on Top (Alt+P)">📌</button>
      <button class="ctrl-btn" id="btn-reload" title="Reload (Alt+R)">🔄</button>
      <button class="ctrl-btn" id="btn-hide" title="Toggle Visibility (Alt+V)">👁</button>
      <button class="ctrl-btn" id="btn-close" title="Close (Alt+Q)">✕</button>
    </div>
  </div>

  <iframe id="vtuber-frame"
    src="about:blank"
    allowtransparency="true"
    sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
  ></iframe>

  <div id="statusbar">
    <span id="status-text">Connecting...</span>
    <span id="coords-text"></span>
  </div>

  <div id="resize-handle"></div>

  <script>
    const API = window.pywebview.api;
    let isDragging = false;
    let dragOffX = 0, dragOffY = 0;
    let isResizing = false;
    let resizeOffX = 0, resizeOffY = 0;
    let startW = 0, startH = 0;

    const frame = document.getElementById('vtuber-frame');
    const dot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    const coordsText = document.getElementById('coords-text');
    const titlebar = document.getElementById('titlebar');
    const resizeHandle = document.getElementById('resize-handle');

    function loadVtuber() {
      dot.className = 'dot loading';
      statusText.textContent = 'Loading VTuber...';
      frame.src = '__VTUBER_URL__';
    }

    frame.addEventListener('load', () => {
      dot.className = 'dot';
      statusText.textContent = 'Online — ' + new Date().toLocaleTimeString();
    });

    // Heartbeat: check VTuber health every 30s
    setInterval(async () => {
      try {
        const res = await API.check_vtuber_health();
        if (res.online) {
          dot.className = 'dot';
          statusText.textContent = 'Online — ' + new Date().toLocaleTimeString();
        } else {
          dot.className = 'dot offline';
          statusText.textContent = 'Offline — ' + (res.error || 'no response');
        }
      } catch(e) {
        dot.className = 'dot offline';
        statusText.textContent = 'Connection error';
      }
    }, 30000);

    // Drag
    titlebar.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return;
      isDragging = true;
      dragOffX = e.clientX;
      dragOffY = e.clientY;
      e.preventDefault();
    });
    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      window.pywebview.position = {
        x: window.pywebview.position.x + e.movementX,
        y: window.pywebview.position.y + e.movementY,
      };
    });
    document.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        API.set_position(window.pywebview.position.x, window.pywebview.position.y);
      }
    });

    // Resize
    resizeHandle.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return;
      isResizing = true;
      startW = window.innerWidth;
      startH = window.innerHeight;
      resizeOffX = e.clientX;
      resizeOffY = e.clientY;
      e.preventDefault();
      e.stopPropagation();
    });
    document.addEventListener('mousemove', (e) => {
      if (!isResizing) return;
      const dw = e.clientX - resizeOffX;
      const dh = e.clientY - resizeOffY;
      const newW = Math.max(200, startW + dw);
      const newH = Math.max(150, startH + dh);
      window.resizeTo(newW, newH);
    });
    document.addEventListener('mouseup', () => { isResizing = false; });

    // Controls
    document.getElementById('btn-hide').addEventListener('click', async () => {
      const res = await API.toggle_visibility();
      document.getElementById('btn-hide').classList.toggle('active', !res.visible);
    });
    document.getElementById('btn-pin').addEventListener('click', async () => {
      const curr = await API.get_status();
      const next = !curr.always_on_top;
      await API.set_always_on_top(next);
      document.getElementById('btn-pin').classList.toggle('active', next);
    });
    document.getElementById('btn-reload').addEventListener('click', () => {
      loadVtuber();
    });
    document.getElementById('btn-close').addEventListener('click', () => {
      window.close();
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.altKey) {
        switch(e.key.toLowerCase()) {
          case 'v': document.getElementById('btn-hide').click(); break;
          case 'p': document.getElementById('btn-pin').click(); break;
          case 'r': document.getElementById('btn-reload').click(); break;
          case 'q': document.getElementById('btn-close').click(); break;
        }
      }
    });

    // Double-click titlebar to toggle
    titlebar.addEventListener('dblclick', () => {
      document.getElementById('btn-hide').click();
    });

    // Init
    loadVtuber();
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------
class DesktopPetApp:
    """Main desktop pet application."""

    def __init__(self):
        self.pet_state = PetState()
        self.window = None
        self.api = None

    def create_window(self):
        """Create the pywebview window."""
        x = self.pet_state.get("x", -1)
        y = self.pet_state.get("y", -1)
        w = self.pet_state.get("width", WINDOW_WIDTH)
        h = self.pet_state.get("height", WINDOW_HEIGHT)
        on_top = self.pet_state.get("always_on_top", ALWAYS_ON_TOP)
        visible = self.pet_state.get("visible", True)

        # Center if no saved position
        if x == -1 or y == -1:
            try:
                user32 = ctypes.windll.user32
                screen_w = user32.GetSystemMetrics(0)
                screen_h = user32.GetSystemMetrics(1)
                x = max(0, (screen_w - w) // 2)
                y = max(0, (screen_h - h) // 2 - 100)
            except Exception:
                x, y = 100, 100

        self.window = webview.create_window(
            title="VTuber Pet",
            url="about:blank",
            width=w,
            height=h,
            x=x,
            y=y,
            resizable=True,
            frameless=True,
            easy_drag=False,
            minimized=False,
            on_top=on_top,
            transparent=True,
            text_select=False,
            confirm_close=True,
            background_color="#000000",
        )

        # Set up API bridge
        self.api = PetApi(self.pet_state, self.window)

        # Apply transparency via Win32
        if WIN32_AVAILABLE:
            # pywebview 6.x uses 'handle' on Windows
            hwnd = getattr(self.window, 'handle', None)
            if hwnd is None:
                # Try to find window by title after a brief delay
                import time
                time.sleep(0.3)
                hwnd = win32gui.FindWindow(None, "VTuber Pet")
            if hwnd:
                hwnd = int(hwnd)
                alpha = int(self.pet_state.get("transparency", TRANSPARENCY) * 255)
                set_window_transparency(hwnd, alpha)
                set_always_on_top(hwnd, on_top)

        return self.window

    def run(self):
        """Run the desktop pet application."""
        log.info("=" * 50)
        log.info("VTuber Desktop Pet starting...")
        log.info(f"VTuber URL: {VTUBER_URL}")
        log.info(f"Window: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        log.info(f"Always on top: {ALWAYS_ON_TOP}")
        log.info(f"Transparency: {TRANSPARENCY}")
        log.info("=" * 50)

        # Check VTuber server
        try:
            import urllib.request
            req = urllib.request.Request(f"{VTUBER_URL}/", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                log.info(f"VTuber server is UP (HTTP {resp.status})")
        except Exception as e:
            log.warning(f"VTuber server check failed: {e}")
            log.info("Pet will still launch — VTuber may be starting up")

        # Create window
        self.create_window()

        # Load HTML content with URL injected
        html = PET_HTML.replace("__VTUBER_URL__", VTUBER_URL)

        try:
            webview.start(
                func=lambda: self.window.load_html(html),
                debug=False,
            )
        except KeyboardInterrupt:
            log.info("Pet closed by user (Ctrl+C)")
        except Exception as e:
            log.error(f"Pet error: {e}", exc_info=True)
        finally:
            self.pet_state.save()
            log.info("Pet state saved. Goodbye!")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    """Entry point for the desktop pet."""
    app = DesktopPetApp()
    app.run()


if __name__ == "__main__":
    main()