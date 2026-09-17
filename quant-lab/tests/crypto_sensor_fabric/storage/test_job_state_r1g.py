"""SENSOR-B4-I07R1G — runtime checkpoint-proof schema + replay-parity proof.

The remaining operator seam (I07R1G §0/§3): the exact-retry path validated
that a committed checkpoint's proof EXISTED, but not that it was VALID.
Restart validated the full contract, so runtime and restart could disagree —
a long-lived repository whose post-lock refresh adopts a forged head would
ADOPT it where a fresh restart would refuse it.

Every case here therefore attacks BOTH paths with the SAME durable chain:

- the repository is constructed BEFORE the fabrication, so the outermost
  per-job lock's validated refresh ADOPTS the forged later head at its
  correct hashed physical key (no divergence for refresh to detect) — the
  runtime exact-retry path is what must refuse it;
- a fresh restart over the same durable chain must refuse it identically.

The forged event is a CHAIN-VALID later checkpoint head (``ACQUIRING ->
CHECKPOINT_ADVANCED``, canonical event id ``{job_id}:{sequence:06d}``,
``resulting_state.updated_at == transition.transitioned_at``) so the only
thing separating it from an adoptable checkpoint is the proof itself — the
intact-proof control in this module proves exactly that (§10/§11), which
makes every rejection below specific to proof validity rather than to the
forgery's shape.

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
from crypto_sensor_fabric.providers.base.models import ResumeToken
from crypto_sensor_fabric.storage.enums import StorageJobStatus
from crypto_sensor_fabric.storage.jobs import JobCatalogCorrupt

from _sibling_import import load_sibling

_base = load_sibling("_i07r1_base_mod", "test_job_state_r1")

JobStack = _base.JobStack
_create = _base._create
_drive_to_manifest = _base._drive_to_manifest
_full_batch = _base._full_batch
_checkpoint = _base._checkpoint

TOKEN = ResumeToken(mode="PAGE", provider_cursor="c", page_number=1)

#: The typed corruption classification BOTH paths must produce, taken from
#: the real exception class so a rename cannot silently weaken these proofs.
CORRUPTION = JobCatalogCorrupt.__name__
NO_ERROR = "NO_ERROR"

MANIFEST = StorageJobStatus.MANIFEST_COMMITTED
RAW = StorageJobStatus.RAW_COMMITTED

_SECOND_ACQ = "acq-second"


# ---------------------------------------------------------------------------
# Forged-head scenarios (I07R1G §3, §10, §11, §12)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ForgedCase:
    """One proof-attack variant applied to a chain-valid later head.

    ``floor`` selects the durability floor the genuine checkpoint (and so
    the forged proof) is authorized under; ``second_acquisition_fingerprint``
    seeds a second durable acquisition over the SAME blob bytes but a
    different request identity (§12); ``mutate`` edits the forged event.
    """

    name: str
    floor: Any = MANIFEST
    second_acquisition_fingerprint: str | None = None
    mutate: Callable[[dict[str, Any], dict[str, Any]], None] | None = None
    #: REJECT = forged proof must fail closed; ACCEPT = the control case.
    expectation: str = "REJECT"


def _no_mutation(forged: dict[str, Any], resulting: dict[str, Any]) -> None:
    return None


def _drop_proof(forged: dict[str, Any], resulting: dict[str, Any]) -> None:
    del forged["checkpoint_proof"]


def _version_two(forged: dict[str, Any], resulting: dict[str, Any]) -> None:
    forged["checkpoint_proof"]["proof_version"] = 2


def _version_missing(forged: dict[str, Any], resulting: dict[str, Any]) -> None:
    del forged["checkpoint_proof"]["proof_version"]


def _floor_missing(forged: dict[str, Any], resulting: dict[str, Any]) -> None:
    del forged["checkpoint_proof"]["minimum_durable_status"]


def _floor_unknown(forged: dict[str, Any], resulting: dict[str, Any]) -> None:
    forged["checkpoint_proof"]["minimum_durable_status"] = "NOT_A_FLOOR"


def _acquisition_mismatch(
    forged: dict[str, Any], resulting: dict[str, Any]
) -> None:
    forged["checkpoint_proof"]["acquisition_id"] = "acq-someone-else"


def _blob_mismatch(forged: dict[str, Any], resulting: dict[str, Any]) -> None:
    forged["checkpoint_proof"]["blob_sha256"] = "c" * 64


def _manifest_mismatch(
    forged: dict[str, Any], resulting: dict[str, Any]
) -> None:
    forged["checkpoint_proof"]["manifest_id"] = "pm-unrelated"


def _raw_manifest_contradiction(
    forged: dict[str, Any], resulting: dict[str, Any]
) -> None:
    # Internally consistent (proof and anchors agree) but structurally
    # impossible: the RAW floor has no manifest anchor (I07R1 §12).
    forged["checkpoint_proof"]["manifest_id"] = "pm-tampered-in"
    resulting["last_manifest_id"] = "pm-tampered-in"


def _manifest_anchor_missing(
    forged: dict[str, Any], resulting: dict[str, Any]
) -> None:
    forged["checkpoint_proof"]["manifest_id"] = None
    resulting["last_manifest_id"] = None


def _proof_wrong_type(forged: dict[str, Any], resulting: dict[str, Any]) -> None:
    forged["checkpoint_proof"] = []


def _proof_empty_mapping(
    forged: dict[str, Any], resulting: dict[str, Any]
) -> None:
    forged["checkpoint_proof"] = {}


def _proof_string(forged: dict[str, Any], resulting: dict[str, Any]) -> None:
    forged["checkpoint_proof"] = "proof"


def _proof_integer(forged: dict[str, Any], resulting: dict[str, Any]) -> None:
    forged["checkpoint_proof"] = 1


def _proof_bool(forged: dict[str, Any], resulting: dict[str, Any]) -> None:
    forged["checkpoint_proof"] = True


def _extra_field(forged: dict[str, Any], resulting: dict[str, Any]) -> None:
    forged["checkpoint_proof"]["proof_extension"] = "v2-hint"


def _same_blob_wrong_acquisition(
    forged: dict[str, Any], resulting: dict[str, Any]
) -> None:
    # Anchors stay internally CONSISTENT (proof and state both point at the
    # second acquisition, whose blob bytes are identical) — only the durable
    # request identity of that acquisition differs from the job's birth.
    forged["checkpoint_proof"]["acquisition_id"] = _SECOND_ACQ
    resulting["last_committed_acquisition_id"] = _SECOND_ACQ


CASES: tuple[ForgedCase, ...] = (
    ForgedCase("proof-missing", mutate=_drop_proof),
    ForgedCase("version-unknown", mutate=_version_two),
    ForgedCase("version-missing", mutate=_version_missing),
    ForgedCase("floor-missing", mutate=_floor_missing),
    ForgedCase("floor-unknown", mutate=_floor_unknown),
    ForgedCase("acquisition-mismatch", mutate=_acquisition_mismatch),
    ForgedCase("blob-mismatch", mutate=_blob_mismatch),
    ForgedCase("manifest-mismatch", mutate=_manifest_mismatch),
    ForgedCase("raw-manifest-contradiction", floor=RAW, mutate=_raw_manifest_contradiction),
    ForgedCase("manifest-anchor-missing", mutate=_manifest_anchor_missing),
    ForgedCase("proof-wrong-type", mutate=_proof_wrong_type),
    ForgedCase("proof-empty-mapping", mutate=_proof_empty_mapping),
    ForgedCase("proof-string", mutate=_proof_string),
    ForgedCase("proof-integer", mutate=_proof_integer),
    ForgedCase("proof-bool", mutate=_proof_bool),
    ForgedCase("proof-extra-field", mutate=_extra_field),
    ForgedCase(
        "same-blob-wrong-acquisition",
        second_acquisition_fingerprint="fp-r1g-second-request",
        mutate=_same_blob_wrong_acquisition,
    ),
    ForgedCase("intact-control", mutate=_no_mutation, expectation="ACCEPT"),
)


def _events_dir(root: Path) -> Path:
    return root / "catalogs" / "jobs_state" / "events"


def _job_events(root: Path, job_id: str) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for path in sorted(_events_dir(root).glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("job_id") == job_id:
            payloads.append(payload)
    payloads.sort(key=lambda event: event["sequence"])
    return payloads


def _bump_iso(value: str, seconds: int) -> str:
    """Add ``seconds`` to an ISO-8601 instant, preserving its Z/offset form."""
    bumped = datetime.fromisoformat(value) + timedelta(seconds=seconds)
    text = bumped.isoformat()
    return text.replace("+00:00", "Z") if value.endswith("Z") else text


def _forged_head_path(root: Path, transition_id: str) -> Path:
    key = hashlib.sha256(transition_id.encode("utf-8")).hexdigest()
    return _events_dir(root) / f"{key}.json"


def forge_later_checkpoint_head(
    root: Path, case: ForgedCase
) -> dict[str, Any]:
    """Build a chain-valid later checkpoint head carrying ``case``'s proof.

    Returns the live stack (long-lived repository), the exact batch kwargs,
    the forged payload and the seeded blob SHA.
    """
    job_id = f"job-{case.name}"
    stack = JobStack(
        root, clock=_base.TickingClock(), min_durable_status=case.floor
    )
    repo = stack.repo
    _create(repo, job_id)
    _drive_to_manifest(repo, job_id)
    sha = _full_batch(
        stack,
        f"acq-{case.name}",
        f"pm-{case.name}",
        f'{{"rows": ["{case.name}"]}}'.encode("utf-8"),
    )
    if case.second_acquisition_fingerprint is not None:
        # SAME physical bytes, a DIFFERENT durable request identity (§12).
        stack.seed_acquisition(
            sha,
            _SECOND_ACQ,
            request_fingerprint=case.second_acquisition_fingerprint,
        )
    manifest_id = None if case.floor is RAW else f"pm-{case.name}"
    _checkpoint(repo, job_id, f"acq-{case.name}", manifest_id)
    # Continue the chain so the forged head can be a chain-VALID checkpoint
    # edge (ACQUIRING -> CHECKPOINT_ADVANCED) rather than a chain break.
    repo.advance_status(
        job_id,
        to_status=StorageJobStatus.ACQUIRING,
        reason="batch continuation after checkpoint",
    )

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
    forged["transition"]["from_status"] = StorageJobStatus.ACQUIRING.value
    forged["transition"]["to_status"] = (
        StorageJobStatus.CHECKPOINT_ADVANCED.value
    )
    forged["transition"]["transitioned_at"] = instant
    forged["transition"]["reason"] = "forged checkpoint head (proof attack)"
    forged["resulting_state"]["updated_at"] = instant
    forged["resulting_state"]["status"] = StorageJobStatus.CHECKPOINT_ADVANCED.value
    mutate = case.mutate or _no_mutation
    mutate(forged, forged["resulting_state"])
    _forged_head_path(root, forged["transition_id"]).write_bytes(
        json.dumps(forged).encode("utf-8")
    )
    batch: dict[str, Any] = {
        "resume_token": TOKEN,
        "acquisition_id": f"acq-{case.name}",
    }
    if manifest_id is not None:
        batch["manifest_id"] = manifest_id
    return {
        "stack": stack,
        "repo": repo,
        "job_id": job_id,
        "batch": batch,
        "forged": forged,
        "genuine": genuine,
        "blob_sha256": sha,
    }


def run_forged_case(root: Path, case: ForgedCase) -> dict[str, Any]:
    """Attack runtime THEN restart with the same forged chain (I07R1G §10).

    The runtime attempt uses the repository constructed BEFORE the
    fabrication (adopted by post-lock refresh); the restart attempt
    constructs a fresh repository over the identical durable chain.  Both
    must produce the same typed corruption, and corruption must never
    mutate the chain.
    """
    scenario = forge_later_checkpoint_head(root, case)
    repo = scenario["repo"]
    events_before = len(list(_events_dir(root).glob("*.json")))

    runtime_error = NO_ERROR
    runtime_state = None
    try:
        runtime_state = repo.advance_checkpoint(
            scenario["job_id"], **scenario["batch"]
        )
    except BaseException as exc:  # noqa: BLE001 — classified below
        runtime_error = type(exc).__name__

    chain_unchanged = len(list(_events_dir(root).glob("*.json"))) == events_before

    restart_error = NO_ERROR
    try:
        JobStack(root, clock=scenario["stack"].clock)
    except BaseException as exc:  # noqa: BLE001 — classified below
        restart_error = type(exc).__name__

    rejected = CORRUPTION
    typed = runtime_error if runtime_error != NO_ERROR else restart_error
    if case.expectation == "REJECT":
        satisfied = runtime_error == rejected and restart_error == rejected
    else:  # ACCEPT: the control's intact proof must be adoptable
        satisfied = runtime_error == NO_ERROR and restart_error == NO_ERROR
    return {
        "case": case.name,
        "expectation": case.expectation,
        "runtime_path": runtime_error,
        "restart_path": restart_error,
        "runtime_rejected": runtime_error == rejected,
        "restart_rejected": restart_error == rejected,
        "typed_error": typed,
        "chain_unchanged": chain_unchanged,
        "runtime_adopted_status": (
            runtime_state.status.value if runtime_state is not None else None
        ),
        "runtime_adopted_acquisition": (
            runtime_state.last_committed_acquisition_id
            if runtime_state is not None
            else None
        ),
        "result": "PASS" if satisfied and chain_unchanged else "FAIL",
    }


# ---------------------------------------------------------------------------
# §10/§11: forged proofs — runtime and restart must agree
# ---------------------------------------------------------------------------


REJECT_CASES = tuple(case for case in CASES if case.expectation == "REJECT")


@pytest.mark.parametrize("case", REJECT_CASES, ids=lambda case: case.name)
def test_forged_proof_rejected_by_runtime_and_restart(
    tmp_path: Path, case: ForgedCase
) -> None:
    """Every forged proof fails closed on BOTH paths with the same type."""
    outcome = run_forged_case(tmp_path / case.name, case)
    assert outcome["runtime_path"] == CORRUPTION, outcome
    assert outcome["restart_path"] == CORRUPTION, outcome
    assert outcome["chain_unchanged"], outcome  # corruption never writes
    assert outcome["result"] == "PASS", outcome


def test_intact_proof_forged_head_is_adopted_control(tmp_path: Path) -> None:
    """Non-vacuity control (I07R1G §10/§11).

    The SAME forgery mechanics with an INTACT proof must be accepted by both
    paths — proving the rejections above are specific to proof validity and
    not to the forged event's shape (chain position, event id, anchors or
    chronology).
    """
    outcome = run_forged_case(
        tmp_path / "control",
        next(case for case in CASES if case.expectation == "ACCEPT"),
    )
    assert outcome["runtime_path"] == NO_ERROR, outcome
    assert outcome["restart_path"] == NO_ERROR, outcome
    # The forged head really IS the adopted head: same status, same anchors.
    assert outcome["runtime_adopted_status"] == "CHECKPOINT_ADVANCED", outcome
    assert outcome["runtime_adopted_acquisition"] == "acq-intact-control", outcome
    assert outcome["chain_unchanged"], outcome  # exact retry writes nothing
    assert outcome["result"] == "PASS", outcome


def test_same_bytes_wrong_acquisition_proof_rejected(tmp_path: Path) -> None:
    """§12: identical bytes must not make proof identity interchangeable.

    The attack premise is asserted first: the second acquisition really does
    carry the same physical blob SHA, and the forged proof/state anchors
    agree with each other — only the DURABLE request identity differs from
    the job's birth, which the re-proof must reject.
    """
    case = next(c for c in CASES if c.name == "same-blob-wrong-acquisition")
    scenario = forge_later_checkpoint_head(tmp_path / case.name, case)
    stack = scenario["stack"]
    forged = scenario["forged"]
    original = stack.acq_repo.get_acquisition(f"acq-{case.name}")
    second = stack.acq_repo.get_acquisition(_SECOND_ACQ)
    assert second.blob_sha256 == original.blob_sha256  # same bytes ...
    assert second.request_fingerprint != original.request_fingerprint
    assert (
        forged["checkpoint_proof"]["acquisition_id"]
        == forged["resulting_state"]["last_committed_acquisition_id"]
    )  # ... internally consistent anchors
    outcome = run_forged_case(tmp_path / "same-blob", case)
    assert outcome["runtime_path"] == CORRUPTION, outcome
    assert outcome["restart_path"] == CORRUPTION, outcome
