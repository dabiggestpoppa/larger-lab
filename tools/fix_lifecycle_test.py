"""Fix lifecycle test to not hang."""
path = r"C:\Users\wifik\Desktop\projects\larger-lab\tests\test_observer\test_o1_primary_observer.py"
content = open(path).read()

# Replace the lifecycle test class
old = '''class TestObserverLifecycle:
    """Heartbeat, healthcheck, recovery."""

    def setup_method(self):
        from core.observer.observer_lifecycle import ObserverLifecycle
        from core.observer import observer_state
        observer_state.ObserverState._instance = None
        self.lifecycle = ObserverLifecycle(
            heartbeat_interval=0.1,
            healthcheck_interval=0.2,
        )

    def test_start_stop(self):
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

new = '''class TestObserverLifecycle:
    """Heartbeat, healthcheck, recovery."""

    def setup_method(self):
        from core.observer.observer_lifecycle import ObserverLifecycle
        self.lifecycle = ObserverLifecycle(
            heartbeat_interval=0.05,
            healthcheck_interval=0.1,
        )

    def teardown_method(self):
        if self.lifecycle.is_running:
            self.lifecycle.stop()

    def test_start_stop(self):
        self.lifecycle.start()
        assert self.lifecycle.is_running is True
        time.sleep(0.2)
        assert self.lifecycle.heartbeat_count >= 1
        self.lifecycle.stop()
        assert self.lifecycle.is_running is False

    def test_health_status(self):
        from core.observer.observer_state import HealthStatus
        status = self.lifecycle.get_status()
        assert status["running"] is False
        self.lifecycle.start()
        time.sleep(0.15)
        status = self.lifecycle.get_status()
        assert status["health"] == HealthStatus.HEALTHY.value
        self.lifecycle.stop()'''

if old in content:
    content = content.replace(old, new)
    print("Fixed lifecycle test")
else:
    print("Pattern not found")

open(path, "w").write(content)
print("Done")
