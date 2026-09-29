"""SENSOR-B4-I12R2R1 — historical evidence immutability + checkpoint-scoped
verification (governance/evidence repair; ZERO production changes).

Operator finding (I12R2R1 §1): the I12R2 publication regenerated the
historical I12R1 REPRESENTATION_SELECTION artifact from CURRENT production
behavior, violating the append-only historical-evidence law.  This module
pins the dual-truth end state:

- HISTORICAL: the I12R1 artifact holds the behavior actually published at
  the I12R1 checkpoint (schema mismatch + both representations requested
  -> valid T0A returned with empty projection_refs), verified by immutable
  checkpoint identity (SHA-256 + Git object truth at the accepted I12R1
  head), NOT by current runtime regeneration;
- CURRENT: I12R2 production fails that same query typed
  (ProjectionSchemaUnsupported), proven live and by the I12R2 matrices,
  which regenerate byte-identically from current production.

The test module passes ONLY if both statements are simultaneously
preserved (§14 dual-truth test) — historical integrity plus current
behavioral proof, without rewriting either.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = str(Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from _sibling_import import load_sibling  # noqa: E402

_harness = load_sibling("i12r1_e2e", "test_i12r1_query_end_to_end")
Lake = _harness.Lake
wired_service = _harness.wired_service

from crypto_sensor_fabric.storage.models import RawEvidenceQuery  # noqa: E402
from crypto_sensor_fabric.storage.query import (  # noqa: E402
    ProjectionSchemaUnsupported,
)

REPO = Path(__file__).resolve().parents[4]
EVIDENCE_DIR = (
    REPO / "quant-lab" / "research" / "crypto_foundry" / "sensor_fabric"
    / "evidence" / "bloc_04"
)

HISTORICAL_MATRIX = "BLOC_04_I12R1_REPRESENTATION_SELECTION_MATRIX.json"
I12R1_ACCEPTED_HEAD = "76042ca4c4abf17884980fca84a7aa1ba2d680c6"
I12R1_REPRESENTATION_EVIDENCE_SHA256 = (
    "039580c07b7e6f65a74f892f513dcba7ccdc5f6f5e385e82f13595e6e437a5f3"
)
HISTORICAL_FALLBACK_ROW = "schema_mismatch_with_T0A_fallback_documented"
CURRENT_FAIL_CLOSED_ROW = "both_requested_schema_mismatch_refused"
I12R2_MATRIX = "BLOC_04_I12R2_REPRESENTATION_SATISFACTION_MATRIX.json"
I12R2_NARRATIVE = "BLOC_04_I12R2_FAIL_SAFE_CLOSURE.md"


def _rel(path: Path) -> str:
    return path.resolve().relative_to(REPO.resolve()).as_posix()


def _git_blob(sha: str, path: Path) -> bytes:
    return subprocess.run(
        ["git", "cat-file", "blob", f"{sha}:{_rel(path)}"],
        check=True,
        capture_output=True,
    ).stdout


# ---------------------------------------------------------------------------
# §2/§5A — historical artifact restored to exact checkpoint bytes
# ---------------------------------------------------------------------------


class TestHistoricalArtifactImmutability:
    def test_sha256_matches_frozen_pin(self) -> None:
        path = EVIDENCE_DIR / HISTORICAL_MATRIX
        assert path.exists()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == I12R1_REPRESENTATION_EVIDENCE_SHA256, (
            "the historical I12R1 representation artifact is no longer the "
            "evidence published at the I12R1 checkpoint"
        )

    def test_sha256_matches_git_object_truth_at_accepted_head(self) -> None:
        path = EVIDENCE_DIR / HISTORICAL_MATRIX
        assert path.read_bytes() == _git_blob(I12R1_ACCEPTED_HEAD, path), (
            "artifact diverges from the Git object at the accepted I12R1 head"
        )


# ---------------------------------------------------------------------------
# §5B/§5D — structural law of the ORIGINAL I12R1 publication
# ---------------------------------------------------------------------------


class TestHistoricalStructure:
    def _payload(self) -> dict:
        return json.loads(
            (EVIDENCE_DIR / HISTORICAL_MATRIX).read_text(encoding="utf-8")
        )

    def test_checkpoint_and_matrix_identity(self) -> None:
        payload = self._payload()
        assert payload["mandate"] == "SENSOR-B4-I12R1"
        assert payload["matrix"] == "BLOC_04_I12R1_REPRESENTATION_SELECTION"

    def test_row_count_and_counterfactual_law(self) -> None:
        rows = self._payload()["rows"]
        assert len(rows) == 10
        counterfactuals = [
            r for r in rows if r["invariant_source"] == "SYNTHETIC_COUNTERFACTUAL"
        ]
        assert len(counterfactuals) == 1
        assert counterfactuals[0]["result"] == "FAIL"
        measured = [
            r for r in rows if r["invariant_source"] != "SYNTHETIC_COUNTERFACTUAL"
        ]
        assert all(r["result"] == "OK" for r in measured)
        assert all(r.get("measured") for r in measured)
        assert self._payload()["summary"] == {"rows": 10, "ok": 9, "fail": 1}

    def test_historical_fallback_row_present_as_published(self) -> None:
        """The historical row remains exactly as ORIGINALLY published: the
        superseded T0A fallback was I12R1 production truth."""
        hist = [
            r for r in self._payload()["rows"]
            if r["case"] == HISTORICAL_FALLBACK_ROW
        ]
        assert len(hist) == 1, "historical fallback row missing"
        row = hist[0]
        assert row["invariant_source"] == "PRODUCTION_BEHAVIOR"
        assert row["result"] == "OK"
        # Original measured payload: valid T0A returned, T0B silently absent.
        assert row["measured"]["exception"] is None
        assert row["measured"]["projection_refs"] == []
        assert row["measured"]["blob_refs"]


# ---------------------------------------------------------------------------
# §3/§5E/§8 — CURRENT I12R2 behavior and matrices regenerate live
# ---------------------------------------------------------------------------


class TestCurrentI12R2Truth:
    def test_current_production_fails_closed(self, tmp_path: Path) -> None:
        """The same query that the historical artifact recorded as an
        option-A T0A fallback now fails typed (§3: production NOT reverted)."""
        lake = Lake(tmp_path)
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-1")
        lake.commit_projection("proj-1", [(sha, "acq-1")])
        lake.commit_manifest("pm-1", blob_refs=[sha], projection_refs=["proj-1"])
        with pytest.raises(ProjectionSchemaUnsupported):
            wired_service(lake).execute(
                RawEvidenceQuery(
                    include_t0a=True,
                    include_t0b=True,
                    projection_schema_ids=["nonmatching.schema"],
                )
            )

    def test_i12r2_representation_matrix_regenenerates_byte_identically(
        self,
    ) -> None:
        from test_i12r2_evidence import build_representation_matrix, _canonical_bytes

        path = EVIDENCE_DIR / I12R2_MATRIX
        assert path.exists()
        assert path.read_bytes() == _canonical_bytes(build_representation_matrix())

    def test_i12r2_authority_matrix_regenenerates_byte_identically(self) -> None:
        from test_i12r2_evidence import build_authority_matrix, _canonical_bytes

        path = EVIDENCE_DIR / "BLOC_04_I12R2_AUTHORITY_REQUIRED_MATRIX.json"
        assert path.exists()
        assert path.read_bytes() == _canonical_bytes(build_authority_matrix())

    def test_i12r2_matrix_carries_current_fail_closed_row(self) -> None:
        payload = json.loads(
            (EVIDENCE_DIR / I12R2_MATRIX).read_text(encoding="utf-8")
        )
        rows = [
            r for r in payload["rows"] if r["case"] == CURRENT_FAIL_CLOSED_ROW
        ]
        assert len(rows) == 1
        row = rows[0]
        assert row["invariant_source"] == "PRODUCTION_BEHAVIOR"
        assert row["result"] == "OK"
        assert row["measured"]["exception"] == "ProjectionSchemaUnsupported"


# ---------------------------------------------------------------------------
# §6 — semantic linkage, not just hash tautology
# ---------------------------------------------------------------------------


class TestSemanticLinkage:
    def test_narrative_marks_supersession(self) -> None:
        text = (EVIDENCE_DIR / I12R2_NARRATIVE).read_text(encoding="utf-8")
        assert HISTORICAL_FALLBACK_ROW in text
        assert CURRENT_FAIL_CLOSED_ROW in text
        assert "superseded" in text.lower()
        assert "option-A fallback is superseded" in text

    def test_superseded_r1_artifact_module_never_rewrites_history(self) -> None:
        """The R1 evidence module's publication set excludes the historical
        matrix: a future builder regression cannot silently rewrite it."""
        from test_i12r1_evidence import _MATRICES, publish_all  # noqa: F401

        names = [name for name, _ in _MATRICES]
        assert HISTORICAL_MATRIX not in names


# ---------------------------------------------------------------------------
# §14 — the DUAL-TRUTH test (core purpose of the repair)
# ---------------------------------------------------------------------------


class TestDualTruth:
    def test_historical_fallback_and_current_fail_closed_coexist(
        self, tmp_path: Path
    ) -> None:
        """PASSes ONLY if BOTH statements are simultaneously preserved:

        HISTORICAL (I12R1 artifact, checkpoint-scoped identity):
          both requested + schema mismatch -> valid T0A, projection_refs=[]
        CURRENT (I12R2 production, live execution):
          the same query -> ProjectionSchemaUnsupported
        """
        import pytest as _pytest

        # (1) HISTORICAL truth preserved: exact bytes + row present as
        # originally published.
        path = EVIDENCE_DIR / HISTORICAL_MATRIX
        assert (
            hashlib.sha256(path.read_bytes()).hexdigest()
            == I12R1_REPRESENTATION_EVIDENCE_SHA256
        )
        assert path.read_bytes() == _git_blob(I12R1_ACCEPTED_HEAD, path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        hist = [
            r for r in payload["rows"] if r["case"] == HISTORICAL_FALLBACK_ROW
        ]
        assert len(hist) == 1 and hist[0]["result"] == "OK"
        assert hist[0]["measured"]["exception"] is None
        assert hist[0]["measured"]["projection_refs"] == []

        # (2) CURRENT truth preserved: same query fails typed NOW.
        lake = Lake(tmp_path)
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-1")
        lake.commit_projection("proj-1", [(sha, "acq-1")])
        lake.commit_manifest("pm-1", blob_refs=[sha], projection_refs=["proj-1"])
        with _pytest.raises(ProjectionSchemaUnsupported):
            wired_service(lake).execute(
                RawEvidenceQuery(
                    include_t0a=True,
                    include_t0b=True,
                    projection_schema_ids=["nonmatching.schema"],
                )
            )
