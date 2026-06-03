"""
Telegram Presence System — Phase 1: Runtime Foundation
=====================================================
Persistent operational observer interface with:
- Async LLM calls (never blocks gateway)
- Session continuity with TTL
- Workspace scanning
- Streaming progress updates
- Command routing
- OpenClaw-style presence
"""
import os, sys, time, json, requests, datetime, threading
from collections import defaultdict, deque

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
from core.observer.presence_engine import (
    WATCHERS, TIMELINE, CONTINUITY, PRIORITY,
    start_presence_engine, stop_presence_engine
)

# ─── Logging ─────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = "[" + ts + "] " + str(msg)
    print(line, flush=True)
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/telegram-gateway.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except: pass

# ─── Telegram Helpers ────────────────────────────────────────────────────

def send(base_url, chat_id, text, parse_mode="Markdown"):
    if not text: return
    while len(text) > 4000:
        idx = text.rfind("\n", 0, 4000)
        if idx == -1: idx = 4000
        try:
            requests.post(f"{base_url}/sendMessage",
                json={"chat_id": chat_id, "text": text[:idx], "parse_mode": parse_mode},
                timeout=15)
        except: pass
        text = text[idx:]
    if text:
        try:
            requests.post(f"{base_url}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
                timeout=15)
        except: pass

def typing(base_url, chat_id):
    try:
        requests.post(f"{base_url}/sendChatAction",
            json={"chat_id": chat_id, "action": "typing"}, timeout=5)
    except: pass

# ─── Session Manager ─────────────────────────────────────────────────────

class SessionManager:
    def __init__(self, window=20, ttl=3600):
        self._sessions = defaultdict(list)
        self._window = window
        self._ttl = ttl

    def add(self, chat_id, role, text):
        self._sessions[chat_id].append({"role": role, "text": text, "ts": time.time()})
        if len(self._sessions[chat_id]) > self._window * 2:
            self._sessions[chat_id] = self._sessions[chat_id][-self._window:]

    def get_context(self, chat_id):
        now = time.time()
        msgs = [m for m in self._sessions.get(chat_id, []) if now - m["ts"] < self._ttl]
        self._sessions[chat_id] = msgs
        return [{"role": m["role"], "content": m["text"]} for m in msgs]

    def get_summary(self, chat_id):
        """Return a brief summary of recent conversation for continuity."""
        ctx = self.get_context(chat_id)
        if not ctx:
            return "No prior conversation."
        lines = []
        for m in ctx[-6:]:
            role = m['role']
            text = m['content'][:120]
            lines.append(f"• **{role}:** {text}")
        return "\n".join(lines)

SESSIONS = SessionManager()

# ─── Workspace Scanner ──────────────────────────────────────────────────

def scan_workspace():
    lines = []
    try:
        tc = os.path.join(os.getcwd(), "shared-conversations", "team-chat.md")
        if os.path.exists(tc):
            mt = datetime.datetime.fromtimestamp(os.path.getmtime(tc))
            lc = sum(1 for _ in open(tc, encoding="utf-8", errors="ignore"))
            lines.append(f"📋 `team-chat.md` — {lc} lines, updated {mt.strftime('%H:%M')}")
    except: pass
    try:
        pd = os.path.join(os.getcwd(), "progress")
        if os.path.exists(pd):
            fs = sorted(os.listdir(pd),
                key=lambda f: os.path.getmtime(os.path.join(pd, f)), reverse=True)[:5]
            if fs:
                lines.append("📁 *Recent progress:*")
                for f in fs:
                    mt = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(pd, f)))
                    lines.append(f"  • `{f}` — {mt.strftime('%H:%M')}")
    except: pass
    try:
        v = Vault()
        cnt = sum(1 for _, _, files in os.walk(v.path) for f in files if f.endswith(".md"))
        lines.append(f"📚 *Vault:* {cnt} notes")
    except: pass
    return "\n".join(lines) if lines else "No recent activity."

# ─── Async Task Queue ────────────────────────────────────────────────────

class TaskQueue:
    """Bounded async task queue — prevents runaway threading."""
    def __init__(self, max_workers=3):
        self._queue = deque()
        self._lock = threading.Lock()
        self._active = 0
        self._max_workers = max_workers

    def submit(self, fn, *args, **kwargs):
        with self._lock:
            if self._active >= self._max_workers:
                log(f"Task queue full ({self._active}/{self._max_workers}), dropping task")
                return False
            self._active += 1
        def _run():
            try:
                fn(*args, **kwargs)
            except Exception as e:
                log(f"Task error: {e}")
            finally:
                with self._lock:
                    self._active -= 1
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return True

TASK_QUEUE = TaskQueue(max_workers=3)

# ─── Main Gateway ────────────────────────────────────────────────────────

def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        log("ERROR: TELEGRAM_TOKEN not set")
        return

    base_url = f"https://api.telegram.org/bot{token}"
    offset = 0

    # Clear any stale updates from previous runs so we start fresh
    try:
        _clear = requests.get(f"{base_url}/getUpdates", params={"offset": -1, "timeout": 0}, timeout=5)
        _cleared = _clear.json().get("result", [])
        log(f"Stale check: {len(_cleared)} pending updates")
        if _cleared:
            offset = max(u["update_id"] for u in _cleared) + 1
            log(f"Cleared stale updates, starting at offset {offset}")
    except Exception as _e:
        log(f"Stale clear error: {_e}")

    log("Initializing Telegram Presence System — All 3 Phases...")
    vault = Vault()
    journal = Journal(vault)
    orch = AutonomousOrchestrator(vault=vault, journal=journal)
    router = CommandRouter(vault=vault, journal=journal, orchestrator=orch)
    agent = ChatAgent()
    sov = SovereignField()

    # Start Phase 3: Presence Engine
    start_presence_engine()
    log(f"Vault: {vault.path}")
    try:
        r = requests.get(f"{base_url}/getMe", timeout=10)
        bi = r.json().get("result", {})
        log(f"Bot connected: @{bi.get('username')} ({bi.get('first_name')})")
    except Exception as e:
        log(f"ERROR: {e}")
        return

    # Send startup notification
    send(base_url, int(os.environ.get("TELEGRAM_CHAT_ID", "0")),
         "🟢 *PO Phase 1 Online*\n\nTelegram Runtime Foundation active.\nSession continuity • Workspace scan • Async LLM • Command routing",
         parse_mode="Markdown")

    log("Poll loop started. PO is live on Telegram.")
    _heartbeat = time.time()

    while True:
        try:
            # Heartbeat every 60s
            if time.time() - _heartbeat > 60:
                log("HEARTBEAT: poll loop alive")
                _heartbeat = time.time()

            _poll_url = f"{base_url}/getUpdates?offset={offset}&limit=10&timeout=30"
            r = requests.get(_poll_url, timeout=35)
            data = r.json()
            if not data.get("ok"):
                log(f"getUpdates error: {data}")
                time.sleep(5)
                continue

            results = data.get("result", [])
            log(f"poll: offset={offset} got={len(results)}")
            for u in results:
                offset = u["update_id"] + 1
                msg = u.get("message") or {}
                text = msg.get("text") or msg.get("caption")
                cid = msg.get("chat", {}).get("id")
                if not text or not cid:
                    continue

                log(f"MSG [{cid}]: {text[:80]}")

                try:
                    if text.strip().startswith("/"):
                        # Slash command — synchronous (fast)
                        cmd = text.strip()
                        send(base_url, cid, f"⚡ `{cmd}`")
                        typing(base_url, cid)
                        resp = router.handle(cmd)
                        SESSIONS.add(cid, "user", text)
                        SESSIONS.add(cid, "assistant", resp)
                        send(base_url, cid, resp)
                    else:
                        # Chat message — async via task queue
                        SESSIONS.add(cid, "user", text)

                        # Check for continuity queries
                        lower = text.lower().strip()
                        continuity_triggers = ["what happened", "what's up", "whats up",
                                               "what going on", "status update", "summary",
                                               "what did i miss", "catch me up", "yo", "yoo", "yoioo"]
                        is_continuity = any(t in lower for t in continuity_triggers)

                        def do_llm(chat_id=cid, msg_text=text, continuity=is_continuity):
                            try:
                                send(base_url, chat_id,
                                     f"🧠 *Processing:* `{msg_text[:60]}`")
                                typing(base_url, chat_id)

                                scan_result = scan_workspace()
                                send(base_url, chat_id,
                                     f"🔍 *Workspace Scan:*\n{scan_result}")
                                typing(base_url, chat_id)

                                # Build rich context
                                ctx = sov.get_sovereign_context()

                                # Add timeline for continuity queries
                                if continuity:
                                    timeline_summary = TIMELINE.get_summary(10)
                                    ctx += f"\n\n## Operational Timeline\n{timeline_summary}"

                                    # Add task summary
                                    try:
                                        task_summary = orch.tasks.summary()
                                        ctx += f"\n\n## Tasks\n{task_summary}"
                                    except:
                                        pass

                                # Add session history — pass as conversation context
                                history = SESSIONS.get_context(chat_id)
                                if history:
                                    ctx += "\n\n## Recent Conversation\n"
                                    for h in history[-6:]:
                                        ctx += f"- **{h['role']}:** {h['content'][:100]}\n"

                                # Build full message list for multi-turn
                                messages = [{"role": "system", "content": agent._build_system_prompt(sovereign_context=ctx)}]
                                for h in history:
                                    messages.append({"role": h["role"], "content": h["content"]})
                                messages.append({"role": "user", "content": msg_text})

                                # Call LLM directly with full history
                                resp, used_model, err = agent._call_llm(messages, agent.current_model)
                                if not resp:
                                    # Try next model in chain
                                    for attempt in range(1, len(agent.MODEL_CHAIN)):
                                        model = agent.MODEL_CHAIN[(agent._model_index + attempt) % len(agent.MODEL_CHAIN)]
                                        resp, used_model, err = agent._call_llm(messages, model)
                                        if resp:
                                            break

                                # Record in timeline and continuity cache
                                TIMELINE.record("chat", {"user": msg_text[:50], "response_len": len(resp)})
                                CONTINUITY.add("last_chat", msg_text[:100])

                                SESSIONS.add(chat_id, "assistant", resp)
                                send(base_url, chat_id, resp)
                                log(f"LLM RESP ({len(resp)} chars)")
                            except Exception as e:
                                import traceback as _tb
                                log("LLM ERR: " + str(e) + "\n" + _tb.format_exc())
                                try:
                                    send(base_url, chat_id, "❌ *Error:* `" + str(e)[:200] + "`")
                                except: pass

                        TASK_QUEUE.submit(do_llm)

                except Exception as e:
                    log(f"ERR: {e}")
                    try:
                        send(base_url, cid, f"❌ *Error:* `{str(e)[:200]}`")
                    except: pass

        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            log(f"Poll err: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
