"""SENSOR-B4-I07R1I — failed-gate atomicity + validated public reads.

The remaining seam (I07R1I §3-§7): ``_NestedFileLock.__enter__`` acquired
the per-job physical lock, installed ``_lock_owners[job_id]`` and THEN ran
``_refresh_durable_truth`` (both catalog refreshes + the shared per-job
chain authority).  If that gate raised, ``__exit__`` never ran: the
``except`` released only the in-process RLock, so the owner record and the
physical lock survived.  The NEXT same-thread operation on that job then
classified itself as NESTED and skipped acquire/refresh/validate entirely —
a rejected gate became a live reentrant context, and validation failure
weakened the next validation attempt.

Separately (§13-§16): ``get_job`` / ``list_transitions`` read the catalogs
directly, so durable-but-invalid state a long-lived repository had just
adopted from disk by refresh was readable as validated runtime truth.

Every case here uses the proven I07R1G/I07R1H attack shape: the repository
is constructed FIRST, a legitimate chain exists, and a chain-invalid (but
catalog-valid, and where present checkpoint-proof-valid) later event is
published at its CORRECT hashed physical key.  The outer lock refresh
adopts it; the shared chain authority must reject it BEFORE any runtime
decision reads it — on the write path and on the public read path alike.

Read-only against the committed evidence tree; real durable stack only.
"""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from typing import Any

# Make the sibling loader importable regardless of pytest invocation
# directory (importlib mode + competing repo-root ``tests`` package).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest
from crypto_sensor_fabric.storage.enums import StorageJobStatus
from crypto_sensor_fabric.storage.jobs import (
    JobCatalogCorrupt,
    JobLockHeld,
    JobUnknown,
)
from crypto_sensor_fabric.storage.json_catalog import JsonCatalogCorrupt

from _sibling_import import extract_checkpoint_section, load_sibling

_base = load_sibling("_i07r1_base_mod", "test_job_state_r1")
_r1h = load_sibling("_i07r1h_mod", "test_job_state_r1h")

_create = _base._create

CHECKPOINT = StorageJobStatus.CHECKPOINT_ADVANCED
ACQUIRING = StorageJobStatus.ACQUIRING
PLANNED = StorageJobStatus.PLANNED

#: The annotated continuation edge — the probe every corrupt-chain case
#: requests.  It is rejected during lock ENTRY (refresh + chain
#: validation), so the requested transition is never reached.
_CONTINUATION = {"to_status": ACQUIRING, "reason": "batch continuation"}

#: One legitimate FORWARD step from the ACQUIRING head `_build_chain` leaves
#: behind — the probe used where the gate must actually succeed.
_FORWARD = {"to_status": StorageJobStatus.RAW_STAGED}

NO_ERROR = "NO_ERROR"
CORRUPTION = JobCatalogCorrupt.__name__
CATALOG_CORRUPTION = JsonCatalogCorrupt.__name__
LOCK_HELD = JobLockHeld.__name__


def _classify(action: Any) -> str:
    """Run ``action``; return its error class name, or ``NO_ERROR``."""
    try:
        action()
    except BaseException as exc:  # noqa: BLE001 — classified by name
        return type(exc).__name__
    return NO_ERROR

#: Upstream I07 approval keys that must remain OPERATOR_HOLD (§24/§36).
_HOLD_KEYS = (
    "PASS_SENSOR_B4_I07R1H_REFRESHED_CHAIN_VALIDATION_PARITY_SEALED",
    "PASS_SENSOR_B4_I07R1G_RUNTIME_PROOF_SCHEMA_REPLAY_PARITY_SEALED",
    "PASS_SENSOR_B4_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEALED",
    "PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED",
    "PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED",
)


# ---------------------------------------------------------------------------
# Attack shape + instrumentation
# ---------------------------------------------------------------------------


def _corrupt_scenario(
    root: Path, name: str = "job-r1i"
) -> tuple[Any, Any, str]:
    """Legitimate chain, then a chain-invalid later head published externally.

    Built with the I07R1H forged-head shape (repository FIRST), so the
    next operation on the job takes the outer lock, refreshes both
    catalogs — adopting the forged head — and must be rejected by the
    shared chain authority rather than consumed as runtime state.
    """
    stack, repo = _r1h._build_chain(root, name)
    _r1h._publish_forged_head(
        root,
        _r1h.ChainCase("r1i-forge", _r1h._from_status_chain_break),
        name,
    )
    return stack, repo, name


class _Counters:
    """Deterministic per-job gate counters (I07R1I §10)."""

    def __init__(self) -> None:
        self.refresh = 0
        self.validate = 0


def _instrument(repo: Any, job_id: str) -> _Counters:
    """Count real outer-lock refreshes and chain validations for ``job_id``.

    Both are counted: ``_refresh_durable_truth`` drives ``_validate_job_chain``
    on the instance, so a nested-shortcut regression shows up as a counter
    that does not advance on the second attempt.
    """
    counters = _Counters()
    original_refresh = repo._refresh_durable_truth
    original_validate = repo._validate_job_chain

    def refresh(target: str) -> None:
        if target == job_id:
            counters.refresh += 1
        original_refresh(target)

    def validate(target: str) -> None:
        if target == job_id:
            counters.validate += 1
        original_validate(target)

    repo._refresh_durable_truth = refresh
    repo._validate_job_chain = validate
    return counters


def _in_thread(action: Any) -> str:
    """Run ``action`` on a FRESH thread; return its error class name."""
    box: dict[str, str] = {}

    def run() -> None:
        box["error"] = _classify(action)

    thread = threading.Thread(target=run)
    thread.start()
    thread.join(timeout=60)
    assert not thread.is_alive(), "second thread never completed"
    return box.get("error", NO_ERROR)


def _inject_malformed_fragment(root: Path, catalog: str) -> Path:
    """Publish an unparseable fragment into ONE job-state catalog.

    A real durable-truth failure: an external writer left a corrupt
    committed fragment behind.  ``refresh()`` must fail closed with the
    typed catalog error, AFTER the physical job lock is held.
    """
    directory = _r1h._events_dir(root)
    if catalog == "births":
        directory = directory.parent / "jobs"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "not-a-fragment.json"
    path.write_text("{ this is not valid json", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# §3-§11 — first failure, then the SAME-THREAD retry
# ---------------------------------------------------------------------------


def test_first_corrupt_attempt_fails_closed(tmp_path: Path) -> None:
    """(A) The refreshed forged head is rejected, not consumed (§3)."""
    _stack, repo, job_id = _corrupt_scenario(tmp_path)
    with pytest.raises(JobCatalogCorrupt):
        repo.advance_status(job_id, **_CONTINUATION)


def test_same_thread_second_attempt_fails_closed_and_revalidates(
    tmp_path: Path,
) -> None:
    """(B, C) A rejected gate never becomes a live reentrant context (§3/§4).

    The second operation must NOT take the nested shortcut: it re-enters as
    a fresh outer context, re-refreshes and re-validates, and fails closed
    again.  Two real validation attempts, no forged adoption.
    """
    _stack, repo, job_id = _corrupt_scenario(tmp_path)
    counters = _instrument(repo, job_id)

    with pytest.raises(JobCatalogCorrupt):
        repo.advance_status(job_id, **_CONTINUATION)
    first_refresh, first_validate = counters.refresh, counters.validate

    with pytest.raises(JobCatalogCorrupt):
        repo.advance_status(job_id, **_CONTINUATION)

    assert first_validate == 1, first_validate
    assert counters.validate == 2, counters.validate
    assert counters.refresh == 2, counters.refresh
    assert (first_refresh, first_validate) == (1, 1)


def test_failed_outer_entry_rolls_back_owner_state(tmp_path: Path) -> None:
    """(D) No stale owner record / nesting depth survives the failure (§8)."""
    _stack, repo, job_id = _corrupt_scenario(tmp_path)
    with pytest.raises(JobCatalogCorrupt):
        repo.advance_status(job_id, **_CONTINUATION)
    assert job_id not in repo._lock_owners, repo._lock_owners


def test_failed_outer_entry_rolls_back_owned_physical_lock(
    tmp_path: Path,
) -> None:
    """(E) The lock THIS attempt acquired is released on failure (§9)."""
    _stack, repo, job_id = _corrupt_scenario(tmp_path)
    with pytest.raises(JobCatalogCorrupt):
        repo.advance_status(job_id, **_CONTINUATION)
    assert not repo._lock_path(job_id).exists(), repo._lock_path(job_id)


def test_other_thread_sees_corruption_not_leaked_lock(tmp_path: Path) -> None:
    """(F) Current-process cleanup did not leak the physical lock (§11).

    A second thread must acquire the job lock normally and then fail closed
    on the SAME corrupt chain — ``JobCatalogCorrupt``, never ``JobLockHeld``.
    """
    _stack, repo, job_id = _corrupt_scenario(tmp_path)
    with pytest.raises(JobCatalogCorrupt):
        repo.advance_status(job_id, **_CONTINUATION)

    error = _in_thread(lambda: repo.advance_status(job_id, **_CONTINUATION))
    assert error == JobCatalogCorrupt.__name__, error
    assert job_id not in repo._lock_owners, repo._lock_owners


# ---------------------------------------------------------------------------
# §12 — the rollback rule is broader than the chain authority
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("catalog", ["births", "events"])
def test_catalog_refresh_failure_rolls_back(
    tmp_path: Path, catalog: str
) -> None:
    """(G, H) ANY post-acquisition ``__enter__`` failure rolls back (§12).

    ``_births.refresh()`` and ``_events.refresh()`` are injected
    independently so both post-lock refresh steps are covered.  Expected:
    the typed ORIGINAL catalog failure, no owner entry, no owned lock file,
    and a genuine fresh outer entry on the next same-thread call.
    """
    _stack, repo = _r1h._build_chain(tmp_path, "job-refresh")
    fragment = _inject_malformed_fragment(tmp_path, catalog)
    counters = _instrument(repo, "job-refresh")

    with pytest.raises(JsonCatalogCorrupt):
        repo.advance_status("job-refresh", **_CONTINUATION)

    assert counters.refresh == 1, counters.refresh
    # The refresh itself aborted, so the chain authority never ran.
    assert counters.validate == 0, counters.validate
    assert "job-refresh" not in repo._lock_owners, repo._lock_owners
    assert not repo._lock_path("job-refresh").exists()

    # The corruption is gone; the next call must perform a FRESH outer entry
    # (a leaked owner record would have made it a no-op nested one).
    fragment.unlink()
    state = repo.advance_status("job-refresh", **_FORWARD)
    assert state.status is StorageJobStatus.RAW_STAGED
    assert counters.refresh == 2, counters.refresh
    assert counters.validate == 1, counters.validate
    assert "job-refresh" not in repo._lock_owners


# ---------------------------------------------------------------------------
# §6-§7 — foreign locks and cleanup-error precedence
# ---------------------------------------------------------------------------


def test_foreign_lock_is_never_auto_deleted(tmp_path: Path) -> None:
    """§6: a pre-existing lock is I08 evidence, never this attempt's to clean.

    ``_acquire_file_lock`` fails before any handle or owner entry is
    installed, so the foreign lock file must survive untouched.
    """
    _stack, repo, job_id = _corrupt_scenario(tmp_path)
    repo._lock_timeout_seconds = 0.05
    foreign = repo._lock_path(job_id)
    foreign.parent.mkdir(parents=True, exist_ok=True)
    foreign.write_text("stale foreign lock\n", encoding="utf-8")

    with pytest.raises(JobLockHeld):
        repo.get_job(job_id)

    assert foreign.exists(), "a foreign/stale lock must never be deleted"
    assert job_id not in repo._lock_owners, repo._lock_owners


def test_cleanup_error_does_not_mask_validation_error(
    tmp_path: Path,
) -> None:
    """§7: the corruption diagnosis stays authoritative over cleanup faults.

    The owner record is rolled back BEFORE the release is attempted, so a
    failing release leaves recovery evidence (the lock file) without
    replacing the original ``JobCatalogCorrupt``.
    """
    _stack, repo, job_id = _corrupt_scenario(tmp_path)

    def blocked_release(handle: Any, target: str) -> None:
        raise OSError("release blocked")

    repo._release_file_lock = blocked_release
    with pytest.raises(JobCatalogCorrupt):
        repo.advance_status(job_id, **_CONTINUATION)

    assert job_id not in repo._lock_owners, repo._lock_owners
    assert repo._lock_path(job_id).exists(), "unreleased lock is I08 evidence"


# ---------------------------------------------------------------------------
# §13-§15 — public reads cross the same validation boundary
# ---------------------------------------------------------------------------


def test_direct_get_job_rejects_refresh_adopted_corruption(
    tmp_path: Path,
) -> None:
    """(I, §20) ``get_job`` alone must trigger validation — no prior write."""
    _stack, repo, job_id = _corrupt_scenario(tmp_path)
    with pytest.raises(JobCatalogCorrupt):
        repo.get_job(job_id)


def test_direct_list_transitions_rejects_refresh_adopted_corruption(
    tmp_path: Path,
) -> None:
    """(J, §20) ``list_transitions`` never exposes an invalid transition."""
    _stack, repo, job_id = _corrupt_scenario(tmp_path)
    with pytest.raises(JobCatalogCorrupt):
        repo.list_transitions(job_id)


def test_public_reads_do_not_read_refresh_adopted_state(
    tmp_path: Path,
) -> None:
    """§13: a cached durable-but-invalid tail is NOT readable runtime truth.

    Proves the rejection is specific to VALIDITY, not to the record having
    arrived through refresh: the forged head IS in the catalog cache when
    the read refuses it.
    """
    _stack, repo, job_id = _corrupt_scenario(tmp_path)
    repo._events.refresh()  # adopt the forged fragment on purpose
    forged = _r1h._job_events(tmp_path, job_id)[-1]
    assert repo._events.has(forged["transition_id"])
    with pytest.raises(JobCatalogCorrupt):
        repo.get_job(job_id)
    with pytest.raises(JobCatalogCorrupt):
        repo.list_transitions(job_id)


# ---------------------------------------------------------------------------
# §19 — valid public reads stay green
# ---------------------------------------------------------------------------


def test_valid_public_reads_are_green(tmp_path: Path) -> None:
    """(K, L) The validated read path preserves legitimate reads."""
    _stack, repo = _r1h._build_chain(tmp_path, "job-valid")
    state = repo.get_job("job-valid")
    assert state.status is ACQUIRING
    assert state.job_id == "job-valid"
    transitions = repo.list_transitions("job-valid")
    assert len(transitions) == 8, len(transitions)
    assert transitions[-1].to_status is ACQUIRING


def test_cross_repository_valid_publication_is_visible(
    tmp_path: Path,
) -> None:
    """(M, N) A long-lived reader sees a valid cross-repository publication.

    The reader repository is constructed BEFORE the writer advances the
    job, so only the read-path refresh can make the new head visible — and
    it must be visible, on both ``get_job`` and ``list_transitions``.
    """
    stack, writer = _r1h._build_chain(tmp_path, "job-cross")
    reader = _base.JobStack(tmp_path, clock=stack.clock).repo
    before = len(reader.list_transitions("job-cross"))

    writer.advance_status("job-cross", **_FORWARD)

    assert reader.get_job("job-cross").status is StorageJobStatus.RAW_STAGED
    after = reader.list_transitions("job-cross")
    assert len(after) == before + 1, (before, len(after))
    assert after[-1].to_status is StorageJobStatus.RAW_STAGED


def test_unknown_job_read_still_raises_job_unknown(tmp_path: Path) -> None:
    """Gate regression: a missing job is still ``JobUnknown``, not corruption."""
    _stack, repo = _r1h._build_chain(tmp_path, "job-known")
    with pytest.raises(JobUnknown):
        repo.get_job("job-absent")
    with pytest.raises(JobUnknown):
        repo.list_transitions("job-absent")
    assert "job-absent" not in repo._lock_owners


# ---------------------------------------------------------------------------
# §17-§18 — reentrancy and the legitimate empty path
# ---------------------------------------------------------------------------


def test_successful_nested_entry_does_not_refresh_again(
    tmp_path: Path,
) -> None:
    """§17: nested skipping is allowed ONLY under a live outer context."""
    _stack, repo = _r1h._build_chain(tmp_path, "job-nested")
    counters = _instrument(repo, "job-nested")

    with repo._job_lock("job-nested"):
        with repo._job_lock("job-nested"):
            assert repo._lock_owners["job-nested"]["depth"] == 2

    assert counters.refresh == 1, counters.refresh
    assert counters.validate == 1, counters.validate
    assert "job-nested" not in repo._lock_owners


def test_one_write_entry_refreshes_once(tmp_path: Path) -> None:
    """§17: the write path reads state internally without re-refreshing."""
    _stack, repo = _r1h._build_chain(tmp_path, "job-once")
    counters = _instrument(repo, "job-once")

    repo.advance_status("job-once", **_FORWARD)

    assert counters.refresh == 1, counters.refresh
    assert counters.validate == 1, counters.validate
    assert "job-once" not in repo._lock_owners


def test_create_job_empty_path_regression(tmp_path: Path) -> None:
    """(O, §18) No birth + no events under create_job's lock is valid.

    The gated public read must not reject, recurse into itself, or refuse
    legitimate first creation.
    """
    stack = _base.JobStack(tmp_path)
    repo = stack.repo
    created = repo.create_job(
        job_id="job-fresh",
        provider_id="KRAKEN_FUTURES",
        sensor_family=_base.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint=_base._FP,
    )
    assert created.status is PLANNED
    # Idempotent re-create (internal unlocked read) then a PUBLIC gated read.
    assert repo.create_job(
        job_id="job-fresh",
        provider_id="KRAKEN_FUTURES",
        sensor_family=_base.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint=_base._FP,
    ).status is PLANNED
    assert repo.get_job("job-fresh").status is PLANNED
    assert repo.list_transitions("job-fresh") == []
    assert "job-fresh" not in repo._lock_owners
    # The legitimate new-job entry leaves no lock behind.
    assert not repo._lock_path("job-fresh").exists()


# ---------------------------------------------------------------------------
# §26 — the upstream I07R1H control is untouched
# ---------------------------------------------------------------------------


def test_intact_refreshed_control_still_accepted(tmp_path: Path) -> None:
    """(P) The I07R1H intact refreshed control remains adopted."""
    control = next(
        case for case in _r1h.CASES if case.expectation == "ACCEPT"
    )
    outcome = _r1h.run_chain_case(tmp_path / "control", control)
    assert outcome["runtime_path"] == NO_ERROR, outcome
    assert outcome["restart_path"] == NO_ERROR, outcome
    assert outcome["events_after"] == outcome["events_before"] + 1, outcome


def test_corruption_never_writes(tmp_path: Path) -> None:
    """Every rejected gate leaves the durable chain byte-count unchanged."""
    _stack, repo, job_id = _corrupt_scenario(tmp_path)
    before = len(list(_r1h._events_dir(tmp_path).glob("*.json")))
    for action in (
        lambda: repo.get_job(job_id),
        lambda: repo.list_transitions(job_id),
        lambda: repo.advance_status(job_id, **_CONTINUATION),
    ):
        with pytest.raises(JobCatalogCorrupt):
            action()
    assert len(list(_r1h._events_dir(tmp_path).glob("*.json"))) == before


# ---------------------------------------------------------------------------
# §22-§23 — the top-level operator ledger structure
# ---------------------------------------------------------------------------

LEDGER = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "SENSOR_FABRIC_IMPLEMENTATION_PROGRESS.md"
)

#: SENSOR-B4-I11R2 -- the ONE exact immutable authority for the I07R1I
#: *proposal* governance state.  ``## Current state`` is a mutable dashboard
#: and MUST advance; binding an immutable historical claim to it means the
#: claim breaks the moment the operator legitimately accepts or supersedes the
#: checkpoint.  I07R1I's own committed, measured, append-only ledger-structure
#: matrix records the proposal state permanently.
I07R1I_MATRIX = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
    / "BLOC_04_I07R1I_LEDGER_STRUCTURE_MATRIX.json"
)

#: The superseding verdict, bound to its own exact append-only section.  The
#: em dash is written as a code point so this heading stays byte-exact.
I07R1I_RATIFY_HEADING = (
    "## SENSOR-B4-I07R1I-RATIFY " + chr(0x2014) + " operator accepts the "
    "complete I07 chain, authorizes I08"
)


def _i07r1i_historical_case(case: str) -> dict[str, Any]:
    """One case of the committed I07R1I matrix, by exact name."""
    matrix = json.loads(I07R1I_MATRIX.read_text(encoding="utf-8"))
    assert matrix["checkpoint"] == "SENSOR-B4-I07R1I", matrix["checkpoint"]
    matches = [row for row in matrix["cases"] if row["case"] == case]
    assert len(matches) == 1, (case, matches)
    return matches[0]


def _current_state_rows() -> list[list[str]]:
    """Logical cells of every ordinary row in the top-level Current state table.

    Deliberately narrow (I07R1I §23): the FIRST ``## Current state`` heading
    and the ``| Field | Value |`` table directly under it, nothing else.  A
    general Markdown parser is not needed to prove one row has a duplicated
    trailing cell.
    """
    text = LEDGER.read_text(encoding="utf-8")
    lines = text.split("\n")
    start = next(
        index
        for index, line in enumerate(lines)
        if line.strip() == "## Current state"
    )
    rows: list[list[str]] = []
    for line in lines[start:]:
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = line.strip().strip("|").split("|")
        if [cell.strip() for cell in cells] == ["Field", "Value"]:
            continue  # the header itself
        if all(set(cell.strip()) <= {"-", " "} for cell in cells):
            continue  # the |---|---| separator
        rows.append([cell.strip() for cell in cells])
    return rows


def test_current_state_table_is_two_columns() -> None:
    """§22/§23: every ordinary Current state row is exactly Field | Value.

    Counterfactually red at 940c2509, where the Current checkpoint row
    carried an intended cell followed by a duplicated trailing segment.
    """
    rows = _current_state_rows()
    assert rows, "no ordinary rows found under ## Current state"
    malformed = [row for row in rows if len(row) != 2]
    assert not malformed, malformed


def test_current_checkpoint_row_appears_exactly_once() -> None:
    rows = _current_state_rows()
    checkpoint_rows = [row for row in rows if row[0] == "Current checkpoint"]
    assert len(checkpoint_rows) == 1, checkpoint_rows


def test_ledger_operator_state_is_truthful() -> None:
    """SENSOR-B4-I11R2: the recorded I07R1I proposal truth, from the exact
    immutable I07R1I evidence rather than the live ``## Current state``
    dashboard.

    This test used to require the LIVE top-level ``## Current state`` table
    to still read ``SENSOR-B4-I07R1I`` with all five upstream approvals
    ``OPERATOR_HOLD``.  That is a statement about the I07R1I *proposal*, and
    the operator subsequently accepted the complete chain in
    ``SENSOR-B4-I07R1I-RATIFY`` -- so the dashboard was SUPPOSED to advance,
    and the test broke with no regression in anything I07R1I ever did.  The
    proposal truth is immutable and remains fully provable; it now comes from
    the committed measured I07R1I ledger-structure matrix.  The superseding
    ratification is pinned by :func:`test_i07r1i_ratification_is_recorded`.
    """
    hold = _i07r1i_historical_case("i07_hold_chain_truthful")
    assert hold["result"] == "PASS"
    assert hold["proposal_pending"] is True
    assert tuple(hold["hold_keys"]) == _HOLD_KEYS

    resume = _i07r1i_historical_case("durable_resume_pending_acceptance")
    assert resume["result"] == "PASS"
    assert resume["durable_resume_implemented"] == "PENDING_OPERATOR_ACCEPTANCE"
    assert resume["recovery_scanner_implemented"] is False

    following = _i07r1i_historical_case("next_checkpoint_not_authorized")
    assert following["result"] == "PASS"
    assert following["next_checkpoint_authorized"] is False


def test_i07r1i_ratification_is_recorded() -> None:
    """SENSOR-B4-I11R2: the superseding operator verdict is still pinned.

    Decoupling the stale proposal test must NOT delete the accountability
    that replaced it: the ledger's exact I07R1I-RATIFY section must still show
    the chain accepted, durable resume TRUE, and I08 -- and only I08 --
    authorized.
    """
    section = extract_checkpoint_section(
        LEDGER.read_text(encoding="utf-8"), I07R1I_RATIFY_HEADING
    )
    assert "OPERATOR_ACCEPTED" in section
    for key in _HOLD_KEYS:
        assert key in section, key
    assert "DURABLE_RESUME_IMPLEMENTED = TRUE" in section
    assert "RECOVERY_SCANNER_IMPLEMENTED = FALSE" in section
    assert "next_checkpoint_authorized = TRUE" in section
    assert "SENSOR-B4-I08 RECOVERY / QUARANTINE ONLY" in section
    assert "I09+ NOT" in section
    # A ratification is governance-only: it changed no source, test or evidence.
    assert "no test delta" in section


def test_current_state_is_a_dashboard_not_a_historical_checkpoint() -> None:
    """SENSOR-B4-I11R2: the dashboard states only the PRESENT checkpoint.

    The live table is a two-column Field|Value dashboard for the checkpoint
    actually implemented.  It must never be re-pinned to a superseded
    checkpoint's proposal state, and it must never re-assert a hold the
    operator has since accepted.
    """
    rows = _current_state_rows()
    table = "\n".join("|".join(row) for row in rows).replace(" = ", "=")
    checkpoint_rows = [row for row in rows if row[0] == "Current checkpoint"]
    assert len(checkpoint_rows) == 1
    current = checkpoint_rows[0][1]

    # Present-checkpoint truth only.
    assert "SENSOR-B4-I11" in current
    assert "research frozen" in current
    assert "I12" in current
    assert "next_checkpoint_authorized=FALSE" in table
    # Never a superseded checkpoint's proposal state.
    assert "SENSOR-B4-I07R1I" not in current
    assert "DURABLE_RESUME_IMPLEMENTED=PENDING_OPERATOR_ACCEPTANCE" not in table


def test_ledger_is_utf8_lf() -> None:
    """The governance document stays normal LF UTF-8."""
    raw = LEDGER.read_bytes()
    raw.decode("utf-8")
    assert b"\r\n" not in raw
