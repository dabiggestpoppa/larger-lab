"""OCE Backend Startup Script."""
import os, sys, traceback
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import uvicorn
    from oce.backend.main import app
    print("[OCE] Starting backend on port 8000...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
except Exception as e:
    print(f"[OCE] FATAL: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)
