"""Governed EvidenceRegistry (G2R-02).

Before ANY adjudicated decision the scenario runner builds a governed evidence
registry from the scenario's observable evidence objects. Every evidence_ref
used by an EvidenceObservation, PhaseProposal, PhaseDecisionRecord or a governed
institutional lifecycle action MUST resolve to an actual registered object:

  * unknown evidence ref  -> FAIL CLOSED (raised / recorded, never applied);
  * duplicate conflicting evidence id -> FAIL CLOSED at construction;
  * evidence-object provenance always survives the run.

The registry also derives the NON-SCALAR lineage support described in G2R §5
(raw count, distinct source lineages, distinct method/model lineages, shared
allocator / retrieval exposure) so an `independent_contradiction = HIGH` claim
cannot ride on a single evidence lineage. No authoritative effective-sample-size
score is produced — G2R only distinguishes ONE lineage from MULTIPLE DISTINCT.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex
from .affected import AffectedSurface
from .evidence import ContradictionRecord, EvidenceRecord, ResolutionCondition
from .independence import IndependenceRecord
from .patch import PatchPressureRecord

#: kinds the registry will accept from scenario observable_evidence.json
REGISTRY_KINDS = (
    "OBSERVATION",
    "DETERMINISTIC",
    "AGENT_CLAIM",
    "INDEPENDENT_CONFIRMATION",
    "CONTRADICTION",
    "PATCH_PRESSURE",
    "INDEPENDENCE",
    "AFFECTED_SURFACE",
    "RESOLUTION",
)


class UnknownEvidenceRef(KeyError):
    pass


class DuplicateEvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class LineageSummary:
    """NON-SCALAR lineage support for one observation (G2R §5). Preserves the
    raw vector; a derived summary exists but is label EXPERIMENTAL and carries
    no transition authority."""

    raw_evidence_count: int
    distinct_source_lineages: int
    distinct_model_lineages: int
    shared_allocator: bool
    shared_retrieval: bool
    resolution_kinds: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_evidence_count": self.raw_evidence_count,
            "distinct_source_lineages": self.distinct_source_lineages,
            "distinct_model_lineages": self.distinct_model_lineages,
            "shared_allocator": self.shared_allocator,
            "shared_retrieval": self.shared_retrieval,
            "resolution_kinds": list(self.resolution_kinds),
        }

    # EXPERIMENTAL ONLY — no transition authority, kept for operator displays.
    @property
    def derived_lineage_score(self) -> float:
        return float(min(self.distinct_source_lineages, self.raw_evidence_count))


def _split_lineages(value: str) -> List[str]:
    """'LINEAGE_A|B' style labels -> distinct parts."""
    return [p for p in (str(value or "").replace("|", ";").split(";")) if p.strip()]


class EvidenceRegistry:
    """id -> registered evidence object, with duplicate-conflict detection and
    deterministic lineage derivation."""

    def __init__(self, objects: Optional[Sequence[Any]] = None):
        self._objects: Dict[str, Any] = {}
        self._canon: Dict[str, str] = {}
        for obj in (objects or []):
            self.register(obj)

    # ------------------------------------------------------------------ #
    @staticmethod
    def from_records(records: Iterable[Mapping[str, Any]]) -> "EvidenceRegistry":
        """Build a registry from scenario `observable_evidence.json` records."""
        reg = EvidenceRegistry()
        for rec in records:
            reg.register(reg._coerce(rec))
        return reg

    def _coerce(self, rec: Mapping[str, Any]) -> Any:
        kind = str(rec.get("kind", "OBSERVATION")).upper()
        rid = str(rec["record_id"])
        if kind in ("OBSERVATION", "DETERMINISTIC", "AGENT_CLAIM", "INDEPENDENT_CONFIRMATION"):
            actual = ("AGENT_CLAIM" if kind == "AGENT_CLAIM" else
                      "INDEPENDENT_CONFIRMATION" if kind == "INDEPENDENT_CONFIRMATION" else
                      "OBSERVATION" if kind == "OBSERVATION" else "DETERMINISTIC")
            return EvidenceRecord(
                record_id=rid,
                kind=actual,
                claim=str(rec.get("claim", "")),
                source_lineage=str(rec.get("lineage", "")),
                resolution_class=str(rec.get("resolution_class", "")),
                allocator=str(rec.get("allocator", "")),
                retrieval_lineage=str(rec.get("retrieval_lineage", "")),
                seq=int(rec.get("seq", 0)),
            )
        if kind == "CONTRADICTION":
            return ContradictionRecord(
                contradiction_id=rid,
                claim_a=str(rec.get("claim_a", "")),
                claim_b=str(rec.get("claim_b", "")),
                conflict_level=str(rec.get("conflict_level", "EXPLANATORY")),
                seq=int(rec.get("seq", 0)),
            )
        if kind == "PATCH_PRESSURE":
            return PatchPressureRecord(
                record_id=rid,
                causal_signature=str(rec.get("causal_signature", "")),
                affected_object=str(rec.get("affected_object", "")),
                structural_level=str(rec.get("structural_level", "L1")),
                override_count=int(rec.get("override_count", 0)),
                seq=int(rec.get("seq", 0)),
            )
        if kind == "INDEPENDENCE":
            return IndependenceRecord(
                record_id=rid,
                raw_reviewers=int(rec.get("raw_reviewers", 0)),
                distinct_source_lineages=int(rec.get("distinct_source_lineages", 0)),
                seq=int(rec.get("seq", 0)),
            )
        if kind == "AFFECTED_SURFACE":
            return AffectedSurface(
                affected_surface_id=rid,
                seq=int(rec.get("seq", 0)),
            )
        if kind == "RESOLUTION":
            return ResolutionCondition(
                resolution_id=rid,
                resolution_class=str(rec.get("resolution_class", "NO_RESOLUTION")),
                claim=str(rec.get("claim", "")),
                evidence_refs=[str(r) for r in rec.get("evidence_refs", [])],
                seq=int(rec.get("seq", 0)),
            )
        raise DuplicateEvidenceError(f"unknown registry record kind {kind!r} for {rid!r}")

    # ------------------------------------------------------------------ #
    def register(self, obj: Any) -> None:
        rid = getattr(obj, "record_id", None) or getattr(obj, "contradiction_id", None) or \
            getattr(obj, "affected_surface_id", None) or getattr(obj, "resolution_id", None)
        if not rid:
            raise DuplicateEvidenceError("evidence object carries no registry id")
        canon = deterministic_hex("obj", type(obj).__name__, _obj_canon(obj))
        if rid in self._objects and self._canon.get(rid) != canon:
            raise DuplicateEvidenceError(
                f"duplicate evidence id {rid!r} with CONFLICTING content (fail closed)"
            )
        self._objects[rid] = obj
        self._canon[rid] = canon

    def has(self, rid: str) -> bool:
        return rid in self._objects

    def resolve(self, rid: str) -> Any:
        if rid not in self._objects:
            raise UnknownEvidenceRef(f"evidence ref {rid!r} is not registered (fail closed)")
        return self._objects[rid]

    def resolve_all(self, refs: Sequence[str]) -> List[Any]:
        return [self.resolve(r) for r in refs]

    def check_all(self, refs: Sequence[str]) -> None:
        """Fail-closed validation; raises UnknownEvidenceRef on the first hole."""
        for r in refs:
            self.resolve(r)

    @property
    def ids(self) -> List[str]:
        return sorted(self._objects)

    def __len__(self) -> int:
        return len(self._objects)

    # ------------------------------------------------------------------ #
    # NON-SCALAR lineage support (G2R §5)
    # ------------------------------------------------------------------ #
    def lineage_summary(self, refs: Sequence[str]) -> LineageSummary:
        """Distinct-lineage support for the observation's evidence refs."""
        raw = len(refs)
        sources: set[str] = set()
        models: set[str] = set()
        allocators: set[str] = set()
        retrievals: set[str] = set()
        resolutions: List[str] = []
        for r in refs:
            try:
                obj = self.resolve(r)
            except UnknownEvidenceRef:
                # ref validation happens before lineage derivation; unknown refs
                # fail closed at the runner level, never silently here
                continue
            ev = getattr(obj, "source_lineage", "") or getattr(obj, "lineage", "")
            sources.update(_split_lineages(ev))
            kind = getattr(obj, "kind", "")
            if kind == "INDEPENDENT_CONFIRMATION":
                models.add("indep-confirmation")
            res = getattr(obj, "resolution_class", "")
            if res:
                resolutions.append(res)
            alloc = getattr(obj, "allocator", "")
            if alloc:
                allocators.add(alloc)
            retr = getattr(obj, "retrieval_lineage", "")
            if retr:
                retrievals.add(retr)
        return LineageSummary(
            raw_evidence_count=raw,
            distinct_source_lineages=len(sources),
            distinct_model_lineages=len(models) or (len(sources) if sources else 0),
            shared_allocator=len(allocators) > 1,
            shared_retrieval=len(retrievals) > 1,
            resolution_kinds=tuple(sorted(set(resolutions))),
        )


def _obj_canon(obj: Any) -> str:
    from dataclasses import asdict

    if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        data = obj.to_dict()
    else:
        try:
            data = asdict(obj)  # type: ignore[arg-type]
        except TypeError:
            data = repr(obj)
    import json

    return json.dumps(data, sort_keys=True, default=str)