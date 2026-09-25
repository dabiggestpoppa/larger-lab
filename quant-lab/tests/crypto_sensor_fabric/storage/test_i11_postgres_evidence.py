"""Read-only truth checks for the append-only I11 evidence pack."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

EVIDENCE_DIR = Path(__file__).parents[3] / "research" / "crypto_foundry" / "sensor_fabric" / "evidence" / "bloc_04"
ARTIFACTS = (
    "BLOC_04_I11_POSTGRES_SCHEMA_MATRIX.json",
    "BLOC_04_I11_RECONSTRUCTION_MATRIX.json",
    "BLOC_04_I11_AUTHORITY_FIREWALL_MATRIX.json",
    "BLOC_04_I11_TRANSACTION_ATOMICITY_MATRIX.json",
    "BLOC_04_I11_RUNTIME_INTEGRATION_MATRIX.json",
)


def _stable(payload: object) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


@pytest.mark.parametrize("name", ARTIFACTS)
def test_i11_matrix_truth_and_committed_bytes_are_stable(name: str) -> None:
    path = EVIDENCE_DIR / name
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["runtime_validation"] == "BLOCKED_ENVIRONMENT"
    rows = payload["rows"]
    assert len(rows) == payload["row_count"]
    for row in rows:
        required = row["required_invariants"]
        assert all(isinstance(row[name], bool) for name in required)
        assert row["result"] == ("OK" if all(row[name] for name in required) else "FAIL")
    deliberate = [row["case"] for row in rows if row["case"].startswith("counterfactual_")]
    assert deliberate == payload["deliberate_failures"]
    assert all(row["result"] == "FAIL" for row in rows if row["case"] in deliberate)
    assert _stable(payload) == path.read_bytes()
