"""Test for consensus_observer."""
from field.phase4_instrumentation.consensus_observer import ConsensusObserverModule


def test_consensus_observer_init():
    """Module initializes with default config."""
    mod = ConsensusObserverModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_consensus_observer_start_stop():
    """Module start/stop toggles running state."""
    mod = ConsensusObserverModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
