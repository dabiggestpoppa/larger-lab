"""SENSOR-B4-I07R1I — deterministic machine-evidence matrices.

Builders are PURE: they run the real scenarios in tmp dirs and return dicts
serialized through ``stable_evidence_bytes``.  Normal pytest runs NEVER
write the committed evidence tree — tests generate to memory/tmp_path and
compare against committed bytes (I05R4 read-only policy, I07R1I §29).
Publication happens once per checkpoint via an explicit operator invocation
(module bottom).

Matrices (I07R1I §27):
- BLOC_04_I07R1I_FAILED_GATE_ATOMICITY_MATRIX.json
- BLOC_04_I07R1I_LEDGER_STRUCTURE_MATRIX.json

Every case payload is structural only (booleans, statuses, counts, names) —
no timings, no wall-clock, no paths — so regeneration is byte-stable.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

# Make the sibling loader importable regardless of pytest invocation
# directory (importlib mode + competing repo-root ``tests`` package).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest

from _sibling_import import load_sibling

EVIDENCE_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)

_NO_ERROR = "NO_ERROR"


def stable_evidence_bytes(payload: dict) -> bytes:
    """Canonical deterministic serializer (I05R4 §31 doctrine)."""
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _case(name: str, **fields) -> dict:
    return {"case": name, **fields}


def _load_base():
    return load_sibling("_i07r1_base_mod", "test_job_state_r1")


def _load_r1h():
    return load_sibling("_i07r1h_mod", "test_job_state_r1h")


def _load_r1i():
    return load_sibling("_i07r1i_mod", "test_job_state_r1i")


# ---------------------------------------------------------------------------
# Matrix 1 — failed-gate atomicity + validated public reads (§5-§21)
# ---------------------------------------------------------------------------


def build_failed_gate_atomicity_matrix(tmp: Path) -> dict:
    """Every required I07R1I case, measured on the real durable stack."""
    r1i = _load_r1i()
    r1h = _load_r1h()
    base = _load_base()
    cases: list[dict] = []

    # -- A/B/C/D/E — first failure, then the SAME-THREAD retry ------------
    _stack, repo, job_id = r1i._corrupt_scenario(tmp / "retry", "job-retry")
    counters = r1i._instrument(repo, job_id)
    first = r1i._classify(
        lambda: repo.advance_status(job_id, **r1i._CONTINUATION)
    )
    validate_after_first = counters.validate
    second = r1i._classify(
        lambda: repo.advance_status(job_id, **r1i._CONTINUATION)
    )
    cases.append(
        _case(
            "first_corrupt_attempt",
            error=first,
            typed=first == r1i.CORRUPTION,
            result="PASS" if first == r1i.CORRUPTION else "FAIL",
        )
    )
    cases.append(
        _case(
            "same_thread_second_attempt",
            error=second,
            typed=second == r1i.CORRUPTION,
            forged_head_not_adopted=second != _NO_ERROR,
            result="PASS" if second == r1i.CORRUPTION else "FAIL",
        )
    )
    cases.append(
        _case(
            "second_attempt_revalidated",
            validations_after_first=validate_after_first,
            validations_after_second=counters.validate,
            refreshes_after_second=counters.refresh,
            nested_shortcut_taken=counters.validate == validate_after_first,
            result=(
                "PASS"
                if validate_after_first == 1 and counters.validate == 2
                else "FAIL"
            ),
        )
    )
    cases.append(
        _case(
            "owner_state_rolled_back",
            owner_present=job_id in repo._lock_owners,
            result="PASS" if job_id not in repo._lock_owners else "FAIL",
        )
    )
    cases.append(
        _case(
            "owned_physical_lock_rolled_back",
            lock_file_present=repo._lock_path(job_id).exists(),
            result=(
                "PASS" if not repo._lock_path(job_id).exists() else "FAIL"
            ),
        )
    )

    # -- F — a second thread must see corruption, not a leaked lock -------
    _stack, repo_f, job_f = r1i._corrupt_scenario(tmp / "thread", "job-thread")
    r1i._classify(lambda: repo_f.advance_status(job_f, **r1i._CONTINUATION))
    other = r1i._in_thread(
        lambda: repo_f.advance_status(job_f, **r1i._CONTINUATION)
    )
    cases.append(
        _case(
            "other_thread_no_leaked_lock",
            error=other,
            locked_out=(other == r1i.LOCK_HELD),
            result="PASS" if other == r1i.CORRUPTION else "FAIL",
        )
    )

    # -- G/H — catalog-refresh failure rollback, both catalogs ------------
    for catalog, case_name in (
        ("births", "birth_catalog_refresh_failure_rollback"),
        ("events", "event_catalog_refresh_failure_rollback"),
    ):
        _stack, repo_c = r1h._build_chain(tmp / catalog, f"job-{catalog}")
        fragment = r1i._inject_malformed_fragment(tmp / catalog, catalog)
        counters_c = r1i._instrument(repo_c, f"job-{catalog}")
        error = r1i._classify(
            lambda: repo_c.advance_status(
                f"job-{catalog}", **r1i._CONTINUATION
            )
        )
        owner_clean = f"job-{catalog}" not in repo_c._lock_owners
        lock_clean = not repo_c._lock_path(f"job-{catalog}").exists()
        fragment.unlink()
        recovered = r1i._classify(
            lambda: repo_c.advance_status(f"job-{catalog}", **r1i._FORWARD)
        )
        cases.append(
            _case(
                case_name,
                error=error,
                typed=error == r1i.CATALOG_CORRUPTION,
                owner_rolled_back=owner_clean,
                owned_lock_rolled_back=lock_clean,
                fresh_outer_entry_after=recovered == _NO_ERROR,
                refreshes=counters_c.refresh,
                validations=counters_c.validate,
                result=(
                    "PASS"
                    if (
                        error == r1i.CATALOG_CORRUPTION
                        and owner_clean
                        and lock_clean
                        and recovered == _NO_ERROR
                        and counters_c.refresh == 2
                    )
                    else "FAIL"
                ),
            )
        )

    # -- I/J — direct public reads, no prior write ------------------------
    _stack, repo_i, job_i = r1i._corrupt_scenario(tmp / "get", "job-get")
    get_error = r1i._classify(lambda: repo_i.get_job(job_i))
    cases.append(
        _case(
            "direct_get_job_corruption_rejected",
            error=get_error,
            typed=get_error == r1i.CORRUPTION,
            validation_required_by_read=True,
            result="PASS" if get_error == r1i.CORRUPTION else "FAIL",
        )
    )
    _stack, repo_j, job_j = r1i._corrupt_scenario(tmp / "list", "job-list")
    list_error = r1i._classify(lambda: repo_j.list_transitions(job_j))
    cases.append(
        _case(
            "direct_list_transitions_corruption_rejected",
            error=list_error,
            typed=list_error == r1i.CORRUPTION,
            invalid_transition_exposed=False
            if list_error == r1i.CORRUPTION
            else True,
            result="PASS" if list_error == r1i.CORRUPTION else "FAIL",
        )
    )

    # -- K/L — valid public reads -----------------------------------------
    _stack, repo_v = r1h._build_chain(tmp / "valid", "job-valid")
    try:
        state = repo_v.get_job("job-valid")
        get_ok = state.status.value
    except BaseException as exc:  # noqa: BLE001 — recorded below
        get_ok = type(exc).__name__
    try:
        transitions = repo_v.list_transitions("job-valid")
        list_ok: Any = len(transitions)
    except BaseException as exc:  # noqa: BLE001 — recorded below
        list_ok = type(exc).__name__
    cases.append(
        _case(
            "valid_get_job",
            status=get_ok,
            result="PASS" if get_ok == "ACQUIRING" else "FAIL",
        )
    )
    cases.append(
        _case(
            "valid_list_transitions",
            transition_count=list_ok,
            result="PASS" if list_ok == 8 else "FAIL",
        )
    )

    # -- M/N — cross-repository valid publication through a public read ---
    stack_x, writer = r1h._build_chain(tmp / "cross", "job-cross")
    reader = base.JobStack(tmp / "cross", clock=stack_x.clock).repo
    before = len(reader.list_transitions("job-cross"))
    writer.advance_status("job-cross", **r1i._FORWARD)
    cross_state = r1i._classify(lambda: reader.get_job("job-cross"))
    cross_after = len(reader.list_transitions("job-cross"))
    cases.append(
        _case(
            "cross_repo_valid_get_job",
            error=cross_state,
            refreshed_head_visible=cross_state == _NO_ERROR,
            result="PASS" if cross_state == _NO_ERROR else "FAIL",
        )
    )
    cases.append(
        _case(
            "cross_repo_valid_list_transitions",
            transitions_before=before,
            transitions_after=cross_after,
            result="PASS" if cross_after == before + 1 else "FAIL",
        )
    )

    # -- O — the legitimate empty path ------------------------------------
    fresh_stack = base.JobStack(tmp / "create")
    fresh_repo = fresh_stack.repo
    created = r1i._classify(
        lambda: fresh_repo.create_job(
            job_id="job-fresh",
            provider_id="KRAKEN_FUTURES",
            sensor_family=base.SensorFamily.MECHANICAL_FUNDING,
            request_fingerprint=base._FP,
        )
    )
    empty_ok = r1i._classify(lambda: fresh_repo.get_job("job-fresh"))
    cases.append(
        _case(
            "create_job_empty_path",
            create_error=created,
            gated_read_error=empty_ok,
            no_lock_left=not fresh_repo._lock_path("job-fresh").exists(),
            result=(
                "PASS"
                if created == _NO_ERROR and empty_ok == _NO_ERROR
                else "FAIL"
            ),
        )
    )

    # -- §21 counterfactual — neutralize the rollback, measure the leak ---
    cases.append(_rollback_disabled_counterfactual(tmp / "neutralized"))

    # -- §26 upstream control — I07R1H intact refreshed head still adopted -
    control = next(
        case for case in r1h.CASES if case.expectation == "ACCEPT"
    )
    outcome = r1h.run_chain_case(tmp / "control", control)
    cases.append(
        _case(
            "i07r1h_intact_refreshed_control",
            runtime_error=outcome["runtime_path"],
            restart_error=outcome["restart_path"],
            adoption_proven=(
                outcome["events_after"] == outcome["events_before"] + 1
            ),
            result=outcome["result"],
        )
    )

    return {
        "matrix": "BLOC_04_I07R1I_FAILED_GATE_ATOMICITY_MATRIX",
        "checkpoint": "SENSOR-B4-I07R1I",
        "doctrine": (
            "I07R1I \u00a74-\u00a721 — a failed gate entry is not a live "
            "reentrant context: validation failure must never weaken the "
            "next validation attempt, and public reads must cross the same "
            "per-job gate as writes"
        ),
        "cases": cases,
    }


def _rollback_disabled_counterfactual(tmp: Path) -> dict:
    """§21: disable ONLY the new rollback and re-measure the same scenario.

    Deterministic neutralization (no production edit): with the rollback
    neutralized, the first failure leaks its owner record, so the immediate
    SAME-THREAD retry classifies itself as nested, skips refresh +
    validation and adopts the forged head — the exact defect this
    checkpoint seals.
    """
    r1i = _load_r1i()
    import crypto_sensor_fabric.storage.jobs as jobs_module

    _stack, repo, job_id = r1i._corrupt_scenario(tmp, "job-neutralized")
    counters = r1i._instrument(repo, job_id)
    real_rollback = jobs_module._NestedFileLock._rollback_outer_entry
    jobs_module._NestedFileLock._rollback_outer_entry = (  # type: ignore[method-assign]
        lambda self: None
    )
    try:
        first = r1i._classify(
            lambda: repo.advance_status(job_id, **r1i._CONTINUATION)
        )
        validations_after_first = counters.validate
        second = r1i._classify(
            lambda: repo.advance_status(job_id, **r1i._CONTINUATION)
        )
        leaked_owner = job_id in repo._lock_owners
        leaked_lock = repo._lock_path(job_id).exists()
        validations_after_second = counters.validate
    finally:
        jobs_module._NestedFileLock._rollback_outer_entry = (  # type: ignore[method-assign]
            real_rollback
        )

    return _case(
        "counterfactual_rollback_disabled",
        first_error=first,
        second_error=second,
        validations_after_first=validations_after_first,
        validations_after_second=validations_after_second,
        owner_leaked=leaked_owner,
        owned_lock_file_leaked=leaked_lock,
        second_attempt_skipped_validation=(
            validations_after_second == validations_after_first
        ),
        second_attempt_adopted_forged_head=(second == _NO_ERROR),
        result=(
            "PASS"
            if (
                first == r1i.CORRUPTION
                and second == _NO_ERROR
                and validations_after_second == validations_after_first
                and leaked_owner
                and leaked_lock
            )
            else "FAIL"
        ),
    )


# ---------------------------------------------------------------------------
# Matrix 2 — the top-level operator ledger structure (§22-§24)
# ---------------------------------------------------------------------------


def build_ledger_structure_matrix(tmp: Path) -> dict:
    """The top-level ``## Current state`` table only (§23)."""
    r1i = _load_r1i()
    rows = r1i._current_state_rows()
    cell_counts = [len(row) for row in rows]
    checkpoint_rows = [row for row in rows if row[0] == "Current checkpoint"]
    table = "\n".join("|".join(row) for row in rows).replace(" = ", "=")

    two_columns = bool(rows) and all(count == 2 for count in cell_counts)
    one_checkpoint_row = len(checkpoint_rows) == 1
    checkpoint_cells = len(checkpoint_rows[0]) if checkpoint_rows else 0
    hold_truthful = all(
        f"{key}=OPERATOR_HOLD" in table for key in r1i._HOLD_KEYS
    )
    proposal_matches = (
        "PASS_SENSOR_B4_I07R1I_FAILED_GATE_ATOMICITY_VALIDATED_READ_SEALED"
        "=PENDING_OPERATOR_REVIEW" in table
    )
    durable_pending = (
        "DURABLE_RESUME_IMPLEMENTED=PENDING_OPERATOR_ACCEPTANCE" in table
    )
    recovery_absent = "RECOVERY_SCANNER_IMPLEMENTED=FALSE" in table
    next_unauthorized = "next_checkpoint_authorized=FALSE" in table

    cases = [
        _case(
            "current_state_table_two_columns",
            row_count=len(rows),
            cell_counts=cell_counts,
            malformed_rows=sum(1 for count in cell_counts if count != 2),
            result="PASS" if two_columns else "FAIL",
        ),
        _case(
            "current_checkpoint_exactly_one_row",
            checkpoint_row_count=len(checkpoint_rows),
            result="PASS" if one_checkpoint_row else "FAIL",
        ),
        _case(
            "no_duplicate_trailing_current_checkpoint_cell",
            checkpoint_cell_count=checkpoint_cells,
            result="PASS" if checkpoint_cells == 2 else "FAIL",
        ),
        _case(
            "i07_hold_chain_truthful",
            hold_keys=list(r1i._HOLD_KEYS),
            proposal_pending=proposal_matches,
            result="PASS" if (hold_truthful and proposal_matches) else "FAIL",
        ),
        _case(
            "durable_resume_pending_acceptance",
            durable_resume_implemented="PENDING_OPERATOR_ACCEPTANCE",
            recovery_scanner_implemented=False,
            result=(
                "PASS" if (durable_pending and recovery_absent) else "FAIL"
            ),
        ),
        _case(
            "next_checkpoint_not_authorized",
            next_checkpoint_authorized=False,
            recommended_next="SENSOR-B4-I08 (operator acceptance first)",
            result="PASS" if next_unauthorized else "FAIL",
        ),
    ]
    return {
        "matrix": "BLOC_04_I07R1I_LEDGER_STRUCTURE_MATRIX",
        "checkpoint": "SENSOR-B4-I07R1I",
        "doctrine": (
            "I07R1I \u00a722-\u00a724 — the top-level Current state table "
            "is a two-column Field|Value schema; the Current checkpoint row "
            "carries exactly one cell of operator truth"
        ),
        "cases": cases,
    }


BUILDERS = [
    (
        "build_failed_gate_atomicity_matrix",
        "BLOC_04_I07R1I_FAILED_GATE_ATOMICITY_MATRIX.json",
    ),
    (
        "build_ledger_structure_matrix",
        "BLOC_04_I07R1I_LEDGER_STRUCTURE_MATRIX.json",
    ),
]


@pytest.mark.parametrize("builder_name,filename", BUILDERS)
def test_generated_matches_committed(
    builder_name: str, filename: str, tmp_path
) -> None:
    committed = (EVIDENCE_DIR / filename).read_bytes()
    builder = globals()[builder_name]
    generated = stable_evidence_bytes(builder(tmp_path / builder_name))
    assert generated == committed, (
        f"{filename}: regenerated evidence diverges from committed bytes — "
        "a production behavior changed; update the checkpoint evidence "
        "explicitly, never via pytest execution"
    )


def test_evidence_directory_untouched_after_run(tmp_path) -> None:
    before = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(EVIDENCE_DIR.glob("*.json"))
    }
    for builder_name, _ in BUILDERS:
        globals()[builder_name](tmp_path / builder_name)
    after = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(EVIDENCE_DIR.glob("*.json"))
    }
    assert before == after


def _publish() -> None:
    """EXPLICIT one-time publication (operator action, never pytest)."""
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    for builder_name, filename in BUILDERS:
        builder = globals()[builder_name]
        target = EVIDENCE_DIR / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(stable_evidence_bytes(builder(tmp / builder_name)))
        print(f"published {target}")


if __name__ == "__main__":
    _publish()
