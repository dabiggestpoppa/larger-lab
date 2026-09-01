"""EpochManifest (A-010 §14). Institutional time may be queried by epoch.

G1 validates only serialization / reconstruction-round-trip semantics; the
operational reconstruction *checklist* for which graphs must rehydrate is G4 work
(AMB-12 stays open — see engine/reconstruction.py PROVISIONAL contract).

G4-P0-D: an EpochManifest is a SNAPSHOT with explicit BUILDING -> SEALED
semantics. Once sealed:

  * the manifest is deeply immutable — nested list/dict aliases cannot mutate
    it (internal contents are deep-copied at seal, and to_dict returns deep
    copies);
  * direct attribute mutation of semantic fields raises EpochManifestError;
  * the fingerprint is frozen and byte-stable;
  * future epochs derive from a predecessor (successor_of) WITHOUT rewriting it.
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
    "active_ontology_versions", "high_dependency_assumptions",
    "active_runtime_certifications", "major_capabilities", "known_tensions",
    "unresolved_pattern_refs", "active_knowledge_projection",
    "dormant_knowledge_projection", "validation_rules",
    "authority_state_snapshot", "operator_ratifications",
    "transformation_evidence", "challenge_conditions",
)


@dataclass
class EpochManifest:
    epoch_id: str
    schema_version: str = "1.0.0"
    start_cause: str = ""
    predecessor_epoch: Optional[str] = None
    governing_architecture_versions: List[str] = field(default_factory=list)
    evaluation_contract_version: str = ""
    active_ontology_versions: List[str] = field(default_factory=list)
    high_dependency_assumptions: List[str] = field(default_factory=list)
    active_runtime_certifications: List[str] = field(default_factory=list)
    major_capabilities: List[str] = field(default_factory=list)
    known_tensions: List[str] = field(default_factory=list)
    unresolved_pattern_refs: List[str] = field(default_factory=list)
    active_knowledge_projection: List[str] = field(default_factory=list)
    dormant_knowledge_projection: List[str] = field(default_factory=list)
    validation_rules: List[str] = field(default_factory=list)
    authority_state_snapshot: Dict[str, str] = field(default_factory=dict)
    operator_ratifications: List[str] = field(default_factory=list)
    transformation_evidence: List[str] = field(default_factory=list)
    challenge_conditions: List[str] = field(default_factory=list)   # T16: epoch != dogma
    # --- snapshot semantics (not part of the semantic content) ------------- #
    _sealed: bool = field(default=False, init=False, repr=False)
    _fingerprint: str = field(default="", init=False, repr=False)

    @classmethod
    def make(cls, seq, epoch_id=None, **kw):
        return cls(
            epoch_id=epoch_id or deterministic_hex("epoch", seq),
            **kw,
        )

    # ------------------------------------------------------------------ #
    # sealing (G4-P0-D)
    # ------------------------------------------------------------------ #
    @property
    def sealed(self) -> bool:
        return self._sealed

    def seal(self) -> "EpochManifest":
        """Deep-freeze the snapshot. After this call the semantic contents can
        never change silently: internal mutable fields are deep-copied so
        pre-seal external aliases cannot reach them, and the fingerprint is
        frozen."""
        if not self._sealed:
            for f in SEMANTIC_FIELDS:
                object.__setattr__(self, f, copy.deepcopy(getattr(self, f)))
            object.__setattr__(self, "_sealed", True)
            object.__setattr__(self, "_fingerprint", self._compute_fingerprint())
        return self

    def __setattr__(self, name, value) -> None:
        if getattr(self, "_sealed", False) and name in SEMANTIC_FIELDS:
            raise EpochManifestError(
                f"epoch manifest {self.epoch_id!r} is SEALED; semantic field "
                f"{name!r} cannot be mutated (derive a successor instead)")
        object.__setattr__(self, name, value)

    def __getattribute__(self, name):
        """After seal, semantic field reads return deep copies: in-place nested
        mutation (list.append / dict[key]=) therefore cannot alter the sealed
        snapshot. Reads of non-semantic machinery (sealed, fingerprint, methods)
        are unaffected."""
        if name in SEMANTIC_FIELDS:
            try:
                sealed = object.__getattribute__(self, "_sealed")
            except AttributeError:
                sealed = False
            if sealed:
                return copy.deepcopy(object.__getattribute__(self, name))
        return object.__getattribute__(self, name)

    def _compute_fingerprint(self) -> str:
        return deterministic_hex("epoch_fp", self.to_dict())

    def fingerprint(self) -> str:
        """Frozen after seal; computed deterministically from content before."""
        return self._fingerprint if self._sealed else self._compute_fingerprint()

    @classmethod
    def successor_of(cls, predecessor: "EpochManifest", epoch_id: str,
                     start_cause: str = "", **overrides) -> "EpochManifest":
        """Derive a NEW epoch from a sealed predecessor without rewriting it.
        Projection/certification lists are deep-copied from the predecessor as
        the initial content; overrides replace individual fields."""
        base = predecessor.to_dict()          # deep copies
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
        return cls(**data)
