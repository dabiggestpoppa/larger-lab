"""Fix deadlock in continuity_memory.py."""
path = r"C:\Users\wifik\Desktop\projects\larger-lab\core\observer\continuity_memory.py"
content = open(path).read()

# Fix 1: Use RLock instead of Lock
old_lock = "        self._lock = threading.Lock()"
new_lock = "        self._lock = threading.RLock()"
content = content.replace(old_lock, new_lock)
print("Fixed: RLock")

# Fix 2: Fix _persist to not call to_dict while holding lock
old_persist = """    def _persist(self) -> None:
        try:
            MEMORY_FILE.write_text(json.dumps(self.to_dict(), indent=2))
        except Exception:
            pass"""
new_persist = """    def _persist(self) -> None:
        try:
            data = {
                "session_id": self._record.session_id,
                "start_time": self._record.start_time,
                "last_active": self._record.last_active,
                "workflow_count": self._record.workflow_count,
                "success_count": self._record.success_count,
                "failure_count": self._record.failure_count,
                "active_goals": list(self._record.active_goals),
                "workflow_history": list(self._record.workflow_history[-50:]),
                "routing_patterns": dict(self._record.routing_patterns),
            }
            MEMORY_DIR.mkdir(parents=True, exist_ok=True)
            MEMORY_FILE.write_text(json.dumps(data, indent=2))
        except Exception:
            pass"""
content = content.replace(old_persist, new_persist)
print("Fixed: _persist")

open(path, "w").write(content)
print("Done")
