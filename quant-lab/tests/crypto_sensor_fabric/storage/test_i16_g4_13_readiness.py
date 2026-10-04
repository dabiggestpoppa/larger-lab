"""SENSOR-B4-I16C CHECKPOINT FOSSIL — G4-13 unit handoff contract gap.

HISTORY.  This file was the current-tree measurement vehicle for
SENSOR-B4-I16C.  At that head it correctly measured:

    G4-13 SOURCE = PASS, TIME = PASS, LINEAGE = PASS, UNIT = FAIL
    gap_id = I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP

and stopped the I16 final PASS.  That measurement is committed truth in
``BLOC_04_I16_BLOC4_READINESS.json`` (head 051b6dd1a...) and
``BLOC_04_I16_G4_GATE_MATRIX.json``; the original current-tree assertions
remain in git history at commit 42cc77b6b30f829c4073757989df7422f8223a15.

R1 §3/§27.  After the I16R1 repair the old current-tree assertions would be
WRONG (unit evidence is now publicly reachable by design), and ordinary R1
runs must not rewrite I16 artifacts.  This file is therefore converted into
CHECKPOINT-FOSSIL VALIDATION:

  * it validates the COMMITTED I16 negative artifacts — the frozen record —
    and never asserts the current tree's unit surface,
  * it performs NO writes (mechanically self-checked below),
  * it never emits or rewrites any ``BLOC_04_I16_*`` artifact,

while the POSITIVE remeasurement of G4-13 lives in
``test_i16r1_g4_13_positive.py`` with the successor consumer probe
``i16r1_bloc5_consumer_probe.py``.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

EVIDENCE_DIR = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)

I16_READINESS_NAME = "BLOC_04_I16_BLOC4_READINESS.json"
I16_MATRIX_NAME = "BLOC_04_I16_G4_GATE_MATRIX.json"
I16_FINAL_NAME = "BLOC_04_I16_FINAL_ACCEPTANCE_EVIDENCE.md"
R1_READINESS_NAME = "BLOC_04_I16R1_BLOC4_READINESS.json"

I16_GAP_ID = "I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP"
I16C_HEAD = "051b6dd1a297d49b59ba504f4da8536211f8911d"
I16_GATE_MATRIX_G4_13_HEAD = "42cc77b6b30f829c4073757989df7422f8223a15"


def _read_json(name: str) -> dict:
    return json.loads((EVIDENCE_DIR / name).read_text(encoding="utf-8"))


class TestI16NegativeRecordPreserved:
    def test_readiness_artifact_records_the_measured_gap(self) -> None:
        payload = _read_json(I16_READINESS_NAME)
        assert payload["checkpoint"] == "SENSOR-B4-I16C"
        assert payload["current_head"] == I16C_HEAD
        assert payload["gate_id"] == "G4-13"
        assert payload["result"] == "GAP"
        assert payload["gap_id"] == I16_GAP_ID
        assert payload["dimension_reachability"] == {
            "LINEAGE": True,
            "SOURCE": True,
            "TIME": True,
            "UNIT": False,
        }
        assert payload["dimensions_missing"] == ["UNIT"]

    def test_readiness_artifact_records_the_unit_measurement(self) -> None:
        unit = _read_json(I16_READINESS_NAME)["unit_proof"]
        assert unit["reachable"] is False
        assert unit["unit_named_fields_on_batch"] == []
        assert unit["unit_named_public_exports"] == []
        assert unit["unit_unverified_state_available"] is False
        assert unit["projection_schema_descriptor_exposes_unit"] is False
        assert unit["provider_native_field_keys"] == ["name", "type", "nullable"]
        assert unit["raw_bytes_contain_unit_string"] is True
        assert unit["raw_bytes_count_as_proof"] is False

    def test_gate_matrix_records_g4_13_as_fail(self) -> None:
        matrix = _read_json(I16_MATRIX_NAME)
        rows = [r for r in matrix["rows"] if r["gate_id"] == "G4-13"]
        assert len(rows) == 1
        row = rows[0]
        assert row["result"] == "FAIL"
        assert row["current_head"] == I16_GATE_MATRIX_G4_13_HEAD
        assert row["blocking_reason_if_any"].startswith(I16_GAP_ID)
        assert row["measured_case_count"] == 19

    def test_final_acceptance_evidence_carries_the_gap(self) -> None:
        text = (EVIDENCE_DIR / I16_FINAL_NAME).read_text(encoding="utf-8")
        assert I16_GAP_ID in text

    def test_r1_positive_successor_is_a_distinct_artifact(self) -> None:
        assert (EVIDENCE_DIR / I16_READINESS_NAME).exists()
        positive = _read_json(R1_READINESS_NAME)
        assert positive["checkpoint"] == "SENSOR-B4-I16R1C"
        assert positive["result"] == "PASS"
        assert positive["gap_status"]["gap_id"] == I16_GAP_ID
        assert positive["gap_status"]["status"] == "CLOSED"


class TestFossilValidatorIsWriteFree:
    def test_this_file_performs_no_writes(self) -> None:
        """The checkpoint fossil must never rewrite I16 (or any) artifacts."""
        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = (
                    func.attr
                    if isinstance(func, ast.Attribute)
                    else getattr(func, "id", "")
                )
                assert name not in (
                    "write_text",
                    "write_bytes",
                    "write",
                    "dump",
                    "mkdir",
                    "rename",
                    "replace",
                    "unlink",
                    "remove",
                ), f"fossil validator is not write-free: {name}"
            if isinstance(node, ast.Name):
                assert node.id != "open", "fossil validator must not open handles"

    def test_original_current_tree_probe_is_not_consulted(self) -> None:
        source = Path(__file__).read_text(encoding="utf-8")
        # Assembled so this check cannot match its own needle text.
        needle = "i16" + "_bloc5_consumer_probe"
        assert needle not in source, (
            "the fossil validator must not re-run the I16 negative probe "
            "against the repaired tree"
        )
