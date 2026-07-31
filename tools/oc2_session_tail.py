"""Show last few messages from OC2's active session."""
import json
from pathlib import Path

sessions_dir = Path(r"C:\Users\wifik\.openclaw-2\.openclaw\agents\main\sessions")
files = sorted(sessions_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)

for f in files[:3]:
    print(f"\n=== {f.name} ===")
    lines = f.read_text(encoding="utf-8").strip().splitlines()
    for line in lines[-5:]:
        try:
            d = json.loads(line)
            role = d.get("role", "?")
            content = d.get("content", "")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        print(f"  [{role}] {part.get('text', '')[:200]!r}")
            elif isinstance(content, str):
                print(f"  [{role}] {content[:200]!r}")
        except Exception:
            print(f"  {line[:100]}")
