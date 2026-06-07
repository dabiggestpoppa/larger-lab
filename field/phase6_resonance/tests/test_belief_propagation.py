"""Test for belief_propagation."""
from field.phase6_resonance.belief_propagation import BeliefPropagationModule


def test_belief_propagation_init():
    """Module initializes with default config."""
    mod = BeliefPropagationModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_belief_propagation_start_stop():
    """Module start/stop toggles running state."""
    mod = BeliefPropagationModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
