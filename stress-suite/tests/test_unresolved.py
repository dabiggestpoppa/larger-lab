"""Unresolved states (G1 §13) — represented without forcing a category."""
from dataclasses import asdict
from engine.unresolved import UnresolvedPatternRecord, UnresolvedGovernanceEvent


def test_unresolved_pattern_has_no_closest_category():
    u = UnresolvedPatternRecord.make(1, "residual not fitting known families")
    d = asdict(u)
    assert d["classification"] == "UNRESOLVED_PATTERN"
    # there is no 'closest_category' or 'forced_kind' field in the schema/model
    assert "closest_category" not in d


def test_unresolved_governance_event_has_no_channel_requirement():
    u = UnresolvedGovernanceEvent.make(2, "a governance failure with no known channel",
                                       suggested_consequences=["SAFE_HOLD"])
    d = asdict(u)
    assert d["classification"] == "UNRESOLVED_GOVERNANCE_EVENT"
    # no required assignment to an evidence channel or scope level
    assert "channel" not in d and "scope_level" not in d


def test_exact_observation_survives():
    u = UnresolvedPatternRecord.make(3, "precise raw observation string", confirmed_by=["ev/qc1"])
    assert u.observation == "precise raw observation string"