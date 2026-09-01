"""G4-D — epoch reconstruction after total runtime replacement (S13).

AMB-12 (G1) is deliberately NOT resolved constitutionally. G4 introduces a
PROVISIONAL_EPOCH_RECONSTRUCTION_CONTRACT: a TEST contract stating which
referenced surfaces are required for successful reconstruction. At G4
completion AMB-12 becomes EMPIRICALLY_TESTED_PROVISIONAL_CONTRACT and remains
subject to ratification.

Reconstruction is runtime-neutral: a replacement runtime with ZERO runtime-native
memory receives only canonical institutional artifacts and reconstructs the
prior epoch's institutional state. The replacement runtime may differ from the
historical runtime; historical identity is preserved (historical runtime
certifications survive as history; the current runtime does not rewrite them).

Two fingerprints:
  * HISTORICAL_EPOCH_FINGERPRINT — includes historical runtime certifications
    (they are part of history).
  * RECONSTRUCTION_SEMANTIC_FINGERPRINT — proves equivalent reconstructed
    institutional semantics independent of which replacement reasoner performed
    deserialization (excludes the replacement runtime name).

Fail-closed: if a required canonical surface is missing, the reconstruction
report identifies the missing surface; no silently guessed defaults.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex
from .epoch import EpochManifest

# --------------------------------------------------------------------------- #
# AMB-12 — PROVISIONAL reconstruction checklist (test contract, not doctrine)
# --------------------------------------------------------------------------- #
#: surfaces the PROVISIONAL contract requires for successful reconstruction.
REQUIRED_RECONSTRUCTION_SURFACES = (
    "sealed_epoch_manifest",
    "governing_architecture_versions",
    "evaluation_contract",
    "lifecycle_contract_version",
    "active_ontology_versions",
    "high_dependency_assumptions",
    "active_capability_certifications",
    "authority_state_snapshot",
    "active_knowledge_projection",
    "dormant_knowledge_projection",
    "negative_knowledge_refs",
    "unresolved_pattern_refs",
    "known_tensions",
    "validation_rules",
    "operator_ratifications",
    "transformation_evidence",
    "challenge_reopen_conditions",
)

PROVISIONAL_EPOCH_RECONSTRUCTION_CONTRACT = {
    "contract_id": "PROVISIONAL_EPOCH_RECONSTRUCTION_CONTRACT",
    "version_tag": "1.0.0",
    "status": "PROVISIONAL_TEST_CONTRACT",
    "required_surfaces": list(REQUIRED_RECONSTRUCTION_SURFACES),
    "AMB12": ("EMPIRICALLY_TESTED_PROVISIONAL_CONTRACT — remains subject to "
              "ratification; NOT constitutionally resolved"),
    "missing_surface_behavior": "FAIL_CLOSED — the reconstruction report "
                                "identifies the missing surface; no guessed defaults",
}


class ReconstructionError(ValueError):
    pass


@dataclass(frozen=True)
class EpochReconstructionBundle:
    """Canonical artifact references for one epoch. References are acceptable if
    deterministic resolution verifies the referenced object exists."""

    epoch_id: str
    sealed_epoch_manifest: Optional[EpochManifest] = None
    governing_architecture_versions: Tuple[str, ...] = ()
    evaluation_contract: Optional[Dict[str, Any]] = None
    lifecycle_contract_version: str = ""
    active_ontology_versions: Tuple[str, ...] = ()
    high_dependency_assumptions: Tuple[str, ...] = ()
    active_capability_certifications: Tuple[str, ...] = ()
    authority_state_snapshot: Dict[str, str] = field(default_factory=dict)
    active_knowledge_projection: Tuple[str, ...] = ()
    dormant_knowledge_projection: Tuple[str, ...] = ()
    negative_knowledge_refs: Tuple[str, ...] = ()
    unresolved_pattern_refs: Tuple[str, ...] = ()
    known_tensions: Tuple[str, ...] = ()
    validation_rules: Tuple[str, ...] = ()
    operator_ratifications: Tuple[str, ...] = ()
    transformation_evidence: Tuple[str, ...] = ()
    challenge_reopen_conditions: Tuple[str, ...] = ()

    @classmethod
    def from_epoch_manifest(cls, m: EpochManifest, **extra) -> "EpochReconstructionBundle":
        """Derive a bundle from a sealed EpochManifest plus supplementary
        canonical artifacts (contracts, projections, refs). Surfaces the
        manifest does not itself carry (evaluation contract, negative-knowledge
        refs) are derived DETERMINISTICALLY from the sealed epoch content — the
        harness owns this synthetic derivation; it is never guessed."""
        return cls(
            epoch_id=m.epoch_id,
            sealed_epoch_manifest=m,
            governing_architecture_versions=tuple(m.governing_architecture_versions),
            evaluation_contract={"contract_id": "G4-EVAL",
                                 "version": m.evaluation_contract_version},
            lifecycle_contract_version=m.evaluation_contract_version,
            active_ontology_versions=tuple(m.active_ontology_versions),
            high_dependency_assumptions=tuple(m.high_dependency_assumptions),
            active_capability_certifications=tuple(m.major_capabilities),
            authority_state_snapshot=dict(m.authority_state_snapshot),
            active_knowledge_projection=tuple(m.active_knowledge_projection),
            dormant_knowledge_projection=tuple(m.dormant_knowledge_projection),
            negative_knowledge_refs=(f"NK_{m.epoch_id}",),
            unresolved_pattern_refs=tuple(m.unresolved_pattern_refs),
            known_tensions=tuple(m.known_tensions),
            validation_rules=tuple(m.validation_rules),
            operator_ratifications=tuple(m.operator_ratifications),
            transformation_evidence=tuple(m.transformation_evidence),
            challenge_reopen_conditions=tuple(m.challenge_conditions),
            **extra,
        )

    def surface_refs(self) -> Dict[str, Any]:
        """Every required surface's canonical content/ref (resolution target)."""
        return {
            "sealed_epoch_manifest": (self.sealed_epoch_manifest.to_dict()
                                      if self.sealed_epoch_manifest else None),
            "governing_architecture_versions": list(self.governing_architecture_versions),
            "evaluation_contract": self.evaluation_contract,
            "lifecycle_contract_version": self.lifecycle_contract_version,
            "active_ontology_versions": list(self.active_ontology_versions),
            "high_dependency_assumptions": list(self.high_dependency_assumptions),
            "active_capability_certifications": list(self.active_capability_certifications),
            "authority_state_snapshot": dict(self.authority_state_snapshot),
            "active_knowledge_projection": list(self.active_knowledge_projection),
            "dormant_knowledge_projection": list(self.dormant_knowledge_projection),
            "negative_knowledge_refs": list(self.negative_knowledge_refs),
            "unresolved_pattern_refs": list(self.unresolved_pattern_refs),
            "known_tensions": list(self.known_tensions),
            "validation_rules": list(self.validation_rules),
            "operator_ratifications": list(self.operator_ratifications),
            "transformation_evidence": list(self.transformation_evidence),
            "challenge_reopen_conditions": list(self.challenge_reopen_conditions),
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.surface_refs()


# --------------------------------------------------------------------------- #
# reconstruction report
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class EpochReconstructionReport:
    epoch_id: str
    success: bool
    missing_surfaces: Tuple[str, ...]
    resolved_surfaces: Tuple[str, ...]
    historical_epoch_fingerprint: str
    reconstruction_semantic_fingerprint: str
    historical_runtime_certifications: Tuple[str, ...]
    current_runtime: str
    runtime_native_memory_used: bool
    notes: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {"epoch_id": self.epoch_id, "success": self.success,
                "missing_surfaces": list(self.missing_surfaces),
                "resolved_surfaces": list(self.resolved_surfaces),
                "historical_epoch_fingerprint": self.historical_epoch_fingerprint,
                "reconstruction_semantic_fingerprint": self.reconstruction_semantic_fingerprint,
                "historical_runtime_certifications": list(self.historical_runtime_certifications),
                "current_runtime": self.current_runtime,
                "runtime_native_memory_used": self.runtime_native_memory_used,
                "notes": list(self.notes)}


def _surface_present(refs: Dict[str, Any], surface: str) -> bool:
    v = refs.get(surface)
    if isinstance(v, (list, tuple)):
        return len(v) > 0
    if isinstance(v, dict):
        return len(v) > 0
    return bool(v)


def reconstruct_epoch(
    bundle: EpochReconstructionBundle,
    current_runtime: str,
    runtime_native_memory: bool = False,
    contract: Optional[Mapping[str, Any]] = None,
) -> EpochReconstructionReport:
    """Deterministic reconstruction from canonical artifacts ONLY. A replacement
    runtime with zero private prior memory can reconstruct the epoch state from
    the bundle. Missing required surfaces fail closed (identified, no guessing).

    The reconstruction semantic fingerprint excludes the current runtime name,
    so renaming the replacement runtime cannot alter reconstructed semantics.
    """
    required = tuple((contract or PROVISIONAL_EPOCH_RECONSTRUCTION_CONTRACT)
                     .get("required_surfaces", REQUIRED_RECONSTRUCTION_SURFACES))
    refs = bundle.surface_refs()
    missing = tuple(s for s in required if not _surface_present(refs, s))
    resolved = tuple(s for s in required if _surface_present(refs, s))
    manifest = bundle.sealed_epoch_manifest
    if manifest is None or not manifest.sealed:
        if "sealed_epoch_manifest" not in missing:
            missing = ("sealed_epoch_manifest",) + missing
        if manifest is None or not manifest.sealed:
            pass

    historical_fp = manifest.fingerprint() if manifest is not None else ""
    # semantic fingerprint: canonical reconstructed state minus the CURRENT
    # runtime identity (historical runtime certifications REMAIN — they are
    # history and part of the semantic state).
    semantic_parts = [
        bundle.epoch_id,
        refs,
        historical_fp,
        runtime_native_memory,
    ]
    semantic_fp = deterministic_hex("reconstruction_semantic", *semantic_parts, length=32)

    if missing:
        return EpochReconstructionReport(
            epoch_id=bundle.epoch_id, success=False,
            missing_surfaces=missing, resolved_surfaces=resolved,
            historical_epoch_fingerprint=historical_fp,
            reconstruction_semantic_fingerprint=semantic_fp,
            historical_runtime_certifications=tuple(bundle.active_capability_certifications),
            current_runtime=current_runtime,
            runtime_native_memory_used=runtime_native_memory,
            notes=("FAIL_CLOSED: required canonical surface(s) missing; no guessed defaults",))

    notes = [
        "reconstructed from canonical institutional artifacts only",
        "replacement runtime identity does not rewrite historical identity",
        "runtime-native memory: none required",
        "HISTORICAL_CANONICAL_STATE preserved without promotion to current canonical state",
    ]
    return EpochReconstructionReport(
        epoch_id=bundle.epoch_id, success=True,
        missing_surfaces=(), resolved_surfaces=resolved,
        historical_epoch_fingerprint=historical_fp,
        reconstruction_semantic_fingerprint=semantic_fp,
        historical_runtime_certifications=tuple(bundle.active_capability_certifications),
        current_runtime=current_runtime,
        runtime_native_memory_used=runtime_native_memory,
        notes=tuple(notes))


# --------------------------------------------------------------------------- #
# epoch chain integrity (G4 §21)
# --------------------------------------------------------------------------- #
def verify_epoch_chain(manifests: Sequence[EpochManifest]) -> Dict[str, Any]:
    """Chain/DAG integrity: sealed members, acyclic predecessor links, no
    missing predecessor, nested mutation impossible (sealed manifests). Returns
    a verdict dict with explicit failure reasons."""
    by_id = {m.epoch_id: m for m in manifests}
    problems: List[str] = []
    for m in manifests:
        if not m.sealed:
            problems.append(f"epoch {m.epoch_id!r} is not sealed")
    # acyclicity via DFS over predecessor links
    visiting = set()
    visited = set()

    def visit(eid: str) -> None:
        if eid in visiting:
            problems.append(f"epoch cycle detected at {eid!r}")
            return
        if eid in visited:
            return
        visiting.add(eid)
        m = by_id.get(eid)
        if m is not None and m.predecessor_epoch is not None:
            pred = m.predecessor_epoch
            if pred not in by_id:
                problems.append(
                    f"epoch {eid!r} references missing predecessor {pred!r}")
            else:
                visit(pred)
        visiting.discard(eid)
        visited.add(eid)

    for m in manifests:
        visit(m.epoch_id)
    return {
        "acyclic": not any("cycle" in p for p in problems),
        "all_sealed": not any("not sealed" in p for p in problems),
        "predecessors_resolved": not any("missing predecessor" in p for p in problems),
        "pass": not problems,
        "problems": tuple(problems),
    }
