"""Trace OC2 session initialization to find root cause."""
import json
from pathlib import Path
from datetime import datetime

sessions_dir = Path(r"C:\Users\wifik\.openclaw-2\.openclaw\agents\main\sessions")

# Get ALL session files sorted by time
files = sorted(sessions_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)

print(f"Total session files: {len(files)}")
print()

# Show the FULL content of the most recent session
f = files[0]
mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%m/%d %H:%M:%S")
print(f"=== {f.name} ({mtime}) ===")
lines = f.read_text(encoding="utf-8").strip().splitlines()
print(f"Lines: {len(lines)}")
for i, line in enumerate(lines):
    try:
        d = json.loads(line)
        print(f"\n[{i}] type={d.get('type', '?')}")
        if d.get("type") == "message":
            msg = d.get("message", {})
            role = msg.get("role", "?")
            content = msg.get("content", "")
            api = msg.get("api", "?")
            model = msg.get("model", "?")
            stop = msg.get("stopReason", "?")
            usage = msg.get("usage", {})
            print(f"    role={role} api={api} model={model} stop={stop}")
            print(f"    usage={json.dumps(usage)[:100]}")
            if isinstance(content, list):
                for p in content:
                    if isinstance(p, dict):
                        t = p.get("type", "?")
                        text = p.get("text", p.get("thinking", ""))[:200]
                        print(f"    [{t}]: {text!r}")
            elif isinstance(content, str):
                print(f"    text: {content[:200]!r}")
        elif d.get("type") == "session":
            print(f"    id={d.get('id', '?')[:20]}")
            print(f"    cwd={d.get('cwd', '?')}")
    except Exception as e:
        print(f"    err: {e}")
