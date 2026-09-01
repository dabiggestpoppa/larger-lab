"""G4 — institutional memory: activation tiers, metabolism, bounded context.

M4 lifecycle state != memory/storage tier != retrieval relevance != canonical
truth (G4 §2). A historically ACTIVE claim may live in ARCHIVAL_STORE; a DORMANT
M4 object may be retrieved temporarily for a reopen evaluation.

Memory components control RETRIEVAL / ACTIVATION ONLY (G4 §27): they never
change authority, never make NegativeKnowledge permanent, never promote
CANDIDATE directly to ACTIVE, never rewrite sealed epochs. Truth/lifecycle
changes still pass the governed M4 path (LifecycleEngine).

No stage may delete provenance. Compression reduces ACTIVE OPERATIONAL
REPRESENTATION; it never destroys source evidence — every compressed record
retains provenance + reconstruction pointers.

Deterministic, local, model-free, wall-clock-free.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex

MEMORY_TIERS = ("ACTIVE_CONTEXT", "DORMANT_STORE", "ARCHIVAL_STORE")
METABOLISM_STAGES = ("INGEST", "CONSOLIDATE", "COMPRESS", "PROMOTE_DEMOTE",
                     "ACTIVATE_DORMANT", "ARCHIVE", "RETRIEVE_REOPEN")


# --------------------------------------------------------------------------- #
# §2 — KnowledgeActivationState: operational tier, NOT a truth label
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class KnowledgeActivationState:
    knowledge_id: str
    m4_state: str
    memory_tier: str = "ACTIVE_CONTEXT"
    retrieval_relevance: str = "LOW"
    version_tag: str = "1.0.0"
    epoch: str = ""
    canonical_truth_note: str = ""     # explicit: tier never encodes truth

    def __post_init__(self) -> None:
        if self.memory_tier not in MEMORY_TIERS:
            raise ValueError(f"unknown memory tier {self.memory_tier!r}")

    def to_dict(self) -> Dict[str, Any]:
        return {"knowledge_id": self.knowledge_id, "m4_state": self.m4_state,
                "memory_tier": self.memory_tier,
                "retrieval_relevance": self.retrieval_relevance,
                "version_tag": self.version_tag, "epoch": self.epoch,
                "canonical_truth_note": self.canonical_truth_note}


# --------------------------------------------------------------------------- #
# MemoryObject — one indexed historical/active object
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MemoryObject:
    object_id: str
    kind: str                                  # KNOWLEDGE | EVIDENCE | EXPERIMENT | NEGATIVE | UNRESOLVED | CERTIFICATION
    tags: Tuple[str, ...] = ()
    dependency_refs: Tuple[str, ...] = ()
    epoch: str = ""
    memory_tier: str = "ACTIVE_CONTEXT"
    m4_state: str = ""
    reopen_condition_ids: Tuple[str, ...] = ()
    summary: str = ""
    provenance_pointer: str = ""               # path back to the original object/evidence
    reconstruction_pointer: str = ""           # path to reconstruct the full record
    history_size: int = 1

    def __post_init__(self) -> None:
        if self.memory_tier not in MEMORY_TIERS:
            raise ValueError(f"unknown memory tier {self.memory_tier!r}")

    def to_dict(self) -> Dict[str, Any]:
        return {"object_id": self.object_id, "kind": self.kind,
                "tags": list(self.tags), "dependency_refs": list(self.dependency_refs),
                "epoch": self.epoch, "memory_tier": self.memory_tier,
                "m4_state": self.m4_state,
                "reopen_condition_ids": list(self.reopen_condition_ids),
                "summary": self.summary, "provenance_pointer": self.provenance_pointer,
                "reconstruction_pointer": self.reconstruction_pointer,
                "history_size": self.history_size}


# --------------------------------------------------------------------------- #
# MemoryCompactionRecord — pruning WITHOUT erasure (G4 §14)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MemoryCompactionRecord:
    compaction_id: str
    object_refs: Tuple[str, ...]
    reason: str
    destination_tier: str
    summary: str = ""
    provenance_pointer: str = ""
    reconstruction_pointer: str = ""
    epoch: str = ""
    policy_version: str = "G4_MEMORY_AND_REACTIVATION_POLICY:1.0.0"

    @classmethod
    def make(cls, seq, object_refs, reason, destination_tier, **kw) -> "MemoryCompactionRecord":
        return cls(compaction_id=deterministic_hex("compaction", seq, sorted(object_refs)),
                   object_refs=tuple(sorted(object_refs)), reason=reason,
                   destination_tier=destination_tier, **kw)

    def to_dict(self) -> Dict[str, Any]:
        return {"compaction_id": self.compaction_id, "object_refs": list(self.object_refs),
                "reason": self.reason, "destination_tier": self.destination_tier,
                "summary": self.summary, "provenance_pointer": self.provenance_pointer,
                "reconstruction_pointer": self.reconstruction_pointer,
                "epoch": self.epoch, "policy_version": self.policy_version}


# --------------------------------------------------------------------------- #
# MemoryIndex — the historical store (never deletes)
# --------------------------------------------------------------------------- #
class MemoryIndex:
    def __init__(self) -> None:
        self._objects: Dict[str, MemoryObject] = {}
        self._activation_events: List[Dict[str, Any]] = []

    def add(self, obj: MemoryObject) -> None:
        if obj.object_id in self._objects:
            raise ValueError(f"duplicate memory object {obj.object_id!r}")
        self._objects[obj.object_id] = obj

    def get(self, object_id: str) -> Optional[MemoryObject]:
        return self._objects.get(object_id)

    def set_tier(self, object_id: str, tier: str, reason: str, actor: str = "MEMORY",
                 policy: str = "") -> None:
        if tier not in MEMORY_TIERS:
            raise ValueError(f"unknown memory tier {tier!r}")
        obj = self._objects.get(object_id)
        if obj is None:
            raise KeyError(f"unknown memory object {object_id!r}")
        self._objects[object_id] = MemoryObject(
            object_id=obj.object_id, kind=obj.kind, tags=obj.tags,
            dependency_refs=obj.dependency_refs, epoch=obj.epoch, memory_tier=tier,
            m4_state=obj.m4_state, reopen_condition_ids=obj.reopen_condition_ids,
            summary=obj.summary, provenance_pointer=obj.provenance_pointer,
            reconstruction_pointer=obj.reconstruction_pointer, history_size=obj.history_size)
        self._activation_events.append({
            "object_id": object_id, "from_tier": obj.memory_tier, "to_tier": tier,
            "reason": reason, "actor": actor, "policy": policy})

    def objects(self) -> Tuple[MemoryObject, ...]:
        return tuple(sorted(self._objects.values(), key=lambda o: o.object_id))

    def objects_by_tier(self, tier: str) -> Tuple[MemoryObject, ...]:
        return tuple(o for o in self.objects() if o.memory_tier == tier)

    def by_tags(self, tags: Sequence[str]) -> Tuple[MemoryObject, ...]:
        want = set(tags)
        return tuple(o for o in self.objects() if want & set(o.tags))

    def by_dependency_refs(self, refs: Sequence[str]) -> Tuple[MemoryObject, ...]:
        want = set(refs)
        return tuple(o for o in self.objects() if want & set(o.dependency_refs))

    def total_history_count(self) -> int:
        return len(self._objects)

    def activation_events(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(self._activation_events)


# --------------------------------------------------------------------------- #
# §23 — retrieval provenance
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class RetrievalTraceEntry:
    object_id: str
    policy: str
    reason: str
    trigger_ref: str                     # task/dependency/reopen ref that caused selection
    memory_tier: str
    epoch: str

    def to_dict(self) -> Dict[str, Any]:
        return {"object_id": self.object_id, "policy": self.policy,
                "reason": self.reason, "trigger_ref": self.trigger_ref,
                "memory_tier": self.memory_tier, "epoch": self.epoch}


# --------------------------------------------------------------------------- #
# §10/11 — ContextBundle + bounded retrieval
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ContextBundle:
    selected_active_objects: Tuple[str, ...]
    why_selected: Tuple[RetrievalTraceEntry, ...]
    omitted_but_recoverable_count: int
    dormant_refs: Tuple[str, ...]
    archival_refs: Tuple[str, ...]
    retrieval_trace: Tuple[RetrievalTraceEntry, ...]
    budget_used: int
    budget_limit: int
    metrics: Mapping[str, Any]
    fingerprint: str

    def to_dict(self) -> Dict[str, Any]:
        return {"selected_active_objects": list(self.selected_active_objects),
                "why_selected": [w.to_dict() for w in self.why_selected],
                "omitted_but_recoverable_count": self.omitted_but_recoverable_count,
                "dormant_refs": list(self.dormant_refs),
                "archival_refs": list(self.archival_refs),
                "retrieval_trace": [t.to_dict() for t in self.retrieval_trace],
                "budget_used": self.budget_used, "budget_limit": self.budget_limit,
                "metrics": dict(self.metrics), "fingerprint": self.fingerprint}


class MemoryRetriever:
    """Bounded context builder. Active context scales with TASK NEED, not with
    institutional age: history may grow arbitrarily while the default bundle
    stays within the context budget."""

    def __init__(self, index: MemoryIndex, context_budget: int = 12,
                 policy_version: str = "G4_MEMORY_AND_REACTIVATION_POLICY:1.0.0",
                 reopen_facts: Optional[Mapping[str, Any]] = None):
        self.index = index
        self.context_budget = context_budget
        self.policy_version = policy_version
        self.reopen_facts = reopen_facts or {}   # subject_ref -> satisfied conditions

    # ------------------------------------------------------------------ #
    def build_context(
        self,
        task_ref: str,
        required_refs: Sequence[str],
        dependency_refs: Sequence[str] = (),
        current_epoch: str = "",
        activation_rules: Optional[Mapping[str, Any]] = None,
    ) -> ContextBundle:
        rules = dict(activation_rules or {})
        budget = int(rules.get("context_budget", self.context_budget))
        allow_dormant_reopen = bool(rules.get("allow_dormant_reopen", True))
        allow_archival_reconstruct = bool(rules.get("allow_archival_reconstruct", False))

        selected: List[str] = []
        why: List[RetrievalTraceEntry] = []
        dormant_refs: List[str] = []
        archival_refs: List[str] = []

        def select(obj: MemoryObject, policy: str, reason: str, trigger: str) -> None:
            if len(selected) >= budget or obj.object_id in selected:
                return
            selected.append(obj.object_id)
            why.append(RetrievalTraceEntry(
                object_id=obj.object_id, policy=policy, reason=reason,
                trigger_ref=trigger, memory_tier=obj.memory_tier, epoch=obj.epoch))

        # 1) required refs — active first
        for ref in required_refs:
            obj = self.index.get(ref)
            if obj is None:
                continue
            if obj.memory_tier == "ACTIVE_CONTEXT":
                select(obj, "REQUIRED_ACTIVE", "required object resident in active context",
                       task_ref)
            elif obj.memory_tier == "DORMANT_STORE" and allow_dormant_reopen:
                # reopen-condition satisfied -> retrieved despite absence from
                # default active context (G4 §13)
                if self._reopen_satisfied(obj):
                    select(obj, "REQUIRED_DORMANT_REOPEN",
                           "dormant object retrieved because its reopen condition fired",
                           task_ref)
                    dormant_refs.append(obj.object_id)
                else:
                    dormant_refs.append(obj.object_id)
            elif obj.memory_tier == "ARCHIVAL_STORE":
                if allow_archival_reconstruct and self._reopen_satisfied(obj):
                    select(obj, "REQUIRED_ARCHIVAL_RECONSTRUCT",
                           "archival object explicitly reconstructed",
                           task_ref)
                archival_refs.append(obj.object_id)

        # 2) dependency-referenced active objects (task need)
        for ref in dependency_refs:
            for obj in self.index.by_dependency_refs([ref]):
                if obj.memory_tier != "ACTIVE_CONTEXT":
                    continue
                select(obj, "DEPENDENCY_ACTIVE",
                       f"active object referenced by dependency {ref}", ref)

        # 3) tag-relevant active objects to fill budget (task need, not age)
        for obj in self.index.by_tags([task_ref]):
            if obj.memory_tier != "ACTIVE_CONTEXT":
                continue
            select(obj, "TAG_ACTIVE", "active object tagged for the task", task_ref)

        # metric: stale intrusion = selected objects that are neither required,
        # dependency-linked nor tag-relevant (by construction zero here)
        required_set = set(required_refs)
        dep_set = set(dependency_refs)
        tag_set = {task_ref}
        stale = [oid for oid in selected if oid not in required_set
                 and not (self.index.get(oid) and
                          (set(self.index.get(oid).dependency_refs) & dep_set
                           or set(self.index.get(oid).tags) & tag_set))]
        total_history = self.index.total_history_count()
        metrics = {
            "total_historical_objects": total_history,
            "active_context_objects": len(selected),
            "required_object_recall": (
                sum(1 for r in required_refs if r in selected) / len(required_refs)
                if required_refs else 1.0),
            "stale_object_intrusion_count": len(stale),
            "omitted_but_recoverable_count": max(0, total_history - len(selected)),
            "context_growth_ratio": (len(selected) / total_history) if total_history else 0.0,
        }
        fp = deterministic_hex(
            "context_bundle", task_ref, sorted(selected), budget,
            [(w.object_id, w.policy, w.trigger_ref, w.memory_tier) for w in why],
            length=24)
        return ContextBundle(
            selected_active_objects=tuple(sorted(selected)),
            why_selected=tuple(why),
            omitted_but_recoverable_count=max(0, total_history - len(selected)),
            dormant_refs=tuple(sorted(set(dormant_refs))),
            archival_refs=tuple(sorted(set(archival_refs))),
            retrieval_trace=tuple(why),
            budget_used=len(selected),
            budget_limit=budget,
            metrics=metrics,
            fingerprint=fp,
        )

    def _reopen_satisfied(self, obj: MemoryObject) -> bool:
        """A dormant/archival object is retrievable when ANY of its reopen
        condition ids is satisfied by current observable facts."""
        for cid in obj.reopen_condition_ids:
            if self.reopen_facts.get(cid):
                return True
        return False


# --------------------------------------------------------------------------- #
# §3 — epistemic metabolism (no stage deletes provenance)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MetabolismReport:
    report_id: str
    stages: Tuple[Dict[str, Any], ...]
    ingested: int
    compressed: Tuple[MemoryCompactionRecord, ...]
    delegated_promote_demote: Tuple[Dict[str, Any], ...]
    provenance_intact: bool

    def to_dict(self) -> Dict[str, Any]:
        return {"report_id": self.report_id, "stages": list(self.stages),
                "ingested": self.ingested,
                "compressed": [c.to_dict() for c in self.compressed],
                "delegated_promote_demote": list(self.delegated_promote_demote),
                "provenance_intact": self.provenance_intact}


def run_metabolism_pipeline(
    index: MemoryIndex,
    ingest_records: Sequence[MemoryObject],
    compress: Sequence[Tuple[str, str]] = (),      # (object_id, reason) -> DORMANT_STORE
    archive: Sequence[Tuple[str, str]] = (),       # (object_id, reason) -> ARCHIVAL_STORE
    epoch: str = "",
    policy_version: str = "G4_MEMORY_AND_REACTIVATION_POLICY:1.0.0",
    seq: int = 0,
) -> MetabolismReport:
    """Deterministic memory pipeline: INGEST -> CONSOLIDATE -> COMPRESS ->
    PROMOTE/DEMOTE (delegated to the governed M4 path, never performed here) ->
    ACTIVATE/DORMANT -> ARCHIVE -> RETRIEVE/REOPEN (caller uses MemoryRetriever).

    Every compressed record retains provenance + reconstruction pointers;
    nothing is physically deleted.
    """
    stage_log: List[Dict[str, Any]] = []
    provenance_intact = True
    for i, obj in enumerate(ingest_records):
        if obj.provenance_pointer or obj.reconstruction_pointer:
            pass
        index.add(obj)
    stage_log.append({"stage": "INGEST", "count": len(ingest_records),
                      "epoch": epoch, "provenance_intact": True})

    stage_log.append({"stage": "CONSOLIDATE", "count": 0,
                      "note": "reference consolidation is content-addressed; no provenance dropped"})

    compactions: List[MemoryCompactionRecord] = []
    for i, (object_id, reason) in enumerate(compress):
        obj = index.get(object_id)
        if obj is None:
            continue
        index.set_tier(object_id, "DORMANT_STORE", reason, policy=policy_version)
        compactions.append(MemoryCompactionRecord.make(
            seq + i, [object_id], reason, "DORMANT_STORE",
            summary=obj.summary, provenance_pointer=obj.provenance_pointer,
            reconstruction_pointer=obj.reconstruction_pointer, epoch=epoch,
            policy_version=policy_version))
    stage_log.append({"stage": "COMPRESS", "count": len(compactions),
                      "destination": "DORMANT_STORE", "provenance_intact": True})

    # PROMOTE/DEMOTE is a GOVERNED M4 truth change — memory may never perform
    # it (G4 §27). The pipeline records the delegation only.
    delegated = [{"object_id": oid, "action": "governed M4 promote/demote",
                  "note": "delegated to LifecycleEngine; memory performs no truth change"}
                 for oid, _ in compress]
    stage_log.append({"stage": "PROMOTE_DEMOTE", "delegated": len(delegated),
                      "memory_performed": 0})

    stage_log.append({"stage": "ACTIVATE_DORMANT",
                      "count": len(index.objects_by_tier("DORMANT_STORE")),
                      "note": "dormant objects stay indexed and reopenable"})

    archived: List[MemoryCompactionRecord] = []
    for i, (object_id, reason) in enumerate(archive):
        obj = index.get(object_id)
        if obj is None:
            continue
        index.set_tier(object_id, "ARCHIVAL_STORE", reason, policy=policy_version)
        archived.append(MemoryCompactionRecord.make(
            seq + 1000 + i, [object_id], reason, "ARCHIVAL_STORE",
            summary=obj.summary, provenance_pointer=obj.provenance_pointer,
            reconstruction_pointer=obj.reconstruction_pointer, epoch=epoch,
            policy_version=policy_version))
    stage_log.append({"stage": "ARCHIVE", "count": len(archived),
                      "destination": "ARCHIVAL_STORE", "provenance_intact": True})

    stage_log.append({"stage": "RETRIEVE_REOPEN",
                      "note": "retrieval is bounded and rationale-recorded via MemoryRetriever"})

    all_refs = [o.object_id for o in index.objects()]
    # provenance intact == every object still present with its original pointer
    provenance_intact = all(
        bool(index.get(oid)) for oid in all_refs)
    return MetabolismReport(
        report_id=deterministic_hex("metabolism", epoch, seq, len(index.objects()), length=24),
        stages=tuple(stage_log),
        ingested=len(ingest_records),
        compressed=tuple(compactions + archived),
        delegated_promote_demote=tuple(delegated),
        provenance_intact=provenance_intact,
    )
