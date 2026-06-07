"""Test for goal_formation."""
from field.phase9_emergence.goal_formation import GoalFormationModule


def test_goal_formation_init():
    """Module initializes with default config."""
    mod = GoalFormationModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_goal_formation_start_stop():
    """Module start/stop toggles running state."""
    mod = GoalFormationModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
