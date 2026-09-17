"""SENSOR-B4-I07R1F — deterministic machine-evidence matrices for the final
persisted-floor / catalog-concurrency / ledger microseal.

Builders are PURE: they run the real scenarios in tmp dirs and return dicts
serialized through ``stable_evidence_bytes``.  Normal pytest runs NEVER write
the committed evidence tree — tests generate to memory/tmp_path and compare
against committed bytes (I05R4 read-only policy, I07R1 §42 / I07R1F §18).
Publication happens once per checkpoint via an explicit operator invocation
(module bottom).

Matrices (I07R1F §18):
- BLOC_04_I07R1F_PERSISTED_FLOOR_MATRIX.json
- BLOC_04_I07R1F_CATALOG_CONCURRENCY_MATRIX.json

Every case payload is structural only (statuses, counts, booleans) — no
timings, no wall-clock, no paths — so regeneration is byte-stable.
"""

from __future__ import annotations

import hashlib
import json
import sys
import threading
import time
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


def stable_evidence_bytes(payload: dict) -> bytes:
    """Canonical deterministic serializer (I05R4 §31 doctrine)."""
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _case(name: str, **fields) -> dict:
    return {"case": name, **fields}


def _load_base():
    return load_sibling("_i07r1_base_mod", "test_job_state_r1")


def _resume_token():
    from crypto_sensor_fabric.providers.base.models import ResumeToken

    return ResumeToken(mode="PAGE", provider_cursor="c", page_number=1)


def _gate_events(repo, job_id: str) -> list[Any]:
    from crypto_sensor_fabric.storage.enums import StorageJobStatus

    return [
        transition
        for transition in repo.list_transitions(job_id)
        if transition.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    ]


# ---------------------------------------------------------------------------
# Matrix 1 — persisted floor governs historical retries (I07R1F §3-§8)
# ---------------------------------------------------------------------------


def build_persisted_floor_matrix(tmp: Path) -> dict:
    """NEW checkpoints obey the constructor; OLD ones obey their own proof."""
    from crypto_sensor_fabric.storage.enums import StorageJobStatus

    base = _load_base()
    JobStack = base.JobStack
    token = _resume_token()
    cases: list[dict] = []

    # raw_persisted_manifest_constructor_retry (§5): a RAW checkpoint must
    # survive a stricter MANIFEST_COMMITTED constructor restart.
    shared = base.TickingClock()
    stack = JobStack(
        tmp / "pfraw",
        clock=shared,
        min_durable_status=StorageJobStatus.RAW_COMMITTED,
    )
    repo = stack.repo
    base._create(repo, "ev-pf-raw")
    base._drive_to_manifest(repo, "ev-pf-raw")
    sha = base._full_batch(
        stack, "acq-pf-raw", "pm-pf-raw", b'{"rows": ["pfr"]}'
    )
    repo.advance_checkpoint(
        "ev-pf-raw", resume_token=token, acquisition_id="acq-pf-raw"
    )
    stricter = JobStack(
        tmp / "pfraw",
        clock=shared,
        min_durable_status=StorageJobStatus.MANIFEST_COMMITTED,
    ).repo
    raw_result = "FAIL"
    adopted_manifest: Any = "UNSET"
    adopted_blob_matches = False
    raw_gate_count = -1
    try:
        retried = stricter.advance_checkpoint(
            "ev-pf-raw", resume_token=token, acquisition_id="acq-pf-raw"
        )
        adopted_manifest = retried.last_manifest_id
        adopted_blob_matches = retried.last_committed_blob_sha256 == sha
        raw_gate_count = len(_gate_events(stricter, "ev-pf-raw"))
        raw_result = (
            "PASS"
            if retried.status is StorageJobStatus.CHECKPOINT_ADVANCED
            and retried.last_manifest_id is None
            and adopted_blob_matches
            and raw_gate_count == 1
            else "FAIL"
        )
    except Exception:  # noqa: BLE001 — recorded as FAIL below
        pass
    cases.append(
        _case(
            "raw_persisted_manifest_constructor_retry",
            persisted_floor="RAW_COMMITTED",
            constructor_floor="MANIFEST_COMMITTED",
            adopted_manifest_id=adopted_manifest,
            adopted_blob_matches=adopted_blob_matches,
            gate_event_count=raw_gate_count,
            result=raw_result,
        )
    )

    # manifest_persisted_raw_constructor_retry (§6): a MANIFEST checkpoint
    # must survive a laxer RAW_COMMITTED constructor restart.
    shared2 = base.TickingClock()
    stack2 = JobStack(
        tmp / "pfman",
        clock=shared2,
        min_durable_status=StorageJobStatus.MANIFEST_COMMITTED,
    )
    repo2 = stack2.repo
    base._create(repo2, "ev-pf-man")
    base._drive_to_manifest(repo2, "ev-pf-man")
    sha2 = base._full_batch(
        stack2, "acq-pf-man", "pm-pf-man", b'{"rows": ["pfm"]}'
    )
    repo2.advance_checkpoint(
        "ev-pf-man",
        resume_token=token,
        acquisition_id="acq-pf-man",
        manifest_id="pm-pf-man",
    )
    laxer = JobStack(
        tmp / "pfman",
        clock=shared2,
        min_durable_status=StorageJobStatus.RAW_COMMITTED,
    ).repo
    man_result = "FAIL"
    kept_manifest: Any = "UNSET"
    man_gate_count = -1
    proven_floor = "UNSET"
    try:
        retried2 = laxer.advance_checkpoint(
            "ev-pf-man",
            resume_token=token,
            acquisition_id="acq-pf-man",
            manifest_id="pm-pf-man",
        )
        kept_manifest = retried2.last_manifest_id
        man_gate_count = len(_gate_events(laxer, "ev-pf-man"))
        proof = laxer._latest_event("ev-pf-man")["checkpoint_proof"]  # noqa: SLF001
        proven_floor = proof["minimum_durable_status"]
        man_result = (
            "PASS"
            if retried2.status is StorageJobStatus.CHECKPOINT_ADVANCED
            and kept_manifest == "pm-pf-man"
            and retried2.last_committed_blob_sha256 == sha2
            and man_gate_count == 1
            and proven_floor == StorageJobStatus.MANIFEST_COMMITTED.value
            else "FAIL"
        )
    except Exception:  # noqa: BLE001 — recorded as FAIL below
        pass
    cases.append(
        _case(
            "manifest_persisted_raw_constructor_retry",
            persisted_floor="MANIFEST_COMMITTED",
            constructor_floor="RAW_COMMITTED",
            adopted_manifest_id=kept_manifest,
            persisted_proof_floor=proven_floor,
            gate_event_count=man_gate_count,
            result=man_result,
        )
    )

    # new_raw_uses_current_floor (§7/§12): RAW constructor -> manifest_id
    # must be None; a supplied anchor is contradictory input.
    stack3 = JobStack(
        tmp / "newraw", min_durable_status=StorageJobStatus.RAW_COMMITTED
    )
    repo3 = stack3.repo
    base._create(repo3, "ev-new-raw")
    base._drive_to_manifest(repo3, "ev-new-raw")
    base._full_batch(
        stack3, "acq-new-raw", "pm-new-raw", b'{"rows": ["nr"]}'
    )
    contradictory_rejected = "FAIL"
    try:
        repo3.advance_checkpoint(
            "ev-new-raw",
            resume_token=token,
            acquisition_id="acq-new-raw",
            manifest_id="pm-new-raw",
        )
    except Exception:  # noqa: BLE001 — the expected refusal
        contradictory_rejected = "PASS"
    new_raw_state = repo3.advance_checkpoint(
        "ev-new-raw", resume_token=token, acquisition_id="acq-new-raw"
    )
    cases.append(
        _case(
            "new_raw_uses_current_floor",
            constructor_floor="RAW_COMMITTED",
            stored_manifest_id=new_raw_state.last_manifest_id,
            contradictory_anchor_rejected=contradictory_rejected,
            result=(
                "PASS"
                if new_raw_state.last_manifest_id is None
                and contradictory_rejected == "PASS"
                else "FAIL"
            ),
        )
    )

    # new_manifest_uses_current_floor (§7/§13): MANIFEST constructor requires
    # the exact durable manifest.
    stack4 = JobStack(
        tmp / "newman", min_durable_status=StorageJobStatus.MANIFEST_COMMITTED
    )
    repo4 = stack4.repo
    base._create(repo4, "ev-new-man")
    base._drive_to_manifest(repo4, "ev-new-man")
    base._full_batch(
        stack4, "acq-new-man", "pm-new-man", b'{"rows": ["nm"]}'
    )
    missing_rejected = "FAIL"
    try:
        repo4.advance_checkpoint(
            "ev-new-man", resume_token=token, acquisition_id="acq-new-man"
        )
    except Exception:  # noqa: BLE001 — the expected refusal
        missing_rejected = "PASS"
    new_man_state = repo4.advance_checkpoint(
        "ev-new-man",
        resume_token=token,
        acquisition_id="acq-new-man",
        manifest_id="pm-new-man",
    )
    cases.append(
        _case(
            "new_manifest_uses_current_floor",
            constructor_floor="MANIFEST_COMMITTED",
            stored_manifest_id=new_man_state.last_manifest_id,
            missing_manifest_rejected=missing_rejected,
            result=(
                "PASS"
                if new_man_state.last_manifest_id == "pm-new-man"
                and missing_rejected == "PASS"
                else "FAIL"
            ),
        )
    )

    # divergent_historical_retry_rejected (§8): persisted-floor support is
    # not overwrite permission.
    shared3 = base.TickingClock()
    stack5 = JobStack(
        tmp / "pfdiv",
        clock=shared3,
        min_durable_status=StorageJobStatus.RAW_COMMITTED,
    )
    repo5 = stack5.repo
    base._create(repo5, "ev-pf-div")
    base._drive_to_manifest(repo5, "ev-pf-div")
    base._full_batch(stack5, "acq-pf-div", "pm-pf-div", b'{"rows": ["pd"]}')
    repo5.advance_checkpoint(
        "ev-pf-div", resume_token=token, acquisition_id="acq-pf-div"
    )
    stricter5 = JobStack(
        tmp / "pfdiv",
        clock=shared3,
        min_durable_status=StorageJobStatus.MANIFEST_COMMITTED,
    ).repo
    from crypto_sensor_fabric.providers.base.models import ResumeToken

    divergent_outcomes = []
    for kwargs in (
        {
            "resume_token": ResumeToken(
                mode="PAGE", provider_cursor="c", page_number=7
            ),
            "acquisition_id": "acq-pf-div",
        },
        {"resume_token": token, "acquisition_id": "acq-other"},
        {"resume_token": token, "acquisition_id": "acq-pf-div",
         "manifest_id": "pm-other"},
    ):
        divergent_outcomes.append(
            _expect_conflict(stricter5, "ev-pf-div", kwargs)
        )
    chain_length = len(stricter5.list_transitions("ev-pf-div"))
    cases.append(
        _case(
            "divergent_historical_retry_rejected",
            divergent_variants=3,
            rejected_variants=sum(
                1 for outcome in divergent_outcomes if outcome == "PASS"
            ),
            chain_events=chain_length,
            result=(
                "PASS"
                if all(outcome == "PASS" for outcome in divergent_outcomes)
                and chain_length == len(repo5.list_transitions("ev-pf-div"))
                else "FAIL"
            ),
        )
    )

    return {
        "matrix": "BLOC_04_I07R1F_PERSISTED_FLOOR_MATRIX",
        "checkpoint": "SENSOR-B4-I07R1F",
        "doctrine": (
            "I07R1F \u00a73-\u00a78 \u2014 constructor config governs NEW "
            "checkpoints; persisted proof governs durable history"
        ),
        "cases": cases,
    }


def _expect_conflict(repo, job_id: str, kwargs: dict) -> str:
    from crypto_sensor_fabric.storage.jobs import JobTransitionConflict

    try:
        repo.advance_checkpoint(job_id, **kwargs)
    except JobTransitionConflict:
        return "PASS"
    except Exception:  # noqa: BLE001 — any other outcome is not the typed refusal
        return "FAIL"
    return "FAIL"


# ---------------------------------------------------------------------------
# Matrix 2 — shared durable-catalog cache concurrency (I07R1F §9-§14)
# ---------------------------------------------------------------------------


def build_catalog_concurrency_matrix(tmp: Path) -> dict:
    """One catalog cache, several job locks: no false corruption, no fork."""
    from crypto_sensor_fabric.storage.enums import StorageJobStatus
    from crypto_sensor_fabric.storage.json_catalog import (
        DurableJsonCatalog,
        JsonCatalogCorrupt,
    )

    base = _load_base()
    r1f = load_sibling("_i07r1f_mod", "test_job_state_r1f")
    JobStack = base.JobStack
    token = _resume_token()
    cases: list[dict] = []

    # refresh_commit_same_catalog (§11): the refreshing thread pauses after
    # its file listing, so the concurrent commit provably lands inside its
    # scan/compare window.
    race_root = tmp / "race"
    catalog = DurableJsonCatalog(race_root / "cat", logical_id_field="logical_id")
    catalog.commit("id-seed", {"logical_id": "id-seed"})
    real_parse = catalog._parse_fragment  # noqa: SLF001
    slow_name = "ev-r1f-race-refresh"

    def _pausing_parse(path: Path) -> Any:
        parsed = real_parse(path)
        if threading.current_thread().name == slow_name:
            time.sleep(0.05)
        return parsed

    catalog._parse_fragment = _pausing_parse  # type: ignore[method-assign]  # noqa: SLF001
    race_errors: list[BaseException] = []
    new_id = "id-race-new"

    def _refresh() -> None:
        try:
            catalog.refresh()
        except BaseException as exc:  # noqa: BLE001 — recorded for the case
            race_errors.append(exc)

    def _commit() -> None:
        try:
            catalog.commit(new_id, {"logical_id": new_id})
        except BaseException as exc:  # noqa: BLE001 — recorded for the case
            race_errors.append(exc)

    refresher = threading.Thread(target=_refresh, name=slow_name)
    committer = threading.Thread(target=_commit, name="ev-r1f-race-commit")
    refresher.start()
    committer.start()
    refresher.join(timeout=30)
    committer.join(timeout=30)
    catalog._parse_fragment = real_parse  # type: ignore[method-assign]  # noqa: SLF001
    on_disk_ids = {
        json.loads(path.read_text(encoding="utf-8"))["logical_id"]
        for path in (race_root / "cat").glob("*.json")
    }
    cases.append(
        _case(
            "refresh_commit_same_catalog",
            false_corruption_errors=len(race_errors),
            new_record_visible=catalog.get(new_id) is not None,
            cache_matches_disk=on_disk_ids == set(catalog.list_ids()),
            result=(
                "PASS"
                if not race_errors
                and catalog.get(new_id) is not None
                and on_disk_ids == set(catalog.list_ids())
                else "FAIL"
            ),
        )
    )

    # different_jobs_same_repository (§12): both chains commit concurrently
    # on ONE repository, with the slow thread's listing predating the fast
    # thread's commit.
    clock = r1f.LockedClock()
    stack = JobStack(tmp / "twojob", clock=clock)
    repo = stack.repo
    tags = ("a", "b")
    for tag in tags:
        base._create(repo, f"ev-cc-{tag}")
        base._drive_to_manifest(repo, f"ev-cc-{tag}")
        base._full_batch(
            stack,
            f"acq-cc-{tag}",
            f"pm-cc-{tag}",
            f'{{"rows": ["cc-{tag}"]}}'.encode("utf-8"),
        )
    slow_cc = "ev-r1f-cc-slow"
    listed = threading.Event()
    real_events_parse = repo._events._parse_fragment  # noqa: SLF001

    def _pausing_events_parse(path: Path) -> Any:
        parsed = real_events_parse(path)
        if threading.current_thread().name == slow_cc:
            listed.set()
            time.sleep(0.05)
        return parsed

    repo._events._parse_fragment = _pausing_events_parse  # type: ignore[method-assign]  # noqa: SLF001
    cc_results: dict[str, Any] = {}
    cc_errors: list[BaseException] = []

    def _run(tag: str) -> None:
        try:
            if tag != "b":
                assert listed.wait(timeout=30)
            cc_results[tag] = repo.advance_checkpoint(
                f"ev-cc-{tag}",
                resume_token=token,
                acquisition_id=f"acq-cc-{tag}",
                manifest_id=f"pm-cc-{tag}",
            )
        except BaseException as exc:  # noqa: BLE001 — recorded for the case
            cc_errors.append(exc)

    threads = [
        threading.Thread(target=_run, args=(tag,), name=name)
        for tag, name in (("a", "ev-r1f-cc-fast"), ("b", slow_cc))
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    repo._events._parse_fragment = real_events_parse  # type: ignore[method-assign]  # noqa: SLF001
    fresh = JobStack(tmp / "twojob", clock=clock).repo
    gate_counts = [len(_gate_events(fresh, f"ev-cc-{tag}")) for tag in tags]
    rebuilt = all(
        fresh.get_job(f"ev-cc-{tag}").last_committed_acquisition_id
        == f"acq-cc-{tag}"
        for tag in tags
    )
    cases.append(
        _case(
            "different_jobs_same_repository",
            concurrent_errors=len(cc_errors),
            committed_chains=len(cc_results),
            gate_events_per_chain=gate_counts,
            restart_reconstructs_both=rebuilt,
            result=(
                "PASS"
                if not cc_errors
                and len(cc_results) == 2
                and gate_counts == [1, 1]
                and rebuilt
                and all(
                    cc_results[tag].status
                    is StorageJobStatus.CHECKPOINT_ADVANCED
                    for tag in tags
                )
                else "FAIL"
            ),
        )
    )

    # refresh_vanished_fail_closed (§13).
    vanish_catalog = DurableJsonCatalog(
        tmp / "vanish" / "cat", logical_id_field="logical_id"
    )
    vanish_catalog.commit("id-vanish", {"logical_id": "id-vanish"})
    (
        tmp
        / "vanish"
        / "cat"
        / f"{hashlib.sha256(b'id-vanish').hexdigest()}.json"
    ).unlink()
    vanished = "FAIL"
    try:
        vanish_catalog.refresh()
    except JsonCatalogCorrupt:
        vanished = "PASS"
    except Exception:  # noqa: BLE001 — only the typed corruption counts
        pass
    cases.append(_case("refresh_vanished_fail_closed", result=vanished))

    # refresh_divergence_fail_closed (§13).
    diverge_catalog = DurableJsonCatalog(
        tmp / "diverge" / "cat", logical_id_field="logical_id"
    )
    diverge_catalog.commit(
        "id-diverge", {"logical_id": "id-diverge", "rows": [1]}
    )
    (
        tmp
        / "diverge"
        / "cat"
        / f"{hashlib.sha256(b'id-diverge').hexdigest()}.json"
    ).write_text(
        json.dumps({"logical_id": "id-diverge", "rows": [2]}), encoding="utf-8"
    )
    diverged = "FAIL"
    try:
        diverge_catalog.refresh()
    except JsonCatalogCorrupt:
        diverged = "PASS"
    except Exception:  # noqa: BLE001 — only the typed corruption counts
        pass
    cases.append(_case("refresh_divergence_fail_closed", result=diverged))

    # cross_repo_refresh_regression (§14): in-process cache safety must not
    # change cross-repository truth.
    clock_x = r1f.LockedClock()
    stack_x = JobStack(tmp / "xrepo", clock=clock_x)
    repo_a = stack_x.repo
    repo_b = type(repo_a)(
        tmp / "xrepo" / "catalogs" / "jobs_state",
        acquisitions=stack_x.acq_repo,
        manifests=stack_x.manifest_repo,
        blob_metadata_repository=stack_x.blob_repo,
        clock=clock_x,
    )
    base._create(repo_a, "ev-xr")
    repo_b.advance_status("ev-xr", to_status=StorageJobStatus.ACQUIRING)
    repo_a.advance_status("ev-xr", to_status=StorageJobStatus.RAW_STAGED)
    state_x = repo_b.advance_status(
        "ev-xr",
        to_status=StorageJobStatus.RAW_COMMITTED,
        expected_from=StorageJobStatus.RAW_STAGED,
    )
    chain_x = [t.to_status.value for t in repo_b.list_transitions("ev-xr")]
    cases.append(
        _case(
            "cross_repo_refresh_regression",
            observed_chain=chain_x,
            result=(
                "PASS"
                if state_x.status is StorageJobStatus.RAW_COMMITTED
                and chain_x == ["ACQUIRING", "RAW_STAGED", "RAW_COMMITTED"]
                else "FAIL"
            ),
        )
    )

    return {
        "matrix": "BLOC_04_I07R1F_CATALOG_CONCURRENCY_MATRIX",
        "checkpoint": "SENSOR-B4-I07R1F",
        "doctrine": (
            "I07R1F \u00a79-\u00a714 \u2014 a shared catalog cache is "
            "internally synchronized; durable truth stays fail-closed"
        ),
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Read-only comparison tests (I05R4 evidence policy, I07R1F §18)
# ---------------------------------------------------------------------------


BUILDERS = [
    (
        "build_persisted_floor_matrix",
        "BLOC_04_I07R1F_PERSISTED_FLOOR_MATRIX.json",
    ),
    (
        "build_catalog_concurrency_matrix",
        "BLOC_04_I07R1F_CATALOG_CONCURRENCY_MATRIX.json",
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
    evidence tree (read-only policy, I07R1F §18)."""
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
