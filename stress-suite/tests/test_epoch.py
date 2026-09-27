"""EpochManifest (G1 §14 / AMB-12) — serialization/reconstruction round-trip."""
from engine.epoch import EpochManifest


def test_roundtrip_preserves_all_fields():
    e = EpochManifest.make(seq=1, epoch_id="E17", start_cause="post-window reconsolidation",
                           predecessor_epoch="E16",
                           governing_architecture_versions=["const-1.1", "A010-1.0"],
                           evaluation_contract_version="V1",
                           active_ontology_versions=["genome-v3"],
                           high_dependency_assumptions=["centrality-A"],
                           active_runtime_certifications=["rt-X"],
                           major_capabilities=["scan"],
                           known_tensions=["T1"],
                           unresolved_pattern_refs=["UP1"],
                           active_knowledge_projection=["K_A"],
                           dormant_knowledge_projection=["K_dorm"],
                           validation_rules=["R1"],
                           authority_state_snapshot={"PO": "PO"},
                           operator_ratifications=["rat-1"],
                           transformation_evidence=["ev-1"],
                           challenge_conditions=["c1"])
    e2 = EpochManifest.from_dict(e.to_dict())
    assert e2.to_dict() == e.to_dict()


def test_fingerprint_stable_and_sensitive():
    a = EpochManifest.make(seq=2, epoch_id="E17", known_tensions=["T1"])
    b = EpochManifest.make(seq=2, epoch_id="E17", known_tensions=["T1"])
    c = EpochManifest.make(seq=2, epoch_id="E17", known_tensions=["T2"])
    assert a.fingerprint() == b.fingerprint()
    assert a.fingerprint() != c.fingerprint()