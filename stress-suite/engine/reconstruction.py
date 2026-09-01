"""G4-D/G4R — epoch reconstruction after total runtime replacement (S13).

AMB-12 (G1) is deliberately NOT resolved constitutionally. G4 introduces a
PROVISIONAL_EPOCH_RECONSTRUCTION_CONTRACT: a TEST contract stating which
referenced surfaces are required for successful reconstruction. At G4
completion AMB-12 becomes EMPIRICALLY_TESTED_PROVISIONAL_CONTRACT and remains
subject to ratification.

G4R-11/12/13/14/20 — reconstruction is REGISTRY-BACKED, not synthesized:
  * A CanonicalArtifactRegistry holds ACTUAL pre-existing canonical fixture
    artifacts (sealed manifests, evaluation contracts, lifecycle contracts,
    ontology refs, certifications, authority snapshots, knowledge records,
    negative-knowledge records, unresolved patterns, validation rules,
    operator ratifications, transformation evidence, reopen conditions).
  * EpochReconstructionBundle carries REFERENCES into that registry. A manifest
    alone is NOT sufficient when the PROVISIONAL contract requires external
    surfaces: missing registry artifacts FAIL CLOSED and are identified; the
    bundle NEVER invents {"version": "..."} placeholders during reconstruction.
  * evaluation_contract_version and lifecycle_contract_version are SEPARATE
    machines and are resolved separately — the lifecycle version is never
    inferred from the evaluation version (G4R-14).
  * Cross-artifact consistency is enforced (G4R-13): resolved evaluation /
    lifecycle contract versions must equal the manifest's declared versions;
    the resolved authority snapshot's fingerprint must equal the manifest's
    inline authority snapshot; knowledge projections must resolve to records
    with compatible historical epochs.
  * Content is validated per surface (G4R-20) — a non-empty {"foo": "bar"} can
    never satisfy an evaluation-contract surface.

G4R-15 — runtime-neutral honesty: when the replacement runtime used
runtime-native memory, reconstruction may still produce a diagnostic report,
but reconstruction_evidence_qualified is False and the run does NOT count as
evidence for the S13 runtime-neutral reconstruction pass.

Two fingerprints:
  * HISTORICAL_EPOCH_FINGERPRINT — includes historical runtime certifications
    (they are part of history).
  * RECONSTRUCTION_SEMANTIC_FINGERPRINT — proves equivalent reconstructed
    institutional semantics independent of which replacement reasoner performed
    deserialization (excludes the replacement runtime name).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex
from .epoch import EpochManifest

# --------------------------------------------------------------------------- #
# AMB-12 — PROVISIONAL reconstruction checklist (test contract, not doctrine)
# --------------------------------------------------------------------------- #
REQUIRED_RECONSTRUCTION_SURFACES = (
    "sealed_epoch_manifest",
    "governing_architecture_versions",
    "evaluation_contract",
    "lifecycle_contract",
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
    "version_tag": "1.1.0",
    "status": "PROVISIONAL_TEST_CONTRACT",
    "required_surfaces": list(REQUIRED_RECONSTRUCTION_SURFACES),
    "AMB12": ("EMPIRICALLY_TESTED_PROVISIONAL_CONTRACT — remains subject to "
              "ratification; NOT constitutionally resolved"),
    "missing_surface_behavior": "FAIL_CLOSED — the reconstruction report "
                                "identifies the missing surface; no guessed defaults",
    "registry_requirement": ("surfaces marked EXTERNAL must resolve to "
                             "pre-existing canonical artifacts in the "
                             "CanonicalArtifactRegistry; a manifest alone is "
                             "insufficient (G4R-12)"),
}


class ReconstructionError(ValueError):
    pass


# --------------------------------------------------------------------------- #
# CanonicalArtifactRegistry (G4R-11) — pre-existing canonical fixture truth
# --------------------------------------------------------------------------- #
ARTIFACT_KINDS = (
    "SEALED_EPOCH_MANIFEST", "EVALUATION_CONTRACT", "LIFECYCLE_CONTRACT",
    "ONTOLOGY", "HIGH_DEPENDENCY_ASSUMPTION", "RUNTIME_CERTIFICATION",
    "CAPABILITY_CERTIFICATION", "AUTHORITY_SNAPSHOT", "KNOWLEDGE_RECORD",
    "NEGATIVE_KNOWLEDGE", "UNRESOLVED_PATTERN", "VALIDATION_RULE",
    "OPERATOR_RATIFICATION", "TRANSFORMATION_EVIDENCE", "REOPEN_CONDITION",
)


@dataclass(frozen=True)
class CanonicalArtifact:
    kind: str
    artifact_id: str
    content: Mapping[str, Any]
    fingerprint: str
    epoch_id: str = ""

    def __post_init__(self) -> None:
        if self.kind not in ARTIFACT_KINDS:
            raise ReconstructionError(f"unknown canonical artifact kind {self.kind!r}")
        if not self.artifact_id:
            raise ReconstructionError("canonical artifact requires a non-empty id")

    @classmethod
    def make(cls, kind: str, artifact_id: str, content: Mapping[str, Any],
             epoch_id: str = "") -> "CanonicalArtifact":
        return cls(kind=kind, artifact_id=artifact_id, content=dict(content),
                   fingerprint=deterministic_hex("artifact", kind, artifact_id, content),
                   epoch_id=epoch_id)

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "artifact_id": self.artifact_id,
                "content": dict(self.content), "fingerprint": self.fingerprint,
                "epoch_id": self.epoch_id}


class CanonicalArtifactRegistry:
    """kind+id -> canonical artifact, with duplicate rejection."""

    def __init__(self) -> None:
        self._by_key: Dict[Tuple[str, str], CanonicalArtifact] = {}

    def register(self, artifact: CanonicalArtifact) -> None:
        key = (artifact.kind, artifact.artifact_id)
        if key in self._by_key:
            raise ReconstructionError(
                f"duplicate canonical artifact {artifact.artifact_id!r} ({artifact.kind})")
        self._by_key[key] = artifact

    def register_manifest(self, manifest: EpochManifest) -> None:
        if not manifest.sealed:
            manifest.seal()
        self.register(CanonicalArtifact.make(
            "SEALED_EPOCH_MANIFEST", manifest.epoch_id, manifest.to_dict(),
            epoch_id=manifest.epoch_id))

    def has(self, kind: str, artifact_id: str) -> bool:
        return (kind, artifact_id) in self._by_key

    def resolve(self, kind: str, artifact_id: str) -> CanonicalArtifact:
        key = (kind, artifact_id)
        if key not in self._by_key:
            raise ReconstructionError(
                f"canonical artifact {artifact_id!r} ({kind}) is not registered")
        return self._by_key[key]

    def resolve_optional(self, kind: str, artifact_id: str) -> Optional[CanonicalArtifact]:
        return self._by_key.get((kind, artifact_id))

    def register_fixture(self, data: Mapping[str, Any]) -> None:
        self.register(CanonicalArtifact.make(
            kind=str(data["kind"]), artifact_id=str(data["artifact_id"]),
            content=dict(data.get("content", {})),
            epoch_id=str(data.get("epoch_id", ""))))

    def all_ids(self) -> Tuple[str, ...]:
        return tuple(sorted(f"{k}:{i}" for (k, i) in self._by_key))


# --------------------------------------------------------------------------- #
# EpochReconstructionBundle — REFERENCES into the registry, never synthesized
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class EpochReconstructionBundle:
    epoch_id: str
    sealed_epoch_manifest: Optional[EpochManifest]
    # manifest-inline surfaces (from the sealed manifest itself)
    governing_architecture_versions: Tuple[str, ...] = ()
    known_tensions: Tuple[str, ...] = ()
    # EXTERNAL registry references (must resolve in CanonicalArtifactRegistry)
    evaluation_contract_ref: str = ""
    lifecycle_contract_ref: str = ""
    authority_snapshot_ref: str = ""
    ontology_refs: Tuple[str, ...] = ()
    high_dependency_assumption_refs: Tuple[str, ...] = ()
    certification_refs: Tuple[str, ...] = ()
    capability_certification_refs: Tuple[str, ...] = ()
    active_knowledge_refs: Tuple[str, ...] = ()
    dormant_knowledge_refs: Tuple[str, ...] = ()
    negative_knowledge_refs: Tuple[str, ...] = ()
    unresolved_pattern_refs: Tuple[str, ...] = ()
    validation_rule_refs: Tuple[str, ...] = ()
    operator_ratification_refs: Tuple[str, ...] = ()
    transformation_evidence_refs: Tuple[str, ...] = ()
    challenge_reopen_condition_refs: Tuple[str, ...] = ()

    @classmethod
    def for_manifest(cls, m: EpochManifest) -> "EpochReconstructionBundle":
        """Build the reference bundle from a sealed manifest. Refs are derived
        deterministically FROM the manifest's declared versions/ids; resolution
        happens later against the registry, so missing external artifacts are
        REPORTED as missing surfaces rather than guessed."""
        if not m.sealed:
            raise ReconstructionError("cannot reconstruct from an unsealed manifest")
        return cls(
            epoch_id=m.epoch_id,
            sealed_epoch_manifest=m,
            governing_architecture_versions=tuple(m.governing_architecture_versions),
            known_tensions=tuple(m.known_tensions),
            evaluation_contract_ref=m.evaluation_contract_version,
            lifecycle_contract_ref=m.lifecycle_contract_version,
            authority_snapshot_ref=m.authority_snapshot_ref or f"AUTH_SNAP:{m.epoch_id}",
            ontology_refs=tuple(m.active_ontology_versions),
            high_dependency_assumption_refs=tuple(m.high_dependency_assumptions),
            certification_refs=tuple(m.active_runtime_certifications),
            capability_certification_refs=tuple(m.major_capabilities),
            active_knowledge_refs=tuple(m.active_knowledge_projection),
            dormant_knowledge_refs=tuple(m.dormant_knowledge_projection),
            negative_knowledge_refs=tuple(m.negative_knowledge_refs),
            unresolved_pattern_refs=tuple(m.unresolved_pattern_refs),
            validation_rule_refs=tuple(m.validation_rules),
            operator_ratification_refs=tuple(m.operator_ratifications),
            transformation_evidence_refs=tuple(m.transformation_evidence),
            challenge_reopen_condition_refs=tuple(m.challenge_conditions),
        )


# --------------------------------------------------------------------------- #
# per-surface content validation (G4R-20) + resolution (G4R-11/12/13)
# --------------------------------------------------------------------------- #
def _kind_validator(kind: str, required_fields: Sequence[str],
                    content: Mapping[str, Any]) -> Optional[str]:
    missing = [f for f in required_fields if not content.get(f)]
    if missing:
        return f"{kind} artifact missing mandatory field(s): {missing}"
    return None


def _resolve_surface(refs: Mapping[str, Any], registry: CanonicalArtifactRegistry,
                     surface: str, kind: str, artifact_id: str,
                     required_fields: Sequence[str],
                     content_transform=None) -> Tuple[bool, Optional[str], Any]:
    """Resolve one external artifact surface. Returns (ok, failure_reason, artifact)."""
    if not artifact_id:
        return False, f"surface '{surface}': no {kind} ref declared by the manifest", None
    art = registry.resolve_optional(kind, artifact_id)
    if art is None:
        return False, f"surface '{surface}': canonical {kind} artifact " \
                      f"{artifact_id!r} is not registered (manifest alone is insufficient)", None
    violation = _kind_validator(kind, required_fields, art.content)
    if violation is not None:
        return False, f"surface '{surface}': {violation}", None
    if content_transform is not None:
        err = content_transform(art, refs)
        if err:
            return False, err, None
    return True, None, art


def _resolve_ref_list(refs: Mapping[str, Any], registry: CanonicalArtifactRegistry,
                      surface: str, kind: str, artifact_ids: Sequence[str],
                      required_fields: Sequence[str],
                      content_transform=None,
                      allow_empty: bool = False) -> Tuple[bool, Optional[str], List[Any]]:
    resolved: List[Any] = []
    if not artifact_ids:
        if allow_empty:
            return True, None, []
        return False, f"surface '{surface}': no {kind} refs declared by the manifest", None
    for aid in artifact_ids:
        art = registry.resolve_optional(kind, aid)
        if art is None:
            return False, f"surface '{surface}': {kind} artifact {aid!r} is not registered", None
        violation = _kind_validator(kind, required_fields, art.content)
        if violation is not None:
            return False, f"surface '{surface}': {violation}", None
        if content_transform is not None:
            err = content_transform(art, refs)
            if err:
                return False, f"surface '{surface}': {err}", None
        resolved.append(art)
    return True, None, resolved


# --------------------------------------------------------------------------- #
# reconstruction report
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class EpochReconstructionReport:
    epoch_id: str
    success: bool
    reconstruction_evidence_qualified: bool          # G4R-15
    missing_surfaces: Tuple[str, ...]
    invalid_surfaces: Tuple[str, ...]
    resolved_surfaces: Tuple[str, ...]
    historical_epoch_fingerprint: str
    reconstruction_semantic_fingerprint: str
    historical_runtime_certifications: Tuple[str, ...]
    current_runtime: str
    runtime_native_memory_used: bool
    notes: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {"epoch_id": self.epoch_id, "success": self.success,
                "reconstruction_evidence_qualified": self.reconstruction_evidence_qualified,
                "missing_surfaces": list(self.missing_surfaces),
                "invalid_surfaces": list(self.invalid_surfaces),
                "resolved_surfaces": list(self.resolved_surfaces),
                "historical_epoch_fingerprint": self.historical_epoch_fingerprint,
                "reconstruction_semantic_fingerprint": self.reconstruction_semantic_fingerprint,
                "historical_runtime_certifications": list(self.historical_runtime_certifications),
                "current_runtime": self.current_runtime,
                "runtime_native_memory_used": self.runtime_native_memory_used,
                "notes": list(self.notes)}


def _contract_version_consistency(surface: str, declared_ref: str,
                                  art: CanonicalArtifact) -> Optional[str]:
    """G4R-13: the resolved contract artifact's version must match the version
    the manifest declared. Declared refs use the canonical 'ID:VERSION' form;
    plain refs compare verbatim."""
    declared = art.content.get("version")
    if not declared:
        return f"surface '{surface}': contract artifact carries no version"
    if ":" in declared_ref:
        expected = declared_ref.split(":", 1)[1]
    else:
        expected = declared_ref
    if declared != expected:
        return (f"surface '{surface}': resolved version {declared!r} != "
                f"manifest declared {declared_ref!r} (G4R-13)")
    return None


def _eval_contract_consistency(art: CanonicalArtifact, refs: Mapping[str, Any]) -> Optional[str]:
    m = refs.get("_manifest")
    if m is not None and m.evaluation_contract_version:
        return _contract_version_consistency("evaluation_contract",
                                             m.evaluation_contract_version, art)
    return None


def _lifecycle_contract_consistency(art: CanonicalArtifact, refs: Mapping[str, Any]) -> Optional[str]:
    m = refs.get("_manifest")
    if m is not None and m.lifecycle_contract_version:
        return _contract_version_consistency("lifecycle_contract",
                                             m.lifecycle_contract_version, art)
    return None


def _authority_snapshot_consistency(art: CanonicalArtifact, refs: Mapping[str, Any]) -> Optional[str]:
    m = refs.get("_manifest")
    if m is None:
        return None
    inline_fp = deterministic_hex("authority_snapshot", dict(m.authority_state_snapshot))
    art_fp = deterministic_hex("authority_snapshot", dict(art.content))
    if inline_fp != art_fp:
        return (f"surface 'authority_state_snapshot': resolved artifact fingerprint "
                f"does not match the manifest's inline authority snapshot (G4R-13)")
    if not m.authority_state_snapshot:
        return "surface 'authority_state_snapshot': manifest snapshot is empty"
    return None


def _knowledge_epoch_consistency(art: CanonicalArtifact, refs: Mapping[str, Any]) -> Optional[str]:
    m = refs.get("_manifest")
    if m is not None and art.epoch_id and m.epoch_id and art.epoch_id != m.epoch_id:
        return (f"surface 'knowledge_projection': record {art.artifact_id!r} belongs "
                f"to epoch {art.epoch_id!r}, incompatible with manifest epoch {m.epoch_id!r}")
    return None


def reconstruct_epoch(
    bundle: EpochReconstructionBundle,
    registry: CanonicalArtifactRegistry,
    current_runtime: str,
    runtime_native_memory: bool = False,
    contract: Optional[Mapping[str, Any]] = None,
) -> EpochReconstructionReport:
    """Deterministic reconstruction from CANONICAL ARTIFACTS ONLY. External
    surfaces must resolve to pre-existing registered artifacts — a manifest
    alone is never sufficient (G4R-12). Missing or inconsistent surfaces fail
    closed with the surface identified (G4R-13/20). Content is validated per
    surface, never by mere non-emptiness.

    reconstruction_evidence_qualified (G4R-15): a run that used runtime-native
    memory may still produce a diagnostic report, but it does NOT count as
    evidence for the S13 runtime-neutral reconstruction pass.
    """
    required = tuple((contract or PROVISIONAL_EPOCH_RECONSTRUCTION_CONTRACT)
                     .get("required_surfaces", REQUIRED_RECONSTRUCTION_SURFACES))
    manifest = bundle.sealed_epoch_manifest
    refs = dict(bundle.__dict__)          # surface content/refs
    refs["_manifest"] = manifest         # cross-artifact consistency target (G4R-13)
    missing: List[str] = []
    invalid: List[str] = []
    resolved_surfaces: List[str] = []

    def surface_present(surface: str) -> bool:
        return surface not in missing and surface not in invalid

    # --- inline surfaces ------------------------------------------------- #
    if manifest is None or not manifest.sealed:
        missing.append("sealed_epoch_manifest")
    else:
        resolved_surfaces.append("sealed_epoch_manifest")
    if bundle.governing_architecture_versions:
        resolved_surfaces.append("governing_architecture_versions")
    else:
        missing.append("governing_architecture_versions")
    if bundle.known_tensions:
        resolved_surfaces.append("known_tensions")
    else:
        missing.append("known_tensions")

    # --- external registry surfaces (G4R-11/12) --------------------------- #
    ok, err, _ = _resolve_surface(
        refs, registry, "evaluation_contract", "EVALUATION_CONTRACT",
        bundle.evaluation_contract_ref, ("contract_id", "version"),
        content_transform=_eval_contract_consistency)
    if not ok:
        if "not registered" in str(err) or "no EVALUATION" in str(err):
            missing.append("evaluation_contract")
        else:
            invalid.append("evaluation_contract")

    ok, err, _ = _resolve_surface(
        refs, registry, "lifecycle_contract", "LIFECYCLE_CONTRACT",
        bundle.lifecycle_contract_ref, ("contract_id", "version"),
        content_transform=_lifecycle_contract_consistency)
    if not ok:
        if "not registered" in str(err) or "no LIFECYCLE" in str(err):
            missing.append("lifecycle_contract")
        else:
            invalid.append("lifecycle_contract")
    else:
        resolved_surfaces.append("lifecycle_contract")

    ok, err, _ = _resolve_surface(
        refs, registry, "authority_state_snapshot", "AUTHORITY_SNAPSHOT",
        bundle.authority_snapshot_ref, (),
        content_transform=_authority_snapshot_consistency)
    if not ok:
        if "not registered" in str(err) or "no AUTHORITY" in str(err):
            missing.append("authority_state_snapshot")
        else:
            invalid.append("authority_state_snapshot")
    else:
        resolved_surfaces.append("authority_state_snapshot")

    ok, err, _ = _resolve_ref_list(
        refs, registry, "active_ontology_versions", "ONTOLOGY",
        bundle.ontology_refs, ("artifact_id",))
    if ok:
        resolved_surfaces.append("active_ontology_versions")
    else:
        missing.append("active_ontology_versions")

    ok, err, _ = _resolve_ref_list(
        refs, registry, "high_dependency_assumptions", "HIGH_DEPENDENCY_ASSUMPTION",
        bundle.high_dependency_assumption_refs, ("artifact_id",))
    if ok:
        resolved_surfaces.append("high_dependency_assumptions")
    else:
        missing.append("high_dependency_assumptions")

    ok, err, certs = _resolve_ref_list(
        refs, registry, "active_capability_certifications", "RUNTIME_CERTIFICATION",
        bundle.certification_refs, ("artifact_id",))
    ok2, err2, caps = _resolve_ref_list(
        refs, registry, "active_capability_certifications", "CAPABILITY_CERTIFICATION",
        bundle.capability_certification_refs, ("artifact_id",))
    if ok and ok2:
        resolved_surfaces.append("active_capability_certifications")
    else:
        missing.append("active_capability_certifications")

    ok, err, _ = _resolve_ref_list(
        refs, registry, "active_knowledge_projection", "KNOWLEDGE_RECORD",
        bundle.active_knowledge_refs, ("record_id",),
        content_transform=_knowledge_epoch_consistency)
    if ok:
        resolved_surfaces.append("active_knowledge_projection")
    else:
        missing.append("active_knowledge_projection")

    ok, err, _ = _resolve_ref_list(
        refs, registry, "dormant_knowledge_projection", "KNOWLEDGE_RECORD",
        bundle.dormant_knowledge_refs, ("record_id",),
        content_transform=_knowledge_epoch_consistency)
    if ok:
        resolved_surfaces.append("dormant_knowledge_projection")
    else:
        missing.append("dormant_knowledge_projection")

    ok, err, _ = _resolve_ref_list(
        refs, registry, "negative_knowledge_refs", "NEGATIVE_KNOWLEDGE",
        bundle.negative_knowledge_refs, ("record_id",))
    if ok:
        resolved_surfaces.append("negative_knowledge_refs")
    else:
        missing.append("negative_knowledge_refs")

    ok, err, _ = _resolve_ref_list(
        refs, registry, "unresolved_pattern_refs", "UNRESOLVED_PATTERN",
        bundle.unresolved_pattern_refs, ("artifact_id",))
    if ok:
        resolved_surfaces.append("unresolved_pattern_refs")
    else:
        missing.append("unresolved_pattern_refs")

    ok, err, _ = _resolve_ref_list(
        refs, registry, "validation_rules", "VALIDATION_RULE",
        bundle.validation_rule_refs, ("artifact_id",))
    if ok:
        resolved_surfaces.append("validation_rules")
    else:
        missing.append("validation_rules")

    ok, err, _ = _resolve_ref_list(
        refs, registry, "operator_ratifications", "OPERATOR_RATIFICATION",
        bundle.operator_ratification_refs, ("ratification_ref",))
    if ok:
        resolved_surfaces.append("operator_ratifications")
    else:
        missing.append("operator_ratifications")

    ok, err, _ = _resolve_ref_list(
        refs, registry, "transformation_evidence", "TRANSFORMATION_EVIDENCE",
        bundle.transformation_evidence_refs, ("evidence_id",))
    if ok:
        resolved_surfaces.append("transformation_evidence")
    else:
        missing.append("transformation_evidence")

    ok, err, _ = _resolve_ref_list(
        refs, registry, "challenge_reopen_conditions", "REOPEN_CONDITION",
        bundle.challenge_reopen_condition_refs, ("condition_id",))
    if ok:
        resolved_surfaces.append("challenge_reopen_conditions")
    else:
        missing.append("challenge_reopen_conditions")

    # de-duplicate
    missing = sorted(set(missing))
    invalid = sorted(set(invalid))
    resolved_surfaces = sorted(set(resolved_surfaces))

    historical_fp = manifest.fingerprint() if manifest is not None else ""
    # semantic fingerprint: canonical reconstructed state minus the CURRENT
    # runtime identity (historical runtime certifications REMAIN — they are
    # history and part of the semantic state).
    semantic_parts = [
        bundle.epoch_id,
        bundle.evaluation_contract_ref,
        bundle.lifecycle_contract_ref,
        bundle.authority_snapshot_ref,
        bundle.ontology_refs,
        bundle.certification_refs,
        bundle.active_knowledge_refs,
        bundle.dormant_knowledge_refs,
        bundle.negative_knowledge_refs,
        bundle.unresolved_pattern_refs,
        bundle.validation_rule_refs,
        bundle.operator_ratification_refs,
        bundle.transformation_evidence_refs,
        bundle.challenge_reopen_condition_refs,
        historical_fp,
        runtime_native_memory,
        sorted(registry.all_ids()),
    ]
    semantic_fp = deterministic_hex("reconstruction_semantic", *semantic_parts, length=32)

    qualified = not missing and not invalid and not runtime_native_memory
    success = not missing and not invalid
    if not success:
        return EpochReconstructionReport(
            epoch_id=bundle.epoch_id, success=False,
            reconstruction_evidence_qualified=False,
            missing_surfaces=tuple(missing), invalid_surfaces=tuple(invalid),
            resolved_surfaces=tuple(resolved_surfaces),
            historical_epoch_fingerprint=historical_fp,
            reconstruction_semantic_fingerprint=semantic_fp,
            historical_runtime_certifications=tuple(bundle.capability_certification_refs),
            current_runtime=current_runtime,
            runtime_native_memory_used=runtime_native_memory,
            notes=("FAIL_CLOSED: required canonical surface(s) missing or invalid; "
                   "no guessed defaults",))
    notes = [
        "reconstructed from canonical institutional artifacts only",
        "replacement runtime identity does not rewrite historical identity",
        "runtime-native memory: none required",
        "HISTORICAL_CANONICAL_STATE preserved without promotion to current canonical state",
    ]
    if runtime_native_memory:
        notes.append("diagnostic only: runtime-native memory was used; this run is "
                     "NOT qualified evidence for the runtime-neutral reconstruction pass (G4R-15)")
    return EpochReconstructionReport(
        epoch_id=bundle.epoch_id, success=True,
        reconstruction_evidence_qualified=qualified,
        missing_surfaces=(), invalid_surfaces=(),
        resolved_surfaces=tuple(resolved_surfaces),
        historical_epoch_fingerprint=historical_fp,
        reconstruction_semantic_fingerprint=semantic_fp,
        historical_runtime_certifications=tuple(bundle.capability_certification_refs),
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
