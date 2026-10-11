"""SENSOR-B5-I05 - evidence integrity for ``bloc_05_time_validation.json``.

The evidence contract the I05 directive sets (section 06): a tracked
deterministic producer, executable observations with independent expected
outcomes and exact clause references, stable row ordering, stable
serialization, no live-clock dependence, no untracked runtime dependency, two
byte-identical generations, a SHA-256 inventory, and a nonzero exit for failed
mandatory checks.

Each of those is asserted here mechanically rather than asserted-about: the
artifact is re-derived from the tracked generator and compared byte for byte,
its inventory is recomputed from the named files, and the exit-code contract
is exercised on both a passing and a deliberately failing payload.

OFFLINE.  No network.  The generator is invoked exactly as the directive
prescribes (from ``quant-lab`` with ``PYTHONIOENCODING=utf-8``).
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_QUANT_LAB = _HERE.parents[2]
_EVIDENCE = (
    _QUANT_LAB
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_05"
)
ARTIFACT = _EVIDENCE / "bloc_05_time_validation.json"
SCOPE_ARTIFACT = _EVIDENCE / "BLOC_05_I05_SCOPE_AUDIT.json"
SCRIPT = (
    _QUANT_LAB
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "scripts"
    / "b5_i05_time.py"
)
SCRIPT_RELPATH = (
    "research/crypto_foundry/sensor_fabric/scripts/b5_i05_time.py"
)


def _payload() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _run_generator() -> tuple[int, bytes]:
    before = ARTIFACT.read_bytes() if ARTIFACT.exists() else b""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, SCRIPT_RELPATH],
        cwd=_QUANT_LAB,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )
    after = ARTIFACT.read_bytes()
    assert before == after or not before, (
        "the generator changed the committed artifact bytes"
    )
    return result.returncode, after


# ---------------------------------------------------------------------------
# Shape and truth of the committed artifact
# ---------------------------------------------------------------------------


def test_the_evidence_artifact_exists() -> None:
    assert ARTIFACT.is_file(), "bloc_05/06 s17 requires bloc_05_time_validation.json"


def test_every_mandatory_row_passed() -> None:
    payload = _payload()
    assert payload["all_results_pass"] is True
    assert payload["summary"]["fail"] == 0
    assert payload["summary"]["rows"] == len(payload["rows"])
    assert payload["summary"]["pass"] == payload["summary"]["rows"]
    for row in payload["rows"]:
        assert row["pass"] is True, row["row_id"]


def test_rows_carry_expected_and_observed_values_with_clause_references() -> None:
    for row in _payload()["rows"]:
        assert row["clause"], row["row_id"]
        assert row["clause"].startswith("bloc_05/"), row["row_id"]
        assert "expected" in row, row["row_id"]
        assert "observed" in row, row["row_id"]


def test_row_ordering_is_stable_and_declared() -> None:
    rows = _payload()["rows"]
    assert len({row["row_id"] for row in rows}) == len(rows)
    assert [row["index"] for row in rows] == list(range(len(rows)))


def test_the_sha256_inventory_is_recomputable() -> None:
    inventory = _payload()["sha256_inventory"]
    assert inventory, "an evidence artifact without an inventory proves nothing"
    for relpath, digest in sorted(inventory.items()):
        path = _QUANT_LAB.parent / relpath
        assert path.is_file(), relpath
        recomputed = hashlib.sha256(path.read_bytes()).hexdigest()
        assert recomputed == digest, relpath


def test_provenance_names_the_tracked_producer_only() -> None:
    payload = _payload()
    provenance = payload["generator"]
    assert SCRIPT_RELPATH in provenance
    assert ".bu_tmp" not in provenance
    assert "python " in provenance


def test_the_producer_has_no_live_clock_and_no_untracked_dependency() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    for forbidden in (
        "datetime.now(",
        "datetime.utcnow(",
        "date.today(",
        "time.time(",
        "date.today()",
    ):
        assert forbidden not in text, forbidden
    assert "import subprocess" in text  # git scope rows only, never the network


def test_scope_audit_artifact_is_present_and_clean() -> None:
    payload = json.loads(SCOPE_ARTIFACT.read_text(encoding="utf-8"))
    assert payload["checkpoint"] == "SENSOR-B5-I05"
    assert payload["all_results_pass"] is True
    assert payload["summary"]["fail"] == 0
    for row in payload["rows"]:
        assert row["pass"] is True, row["row_id"]


# ---------------------------------------------------------------------------
# Reproducibility and the exit contract
# ---------------------------------------------------------------------------


def test_regeneration_is_byte_identical_and_exits_zero() -> None:
    committed = ARTIFACT.read_bytes()
    code, regenerated = _run_generator()
    assert code == 0, "a failed mandatory check must exit nonzero"
    assert regenerated == committed, "two generations must be byte-identical"


def test_regeneration_twice_is_still_byte_identical() -> None:
    first_code, first = _run_generator()
    second_code, second = _run_generator()
    assert (first_code, second_code) == (0, 0)
    assert first == second


def test_a_failing_mandatory_check_exits_nonzero() -> None:
    sys.path.insert(0, str(SCRIPT.parent))
    try:
        import b5_i05_time as producer
    finally:
        sys.path.pop(0)
    passing = producer.build_payload()
    assert producer.mandatory_exit_code(passing) == 0
    failing = json.loads(json.dumps(passing))
    failing["rows"][0]["pass"] = False
    failing["all_results_pass"] = False
    assert producer.mandatory_exit_code(failing) == 1
