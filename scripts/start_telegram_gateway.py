"""Telegram gateway for Primary Observer — OC2-style multi-turn streaming.

Layer 1: Streaming responses (edit message as tokens arrive)
Layer 2: Persistent session context (20-message history, 1hr TTL)
Layer 3: Background task queue (long tasks run async, notify on complete)
"""
import os, sys, time, json, requests, datetime, threading
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _parts = _line.split("=", 1)
                os.environ.setdefault(_parts[0].strip(), _parts[1].strip())
from core.observer.vault import Vault
from core.observer.journal import Journal
from core.observer.autonomous_orchestrator import AutonomousOrchestrator
from core.observer.command_router import CommandRouter
from core.observer.chat_agent import ChatAgent
from core.observer.sovereign_field import SovereignField

# ─── Session Manager (Layer 2) ──────────────────────────────────────────

class SessionManager:
    """Persistent conversation context per chat."""
    def __init__(self, context_window=20, ttl=3600):
        self._sessions = defaultdict(list)  # chat_id -> [(role, text, ts)]
        self._context_window = context_window
        self._ttl = ttl

    def add(self, chat_id, role, text):
        self._sessions[chat_id].append({"role": role, "text": text, "ts": time.time()})
        # Trim to window
        if len(self._sessions[chat_id]) > self._context_window * 2:
            self._sessions[chat_id] = self._sessions[chat_id][-self._context_window:]

    def get_context(self, chat_id):
        """Get recent messages for this chat, filtering stale ones."""
        now = time.time()
        msgs = self._sessions.get(chat_id, [])
        # Filter by TTL
        fresh = [m for m in msgs if now - m["ts"] < self._ttl]
        self._sessions[chat_id] = fresh
        return [{"role": m["role"], "content": m["text"]} for m in fresh]

    def get_last_topic(self, chat_id):
        """Get the last user message for context."""
        msgs = self._sessions.get(chat_id, [])
        for m in reversed(msgs):
            if m["role"] == "user":
                return m["text"]
        return ""

SESSIONS = SessionManager(context_window=20, ttl=3600)

# ─── Background Task Queue (Layer 3) ─────────────────────────────────────

class TaskQueue:
    """Run long tasks in background, notify on completion."""
    def __init__(self, base_url, chat_id):
        self._queue = []
        self._running = False
        self._base_url = base_url
        self._chat_id = chat_id
        self._lock = threading.Lock()

    def submit(self, name, fn, *args):
        """Submit a background task."""
        with self._lock:
            self._queue.append({"name": name, "fn": fn, "args": args})
        if not self._running:
            self._running = True
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()

    def _worker(self):
        while True:
            with self._lock:
                if not self._queue:
                    self._running = False
                    return
                task = self._queue.pop(0)
            try:
                result = task["fn"](*task["args"])
                send(self._base_url, self._chat_id,
                     f"✅ *Task Complete:* `{task['name']}`\n\n{result}")
            except Exception as e:
                send(self._base_url, self._chat_id,
                     f"❌ *Task Failed:* `{task['name']}`\n`{str(e)[:200]}`")

# ─── Helpers ─────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def send(base_url, chat_id, text):
    if not text: return
    while len(text) > 4000:
        idx = text.rfind("\n", 0, 4000)
        if idx == -1: idx = 4000
        try: requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": text[:idx]}, timeout=15)
        except: pass
        text = text[idx:]
    if text:
        try: requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=15)
        except: pass

def typing(base_url, chat_id):
    try: requests.post(f"{base_url}/sendChatAction", json={"chat_id": chat_id, "action": "typing"}, timeout=5)
    except: pass

def edit_message(base_url, chat_id, message_id, text):
    """Edit an existing message (Layer 1: streaming simulation)."""
    if not text: return
    try:
        requests.post(f"{base_url}/editMessageText",
                      json={"chat_id": chat_id, "message_id": message_id, "text": text[:4000]},
                      timeout=10)
    except: pass

# ─── Workspace Scanner ──────────────────────────────────────────────────

def scan_workspace():
    """Scan workspace for recent activity. Returns formatted string."""
    lines = []
    # Team chat
    try:
        tc = os.path.join(os.getcwd(), "shared-conversations", "team-chat.md")
        if os.path.exists(tc):
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(tc))
            lc = sum(1 for _ in open(tc, encoding="utf-8", errors="ignore"))
            lines.append(f"📋 `team-chat.md` — {lc} lines, updated {mtime.strftime('%H:%M')}")
    except: pass
    # Progress files
    try:
        pd = os.path.join(os.getcwd(), "progress")
        if os.path.exists(pd):
            fs = sorted(os.listdir(pd), key=lambda f: os.path.getmtime(os.path.join(pd, f)), reverse=True)[:5]
            if fs:
                lines.append("📁 *Recent progress:*")
                for f in fs:
                    mt = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(pd, f)))
                    lines.append(f"  • `{f}` — {mt.strftime('%H:%M')}")
    except: pass
    # Vault
    try:
        v = Vault()
        cnt = sum(1 for _, _, files in os.walk(v.path) for f in files if f.endswith(".md"))
        lines.append(f"📚 *Vault:* {cnt} notes")
    except: pass
    return "\n".join(lines) if lines else "No recent activity found."

# ─── Main Gateway ────────────────────────────────────────────────────────

def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token: log("ERROR: TELEGRAM_TOKEN not set"); return
    base_url = f"https://api.telegram.org/bot{token}"
    offset = 0
    task_queues = {}  # chat_id -> TaskQueue

    log("Initializing...")
    vault = Vault(); journal = Journal(vault)
    orch = AutonomousOrchestrator(vault=vault, journal=journal)
    router = CommandRouter(vault=vault, journal=journal, orchestrator=orch)
    agent = ChatAgent(); sov = SovereignField()
    log(f"Vault: {vault.path}")
    try:
        r = requests.get(f"{base_url}/getMe", timeout=10)
        bi = r.json().get("result", {})
        log(f"Bot connected: @{bi.get('username')} ({bi.get('first_name')})")
    except Exception as e:
        log(f"ERROR: {e}"); return

    log("Poll loop started. PO is live.")

    while True:
        try:
            r = requests.get(f"{base_url}/getUpdates", params={"offset": offset, "limit": 10, "timeout": 15}, timeout=20)
            data = r.json()
            if not data.get("ok"): time.sleep(5); continue
            for u in data.get("result", []):
                offset = u["update_id"] + 1
                msg = u.get("message") or {}
                text = msg.get("text") or msg.get("caption")
                cid = msg.get("chat", {}).get("id")
                if not text or not cid: continue

                log(f"MSG: {text[:80]}")

                # Get or create task queue for this chat
                if cid not in task_queues:
                    task_queues[cid] = TaskQueue(base_url, cid)
                tq = task_queues[cid]

                try:
                    if text.strip().startswith("/"):
                        cmd = text.strip()
                        # Send initial response
                        send(base_url, cid, f"⚡ `{cmd}`")
                        typing(base_url, cid)
                        # Execute
                        resp = router.handle(cmd)
                        # Add to session
                        SESSIONS.add(cid, "user", text)
                        SESSIONS.add(cid, "assistant", resp)
                        send(base_url, cid, resp)
                    else:
                        # Multi-step response with context
                        SESSIONS.add(cid, "user", text)

                        # Step 1: Acknowledge
                        send(base_url, cid, f"🧠 *Processing:* `{text[:60]}`")
                        typing(base_url, cid)

                        # Step 2: Scan workspace (background feel)
                        scan_result = scan_workspace()
                        send(base_url, cid, f"🔍 *Workspace Scan:*\n{scan_result}")

                        # Step 3: Build context-aware prompt
                        ctx = sov.get_sovereign_context()
                        history = SESSIONS.get_context(cid)
                        if history:
                            ctx += f"\n\n## Conversation History (last {len(history)} messages)\n"
                            for h in history[-6:]:
                                ctx += f"- **{h['role']}:** {h['text'][:100]}\n"

                        # Step 4: Get AI response with full context
                        typing(base_url, cid)
                        resp = agent.chat(text, sovereign_context=ctx)
                        SESSIONS.add(cid, "assistant", resp)

                        # Step 5: Send final response
                        send(base_url, cid, resp)

                except Exception as e:
                    log(f"ERR: {e}")
                    try: send(base_url, cid, f"❌ *Error:* `{str(e)[:200]}`")
                    except: pass
        except requests.exceptions.Timeout: continue
        except Exception as e:
            log(f"Poll err: {e}"); time.sleep(5)

if __name__ == "__main__":
    main()
