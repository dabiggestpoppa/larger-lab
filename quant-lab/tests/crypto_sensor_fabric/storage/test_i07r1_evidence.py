"""SENSOR-B4-I07R1E — deterministic machine-evidence matrices for the
resume-truth hardening seal.

Builders are PURE: they run real scenarios in tmp dirs and return dicts
serialized through ``stable_evidence_bytes``.  Normal pytest runs NEVER
write the committed evidence tree — tests generate to memory/tmp_path and
compare against committed bytes (I05R4 read-only evidence policy, I07R1
§42).  Publication happens once per checkpoint via an explicit operator
invocation (module bottom).

Matrices (I07R1 §40):
- BLOC_04_I07R1_PUBLIC_API_MATRIX.json
- BLOC_04_I07R1_CHECKPOINT_IDENTITY_MATRIX.json
- BLOC_04_I07R1_RESTART_REPLAY_MATRIX.json
- BLOC_04_I07R1_COORDINATION_MATRIX.json
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

EVIDENCE_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)


def stable_evidence_bytes(payload: dict) -> bytes:
    """Canonical deterministic serializer (I05R4 §31 doctrine)."""
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _case(name: str, **fields) -> dict:
    return {"case": name, **fields}


def _load_stack_modules():
    from _sibling_import import load_sibling

    base = load_sibling("_i07r1_base_mod", "test_job_state_r1")
    return base


def _drive_to_manifest(repo, job_id: str) -> None:
    """Resume-aware drive to MANIFEST_COMMITTED (shared with builders)."""
    from crypto_sensor_fabric.storage.enums import StorageJobStatus

    current = repo.get_job(job_id).status
    if current is StorageJobStatus.CHECKPOINT_ADVANCED:
        repo.advance_status(
            job_id,
            to_status=StorageJobStatus.ACQUIRING,
            reason="batch continuation after checkpoint",
        )
        current = StorageJobStatus.ACQUIRING
    order = [
        StorageJobStatus.ACQUIRING,
        StorageJobStatus.RAW_STAGED,
        StorageJobStatus.RAW_COMMITTED,
        StorageJobStatus.PROJECTION_PENDING,
        StorageJobStatus.PROJECTION_COMMITTED,
        StorageJobStatus.MANIFEST_COMMITTED,
    ]
    start = order.index(current) + 1 if current in order else 0
    for status in order[start:]:
        repo.advance_status(job_id, to_status=status)


def _make_job(stack, repo, job_id: str) -> None:
    base = _load_stack_modules()
    repo.create_job(
        job_id=job_id,
        provider_id="KRAKEN_FUTURES",
        sensor_family=base.SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint=base._FP,
    )


# ---------------------------------------------------------------------------
# Matrix 1 — public API (I07R1 §40)
# ---------------------------------------------------------------------------


def build_public_api_matrix(tmp: Path) -> dict:
    """The cursor is unreachable by the public ordinary-transition API."""
    from crypto_sensor_fabric.storage.enums import StorageJobStatus
    from crypto_sensor_fabric.storage.jobs import JobTransitionConflict

    base = _load_stack_modules()
    JobStack = base.JobStack
    cases: list[dict] = []

    stack = JobStack(tmp / "api")
    repo = stack.repo
    _make_job(stack, repo, "ev-api")

    # ordinary_cursor_rejected: resume_token is not a public parameter.
    try:
        repo.advance_status(  # type: ignore[call-arg]
            "ev-api",
            to_status=StorageJobStatus.ACQUIRING,
            resume_token={"mode": "PAGE", "page_number": 1},
        )
        ordinary_cursor_rejected = "FAIL"
    except TypeError:
        ordinary_cursor_rejected = "PASS"
    # ordinary_anchor_rejected: no checkpoint anchor parameter either.
    try:
        repo.advance_status(  # type: ignore[call-arg]
            "ev-api",
            to_status=StorageJobStatus.ACQUIRING,
            last_committed_acquisition_id="acq-x",
        )
        ordinary_anchor_rejected = "FAIL"
    except TypeError:
        ordinary_anchor_rejected = "PASS"
    # private_gate_parameter_unavailable: no underscore flag exists.
    try:
        repo.advance_status(  # type: ignore[call-arg]
            "ev-api",
            to_status=StorageJobStatus.ACQUIRING,
            _via_checkpoint_gate=True,
        )
        private_gate_parameter_unavailable = "FAIL"
    except TypeError:
        private_gate_parameter_unavailable = "PASS"
    setattr(repo, "_via_checkpoint_gate", True)
    # checkpoint_only_through_gate: even the planted attribute cannot open
    # the checkpoint edge; only advance_checkpoint's private primitive can.
    try:
        repo.advance_status(
            "ev-api", to_status=StorageJobStatus.CHECKPOINT_ADVANCED
        )
        checkpoint_only_through_gate = "FAIL"
    except JobTransitionConflict:
        checkpoint_only_through_gate = "PASS"
    # failed_retryable_only_to_acquiring: the single legal retry edge.
    repo.advance_status("ev-api", to_status=StorageJobStatus.ACQUIRING)
    repo.advance_status(
        "ev-api", to_status=StorageJobStatus.FAILED_RETRYABLE, reason="429"
    )
    bad_targets = []
    for bad in (
        StorageJobStatus.RAW_STAGED,
        StorageJobStatus.RAW_COMMITTED,
        StorageJobStatus.PROJECTION_PENDING,
        StorageJobStatus.PROJECTION_COMMITTED,
        StorageJobStatus.MANIFEST_COMMITTED,
    ):
        try:
            repo.advance_status("ev-api", to_status=bad, reason="why not")
            bad_targets.append(f"{bad.value}:ACCEPTED")
        except JobTransitionConflict:
            bad_targets.append(f"{bad.value}:CONFLICT")
    good = repo.advance_status(
        "ev-api", to_status=StorageJobStatus.ACQUIRING, reason="retry"
    )
    failed_retryable_only_to_acquiring = (
        "PASS"
        if all(t.endswith(":CONFLICT") for t in bad_targets)
        and good.status is StorageJobStatus.ACQUIRING
        else "FAIL"
    )
    cases.append(
        _case(
            "ordinary_cursor_rejected",
            outcome=ordinary_cursor_rejected,
        )
    )
    cases.append(
        _case(
            "ordinary_anchor_rejected",
            outcome=ordinary_anchor_rejected,
        )
    )
    cases.append(
        _case(
            "private_gate_parameter_unavailable",
            outcome=private_gate_parameter_unavailable,
        )
    )
    cases.append(
        _case(
            "checkpoint_only_through_gate",
            planted_flag_outcome=checkpoint_only_through_gate,
        )
    )
    cases.append(
        _case(
            "failed_retryable_only_to_acquiring",
            bad_targets=bad_targets,
            resume_outcome=(
                "ACCEPTED" if good.status is StorageJobStatus.ACQUIRING else "REJECTED"
            ),
            result=failed_retryable_only_to_acquiring,
        )
    )
    return {
        "matrix": "BLOC_04_I07R1_PUBLIC_API_MATRIX",
        "checkpoint": "SENSOR-B4-I07R1",
        "doctrine": "I07R1 §3/§4/§5/§21 — gate-only cursor mutation, single retry edge",
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Matrix 2 — checkpoint identity (I07R1 §40)
# ---------------------------------------------------------------------------


def build_checkpoint_identity_matrix(tmp: Path) -> dict:
    """Checkpoint proof is identity-bound, provenance-gated, floor-exact."""
    from crypto_sensor_fabric.contracts.enums import SensorFamily
    from crypto_sensor_fabric.providers.base.enums import Granularity
    from crypto_sensor_fabric.providers.base.models import ResumeToken
    from crypto_sensor_fabric.storage.enums import StorageJobStatus
    from crypto_sensor_fabric.storage.jobs import JobResumeGateError

    base = _load_stack_modules()
    JobStack = base.JobStack
    cases: list[dict] = []

    def _full(stack, job_id: str, acq: str, man: str, data: bytes) -> str:
        sha = stack.seed_blob(data)
        stack.seed_acquisition(sha, acq)
        stack.seed_manifest(man, f"PK-{man}", sha)
        return sha

    def _expect_gate_error(fn) -> str:
        try:
            fn()
            return "FAIL"
        except JobResumeGateError:
            return "PASS"

    # job_acquisition_exact: identity-bound proof advances cleanly.
    stack = JobStack(tmp / "exact")
    repo = stack.repo
    _make_job(stack, repo, "ev-ident")
    _drive_to_manifest(repo, "ev-ident")
    sha = _full(stack, "ev-ident", "acq-ident", "pm-ident", b'{"rows":["x1"]}')
    state = repo.advance_checkpoint(
        "ev-ident",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id="acq-ident",
        manifest_id="pm-ident",
    )
    cases.append(
        _case(
            "job_acquisition_exact",
            status=state.status.value,
            blob_sha256=state.last_committed_blob_sha256,
            result=(
                "PASS"
                if state.status is StorageJobStatus.CHECKPOINT_ADVANCED
                and state.last_committed_blob_sha256 == sha
                else "FAIL"
            ),
        )
    )

    # provider_mismatch: durable acquisition from another provider.
    stack2 = JobStack(tmp / "prov")
    repo2 = stack2.repo
    _make_job(stack2, repo2, "ev-prov")
    _drive_to_manifest(repo2, "ev-prov")
    sha2 = stack2.seed_blob(b'{"rows":["x2"]}')
    stack2.seed_acquisition(sha2, "acq-prov", provider_id="BINANCE_SPOT")
    outcome = _expect_gate_error(
        lambda: repo2.advance_checkpoint(
            "ev-prov",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id="acq-prov",
        )
    )
    cases.append(_case("provider_mismatch", rejected=outcome, result=outcome))

    # sensor_mismatch.
    stack3 = JobStack(tmp / "sensor")
    repo3 = stack3.repo
    _make_job(stack3, repo3, "ev-sensor")
    _drive_to_manifest(repo3, "ev-sensor")
    sha3 = stack3.seed_blob(b'{"rows":["x3"]}')
    stack3.seed_acquisition(
        sha3, "acq-sensor", sensor_family=SensorFamily.MECHANICAL_TRADE
    )
    outcome = _expect_gate_error(
        lambda: repo3.advance_checkpoint(
            "ev-sensor",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id="acq-sensor",
        )
    )
    cases.append(_case("sensor_mismatch", rejected=outcome, result=outcome))

    # request_fingerprint_mismatch.
    stack4 = JobStack(tmp / "fp")
    repo4 = stack4.repo
    _make_job(stack4, repo4, "ev-fp")
    _drive_to_manifest(repo4, "ev-fp")
    sha4 = stack4.seed_blob(b'{"rows":["x4"]}')
    stack4.seed_acquisition(sha4, "acq-fp", request_fingerprint="fp-other")
    outcome = _expect_gate_error(
        lambda: repo4.advance_checkpoint(
            "ev-fp",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id="acq-fp",
        )
    )
    cases.append(
        _case("request_fingerprint_mismatch", rejected=outcome, result=outcome)
    )

    # cross_job_same_blob: content equality does not transfer identity.
    stack5 = JobStack(tmp / "crossjob")
    repo5 = stack5.repo
    _make_job(stack5, repo5, "ev-cross-a")
    _drive_to_manifest(repo5, "ev-cross-a")
    sha5 = stack5.seed_blob(b'{"rows":["shared"]}')
    stack5.seed_acquisition(sha5, "acq-cross-b", request_fingerprint="fp-other")
    outcome = _expect_gate_error(
        lambda: repo5.advance_checkpoint(
            "ev-cross-a",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id="acq-cross-b",
        )
    )
    cases.append(_case("cross_job_same_blob", rejected=outcome, result=outcome))

    # forensic_acquisition_rejected: failed outcome never moves the cursor.
    stack6 = JobStack(tmp / "forensic")
    repo6 = stack6.repo
    _make_job(stack6, repo6, "ev-forensic")
    _drive_to_manifest(repo6, "ev-forensic")
    sha6 = stack6.seed_blob(b'{"rows":["f"]}')
    stack6.seed_acquisition(sha6, "acq-forensic", http_status="404")
    outcome = _expect_gate_error(
        lambda: repo6.advance_checkpoint(
            "ev-forensic",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id="acq-forensic",
        )
    )
    cases.append(
        _case("forensic_acquisition_rejected", rejected=outcome, result=outcome)
    )

    # manifest_exact.
    stack7 = JobStack(tmp / "mexact")
    repo7 = stack7.repo
    _make_job(stack7, repo7, "ev-mexact")
    _drive_to_manifest(repo7, "ev-mexact")
    _full(stack7, "ev-mexact", "acq-mexact", "pm-mexact", b'{"rows":["m1"]}')
    state7 = repo7.advance_checkpoint(
        "ev-mexact",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id="acq-mexact",
        manifest_id="pm-mexact",
    )
    cases.append(
        _case(
            "manifest_exact",
            status=state7.status.value,
            manifest_id=state7.last_manifest_id,
            result=(
                "PASS"
                if state7.status is StorageJobStatus.CHECKPOINT_ADVANCED
                else "FAIL"
            ),
        )
    )

    # manifest_*_mismatch: same blob attributed by an alt durable pair.
    def _manifest_mismatch(tag: str, **fields: Any) -> str:
        stackX = JobStack(tmp / tag)
        repoX = stackX.repo
        _make_job(stackX, repoX, f"ev-{tag}")
        _drive_to_manifest(repoX, f"ev-{tag}")
        shaX = stackX.seed_blob(b'{"rows":["mm"]}')
        stackX.seed_acquisition(shaX, f"acq-{tag}")
        stackX.seed_manifest(f"pm-{tag}", f"PK-{tag}", shaX)
        alt_provider = fields.get("provider", "KRAKEN_FUTURES")
        alt_venue = fields.get("venue", alt_provider)
        alt_sensor = fields.get("sensor_family", SensorFamily.MECHANICAL_FUNDING)
        alt_instrument = fields.get("native_instrument", "PI_XBTUSD")
        alt_granularity = fields.get("source_granularity", Granularity.G1H)
        stackX.seed_acquisition(
            shaX,
            f"acq-{tag}-alt",
            provider_id=alt_provider,
            venue=alt_venue,
            sensor_family=alt_sensor,
            native_instrument=alt_instrument,
            native_granularity=alt_granularity,
        )
        stackX.seed_manifest(
            f"pm-{tag}-alt",
            f"PK-{tag}-alt",
            shaX,
            provider=alt_provider,
            venue=alt_venue,
            sensor_family=alt_sensor,
            native_instrument=alt_instrument,
            source_granularity=alt_granularity,
        )
        return _expect_gate_error(
            lambda: repoX.advance_checkpoint(
                f"ev-{tag}",
                resume_token=ResumeToken(
                    mode="PAGE", provider_cursor="c", page_number=1
                ),
                acquisition_id=f"acq-{tag}",
                manifest_id=f"pm-{tag}-alt",
            )
        )

    for tag, label in (
        ("mprov", "manifest_provider_mismatch"),
        ("mvenue", "manifest_venue_mismatch"),
        ("msensor", "manifest_sensor_mismatch"),
        ("minst", "manifest_instrument_mismatch"),
        ("mgran", "manifest_granularity_mismatch"),
    ):
        fields: dict[str, Any] = {}
        if tag == "mprov":
            fields["provider"] = "BINANCE_SPOT"
        elif tag == "mvenue":
            fields["venue"] = "BINANCE_SPOT"
        elif tag == "msensor":
            fields["sensor_family"] = SensorFamily.MECHANICAL_TRADE
        elif tag == "minst":
            fields["native_instrument"] = "BTC_USDT"
        elif tag == "mgran":
            fields["source_granularity"] = Granularity.G4H
        outcome = _manifest_mismatch(tag, **fields)
        cases.append(_case(label, rejected=outcome, result=outcome))

    # raw_floor_no_manifest: RAW floor requires manifest_id=None.
    stack8 = JobStack(
        tmp / "rawfloor",
        min_durable_status=StorageJobStatus.RAW_COMMITTED,
    )
    repo8 = stack8.repo
    _make_job(stack8, repo8, "ev-rawfloor")
    repo8.advance_status("ev-rawfloor", to_status=StorageJobStatus.ACQUIRING)
    repo8.advance_status("ev-rawfloor", to_status=StorageJobStatus.RAW_STAGED)
    repo8.advance_status("ev-rawfloor", to_status=StorageJobStatus.RAW_COMMITTED)
    sha8 = stack8.seed_blob(b'{"rows":["r"]}')
    stack8.seed_acquisition(sha8, "acq-rawfloor")
    rejected = _expect_gate_error(
        lambda: repo8.advance_checkpoint(
            "ev-rawfloor",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id="acq-rawfloor",
            manifest_id="pm-contradictory",
        )
    )
    ok = repo8.advance_checkpoint(
        "ev-rawfloor",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id="acq-rawfloor",
        manifest_id=None,
    )
    cases.append(
        _case(
            "raw_floor_no_manifest",
            contradictory_anchor_rejected=rejected,
            none_form_status=ok.status.value,
            stored_manifest_id=ok.last_manifest_id,
            result=(
                "PASS"
                if rejected == "PASS"
                and ok.status is StorageJobStatus.CHECKPOINT_ADVANCED
                and ok.last_manifest_id is None
                else "FAIL"
            ),
        )
    )

    # manifest_floor_required: MANIFEST floor demands the exact manifest.
    stack9 = JobStack(tmp / "mfloor")
    repo9 = stack9.repo
    _make_job(stack9, repo9, "ev-mfloor")
    _drive_to_manifest(repo9, "ev-mfloor")
    sha9 = stack9.seed_blob(b'{"rows":["mf"]}')
    stack9.seed_acquisition(sha9, "acq-mfloor2")
    rejected2 = _expect_gate_error(
        lambda: repo9.advance_checkpoint(
            "ev-mfloor",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id="acq-mfloor2",
        )
    )
    cases.append(
        _case(
            "manifest_floor_required",
            missing_manifest_rejected=rejected2,
            result=rejected2,
        )
    )
    return {
        "matrix": "BLOC_04_I07R1_CHECKPOINT_IDENTITY_MATRIX",
        "checkpoint": "SENSOR-B4-I07R1",
        "doctrine": "I07R1 §7-§13 — evidence belongs to the exact job/request",
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Matrix 3 — restart replay (I07R1 §40)
# ---------------------------------------------------------------------------


def _tamper_event(root: Path, selector, mutator) -> None:
    """Apply ``mutator`` to the first committed event fragment matching
    ``selector`` (physical names are content hashes, so selection is by
    payload, never filename order)."""
    events_dir = root / "catalogs" / "jobs_state" / "events"
    victim = None
    payload = None
    for path in sorted(events_dir.glob("*.json")):
        candidate = json.loads(path.read_text(encoding="utf-8"))
        if selector(candidate):
            victim = path
            payload = candidate
            break
    assert victim is not None and payload is not None, (
        "no event matched the tamper selector"
    )
    mutator(payload)
    victim.write_text(json.dumps(payload), encoding="utf-8")


def _proof_event(payload: dict) -> bool:
    return "checkpoint_proof" in payload


def build_restart_replay_matrix(tmp: Path) -> dict:
    """Replay enforces the SAME graph + cross-constraints as the writer."""
    from crypto_sensor_fabric.providers.base.models import ResumeToken
    from crypto_sensor_fabric.storage.enums import StorageJobStatus
    from crypto_sensor_fabric.storage.jobs import (
        JobCatalogCorrupt,
    )

    base = _load_stack_modules()
    JobStack = base.JobStack
    cases: list[dict] = []

    def _checkpointed(tag: str) -> Path:
        root = tmp / tag
        stack = JobStack(root)
        repo = stack.repo
        _make_job(stack, repo, "ev")
        _drive_to_manifest(repo, "ev")
        sha = stack.seed_blob(b'{"rows":["rp"]}')
        stack.seed_acquisition(sha, "acq")
        stack.seed_manifest("pm", "PK", sha)
        repo.advance_checkpoint(
            "ev",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id="acq",
            manifest_id="pm",
        )
        return root

    def _fails_restart(root: Path) -> str:
        try:
            JobStack(root).repo
            return "FAIL"
        except JobCatalogCorrupt:
            return "PASS"

    # valid_chain.
    root = _checkpointed("valid")
    try:
        JobStack(root).repo
        valid = "PASS"
    except Exception:  # noqa: BLE001
        valid = "FAIL"
    cases.append(_case("valid_chain", restart=valid, result=valid))

    # forward_skip: RAW_STAGED rewritten to a two-step target.
    root = _checkpointed("fskip")
    _tamper_event(
        root,
        lambda p: p["transition"]["to_status"] == "RAW_STAGED",
        lambda p: p["transition"].__setitem__(
            "to_status", "PROJECTION_COMMITTED"
        ),
    )
    outcome = _fails_restart(root)
    cases.append(_case("forward_skip", restart=outcome, result=outcome))

    # ungated_checkpoint: ordinary event retargeted to CHECKPOINT_ADVANCED.
    root = _checkpointed("ungated")
    _tamper_event(
        root,
        lambda p: p["transition"]["to_status"] == "RAW_STAGED",
        lambda p: p["transition"].__setitem__("to_status", "CHECKPOINT_ADVANCED"),
    )
    outcome = _fails_restart(root)
    cases.append(_case("ungated_checkpoint", restart=outcome, result=outcome))

    # checkpoint_proof_missing.
    root = _checkpointed("proofmissing")
    _tamper_event(
        root,
        _proof_event,
        lambda p: p.pop("checkpoint_proof", None),
    )
    outcome = _fails_restart(root)
    cases.append(
        _case("checkpoint_proof_missing", restart=outcome, result=outcome)
    )

    # checkpoint_proof_mismatch: proof acquisition != state anchor.
    root = _checkpointed("proofmismatch")
    _tamper_event(
        root,
        _proof_event,
        lambda p: p["checkpoint_proof"].__setitem__(
            "acquisition_id", "acq-someone-else"
        ),
    )
    outcome = _fails_restart(root)
    cases.append(
        _case("checkpoint_proof_mismatch", restart=outcome, result=outcome)
    )

    # failure_without_reason.
    root = tmp / "failnoreason"
    stack = JobStack(root)
    repo = stack.repo
    _make_job(stack, repo, "ev")
    repo.advance_status("ev", to_status=StorageJobStatus.ACQUIRING)
    repo.advance_status(
        "ev", to_status=StorageJobStatus.FAILED_RETRYABLE, reason="x"
    )
    _tamper_event(
        root,
        lambda p: p["transition"]["to_status"] == "FAILED_RETRYABLE",
        lambda p: p["transition"].__setitem__("reason", None),
    )
    outcome = _fails_restart(root)
    cases.append(
        _case("failure_without_reason", restart=outcome, result=outcome)
    )

    # failed_retryable_bad_target (restart side).
    root = tmp / "retrybad"
    stack = JobStack(root)
    repo = stack.repo
    _make_job(stack, repo, "ev")
    repo.advance_status("ev", to_status=StorageJobStatus.ACQUIRING)
    repo.advance_status(
        "ev", to_status=StorageJobStatus.FAILED_RETRYABLE, reason="x"
    )
    _tamper_event(
        root,
        lambda p: p["transition"]["to_status"] == "FAILED_RETRYABLE",
        lambda p: p["transition"].__setitem__("to_status", "MANIFEST_COMMITTED"),
    )
    outcome = _fails_restart(root)
    cases.append(
        _case("failed_retryable_bad_target", restart=outcome, result=outcome)
    )

    # job_identity_tamper.
    root = _checkpointed("jobid")
    _tamper_event(
        root,
        lambda p: p["transition"]["to_status"] == "CHECKPOINT_ADVANCED",
        lambda p: p["resulting_state"].__setitem__(
            "request_fingerprint", "fp-forged"
        ),
    )
    outcome = _fails_restart(root)
    cases.append(_case("job_identity_tamper", restart=outcome, result=outcome))

    # ordinary_cursor_tamper.
    root = tmp / "cursor"
    stack = JobStack(root)
    repo = stack.repo
    _make_job(stack, repo, "ev")
    repo.advance_status("ev", to_status=StorageJobStatus.ACQUIRING)
    _tamper_event(
        root,
        lambda p: p["transition"]["to_status"] == "ACQUIRING",
        lambda p: p["resulting_state"].__setitem__(
            "resume_token",
            {
                "mode": "PAGE",
                "provider_cursor": "forged",
                "page_number": 99,
            },
        ),
    )
    outcome = _fails_restart(root)
    cases.append(_case("ordinary_cursor_tamper", restart=outcome, result=outcome))

    # ordinary_anchor_tamper.
    root = tmp / "anchor"
    stack = JobStack(root)
    repo = stack.repo
    _make_job(stack, repo, "ev")
    repo.advance_status("ev", to_status=StorageJobStatus.ACQUIRING)
    _tamper_event(
        root,
        lambda p: p["transition"]["to_status"] == "ACQUIRING",
        lambda p: p["resulting_state"].__setitem__(
            "last_committed_acquisition_id", "acq-forged"
        ),
    )
    outcome = _fails_restart(root)
    cases.append(_case("ordinary_anchor_tamper", restart=outcome, result=outcome))

    # blob_anchor_tamper: both proof and state point at a foreign blob.
    root = _checkpointed("blobmm")
    _tamper_event(
        root,
        _proof_event,
        lambda p: (
            p["checkpoint_proof"].__setitem__("blob_sha256", "c" * 64),
            p["resulting_state"].__setitem__(
                "last_committed_blob_sha256", "c" * 64
            ),
        ),
    )
    outcome = _fails_restart(root)
    cases.append(_case("blob_anchor_tamper", restart=outcome, result=outcome))

    # manifest_anchor_tamper: unrelated but internally-consistent manifest.
    root = _checkpointed("manmm")
    _tamper_event(
        root,
        _proof_event,
        lambda p: (
            p["checkpoint_proof"].__setitem__("manifest_id", "pm-unrelated"),
            p["resulting_state"].__setitem__("last_manifest_id", "pm-unrelated"),
        ),
    )
    outcome = _fails_restart(root)
    cases.append(_case("manifest_anchor_tamper", restart=outcome, result=outcome))

    # event_identity_tamper: coordinated filename + logical id + sequence.
    root = _checkpointed("evid")
    events_dir = root / "catalogs" / "jobs_state" / "events"
    victim = None
    for path in sorted(events_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload["transition"]["to_status"] == "ACQUIRING":
            victim = path
            break
    assert victim is not None, "expected the ACQUIRING event fragment"
    payload = json.loads(victim.read_text(encoding="utf-8"))
    old_name = victim.name
    new_id = "ev:000099"
    payload["transition_id"] = new_id
    payload["transition"]["transition_id"] = new_id
    payload["sequence"] = 99
    victim.write_text(json.dumps(payload), encoding="utf-8")
    new_path = events_dir / (
        hashlib.sha256(new_id.encode("utf-8")).hexdigest() + ".json"
    )
    victim.rename(new_path)
    # Sanity: the coordinated mutation is self-consistent on disk (the
    # stored logical id hashes to its own new filename).
    renamed = json.loads(new_path.read_text(encoding="utf-8"))
    assert renamed["transition_id"] == new_id
    assert old_name != new_path.name
    outcome = _fails_restart(root)
    cases.append(_case("event_identity_tamper", restart=outcome, result=outcome))
    return {
        "matrix": "BLOC_04_I07R1_RESTART_REPLAY_MATRIX",
        "checkpoint": "SENSOR-B4-I07R1",
        "doctrine": "I07R1 §19-§27 — the reader enforces the writer's state machine",
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Matrix 4 — coordination (I07R1 §40)
# ---------------------------------------------------------------------------


def build_coordination_matrix(tmp: Path) -> dict:
    """Safe lock namespace + post-lock refresh across repositories."""
    from crypto_sensor_fabric.providers.base.models import ResumeToken
    from crypto_sensor_fabric.storage.enums import StorageJobStatus
    from crypto_sensor_fabric.storage.json_catalog import (
        DurableJsonCatalog,
        JsonCatalogCorrupt,
    )

    base = _load_stack_modules()
    JobStack = base.JobStack
    cases: list[dict] = []

    # safe_lock_path_traversal.
    stack = JobStack(tmp / "traversal")
    repo = stack.repo
    locked_ids = ["../escape", "../../outside", "C:\\temp\\x", "/a/b", "a\\b"]
    traversal_ok = "PASS"
    for job_id in locked_ids:
        _make_job(stack, repo, job_id)
        repo.advance_status(job_id, to_status=StorageJobStatus.ACQUIRING)
        lock_path = repo._lock_path(job_id)  # noqa: SLF001
        if lock_path.parent != repo._locks_root:  # noqa: SLF001
            traversal_ok = "FAIL"
    cases.append(_case("safe_lock_path_traversal", result=traversal_ok))

    # safe_lock_unicode_long.
    stack2 = JobStack(tmp / "unicode")
    repo2 = stack2.repo
    unicode_ok = "PASS"
    for job_id in ("π shifted \U0001f680", "中文 job", "j" * 500):
        _make_job(stack2, repo2, job_id)
        repo2.advance_status(job_id, to_status=StorageJobStatus.ACQUIRING)
        lock_path = repo2._lock_path(job_id)  # noqa: SLF001
        if len(lock_path.stem) != 64 or any(
            c not in "0123456789abcdef" for c in lock_path.stem
        ):
            unicode_ok = "FAIL"
    cases.append(_case("safe_lock_unicode_long", result=unicode_ok))

    # lock_key_collision: distinct logical IDs -> distinct full digests.
    stack3 = JobStack(tmp / "collision")
    repo3 = stack3.repo
    ids = ("job-α", "job-a", "job/A", "job\\A", "job:a")
    keys = {i: repo3._lock_path(i).name for i in ids}  # noqa: SLF001
    collision_ok = (
        "PASS" if len(set(keys.values())) == len(ids) else "FAIL"
    )
    for job_id, name in keys.items():
        if name[:-5] != hashlib.sha256(job_id.encode("utf-8")).hexdigest():
            collision_ok = "FAIL"
    cases.append(
        _case(
            "lock_key_collision",
            distinct_keys=len(set(keys.values())),
            total_ids=len(ids),
            result=collision_ok,
        )
    )

    # two_repo_refresh: repo B (pre-existing) observes A's writes.
    shared = base.TickingClock()
    stack4 = JobStack(tmp / "refresh", clock=shared)
    repo_a = stack4.repo
    repo_b = type(repo_a)(
        tmp / "refresh" / "catalogs" / "jobs_state",
        acquisitions=stack4.acq_repo,
        manifests=stack4.manifest_repo,
        blob_metadata_repository=stack4.blob_repo,
        clock=shared,
    )
    _make_job(stack4, repo_a, "ev-refresh")
    repo_b.advance_status("ev-refresh", to_status=StorageJobStatus.ACQUIRING)
    repo_a.advance_status(
        "ev-refresh", to_status=StorageJobStatus.RAW_STAGED
    )
    state = repo_b.advance_status(
        "ev-refresh",
        to_status=StorageJobStatus.RAW_COMMITTED,
        expected_from=StorageJobStatus.RAW_STAGED,
    )
    chain = [t.to_status.value for t in repo_b.list_transitions("ev-refresh")]
    two_repo_refresh = (
        "PASS"
        if state.status is StorageJobStatus.RAW_COMMITTED
        and chain
        == [
            "ACQUIRING",
            "RAW_STAGED",
            "RAW_COMMITTED",
        ]
        else "FAIL"
    )
    cases.append(
        _case(
            "two_repo_refresh",
            observed_chain=chain,
            result=two_repo_refresh,
        )
    )

    # two_repo_sequence: racing one transition cannot fork the chain.
    shared2 = base.TickingClock()
    stack5 = JobStack(tmp / "seq", clock=shared2)
    repo_a5 = stack5.repo
    repo_b5 = type(repo_a5)(
        tmp / "seq" / "catalogs" / "jobs_state",
        acquisitions=stack5.acq_repo,
        manifests=stack5.manifest_repo,
        blob_metadata_repository=stack5.blob_repo,
        clock=shared2,
    )
    _make_job(stack5, repo_a5, "ev-seq")
    repo_a5.advance_status("ev-seq", to_status=StorageJobStatus.ACQUIRING)
    import threading as _threading

    errors: list[Exception] = []
    barrier = _threading.Barrier(2)

    def _worker(r) -> None:
        try:
            barrier.wait()
            r.advance_status("ev-seq", to_status=StorageJobStatus.RAW_STAGED)
        except Exception as exc:  # noqa: BLE001 — typed loser acceptable
            errors.append(exc)

    threads = [
        _threading.Thread(target=_worker, args=(r,))
        for r in (repo_a5, repo_b5)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    fresh = JobStack(tmp / "seq", clock=shared2).repo
    chain2 = [
        t.to_status.value for t in fresh.list_transitions("ev-seq")
    ]
    two_repo_sequence = (
        "PASS"
        if chain2 == ["ACQUIRING", "RAW_STAGED"]
        and len(errors) <= 1
        else "FAIL"
    )
    cases.append(
        _case(
            "two_repo_sequence",
            committed_chain=chain2,
            loser_errors=len(errors),
            result=two_repo_sequence,
        )
    )

    # external_checkpoint_retry: repo B adopts A's committed checkpoint.
    shared3 = base.TickingClock()
    stack6 = JobStack(tmp / "xtretry", clock=shared3)
    repo_a6 = stack6.repo
    repo_b6 = type(repo_a6)(
        tmp / "xtretry" / "catalogs" / "jobs_state",
        acquisitions=stack6.acq_repo,
        manifests=stack6.manifest_repo,
        blob_metadata_repository=stack6.blob_repo,
        clock=shared3,
    )
    _make_job(stack6, repo_a6, "ev-xt")
    _drive_to_manifest(repo_a6, "ev-xt")
    sha6 = stack6.seed_blob(b'{"rows":["xt"]}')
    stack6.seed_acquisition(sha6, "acq-xt")
    stack6.seed_manifest("pm-xt", "PK-XT", sha6)
    committed = repo_a6.advance_checkpoint(
        "ev-xt",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id="acq-xt",
        manifest_id="pm-xt",
    )
    retried = repo_b6.advance_checkpoint(
        "ev-xt",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id="acq-xt",
        manifest_id="pm-xt",
    )
    gate_events = [
        t
        for t in repo_b6.list_transitions("ev-xt")
        if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    ]
    external_retry = (
        "PASS"
        if committed.status is StorageJobStatus.CHECKPOINT_ADVANCED
        and retried.status is StorageJobStatus.CHECKPOINT_ADVANCED
        and retried.last_committed_blob_sha256 == sha6
        and len(gate_events) == 1
        else "FAIL"
    )
    cases.append(
        _case(
            "external_checkpoint_retry",
            adopted_status=retried.status.value,
            gate_event_count=len(gate_events),
            result=external_retry,
        )
    )

    # Refresh fail-closed probe (vanish) folded into the refresh doctrine
    # case for machine evidence completeness.
    stack7 = JobStack(tmp / "vanish")
    repo7 = stack7.repo
    _make_job(stack7, repo7, "ev-vanish")
    repo7.advance_status("ev-vanish", to_status=StorageJobStatus.ACQUIRING)
    events_dir = tmp / "vanish" / "catalogs" / "jobs_state" / "events"
    catalog = DurableJsonCatalog(events_dir, logical_id_field="transition_id")
    vanished = "PASS"
    next(events_dir.glob("*.json")).unlink()
    try:
        catalog.refresh()
        vanished = "FAIL"
    except JsonCatalogCorrupt:
        pass
    cases.append(
        _case(
            "refresh_fail_closed_on_vanish",
            result=vanished,
        )
    )
    return {
        "matrix": "BLOC_04_I07R1_COORDINATION_MATRIX",
        "checkpoint": "SENSOR-B4-I07R1",
        "doctrine": "I07R1 §28-§36 — logical IDs never become paths; locks refresh truth",
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Read-only comparison tests (I05R4 evidence policy, I07R1 §42)
# ---------------------------------------------------------------------------


BUILDERS = [
    ("build_public_api_matrix", "BLOC_04_I07R1_PUBLIC_API_MATRIX.json"),
    (
        "build_checkpoint_identity_matrix",
        "BLOC_04_I07R1_CHECKPOINT_IDENTITY_MATRIX.json",
    ),
    (
        "build_restart_replay_matrix",
        "BLOC_04_I07R1_RESTART_REPLAY_MATRIX.json",
    ),
    (
        "build_coordination_matrix",
        "BLOC_04_I07R1_COORDINATION_MATRIX.json",
    ),
]


@pytest.mark.parametrize("builder_name,filename", BUILDERS)
def test_generated_matches_committed(
    builder_name: str, filename: str, tmp_path
) -> None:
    committed = (EVIDENCE_DIR / filename).read_bytes()
    builder = globals()[builder_name]
    generated = stable_evidence_bytes(builder(tmp_path))
    assert generated == committed, (
        f"{filename}: regenerated evidence diverges from committed bytes — "
        "a production behavior changed; update the checkpoint evidence "
        "explicitly, never via test execution"
    )


def test_evidence_directory_untouched_after_run(tmp_path) -> None:
    """Running this module's builders leaves no trace in the committed
    evidence tree (read-only policy, I07R1 §42)."""
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
