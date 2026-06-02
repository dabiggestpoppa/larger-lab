"""
PO Watchdog — Monitor Primary Observer actions and state.

Usage:
  python tools/po_watchdog.py         # run monitoring loop (tail)
  python tools/po_watchdog.py --check # single check and exit

The script watches `data/observer/observer_state.json` and
`data/observer/chat/chat_log.json` for changes and writes a
tailable log to the Temp openclaw folder for quick inspection.
"""
from __future__ import annotations

import time
import json
from pathlib import Path
from datetime import datetime
import argparse
import sys

WORKSPACE = Path(__file__).parent.parent
STATE_FILE = WORKSPACE / "data" / "observer" / "observer_state.json"
CHAT_LOG = WORKSPACE / "data" / "observer" / "chat" / "chat_log.json"
LOG_DIR = Path(r"C:\Users\wifik\AppData\Local\Temp\openclaw")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "po_watchdog.log"
STATE_STORE = WORKSPACE / "tools" / ".po-watchdog-state.json"

def now():
    return datetime.now().isoformat()

def log(msg, level="INFO"):
    line = f"[{now()}] [{level}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_json(path: Path):
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"Failed to load {path}: {e}", "ERROR")
        return None

def diff_state(old: dict | None, new: dict | None) -> list[str]:
    changes = []
    if old is None and new is None:
        return changes
    old = old or {}
    new = new or {}
    watched_keys = ["active_task", "observer_health", "continuity_score", "active_agents", "session_context"]
    for k in watched_keys:
        o = old.get(k)
        n = new.get(k)
        if o != n:
            changes.append(f"{k}: {o!r} -> {n!r}")
    return changes

from core.observer import observer_persistence


def tail_loop(interval: int = 5):
    last_state = load_json(STATE_STORE) or {}
    last_observer = load_json(STATE_FILE)
    last_chat = load_json(CHAT_LOG) or []

    log("PO Watchdog started — monitoring Primary Observer")

    while True:
        try:
            cur_observer = load_json(STATE_FILE)
            if cur_observer is not None:
                changes = diff_state(last_observer, cur_observer)
                if changes:
                    for c in changes:
                        log(f"STATE CHANGE: {c}")
                        # persist state change to DB
                        try:
                            # split 'key: old -> new'
                            if ":" in c:
                                k, rest = c.split(":", 1)
                                if "->" in rest:
                                    old, new = rest.split("->", 1)
                                else:
                                    old, new = None, rest
                                observer_persistence.persist_state_change(k.strip(), old.strip() if old else None, new.strip() if new else None)
                        except Exception:
                            pass
                    # also write a compact snapshot
                    log(f"Observer summary: active_task={cur_observer.get('active_task')}, health={cur_observer.get('observer_health')}, active_agents={cur_observer.get('active_agents')}")
                last_observer = cur_observer

            cur_chat = load_json(CHAT_LOG) or []
                if len(cur_chat) > len(last_chat):
                new_msgs = cur_chat[len(last_chat):]
                for m in new_msgs:
                    ts = m.get('timestamp') or now()
                    src = m.get('source') or m.get('author') or 'PO'
                    text = m.get('message') or m.get('content') or str(m)
                    log(f"CHAT [{ts}] [{src}] {text}")
                    try:
                        observer_persistence.persist_chat_message(ts, src, text, m)
                    except Exception:
                        pass
                last_chat = cur_chat

            # Persist our last seen pointers
            STATE_STORE.write_text(json.dumps({
                "last_seen_ts": now(),
                "observer_version": cur_observer.get('version') if cur_observer else None,
                "chat_count": len(last_chat),
            }, indent=2))

            time.sleep(interval)
        except KeyboardInterrupt:
            log("PO Watchdog stopped by user", "INFO")
            break
        except Exception as e:
            log(f"Watchdog error: {e}", "ERROR")
            time.sleep(interval)

def single_check():
    ob = load_json(STATE_FILE)
    chat = load_json(CHAT_LOG) or []
    if ob:
        log(f"Observer: active_task={ob.get('active_task')}, health={ob.get('observer_health')}, active_agents={ob.get('active_agents')}")
    else:
        log("Observer state file not found")
    log(f"Chat log entries: {len(chat)}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    p.add_argument("--interval", type=int, default=5)
    args = p.parse_args()

    if args.check:
        single_check()
        sys.exit(0)

    tail_loop(args.interval)

if __name__ == "__main__":
    main()
