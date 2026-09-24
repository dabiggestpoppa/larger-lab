"""SENSOR-B4-I08R2R1A — measured evidence truth and false-green counterfactual."""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from _sibling_import import load_sibling  # noqa: E402

_r2 = load_sibling("_i08r2r1_truth_r2_mod", "test_i08r2_evidence")


def evaluate_case(case: dict[str, Any]) -> str:
    """Derive a matrix verdict only from its declared required invariants."""
    required = case.get("required_invariants")
    if not isinstance(required, list) or not required:
        raise AssertionError(f"case has no required_invariants: {case!r}")
    if len(required) != len(set(required)):
        raise AssertionError(f"case has duplicate required invariants: {case!r}")
    return (
        "OK"
        if all(case.get(invariant) is True for invariant in required)
        else "FAIL"
    )


def _case(payload: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(payload)


def test_corrected_r2_lock_scenarios_use_replay_report_truth(
    tmp_path: Path,
) -> None:
    matrix = _r2.measure_i08r2_lock_clear_atomicity_matrix(tmp_path)
    cases = {row["case"]: row for row in matrix["cases"]}
    crash = cases["crash_after_unlink_replays_original"]
    present = cases["present_lock_intent_not_false_completed"]

    assert crash["apply_return_is_not_replay_report"] is True
    assert crash["replay_closed"] is True
    assert evaluate_case(crash) == "OK"
    assert present["apply_return_is_not_replay_report"] is True
    assert present["no_action"] is True
    assert present["report_left_open"] is True
    assert evaluate_case(present) == "OK"


def test_required_predicate_counterfactual_emits_fail() -> None:
    payload = {
        "case": "counterfactual_required_predicate_false",
        "completed": True,
        "one_action": True,
        "replay_closed": False,
        "required_invariants": ["completed", "one_action", "replay_closed"],
        "result": "OK",
    }
    assert evaluate_case(payload) == "FAIL"
    payload["result"] = evaluate_case(payload)
    assert payload["result"] == "FAIL"


def test_meta_evaluator_rejects_missing_or_nonboolean_invariant() -> None:
    for required in ([], ["completed", "completed"]):
        try:
            evaluate_case(
                {"case": "invalid", "completed": True, "required_invariants": required}
            )
        except AssertionError:
            pass
        else:  # pragma: no cover - assertion contract
            raise AssertionError("invalid required invariant declaration accepted")

    missing = _case(
        {
            "case": "missing",
            "required_invariants": ["completed"],
            "result": "OK",
        }
    )
    assert evaluate_case(missing) == "FAIL"
    nonboolean = _case(
        {
            "case": "nonboolean",
            "completed": "true",
            "required_invariants": ["completed"],
            "result": "OK",
        }
    )
    assert evaluate_case(nonboolean) == "FAIL"
