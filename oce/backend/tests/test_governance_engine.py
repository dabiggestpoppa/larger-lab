"""
Tests for OCE Governance Engine — OCE-8.5a
============================================
17 tests covering proposal lifecycle, sovereignty boundaries,
MAD override, and governance log.
"""

import pytest


@pytest.fixture(autouse=True)
def reset_governance(tmp_path):
    """Reset the GovernanceEngine singleton before each test."""
    from governance_engine import GovernanceEngine
    import governance_engine
    original_path = governance_engine.DB_PATH
    test_db = str(tmp_path / "test_governance.db")
    governance_engine.DB_PATH = test_db
    GovernanceEngine._instance = None
    yield
    GovernanceEngine._instance = None
    governance_engine.DB_PATH = original_path


class TestGovernanceEngineInit:
    def test_singleton_identity(self):
        from governance_engine import get_governance_engine
        g1 = get_governance_engine()
        g2 = get_governance_engine()
        assert g1 is g2

    def test_initial_sovereignty_report(self):
        from governance_engine import get_governance_engine
        g = get_governance_engine()
        report = g.get_sovereignty_report()
        assert report["total_boundaries"] > 0
        assert "immutable_boundaries" in report


class TestProposalLifecycle:
    def test_propose_policy_change(self):
        from governance_engine import get_governance_engine
        g = get_governance_engine()
        pid = g.propose_policy_change(
            proposal_type="policy_change",
            title="Test Proposal",
            description="A test",
            changes={"max_workers": 4},
            reason="Testing",
        )
        assert pid is not None
        assert len(pid) > 0

    def test_get_proposal(self):
        from governance_engine import get_governance_engine
        g = get_governance_engine()
        pid = g.propose_policy_change(
            proposal_type="policy_change",
            title="Test",
            description="Test",
            changes={"max_workers": 4},
            reason="Test",
        )
        proposal = g.get_proposal_status(pid)
        assert proposal is not None

    def test_approve_proposal(self):
        from governance_engine import get_governance_engine
        g = get_governance_engine()
        pid = g.propose_policy_change(
            proposal_type="policy_change",
            title="Test",
            description="Test",
            changes={"max_workers": 4},
            reason="Test",
        )
        result = g.approve_proposal(pid, "MAD")
        assert result is True

    def test_reject_proposal(self):
        from governance_engine import get_governance_engine
        g = get_governance_engine()
        pid = g.propose_policy_change(
            proposal_type="policy_change",
            title="Test",
            description="Test",
            changes={"max_workers": 4},
            reason="Test",
        )
        g.reject_proposal(pid, "MAD", "Not needed")
        proposal = g.get_proposal(pid)
        assert proposal["status"] == "rejected"

    def test_list_proposals(self):
        from governance_engine import get_governance_engine
        g = get_governance_engine()
        g.propose_policy_change(
            proposal_type="policy_change",
            title="Test",
            description="Test",
            changes={"max_workers": 4},
            reason="Test",
        )
        proposals = g.list_proposals()
        assert len(proposals) >= 1

    def test_list_proposals_by_status(self):
        from governance_engine import get_governance_engine
        g = get_governance_engine()
        pid = g.propose_policy_change(
            proposal_type="policy_change",
            title="Test",
            description="Test",
            changes={"max_workers": 4},
            reason="Test",
        )
        g.approve_proposal(pid, "MAD")
        approved = g.list_proposals(status="approved")
        assert len(approved) >= 1


class TestSovereigntyBoundaries:
    def test_cannot_modify_sovereignty_boundary(self):
        from governance_engine import get_governance_engine
        g = get_governance_engine()
        with pytest.raises(ValueError):
            g.propose_policy_change(
                proposal_type="sovereignty_boundary",
                title="Bad",
                description="Test",
                changes={"mad_override_enabled": False},
                reason="Test",
            )

    def test_cannot_exceed_max_boundary(self):
        from governance_engine import get_governance_engine
        g = get_governance_engine()
        with pytest.raises(ValueError, match="exceeds maximum"):
            g.propose_policy_change(
                proposal_type="policy_change",
                title="Bad",
                description="Test",
                changes={"max_workers": 999},
                reason="Test",
            )

    def test_cannot_go_below_min_boundary(self):
        from governance_engine import get_governance_engine
        g = get_governance_engine()
        with pytest.raises(ValueError, match="below minimum"):
            g.propose_policy_change(
                proposal_type="policy_change",
                title="Bad",
                description="Test",
                changes={"max_workers": 0},
                reason="Test",
            )

    def test_immutable_boundary(self):
        from governance_engine import get_governance_engine
        g = get_governance_engine()
        with pytest.raises(ValueError, match="immutable"):
            g.propose_policy_change(
                proposal_type="sovereignty_boundary",
                title="Bad",
                description="Test",
                changes={"mad_override_enabled": False},
                reason="Test",
            )

    def test_valid_change_within_boundaries(self):
        from governance_engine import get_governance_engine
        g = get_governance_engine()
        pid = g.propose_policy_change(
            proposal_type="policy_change",
            title="Good",
            description="Test",
            changes={"max_workers": 8},
            reason="Test",
        )
        assert pid is not None

    def test_sovereignty_report(self):
        from governance_engine import get_governance_engine
        g = get_governance_engine()
        report = g.get_sovereignty_report()
        assert "boundaries" in report
        assert "total_boundaries" in report
        assert "immutable_boundaries" in report
        assert "mad_override_enabled" in report["immutable_boundaries"]


class TestMADOverride:
    def test_override_autonomous_decision(self):
        from governance_engine import get_governance_engine
        g = get_governance_engine()
        g.override_autonomous_decision(
            decision_id="test-decision-123",
            reason="Testing override",
            mad_id="MAD",
        )
        log = g.get_governance_log()
        assert len(log) >= 1

    def test_governance_log(self):
        from governance_engine import get_governance_engine
        g = get_governance_engine()
        g.propose_policy_change(
            proposal_type="policy_change",
            title="Test",
            description="Test",
            changes={"max_workers": 4},
            reason="Test",
        )
        log = g.get_governance_log()
        assert len(log) >= 1


class TestSingleton:
    def test_singleton_identity(self):
        from governance_engine import get_governance_engine
        g1 = get_governance_engine()
        g2 = get_governance_engine()
        assert g1 is g2
