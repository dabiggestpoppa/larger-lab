"""SENSOR-B4-I07R1H — deterministic machine-evidence matrix for the runtime
refreshed-chain / restart validation parity seal.

Builders are PURE: they run the real scenarios in tmp dirs and return dicts
serialized through ``stable_evidence_bytes``.  Normal pytest runs NEVER write
the committed evidence tree — tests generate to memory/tmp_path and compare
against committed bytes (I05R4 read-only policy, I07R1H §29/§30).  Publication
happens once per checkpoint via an explicit operator invocation (module
bottom).

Matrix (I07R1H §29):
- BLOC_04_I07R1H_REFRESHED_CHAIN_PARITY_MATRIX.json

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

#: Spec matrix case name -> adversarial case name (I07R1H §29).
_CHAIN_MATRIX_CASES: tuple[tuple[str, str], ...] = (
    ("from_status_chain_break", "from-status-chain-break"),
    ("transition_job_id_mismatch", "transition-job-id-mismatch"),
    ("result_status_mismatch", "result-status-mismatch"),
    ("provider_identity_mismatch", "provider-identity-mismatch"),
    ("sensor_identity_mismatch", "sensor-identity-mismatch"),
    ("request_identity_mismatch", "request-identity-mismatch"),
    ("updated_at_transition_mismatch", "updated-at-transition-mismatch"),
    ("backward_chronology", "backward-chronology"),
    ("sequence_gap", "sequence-gap"),
    ("event_identity_mismatch", "event-identity-mismatch"),
    (
        "ordinary_resume_pointer_mutation",
        "ordinary-resume-pointer-mutation",
    ),
    ("ordinary_anchor_mutation", "ordinary-anchor-mutation"),
    ("proof_on_ordinary_event", "proof-on-ordinary-event"),
)


def stable_evidence_bytes(payload: dict) -> bytes:
    """Canonical deterministic serializer (I05R4 §31 doctrine)."""
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _case(name: str, **fields) -> dict:
    return {"case": name, **fields}


def _load_base():
    return load_sibling("_i07r1_base_mod", "test_job_state_r1")


def _load_r1h():
    return load_sibling("_i07r1h_mod", "test_job_state_r1h")


# ---------------------------------------------------------------------------
# Matrix — runtime and restart reject the SAME chain-corrupt heads (§17-§26)
# ---------------------------------------------------------------------------


def build_refreshed_chain_parity_matrix(tmp: Path) -> dict:
    """Every chain-corrupt head fails closed on BOTH paths; the intact
    refreshed control is adopted (§26)."""
    r1h = _load_r1h()
    by_name = {case.name: case for case in r1h.CASES}
    cases: list[dict] = []

    for matrix_name, case_name in _CHAIN_MATRIX_CASES:
        outcome = r1h.run_chain_case(tmp / case_name, by_name[case_name])
        cases.append(
            _case(
                matrix_name,
                runtime_rejected=outcome["runtime_path"] == r1h.CORRUPTION,
                restart_rejected=outcome["restart_path"] == r1h.CORRUPTION,
                typed_error=outcome["typed_error"],
                runtime_path_error=outcome["runtime_path"],
                restart_path_error=outcome["restart_path"],
                chain_unchanged=(
                    outcome["events_after"] == outcome["events_before"]
                ),
                result=outcome["result"],
            )
        )

    # Intact control (§26): the same publication mechanics with a fully
    # chain-valid event are adopted at runtime and accepted at restart —
    # the +1 event proves the forged head really entered the chain.
    control = r1h.run_chain_case(
        tmp / "intact-refreshed-control", by_name["intact-refreshed-control"]
    )
    cases.append(
        _case(
            "intact_refreshed_control",
            runtime_adopted=control["runtime_path"] == "NO_ERROR",
            restart_accepted=control["restart_path"] == "NO_ERROR",
            adoption_proven=control["events_after"]
            == control["events_before"] + 1,
            result=control["result"],
        )
    )

    # Cross-config valid retry regressions (§27): the runtime gate must not
    # reinterpret valid history — persisted-floor authority preserved.
    cases.extend(_cross_config_regressions(tmp))
    return {
        "matrix": "BLOC_04_I07R1H_REFRESHED_CHAIN_PARITY_MATRIX",
        "checkpoint": "SENSOR-B4-I07R1H",
        "doctrine": (
            "I07R1H \u00a73-\u00a728 — catalog integrity is not job-chain "
            "validity: a record adopted by outer-lock refresh must satisfy "
            "the same durable job contract a restart would enforce before "
            "it can influence runtime state"
        ),
        "cases": cases,
    }


def _cross_config_regressions(tmp: Path) -> list[dict]:
    """RAW-persisted / MANIFEST-constructor and MANIFEST-persisted /
    RAW-constructor valid retries (I07R1F §5-§6, preserved under I07R1H)."""
    base = _load_base()
    from crypto_sensor_fabric.storage.enums import StorageJobStatus

    def _retry(
        name: str,
        *,
        create_floor: Any,
        retry_floor: Any,
        want_manifest: str | None,
    ) -> dict:
        shared = base.TickingClock()
        stack = base.JobStack(
            tmp / name, clock=shared, min_durable_status=create_floor
        )
        try:
            repo = stack.repo
            job_id = f"ev-{name}"
            base._create(repo, job_id)
            if create_floor is StorageJobStatus.MANIFEST_COMMITTED:
                base._drive_to_manifest(repo, job_id)
            else:
                repo.advance_status(
                    job_id, to_status=StorageJobStatus.ACQUIRING
                )
                repo.advance_status(
                    job_id, to_status=StorageJobStatus.RAW_STAGED
                )
                repo.advance_status(
                    job_id, to_status=StorageJobStatus.RAW_COMMITTED
                )
            sha = base._full_batch(
                stack, f"acq-{name}", f"pm-{name}", b'{"rows": ["x"]}'
            )
            manifest_id = (
                f"pm-{name}"
                if create_floor is StorageJobStatus.MANIFEST_COMMITTED
                else None
            )
            base._checkpoint(repo, job_id, f"acq-{name}", manifest_id)
            restarted = base.JobStack(
                tmp / name, clock=shared, min_durable_status=retry_floor
            ).repo
            retried = restarted.advance_checkpoint(
                job_id,
                resume_token=_resume_token(),
                acquisition_id=f"acq-{name}",
                **(
                    {"manifest_id": manifest_id}
                    if manifest_id is not None
                    else {}
                ),
            )
            fields = {
                "status": retried.status.value,
                "last_manifest_id": retried.last_manifest_id,
                "blob_anchor_matches": (
                    retried.last_committed_blob_sha256 == sha
                ),
            }
            ok = (
                retried.status is StorageJobStatus.CHECKPOINT_ADVANCED
                and retried.last_manifest_id == want_manifest
                and fields["blob_anchor_matches"]
            )
            return _case(name, **fields, result="PASS" if ok else "FAIL")
        except Exception:  # noqa: BLE001 — recorded as FAIL below
            return _case(name, result="FAIL")

    return [
        _retry(
            "valid_raw_cross_constructor_retry",
            create_floor=StorageJobStatus.RAW_COMMITTED,
            retry_floor=StorageJobStatus.MANIFEST_COMMITTED,
            want_manifest=None,
        ),
        _retry(
            "valid_manifest_cross_constructor_retry",
            create_floor=StorageJobStatus.MANIFEST_COMMITTED,
            retry_floor=StorageJobStatus.RAW_COMMITTED,
            want_manifest="pm-valid_manifest_cross_constructor_retry",
        ),
    ]


def _resume_token():
    from crypto_sensor_fabric.providers.base.models import ResumeToken

    return ResumeToken(mode="PAGE", provider_cursor="c", page_number=1)


BUILDERS = [
    (
        "build_refreshed_chain_parity_matrix",
        "BLOC_04_I07R1H_REFRESHED_CHAIN_PARITY_MATRIX.json",
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
