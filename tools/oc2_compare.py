"""Compare old working session with new failing session."""
import json
from pathlib import Path
from datetime import datetime

sessions_dir = Path(r"C:\Users\wifik\.openclaw-2\.openclaw\agents\main\sessions")

# Find the old working session (a97b93dd) and the new failing session
old_session = sessions_dir / "a97b93dd-6cea-4e7c-b5eb-7eb3b695bf7f.jsonl"
new_session = sorted(sessions_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)[0]

print("=== OLD WORKING SESSION ===")
if old_session.exists():
    lines = old_session.read_text(encoding="utf-8").strip().splitlines()
    print(f"Lines: {len(lines)}")
    for i, line in enumerate(lines[:10]):
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
                print(f"  [{i}] {role}: {text[:100]!r}")
            else:
                print(f"  [{i}] {dtype}")
        except Exception as e:
            print(f"  [{i}] err: {e}")
else:
    print("NOT FOUND")

print(f"\n=== NEW FAILING SESSION ({new_session.name[:20]}...) ===")
lines = new_session.read_text(encoding="utf-8").strip().splitlines()
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
            print(f"  [{i}] {role}: {text[:100]!r}")
        else:
            print(f"  [{i}] {dtype}")
    except Exception as e:
        print(f"  [{i}] err: {e}")
