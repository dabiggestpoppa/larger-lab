import json
from pathlib import Path

sessions_dir = Path(r"C:\Users\wifik\.openclaw-2\.openclaw\agents\main\sessions")
files = sorted(sessions_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
f = files[0]
print(f"Latest: {f.name[:30]}... ({f.stat().st_size} bytes)")
lines = f.read_text(encoding="utf-8").strip().splitlines()
print(f"Lines: {len(lines)}")
for i, line in enumerate(lines):
    try:
        d = json.loads(line)
        if d.get("type") == "message":
            role = d.get("message", {}).get("role", "?")
            content = d.get("message", {}).get("content", "")
            text = ""
            if isinstance(content, list):
                for p in content:
                    if isinstance(p, dict) and p.get("type") == "text":
                        text += p.get("text", "")
            print(f"  [{i}] {role}: {text[:200]!r}")
    except Exception as e:
        print(f"  [{i}] err: {e}")
