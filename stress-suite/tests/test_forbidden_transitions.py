"""Consolidated forbidden-transition rules (G1 §10)."""
from engine.forbidden import ForbiddenTransitionValidator as F


def test_rule01_stable_to_new_stable():
    r = F.stable_to_new_stable("STABLE", "NEW_STABLE", review_path_completed=False)
    assert r.violation
    assert F.stable_to_new_stable("STABLE", "NEW_STABLE", review_path_completed=True).violation is False


def test_rule02_watch_to_architecture():
    assert F.watch_to_architecture_mutation("WATCH", "ARCHITECTURE_MUTATION").violation
    assert F.watch_to_architecture_mutation("WATCH", "HOMEOSTATIC_REPAIR").violation is False


def test_rule03_window_to_capital():
    assert F.window_to_capital("TRANSFORMATION_WINDOW", "CAPITAL_MUTATION").violation
    assert F.window_to_capital("TRANSFORMATION_WINDOW", "READ_ONLY").violation is False


def test_rule04_unresolved_to_ontology():
    assert F.unresolved_to_ontology("UNRESOLVED_PATTERN", evidence_sufficient=False, admissible=False).violation
    assert F.unresolved_to_ontology("UNRESOLVED_PATTERN", evidence_sufficient=True, admissible=True).violation is False


def test_rule05_confidence_not_confirmation():
    assert F.agent_confidence_to_confirmation("AGENT_CLAIM", "INDEPENDENT_CONFIRMATION").violation
    assert F.agent_confidence_to_confirmation("AGENT_CLAIM", "AGENT_CLAIM").violation is False


def test_rule06_capability_not_authority():
    assert F.capability_to_authority(capability_gain=True, authority_gain=True).violation
    assert F.capability_to_authority(capability_gain=True, authority_gain=False).violation is False


def test_rule07_provenance_preserved():
    assert F.provenance_deletion(provenance_preserved=True).violation is False
    assert F.provenance_deletion(provenance_preserved=False).violation


def test_rule08_midwindow_contract_frozen():
    assert F.midwindow_contract_mutation(contract_frozen=True, proposed_change=True).violation
    assert F.midwindow_contract_mutation(contract_frozen=True, proposed_change=False).violation is False


def test_rule09_runtime_replacement_keeps_epoch():
    assert F.runtime_replacement_loses_epoch(canonical_epoch_preserved=False).violation
    assert F.runtime_replacement_loses_epoch(canonical_epoch_preserved=True).violation is False


def test_rule10_dormant_to_active():
    assert F.dormant_to_active("DORMANT", "ACTIVE").violation
    assert F.dormant_to_active("DORMANT", "REACTIVATED").violation is False