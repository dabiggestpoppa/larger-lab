"""
OCE Desktop Control API
========================
FastAPI server exposing desktop control as HTTP endpoints for OpenClaw agents.

Run: python tools/operator/desktop_api.py
Port: 8001 (separate from OCE backend on 8000)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

from desktop_control import DesktopController, ScreenRegion

app = FastAPI(
    title="OCE Desktop Control API",
    description="Desktop control layer for OpenClaw Operator",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

dc = DesktopController()


# ─── Models ──────────────────────────────────────────────────────────────────

class ScreenshotRequest(BaseModel):
    region: Optional[Dict[str, int]] = None  # {x, y, width, height}

class ClickRequest(BaseModel):
    x: int
    y: int
    button: str = "left"
    double: bool = False

class TypeRequest(BaseModel):
    text: str
    interval: float = 0.02

class HotkeyRequest(BaseModel):
    keys: List[str]

class ScrollRequest(BaseModel):
    direction: str = "down"
    amount: int = 3

class DragRequest(BaseModel):
    from_x: int
    from_y: int
    to_x: int
    to_y: int
    duration: float = 0.5

class FindWindowRequest(BaseModel):
    title: str

class FocusWindowRequest(BaseModel):
    title: str

class FindTemplateRequest(BaseModel):
    template_path: str
    threshold: float = 0.8


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"service": "OCE Desktop Control API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "screen": dc.screen.get_screen_size()}


@app.post("/desktop/screenshot")
async def screenshot(req: ScreenshotRequest):
    """Take a screenshot. Optionally pass region {x, y, width, height}."""
    try:
        result = dc.screenshot(req.region)
        return {"ok": True, "path": result.path, "width": result.width, "height": result.height}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/click")
async def click(req: ClickRequest):
    """Click at screen coordinates."""
    try:
        dc.click(req.x, req.y, req.button, req.double)
        return {"ok": True, "action": "click", "x": req.x, "y": req.y}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/type")
async def type_text(req: TypeRequest):
    """Type text at current cursor position."""
    try:
        dc.type(req.text, req.interval)
        return {"ok": True, "action": "type", "length": len(req.text)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/hotkey")
async def hotkey(req: HotkeyRequest):
    """Press a keyboard shortcut (e.g., ['control', 's'])."""
    try:
        dc.hotkey(*req.keys)
        return {"ok": True, "action": "hotkey", "keys": req.keys}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/scroll")
async def scroll(req: ScrollRequest):
    """Scroll the mouse wheel."""
    try:
        dc.scroll(req.direction, req.amount)
        return {"ok": True, "action": "scroll", "direction": req.direction}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/drag")
async def drag(req: DragRequest):
    """Drag from one point to another."""
    try:
        dc.drag(req.from_x, req.from_y, req.to_x, req.to_y, req.duration)
        return {"ok": True, "action": "drag"}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/desktop/windows")
async def list_windows():
    """List all visible windows."""
    try:
        windows = dc.list_windows()
        return {"ok": True, "windows": windows, "count": len(windows)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/window/find")
async def find_window(req: FindWindowRequest):
    """Find a window by title substring."""
    try:
        win = dc.find_window(req.title)
        if win:
            return {"ok": True, "window": win}
        return {"ok": False, "error": f"Window not found: {req.title}"}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/window/focus")
async def focus_window(req: FocusWindowRequest):
    """Find and focus a window by title."""
    try:
        ok = dc.focus_window(req.title)
        return {"ok": ok, "focused": req.title if ok else None}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/find")
async def find_template(req: FindTemplateRequest):
    """Find a template image on screen."""
    try:
        matches = dc.find_on_screen(req.template_path, req.threshold)
        return {"ok": True, "matches": matches, "count": len(matches)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/wait")
async def wait_for(req: FindTemplateRequest):
    """Wait for a template to appear on screen (polls every 0.5s, max 10s)."""
    import time
    try:
        for _ in range(20):
            matches = dc.find_on_screen(req.template_path, req.threshold)
            if matches:
                return {"ok": True, "matches": matches, "found": True}
            time.sleep(0.5)
        return {"ok": True, "matches": [], "found": False, "timeout": True}
    except Exception as e:
        raise HTTPException(500, str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
