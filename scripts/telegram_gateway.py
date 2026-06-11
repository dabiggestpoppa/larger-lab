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
from typing import Dict, Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _parts = _line.split("=", 1)
                os.environ.setdefault(_parts[0].strip(), _parts[1].strip())

# Verify token is loaded
if not os.environ.get("TELEGRAM_TOKEN"):
    # Fallback: try loading from project root explicitly
    _repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _env_fallback = os.path.join(_repo_root, ".env")
    if os.path.exists(_env_fallback):
        with open(_env_fallback, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _parts = _line.split("=", 1)
                    os.environ.setdefault(_parts[0].strip(), _parts[1].strip())

from core.observer.vault import Vault
from core.observer.journal import Journal
from core.observer.autonomous_orchestrator import AutonomousOrchestrator
from core.observer.command_router import CommandRouter
from core.observer.po_agent import POAgent
from core.observer.sovereign_field import SovereignField
from core.observer.presence_engine import (
    WATCHERS, TIMELINE, CONTINUITY, PRIORITY,
    start_presence_engine, stop_presence_engine
)
from oce.backend.rate_limit_tracker import record_api_call, get_rate_limit_tracker

# --- Singleton Enforcement (Windows Mutex + PID File) ---
# Uses a Windows named mutex for true OS-level singleton guarantee.
# Also kills ALL other telegram_gateway.py processes on startup.
_PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".telegram_gateway.pid")
_MUTEX_NAME = "Global\\TelegramGateway_Singleton_Mutex"

def _kill_all_gateway_processes():
    """Kill ALL other telegram_gateway.py processes (except self)."""
    my_pid = os.getpid()
    killed = 0
    try:
        result = __import__('subprocess').run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10)
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if not line or 'python.exe' not in line.lower():
                continue
            parts = line.split(',')
            if len(parts) < 2:
                continue
            try:
                pid = int(parts[1].strip('"'))
                if pid == my_pid:
                    continue
                cmd_result = __import__('subprocess').run(
                    ["wmic", "process", "where", f"ProcessId={pid}", "get", "CommandLine"],
                    capture_output=True, text=True, timeout=5)
                if 'telegram_gateway' in cmd_result.stdout:
                    __import__('subprocess').run(["taskkill", "/F", "/PID", str(pid)],
                        capture_output=True, timeout=5)
                    killed += 1
                    log(f"Killed duplicate gateway PID {pid}")
            except (ValueError, OSError, IndexError):
                pass
    except Exception as e:
        log(f"Error scanning for duplicates: {e}")
    if killed > 0:
        time.sleep(2)  # Wait for processes to die
    return killed

def _acquire_singleton():
    """Kill all duplicates + retry. No mutex — kill-duplicates is sufficient."""
    # Step 1: Kill ALL other gateway processes
    killed = _kill_all_gateway_processes()

    # Step 2: If we killed something, wait longer for OS to clean up
    if killed > 0:
        time.sleep(5)

    # Step 3: Write PID file
    try:
        with open(_PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass

    return True

def _release_singleton():
    """Clean up PID file."""
    if os.path.exists(_PID_FILE):
        try:
            os.remove(_PID_FILE)
        except OSError:
            pass

# ---- Logging ----

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
    def __init__(self, window=12, ttl=7200, compact_threshold=8):
        self._sessions = defaultdict(list)
        self._window = window          # max messages to keep verbatim
        self._ttl = ttl                # 2 hour TTL
        self._compact_threshold = compact_threshold  # compact when exceeding this
        self._summaries = defaultdict(list)  # compacted summaries per chat

    def add(self, chat_id, role, text):
        self._sessions[chat_id].append({"role": role, "text": text, "ts": time.time()})
        # Auto-compact: when session gets too long, summarize older messages
        if len(self._sessions[chat_id]) > self._compact_threshold * 2:
            self._compact(chat_id)

    def _compact(self, chat_id):
        """Summarize older messages to reduce context size."""
        msgs = self._sessions[chat_id]
        if len(msgs) <= self._compact_threshold:
            return
        # Keep the most recent N messages verbatim, summarize the rest
        old_msgs = msgs[:-self._compact_threshold]
        recent_msgs = msgs[-self._compact_threshold:]
        # Create a compact summary of old messages
        summary_parts = []
        for m in old_msgs:
            role = m["role"]
            text = m["text"][:100]
            summary_parts.append(f"{role}: {text}")
        summary = f"[Earlier conversation ({len(old_msgs)} messages): " + " | ".join(summary_parts[-4:]) + "]"
        self._summaries[chat_id].append(summary)
        self._sessions[chat_id] = recent_msgs

    def get_context(self, chat_id, max_chars=2000):
        """Get conversation context, compacted to fit within max_chars."""
        now = time.time()
        msgs = [m for m in self._sessions.get(chat_id, []) if now - m["ts"] < self._ttl]
        self._sessions[chat_id] = msgs
        result = []
        total_chars = 0
        # Add compacted summaries first
        for s in self._summaries.get(chat_id, []):
            result.insert(0, {"role": "system", "content": s})
            total_chars += len(s)
        # Add recent messages, newest first, until we hit the char limit
        for m in reversed(msgs):
            entry = {"role": m["role"], "content": m["text"]}
            total_chars += len(m["text"])
            if total_chars > max_chars:
                result.insert(0, {"role": "system", "content": f"[... {len(msgs) - len(result)} more messages truncated]"})
                break
            result.insert(0, entry)
        return result

    def get_summary(self, chat_id):
        """Return a brief summary of recent conversation for continuity."""
        ctx = self.get_context(chat_id, max_chars=500)
        if not ctx:
            return "No prior conversation."
        lines = []
        for m in ctx[-6:]:
            role = m['role']
            text = m['content'][:120]
            lines.append(f"• **{role}:** {text}")
        return "\n".join(lines)

    def clear(self, chat_id):
        """Clear all session data for a chat (for /new command)."""
        self._sessions[chat_id] = []
        self._summaries[chat_id] = []

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

# ─── Per-Chat Queue ──────────────────────────────────────────────────────
# Ensures messages from the same chat are processed sequentially.
# If a user sends 3 messages while agent is working on #1, they queue up.

class ChatQueue:
    """Per-chat sequential message queue. Each chat gets its own worker thread."""

    def __init__(self):
        self._queues: Dict[int, deque] = defaultdict(deque)
        self._locks: Dict[int, threading.Lock] = defaultdict(threading.Lock)
        self._active: Dict[int, bool] = defaultdict(bool)

    def submit(self, chat_id: int, fn: Callable, *args, **kwargs):
        """Submit a task for a specific chat. Tasks run sequentially per chat."""
        with self._locks[chat_id]:
            self._queues[chat_id].append((fn, args, kwargs))
            if self._active[chat_id]:
                # Agent is already working — message will be picked up when current task finishes
                log(f"Chat {chat_id}: queued message (queue depth: {len(self._queues[chat_id])})")
                return
            self._active[chat_id] = True

        # Start processing thread for this chat
        t = threading.Thread(target=self._process_chat, args=(chat_id,), daemon=True)
        t.start()

    def _process_chat(self, chat_id: int):
        """Process all queued messages for a chat sequentially."""
        while True:
            with self._locks[chat_id]:
                if not self._queues[chat_id]:
                    self._active[chat_id] = False
                    return
                fn, args, kwargs = self._queues[chat_id].popleft()

            try:
                fn(*args, **kwargs)
            except Exception as e:
                log(f"Chat {chat_id} task error: {e}")

CHAT_QUEUE = ChatQueue()

# ─── Main Gateway ────────────────────────────────────────────────────────

def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        log("ERROR: TELEGRAM_TOKEN not set")
        return

    # Acquire singleton (kills all duplicates)
    if not _acquire_singleton():
        sys.exit(1)

    log(f"Starting telegram gateway with token {token[:10]}...")
    base_url = f"https://api.telegram.org/bot{token}"
    offset = 0

    # ── Aggressive session reclaim ──
    # Delete webhook + grab session before competing bot can
    _session_reclaimed = False
    for _reclaim in range(10):
        try:
            # Always delete webhook first
            _wh = requests.get(f"{base_url}/deleteWebhook", timeout=10)
            log(f"deleteWebhook: {_wh.json().get('description', _wh.status_code)}")
            time.sleep(1)
            # Immediately try to grab the session
            _clear = requests.get(f"{base_url}/getUpdates", params={"offset": -1, "timeout": 0}, timeout=10)
            _data = _clear.json()
            if _data.get("ok"):
                _cleared = _data.get("result", [])
                log(f"Session reclaimed! Stale updates: {len(_cleared)}")
                if _cleared:
                    offset = max(u["update_id"] for u in _cleared) + 1
                    log(f"Cleared stale updates, starting at offset {offset}")
                _session_reclaimed = True
                break
            else:
                _err = _data.get("description", "")
                if "409" in str(_data.get("error_code", "")) or "Conflict" in _err:
                    log(f"Reclaim attempt {_reclaim+1}: 409 Conflict, retrying in 3s...")
                    time.sleep(3)
                else:
                    log(f"Reclaim attempt {_reclaim+1}: {_data}")
                    time.sleep(2)
        except Exception as _e:
            log(f"Reclaim error (attempt {_reclaim+1}): {_e}")
            time.sleep(2)
    if not _session_reclaimed:
        log("[WARN] Could not reclaim session after 10 attempts. Will keep trying in poll loop.")

    log("Initializing Telegram Presence System — All 3 Phases + Agent...")
    vault = Vault()
    journal = Journal(vault)
    orch = AutonomousOrchestrator(vault=vault, journal=journal)
    router = CommandRouter(vault=vault, journal=journal, orchestrator=orch)
    agent = POAgent()
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
         "🟢 *PO Agent Online*\n\nFull agent capability active:\n• File read/write/edit\n• Shell commands\n• OCE API calls\n• GitHub operations\n• Python execution\n• Vault search\n• Tool-calling loop\n\nSlash commands still work. Chat messages now use full agent.",
         parse_mode="Markdown")

    log("Poll loop started. PO is live on Telegram.")
    _heartbeat = time.time()

    _409_count = 0
    _409_backoff = 5  # starts at 5s, doubles up to 120s
    while True:
        try:
            # Heartbeat every 60s
            if time.time() - _heartbeat > 60:
                log("HEARTBEAT: poll loop alive")
                _heartbeat = time.time()

            # Use short timeout (15s) so we detect 409s fast and can recover
            _poll_url = f"{base_url}/getUpdates?offset={offset}&limit=10&timeout=15"
            r = requests.get(_poll_url, timeout=20)
            data = r.json()
            if not data.get("ok"):
                _err = data.get("description", "")
                if "409" in str(data.get("error_code", "")) or "Conflict" in _err:
                    _409_count += 1
                    _409_backoff = min(_409_backoff * 2, 120)  # exponential backoff, max 2min
                    log(f"409 Conflict (#{_409_count}): another bot instance polling. Backoff {_409_backoff}s...")
                    # Always try deleteWebhook + immediate retry to steal session back
                    try:
                        requests.get(f"{base_url}/deleteWebhook", timeout=10)
                        log("Sent deleteWebhook to clear competing session")
                    except:
                        pass
                    time.sleep(_409_backoff)
                    continue
                else:
                    log(f"getUpdates error: {data}")
                    time.sleep(5)
                    continue
            else:
                if _409_count > 0:
                    log(f"409 resolved after {_409_count} conflicts. Resetting backoff.")
                _409_count = 0
                _409_backoff = 5  # Reset backoff on success

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
                        cmd = text.strip().lower()
                        # Handle /new — clear session and compact
                        if cmd == "/new" or cmd == "/reset":
                            SESSIONS.clear(cid)
                            send(base_url, cid, "🔄 *Session reset.* Starting fresh conversation.")
                            continue
                        # Handle /status — show session stats
                        if cmd == "/status":
                            ctx = SESSIONS.get_context(cid)
                            summary = SESSIONS.get_summary(cid)
                            send(base_url, cid, f"📊 *Session Stats*\n• Messages: {len(ctx)}\n• TTL: 2h\n• Auto-compact: 8 msgs\n\n*Recent:*\n{summary}")
                            continue
                        send(base_url, cid, f"⚡ `{cmd}`")
                        typing(base_url, cid)
                        resp = router.handle(cmd)
                        SESSIONS.add(cid, "user", text)
                        SESSIONS.add(cid, "assistant", resp)
                        send(base_url, cid, resp)
                    else:
                        # Chat message — full agent with streaming progress
                        SESSIONS.add(cid, "user", text)

                        def do_agent(chat_id=cid, msg_text=text):
                            try:
                                log(f"DO_AGENT START: {msg_text[:60]}")

                                # Send brief acknowledgment (typing indicator is enough)
                                typing(base_url, chat_id)

                                # Progress callback — throttled to reduce message spam
                                _progress_lock = threading.Lock()
                                _last_progress_time = [0.0]
                                def on_progress(event_type, data):
                                    try:
                                        # Throttle: max 1 progress msg per 5 seconds
                                        now = time.time()
                                        with _progress_lock:
                                            if now - _last_progress_time[0] < 5.0 and event_type in ("round", "tool_result", "complete"):
                                                return
                                            _last_progress_time[0] = now
                                        if event_type == "round":
                                            pass  # Suppress round-by-round noise
                                        elif event_type == "tool_call":
                                            tool_name = data.get("tool", "unknown")
                                            _fast_tools = {"read_file", "grep", "glob", "list_dir"}
                                            if tool_name not in _fast_tools:
                                                send(base_url, chat_id,
                                                     f"🔧 `{tool_name}`")
                                        elif event_type == "tool_result":
                                            pass  # Suppress tool result previews
                                        elif event_type == "complete":
                                            pass  # Suppress — final response follows
                                        elif event_type == "max_rounds":
                                            send(base_url, chat_id,
                                                 "⚠️ Max tool rounds reached. Generating final response...")
                                        elif event_type == "error":
                                            send(base_url, chat_id,
                                                 f"❌ *Error:* `{data.get('message', 'unknown')[:200]}`")
                                        typing(base_url, chat_id)
                                    except Exception as e:
                                        log(f"Progress send error: {e}")

                                # Build operational context
                                ctx_parts = []

                                # Add workspace scan
                                try:
                                    scan = scan_workspace()
                                    if scan:
                                        ctx_parts.append(f"## Workspace\n{scan}")
                                except: pass

                                # Add sovereign context
                                try:
                                    ctx_parts.append(sov.get_sovereign_context())
                                except: pass

                                # Add timeline
                                try:
                                    timeline_summary = TIMELINE.get_summary(5)
                                    if timeline_summary:
                                        ctx_parts.append(f"## Recent Timeline\n{timeline_summary}")
                                except: pass

                                # Add tasks
                                try:
                                    task_summary = orch.tasks.summary()
                                    if task_summary:
                                        ctx_parts.append(f"## Tasks\n{task_summary}")
                                except: pass

                                # Add session history (compacted, char-limited)
                                history = SESSIONS.get_context(chat_id, max_chars=1500)
                                if history:
                                    ctx_parts.append("## Recent Conversation")
                                    for h in history[-6:]:
                                        ctx_parts.append(f"- **{h['role']}:** {h['content'][:200]}")

                                full_ctx = "\n\n".join(ctx_parts)

                                # Run agent — timeout must cover full model chain:
                                # 3 models × 120s LLM timeout × 1 retry = 360s worst case
                                # Use 300s — if it takes longer, something is wrong
                                import concurrent.futures
                                _agent_future = None
                                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                                    _agent_future = executor.submit(agent.chat, msg_text, full_ctx, progress_callback=on_progress)
                                    try:
                                        resp = _agent_future.result(timeout=300)
                                    except concurrent.futures.TimeoutError:
                                        resp = "🕑 Response timed out after 300s. Try a simpler question or use /new to start fresh."
                                        log("AGENT TIMEOUT")
                                        # Cancel the future to prevent thread leak
                                        _agent_future.cancel()
                                    except Exception as _agent_e:
                                        resp = f"❌ Agent error: `{str(_agent_e)[:200]}`"
                                        log(f"AGENT FUTURE ERROR: {_agent_e}")

                                # Record in timeline and continuity cache
                                TIMELINE.record("agent_chat", {"user": msg_text[:50], "response_len": len(resp)})
                                CONTINUITY.add("last_chat", msg_text[:100])

                                SESSIONS.add(chat_id, "assistant", resp)
                                send(base_url, chat_id, resp)
                                log(f"AGENT RESP ({len(resp)} chars)")
                            except Exception as e:
                                import traceback as _tb
                                log("AGENT ERR: " + str(e) + "\n" + _tb.format_exc())
                                try:
                                    send(base_url, chat_id, f"❌ *Error:* `{str(e)[:200]}`")
                                except: pass

                        # Submit to per-chat queue (sequential per chat, concurrent across chats)
                        CHAT_QUEUE.submit(cid, do_agent)
                        log(f"Chat {cid}: agent task submitted")

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
