"""SENSOR-B4-I13R3-RATIFY — operator-acceptance boundary microchecks.

Narrow ratification verification only (I13 chain acceptance):

1. NONEXISTENT-CHILD CONTAINMENT (ratification §12): export into a
   NOT-pre-existing child beneath every protected source family must
   refuse with ``ExportDestinationUnsafe`` — NOT ``ExportPackExists`` —
   proving the containment comparison
   (``resolved_dest == protected_root`` OR
   ``protected_root in resolved_dest.parents``) fires independently of
   the pre-existing-directory refusal.  The probe destination never
   exists before the call.

2. FAIL-SAFE BOUNDARY DERIVATION (§13): canonical composition derives
   every wired dependency's source boundary automatically; a dependency
   that cannot prove a root refuses CONSTRUCTION with
   ``ExportSourceBoundaryUnproven``.

3. protected_source_roots EXTENSION LAW (§14): explicit roots ADD
   protection; they cannot replace or disable the derived canonical
   boundaries.

ZERO production changes: this module only exercises accepted surfaces.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from _sibling_import import load_sibling  # noqa: E402

from crypto_sensor_fabric.storage import (  # noqa: E402
    EvidencePackExporter,
    RawEvidenceQuery,
)
from crypto_sensor_fabric.storage.export import (  # noqa: E402
    ExportLimits,
    ExportSourceBoundaryUnproven,
)

i13 = load_sibling("test_i13_export_restore", "test_i13_export_restore")
i13r2 = load_sibling("test_i13r2_evidence", "test_i13r2_evidence")

_exporter = i13._exporter
build_deterministic_lake = i13r2.build_deterministic_lake
FIXED = i13.FIXED


def _attempt_export(exporter, destination: Path) -> str:
    """'EXPORTED' or the exception type name (never let it raise)."""
    try:
        exporter.export_query(RawEvidenceQuery(), destination)
        return "EXPORTED"
    except Exception as exc:  # noqa: BLE001
        return type(exc).__name__


class TestNonexistentChildContainment:
    """§12: the containment guard fires on NONEXISTENT children."""

    def test_export_into_nonexistent_child_of_each_protected_root(
        self, tmp_path
    ) -> None:
        root = tmp_path / "ratify"
        root.mkdir()
        lake = build_deterministic_lake(root / "src")
        exporter = _exporter(lake)  # canonical composition, no overrides

        t0a = root / "src" / "t0a"
        t0b = root / "src" / "t0b"
        probes: list[tuple[str, Path]] = [
            ("t0a_blob_root", t0a / "__ratify_export_probe__"),
            ("t0a_catalog_root", t0a / "catalogs" / "__ratify_export_probe__"),
            ("t0b_projection_root", t0b / "__ratify_export_probe__"),
            ("t0b_projection_catalog", t0b / "catalogs" / "manifests" / "projections" / "__ratify_export_probe__"),
            ("t0b_context_catalog", t0b / "catalogs" / "manifests" / "projection_context" / "__ratify_export_probe__"),
            ("t0b_lineage_catalog", t0b / "catalogs" / "manifests" / "projection_lineage" / "__ratify_export_probe__"),
            ("t0b_schema_catalog", t0b / "catalogs" / "projection_schemas" / "__ratify_export_probe__"),
            ("revision_registry_root", t0a / "revisions" / "__ratify_export_probe__"),
        ]
        for label, probe in probes:
            # The probe must NOT exist before the call — this is what
            # distinguishes containment refusal from pre-existing-directory
            # refusal (ExportPackExists).
            assert not probe.exists(), label
            outcome = _attempt_export(exporter, probe)
            assert outcome == "ExportDestinationUnsafe", (label, outcome)
            assert not probe.exists(), label

    def test_nonexistent_child_below_external_root_exports(self, tmp_path) -> None:
        """Control: a nonexistent child OUTSIDE every protected root exports."""
        root = tmp_path / "ratify-control"
        root.mkdir()
        lake = build_deterministic_lake(root / "src")
        exporter = _exporter(lake)
        destination = root / "outside" / "never-existed" / "pack"
        assert not destination.exists()
        receipt = exporter.export_query(RawEvidenceQuery(), destination)
        assert receipt.object_count > 0


class TestFailSafeBoundaryDerivation:
    """§13: derived boundaries; construction refuses when unprovable."""

    def test_unproven_boundary_dependency_refuses_construction(
        self, tmp_path
    ) -> None:
        root = tmp_path / "derive"
        root.mkdir()
        lake = build_deterministic_lake(root / "src")

        class _UnprovenRepo:
            """Duck-typed dependency with NO public root accessor."""

            def __init__(self) -> None:
                self._hidden = "/internal/never/visible"

        with pytest.raises(ExportSourceBoundaryUnproven):
            EvidencePackExporter(
                service=lake.service(),
                blob_store=lake.store,
                blob_metadata_repository=lake.blob_repo,
                acquisition_repository=lake.acq_repo,
                manifest_repository=lake.manifest_repo,
                artifact_repository=_UnprovenRepo(),  # type: ignore[arg-type]
                clock=lambda: FIXED,
                limits=ExportLimits(),
            )

    def test_canonical_composition_derives_all_wired_boundaries(
        self, tmp_path
    ) -> None:
        """The canonical exporter (NO protected_source_roots) still refuses
        destinations beneath every wired dependency family — proof that the
        boundaries were derived, not caller-supplied."""
        root = tmp_path / "derive-canonical"
        root.mkdir()
        lake = build_deterministic_lake(root / "src")
        sha_a1 = lake.acq_repo.get_acquisition("acq-1").blob_sha256
        lake.commit_projection("proj-1", [(sha_a1, "acq-1")])

        exporter = _exporter(lake)
        t0b = root / "src" / "t0b"
        for probe in (
            t0b / "__derive_probe__",
            t0b / "projections" / "__derive_probe__",
            root / "src" / "t0a" / "revisions" / "__derive_probe__",
        ):
            assert not probe.exists()
            outcome = _attempt_export(exporter, probe)
            assert outcome == "ExportDestinationUnsafe", (probe, outcome)


class TestProtectedSourceRootsExtensionLaw:
    """§14: explicit roots EXTEND; they never replace derived ones."""

    def test_explicit_root_protected_without_disabling_derived(
        self, tmp_path
    ) -> None:
        root = tmp_path / "extension"
        root.mkdir()
        lake = build_deterministic_lake(root / "src")
        extra = root / "extra-protected-tree"
        extra.mkdir()
        exporter = _exporter(
            lake, protected_source_roots=[extra]
        )
        # 1. The EXPLICIT root is protected (derived law extended).
        probe_extra = extra / "__extension_probe__"
        assert not probe_extra.exists()
        assert (
            _attempt_export(exporter, probe_extra)
            == "ExportDestinationUnsafe"
        )
        # 2. The DERIVED canonical boundaries remain protected — the
        #    explicit list did not replace them.
        probe_t0a = root / "src" / "t0a" / "__extension_probe__"
        assert not probe_t0a.exists()
        assert (
            _attempt_export(exporter, probe_t0a)
            == "ExportDestinationUnsafe"
        )
        probe_t0b = root / "src" / "t0b" / "__extension_probe__"
        assert not probe_t0b.exists()
        assert (
            _attempt_export(exporter, probe_t0b)
            == "ExportDestinationUnsafe"
        )
        # 3. An external destination still exports.
        outside = root / "outside" / "pack"
        receipt = exporter.export_query(RawEvidenceQuery(), outside)
        assert receipt.object_count > 0
