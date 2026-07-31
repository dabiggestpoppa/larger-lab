"""Read OC2 session file."""
import json
from pathlib import Path

f = Path(r"C:\Users\wifik\.openclaw-2\.openclaw\agents\main\sessions\2dd7d0db-1675-4c06-86fa-0a21716c5864.jsonl")
lines = f.read_text(encoding="utf-8").strip().splitlines()
print(f"Total lines: {len(lines)}")
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
            print(f"\n  [{i}] role={role} text={text[:200]!r}")
        else:
            print(f"\n  [{i}] type={dtype}")
    except Exception as e:
        print(f"\n  [{i}] parse error: {e}")
