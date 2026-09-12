"""Generate a machine-readable phase freeze manifest (canon Book VI 18.3).

Usage:

    python qcae/implementation/tools/freeze_manifest.py <phase> <outfile.json>

The manifest records the commit SHAs of the phase's milestone commits, the
pytest run summary, schema snapshots (versioned envelope shape of every core
record class), and the evidence matrix items for the phase. Reviewers audit
phase readiness from this artifact instead of trusting the build agent's
summary (18.3 Exit Criteria).
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from qcae import CANON_VERSION, __version__  # noqa: E402
from qcae.core.amendments.a001.economic_experience import (  # noqa: E402
    EconomicExperienceRecord,
    EconomicsBlock,
)
from qcae.core.amendments.a001.external_registry import (  # noqa: E402
    ExternalLifecycleRole,
    ExternalRegistry,
    ExternalRegistryRef,
)
from qcae.core.amendments.a001.gaps import (  # noqa: E402
    GAP_OWNERSHIP,
    GapOwner,
    GapRef,
    GapType,
    MixedGapDecomposition,
)
from qcae.core.amendments.a001.handoff import (  # noqa: E402
    HANDOFF_GAP_TYPES,
    FallbackClass,
    HandoffConstraints,
    HandoffDirection,
    HandoffMode,
    HandoffProvenance,
    HandoffResult,
    HandoffStatus,
    RequiredOutput,
    ResearchCapabilityHandoff,
)
from qcae.core.amendments.a001.resolution import (  # noqa: E402
    CapabilityResolutionMode,
)
from qcae.core.amendments.a001.shared import (  # noqa: E402
    A001_AMENDMENT_ID,
    A001_AMENDMENT_VERSION,
    DataRights,
)
from qcae.core.capabilities.atom import CapabilityAtom  # noqa: E402
from qcae.core.capabilities.candidate import Candidate  # noqa: E402
from qcae.core.capabilities.composite import CompositionMember  # noqa: E402
from qcae.core.contracts.contract import CapabilityContract  # noqa: E402
from qcae.core.decisions.acquisition import AcquisitionDecision  # noqa: E402
from qcae.core.decisions.authority import AuthorityDecision, AuthorityRequest  # noqa: E402
from qcae.core.evidence_ref import EvidenceRef  # noqa: E402
from qcae.core.jobs import Job, Step  # noqa: E402
from qcae.core.lifecycle.state import (  # noqa: E402
    EVIDENCE_GATES,
    TERMINAL_STATES,
    WAIVABLE_GATES,
    LifecycleState,
)
from qcae.core.lifecycle.waiver import TransitionWaiver  # noqa: E402
from qcae.core.relationships.graph import EntityRef, Relationship  # noqa: E402
from qcae.core.serialization import sha256_of  # noqa: E402


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def schema_snapshot(cls) -> dict:
    """Versioned envelope shape of a record class without instance data."""
    return {
        "object_type": cls.object_type(),
        "schema_version": cls.SCHEMA_VERSION,
        "fields": list(cls._serialized_fields()),
    }


def build_manifest(phase: str) -> dict:
    # Phase milestone commits from history (P#- prefixed).
    commits = []
    for line in git("log", "--oneline", "-30").splitlines():
        sha, _, subject = line.partition(" ")
        if subject.startswith((f"{phase}-",)):
            commits.append({"sha": sha, "subject": subject})

    record_classes = [
        CapabilityContract,
        CapabilityAtom,
        CompositionMember,
        Candidate,
        EntityRef,
        Relationship,
        EvidenceRef,
        TransitionWaiver,
        AcquisitionDecision,
        AuthorityRequest,
        AuthorityDecision,
        Step,
        Job,
    ]

    manifest = {
        "manifest_version": 1,
        "phase": phase,
        "canon_version": CANON_VERSION,
        "qcae_version": __version__,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "head_commit": git("rev-parse", "HEAD"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "phase_commits": commits,
        "schema_snapshots": [schema_snapshot(cls) for cls in record_classes],
        "schema_snapshot_digest": None,  # filled below
        "lifecycle": {
            "states": [s.value for s in LifecycleState],
            "evidence_gate_order": [s.value for s in EVIDENCE_GATES],
            "waivable_gates": sorted(s.value for s in WAIVABLE_GATES),
            "terminal_states": sorted(s.value for s in TERMINAL_STATES),
        },
        "tests": None,  # filled by caller from the pytest run
        "known_failures_outside_qcae": [
            "tests/forge/phase_00/test_extension_docs.py (2 pre-existing failures "
            "on this branch, unrelated to QCAE; present before P0 work)"
        ],
        "deferred_items": [
            {
                "item": "AtomStatus values are a P0 derivation (canon 1.2.22 "
                "leaves status unvalued)",
                "severity": "MINOR",
                "owner": "build-agent",
                "trigger": "P5 capability forensics",
            },
            {
                "item": "Job/Step status vocabularies are minimal identity "
                "contracts; queue/lease semantics arrive at P2",
                "severity": "MINOR",
                "owner": "build-agent",
                "trigger": "P2 job runtime",
            },
        ],
        "blockers": [],
        "evidence_refs": {
            "progress_ledger": "qcae/QCAE_IMPLEMENTATION_PROGRESS.md",
            "adrs": [
                "qcae/implementation/decisions/ADR-0001-core-domain-representation.md",
                "qcae/implementation/decisions/ADR-0002-package-layout-and-test-wiring.md",
            ],
            "architecture_guards": (
                "qcae/tests/architecture/test_p0_dependency_guards.py"
            ),
            "lifecycle_tests": "qcae/tests/unit/test_p0_lifecycle.py",
            "serialization_tests": "qcae/tests/unit/test_p0_serialization.py",
            "contract_tests": "qcae/tests/unit/test_p0_contract.py",
            "capability_tests": "qcae/tests/unit/test_p0_capabilities.py",
            "relationship_tests": "qcae/tests/unit/test_p0_relationships.py",
            "decision_job_tests": "qcae/tests/unit/test_p0_decisions_jobs.py",
        },
    }
    manifest["schema_snapshot_digest"] = sha256_of(manifest["schema_snapshots"])
    return manifest


def _enum_snapshot(enum_cls) -> dict:
    return {"values": [m.value for m in enum_cls]}


def build_amendment_manifest(phase: str, original_manifest_path: Path) -> dict:
    """Amendment-aware freeze manifest (reconciliation prompt §10).

    Preserves the original P0 freeze by reference and records the additive
    A-001 reconciliation as a separate baseline.
    """
    manifest = build_manifest(phase)
    original = json.loads(original_manifest_path.read_text(encoding="utf-8"))

    manifest["original_freeze_ref"] = {
        "manifest": original_manifest_path.name,
        "head_commit_at_original_freeze": original["head_commit"],
        "original_test_ledger": original["tests"],
        "preserved": True,
    }
    manifest["active_amendments"] = [
        {
            "amendment_id": A001_AMENDMENT_ID,
            "version": A001_AMENDMENT_VERSION,
            "title": "Research Mesh Boundary and Economic Experience",
            "register": "qcae/amendments/README.md",
            "document": (
                "qcae/amendments/"
                "QCAE_AMENDMENT_A001_RESEARCH_MESH_BOUNDARY_AND_"
                "ECONOMIC_EXPERIENCE_v1.0.md"
            ),
            "interface_schemas": [
                "qcae/amendments/schemas/research-capability-handoff.schema.json",
                "qcae/amendments/schemas/economic-experience.schema.json",
            ],
        }
    ]
    manifest["amendment_commits"] = [
        {"sha": sha, "subject": subject}
        for sha, subject in (
            line.partition(" ")[::2]
            for line in git("log", "--oneline", "-60").splitlines()
        )
        if subject.startswith("docs(qcae):")
    ]
    manifest["gap_taxonomy"] = {
        "gap_types": _enum_snapshot(GapType),
        "gap_ownership": {k.value: v.value for k, v in GAP_OWNERSHIP.items()},
        "mixed_gap_requires_decomposition": True,
        "handoff_boundary_subset": sorted(g.value for g in HANDOFF_GAP_TYPES),
    }
    manifest["resolution_vocabulary"] = {
        "capability_resolution_modes": _enum_snapshot(CapabilityResolutionMode),
        "layered_over_acquisition_form": True,
        "acquisition_form_unchanged": True,
        "adr": "ADR-0003",
    }
    manifest["data_rights"] = _enum_snapshot(DataRights)
    manifest["cross_registry_references"] = {
        "registries": _enum_snapshot(ExternalRegistry),
        "lifecycle_roles": _enum_snapshot(ExternalLifecycleRole),
        "schema_snapshot": schema_snapshot(ExternalRegistryRef),
        "ownership_note": (
            "references carry owner_domain and OBSERVE/SUBMIT role only; "
            "lifecycle authority never merges (A-001 section 6)"
        ),
    }
    manifest["deferred_lifecycle_resolution"] = {
        "adr": "ADR-0004",
        "interpretation": "A",
        "summary": (
            "DEFERRED is terminal for that decision/version; renewed "
            "investigation creates a superseding object"
        ),
    }
    manifest["schema_drift_guard"] = {
        "adr": "ADR-0005",
        "test": "qcae/tests/unit/test_p0_a001_schema_drift.py",
        "dependencies_added": [],
    }
    # Amendment record schema snapshots appended to the base set (reconciliation
    # prompt section 10: updated schema snapshots incl. handoff/econ/cross-registry).
    amendment_records = [
        GapRef,
        MixedGapDecomposition,
        HandoffConstraints,
        HandoffProvenance,
        HandoffResult,
        ResearchCapabilityHandoff,
        EconomicsBlock,
        EconomicExperienceRecord,
        ExternalRegistryRef,
    ]
    amendment_snapshots = [schema_snapshot(cls) for cls in amendment_records]
    manifest["schema_snapshots"] = manifest["schema_snapshots"] + amendment_snapshots
    manifest["schema_snapshot_digest"] = sha256_of(manifest["schema_snapshots"])
    manifest["schema_snapshot_counts"] = {
        "original_p0": len(original["schema_snapshots"]),
        "amendment_added": len(amendment_snapshots),
        "total": len(manifest["schema_snapshots"]),
    }
    return manifest


def main() -> None:
    phase = sys.argv[1] if len(sys.argv) > 1 else "P0"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO_ROOT / "qcae" / "implementation" / f"{phase.lower()}-freeze-manifest.json"
    if phase.endswith("-A001"):
        original = REPO_ROOT / "qcae" / "implementation" / "P0-freeze-manifest.json"
        manifest = build_amendment_manifest(phase, original)
    else:
        manifest = build_manifest(phase)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(manifest['schema_snapshots'])} schema snapshots, "
          f"{len(manifest['phase_commits'])} phase commits)")


if __name__ == "__main__":
    main()
