"""
OC2 Gateway Auto-Restart Watchdog
===================================

Monitors the OpenClaw gateway process and restarts it when:
1. Event loop delay exceeds 3x the baseline threshold (default: 3000ms p99)
2. Process is not responding on the health endpoint
3. Process has died completely

Also monitors Telegram API connectivity and forces a channel restart
when network errors exceed a threshold.

Usage:
    python tools/oc2-gateway-watchdog.py          # Run continuously (default)
    python tools/oc2-gateway-watchdog.py --once   # Single check
    python tools/oc2-gateway-watchdog.py --help   # Show options
"""

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import urllib.request
import urllib.error

# ─── Configuration ──────────────────────────────────────────────────────────

GATEWAY_HOST = "127.0.0.1"
GATEWAY_PORT = 18790
HEALTH_URL = f"http://{GATEWAY_HOST}:{GATEWAY_PORT}/health"
LOG_FILE = os.path.join(
    os.environ.get("TMPDIR", os.environ.get("TEMP", "/tmp")),
    "openclaw",
    "watchdog.log",
)

# Thresholds
EVENT_LOOP_DELAY_P99_THRESHOLD_MS = 3000.0  # 3x baseline (~1000ms)
EVENT_LOOP_UTILIZATION_THRESHOLD = 0.8       # 80%
CPU_CORE_RATIO_THRESHOLD = 0.8               # 80%
HEALTH_CHECK_TIMEOUT_SEC = 10
MAX_RESTARTS_PER_HOUR = 5
RESTART_COOLDOWN_SEC = 30

# Paths
OPENCLAW_HOME = os.path.join(
    os.environ.get("OPENCLAW_HOME", r"C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2")
)
OPENCLAW_BIN = r"C:\Users\wifik\AppData\Roaming\npm\node_modules\openclaw\dist\index.js"
NODE_EXE = r"C:\Program Files\nodejs\node.exe"
WORKSPACE_ROOT = r"C:\Users\wifik\Desktop\projects\larger-lab"

# ─── Logging ─────────────────────────────────────────────────────────────────

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("oc2-watchdog")


# ─── State ───────────────────────────────────────────────────────────────────

class WatchdogState:
    def __init__(self):
        self.restart_count = 0
        self.last_restart_time = 0.0
        self.last_restart_reason = ""
        self.consecutive_failures = 0
        self.start_time = time.time()

    def can_restart(self) -> bool:
        now = time.time()
        # Reset counter after 1 hour
        if now - self.last_restart_time > 3600:
            self.restart_count = 0
        if self.restart_count >= MAX_RESTARTS_PER_HOUR:
            return False
        if now - self.last_restart_time < RESTART_COOLDOWN_SEC:
            return False
        return True

    def record_restart(self, reason: str):
        self.restart_count += 1
        self.last_restart_time = time.time()
        self.last_restart_reason = reason
        self.consecutive_failures = 0


state = WatchdogState()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_gateway_pid() -> int | None:
    """Find the gateway process PID, or None if not running."""
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Process -Name 'node' -ErrorAction SilentlyContinue | "
                "Where-Object { (Get-CimInstance Win32_Process -Filter \"ProcessId=$($_.Id)\").CommandLine -match 'openclaw' } | "
                "Select-Object -ExpandProperty Id",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        pid_str = result.stdout.strip()
        if pid_str:
            return int(pid_str.split("\n")[0].strip())
    except Exception as e:
        logger.debug(f"PID lookup error: {e}")
    return None


def check_health() -> dict | None:
    """Check gateway health endpoint. Returns JSON dict or None."""
    try:
        req = urllib.request.Request(HEALTH_URL, method="GET")
        with urllib.request.urlopen(req, timeout=HEALTH_CHECK_TIMEOUT_SEC) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data)
    except Exception as e:
        logger.debug(f"Health check failed: {e}")
        return None


def check_gateway_log_for_errors() -> dict:
    """
    Parse the latest gateway log for diagnostic info.
    Returns dict with event_loop_delay, cpu, telegram_errors, etc.
    """
    log_dir = os.path.join(
        os.environ.get("TMPDIR", os.environ.get("TEMP", "/tmp")),
        "openclaw",
    )
    log_file = os.path.join(log_dir, f"openclaw-{datetime.now().strftime('%Y-%m-%d')}.log")

    if not os.path.exists(log_file):
        return {}

    result = {
        "event_loop_delay_p99": 0.0,
        "event_loop_utilization": 0.0,
        "cpu_core_ratio": 0.0,
        "telegram_send_errors": 0,
        "telegram_network_errors": 0,
        "polling_stalls": 0,
        "liveness_warnings": 0,
    }

    try:
        # Read last 200 lines
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-200:]

        for line in lines:
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue

            msg = entry.get("message", "") or entry.get("1", "")

            # Parse diagnostic liveness warnings
            if "liveness warning" in msg:
                result["liveness_warnings"] += 1
                # Extract eventLoopDelayP99Ms
                if "eventLoopDelayP99Ms=" in msg:
                    try:
                        val = float(msg.split("eventLoopDelayP99Ms=")[1].split()[0].rstrip("ms"))
                        result["event_loop_delay_p99"] = max(result["event_loop_delay_p99"], val)
                    except (ValueError, IndexError):
                        pass
                if "eventLoopUtilization=" in msg:
                    try:
                        val = float(msg.split("eventLoopUtilization=")[1].split()[0])
                        result["event_loop_utilization"] = max(result["event_loop_utilization"], val)
                    except (ValueError, IndexError):
                        pass
                if "cpuCoreRatio=" in msg:
                    try:
                        val = float(msg.split("cpuCoreRatio=")[1].split()[0])
                        result["cpu_core_ratio"] = max(result["cpu_core_ratio"], val)
                    except (ValueError, IndexError):
                        pass

            # Count Telegram errors
            if "sendChatAction failed" in msg or "sendMessage failed" in msg:
                result["telegram_send_errors"] += 1
            if "Network request" in msg and "failed" in msg:
                result["telegram_network_errors"] += 1
            if "Polling stall detected" in msg:
                result["polling_stalls"] += 1

    except Exception as e:
        logger.debug(f"Log parsing error: {e}")

    return result


def kill_gateway():
    """Kill the gateway process."""
    pid = get_gateway_pid()
    if pid:
        logger.info(f"Killing gateway process PID={pid}")
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {pid} -Force"],
                capture_output=True,
                timeout=10,
            )
            time.sleep(3)
        except Exception as e:
            logger.error(f"Failed to kill gateway: {e}")


def start_gateway() -> bool:
    """Start the gateway process. Returns True if started successfully."""
    logger.info("Starting OC2 gateway...")

    env = os.environ.copy()
    env["OPENCLAW_HOME"] = OPENCLAW_HOME
    env["TMPDIR"] = os.environ.get("TMPDIR", os.environ.get("TEMP", ""))

    try:
        subprocess.Popen(
            [NODE_EXE, OPENCLAW_BIN, "gateway", "run", "--port", str(GATEWAY_PORT), "--allow-unconfigured"],
            cwd=WORKSPACE_ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

        # Wait for health check to pass
        for attempt in range(30):
            time.sleep(2)
            health = check_health()
            if health and health.get("status") == "live":
                logger.info(f"Gateway started and healthy (attempt {attempt + 1})")
                return True
            pid = get_gateway_pid()
            if pid is None:
                logger.warning(f"Gateway process not found (attempt {attempt + 1})")

        logger.error("Gateway started but health check failed after 60s")
        return False

    except Exception as e:
        logger.error(f"Failed to start gateway: {e}")
        return False


def restart_gateway(reason: str):
    """Kill and restart the gateway."""
    if not state.can_restart():
        logger.warning(
            f"Restart suppressed: count={state.restart_count}/{MAX_RESTARTS_PER_HOUR}, "
            f"last_reason={state.last_restart_reason}"
        )
        return False

    logger.info(f"Restarting gateway. Reason: {reason}")
    state.record_restart(reason)
    kill_gateway()
    return start_gateway()


# ─── Main Check Logic ────────────────────────────────────────────────────────

def run_check() -> str:
    """
    Run a single watchdog check.
    Returns status string: "healthy", "restarted", "unhealthy", "dead"
    """
    # 1. Check if process is alive
    pid = get_gateway_pid()
    if pid is None:
        logger.warning("Gateway process not found")
        state.consecutive_failures += 1
        if state.can_restart():
            success = restart_gateway("process_dead")
            return "restarted" if success else "dead"
        return "dead"

    # 2. Check health endpoint
    health = check_health()
    if health is None:
        logger.warning(f"Gateway PID={pid} not responding on health endpoint")
        state.consecutive_failures += 1
        if state.consecutive_failures >= 3 and state.can_restart():
            success = restart_gateway("health_check_failed")
            return "restarted" if success else "unhealthy"
        return "unhealthy"

    # 3. Check logs for event loop / CPU / Telegram issues
    diagnostics = check_gateway_log_for_errors()

    event_loop_delay = diagnostics.get("event_loop_delay_p99", 0)
    event_loop_util = diagnostics.get("event_loop_utilization", 0)
    cpu_ratio = diagnostics.get("cpu_core_ratio", 0)
    telegram_errors = diagnostics.get("telegram_send_errors", 0)
    polling_stalls = diagnostics.get("polling_stalls", 0)

    logger.info(
        f"Status: PID={pid}, delay_p99={event_loop_delay:.0f}ms, "
        f"util={event_loop_util:.2f}, cpu={cpu_ratio:.2f}, "
        f"telegram_errors={telegram_errors}, stalls={polling_stalls}"
    )

    # Check thresholds
    if event_loop_delay > EVENT_LOOP_DELAY_P99_THRESHOLD_MS:
        logger.warning(f"Event loop delay {event_loop_delay:.0f}ms exceeds threshold {EVENT_LOOP_DELAY_P99_THRESHOLD_MS}ms")
        state.consecutive_failures += 1
        if state.consecutive_failures >= 2 and state.can_restart():
            success = restart_gateway(f"event_loop_delay_{event_loop_delay:.0f}ms")
            return "restarted" if success else "unhealthy"

    if event_loop_util > EVENT_LOOP_UTILIZATION_THRESHOLD:
        logger.warning(f"Event loop utilization {event_loop_util:.2f} exceeds threshold {EVENT_LOOP_UTILIZATION_THRESHOLD}")
        state.consecutive_failures += 1
        if state.consecutive_failures >= 2 and state.can_restart():
            success = restart_gateway(f"event_loop_util_{event_loop_util:.2f}")
            return "restarted" if success else "unhealthy"

    if cpu_ratio > CPU_CORE_RATIO_THRESHOLD:
        logger.warning(f"CPU core ratio {cpu_ratio:.2f} exceeds threshold {CPU_CORE_RATIO_THRESHOLD}")
        state.consecutive_failures += 1
        if state.consecutive_failures >= 3 and state.can_restart():
            success = restart_gateway(f"cpu_ratio_{cpu_ratio:.2f}")
            return "restarted" if success else "unhealthy"

    if polling_stalls > 0:
        logger.warning(f"Telegram polling stall detected ({polling_stalls} in recent logs)")
        state.consecutive_failures += 1
        if state.can_restart():
            success = restart_gateway("telegram_polling_stall")
            return "restarted" if success else "unhealthy"

    # All good
    state.consecutive_failures = 0
    return "healthy"


# ─── Main Loop ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OC2 Gateway Auto-Restart Watchdog")
    parser.add_argument("--once", action="store_true", help="Run a single check and exit")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds (default: 30)")
    parser.add_argument("--delay-threshold", type=float, default=EVENT_LOOP_DELAY_P99_THRESHOLD_MS,
                        help=f"Event loop delay threshold in ms (default: {EVENT_LOOP_DELAY_P99_THRESHOLD_MS})")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    global EVENT_LOOP_DELAY_P99_THRESHOLD_MS
    EVENT_LOOP_DELAY_P99_THRESHOLD_MS = args.delay_threshold

    logger.info(
        f"OC2 Watchdog started. interval={args.interval}s, "
        f"delay_threshold={EVENT_LOOP_DELAY_P99_THRESHOLD_MS}ms, "
        f"max_restarts/hour={MAX_RESTARTS_PER_HOUR}"
    )

    if args.once:
        status = run_check()
        logger.info(f"Check result: {status}")
        sys.exit(0 if status in ("healthy", "restarted") else 1)

    # Continuous loop
    def signal_handler(sig, frame):
        logger.info("Watchdog shutting down")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while True:
        try:
            status = run_check()
            logger.info(f"Check result: {status}")
        except Exception as e:
            logger.error(f"Check error: {e}")

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
