"""
PO Streamer — poll observer actions DB and stream events to team chat and Obsidian vault.

Run: python tools/po_streamer.py
"""
from pathlib import Path
import time
import json
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.observer import observer_persistence
from tools.obsidian_access import vault_write

TEAM_CHAT = ROOT / 'shared-conversations' / 'team-chat.md'
STATE_FILE = ROOT / 'tools' / '.po-streamer-state.json'

def now():
    return datetime.now().isoformat()

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}

def save_state(s):
    STATE_FILE.write_text(json.dumps(s, indent=2), encoding='utf-8')

def append_team_chat(text: str):
    TEAM_CHAT.parent.mkdir(parents=True, exist_ok=True)
    with open(TEAM_CHAT, 'a', encoding='utf-8') as f:
        f.write(text + '\n')

def run(interval: int = 5):
    state = load_state()
    last_event_id = state.get('last_event_id', 0)
    # prepare notifier (lazy)
    notifier = None
    while True:
        try:
            rows = observer_persistence.query_recent_events(200)
            # rows are in DESC order
            new = [r for r in reversed(rows) if r[0] > last_event_id]
            for r in new:
                eid, event_type, source, ts, data = r
                msg = f"[{ts}] [{event_type}] from {source}: {data}"
                append_team_chat(msg)
                # write short vault note
                title = f"PO Event {eid} {event_type}"
                body = json.dumps(data, indent=2)
                content = "# PO Event {eid}\n\n- time: {ts}\n- type: {event_type}\n- source: {source}\n\n```\n{body}\n```\n".format(eid=eid, ts=ts, event_type=event_type, source=source, body=body)
                vault_write(category='execution', title=title, content=content)
                last_event_id = eid
                # Desktop notification for critical events
                try:
                    critical = [
                        'task_failed', 'observer_degraded', 'spawn_failed', 'continuity_lost',
                        'repair_triggered', 'agent_terminated'
                    ]
                    text = str(data)
                    if any(k in event_type.lower() for k in critical) or 'circuit breaker' in text.lower() or 'failed' in text.lower():
                        try:
                            # Try import; if not available, attempt to install
                            if notifier is None:
                                try:
                                    from win10toast import ToastNotifier
                                except Exception:
                                    import subprocess, sys
                                    subprocess.run([sys.executable, '-m', 'pip', 'install', 'win10toast'], check=False)
                                    from win10toast import ToastNotifier
                                notifier = ToastNotifier()
                            title = f"PO Alert: {event_type}"
                            body = f"{source}: {str(data)[:200]}"
                            notifier.show_toast(title, body, duration=7, threaded=True)
                        except Exception:
                            pass
                except Exception:
                    pass

            state['last_event_id'] = last_event_id
            save_state(state)
            time.sleep(interval)
        except KeyboardInterrupt:
            break
        except Exception:
            time.sleep(interval)

if __name__ == '__main__':
    run()
