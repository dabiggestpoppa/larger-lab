"""Simple team-chat.md watcher. Prints new content when file grows."""
import time, hashlib, sys
from pathlib import Path

CHAT_FILE = Path(__file__).parent.parent / "shared-conversations" / "team-chat.md"
CHECK_INTERVAL = 30  # seconds

def get_hash():
    content = CHAT_FILE.read_text(encoding="utf-8")
    return hashlib.md5(content.encode()).hexdigest(), len(content.splitlines())

def main():
    print(f"[WATCH] Monitoring {CHAT_FILE}", flush=True)
    last_hash, last_lines = get_hash()
    print(f"[WATCH] Baseline: {last_lines} lines, hash={last_hash[:8]}", flush=True)
    
    while True:
        time.sleep(CHECK_INTERVAL)
        try:
            cur_hash, cur_lines = get_hash()
            if cur_hash != last_hash and cur_lines > last_lines:
                content = CHAT_FILE.read_text(encoding="utf-8").splitlines()
                new_content = content[last_lines:]
                print(f"\n[CHANGE] {last_lines} -> {cur_lines} lines (+{cur_lines - last_lines})", flush=True)
                for line in new_content[:80]:
                    print(line, flush=True)
                print("[END CHANGE]", flush=True)
                last_hash, last_lines = cur_hash, cur_lines
        except Exception as e:
            print(f"[ERROR] {e}", flush=True)

if __name__ == "__main__":
    main()
