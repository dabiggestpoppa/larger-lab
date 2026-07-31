"""Dump raw last entries from OC2 session."""
import json
from pathlib import Path

sessions_dir = Path(r"C:\Users\wifik\.openclaw-2\.openclaw\agents\main\sessions")
files = sorted(sessions_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)

# Show last 3 entries from the most recent session
f = files[0]
print(f"=== {f.name} ===")
lines = f.read_text(encoding="utf-8").strip().splitlines()
for line in lines[-3:]:
    try:
        d = json.loads(line)
        # Print the full structure but truncated
        print(json.dumps(d, indent=2, default=str)[:1000])
        print("---")
    except Exception as e:
        print(f"Parse error: {e}")
        print(line[:200])
