"""P1-C06 — positive/negative knowledge evidence (P1 spec §8–§9, tests 21–25)."""

from __future__ import annotations

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.knowledge import (
    NegativeKnowledge,
    NegativeKnowledgeType,
    PositiveKnowledge,
    ReconsiderationCondition,
    make_negative_knowledge,
    make_positive_knowledge,
)


def _negative(**over) -> NegativeKnowledge:
    defaults = dict(
        record_id="neg-001",
        failure_type=NegativeKnowledgeType.CONTRACT_FAILURE,
        subject_id="repo:owner/libx@v2.4",
        source_revision="v2.4",
        contract_id="CAP-ORDER-001",
        contract_version="1.0.0",
        acquisition_form="USE_DEPENDENCY",
        causal_detail="v2.4 fails ordering clause C-17 on duplicate-event streams: events sharing a timestamp arrive out of order",
        evidence_ids=("ev-fail-1", "ev-fail-2"),
        reconsideration=(ReconsiderationCondition(condition="upstream_revision > v2.4"),),
        scope_summary="USE_DEPENDENCY path, research env, duplicate-event workloads",
        created_at="2026-09-12T00:00:00Z",
    )
    defaults.update(over)
    return make_negative_knowledge(**defaults)


class TestNegativeKnowledge:
    def test_every_canonical_category_accepted(self) -> None:
        for i, t in enumerate(NegativeKnowledgeType):
            rec = _negative(record_id=f"neg-{i}", failure_type=t)
            rec.validate()
        assert len(NegativeKnowledgeType) == 11

    def test_missing_causal_detail_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="causal_detail"):
            _negative(causal_detail="repo bad")

    def test_reconsideration_condition_persisted_and_round_trips(self) -> None:
        rec = _negative(
            reconsideration=(
                ReconsiderationCondition(condition="upstream_revision > v2.4",
                                         detail="ordering fix announced upstream"),
                ReconsiderationCondition(condition="license_change to permissive"),
            )
        )
        restored = NegativeKnowledge.from_dict(rec.to_dict())
        assert restored == rec
        assert restored.reconsideration[0].condition == "upstream_revision > v2.4"

    def test_evidence_required(self) -> None:
        with pytest.raises(QcaeValidationError, match="evidence"):
            _negative(evidence_ids=())

    def test_failed_candidate_discoverable_by_source_revision(self) -> None:
        """Identity fields exist precisely so retrieval by source/revision works."""
        rec = _negative()
        payload = rec.to_dict()
        assert payload["subject_id"] == "repo:owner/libx@v2.4"
        assert payload["source_revision"] == "v2.4"
        assert payload["contract_id"] == "CAP-ORDER-001"

    def test_new_revision_does_not_silently_overwrite_old_rejection(self) -> None:
        old = _negative()
        new = _negative(
            record_id="neg-002",
            source_revision="v2.5",
            superseded_by="neg-002",
            causal_detail="v2.5 re-evaluated after upstream ordering fix; clause C-17 now passes",
        )
        # old record untouched, still carries its failure verdict
        assert old.superseded_by == ""
        assert old.failure_type is NegativeKnowledgeType.CONTRACT_FAILURE
        new.validate()

    def test_round_trip(self) -> None:
        rec = _negative()
        assert NegativeKnowledge.from_dict(rec.to_dict()) == rec


class TestPositiveKnowledge:
    def _positive(self, **over) -> PositiveKnowledge:
        defaults = dict(
            record_id="pos-001",
            statement="revision v3.1 passed contract CAP-ORDER-001 v1.0.0 in research env",
            subject_id="repo:owner/libx@v3.1",
            evidence_ids=("ev-pass-1",),
            created_at="2026-09-12T00:00:00Z",
            source_revision="v3.1",
            contract_id="CAP-ORDER-001",
            contract_version="1.0.0",
        )
        defaults.update(over)
        return make_positive_knowledge(**defaults)

    def test_material_requires_evidence(self) -> None:
        with pytest.raises(QcaeValidationError, match="must link evidence"):
            self._positive(evidence_ids=())

    def test_note_form_allows_no_evidence_but_stays_non_material(self) -> None:
        note = self._positive(material=False, evidence_ids=(), source_revision="",
                              contract_id="", contract_version="")
        note.validate()
        assert note.material is False

    def test_material_requires_scope_identity(self) -> None:
        with pytest.raises(QcaeValidationError, match="source_revision"):
            self._positive(source_revision="")

    def test_known_limitation_preserved(self) -> None:
        rec = self._positive(known_limitation="adapter assumes fixed bar close alignment")
        assert PositiveKnowledge.from_dict(rec.to_dict()).known_limitation.startswith("adapter assumes")
