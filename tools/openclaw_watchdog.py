#!/usr/bin/env python3
"""
OpenClaw Gateway Watchdog for OC2

Monitors the OC2 gateway health and auto-restarts on failure.
Prevents 7-hour outages like 2026-06-06.

Usage:
    python tools/openclaw_watchdog.py
    python tools/openclaw_watchdog.py --interval 30 --auto-restart

Checks performed every interval:
1. GET /health endpoint — must return {"ok": true, "status": "live"}
2. Last 5 min of log — must NOT contain FailoverError or Unknown model errors
3. Port 18790 must be listening

On failure:
- Auto-restart via Stop-ScheduledTask / Start-ScheduledTask
- Send Telegram alert to owner
- Log to watchdog log file
- Exit after 3 consecutive failures (give up, alert loudly)

Author: PM2 (Polymorph 2) — 2026-06-06
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Try to import requests; fall back to urllib if not available
try:
    import requests  # type: ignore
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.error

# ============================================================================
# Configuration
# ============================================================================

GATEWAY_HOST = "127.0.0.1"
GATEWAY_PORT = 18790
GATEWAY_URL = f"http://{GATEWAY_HOST}:{GATEWAY_PORT}/health"
SCHEDULED_TASK = "OpenClaw-2-Gateway"
LOG_FILE = Path(os.environ.get("TEMP", "C:/Users/wifik/AppData/Local/Temp")) / "openclaw" / "openclaw-2026-06-06.log"
WATCHDOG_LOG = Path(__file__).parent.parent / "logs" / "openclaw_watchdog.log"
WATCHDOG_STATE = Path(__file__).parent.parent / "logs" / "openclaw_watchdog_state.json"

# Telegram alert settings (uses OpenClaw's bot token, sendMessage directly)
TELEGRAM_BOT_TOKEN = "8945439460:AAHZT2Xx0jHaApejRJYi-xORG5FkKNAQ5yM"
TELEGRAM_CHAT_ID = "8258195396"  # owner

# Watchdog tuning
HEALTH_TIMEOUT_SEC = 5
LOG_ERROR_WINDOW_MIN = 5
MAX_CONSECUTIVE_FAILURES = 3
RESTART_COOLDOWN_SEC = 60  # don't restart more than once per minute
STARTUP_GRACE_SEC = 120  # after restart, wait this long before checking health


# ============================================================================
# Logging
# ============================================================================

def log(msg: str, level: str = "INFO"):
    """Log to both console and watchdog log file."""
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)
    try:
        WATCHDOG_LOG.parent.mkdir(parents=True, exist_ok=True)
        with WATCHDOG_LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"[WARN] Could not write to watchdog log: {e}", flush=True)


def load_state() -> dict:
    """Load persistent state (failure counts, last restart time)."""
    if WATCHDOG_STATE.exists():
        try:
            return json.loads(WATCHDOG_STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"consecutive_failures": 0, "last_restart": 0, "last_alert": 0}


def save_state(state: dict):
    """Save persistent state."""
    try:
        WATCHDOG_STATE.parent.mkdir(parents=True, exist_ok=True)
        WATCHDOG_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as e:
        log(f"Could not save state: {e}", "WARN")


# ============================================================================
# Health checks
# ============================================================================

def check_health() -> tuple[bool, str]:
    """Check gateway health endpoint. Returns (is_healthy, detail)."""
    try:
        if HAS_REQUESTS:
            r = requests.get(GATEWAY_URL, timeout=HEALTH_TIMEOUT_SEC)
        else:
            with urllib.request.urlopen(GATEWAY_URL, timeout=HEALTH_TIMEOUT_SEC) as resp:
                body = resp.read().decode("utf-8")
                class R: pass
                r = R()
                r.status_code = resp.status
                r.text = body

        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"

        try:
            data = json.loads(r.text) if hasattr(r, "text") else json.loads(r.read().decode())
        except Exception:
            return False, f"Invalid JSON: {r.text[:200]}"

        if not data.get("ok"):
            return False, f"Status not ok: {data}"

        return True, data.get("status", "live")
    except Exception as e:
        return False, f"Exception: {type(e).__name__}: {e}"


def check_log_errors() -> tuple[bool, str]:
    """Check log file for recent FailoverError / Unknown model errors.

    Only flags errors that occurred AFTER the most recent successful gateway start.
    This prevents flagging historical errors from previous failures.
    """
    if not LOG_FILE.exists():
        return True, "log file not found (assuming OK)"

    try:
        # Read last 2000 lines (cheap enough)
        with LOG_FILE.open("r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-2000:]

        cutoff = datetime.now() - timedelta(minutes=LOG_ERROR_WINDOW_MIN)
        error_pattern = re.compile(r"FailoverError|Unknown model")

        # Find the timestamp of the most recent "gateway ready" line
        # Errors before that are historical and should be ignored
        last_ready_ts = None
        for line in lines:
            try:
                obj = json.loads(line)
                msg = obj.get("message", "")
                if "gateway ready" in msg:
                    ts_str = obj.get("time", "")
                    try:
                        last_ready_ts = datetime.fromisoformat(ts_str)
                    except Exception:
                        pass
            except json.JSONDecodeError:
                pass

        # If no ready event found, look for "starting HTTP server" or "loading configuration"
        # as a proxy for the most recent start
        if last_ready_ts is None:
            for line in lines:
                try:
                    obj = json.loads(line)
                    msg = obj.get("message", "")
                    if "starting HTTP server" in msg or "loading configuration" in msg:
                        ts_str = obj.get("time", "")
                        try:
                            last_ready_ts = datetime.fromisoformat(ts_str)
                        except Exception:
                            pass
                except json.JSONDecodeError:
                    pass

        recent_errors = []
        parsed_count = 0
        unparseable_count = 0
        for line in lines:
            try:
                obj = json.loads(line)
                msg = obj.get("message", "")
                if error_pattern.search(msg):
                    ts_str = obj.get("time", "")
                    try:
                        # 2026-06-06T20:32:06.677-04:00
                        ts = datetime.fromisoformat(ts_str)
                        parsed_count += 1
                        # Skip errors BEFORE last gateway start (historical)
                        if last_ready_ts and ts < last_ready_ts:
                            continue
                        # Skip errors OLDER than the window
                        if ts < cutoff:
                            continue
                        recent_errors.append(f"{ts_str} - {msg[:150]}")
                    except Exception:
                        unparseable_count += 1
                        # If we can't parse the timestamp AND no last_ready_ts, skip to be safe
                        if last_ready_ts is None:
                            continue
                        recent_errors.append(f"unparseable - {msg[:150]}")
            except json.JSONDecodeError:
                pass

        if recent_errors:
            return False, f"{len(recent_errors)} errors since last restart (window={LOG_ERROR_WINDOW_MIN}min): {recent_errors[0]}"

        if unparseable_count > 0 and parsed_count == 0:
            return True, f"no parseable errors (skipped {unparseable_count} unparseable)"

        return True, "no recent errors"
    except Exception as e:
        return True, f"log check failed: {e} (assuming OK)"


def check_port() -> tuple[bool, str]:
    """Check that port 18790 is listening. Returns (is_listening, detail).

    Note: Gateway may use IPv6 or have port in TIME_WAIT — try multiple methods.
    """
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command",
             f"@(Get-NetTCPConnection -State Listen -LocalPort {GATEWAY_PORT} -ErrorAction SilentlyContinue) | "
             f"Select-Object -ExpandProperty OwningProcess -First 1"],
            text=True, timeout=10
        ).strip()
        if out and out.isdigit():
            return True, f"port {GATEWAY_PORT} listening (PID {out})"
        # Fallback: try a TCP connect test
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        try:
            sock.connect((GATEWAY_HOST, GATEWAY_PORT))
            sock.close()
            return True, f"port {GATEWAY_PORT} reachable via TCP connect"
        except Exception:
            pass
        sock.close()
        return False, f"port {GATEWAY_PORT} not listening (no listener found)"
    except subprocess.TimeoutExpired:
        return False, "port check timed out"
    except Exception as e:
        return False, f"port check error: {e}"


# ============================================================================
# Recovery actions
# ============================================================================

def restart_gateway() -> tuple[bool, str]:
    """Restart the OC2 gateway via scheduled task. Returns (success, message)."""
    log("Attempting gateway restart...", "WARN")
    try:
        # Stop
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Stop-ScheduledTask -TaskName '{SCHEDULED_TASK}'"],
            capture_output=True, timeout=15
        )
        time.sleep(3)

        # Kill any leftover node process on port
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"$p = Get-NetTCPConnection -State Listen -LocalPort {GATEWAY_PORT} -ErrorAction SilentlyContinue; if ($p) {{ Stop-Process -Id $p.OwningProcess -Force }}"],
            capture_output=True, timeout=10
        )
        time.sleep(3)

        # Start
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Start-ScheduledTask -TaskName '{SCHEDULED_TASK}'"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return False, f"Start-ScheduledTask failed: {result.stderr}"

        # Wait for it to come up (gateway takes 30-90s to start)
        log(f"Waiting {STARTUP_GRACE_SEC}s for gateway to come up...", "INFO")
        time.sleep(STARTUP_GRACE_SEC)

        ok, msg = check_health()
        if ok:
            return True, f"Restart successful: {msg}"
        return False, f"Gateway still unhealthy after restart: {msg}"
    except Exception as e:
        return False, f"Restart failed: {type(e).__name__}: {e}"


def send_telegram_alert(message: str, state: dict) -> bool:
    """Send alert via Telegram bot. Throttled to once per 5 minutes."""
    now = time.time()
    last_alert = state.get("last_alert", 0)
    if now - last_alert < 300:  # 5 min cooldown
        log(f"Alert throttled (last sent {int(now - last_alert)}s ago)", "DEBUG")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🚨 OC2 Watchdog Alert\n\n{message}\n\nTime: {datetime.now().isoformat(timespec='seconds')}",
        }
        if HAS_REQUESTS:
            r = requests.post(url, json=payload, timeout=10)
        else:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                r = type("R", (), {"status_code": resp.status})()

        if r.status_code == 200:
            state["last_alert"] = now
            log(f"Telegram alert sent", "INFO")
            return True
        log(f"Telegram alert failed: HTTP {r.status_code}", "WARN")
        return False
    except Exception as e:
        log(f"Telegram alert error: {e}", "WARN")
        return False


# ============================================================================
# Main loop
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="OC2 OpenClaw gateway watchdog")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds (default: 60)")
    parser.add_argument("--auto-restart", action="store_true", help="Auto-restart on failure (default: alert only)")
    parser.add_argument("--once", action="store_true", help="Run once and exit (for testing)")
    args = parser.parse_args()

    log(f"OpenClaw Watchdog started (interval={args.interval}s, auto_restart={args.auto_restart})")
    log(f"Gateway: {GATEWAY_URL}")
    log(f"Log: {LOG_FILE}")
    log(f"State: {WATCHDOG_STATE}")

    state = load_state()

    def check_cycle() -> bool:
        """Run one check cycle. Returns True if healthy, False otherwise."""
        ok_health, health_msg = check_health()
        ok_log, log_msg = check_log_errors()
        ok_port, port_msg = check_port()

        # Skip health checks during startup grace period after restart
        now_ts = time.time()
        if state.get("startup_grace_until", 0) > now_ts:
            remaining = int(state["startup_grace_until"] - now_ts)
            log(f"⏳ Startup grace period active ({remaining}s remaining), skipping health check")
            save_state(state)
            return True

        all_ok = ok_health and ok_log and ok_port
        status_emoji = "✅" if all_ok else "❌"
        log(f"{status_emoji} health={health_msg} | log={log_msg} | port={port_msg}")

        if all_ok:
            if state["consecutive_failures"] > 0:
                log(f"Recovered after {state['consecutive_failures']} failures", "INFO")
                send_telegram_alert(
                    f"✅ OC2 Gateway RECOVERED\n"
                    f"Health: {health_msg}\n"
                    f"Previous failures: {state['consecutive_failures']}",
                    state
                )
            state["consecutive_failures"] = 0
        else:
            state["consecutive_failures"] += 1
            log(f"Failure #{state['consecutive_failures']}", "WARN")

            # Auto-restart?
            if args.auto_restart and state["consecutive_failures"] == 1:
                # Only auto-restart on first failure, then alert
                now = time.time()
                if now - state.get("last_restart", 0) > RESTART_COOLDOWN_SEC:
                    success, msg = restart_gateway()
                    if success:
                        state["last_restart"] = now
                        state["consecutive_failures"] = 0
                        state["startup_grace_until"] = now + STARTUP_GRACE_SEC
                        log(f"Startup grace period set for {STARTUP_GRACE_SEC}s", "INFO")
                        send_telegram_alert(f"✅ Auto-restart successful\n{msg}", state)
                    else:
                        send_telegram_alert(
                            f"❌ Auto-restart FAILED\n{msg}\n"
                            f"Manual intervention needed.",
                            state
                        )
                else:
                    log(f"Restart cooldown active (last restart {int(now - state['last_restart'])}s ago)", "WARN")

            # Alert on multiple failures
            if state["consecutive_failures"] >= MAX_CONSECUTIVE_FAILURES:
                send_telegram_alert(
                    f"❌ OC2 Gateway DOWN — {state['consecutive_failures']} consecutive failures\n"
                    f"Health: {health_msg}\n"
                    f"Log: {log_msg}\n"
                    f"Port: {port_msg}\n\n"
                    f"Manual fix needed. See tools/OPENCLAW-RUNBOOK.md",
                    state
                )
                # Exit after alerting on max failures (in --once mode, otherwise keep trying)
                if args.once:
                    log("Max failures reached in once-mode, exiting", "ERROR")
                    sys.exit(1)

        save_state(state)
        return all_ok

    if args.once:
        ok = check_cycle()
        sys.exit(0 if ok else 1)

    # Main loop
    while True:
        try:
            check_cycle()
        except KeyboardInterrupt:
            log("Interrupted by user, exiting")
            break
        except Exception as e:
            log(f"Unhandled exception in check cycle: {e}", "ERROR")
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
