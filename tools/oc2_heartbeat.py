"""
OC2 OCE Heartbeat Writer
Writes OC2 status to OCE persistent field for monitoring.
Run via cron every 5 minutes during active builds.
"""
import json
import urllib.request
import os
from datetime import datetime

OCE_URL = "http://localhost:8000"
WORKSPACE = r"C:\Users\wifik\Desktop\projects\larger-lab"

def check_track_a_progress():
    """Check Track A file existence to determine progress."""
    files = {
        "CryptoAssetScanner": os.path.exists(os.path.join(WORKSPACE, "crypto", "CryptoAssetScanner.py")),
        "ST_NinjaScript": os.path.exists(os.path.join(WORKSPACE, "tradovate", "CEREBUS_ST_NT8.cs")),
        "P90_NinjaScript": os.path.exists(os.path.join(WORKSPACE, "tradovate", "CEREBUS_P90_NT8.cs")),
    }
    completed = sum(1 for v in files.values() if v)
    return {
        "files": files,
        "completed": completed,
        "total": len(files)
    }

def write_heartbeat():
    progress = check_track_a_progress()
    
    data = {
        "key": "oc2_status",
        "value": {
            "agent": "OC2",
            "status": "active",
            "track_a_progress": f"{progress['completed']}/{progress['total']}",
            "track_a_files": progress['files'],
            "timestamp": datetime.now().isoformat(),
            "oce_monitoring": True
        }
    }
    
    req = urllib.request.Request(
        f"{OCE_URL}/api/persistent-field/heartbeat",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=5)
        print(f"Heartbeat wrote: {progress['completed']}/{progress['total']} track A")
        return True
    except Exception as e:
        print(f"Heartbeat failed: {e}")
        return False

if __name__ == "__main__":
    write_heartbeat()
