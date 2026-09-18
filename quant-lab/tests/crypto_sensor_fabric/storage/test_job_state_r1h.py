"""SENSOR-B4-I07R1H — runtime refreshed-chain + restart validation parity.

The remaining seam (I07R1H §0/§3): the outermost per-job lock calls
``_births.refresh()`` + ``_events.refresh()`` and then materializes the
newest ``resulting_state`` directly — but ``DurableJsonCatalog.refresh()``
proves only fragment parse + physical-key binding, NOT that the adopted
event satisfies the job-state contract (transition graph, contiguity,
linkage, binding, pointer immutability).  A long-lived repository could
therefore CONSUME as runtime state an event a fresh restart would reject.

Every case here attacks BOTH paths with the SAME durable chain, using the
proven I07R1G attack shape (repository constructed BEFORE the fabrication →
outer-lock refresh adopts the forged later head at its correct hashed
physical key → runtime operation executes):

- the forged event's ``checkpoint_proof`` (where present) stays FULLY VALID
  — only EVENT/CHAIN semantics are corrupted.  Proof corruption is already
  I07R1G; valid proof must not excuse an invalid event (core doctrine);
- the long-lived repository's next operation on the job must raise
  :class:`JobCatalogCorrupt` BEFORE the forged head influences state;
- a fresh restart over the identical chain must fail identically;
- corruption never writes: the event count is unchanged after every attack;
- the INTACT control (a fully chain-valid forged event, valid proof) is
  adopted at runtime and accepted at restart — and the +1 event after its
  successful probe proves the forged head really was adopted into the chain
  (otherwise the probe's own event would have collided on sequence).

Read-only against the committed evidence tree; real durable stack only.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

# Make the sibling loader importable regardless of pytest invocation
# directory (importlib mode + competing repo-root ``tests`` package).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest
from crypto_sensor_fabric.storage.enums import StorageJobStatus
from crypto_sensor_fabric.storage.jobs import JobCatalogCorrupt

from _sibling_import import load_sibling

_base = load_sibling("_i07r1_base_mod", "test_job_state_r1")

_create = _base._create

#: The typed corruption classification BOTH paths must produce.
CORRUPTION = JobCatalogCorrupt.__name__
NO_ERROR = "NO_ERROR"

_ACQUIRING = StorageJobStatus.ACQUIRING
_CHECKPOINT = StorageJobStatus.CHECKPOINT_ADVANCED
_ORDINARY = StorageJobStatus.RAW_STAGED

#: One legitimate ordinary probe after a refreshed checkpoint head: the
#: annotated continuation edge (CHECKPOINT_ADVANCED -> ACQUIRING).
_CONTINUATION = {"to_status": _ACQUIRING, "reason": "batch continuation"}


# ---------------------------------------------------------------------------
# Chain-shape attacks (I07R1H §17-§25)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChainCase:
    """One event/chain attack applied to a valid forged later head.

    ``mutate(forged)`` edits the forged payload; the checkpoint proof
    (when present) is NEVER touched — I07R1H attacks chain semantics only,
    so every rejection is attributable to the event, not to the
    (already-sealed) proof.  ``expectation`` marks the intact control.
    """

    name: str
    mutate: Callable[[dict[str, Any]], None]
    expectation: str = "REJECT"


def _from_status_chain_break(forged: dict[str, Any]) -> None:
    # §17: prior real head ACQUIRING; the forged checkpoint claims
    # RAW_STAGED.  The proof stays valid for the anchors; the chain does
    # not — from_status linkage must break before the state is consumed.
    forged["transition"]["from_status"] = StorageJobStatus.RAW_STAGED.value


def _transition_job_id_mismatch(forged: dict[str, Any]) -> None:
    # §18: top-level event job_id stays the real job; transition.job_id
    # claims another REAL job — transition/job binding broken.
    forged["transition"]["job_id"] = forged["job_id"] + "-other"


def _result_status_mismatch(forged: dict[str, Any]) -> None:
    # §19: resulting.status diverges from transition.to_status while the
    # proof anchors stay valid/consistent.
    forged["resulting_state"]["status"] = _ACQUIRING.value


def _provider_identity_mismatch(forged: dict[str, Any]) -> None:
    # §20: birth identity is immutable; provider mutated under a valid proof.
    forged["resulting_state"]["provider_id"] = "BINANCE_SPOT"


def _sensor_identity_mismatch(forged: dict[str, Any]) -> None:
    forged["resulting_state"]["sensor_family"] = "MECHANICAL_TRADE"


def _request_identity_mismatch(forged: dict[str, Any]) -> None:
    forged["resulting_state"]["request_fingerprint"] = "fp-forged"


def _updated_at_mismatch(forged: dict[str, Any]) -> None:
    # §21: resulting.updated_at must equal transition.transitioned_at.
    forged["resulting_state"]["updated_at"] = "2030-01-01T00:00:00+00:00"


def _backward_chronology(forged: dict[str, Any]) -> None:
    # §21: the transition instant predates the previous head's update
    # (time binding kept consistent so chronology is the violated rule).
    forged["transition"]["transitioned_at"] = "2020-01-01T00:00:00+00:00"
    forged["resulting_state"]["updated_at"] = "2020-01-01T00:00:00+00:00"


def _sequence_gap(forged: dict[str, Any]) -> None:
    # §22: physical key recomputed for the forged logical id so catalog
    # integrity passes and JOB validation must catch the contiguity break.
    sequence = forged["sequence"] + 7
    forged["sequence"] = sequence
    forged["transition_id"] = f"{forged['job_id']}:{sequence:06d}"
    forged["transition"]["transition_id"] = forged["transition_id"]


def _event_identity_mismatch(forged: dict[str, Any]) -> None:
    # §23: logical id / sequence relationship violates
    # _event_id(job_id, sequence); the physical key stays valid for the
    # (consistent) logical id so the corruption reaches JOB validation.
    forged["sequence"] = forged["sequence"] + 3
    forged["transition_id"] = f"{forged['job_id']}:000042"
    forged["transition"]["transition_id"] = forged["transition_id"]


def _to_ordinary(forged: dict[str, Any]) -> None:
    """Reshape the forged checkpoint head into an ORDINARY event from
    ACQUIRING (a legal graph edge) while keeping the copied state."""
    sequence = forged["sequence"]
    transition_id = f"{forged['job_id']}:{sequence:06d}"
    forged.pop("checkpoint_proof", None)
    forged["transition"]["from_status"] = _ACQUIRING.value
    forged["transition"]["to_status"] = _ORDINARY.value
    forged["transition"]["transition_id"] = transition_id
    forged["resulting_state"]["status"] = _ORDINARY.value


def _proof_on_ordinary_event(forged: dict[str, Any]) -> None:
    # §25: a chain-valid ORDINARY event carrying a fully valid-looking
    # checkpoint_proof — proof metadata belongs only to checkpoint events.
    _to_ordinary(forged)
    state = forged["resulting_state"]
    forged["checkpoint_proof"] = {
        "proof_version": 1,
        "minimum_durable_status": "MANIFEST_COMMITTED",
        "acquisition_id": state["last_committed_acquisition_id"],
        "blob_sha256": state["last_committed_blob_sha256"],
        "manifest_id": state["last_manifest_id"],
    }


def _ordinary_resume_pointer_mutation(forged: dict[str, Any]) -> None:
    # §24: ordinary events preserve the cursor exactly.
    _to_ordinary(forged)
    forged["resulting_state"]["resume_token"] = {
        "mode": "PAGE",
        "provider_cursor": "forged",
        "page_number": 99,
    }


def _ordinary_anchor_mutation(forged: dict[str, Any]) -> None:
    # §24: ordinary events preserve the committed anchors exactly.
    _to_ordinary(forged)
    forged["resulting_state"]["last_committed_acquisition_id"] = "acq-forged"


def _no_mutation(forged: dict[str, Any]) -> None:
    return None


#: Matrix cases (I07R1H §29).  Order = the committed matrix order.
CASES: tuple[ChainCase, ...] = (
    ChainCase("from-status-chain-break", _from_status_chain_break),
    ChainCase("transition-job-id-mismatch", _transition_job_id_mismatch),
    ChainCase("result-status-mismatch", _result_status_mismatch),
    ChainCase("provider-identity-mismatch", _provider_identity_mismatch),
    ChainCase("sensor-identity-mismatch", _sensor_identity_mismatch),
    ChainCase("request-identity-mismatch", _request_identity_mismatch),
    ChainCase("updated-at-transition-mismatch", _updated_at_mismatch),
    ChainCase("backward-chronology", _backward_chronology),
    ChainCase("sequence-gap", _sequence_gap),
    ChainCase("event-identity-mismatch", _event_identity_mismatch),
    ChainCase("ordinary-resume-pointer-mutation", _ordinary_resume_pointer_mutation),
    ChainCase("ordinary-anchor-mutation", _ordinary_anchor_mutation),
    ChainCase("proof-on-ordinary-event", _proof_on_ordinary_event),
    ChainCase("intact-refreshed-control", _no_mutation, "ACCEPT"),
)


# ---------------------------------------------------------------------------
# Runtime/restart parity harness
# ---------------------------------------------------------------------------


def _events_dir(root: Path) -> Path:
    return root / "catalogs" / "jobs_state" / "events"


def _job_events(root: Path, job_id: str) -> list[dict[str, Any]]:
    events = []
    for path in sorted(_events_dir(root).glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("job_id") == job_id:
            events.append(payload)
    events.sort(key=lambda event: event["sequence"])
    return events


def _bump_iso(value: str, seconds: int) -> str:
    bumped = datetime.fromisoformat(value) + timedelta(seconds=seconds)
    text = bumped.isoformat()
    return text.replace("+00:00", "Z") if value.endswith("Z") else text


def _publish_forged_head(root: Path, case: ChainCase, job_id: str) -> dict[str, Any]:
    """Build the legitimate chain, then publish ``case``'s forged later
    head at its correct hashed physical key (I07R1H §16 attack shape)."""
    events = _job_events(root, job_id)
    genuine = next(
        event for event in events if event.get("checkpoint_proof") is not None
    )
    sequence = max(event["sequence"] for event in events) + 1
    instant = _bump_iso(
        max(event["resulting_state"]["updated_at"] for event in events), 1
    )
    forged = json.loads(json.dumps(genuine))
    forged["sequence"] = sequence
    forged["transition_id"] = f"{job_id}:{sequence:06d}"
    forged["transition"]["transition_id"] = forged["transition_id"]
    forged["transition"]["from_status"] = _ACQUIRING.value
    forged["transition"]["to_status"] = _CHECKPOINT.value
    forged["transition"]["transitioned_at"] = instant
    forged["transition"]["reason"] = "forged checkpoint head (chain attack)"
    forged["resulting_state"]["updated_at"] = instant
    forged["resulting_state"]["status"] = _CHECKPOINT.value
    case.mutate(forged)
    key = hashlib.sha256(forged["transition_id"].encode("utf-8")).hexdigest()
    (_events_dir(root) / f"{key}.json").write_bytes(
        json.dumps(forged).encode("utf-8")
    )
    return forged


def _build_chain(root: Path, job_id: str) -> tuple[Any, Any]:
    """Repository-first legitimate chain: birth → manifest-committed batch
    → checkpoint → annotated continuation.  A second real job exists so
    §18's transition.job_id attack can name one."""
    stack = _base.JobStack(root, clock=_base.TickingClock())
    repo = stack.repo
    _create(repo, job_id)
    _create(repo, job_id + "-other")
    _base._drive_to_manifest(repo, job_id)
    _base._full_batch(
        stack,
        f"acq-{job_id}",
        f"pm-{job_id}",
        f'{{"rows": ["{job_id}"]}}'.encode("utf-8"),
    )
    _base._checkpoint(repo, job_id, f"acq-{job_id}", f"pm-{job_id}")
    repo.advance_status(job_id, **_CONTINUATION)  # noqa: SLF001 — test shape
    return stack, repo


def run_chain_case(root: Path, case: ChainCase) -> dict[str, Any]:
    """Attack runtime THEN restart with the same chain-corrupt head.

    The runtime attempt uses the repository constructed BEFORE the
    fabrication: its next operation on the job acquires the file lock,
    refreshes both catalogs (adopting the forged head), then runs the
    shared chain authority — which must fail closed BEFORE any runtime
    decision reads the corrupt state.  The restart attempt constructs a
    fresh repository over the identical durable chain.
    """
    job_id = f"job-{case.name}"
    stack, repo = _build_chain(root, job_id)
    _publish_forged_head(root, case, job_id)

    events_before = len(list(_events_dir(root).glob("*.json")))
    runtime_error = NO_ERROR
    try:
        repo.advance_status(job_id, **_CONTINUATION)
    except BaseException as exc:  # noqa: BLE001 — classified below
        runtime_error = type(exc).__name__
    events_after = len(list(_events_dir(root).glob("*.json")))

    restart_error = NO_ERROR
    try:
        _base.JobStack(root, clock=stack.clock)
    except BaseException as exc:  # noqa: BLE001 — classified below
        restart_error = type(exc).__name__

    if case.expectation == "REJECT":
        # Corruption never writes: the event count is untouched.
        satisfied = (
            runtime_error == CORRUPTION
            and restart_error == CORRUPTION
            and events_after == events_before
        )
    else:
        # The control PROVES adoption: the probe succeeded AND appended
        # its own event after the forged head (a collision on the forged
        # sequence would have raised instead).
        satisfied = (
            runtime_error == NO_ERROR
            and restart_error == NO_ERROR
            and events_after == events_before + 1
        )
    return {
        "case": case.name,
        "expectation": case.expectation,
        "runtime_path": runtime_error,
        "restart_path": restart_error,
        "typed_error": (
            runtime_error if runtime_error != NO_ERROR else restart_error
        ),
        "events_before": events_before,
        "events_after": events_after,
        "result": "PASS" if satisfied else "FAIL",
    }


# ---------------------------------------------------------------------------
# §29: every corruption case fails closed on BOTH paths
# ---------------------------------------------------------------------------


REJECT_CASES = tuple(case for case in CASES if case.expectation == "REJECT")


@pytest.mark.parametrize("case", REJECT_CASES, ids=lambda case: case.name)
def test_chain_corrupt_head_rejected_by_runtime_and_restart(
    tmp_path: Path, case: ChainCase
) -> None:
    outcome = run_chain_case(tmp_path / case.name, case)
    assert outcome["runtime_path"] == CORRUPTION, outcome
    assert outcome["restart_path"] == CORRUPTION, outcome
    assert outcome["events_after"] == outcome["events_before"], outcome
    assert outcome["result"] == "PASS", outcome


def test_intact_refreshed_head_is_adopted_control(tmp_path: Path) -> None:
    """Non-vacuity control (I07R1H §26).

    The SAME publication mechanics with a FULLY chain-valid event (valid
    proof, canonical identity, correct linkage) must be adopted at runtime
    through the refresh path and accepted at restart — proving the
    rejections above are specific to chain validity, never to a record
    having arrived through refresh.  The +1 event proves the forged head
    was really inside the chain when the probe ran.
    """
    outcome = run_chain_case(
        tmp_path / "control",
        next(case for case in CASES if case.expectation == "ACCEPT"),
    )
    assert outcome["runtime_path"] == NO_ERROR, outcome
    assert outcome["restart_path"] == NO_ERROR, outcome
    assert outcome["events_after"] == outcome["events_before"] + 1, outcome
    assert outcome["result"] == "PASS", outcome


def test_runtime_validation_is_job_local(tmp_path: Path) -> None:
    """§5: the outer lock validates the LOCKED job's chain, not the world.

    Job A's chain carries a corrupt forged head; operating on a DIFFERENT
    healthy job B must not be blocked by A's corruption — A's own next
    operation is what fails closed.  (§28: no global all-job rescan under
    every lock.)
    """
    stack, repo = _build_chain(tmp_path, "job-corrupt-a")
    _publish_forged_head(
        tmp_path,
        ChainCase("job-local", _from_status_chain_break),
        "job-corrupt-a",
    )
    # Job B operates cleanly despite A's corrupt refreshed tail.
    state = repo.advance_status("job-corrupt-a-other", to_status=_ACQUIRING)
    assert state.status is _ACQUIRING
    # Job A's own next operation fails closed on the corrupt chain.
    with pytest.raises(JobCatalogCorrupt):
        repo.advance_status("job-corrupt-a", **_CONTINUATION)
