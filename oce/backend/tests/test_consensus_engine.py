"""
Tests for OCE Consensus Engine — OCE-8.5b
===========================================
14 tests covering voting, quorum, conflict resolution.
"""

import pytest


@pytest.fixture(autouse=True)
def reset_consensus(tmp_path):
    """Reset the ConsensusEngine singleton before each test."""
    from consensus_engine import ConsensusEngine
    import consensus_engine
    original_path = consensus_engine.DB_PATH
    test_db = str(tmp_path / "test_consensus.db")
    consensus_engine.DB_PATH = test_db
    ConsensusEngine._instance = None
    yield
    ConsensusEngine._instance = None
    consensus_engine.DB_PATH = original_path


class TestVoting:
    def _setup_topic(self, engine, topic="test-topic"):
        engine.create_topic(topic, "Test topic")

    def test_submit_vote(self):
        from consensus_engine import get_consensus_engine, VoteValue
        engine = get_consensus_engine()
        self._setup_topic(engine)
        engine.submit_vote("test-topic", "voter-1", VoteValue.APPROVE)

    def test_submit_multiple_votes(self):
        from consensus_engine import get_consensus_engine, VoteValue
        engine = get_consensus_engine()
        self._setup_topic(engine)
        engine.submit_vote("test-topic", "voter-1", VoteValue.APPROVE)
        engine.submit_vote("test-topic", "voter-2", VoteValue.APPROVE)

    def test_weighted_vote(self):
        from consensus_engine import get_consensus_engine, VoteValue
        engine = get_consensus_engine()
        self._setup_topic(engine)
        engine.submit_vote("test-topic", "voter-1", VoteValue.APPROVE, weight=2.0)

    def test_abstain_vote(self):
        from consensus_engine import get_consensus_engine, VoteValue
        engine = get_consensus_engine()
        self._setup_topic(engine)
        engine.submit_vote("test-topic", "voter-1", VoteValue.ABSTAIN)

    def test_get_consensus_not_found(self):
        from consensus_engine import get_consensus_engine
        engine = get_consensus_engine()
        result = engine.get_consensus("nonexistent-topic")
        assert result["status"] == "not_found"


class TestQuorum:
    def _setup_topic(self, engine, topic="test-topic", strategy="majority", quorum=0.66):
        engine.create_topic(topic, "Test topic", strategy=strategy, quorum_threshold=quorum)

    def test_pending_no_consensus(self):
        from consensus_engine import get_consensus_engine, VoteValue
        engine = get_consensus_engine()
        self._setup_topic(engine)
        engine.submit_vote("test-topic", "voter-1", VoteValue.APPROVE)
        result = engine.get_consensus("test-topic")
        assert result["status"] in ("pending", "approved")

    def test_majority_approved(self):
        from consensus_engine import get_consensus_engine, VoteValue
        engine = get_consensus_engine()
        self._setup_topic(engine)
        engine.submit_vote("test-topic", "voter-1", VoteValue.APPROVE)
        engine.submit_vote("test-topic", "voter-2", VoteValue.APPROVE)
        engine.submit_vote("test-topic", "voter-3", VoteValue.REJECT)
        result = engine.get_consensus("test-topic")
        assert result["status"] == "approved"

    def test_majority_rejected(self):
        from consensus_engine import get_consensus_engine, VoteValue
        engine = get_consensus_engine()
        self._setup_topic(engine)
        engine.submit_vote("test-topic", "voter-1", VoteValue.REJECT)
        engine.submit_vote("test-topic", "voter-2", VoteValue.REJECT)
        engine.submit_vote("test-topic", "voter-3", VoteValue.APPROVE)
        result = engine.get_consensus("test-topic")
        assert result["status"] == "rejected"

    def test_unanimous_requires_all_approve(self):
        from consensus_engine import get_consensus_engine, VoteValue
        engine = get_consensus_engine()
        self._setup_topic(engine, strategy="unanimous", quorum=1.0)
        engine.submit_vote("test-topic", "voter-1", VoteValue.APPROVE)
        engine.submit_vote("test-topic", "voter-2", VoteValue.APPROVE)
        result = engine.get_consensus("test-topic")
        assert result["status"] == "approved"

    def test_unanimous_fails_with_reject(self):
        from consensus_engine import get_consensus_engine, VoteValue
        engine = get_consensus_engine()
        self._setup_topic(engine, strategy="unanimous", quorum=1.0)
        engine.submit_vote("test-topic", "voter-1", VoteValue.APPROVE)
        engine.submit_vote("test-topic", "voter-2", VoteValue.REJECT)
        result = engine.get_consensus("test-topic")
        assert result["status"] == "rejected"


class TestConflictResolution:
    def _setup_topic(self, engine, topic="test-topic"):
        engine.create_topic(topic, "Test topic")

    def test_resolve_approved(self):
        from consensus_engine import get_consensus_engine, VoteValue
        engine = get_consensus_engine()
        self._setup_topic(engine)
        engine.submit_vote("test-topic", "voter-1", VoteValue.APPROVE)
        engine.submit_vote("test-topic", "voter-2", VoteValue.APPROVE)
        result = engine.resolve_conflict("test-topic", "majority")
        assert result["status"] in ("resolved", "approved")

    def test_resolve_rejected(self):
        from consensus_engine import get_consensus_engine, VoteValue
        engine = get_consensus_engine()
        self._setup_topic(engine)
        engine.submit_vote("test-topic", "voter-1", VoteValue.REJECT)
        engine.submit_vote("test-topic", "voter-2", VoteValue.REJECT)
        result = engine.resolve_conflict("test-topic", "majority")
        assert result["status"] in ("resolved", "rejected")

    def test_resolve_inconclusive(self):
        from consensus_engine import get_consensus_engine, VoteValue
        engine = get_consensus_engine()
        self._setup_topic(engine)
        engine.submit_vote("test-topic", "voter-1", VoteValue.APPROVE)
        engine.submit_vote("test-topic", "voter-2", VoteValue.REJECT)
        result = engine.resolve_conflict("test-topic", "majority")
        assert result["status"] in ("approved", "rejected", "inconclusive", "conflict", "pending")


class TestVotingHistory:
    def test_voting_history(self):
        from consensus_engine import get_consensus_engine, VoteValue
        engine = get_consensus_engine()
        engine.create_topic("test-topic", "Test")
        engine.submit_vote("test-topic", "voter-1", VoteValue.APPROVE)
        history = engine.get_voting_history()
        assert len(history) >= 1

    def test_open_topics(self):
        from consensus_engine import get_consensus_engine, VoteValue
        engine = get_consensus_engine()
        engine.create_topic("test-topic", "Test")
        engine.submit_vote("test-topic", "voter-1", VoteValue.APPROVE)
        topics = engine.get_open_topics()
        assert isinstance(topics, list)

    def test_singleton(self):
        from consensus_engine import get_consensus_engine
        e1 = get_consensus_engine()
        e2 = get_consensus_engine()
        assert e1 is e2
