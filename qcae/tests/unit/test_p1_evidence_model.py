"""P1-C01 — evidence object domain model evidence (Book IV 9.1, 9.6)."""

from __future__ import annotations

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.evidence import (
    EvidenceArtifact,
    EvidenceObjectType,
    FreshnessState,
    ScopeDimensions,
    make_evidence_artifact,
    RAW_OBJECT_TYPES,
    INTERPRETATION_OBJECT_TYPES,
)
from qcae.core.serialization import QcaeSchemaVersionError
from qcae.core.vocabulary import EvidenceClass


def _scope(**over) -> ScopeDimensions:
    defaults = {"implementation_revision": "rev-abc123", "contract_version": "1.0.0"}
    defaults.update(over)
    return ScopeDimensions(**defaults)


def _artifact(**over) -> EvidenceArtifact:
    defaults = dict(
        evidence_id="ev-test-001",
        subject_id="atom-ordering-detection",
        evidence_object_type=EvidenceObjectType.TEST_RESULT,
        evidence_class=EvidenceClass.E2_SOURCE,
        artifact_digest="a" * 64,
        producer="ContractTestWorker",
        created_at="2026-09-12T00:00:00Z",
        scope=_scope(),
        summary="ordering clause C-17 passed on duplicate-event stream",
    )
    defaults.update(over)
    return make_evidence_artifact(**defaults)


class TestVocabularySeparation:
    def test_object_type_is_distinct_axis_from_strength(self) -> None:
        """Same object type can carry different strength; type never implies it."""
        raw = _artifact(evidence_object_type=EvidenceObjectType.TEST_RESULT, evidence_class=EvidenceClass.E0_CLAIM)
        verified = _artifact(
            evidence_object_type=EvidenceObjectType.TEST_RESULT, evidence_class=EvidenceClass.E5_INDEPENDENT_CONTRACT
        )
        assert raw.evidence_object_type is verified.evidence_object_type
        assert raw.evidence_class is not verified.evidence_class

    def test_all_book_iv_object_types_present(self) -> None:
        assert {t.value for t in EvidenceObjectType} == {
            "SOURCE_ANCHOR",
            "ARTIFACT",
            "OBSERVATION",
            "TEST_RESULT",
            "BENCHMARK_RESULT",
            "DATASET_RECORD",
            "CLAIM",
            "CONTRADICTION",
            "DECISION",
            "AUTHORITY_RECORD",
            "UNCERTAINTY",
        }

    def test_raw_and_interpretation_partitions(self) -> None:
        assert EvidenceObjectType.OBSERVATION in RAW_OBJECT_TYPES
        assert EvidenceObjectType.CLAIM not in RAW_OBJECT_TYPES
        assert EvidenceObjectType.CLAIM in INTERPRETATION_OBJECT_TYPES
        assert EvidenceObjectType.CONTRADICTION in INTERPRETATION_OBJECT_TYPES
        assert RAW_OBJECT_TYPES.isdisjoint(INTERPRETATION_OBJECT_TYPES)

    def test_envelope_object_type_not_shadowed(self) -> None:
        """The serialization envelope key must not be overridable by a field."""
        art = _artifact()
        payload = art.to_dict()
        assert payload["object_type"] == "EvidenceArtifact"
        assert payload["evidence_object_type"] == EvidenceObjectType.TEST_RESULT.value

    def test_unknown_object_type_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="evidence_object_type"):
            _artifact(evidence_object_type="VOICE_MEMO")

    def test_unknown_verification_state_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="evidence_class"):
            _artifact(evidence_class="E99")


class TestRawVsInterpretation:
    def test_interpretation_requires_explicit_status(self) -> None:
        with pytest.raises(QcaeValidationError, match="interpretation_status"):
            _artifact(evidence_object_type=EvidenceObjectType.CLAIM, summary="looks good to me")

    def test_interpretation_with_status_is_valid(self) -> None:
        claim = _artifact(
            evidence_object_type=EvidenceObjectType.CLAIM,
            evidence_class=EvidenceClass.E0_CLAIM,
            interpretation_status="evaluator conclusion, pending runtime verification",
        )
        claim.validate()

    def test_raw_record_does_not_need_interpretation_fields(self) -> None:
        _artifact(interpretation_status="")  # raw object, no conclusion attached


class TestRequiredFields:
    @pytest.mark.parametrize(
        "drop",
        ["evidence_id", "subject_id", "artifact_digest", "producer", "created_at"],
    )
    def test_required_field_rejection(self, drop: str) -> None:
        kwargs = {"evidence_id": "ev-x", "subject_id": "atom-x", "artifact_digest": "b" * 64,
                  "producer": "w", "created_at": "t"}
        kwargs[drop] = ""
        with pytest.raises(QcaeValidationError):
            _artifact(**kwargs)

    def test_malformed_digest_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="artifact_digest"):
            _artifact(artifact_digest="ZZGG-not-hex")

    def test_evidence_requires_subject_and_provenance(self) -> None:
        with pytest.raises(QcaeValidationError, match="subject_id"):
            _artifact(subject_id="")
        with pytest.raises(QcaeValidationError, match="producer"):
            _artifact(producer="  ")


class TestScopeAndFreshness:
    def test_scope_must_be_non_empty(self) -> None:
        with pytest.raises(QcaeValidationError, match="at least one dimension"):
            _artifact(scope=ScopeDimensions())

    def test_scope_dimensions_preserved(self) -> None:
        scope = _scope(environment="ci-linux", market_regime="trending")
        art = _artifact(scope=scope)
        assert art.scope.environment == "ci-linux"
        assert art.scope.market_regime == "trending"

    def test_stale_requires_reason(self) -> None:
        with pytest.raises(QcaeValidationError, match="stale_reason"):
            _artifact(freshness=FreshnessState.STALE)
        stale = _artifact(freshness=FreshnessState.STALE, stale_reason="upstream rev bumped")
        stale.validate()

    def test_validity_window_ordering(self) -> None:
        with pytest.raises(QcaeValidationError, match="valid_until"):
            _artifact(valid_from="2026-09-12", valid_until="2026-01-01")


class TestSupersession:
    def test_supersession_does_not_delete_original(self) -> None:
        """Superseding is a pointer on the old record plus a lineage edge; the
        original record object remains intact and retrievable."""
        import dataclasses

        original = _artifact()
        superseding = _artifact(evidence_id="ev-test-002", summary="re-run on new rev")
        updated = dataclasses.replace(original, superseded_by="ev-test-002")
        updated.validate()
        # original in-memory record unchanged (append-oriented history)
        assert original.superseded_by == ""
        assert updated.superseded_by == "ev-test-002"
        assert updated.evidence_id == original.evidence_id

    def test_self_supersession_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="supersede itself"):
            _artifact(superseded_by="ev-test-001")


class TestSerialization:
    def test_round_trip(self) -> None:
        art = _artifact(revalidation_triggers=("upstream_revision", "license_change"))
        restored = EvidenceArtifact.from_dict(art.to_dict())
        assert restored == art
        assert restored.scope == art.scope
        assert restored.revalidation_triggers == ("upstream_revision", "license_change")

    def test_scope_round_trip_nested(self) -> None:
        art = _artifact()
        payload = art.to_dict()
        assert payload["scope"]["object_type"] == "ScopeDimensions"
        restored = EvidenceArtifact.from_dict(payload)
        assert restored.scope.implementation_revision == "rev-abc123"

    def test_schema_version_rejected(self) -> None:
        payload = _artifact().to_dict()
        payload["schema_version"] = 99
        with pytest.raises(QcaeSchemaVersionError):
            EvidenceArtifact.from_dict(payload)

    def test_digest_is_content_deterministic(self) -> None:
        assert _artifact().digest() == _artifact().digest()
        assert _artifact(summary="different").digest() != _artifact().digest()
