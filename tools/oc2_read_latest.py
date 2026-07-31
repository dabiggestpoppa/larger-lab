"""Read latest OC2 session."""
import json
from pathlib import Path

sessions_dir = Path(r"C:\Users\wifik\.openclaw-2\.openclaw\agents\main\sessions")
files = sorted(sessions_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
f = files[0]
print(f"=== {f.name} ===")
lines = f.read_text(encoding="utf-8").strip().splitlines()
print(f"Lines: {len(lines)}")
for i, line in enumerate(lines):
    try:
        d = json.loads(line)
        dtype = d.get("type", "?")
        if dtype == "message":
            role = d.get("message", {}).get("role", "?")
            content = d.get("message", {}).get("content", "")
            text = ""
            if isinstance(content, list):
                for p in content:
                    if isinstance(p, dict) and p.get("type") == "text":
                        text += p.get("text", "")
            elif isinstance(content, str):
                text = content
            print(f"\n  [{i}] role={role}")
            print(f"       text={text[:300]!r}")
        else:
            print(f"\n  [{i}] type={dtype}")
    except Exception as e:
        print(f"\n  [{i}] err: {e}")
