"""EpochManifest (A-010 §14). Institutional time may be queried by epoch.

G1 validates only serialization / reconstruction-round-trip semantics; the
operational reconstruction *checklist* for which graphs must rehydrate is G4 work
(AMB-12 stays open — see engine/reconstruction.py PROVISIONAL contract).

G4-P0-D / G4R-10: an EpochManifest is a SNAPSHOT with explicit BUILDING -> SEALED
semantics. Once sealed:

  * the manifest is deeply immutable — nested list/dict aliases cannot mutate
    it (internal contents are deep-copied at seal into a frozen internal
    snapshot; reads return deep copies of the snapshot);
  * SEALED is MONOTONIC: an epoch can never unseal itself, and the fingerprint
    can never be overwritten — the guard keys on the internal snapshot, not on
    a mutable `_sealed` convention, so toggling `_sealed` (even via
    object.__setattr__) cannot re-open the semantic snapshot;
  * future epochs derive from a predecessor (successor_of) WITHOUT rewriting it.

G4R-14: evaluation_contract_version and lifecycle_contract_version are separate
contracts and are carried separately (never inferred one from the other). The
manifest may also reference an external authority snapshot artifact
(authority_snapshot_ref) and explicit negative-knowledge record refs so
reconstruction never has to synthesize them.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .base import deterministic_hex


class EpochManifestError(ValueError):
    pass


SEMANTIC_FIELDS = (
    "epoch_id", "schema_version", "start_cause", "predecessor_epoch",
    "governing_architecture_versions", "evaluation_contract_version",
    "lifecycle_contract_version", "active_ontology_versions",
    "high_dependency_assumptions", "active_runtime_certifications",
    "major_capabilities", "known_tensions", "unresolved_pattern_refs",
    "active_knowledge_projection", "dormant_knowledge_projection",
    "negative_knowledge_refs", "validation_rules",
    "authority_state_snapshot", "authority_snapshot_ref",
    "operator_ratifications", "transformation_evidence", "challenge_conditions",
)


@dataclass
class EpochManifest:
    epoch_id: str
    schema_version: str = "1.0.0"
    start_cause: str = ""
    predecessor_epoch: Optional[str] = None
    governing_architecture_versions: List[str] = field(default_factory=list)
    evaluation_contract_version: str = ""
    lifecycle_contract_version: str = ""          # G4R-14: separate from evaluation
    active_ontology_versions: List[str] = field(default_factory=list)
    high_dependency_assumptions: List[str] = field(default_factory=list)
    active_runtime_certifications: List[str] = field(default_factory=list)
    major_capabilities: List[str] = field(default_factory=list)
    known_tensions: List[str] = field(default_factory=list)
    unresolved_pattern_refs: List[str] = field(default_factory=list)
    active_knowledge_projection: List[str] = field(default_factory=list)
    dormant_knowledge_projection: List[str] = field(default_factory=list)
    negative_knowledge_refs: List[str] = field(default_factory=list)   # G4R-11
    validation_rules: List[str] = field(default_factory=list)
    authority_state_snapshot: Dict[str, str] = field(default_factory=dict)
    authority_snapshot_ref: str = ""              # G4R-11: external artifact ref
    operator_ratifications: List[str] = field(default_factory=list)
    transformation_evidence: List[str] = field(default_factory=list)
    challenge_conditions: List[str] = field(default_factory=list)   # T16: epoch != dogma
    # --- snapshot machinery (not part of the semantic content) ------------- #
    _sealed: bool = field(default=False, init=False, repr=False)
    _fingerprint: str = field(default="", init=False, repr=False)
    _snapshot: Optional[Dict[str, object]] = field(default=None, init=False, repr=False)

    @classmethod
    def make(cls, seq, epoch_id=None, **kw):
        return cls(
            epoch_id=epoch_id or deterministic_hex("epoch", seq),
            **kw,
        )

    # ------------------------------------------------------------------ #
    # sealing (G4-P0-D / G4R-10 — monotonic, snapshot-anchored)
    # ------------------------------------------------------------------ #
    @property
    def sealed(self) -> bool:
        return self._sealed

    def seal(self) -> "EpochManifest":
        """Deep-freeze the snapshot. After this call the semantic contents can
        never change: internal mutable fields are deep-copied into a frozen
        internal snapshot and reads always come from that snapshot. The seal is
        MONOTONIC — the internal snapshot is the seal token."""
        if self._snapshot is None:
            snap = {f: copy.deepcopy(getattr(self, f)) for f in SEMANTIC_FIELDS}
            object.__setattr__(self, "_snapshot", snap)
            object.__setattr__(self, "_sealed", True)
            object.__setattr__(self, "_fingerprint",
                               deterministic_hex("epoch_fp", snap, length=40))
        return self

    def __setattr__(self, name, value) -> None:
        if name in SEMANTIC_FIELDS:
            if getattr(self, "_snapshot", None) is not None:
                raise EpochManifestError(
                    f"epoch manifest {self.epoch_id!r} is SEALED; semantic field "
                    f"{name!r} cannot be mutated (derive a successor instead)")
            object.__setattr__(self, name, value)
            return
        if name == "_sealed":
            if getattr(self, "_snapshot", None) is not None and value is not True:
                raise EpochManifestError(
                    f"epoch manifest {self.epoch_id!r} is SEALED; SEALED is "
                    f"monotonic and cannot be toggled off")
        if name == "_fingerprint":
            if (getattr(self, "_snapshot", None) is not None
                    and value != getattr(self, "_fingerprint", "")):
                raise EpochManifestError(
                    f"epoch manifest {self.epoch_id!r} fingerprint is frozen once sealed")
        object.__setattr__(self, name, value)

    def __getattribute__(self, name):
        """After seal, semantic field reads return deep copies of the frozen
        internal snapshot: in-place nested mutation (list.append / dict[key]=)
        therefore cannot alter the sealed snapshot, even if the mutable `_sealed`
        flag were forced off — the snapshot itself is the source of truth."""
        if name in SEMANTIC_FIELDS:
            try:
                snap = object.__getattribute__(self, "_snapshot")
            except AttributeError:
                snap = None
            if snap is not None:
                return copy.deepcopy(snap[name])
        return object.__getattribute__(self, name)

    def _compute_fingerprint(self) -> str:
        return deterministic_hex("epoch_fp", self.to_dict(), length=40)

    def fingerprint(self) -> str:
        """Frozen after seal; computed deterministically from content before."""
        return self._fingerprint if self._snapshot is not None else self._compute_fingerprint()

    @classmethod
    def successor_of(cls, predecessor: "EpochManifest", epoch_id: str,
                     start_cause: str = "", **overrides) -> "EpochManifest":
        """Derive a NEW epoch from a sealed predecessor without rewriting it.
        Projection/certification lists are deep-copied from the predecessor as
        the initial content; overrides replace individual fields."""
        base = predecessor.to_dict()          # deep copies (snapshot-backed if sealed)
        base.update({
            "epoch_id": epoch_id,
            "predecessor_epoch": predecessor.epoch_id,
            "start_cause": start_cause or predecessor.start_cause,
        })
        base.update(overrides)
        return cls(**base)

    # ------------------------------------------------------------------ #
    # serialization — round-trip lossless (G1); returns deep copies after seal
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        return {f: copy.deepcopy(getattr(self, f)) for f in SEMANTIC_FIELDS}

    @classmethod
    def from_dict(cls, data: dict) -> "EpochManifest":
        return cls(**{k: v for k, v in data.items() if k in SEMANTIC_FIELDS})
