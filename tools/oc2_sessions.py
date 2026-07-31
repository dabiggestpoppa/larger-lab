"""Analyze OC2 session files."""
import json
from pathlib import Path
from datetime import datetime

sessions_dir = Path(r"C:\Users\wifik\.openclaw-2\.openclaw\agents\main\sessions")
files = sorted(sessions_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
print(f"Total session files: {len(files)}")
for f in files[:10]:
    lines = f.read_text(encoding="utf-8").strip().splitlines()
    first_text = last_text = ""
    first_role = last_role = ""
    for line in lines:
        try:
            d = json.loads(line)
            if d.get("type") == "message":
                content = d.get("message", {}).get("content", "")
                role = d.get("message", {}).get("role", "")
                text = ""
                if isinstance(content, list):
                    for p in content:
                        if isinstance(p, dict) and p.get("type") == "text":
                            text = p.get("text", "")[:100]
                            break
                elif isinstance(content, str):
                    text = content[:100]
                if not first_text:
                    first_text = text
                    first_role = role
                last_text = text
                last_role = role
        except Exception:
            pass
    mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%H:%M:%S")
    size = f.stat().st_size
    print(f"\n  {f.name[:30]}... lines={len(lines)} size={size} mtime={mtime}")
    print(f"    first [{first_role}]: {first_text!r}")
    print(f"    last  [{last_role}]: {last_text!r}")
