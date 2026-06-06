"""
Hermes Telegram Gateway — Full Agent Interface
================================================
Connects Hermes AI agent to Telegram via polling.
Uses AIAgent from Hermes for full tool-calling capability.

Pattern: Same architecture as scripts/telegram_gateway.py (PO Bot)
"""
import os, sys, time, json, requests, datetime, threading
from collections import defaultdict, deque
from typing import Dict, Callable

# ─── Environment ────────────────────────────────────────────────────────────

# Load .env from workspace root
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _parts = _line.split("=", 1)
                os.environ.setdefault(_parts[0].strip(), _parts[1].strip())

# Add Hermes agent to path for AIAgent
sys.path.insert(0, r"C:\Users\wifik\AppData\Local\hermes\hermes-agent")
# Add workspace venv for mcp and other packages
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\.venv\Lib\site-packages")

# ─── PID File Lock ───────────────────────────────────────────────────────────
_PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".hermes_telegram.pid")

def _is_process_alive(pid):
    if pid == os.getpid():
        return True
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

def _acquire_pid_lock():
    pid = os.getpid()
    if os.path.exists(_PID_FILE):
        try:
            with open(_PID_FILE, "r") as f:
                old_pid = int(f.read().strip())
            if old_pid != pid and _is_process_alive(old_pid):
                log("[FATAL] Another Hermes instance already running (PID %d). Exiting." % old_pid)
                sys.exit(1)
        except (ValueError, FileNotFoundError):
            pass
    with open(_PID_FILE, "w") as f:
        f.write(str(pid))

def _release_pid_lock():
    if os.path.exists(_PID_FILE):
        try:
            os.remove(_PID_FILE)
        except OSError:
            pass

# ─── Logging ────────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [HERMES-TG] {msg}"
    print(line, flush=True)
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/hermes-telegram.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except: pass

# ─── Telegram Helpers ───────────────────────────────────────────────────────

def _escape_markdown(text: str) -> str:
    """Escape Telegram MarkdownV2 special chars: _ * [ ] ( ) ~ ` > # + - = | { } . !
    For legacy Markdown, only *, _, `, [ need escaping."""
    special = r"_*`["
    out = []
    for ch in text:
        if ch in special:
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def send(base_url, chat_id, text, parse_mode="Markdown"):
    if not text:
        return

    def _post(text_chunk: str, mode: str | None):
        payload = {"chat_id": chat_id, "text": text_chunk}
        if mode:
            payload["parse_mode"] = mode
        r = requests.post(
            f"{base_url}/sendMessage",
            json=payload,
            timeout=15,
        )
        return r

    def _send_chunk(text_chunk: str):
        # First try with the requested parse mode
        if parse_mode:
            r = _post(text_chunk, parse_mode)
            if r.status_code == 200:
                return True
            # If markdown parse failed, log and fall back to plain text
            err = ""
            try:
                err = r.json().get("description", "")
            except Exception:
                err = r.text[:200]
            log(f"Send markdown failed ({r.status_code}): {err} — falling back to plain text")
        # Plain text fallback (no parse_mode)
        r = _post(text_chunk, None)
        if r.status_code != 200:
            err = ""
            try:
                err = r.json().get("description", "")
            except Exception:
                err = r.text[:200]
            log(f"Send FAILED ({r.status_code}): {err}")
            return False
        return True

    # Split long messages (Telegram 4096 char limit)
    while len(text) > 4000:
        idx = text.rfind("\n", 0, 4000)
        if idx == -1:
            idx = 4000
        _send_chunk(text[:idx])
        text = text[idx:]
    if text:
        _send_chunk(text)

def typing(base_url, chat_id):
    try:
        requests.post(f"{base_url}/sendChatAction",
            json={"chat_id": chat_id, "action": "typing"}, timeout=5)
    except: pass

# ─── Session Manager ────────────────────────────────────────────────────────

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
        ctx = self.get_context(chat_id)
        if not ctx:
            return "No prior conversation."
        lines = []
        for m in ctx[-6:]:
            role = m['role']
            text = m['content'][:120]
            lines.append(f"  {role}: {text}")
        return "\n".join(lines)

SESSIONS = SessionManager()

# ─── Per-Chat Queue (Sequential per chat, concurrent across chats) ──────────

class ChatQueue:
    def __init__(self):
        self._queues: Dict[int, deque] = defaultdict(deque)
        self._locks: Dict[int, threading.Lock] = defaultdict(threading.Lock)
        self._active: Dict[int, bool] = defaultdict(bool)

    def submit(self, chat_id: int, fn: Callable, *args, **kwargs):
        with self._locks[chat_id]:
            self._queues[chat_id].append((fn, args, kwargs))
            if self._active[chat_id]:
                log(f"Chat {chat_id}: queued (depth: {len(self._queues[chat_id])})")
                return
            self._active[chat_id] = True
        t = threading.Thread(target=self._process_chat, args=(chat_id,), daemon=True)
        t.start()

    def _process_chat(self, chat_id: int):
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

# ─── Command Router ─────────────────────────────────────────────────────────

HELP_TEXT = """
🤖 *Hermes Agent — Telegram Interface*

Available commands:
/start — Start conversation
/help — Show this help
/model — Show current model
/clear — Reset conversation context
/usage — Show token usage

Just send a message to chat with Hermes using full agent capabilities (19+ tools, code execution, web search, file operations, etc.).
"""

def handle_command(base_url, chat_id, cmd_text):
    """Handle slash commands."""
    cmd = cmd_text.strip().lower()

    if cmd in ("/start", "/hello"):
        send(base_url, chat_id, "👋 *Hermes is online!*\n\nSend me anything — I have full agent capabilities:\n• Code execution\n• File read/write\n• Web search\n• 19+ tools\n• Memory & context\n\nTry `/help` for all commands.")
        return True

    elif cmd == "/help":
        send(base_url, chat_id, HELP_TEXT, parse_mode="Markdown")
        return True

    elif cmd == "/model":
        # Show current model info
        try:
            from run_agent import AIAgent
            model_name = os.environ.get("HERMES_MODEL", "openrouter/owl-alpha")
            send(base_url, chat_id, f"🧠 *Current Model:* `{model_name}`\n\nTo change, set `HERMES_MODEL` env var or use the `/model <provider/model>` command.")
        except Exception as e:
            send(base_url, chat_id, f"Could not determine model: {e}")
        return True

    elif cmd.startswith("/model "):
        # Change model at runtime
        new_model = cmd.split("/model ", 1)[1].strip()
        if new_model:
            os.environ["HERMES_MODEL"] = new_model
            send(base_url, chat_id, f"✅ Model changed to: `{new_model}`")
        else:
            send(base_url, chat_id, "Usage: `/model <provider/model_name>`")
        return True

    elif cmd == "/clear":
        SESSIONS._sessions.pop(chat_id, None)
        send(base_url, chat_id, "🧹 Conversation context cleared.")
        return True

    elif cmd == "/usage":
        send(base_url, chat_id, "📊 Usage tracking not yet implemented for Hermes. Coming soon.")
        return True

    return False

# ─── Agent Integration ──────────────────────────────────────────────────────

def create_hermes_agent(chat_id: int):
    """Create a configured Hermes AIAgent for this chat session."""
    from run_agent import AIAgent

    # Default to a real OpenRouter model. "openrouter/owl-alpha" is not on
    # OpenRouter — fall back to "openrouter/auto" which routes to best model.
    model = os.environ.get("HERMES_MODEL", "openrouter/auto")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")

    agent = AIAgent(
        model=model,
        provider="openrouter",
        api_key=openrouter_key,
        base_url="https://openrouter.ai/api/v1",
        platform="telegram",
        user_id=str(chat_id),
        chat_id=str(chat_id),
        chat_type="private",
        max_iterations=10,        # Reduced from 50 to avoid hangs
        tool_delay=0.5,
        quiet_mode=True,
        save_trajectories=False,
        enabled_toolsets=[],       # No tools by default — pure chat, no hangs
        ephemeral_system_prompt=(
            "You are Hermes, a helpful AI assistant. "
            "The user is interacting via Telegram, so keep replies short and conversational. "
            "Avoid Markdown characters like * and _ in your reply — use plain text."
        ),
    )
    return agent

def run_agent_task(base_url, chat_id, text):
    """Execute agent in a thread with timeout."""
    try:
        typing(base_url, chat_id)

        # Create or reuse agent for this chat
        agent = create_hermes_agent(chat_id)

        # Get session context
        history = SESSIONS.get_context(chat_id)

        # Build messages with history
        messages = []
        for h in history[-8:]:  # Last 8 messages
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": text})

        log(f"AGENT START: chat={chat_id}, model={agent.model}, history={len(history)}")

        # Run conversation with timeout
        import concurrent.futures
        response = None
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(agent.run_conversation, messages)
            try:
                response = future.result(timeout=120)
            except concurrent.futures.TimeoutError:
                log(f"AGENT TIMEOUT: chat={chat_id} (120s)")
                response = "⏱️ Response timed out after 120s. Try a simpler question."
            except Exception as e:
                import traceback as _tb
                log(f"AGENT EXCEPTION: chat={chat_id}: {e}\n{_tb.format_exc()[:500]}")
                response = f"❌ Agent error: {str(e)[:300]}"

        # Normalize response — AIAgent.run_conversation returns a DICT like:
        #   {"final_response": "...", "last_reasoning": "...", "messages": [...]}
        # We just want the final text. Also handle None, list, etc.
        if response is None:
            log(f"AGENT RETURNED NONE: chat={chat_id}")
            response = "(no response from agent — try again)"
        elif isinstance(response, dict):
            response = response.get("final_response") or response.get("response") or response.get("text") or str(response)
        elif isinstance(response, list):
            # Could be list of message dicts — extract last assistant content
            for msg in reversed(response):
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                response = part.get("text", "")
                                break
                    elif isinstance(content, str) and content:
                        response = content
                        break
            if not isinstance(response, str):
                response = str(response)
        if not isinstance(response, str):
            response = str(response)

        log(f"AGENT DONE: chat={chat_id}, response_len={len(response)}")

        # Record in session
        SESSIONS.add(chat_id, "user", text)
        SESSIONS.add(chat_id, "assistant", response)

        send(base_url, chat_id, response)

    except Exception as e:
        import traceback as _tb
        log(f"AGENT TASK ERROR: chat={chat_id}: {e}\n{_tb.format_exc()[:500]}")
        try:
            send(base_url, chat_id, f"❌ Error: `{str(e)[:200]}`")
        except Exception as se:
            log(f"Send-on-error also failed: {se}")

# ─── Main Gateway Loop ──────────────────────────────────────────────────────

def main():
    token = os.environ.get("HERMES_TELEGRAM_TOKEN")
    if not token:
        log("ERROR: HERMES_TELEGRAM_TOKEN not set in environment")
        log("Set it in .env: HERMES_TELEGRAM_TOKEN=<bot_token>")
        return

    # Acquire PID lock FIRST — before any network connections
    _acquire_pid_lock()

    base_url = f"https://api.telegram.org/bot{token}"
    chat_id = os.environ.get("HERMES_TELEGRAM_CHAT_ID", "")
    offset = 0

    # Clear stale updates
    try:
        r = requests.get(f"{base_url}/getUpdates",
            params={"offset": -1, "timeout": 0}, timeout=5)
        data = r.json()
        if data.get("ok") and data.get("result"):
            offset = max(u["update_id"] for u in data["result"]) + 1
            log(f"Cleared {len(data['result'])} stale updates, offset={offset}")
    except Exception as e:
        log(f"Stale clear error: {e}")

    # Startup notification
    if chat_id:
        send(base_url, int(chat_id),
            "🟢 *Hermes Agent Online*\n\nFull agent capability active:\n• 19+ tools (code, shell, web, files)\n• Tool-calling loop\n• Session memory\n• Model switching via /model\n\nSend any message to start.",
            parse_mode="Markdown")

    log("Hermes Telegram Gateway started. Polling for messages...")
    log(f"Model: {os.environ.get('HERMES_MODEL', 'openrouter/owl-alpha')}")
    log(f"Bot token configured: {token[:8]}...")

    _heartbeat = time.time()

    while True:
        try:
            if time.time() - _heartbeat > 60:
                log("HEARTBEAT: poll loop alive")
                _heartbeat = time.time()

            r = requests.get(
                f"{base_url}/getUpdates",
                params={"offset": offset, "limit": 10, "timeout": 30},
                timeout=35
            )

            # Check for HTTP error before parsing JSON
            if r.status_code == 409:
                log("409 Conflict — another getUpdates request is in flight. Exiting to let the other instance handle messages.")
                # Sleep briefly so we don't immediately restart in a loop
                time.sleep(5)
                # Release PID lock and exit cleanly
                _release_pid_lock()
                log("Exiting due to 409 conflict. Restart manually if needed.")
                return
            if r.status_code != 200:
                log(f"getUpdates HTTP {r.status_code}: {r.text[:200]}")
                time.sleep(5)
                continue

            data = r.json()

            if not data.get("ok"):
                log(f"getUpdates error: {data}")
                time.sleep(5)
                continue

            results = data.get("result", [])
            if results:
                log(f"poll: offset={offset} got={len(results)}")

            for u in results:
                offset = u["update_id"] + 1
                msg = u.get("message") or {}
                text = msg.get("text") or msg.get("caption") or ""
                cid = msg.get("chat", {}).get("id")
                if not text or not cid:
                    continue

                log(f"MSG [{cid}]: {text[:80]}")

                try:
                    if text.strip().startswith("/"):
                        # Slash command
                        cmd = text.strip()
                        if handle_command(base_url, cid, cmd):
                            continue
                        # Unknown command — fall through to agent
                        typing(base_url, cid)
                        resp = f"Unknown command. Type `/help` for available commands."
                        send(base_url, cid, resp)
                        SESSIONS.add(cid, "user", text)
                        SESSIONS.add(cid, "assistant", resp)
                    else:
                        # Chat message — full agent
                        SESSIONS.add(cid, "user", text)
                        CHAT_QUEUE.submit(cid, run_agent_task, base_url, cid, text)
                        log(f"Chat {cid}: agent task submitted")

                except Exception as e:
                    log(f"MSG ERR: {e}")
                    try:
                        send(base_url, cid, f"❌ Error: `{str(e)[:200]}`")
                    except: pass

        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            log(f"POLL ERR: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()