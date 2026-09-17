"""SENSOR-B4-I07R1G — deterministic machine-evidence matrix for the runtime
checkpoint-proof schema / replay-parity seal.

Builders are PURE: they run the real scenarios in tmp dirs and return dicts
serialized through ``stable_evidence_bytes``.  Normal pytest runs NEVER write
the committed evidence tree — tests generate to memory/tmp_path and compare
against committed bytes (I05R4 read-only policy, I07R1G §17/§19).  Publication
happens once per checkpoint via an explicit operator invocation (module
bottom).

Matrix (I07R1G §17):
- BLOC_04_I07R1G_RUNTIME_PROOF_PARITY_MATRIX.json

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

#: Spec matrix case name -> the adversarial case implementing it (§11).
_FORGED_MATRIX_CASES: tuple[tuple[str, str], ...] = (
    ("proof_missing", "proof-missing"),
    ("proof_version_unknown", "version-unknown"),
    ("proof_version_missing", "version-missing"),
    ("floor_missing", "floor-missing"),
    ("floor_unknown", "floor-unknown"),
    ("acquisition_anchor_mismatch", "acquisition-mismatch"),
    ("blob_anchor_mismatch", "blob-mismatch"),
    ("manifest_anchor_mismatch", "manifest-mismatch"),
    ("raw_manifest_contradiction", "raw-manifest-contradiction"),
    ("manifest_missing_anchor", "manifest-anchor-missing"),
)

#: §11 K/L plus the closed-schema variants, aggregated under
#: ``proof_wrong_type`` (wrong Python type OR not the closed V1 field set).
_WRONG_TYPE_VARIANTS: tuple[str, ...] = (
    "proof-wrong-type",
    "proof-empty-mapping",
    "proof-string",
    "proof-integer",
    "proof-bool",
    "proof-extra-field",
)


def stable_evidence_bytes(payload: dict) -> bytes:
    """Canonical deterministic serializer (I05R4 §31 doctrine)."""
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _case(name: str, **fields) -> dict:
    return {"case": name, **fields}


def _load_base():
    return load_sibling("_i07r1_base_mod", "test_job_state_r1")


def _load_r1g():
    return load_sibling("_i07r1g_mod", "test_job_state_r1g")


def _resume_token():
    from crypto_sensor_fabric.providers.base.models import ResumeToken

    return ResumeToken(mode="PAGE", provider_cursor="c", page_number=1)


def _gate_event_count(repo, job_id: str) -> int:
    from crypto_sensor_fabric.storage.enums import StorageJobStatus

    return len(
        [
            transition
            for transition in repo.list_transitions(job_id)
            if transition.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
        ]
    )


def _forge_fields(outcome: dict) -> dict:
    return {
        "runtime_rejected": outcome["runtime_rejected"],
        "restart_rejected": outcome["restart_rejected"],
        "typed_error": outcome["typed_error"],
        "runtime_path_error": outcome["runtime_path"],
        "restart_path_error": outcome["restart_path"],
        "corruption_wrote_nothing": outcome["chain_unchanged"],
        "result": outcome["result"],
    }


# ---------------------------------------------------------------------------
# Matrix — runtime and restart reject the SAME forged proofs (I07R1G §3-§15)
# ---------------------------------------------------------------------------


def build_runtime_proof_parity_matrix(tmp: Path) -> dict:
    """Every malformed persisted proof fails closed on BOTH paths."""
    from crypto_sensor_fabric.storage.enums import StorageJobStatus

    base = _load_base()
    r1g = _load_r1g()
    token = _resume_token()
    by_name = {case.name: case for case in r1g.CASES}
    cases: list[dict] = []

    for matrix_name, r1g_name in _FORGED_MATRIX_CASES:
        outcome = r1g.run_forged_case(tmp / r1g_name, by_name[r1g_name])
        cases.append(_case(matrix_name, **_forge_fields(outcome)))

    # proof_wrong_type (§8/§11-K/§11-L): a proof that is not a mapping, or not
    # the CLOSED V1 field set, is corruption — never TypeError/KeyError.
    variant_outcomes = [
        r1g.run_forged_case(tmp / name, by_name[name])
        for name in _WRONG_TYPE_VARIANTS
    ]
    cases.append(
        _case(
            "proof_wrong_type",
            variants=list(_WRONG_TYPE_VARIANTS),
            variants_rejected=sum(
                1 for outcome in variant_outcomes if outcome["result"] == "PASS"
            ),
            runtime_rejected=all(
                outcome["runtime_rejected"] for outcome in variant_outcomes
            ),
            restart_rejected=all(
                outcome["restart_rejected"] for outcome in variant_outcomes
            ),
            typed_error=sorted(
                {outcome["typed_error"] for outcome in variant_outcomes}
            )[0],
            result=(
                "PASS"
                if all(outcome["result"] == "PASS" for outcome in variant_outcomes)
                else "FAIL"
            ),
        )
    )

    # same_blob_wrong_acquisition (§12): identical bytes, different durable
    # request identity, internally consistent anchors — still corruption.
    case = by_name["same-blob-wrong-acquisition"]
    scenario = r1g.forge_later_checkpoint_head(tmp / "same-blob-premise", case)
    first = scenario["stack"].acq_repo.get_acquisition(f"acq-{case.name}")
    second = scenario["stack"].acq_repo.get_acquisition(r1g._SECOND_ACQ)  # noqa: SLF001
    forged = scenario["forged"]
    outcome = r1g.run_forged_case(tmp / "same-blob", case)
    cases.append(
        _case(
            "same_blob_wrong_acquisition",
            identical_blob_sha256=second.blob_sha256 == first.blob_sha256,
            different_request_identity=(
                second.request_fingerprint != first.request_fingerprint
            ),
            forged_anchors_internally_consistent=(
                forged["checkpoint_proof"]["acquisition_id"]
                == forged["resulting_state"]["last_committed_acquisition_id"]
            ),
            **_forge_fields(outcome),
        )
    )

    # valid_raw_cross_constructor_retry (§13): proof hardening must not
    # reinterpret valid history — a RAW checkpoint survives a stricter
    # MANIFEST_COMMITTED constructor restart.
    shared = base.TickingClock()
    stack = base.JobStack(
        tmp / "vraw",
        clock=shared,
        min_durable_status=StorageJobStatus.RAW_COMMITTED,
    )
    raw_result = "FAIL"
    raw_fields: dict[str, Any] = {}
    try:
        repo = stack.repo
        base._create(repo, "ev-vraw")
        base._drive_to_manifest(repo, "ev-vraw")
        sha = base._full_batch(
            stack, "acq-vraw", "pm-vraw", b'{"rows": ["vraw"]}'
        )
        repo.advance_checkpoint(
            "ev-vraw", resume_token=token, acquisition_id="acq-vraw"
        )
        stricter = base.JobStack(
            tmp / "vraw",
            clock=shared,
            min_durable_status=StorageJobStatus.MANIFEST_COMMITTED,
        ).repo
        retried = stricter.advance_checkpoint(
            "ev-vraw", resume_token=token, acquisition_id="acq-vraw"
        )
        raw_fields = {
            "status": retried.status.value,
            "last_manifest_id": retried.last_manifest_id,
            "blob_anchor_matches": retried.last_committed_blob_sha256 == sha,
            "gate_events": _gate_event_count(stricter, "ev-vraw"),
        }
        raw_result = (
            "PASS"
            if retried.status is StorageJobStatus.CHECKPOINT_ADVANCED
            and retried.last_manifest_id is None
            and raw_fields["blob_anchor_matches"]
            and raw_fields["gate_events"] == 1
            else "FAIL"
        )
    except Exception:  # noqa: BLE001 — recorded as FAIL below
        pass
    cases.append(_case("valid_raw_cross_constructor_retry", **raw_fields, result=raw_result))

    # valid_manifest_cross_constructor_retry (§13): the inverse — a MANIFEST
    # checkpoint survives a laxer RAW_COMMITTED constructor restart, and the
    # persisted floor is what re-proofs it.
    shared2 = base.TickingClock()
    stack2 = base.JobStack(
        tmp / "vman",
        clock=shared2,
        min_durable_status=StorageJobStatus.MANIFEST_COMMITTED,
    )
    man_result = "FAIL"
    man_fields: dict[str, Any] = {}
    try:
        repo2 = stack2.repo
        base._create(repo2, "ev-vman")
        base._drive_to_manifest(repo2, "ev-vman")
        sha2 = base._full_batch(
            stack2, "acq-vman", "pm-vman", b'{"rows": ["vman"]}'
        )
        repo2.advance_checkpoint(
            "ev-vman",
            resume_token=token,
            acquisition_id="acq-vman",
            manifest_id="pm-vman",
        )
        laxer = base.JobStack(
            tmp / "vman",
            clock=shared2,
            min_durable_status=StorageJobStatus.RAW_COMMITTED,
        ).repo
        retried2 = laxer.advance_checkpoint(
            "ev-vman",
            resume_token=token,
            acquisition_id="acq-vman",
            manifest_id="pm-vman",
        )
        proof = laxer._latest_event("ev-vman")["checkpoint_proof"]  # noqa: SLF001
        man_fields = {
            "status": retried2.status.value,
            "last_manifest_id": retried2.last_manifest_id,
            "blob_anchor_matches": retried2.last_committed_blob_sha256 == sha2,
            "persisted_proof_floor": proof["minimum_durable_status"],
            "gate_events": _gate_event_count(laxer, "ev-vman"),
        }
        man_result = (
            "PASS"
            if retried2.status is StorageJobStatus.CHECKPOINT_ADVANCED
            and retried2.last_manifest_id == "pm-vman"
            and man_fields["blob_anchor_matches"]
            and man_fields["persisted_proof_floor"]
            == StorageJobStatus.MANIFEST_COMMITTED.value
            and man_fields["gate_events"] == 1
            else "FAIL"
        )
    except Exception:  # noqa: BLE001 — recorded as FAIL below
        pass
    cases.append(
        _case("valid_manifest_cross_constructor_retry", **man_fields, result=man_result)
    )

    return {
        "matrix": "BLOC_04_I07R1G_RUNTIME_PROOF_PARITY_MATRIX",
        "checkpoint": "SENSOR-B4-I07R1G",
        "doctrine": (
            "I07R1G \u00a73-\u00a715 \u2014 proof existence is not proof "
            "validity: runtime exact-retry and restart replay validate a "
            "persisted checkpoint proof through one authority and reject "
            "exactly the same malformed proofs as typed JobCatalogCorrupt"
        ),
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Read-only comparison tests (I05R4 evidence policy, I07R1G §17/§19)
# ---------------------------------------------------------------------------


BUILDERS = [
    (
        "build_runtime_proof_parity_matrix",
        "BLOC_04_I07R1G_RUNTIME_PROOF_PARITY_MATRIX.json",
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
        "explicitly, never via test execution"
    )


def test_evidence_directory_untouched_after_run(tmp_path) -> None:
    """Running this module's builders leaves no trace in the committed
    evidence tree (read-only policy, I07R1G §17/§19)."""
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
