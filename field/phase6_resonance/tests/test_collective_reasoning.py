"""Test for collective_reasoning."""
from field.phase6_resonance.collective_reasoning import CollectiveReasoningModule


def test_collective_reasoning_init():
    """Module initializes with default config."""
    mod = CollectiveReasoningModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_collective_reasoning_start_stop():
    """Module start/stop toggles running state."""
    mod = CollectiveReasoningModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False


def test_submit_and_query():
    """Agents can submit proposals and query results."""
    mod = CollectiveReasoningModule()
    mod.start()

    pid = mod.submit_proposal("agent-1", "Increase exploration rate", {"domain": "trading"})
    assert pid is not None

    proposals = mod.get_proposals()
    assert len(proposals) >= 1
    assert proposals[0]["proposal_id"] == pid


def test_voting():
    """Agents can vote on proposals and consensus forms."""
    mod = CollectiveReasoningModule()
    mod.start()

    pid = mod.submit_proposal("agent-1", "Switch to conservative mode")
    mod.cast_vote("agent-2", pid, "agree", weight=1.0)
    mod.cast_vote("agent-3", pid, "agree", weight=0.8)

    result = mod.get_consensus(pid)
    assert result is not None
    assert result["status"] == "consensus"
    assert result["agree_count"] == 2


def test_dissent_tracking():
    """Dissent is tracked and flagged."""
    mod = CollectiveReasoningModule()
    mod.start()

    pid = mod.submit_proposal("agent-1", "Risky move")
    mod.cast_vote("agent-2", pid, "disagree")
    mod.cast_vote("agent-3", pid, "agree")

    flags = mod.get_dissent_flags()
    # agent-2 dissented on something
    assert any(f["agent_id"] == "agent-2" for f in flags)


def test_debate_thread():
    """Debate threads track argument chains."""
    mod = CollectiveReasoningModule()
    mod.start()

    pid = mod.submit_proposal("agent-1", "Test debate")
    tid = mod.open_debate(pid, "agent-2", "I disagree because...")
    mod.reply_to_debate(tid, "agent-3", "Counter-argument")

    thread = mod.get_debate_thread(tid)
    assert thread is not None
    assert len(thread["replies"]) >= 2


def test_get_stats():
    """Stats report correct counts."""
    mod = CollectiveReasoningModule()
    mod.start()

    pid = mod.submit_proposal("agent-1", "Proposal A")
    mod.cast_vote("agent-2", pid, "agree")

    stats = mod.get_stats()
    assert stats["total_proposals"] >= 1
    assert stats["total_votes"] >= 1
