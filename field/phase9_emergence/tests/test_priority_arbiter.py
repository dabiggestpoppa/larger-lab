"""Test for priority_arbiter."""
from field.phase9_emergence.priority_arbiter import PriorityArbiterModule


def test_priority_arbiter_init():
    """Module initializes with default config."""
    mod = PriorityArbiterModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_priority_arbiter_start_stop():
    """Module start/stop toggles running state."""
    mod = PriorityArbiterModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False


def test_submit_and_resolve():
    """Submit items and resolve returns highest priority first."""
    mod = PriorityArbiterModule()
    mod.start()
    mod.submit_item("task_a", priority=3, category="maintenance")
    mod.submit_item("task_b", priority=9, category="critical")
    mod.submit_item("task_c", priority=5, category="routine")

    result = mod.resolve_next()
    assert result is not None
    assert result["item_id"] == "task_b"
    assert result["priority"] == 9

    result2 = mod.resolve_next()
    assert result2["item_id"] == "task_c"

    result3 = mod.resolve_next()
    assert result3["item_id"] == "task_a"


def test_resolve_empty():
    """Resolve returns None when queue is empty."""
    mod = PriorityArbiterModule()
    mod.start()
    assert mod.resolve_next() is None


def test_urgency_boost():
    """Urgency boost increases effective priority."""
    mod = PriorityArbiterModule()
    mod.start()
    mod.submit_item("normal", priority=5, category="routine")
    mod.submit_item("urgent", priority=5, category="routine", urgency=1.0)

    result = mod.resolve_next()
    assert result["item_id"] == "urgent"


def test_category_boost():
    """Category boost affects resolution order."""
    mod = PriorityArbiterModule()
    mod.start()
    mod.set_category_boost("critical", 1.5)
    mod.submit_item("routine_high", priority=8, category="routine")
    mod.submit_item("critical_low", priority=5, category="critical")

    result = mod.resolve_next()
    # critical_low with boost: 5 * 1.5 = 7.5, routine_high: 8 * 1.0 = 8
    # routine_high should still win (8 > 7.5)
    assert result["item_id"] == "routine_high"


def test_queue_depth():
    """Queue depth tracks submitted vs resolved."""
    mod = PriorityArbiterModule()
    mod.start()
    mod.submit_item("a", priority=1, category="test")
    mod.submit_item("b", priority=2, category="test")
    mod.submit_item("c", priority=3, category="test")

    depth = mod.get_queue_depth()
    assert depth["queued"] == 3
    assert depth["resolved"] == 0

    mod.resolve_next()
    depth = mod.get_queue_depth()
    assert depth["queued"] == 2
    assert depth["resolved"] == 1


def test_duplicate_item_id():
    """Duplicate item_id updates existing item."""
    mod = PriorityArbiterModule()
    mod.start()
    mod.submit_item("same_id", priority=3, category="test")
    mod.submit_item("same_id", priority=9, category="test")

    depth = mod.get_queue_depth()
    assert depth["queued"] == 1

    result = mod.resolve_next()
    assert result["priority"] == 9
