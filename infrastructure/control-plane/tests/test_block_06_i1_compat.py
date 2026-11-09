"""B6-I1 compatibility proofs: three verdicts, explicit window, no latest fallback."""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from oce.compat import matrix  # noqa: E402

DOCS = ROOT / "docs/oce-golden-system"


def load() -> dict:
    return json.loads((DOCS / "OCE_BLOCK_06_I1_COMPATIBILITY_MATRIX_v1.0.json")
                      .read_text(encoding="utf-8"))


def test_matrix_check_supported() -> None:
    verdict = matrix.check("v1")
    assert verdict["verdict"] == "SUPPORTED" and verdict["supported"] == ["v1"]


def test_matrix_check_unsupported_version() -> None:
    verdict = matrix.check("v0")
    assert verdict["verdict"] == "UNSUPPORTED"
    assert "outside" in verdict["reason"] and verdict["supported"] == ["v1"]


def test_matrix_check_unknown_version() -> None:
    for requested in ("v2", "latest", "", None, 1):
        verdict = matrix.check(requested)
        assert verdict["verdict"] == "UNKNOWN", requested
        assert verdict["supported"] == ["v1"]


def test_matrix_never_returns_the_latest() -> None:
    for requested in ("v2", "latest", "v9.9.9"):
        assert matrix.check(requested)["verdict"] != "SUPPORTED"


def test_matrix_rows_proven_only_for_c1() -> None:
    doc = load()
    assert doc["supported_window"] == {"min": "v1", "max": "v1", "policy": "additive_minor"}
    assert len(doc["rows"]) == 3
    assert {row["section"] for row in doc["rows"]} == {"C1.S1", "C1.S2", "C1.S5"}
    assert all(row["state"] == "PROVEN" for row in doc["rows"])


def test_matrix_reports_remaining_unproven() -> None:
    doc = load()
    rest = doc["unproven_elsewhere"]
    assert rest["block_6_sections_total"] == 25
    assert rest["proven_in_this_stage"] == 3
    assert rest["state"].endswith("UNPROVEN")
    assert doc["refusal"]["silent_latest"] is False
