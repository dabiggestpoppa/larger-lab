"""PatchPressureRecord (A-010 §8) — surface for later causal-signature analysis.

G1 does NOT claim automated causal discovery (AMB-11 stays open). It only:

* records patch events with their causal_signature if explicitly supplied; and
* offers deterministic grouping by an EXACT supplied causal_signature string,
  never by learned similarity.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from .base import deterministic_hex


@dataclass
class PatchPressureRecord:
    record_id: str
    schema_version: str = "1.0.0"
    patch_event_refs: List[str] = field(default_factory=list)
    affected_object: str = ""
    dependency_refs: List[str] = field(default_factory=list)
    causal_signature: str = ""       # only supplied by caller, not inferred
    override_count: int = 0
    recurrence_count: int = 0
    structural_level: str = "L1"     # scope ladder
    time_event_span: str = ""
    confidence: str = "LOW"
    seq: int = 0
    recommended_escalation: str = ""

    @classmethod
    def make(
        cls,
        seq,
        affected_object,
        structural_level="L1",
        causal_signature="",
        patch_event_refs=None,
        recurrence_count=1,
    ):
        return cls(
            record_id=deterministic_hex("patch_pressure", seq, affected_object, causal_signature),
            affected_object=affected_object,
            structural_level=structural_level,
            causal_signature=causal_signature,
            patch_event_refs=list(patch_event_refs or []),
            recurrence_count=recurrence_count,
            seq=seq,
        )


class PatchPressureGroup:
    """Deterministic grouping by exact provided causal_signature. Does NOT
    perform semantic clustering; unlabelled patches remain ungrouped."""

    def __init__(self) -> None:
        self._groups: Dict[str, List[PatchPressureRecord]] = {}

    def add(self, record: PatchPressureRecord) -> None:
        if not record.causal_signature:
            return
        self._groups.setdefault(record.causal_signature, []).append(record)

    def groups(self) -> Dict[str, List[PatchPressureRecord]]:
        return {k: list(v) for k, v in self._groups.items()}

    def group_sizes(self) -> Dict[str, int]:
        return {k: len(v) for k, v in self._groups.items()}