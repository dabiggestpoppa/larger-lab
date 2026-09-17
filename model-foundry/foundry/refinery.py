"""MF-B3 — Dataset Refinery + Corpus Architecture.

Answers:

    Given governed sources, what dataset can be constructed, with what lineage,
    and what proves it is not silently contaminated or temporally leaked?

Doctrine enforced here:

    AVAILABLE DATA != TRAINABLE DATA
    REGISTERED SOURCE != CLEAN SOURCE

Everything is deterministic and offline: transformations are declared recipes,
not model inference. Refinery failures are first-class
(:class:`RefineryNegativeResult`) because a dataset that could not be built is
scientific information, not a silently dropped row.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from .boundary import grade_contamination
from .core import (
    GENERIC_SERVICE_DOUBLES,
    Contradiction,
    FrozenMap,
    OceTestDouble,
    PolicyBlocked,
    Receipt,
    fingerprint,
)
from .data import ContaminationGraph, SourceRecord, SourceRegistry
from .enums import (
    CONTAMINATION_SEVERITY,
    ContaminationClass,
    RefineryFailure,
    RightsState,
    SourceRole,
    TRAIN_ROLES,
)

#: Refinery run lifecycle is the *same* generic-workflow stand-in declared in
#: :data:`foundry.core.GENERIC_SERVICE_DOUBLES`; it is referenced, not re-declared,
#: so the One-OCE boundary has exactly one declaration per fixture.
REFINERY_DOUBLE = GENERIC_SERVICE_DOUBLES["workflow"]

#: Payload fields that must never appear in a materialized dataset.
SECRET_PATTERNS: tuple[tuple[str, str], ...] = (
    ("private_key_block", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("aws_access_key", r"\bAKIA[0-9A-Z]{16}\b"),
    ("api_key_assignment", r"\b(?:api[_-]?key|secret[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    ("bearer_token", r"\bBearer\s+[A-Za-z0-9\-._~+/]{20,}"),
    ("cerebus_rule_id", r"\bCEREBUS-R\d+\b"),
)


# --------------------------------------------------------------------------
# Records + deterministic transforms
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RawItem:
    """One source item before refinement. Time fields are mandatory."""

    item_id: str
    source_id: str
    text: str
    event_time_utc: str
    known_at_utc: str
    payload_class: str = "text"
    fields: FrozenMap = field(default_factory=FrozenMap)

    def content_digest(self) -> str:
        payload = f"{self.source_id}|{self.normalized_text()}"
        return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def normalized_text(self) -> str:
        return re.sub(r"\s+", " ", self.text.strip().lower())

    def shingles(self, size: int = 5) -> frozenset[str]:
        tokens = re.findall(r"[a-z0-9]+", self.normalized_text())
        if len(tokens) < size:
            return frozenset({" ".join(tokens)}) if tokens else frozenset()
        return frozenset(
            " ".join(tokens[i : i + size]) for i in range(len(tokens) - size + 1)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "source_id": self.source_id,
            "payload_class": self.payload_class,
            "event_time_utc": self.event_time_utc,
            "known_at_utc": self.known_at_utc,
            "fields": dict(self.fields),
            "content_digest": self.content_digest(),
            "text_length": len(self.text),
        }


@dataclass(frozen=True)
class RefineryRecipe:
    """Declared, reviewable transformation chain. No hidden steps."""

    recipe_id: str
    steps: tuple[str, ...]
    dedup_shingle_size: int = 5
    dedup_jaccard_threshold: float = 0.85
    secret_scan: bool = True
    pit_enforce: bool = True
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "steps": list(self.steps),
            "dedup_shingle_size": self.dedup_shingle_size,
            "dedup_jaccard_threshold": self.dedup_jaccard_threshold,
            "secret_scan": self.secret_scan,
            "pit_enforce": self.pit_enforce,
            "description": self.description,
            "deterministic": True,
            "model_inference_used": False,
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


DEFAULT_RECIPE = RefineryRecipe(
    recipe_id="recipe.text.v1",
    steps=("normalize_whitespace", "exact_dedup", "near_dedup", "secret_scan", "pit_audit", "split_by_source"),
    description="canonical text refinement chain",
)


# --------------------------------------------------------------------------
# Audits
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PointInTimeAudit:
    """Temporal/PIT leakage audit for an item set."""

    checked: int
    violations: tuple[dict[str, Any], ...]
    decision_reference_utc: str | None

    def passed(self) -> bool:
        return not self.violations

    def to_dict(self) -> dict[str, Any]:
        return {
            "checked": self.checked,
            "violations": list(self.violations),
            "decision_reference_utc": self.decision_reference_utc,
            "passed": self.passed(),
            "pit_is_a_leak_when_unknown": True,
        }


def audit_point_in_time(
    items: Iterable[RawItem], *, decision_reference_utc: str | None = None
) -> PointInTimeAudit:
    """Detect future information: knowledge arriving after the decision instant."""

    violations: list[dict[str, Any]] = []
    checked = 0
    for item in items:
        checked += 1
        if not item.known_at_utc:
            violations.append(
                {"item_id": item.item_id, "reason": "KNOWN_AT_UNKNOWN", "severity": "LEAK"}
            )
            continue
        if item.known_at_utc < item.event_time_utc:
            violations.append(
                {
                    "item_id": item.item_id,
                    "reason": "KNOWLEDGE_PRECEDES_EVENT",
                    "severity": "IMPLAUSIBLE",
                    "event_time_utc": item.event_time_utc,
                    "known_at_utc": item.known_at_utc,
                }
            )
        if decision_reference_utc is not None and item.known_at_utc > decision_reference_utc:
            violations.append(
                {
                    "item_id": item.item_id,
                    "reason": "FUTURE_INFORMATION_AT_DECISION_INSTANT",
                    "severity": "LEAK",
                    "decision_reference_utc": decision_reference_utc,
                    "known_at_utc": item.known_at_utc,
                }
            )
    return PointInTimeAudit(
        checked=checked,
        violations=tuple(violations),
        decision_reference_utc=decision_reference_utc,
    )


@dataclass(frozen=True)
class SecretScanResult:
    hits: tuple[dict[str, Any], ...]
    scanned: int

    def passed(self) -> bool:
        return not self.hits

    def to_dict(self) -> dict[str, Any]:
        return {"scanned": self.scanned, "hits": list(self.hits), "passed": self.passed()}


def scan_secrets(items: Iterable[RawItem]) -> SecretScanResult:
    hits: list[dict[str, Any]] = []
    scanned = 0
    for item in items:
        scanned += 1
        for name, pattern in SECRET_PATTERNS:
            if re.search(pattern, item.text):
                hits.append(
                    {
                        "item_id": item.item_id,
                        "source_id": item.source_id,
                        "pattern": name,
                    }
                )
    return SecretScanResult(hits=tuple(hits), scanned=scanned)


@dataclass(frozen=True)
class DedupReport:
    """Duplicates collapse within a source *and* across sources.

    Exact-duplicate detection is digest based and therefore source-scoped;
    cross-source identity (mirrors, re-publications) is caught by near-duplicate
    detection at similarity 1.0. Both are counted, because a mirror that survives
    as a separate lineage is fake diversity.
    """

    exact_duplicates_collapsed: int
    near_duplicates_collapsed: tuple[dict[str, Any], ...]
    kept: tuple[str, ...]
    collapsed_to_lineage: dict[str, str]

    @property
    def cross_source_collapsed(self) -> tuple[dict[str, Any], ...]:
        return tuple(
            entry for entry in self.near_duplicates_collapsed if entry.get("cross_source") is True
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "exact_duplicates_collapsed": self.exact_duplicates_collapsed,
            "near_duplicates_collapsed": list(self.near_duplicates_collapsed),
            "near_duplicate_count": len(self.near_duplicates_collapsed),
            "cross_source_duplicate_count": len(self.cross_source_collapsed),
            "kept_items": list(self.kept),
            "collapsed_to_lineage": dict(self.collapsed_to_lineage),
            "duplicates_do_not_add_diversity": True,
        }


def dedup(items: list[RawItem], *, shingle_size: int, jaccard_threshold: float) -> tuple[list[RawItem], DedupReport]:
    """Exact then near duplicate collapse, deterministic ordering."""

    seen_digest: dict[str, str] = {}
    exact_collapsed = 0
    collapsed_to_lineage: dict[str, str] = {}
    kept: list[RawItem] = []
    for item in sorted(items, key=lambda i: (i.source_id, i.item_id)):
        digest = item.content_digest()
        if digest in seen_digest:
            exact_collapsed += 1
            collapsed_to_lineage[item.item_id] = seen_digest[digest]
            continue
        seen_digest[digest] = item.item_id
        kept.append(item)

    near_collapsed: list[dict[str, Any]] = []
    survivors: list[RawItem] = []
    for item in kept:
        shingles = item.shingles(shingle_size)
        duplicate_of = None
        for prior in survivors:
            prior_shingles = prior.shingles(shingle_size)
            union = shingles | prior_shingles
            similarity = len(shingles & prior_shingles) / len(union) if union else 0.0
            if similarity >= jaccard_threshold:
                duplicate_of = prior
                break
        if duplicate_of is not None:
            near_collapsed.append(
                {
                    "item_id": item.item_id,
                    "duplicate_of": duplicate_of.item_id,
                    "cross_source": item.source_id != duplicate_of.source_id,
                    "similarity": round(
                        len(shingles & duplicate_of.shingles(shingle_size))
                        / max(1, len(shingles | duplicate_of.shingles(shingle_size))),
                        4,
                    ),
                }
            )
            collapsed_to_lineage[item.item_id] = duplicate_of.item_id
            continue
        survivors.append(item)

    return survivors, DedupReport(
        exact_duplicates_collapsed=exact_collapsed,
        near_duplicates_collapsed=tuple(near_collapsed),
        kept=tuple(i.item_id for i in survivors),
        collapsed_to_lineage=collapsed_to_lineage,
    )


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DatasetManifest:
    """The materialized, reproducible definition of a dataset."""

    dataset_id: str
    version: int
    purpose: str
    role: SourceRole
    recipe: RefineryRecipe
    sources: tuple[dict[str, Any], ...]
    item_count: int
    splits: FrozenMap
    dedup: dict[str, Any]
    pit_audit: dict[str, Any]
    secret_scan: dict[str, Any]
    contamination: dict[str, Any]
    rights_summary: dict[str, Any]
    provenance_summary: dict[str, Any]
    transformations: tuple[str, ...]
    lineage_fingerprint: str
    excluded_sources: tuple[dict[str, Any], ...] = ()
    notes: str = ""

    @property
    def trainable(self) -> bool:
        """A manifest is a training dataset only if its role is a training role."""

        return self.role in TRAIN_ROLES

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "purpose": self.purpose,
            "role": self.role.value,
            "recipe": self.recipe.to_dict(),
            "sources": list(self.sources),
            "item_count": self.item_count,
            "splits": dict(self.splits),
            "dedup": self.dedup,
            "pit_audit": self.pit_audit,
            "secret_scan": self.secret_scan,
            "contamination": self.contamination,
            "rights_summary": self.rights_summary,
            "provenance_summary": self.provenance_summary,
            "transformations": list(self.transformations),
            "lineage_fingerprint": self.lineage_fingerprint,
            "excluded_sources": list(self.excluded_sources),
            "notes": self.notes,
            "trainable": self.trainable,
            "manifest_is_capability_claim": False,
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


@dataclass(frozen=True)
class RefineryNegativeResult:
    """A dataset that could not be built. First-class output, never a silent drop."""

    dataset_id: str
    failure: RefineryFailure
    detail: str
    blocked_sources: tuple[str, ...]
    evidence: dict[str, Any]
    reopen_condition: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "refinery_negative_result",
            "dataset_id": self.dataset_id,
            "failure": self.failure.value,
            "detail": self.detail,
            "blocked_sources": list(self.blocked_sources),
            "evidence": self.evidence,
            "reopen_condition": self.reopen_condition,
            "negative_result_is_project_failure": False,
        }


@dataclass(frozen=True)
class RefineryRun:
    manifest: DatasetManifest | None
    negative_result: RefineryNegativeResult | None
    receipt: Receipt

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest": self.manifest.to_dict() if self.manifest else None,
            "negative_result": self.negative_result.to_dict() if self.negative_result else None,
            "receipt": self.receipt.to_dict(),
        }


# --------------------------------------------------------------------------
# The refinery
# --------------------------------------------------------------------------


@dataclass
class DatasetRefinery:
    """Deterministically refine governed sources into a manifest."""

    registry: SourceRegistry
    contamination: ContaminationGraph
    double: OceTestDouble = field(default=REFINERY_DOUBLE)
    _versions: dict[str, int] = field(default_factory=dict)

    # -- helpers ----------------------------------------------------------

    def _rights_summary(self, records: list[SourceRecord]) -> dict[str, Any]:
        states: dict[str, int] = {}
        for record in records:
            state = record.rights_state().value
            states[state] = states.get(state, 0) + 1
        return {
            "by_state": states,
            "unknown_rights_sources": sorted(
                r.source_id for r in records if r.rights_state() is RightsState.RIGHTS_UNKNOWN
            ),
            "all_sources_train_permissive": all(r.trainable() for r in records),
        }

    def _contamination_summary(self, source_ids: list[str]) -> dict[str, Any]:
        per_source = {
            source_id: self.contamination.worst_grade(source_id).value for source_id in source_ids
        }
        worst = grade_contamination(
            tuple((sid, ContaminationClass(grade)) for sid, grade in per_source.items())
        )
        blocking = sorted(
            source_id
            for source_id in source_ids
            if self.contamination.claim_blocking_edges(source_id)
        )
        return {
            "per_source_worst_grade": per_source,
            "dataset_worst_grade": worst.value,
            "claim_blocking_sources": blocking,
            "observed_absence_is_not_cleanliness": True,
        }

    def _split(self, items: list[RawItem], role: SourceRole) -> dict[str, Any]:
        """Split by *source*, never by item, so eval material cannot leak into training."""

        by_source: dict[str, list[str]] = {}
        for item in items:
            by_source.setdefault(item.source_id, []).append(item.item_id)
        for source_id in by_source:
            by_source[source_id] = sorted(by_source[source_id])

        if role in TRAIN_ROLES:
            train_sources = sorted(
                source_id
                for source_id in by_source
                if self.registry.get(source_id).role in TRAIN_ROLES
            )
            held_out = sorted(set(by_source) - set(train_sources))
            return {
                "strategy": "BY_SOURCE",
                "train": {"sources": train_sources, "items": sum(len(by_source[s]) for s in train_sources)},
                "held_out": {"sources": held_out, "items": sum(len(by_source[s]) for s in held_out)},
                "item_level_random_split_used": False,
            }
        return {
            "strategy": "BY_SOURCE",
            "eval": {"sources": sorted(by_source), "items": sum(len(v) for v in by_source.values())},
            "item_level_random_split_used": False,
        }

    # -- main -------------------------------------------------------------

    def refine(
        self,
        *,
        dataset_id: str,
        purpose: str,
        role: SourceRole,
        items: list[RawItem],
        source_ids: list[str],
        recipe: RefineryRecipe = DEFAULT_RECIPE,
        decision_reference_utc: str | None = None,
        failure_tolerance: str = "STRICT",
    ) -> RefineryRun:
        """Build a dataset manifest or a truthful negative result."""

        excluded: list[dict[str, Any]] = []
        usable_ids: list[str] = []

        for source_id in sorted(source_ids):
            record = self.registry.get(source_id)

            if record.carries_withheld_doctrine():
                excluded.append(
                    {
                        "source_id": source_id,
                        "reason": RefineryFailure.CONTAMINATION_BLOCKED.value,
                        "detail": "withheld CEREBUS-family doctrine",
                    }
                )
                continue

            if role in TRAIN_ROLES and not record.trainable():
                excluded.append(
                    {
                        "source_id": source_id,
                        "reason": RefineryFailure.RIGHTS_BLOCKED.value,
                        "detail": f"rights state {record.rights_state().value}",
                    }
                )
                continue

            if record.role in {SourceRole.QUARANTINED, SourceRole.EXCLUDED}:
                excluded.append(
                    {
                        "source_id": source_id,
                        "reason": RefineryFailure.CONTAMINATION_BLOCKED.value,
                        "detail": f"role {record.role.value}",
                    }
                )
                continue

            if record.secret_bearing:
                excluded.append(
                    {
                        "source_id": source_id,
                        "reason": RefineryFailure.SCHEMA_INVALID.value,
                        "detail": "secret-bearing source",
                    }
                )
                continue

            usable_ids.append(source_id)

        if not usable_ids:
            return self._negative(
                dataset_id,
                _dominant_failure(excluded, role),
                "no governed source survived rights/contamination gating: "
                + "; ".join(
                    f"{e['source_id']} ({e['reason']}: {e['detail']})" for e in sorted(excluded, key=lambda e: e["source_id"])
                ),
                excluded,
                excluded_sources=[e["source_id"] for e in excluded],
            )

        selected_items = [item for item in items if item.source_id in set(usable_ids)]

        if recipe.secret_scan:
            scan = scan_secrets(selected_items)
            if not scan.passed():
                return self._negative(
                    dataset_id,
                    RefineryFailure.SCHEMA_INVALID,
                    "secret-bearing content detected in candidate items",
                    scan.to_dict(),
                    excluded_sources=sorted({hit["source_id"] for hit in scan.hits}),
                )
        else:
            scan = SecretScanResult(hits=(), scanned=len(selected_items))

        if recipe.pit_enforce:
            pit = audit_point_in_time(
                selected_items, decision_reference_utc=decision_reference_utc
            )
            if not pit.passed() and role in TRAIN_ROLES and failure_tolerance == "STRICT":
                return self._negative(
                    dataset_id,
                    RefineryFailure.PIT_INVALID,
                    "point-in-time leakage detected; future information present at decision instant",
                    pit.to_dict(),
                    excluded_sources=sorted({v["item_id"] for v in pit.violations})[:0],
                )
        else:
            pit = PointInTimeAudit(checked=len(selected_items), violations=(), decision_reference_utc=None)

        kept, dedup_report = dedup(
            selected_items,
            shingle_size=recipe.dedup_shingle_size,
            jaccard_threshold=recipe.dedup_jaccard_threshold,
        )

        lineage_fingerprint = fingerprint(
            {
                "dataset_id": dataset_id,
                "role": role.value,
                "recipe": recipe.fingerprint,
                "items": sorted(i.content_digest() for i in kept),
                "sources": sorted(usable_ids),
            }
        )

        self._versions[dataset_id] = self._versions.get(dataset_id, 0) + 1
        manifest = DatasetManifest(
            dataset_id=dataset_id,
            version=self._versions[dataset_id],
            purpose=purpose,
            role=role,
            recipe=recipe,
            sources=tuple(
                {
                    "source_id": source_id,
                    "role": self.registry.get(source_id).role.value,
                    "rights_state": self.registry.get(source_id).rights_state().value,
                    "lineage": self.registry.get(source_id).authoritative_lineage,
                }
                for source_id in usable_ids
            ),
            item_count=len(kept),
            splits=FrozenMap(self._split(kept, role)),
            dedup=dedup_report.to_dict(),
            pit_audit=pit.to_dict(),
            secret_scan=scan.to_dict(),
            contamination=self._contamination_summary(usable_ids),
            rights_summary=self._rights_summary([self.registry.get(s) for s in usable_ids]),
            provenance_summary=self.registry.provenance_summary(usable_ids),
            transformations=recipe.steps,
            lineage_fingerprint=lineage_fingerprint,
            excluded_sources=tuple(excluded),
            notes="derived artifacts inherit ancestor restrictions",
        )

        receipt = Receipt(
            kind="dataset.refined",
            subject=dataset_id,
            payload={
                "manifest_fingerprint": manifest.fingerprint,
                "lineage_fingerprint": lineage_fingerprint,
                "excluded_sources": excluded,
                "item_count": manifest.item_count,
                "role": role.value,
                "available_data_is_not_trainable_data": True,
            },
        )
        return RefineryRun(manifest=manifest, negative_result=None, receipt=receipt)

    def _negative(
        self,
        dataset_id: str,
        failure: RefineryFailure,
        detail: str,
        evidence: Any,
        *,
        excluded_sources: list[str],
    ) -> RefineryRun:
        negative = RefineryNegativeResult(
            dataset_id=dataset_id,
            failure=failure,
            detail=detail,
            blocked_sources=tuple(sorted(excluded_sources)),
            evidence=evidence if isinstance(evidence, dict) else {"detail": str(evidence)},
            reopen_condition=(
                "reopen when a rights disposition, provenance record, or decontaminated "
                "source set is registered and re-audited under the same recipe"
            ),
        )
        receipt = Receipt(
            kind="dataset.refused",
            subject=dataset_id,
            payload={
                "failure": failure.value,
                "detail": detail,
                "negative_result_recorded": True,
            },
        )
        return RefineryRun(manifest=None, negative_result=negative, receipt=receipt)


#: When every source is excluded, the reported failure must name the *actual*
#: dominant reason rather than a convenient one.
_FAILURE_PRIORITY: tuple[RefineryFailure, ...] = (
    RefineryFailure.CONTAMINATION_BLOCKED,
    RefineryFailure.SCHEMA_INVALID,
    RefineryFailure.PIT_INVALID,
    RefineryFailure.RIGHTS_BLOCKED,
    RefineryFailure.SOURCE_UNRESOLVED,
)


def _dominant_failure(exclusions: list[dict[str, Any]], role: SourceRole) -> RefineryFailure:
    present = {e["reason"] for e in exclusions}
    for candidate in _FAILURE_PRIORITY:
        if candidate.value in present:
            return candidate
    return RefineryFailure.RIGHTS_BLOCKED if role in TRAIN_ROLES else RefineryFailure.SOURCE_UNRESOLVED


def assert_manifest_covers_sources(manifest: DatasetManifest, registry: SourceRegistry) -> None:
    """Every source named in a manifest must resolve, and none may be silently absent."""

    for entry in manifest.sources:
        source_id = entry["source_id"]
        if not registry.resolve(source_id):
            raise PolicyBlocked(
                "MANIFEST_MISMATCH",
                f"manifest references unresolved source {source_id!r}",
            )
        record = registry.get(source_id)
        if manifest.role in TRAIN_ROLES and not record.trainable():
            raise Contradiction(
                f"{source_id}: manifest is a training dataset but source rights do not permit training"
            )
        if record.carries_withheld_doctrine():
            raise Contradiction(
                f"{source_id}: withheld doctrine appears in a materialized dataset"
            )


def total_contamination_grade(graph: ContaminationGraph, source_ids: list[str]) -> ContaminationClass:
    if not source_ids:
        return ContaminationClass.C0_NO_OBSERVED_OVERLAP
    grades = [(sid, graph.worst_grade(sid)) for sid in source_ids]
    return max(grades, key=lambda pair: CONTAMINATION_SEVERITY[pair[1]])[1]


__all__ = [
    "DEFAULT_RECIPE",
    "REFINERY_DOUBLE",
    "SECRET_PATTERNS",
    "DatasetManifest",
    "DatasetRefinery",
    "DedupReport",
    "PointInTimeAudit",
    "RawItem",
    "RefineryNegativeResult",
    "RefineryRecipe",
    "RefineryRun",
    "SecretScanResult",
    "assert_manifest_covers_sources",
    "audit_point_in_time",
    "dedup",
    "scan_secrets",
    "total_contamination_grade",
]
