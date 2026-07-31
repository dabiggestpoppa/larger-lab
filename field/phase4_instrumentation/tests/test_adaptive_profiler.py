"""Test for adaptive_profiler."""
from field.phase4_instrumentation.adaptive_profiler import AdaptiveProfilerModule


def test_adaptive_profiler_init():
    """Module initializes with default config."""
    mod = AdaptiveProfilerModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_adaptive_profiler_start_stop():
    """Module start/stop toggles running state."""
    mod = AdaptiveProfilerModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
