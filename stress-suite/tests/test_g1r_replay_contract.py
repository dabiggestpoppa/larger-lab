"""G1R-03 / G1R-04 — replay honors supplied lifecycle/phase contract versions."""
import pytest

from engine.replay import DeterministicReplay, ReplayEvent
from engine.lifecycle import LifecycleEdgeTable, KnowledgeRecord
from engine.phase import PhaseEdgeTable
from engine.base import Provenance

V1 = LifecycleEdgeTable.default()
V2 = LifecycleEdgeTable(contract_version="2.0.0", status="v2-custom",
                        legal_edges=dict(V1.legal_edges, **{
                            # custom: allow an unusual ACTIVE->TESTED-LITE jump (differs from default)
                            "TESTED": frozenset(["PROMOTED", "CHALLENGED", "DEMOTED", "CANDIDATE", "ACTIVE"]),
                        }))


def _seed_lifecycle(state="TESTED"):
    return [KnowledgeRecord(record_id="k", claim="c",
                            provenance=Provenance(source_kind="FIXTURE", source_label="t"),
                            creation_source="t", initial_state=state)]


def _lifecycle_events():
    return [
        ReplayEvent(1, "lifecycle_step", "lifecycle", "PO", "k",
                    {"to_state": "ACTIVE", "authority_level": "PO", "reason": "x"})
    ]


# --------------------------------------------------------------------------- #
# G1R-03 — replay must use the SUPPLIED lifecycle table, not default fallback
# --------------------------------------------------------------------------- #
def test_replay_uses_supplied_lifecycle_contract():
    evs = _lifecycle_events()
    # default table: TESTED->ACTIVE is NOT legal (goes through PROMOTED)
    default = DeterministicReplay(lifecycle_table=V1, seed_records=_seed_lifecycle()).run(evs)
    assert default.trace[0]["allowed"] is False
    # custom table: TESTED->ACTIVE IS legal
    custom = DeterministicReplay(lifecycle_table=V2, seed_records=_seed_lifecycle()).run(evs)
    assert custom.trace[0]["allowed"] is True


def test_replay_custom_lifecycle_contract_changes_result():
    evs = _lifecycle_events()
    a = DeterministicReplay(lifecycle_table=V1, seed_records=_seed_lifecycle()).run(evs)
    b = DeterministicReplay(lifecycle_table=V2, seed_records=_seed_lifecycle()).run(evs)
    assert (a.trace[0]["allowed"]) != (b.trace[0]["allowed"])
    assert a.fingerprint != b.fingerprint


def test_replay_same_custom_contract_is_deterministic():
    evs = _lifecycle_events()
    a = DeterministicReplay(lifecycle_table=V2, seed_records=_seed_lifecycle()).run(evs)
    b = DeterministicReplay(lifecycle_table=V2, seed_records=_seed_lifecycle()).run(evs)
    assert a.fingerprint == b.fingerprint
    assert a.trace == b.trace


# --------------------------------------------------------------------------- #
# G1R-04 — contract_version must not be decorative
# --------------------------------------------------------------------------- #
def test_replay_rejects_phase_contract_version_mismatch():
    evs = [ReplayEvent(1, "phase_step", "phase", "SENTINEL", "@INST",
                       {"to_state": "WATCH", "evidence_vector": {}, "authority_level": "GOVERNOR",
                        "mutation_class": "READ_ONLY"},
                       contract_version="99.0.0")]
    res = DeterministicReplay().run(evs)
    assert res.trace[0]["allowed"] is False
    assert res.trace[0]["kind"] == "CONTRACT_VERSION_MISMATCH"
    assert res.terminal_phase == "STABLE"


def test_replay_rejects_lifecycle_contract_version_mismatch():
    evs = [ReplayEvent(1, "lifecycle_step", "lifecycle", "PO", "k",
                       {"to_state": "PROMOTED", "authority_level": "PO", "reason": "x"},
                       contract_version="9.9.9")]
    res = DeterministicReplay(seed_records=[KnowledgeRecord(record_id="k", claim="c",
                                                            provenance=Provenance(source_kind="FIXTURE", source_label="t"),
                                                            creation_source="t", initial_state="TESTED")]).run(evs)
    assert res.trace[0]["allowed"] is False
    assert res.trace[0]["kind"] == "CONTRACT_VERSION_MISMATCH"


def test_replay_accepts_matching_contract_version():
    evs = [ReplayEvent(1, "phase_step", "phase", "SENTINEL", "@INST",
                       {"to_state": "WATCH", "evidence_vector": {}, "authority_level": "GOVERNOR",
                        "mutation_class": "READ_ONLY"},
                       contract_version=PhaseEdgeTable.default().contract_version)]
    res = DeterministicReplay().run(evs)
    assert res.trace[0]["allowed"] is True
    assert res.terminal_phase == "WATCH"


def test_replay_blank_contract_version_policy_is_explicit():
    # blank version uses the active contract (smoke-fixture policy)
    evs = _lifecycle_events()
    res = DeterministicReplay(lifecycle_table=V1, seed_records=_seed_lifecycle()).run(evs)
    # blank -> active V1 governs: TESTED->ACTIVE is denied
    assert res.trace[0]["allowed"] is False
    # document that blank == "use active contract" is the smoking/generic policy
    assert True