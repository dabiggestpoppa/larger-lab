"""Start script for Telegram Presence System — All 3 Phases.

Phase 1: Telegram Runtime Foundation
- Async LLM calls (never blocks gateway)
- Session continuity with TTL
- Workspace scanning
- Streaming progress updates
- Command routing

Phase 2: Operational Telemetry + Live Field
- /observers — observer health status
- /drift — drift detection
- /timeline — operational history
- /vault — vault metrics + search
- /tasks — live task tracking

Phase 3: Autonomous Presence Engine
- Watcher Network (vault, progress, health)
- Priority Evaluator (anti-spam filtering)
- Autonomous Push (proactive communication)
- Continuity Cache (persistent context)
- Timeline Engine (operational history)
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _parts = _line.split("=", 1)
                os.environ.setdefault(_parts[0].strip(), _parts[1].strip())

from scripts.telegram_gateway import main

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

# ─── Session Manager ────────────────────────────────────────────────────

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
            fs = sorted(os.listdir(pd), key=lambda f: os.path.getmtime(os.path.join(pd, f)), reverse=True)[:5]
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

# ─── Main Gateway ────────────────────────────────────────────────────────

def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token: log("ERROR: TELEGRAM_TOKEN not set"); return
    base_url = f"https://api.telegram.org/bot{token}"
    offset = 0

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
                        # Chat message — async LLM call so gateway never blocks
                        SESSIONS.add(cid, "user", text)

                        # Step 1: Acknowledge
                        send(base_url, cid, f"🧠 *Processing:* `{text[:60]}`")

                        # Step 2: Scan workspace
                        scan_result = scan_workspace()
                        send(base_url, cid, f"🔍 *Workspace Scan:*\n{scan_result}")

                        # Step 3: Run LLM in background thread
                        def do_llm():
                            try:
                                typing(base_url, cid)
                                ctx = sov.get_sovereign_context()
                                history = SESSIONS.get_context(cid)
                                if history:
                                    ctx += f"\n\n## Recent Conversation\n"
                                    for h in history[-6:]:
                                        ctx += f"- **{h['role']}:** {h['text'][:100]}\n"
                                resp = agent.chat(text, sovereign_context=ctx)
                                SESSIONS.add(cid, "assistant", resp)
                                send(base_url, cid, resp)
                                log(f"LLM RESP ({len(resp)} chars)")
                            except Exception as e:
                                log(f"LLM ERR: {e}")
                                try: send(base_url, cid, f"❌ *Error:* `{str(e)[:200]}`")
                                except: pass

                        t = threading.Thread(target=do_llm, daemon=True)
                        t.start()

                except Exception as e:
                    log(f"ERR: {e}")
                    try: send(base_url, cid, f"❌ *Error:* `{str(e)[:200]}`")
                    except: pass
        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            log(f"Poll err: {e}"); time.sleep(5)

if __name__ == "__main__":
    main()
