"""
Phase 3: Autonomous Presence Engine
====================================
- Watcher Network: monitors subsystems continuously
- Priority Evaluator: filters events to prevent spam
- Autonomous Push: proactive communication
- Continuity Cache: persistent context with TTL
- Timeline Engine: operational history
"""
import os, sys, time, json, threading, datetime
from collections import deque
from typing import Any, Callable, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── Priority Evaluator ─────────────────────────────────────────────────

class PriorityEvaluator:
    """Filters events to prevent notification spam."""

    CRITICAL = {"task_failed", "observer_degraded", "spawn_failed", "continuity_lost", "service_down"}
    HIGH = {"task_completed", "agent_spawned", "repair_triggered", "drift_detected"}
    MEDIUM = {"task_started", "sync_complete", "backup_complete"}
    LOW = {"heartbeat", "poll", "scan"}

    def __init__(self, cooldown=30):
        self._last_push = {}
        self._cooldown = cooldown  # seconds between pushes per category

    def should_push(self, event_type: str, key: str = "default") -> bool:
        """Determine if an event should trigger a push notification."""
        now = time.time()
        cache_key = f"{event_type}:{key}"

        # Critical always pushes
        if event_type in self.CRITICAL:
            self._last_push[cache_key] = now
            return True

        # High/Medium respect cooldown
        if event_type in self.HIGH or event_type in self.MEDIUM:
            last = self._last_push.get(cache_key, 0)
            if now - last < self._cooldown:
                return False
            self._last_push[cache_key] = now
            return True

        # Low never pushes
        return False

    def summary(self) -> str:
        return f"Priority filter: {len(self._last_push)} events tracked, {self._cooldown}s cooldown"


PRIORITY = PriorityEvaluator(cooldown=30)


# ─── Continuity Cache ──────────────────────────────────────────────────

class ContinuityCache:
    """Persistent context with rolling window and TTL."""

    def __init__(self, max_items=100, ttl=86400):
        self._cache = deque(maxlen=max_items)
        self._ttl = ttl
        self._lock = threading.Lock()

    def add(self, key: str, value: Any):
        with self._lock:
            self._cache.append({
                "key": key,
                "value": value,
                "ts": time.time()
            })

    def get_recent(self, count=10) -> List[Dict]:
        with self._lock:
            now = time.time()
            items = [i for i in self._cache if now - i["ts"] < self._ttl]
            return list(items)[-count:]

    def get_summary(self) -> str:
        items = self.get_recent(5)
        if not items:
            return "No recent context."
        lines = []
        for item in items:
            ts = datetime.datetime.fromtimestamp(item["ts"]).strftime("%H:%M")
            val = str(item["value"])[:80]
            lines.append(f"  [{ts}] {item['key']}: {val}")
        return "\n".join(lines)

    def clear(self):
        with self._lock:
            self._cache.clear()


CONTINUITY = ContinuityCache(max_items=100, ttl=86400)


# ─── Timeline Engine ───────────────────────────────────────────────────

class TimelineEngine:
    """Operational history — what happened while user was gone."""

    def __init__(self, max_events=200):
        self._events = deque(maxlen=max_events)
        self._lock = threading.Lock()

    def record(self, event_type: str, data: Dict = None):
        with self._lock:
            self._events.append({
                "type": event_type,
                "data": data or {},
                "ts": time.time()
            })

    def get_since(self, timestamp: float) -> List[Dict]:
        with self._lock:
            return [e for e in self._events if e["ts"] > timestamp]

    def get_summary(self, count=15) -> str:
        with self._lock:
            events = list(self._events)[-count:]
        if not events:
            return "No events recorded."
        lines = []
        for e in events:
            ts = datetime.datetime.fromtimestamp(e["ts"]).strftime("%H:%M")
            etype = e["type"]
            data_str = str(e.get("data", ""))[:60]
            lines.append(f"  [{ts}] {etype} {data_str}")
        return "\n".join(lines)

    def get_gone_summary(self, hours: int = 24) -> str:
        """Summary of what happened in the last N hours."""
        since = time.time() - (hours * 3600)
        events = self.get_since(since)
        if not events:
            return f"No events in the last {hours} hours."

        by_type = {}
        for e in events:
            t = e["type"]
            by_type[t] = by_type.get(t, 0) + 1

        lines = [f"📅 Last {hours}h: {len(events)} events", ""]
        for t, count in sorted(by_type.items(), key=lambda x: -x[1]):
            lines.append(f"  • {t}: {count}")
        return "\n".join(lines)


TIMELINE = TimelineEngine()


# ─── Watcher Network ───────────────────────────────────────────────────

class Watcher:
    """Single watcher — monitors a subsystem."""

    def __init__(self, name: str, interval: int, check_fn: Callable, on_change: Callable = None):
        self.name = name
        self.interval = interval
        self.check_fn = check_fn
        self.on_change = on_change
        self._last_value = None
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        while self._running:
            try:
                value = self.check_fn()
                if self._last_value is not None and value != self._last_value:
                    if self.on_change:
                        self.on_change(self.name, self._last_value, value)
                self._last_value = value
            except Exception:
                pass
            time.sleep(self.interval)


class WatcherNetwork:
    """Manages all watchers."""

    def __init__(self):
        self._watchers: Dict[str, Watcher] = {}

    def add(self, name: str, interval: int, check_fn: Callable, on_change: Callable = None):
        w = Watcher(name, interval, check_fn, on_change)
        self._watchers[name] = w

    def start_all(self):
        for w in self._watchers.values():
            w.start()

    def stop_all(self):
        for w in self._watchers.values():
            w.stop()

    def status(self) -> str:
        lines = ["👁️ Watcher Network", ""]
        for name, w in self._watchers.items():
            icon = "🟢" if w._running else "🔴"
            lines.append(f"  {icon} {name} — every {w.interval}s")
        return "\n".join(lines)


# ─── Change Handlers ───────────────────────────────────────────────────

def on_vault_change(name, old, new):
    TIMELINE.record("vault_change", {"old": str(old)[:50], "new": str(new)[:50]})
    CONTINUITY.add("vault_state", new)
    if PRIORITY.should_push("vault_change"):
        log(f"[PUSH] Vault changed: {str(new)[:50]}")


def on_progress_change(name, old, new):
    TIMELINE.record("progress_change", {"old": str(old)[:50], "new": str(new)[:50]})
    CONTINUITY.add("progress_state", new)


def on_health_change(name, old, new):
    TIMELINE.record("health_change", {"old": str(old)[:50], "new": str(new)[:50]})
    if new != "healthy" and PRIORITY.should_push("service_down", key=name):
        log(f"[PUSH] Service down: {name}")


# ─── Check Functions ───────────────────────────────────────────────────

def check_vault():
    try:
        from core.observer.vault import Vault
        v = Vault()
        count = sum(1 for _, _, files in os.walk(v.path) for f in files if f.endswith(".md"))
        return f"vault:{count}"
    except:
        return "vault:error"


def check_progress():
    try:
        pd = os.path.join(os.getcwd(), "progress")
        if os.path.exists(pd):
            files = sorted(os.listdir(pd), key=lambda f: os.path.getmtime(os.path.join(pd, f)), reverse=True)
            if files:
                return f"progress:{files[0]}"
        return "progress:empty"
    except:
        return "progress:error"


def check_health():
    try:
        import socket
        ports = [8000, 8765, 8770]
        for p in ports:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            try:
                s.connect(("127.0.0.1", p))
                s.close()
            except:
                return f"down:{p}"
        return "healthy"
    except:
        return "error"


# ─── Build Network ─────────────────────────────────────────────────────

WATCHERS = WatcherNetwork()
WATCHERS.add("vault-watcher", 60, check_vault, on_vault_change)
WATCHERS.add("progress-watcher", 120, check_progress, on_progress_change)
WATCHERS.add("health-watcher", 30, check_health, on_health_change)


# ─── Main ───────────────────────────────────────────────────────────────

def start_presence_engine():
    """Start all watchers and presence systems."""
    WATCHERS.start_all()
    log("[Presence] Engine started — watchers active")


def stop_presence_engine():
    """Stop all watchers."""
    WATCHERS.stop_all()
    log("[Presence] Engine stopped")


if __name__ == "__main__":
    log("Testing presence engine...")
    start_presence_engine()
    time.sleep(5)
    log(TIMELINE.get_summary())
    log(WATCHERS.status())
