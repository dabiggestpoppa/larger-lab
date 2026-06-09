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


def test_propose_goal():
    """Proposing a goal returns a Goal with an id."""
    mod = GoalFormationModule()
    mod.start()
    goal = mod.propose_goal("increase_stability", urgency=0.8, source="test")
    assert goal.goal_id is not None
    assert goal.description == "increase_stability"
    assert goal.urgency == 0.8
    assert goal.status == "proposed"
    assert goal.source == "test"


def test_goal_lifecycle():
    """Goal can be accepted and completed."""
    mod = GoalFormationModule()
    mod.start()
    goal = mod.propose_goal("test_goal")
    gid = goal.goal_id

    accepted = mod.accept_goal(gid)
    assert accepted is not None
    assert accepted.status == "active"

    completed = mod.complete_goal(gid, success=True)
    assert completed is not None
    assert completed.status == "completed"
    assert completed.achievement_score == 1.0


def test_get_active_goals():
    """Active goals are returned ordered by priority score."""
    mod = GoalFormationModule()
    mod.start()
    mod.propose_goal("low", urgency=0.2)
    mod.propose_goal("high", urgency=0.9)
    mod.propose_goal("mid", urgency=0.5)

    active = mod.get_active_goals()
    assert len(active) == 3
    # Highest urgency should be first
    assert active[0]["urgency"] == 0.9


def test_prune_stale_goals():
    """Stale goals are pruned after max_age_rounds."""
    mod = GoalFormationModule()
    mod.start()
    goal = mod.propose_goal("stale_test")
    gid = goal.goal_id
    mod.accept_goal(gid)

    # Simulate aging
    for _ in range(105):
        mod._formation_round += 1

    pruned = mod.prune_stale_goals(max_age_rounds=100)
    assert len(pruned) >= 1
    assert pruned[0].status == "pruned"


def test_goal_progress_tracking():
    """Goal progress can be updated."""
    mod = GoalFormationModule()
    mod.start()
    goal = mod.propose_goal("progress_test")
    gid = goal.goal_id
    mod.accept_goal(gid)

    updated = mod.update_goal_progress(gid, 0.5)
    assert updated is not None
    assert updated.progress == 0.5

    updated2 = mod.update_goal_progress(gid, 1.0)
    assert updated2 is not None
    assert updated2.status == "completed"
    assert updated2.achievement_score == 1.0


def test_deprioritize_goal():
    """Goal can be deprioritized."""
    mod = GoalFormationModule()
    mod.start()
    goal = mod.propose_goal("depri_test")
    gid = goal.goal_id

    depri = mod.deprioritize_goal(gid)
    assert depri is not None
    assert depri.status == "deferred"


def test_goal_lineage():
    """Child goals are tracked in parent lineage."""
    mod = GoalFormationModule()
    mod.start()
    parent = mod.propose_goal("parent_goal")
    pid = parent.goal_id

    child = mod.propose_goal("child_goal", parent_id=pid)
    assert child.parent_id == pid

    lineage = mod.get_lineage(pid)
    assert len(lineage) >= 1


def test_formation_stats():
    """Statistics are tracked correctly."""
    mod = GoalFormationModule()
    mod.start()
    mod.propose_goal("s1")
    mod.propose_goal("s2")

    stats = mod.get_stats()
    assert stats["total_proposed"] == 2
    assert stats["active_count"] == 2
