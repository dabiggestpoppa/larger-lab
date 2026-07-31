"""Debug OC2 session to find root cause of error."""
import json
from pathlib import Path
from datetime import datetime

sessions_dir = Path(r"C:\Users\wifik\.openclaw-2\.openclaw\agents\main\sessions")

# Get ALL session files sorted by time
files = sorted(sessions_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)

print(f"Total session files: {len(files)}")
print()

for f in files[:5]:
    lines = f.read_text(encoding="utf-8").strip().splitlines()
    mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%m/%d %H:%M:%S")
    print(f"=== {f.name[:20]}... ({len(lines)} lines, {mtime}) ===")
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
                        if isinstance(p, dict):
                            t = p.get("type", "")
                            if t == "text":
                                text += p.get("text", "")
                            elif t == "toolCall":
                                text += f"[toolCall: {p.get('name', '?')}]"
                            elif t == "toolResult":
                                text += f"[toolResult: {str(p.get('content', ''))[:50]}]"
                            elif t == "thinking":
                                text += f"[thinking: {p.get('thinking', '')[:50]}...]"
                elif isinstance(content, str):
                    text = content
                print(f"  [{i}] {role}: {text[:150]!r}")
            elif dtype == "session":
                print(f"  [{i}] session: {d.get('id', '?')[:20]}")
            else:
                print(f"  [{i}] {dtype}")
        except Exception as e:
            print(f"  [{i}] err: {e}")
    print()
