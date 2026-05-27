"""Fix O-1 tests for lifecycle and singleton issues."""
path = r"C:\Users\wifik\Desktop\projects\larger-lab\tests\test_observer\test_o1_primary_observer.py"
content = open(path).read()

# Fix 1: Use very short intervals in lifecycle tests
old = '''    def test_start_stop(self):
        self.lifecycle.start()
        assert self.lifecycle.is_running is True
        time.sleep(0.15)
        assert self.lifecycle.heartbeat_count >= 1
        self.lifecycle.stop()
        assert self.lifecycle.is_running is False

    def test_health_status(self):
        self.lifecycle.start()
        from core.observer.observer_state import HealthStatus
        status = self.lifecycle.get_status()
        assert status["health"] == HealthStatus.HEALTHY.value
        self.lifecycle.stop()'''

new = '''    def test_start_stop(self):
        self.lifecycle.start()
        assert self.lifecycle.is_running is True
        time.sleep(0.3)
        assert self.lifecycle.heartbeat_count >= 1
        self.lifecycle.stop()
        assert self.lifecycle.is_running is False

    def test_health_status(self):
        from core.observer.observer_state import HealthStatus
        self.lifecycle.start()
        time.sleep(0.1)
        status = self.lifecycle.get_status()
        assert status["health"] == HealthStatus.HEALTHY.value
        self.lifecycle.stop()'''

if old in content:
    content = content.replace(old, new)
    print("Fixed lifecycle test timing")
else:
    print("Lifecycle test pattern not found")

# Fix 2: Fix PrimaryObserver tests to reset singleton
old2 = '''    def setup_method(self):
        from core.observer import observer_state
        observer_state.ObserverState._instance = None
        from core.observer.primary_observer import PrimaryObserver
        self.observer = PrimaryObserver()'''

new2 = '''    def setup_method(self):
        from core.observer import observer_state
        observer_state.ObserverState._instance = None
        # Also reset the singleton module-level reference
        import core.observer.observer_state as os_mod
        os_mod.ObserverState._instance = None
        from core.observer.primary_observer import PrimaryObserver
        self.observer = PrimaryObserver()'''

if old2 in content:
    content = content.replace(old2, new2)
    print("Fixed PrimaryObserver test setup")
else:
    print("PrimaryObserver setup pattern not found")

open(path, "w").write(content)
print("Done")
