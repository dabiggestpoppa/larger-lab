"""SENSOR-B3-I11 — handoff package integrity test (OFFLINE).

Proves:
1. every file path referenced by `BLOC_03_HANDOFF_INDEX.md` exists;
2. every evidence ref inside `PROVIDER_CAPABILITY_RUNTIME.json` resolves to a
   committed bloc_02 artifact.

A broken handoff reference is a FAIL — the handoff package is a reproducible
contract, not a pile of files.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

TEST_ROOT = Path(__file__).resolve().parent
REPO_QUANT_LAB = TEST_ROOT.parents[2]

EVID = (
    REPO_QUANT_LAB
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_03"
)
INDEX = EVID / "BLOC_03_HANDOFF_INDEX.md"
CAPABILITY_RUNTIME = EVID / "PROVIDER_CAPABILITY_RUNTIME.json"
BLOC_02 = EVID.parent / "bloc_02"


def _referenced_paths() -> list[tuple[str, Path]]:
    """Extract (label, absolute path) pairs from the handoff index tables."""
    text = INDEX.read_text(encoding="utf-8")
    found: list[tuple[str, Path]] = []
    # Table cells and inline code paths containing a filename or relative path.
    for match in re.findall(r"`([^`]+\.(?:csv|json|md|yaml|py))`", text):
        rel = match.strip()
        # Relative to the index directory; resolve and verify containment.
        candidate = (EVID / rel).resolve()
        found.append((rel, candidate))
    # De-duplicate by absolute path.
    seen: set[Path] = set()
    out: list[tuple[str, Path]] = []
    for label, path in found:
        if path not in seen:
            seen.add(path)
            out.append((label, path))
    return out


def _evidence_ids_present(search_root: Path) -> set[str]:
    """Reuse the committed-evidence token scan (same heuristic as readiness)."""
    found: set[str] = set()
    for path in search_root.iterdir():
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            tokens = line.replace(",", " ").replace('"', " ").split()
            for token in tokens:
                if ("_" in token or "-" in token) and (
                    "2021" in token
                    or "2022" in token
                    or "2024" in token
                    or "2026" in token
                    or "RECENT_CONTROL" in token
                    or "book_snapshot" in token
                    or "raw_event" in token
                    or "1h" in token
                ):
                    found.add(token.strip())
    return found


class TestHandoffPackageIntegrity:
    def test_index_exists(self) -> None:
        assert INDEX.is_file(), f"handoff index missing: {INDEX}"

    def test_every_index_referenced_file_exists(self) -> None:
        missing = [label for label, path in _referenced_paths() if not path.exists()]
        assert not missing, f"handoff index references missing files: {missing}"

    def test_index_references_are_within_quant_lab(self) -> None:
        root = REPO_QUANT_LAB.resolve()
        outside = [
            label
            for label, path in _referenced_paths()
            if root not in path.parents and path != root
        ]
        assert not outside, f"handoff index escapes quant-lab: {outside}"

    def test_core_artifacts_referenced(self) -> None:
        referenced = {path.name for _, path in _referenced_paths()}
        for core in (
            "FINAL_ADAPTER_READINESS_MATRIX.csv",
            "FINAL_ADAPTER_READINESS_MATRIX.json",
            "PROVIDER_CAPABILITY_RUNTIME.json",
            "PROVIDER_IMPLEMENTATION_REPORT.md",
            "KNOWN_FAILURES.md",
            "ACCESS_CLASS_REPORT.md",
            "OFFLINE_TEST_REPORT.json",
            "NETWORK_SMOKE_EVIDENCE_INDEX.md",
            "BLOC_04_INPUT_MANIFEST.md",
            "FIXTURE_COVERAGE_REPORT.json",
            "BLOC_03_CURRENT_RUNTIME_ADAPTER_OVERLAY.json",
            "PRODUCTION_ADAPTER_MATRIX.csv",
        ):
            assert core in referenced, f"handoff index missing core artifact {core}"

    def test_capability_runtime_evidence_refs_resolve(self) -> None:
        payload = json.loads(CAPABILITY_RUNTIME.read_text(encoding="utf-8"))
        assert "paths" in payload and payload["paths"]
        resolved = _evidence_ids_present(BLOC_02)
        unresolved: list[str] = []
        for row in payload["paths"]:
            for ref in row.get("evidence_refs", []):
                if ref not in resolved:
                    unresolved.append(
                        f"{row['provider_id']}/{row['sensor_family']}: {ref!r}"
                    )
        assert not unresolved, (
            "PROVIDER_CAPABILITY_RUNTIME evidence refs do not resolve to "
            f"committed bloc_02 artifacts: {unresolved}"
        )

    def test_capability_runtime_has_exactly_17_paths(self) -> None:
        payload = json.loads(CAPABILITY_RUNTIME.read_text(encoding="utf-8"))
        rows = payload["paths"]
        assert len(rows) == 17
        keys = {(r["provider_id"], r["sensor_family"]) for r in rows}
        assert len(keys) == 17, "duplicate provider x sensor in capability runtime"

    def test_final_matrix_rows_match_runtime_overlay(self) -> None:
        import csv as _csv

        matrix_rows = list(
            _csv.DictReader((EVID / "FINAL_ADAPTER_READINESS_MATRIX.csv").open(encoding="utf-8", newline=""))
        )
        overlay = json.loads(
            (EVID / "BLOC_03_CURRENT_RUNTIME_ADAPTER_OVERLAY.json").read_text(encoding="utf-8")
        )
        matrix_set = {(r["provider_id"], r["sensor_family"]) for r in matrix_rows}
        overlay_set = {(p["provider_id"], p["sensor_family"]) for p in overlay["paths"]}
        assert len(matrix_rows) == 17
        assert matrix_set == overlay_set == {  # exact-set across final surfaces
            (p["provider_id"], p["sensor_family"]) for p in overlay["paths"]
        }
        assert len(matrix_set) == 17
        assert len(overlay_set) == 17
