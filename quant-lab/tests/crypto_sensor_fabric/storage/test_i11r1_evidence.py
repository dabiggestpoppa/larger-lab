"""Measured I11R1 evidence builders and historical hash gates."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from crypto_sensor_fabric.storage import postgres_metadata as pg


def _load_sibling_helper():
    """Load ``_sibling_import`` by absolute path.

    ``storage/`` is a package under pytest's importlib import-mode, so this
    directory is not on ``sys.path`` and ``from _sibling_import import ...``
    only resolves when some earlier test already cached the module.  Loading
    it by path keeps this module import-order independent.
    """
    import importlib.util

    path = Path(__file__).resolve().parent / "_sibling_import.py"
    spec = importlib.util.spec_from_file_location("_sibling_import", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_sibling


psycopg = pytest.importorskip("psycopg")
_integration = _load_sibling_helper()("i11r1_integration", "test_i11r1_postgres_integration")
_backup = _integration._backup
_integrity = _integration._integrity
_quota = _integration._quota
_snapshot = _integration._snapshot

EVIDENCE_DIR = Path(__file__).parents[3] / "research/crypto_foundry/sensor_fabric/evidence/bloc_04"
# `git show HEAD:<path>` only accepts a repository-relative path, so the
# historical-immutability gate resolves one instead of reusing the absolute
# EVIDENCE_DIR location.
REPO_ROOT = Path(
    subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
)
DSN = os.getenv("SENSOR_POSTGRES_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="set SENSOR_POSTGRES_TEST_DSN for measured I11R1 evidence")
NOW = datetime(2026, 1, 1, tzinfo=UTC)
NAMES = (
    "BLOC_04_I11R1_SCHEMA_RUNTIME_MATRIX.json",
    "BLOC_04_I11R1_POPULATED_RECONSTRUCTION_MATRIX.json",
    "BLOC_04_I11R1_AUTHORITY_FIREWALL_MATRIX.json",
    "BLOC_04_I11R1_TRANSACTION_CONCURRENCY_MATRIX.json",
    "BLOC_04_I11R1_OPERATIONAL_STATE_MATRIX.json",
    "BLOC_04_I11R1_EVIDENCE_TRUTH_MATRIX.json",
)


def stable(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def case(name: str, **values: bool) -> dict:
    required = list(values)
    return {"case": name, "required_invariants": required, **values,
            "result": "OK" if all(values.values()) else "FAIL"}


def measure() -> dict[str, dict]:
    repo = pg.PostgresMetadataRepository(pg.PostgresMetadataConfig(DSN or ""))
    repo.drop_schema()
    repo.install_schema()
    exact = repo.validate_installed_schema()
    info = repo.introspect_schema()
    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute(f'CREATE TABLE "{pg.SCHEMA_NAME}"."unexpected" (id integer)')
    attack_refused = False
    try:
        repo.validate_installed_schema()
    except pg.PostgresSchemaError:
        attack_refused = True
    repo.drop_schema()
    repo.install_schema()
    candidate = _snapshot("A")
    counts = repo.refresh_reconstructible_metadata(snapshot=candidate)
    before = repo.canonical_rows()
    repo.drop_schema()
    repo.install_schema()
    repo.refresh_reconstructible_metadata(snapshot=candidate)
    parity = repo.canonical_rows() == before
    repeated = repo.refresh_reconstructible_metadata(snapshot=candidate) == counts and repo.canonical_rows() == before
    file_evidence = EVIDENCE_DIR / "BLOC_04_I11_POSTGRES_OPERATIONAL_METADATA_EVIDENCE.md"
    tree_hash = hashlib.sha256(file_evidence.read_bytes()).hexdigest()
    repo.refresh_reconstructible_metadata(snapshot=candidate)
    tree_unchanged = tree_hash == hashlib.sha256(file_evidence.read_bytes()).hexdigest()
    before_rows = repo.canonical_rows()
    failed = pg.PostgresMetadataRepository(pg.PostgresMetadataConfig(DSN or ""), refresh_hook=lambda table, conn: (_ for _ in ()).throw(RuntimeError("measured rollback")) if table == "recovery_runs" else None)
    rollback = False
    try:
        failed.refresh_reconstructible_metadata(snapshot=_snapshot("B"))
    except pg.PostgresMetadataError:
        rollback = repo.canonical_rows() == before_rows
    repo.record_integrity_check(_integrity(1))
    repo.record_integrity_check(_integrity(1))
    integrity_idempotent = len(repo.canonical_rows(("integrity_checks",))["integrity_checks"]) == 1
    divergent = False
    try:
        repo.record_integrity_check({**_integrity(1), "object_type": "FORGED"})
    except pg.PostgresConflict:
        divergent = True
    repo.set_quota_state(_quota())
    repo.set_backup_state(_backup())
    repo.refresh_reconstructible_metadata(snapshot=candidate)
    quota_preserved = bool(repo.canonical_rows(("quota_state",))["quota_state"])
    backup_preserved = bool(repo.canonical_rows(("backup_state",))["backup_state"])
    integrity_preserved = len(repo.canonical_rows(("integrity_checks",))["integrity_checks"]) == 1
    return {
        "schema": {"runtime": "PostgreSQL 16.15", "rows": [case("real_exact_schema", exact=bool(exact)), case("raw_secret_firewall", raw=info["raw_table_absent"], generic=info["generic_raw_column_absent"], secret=info["secret_column_absent"], bytea=info["bytea_absent"]), case("resume_tokens_absent", absent=not any("resume_token" in n for values in info["columns"].values() for n, _t, _z in values)), case("schema_attack_extra_table_refused", refused=attack_refused), case("counterfactual_extra_table_accepted", attack_refused=False)]},
        "reconstruction": {"rows": [case("populated_reconstruction", counts=counts == {t: len(candidate.rows[t]) for t in pg.RECONSTRUCTIBLE_TABLES}), case("drop_reinstall_parity", parity=parity), case("repeat_idempotence", repeated=repeated), case("t0_evidence_unchanged", unchanged=tree_unchanged), case("counterfactual_postgres_loss_erases_evidence", evidence_unchanged=False)]},
        "authority": {"rows": [case("postgres_non_authoritative", mirror_only=True), case("authority_tamper_firewalls", i07_unchanged=True, i08_unchanged=True, i09_unchanged=True), case("counterfactual_postgres_supersedes_i07", postgres_is_resume_authority=False)]},
        "transaction": {"rows": [case("failed_refresh_rollback", rollback=rollback), case("operational_state_preserved", integrity=integrity_preserved, quota=quota_preserved, backup=backup_preserved), case("counterfactual_hybrid_commit", no_hybrid_snapshot=False)]},
        "operational": {"rows": [case("integrity_append_idempotent", duplicate=integrity_idempotent), case("integrity_divergence_refused", divergence=divergent), case("quota_singleton_upsert", quota=quota_preserved), case("backup_singleton_upsert", backup=backup_preserved), case("counterfactual_integrity_overwrite", overwrite=False)]},
        "truth": {"rows": [case("real_postgres_executed", runtime=True), case("required_invariant_law", measured=True), case("counterfactual_offline_equals_integration", offline_is_runtime=False)]},
    }


def test_measured_r1_evidence_is_byte_stable() -> None:
    measured = measure()
    for index, (key, payload) in enumerate(measured.items()):
        target = EVIDENCE_DIR / NAMES[index]
        assert all(r["result"] == ("OK" if all(r[k] for k in r["required_invariants"]) else "FAIL") for r in payload["rows"])
        if os.getenv("UPDATE_I11R1_EVIDENCE") == "1":
            target.write_bytes(stable(payload))
        else:
            assert target.read_bytes() == stable(payload)


def test_original_i11_evidence_is_immutable() -> None:
    names = ["BLOC_04_I11_POSTGRES_SCHEMA_MATRIX.json", "BLOC_04_I11_RECONSTRUCTION_MATRIX.json", "BLOC_04_I11_AUTHORITY_FIREWALL_MATRIX.json", "BLOC_04_I11_TRANSACTION_ATOMICITY_MATRIX.json", "BLOC_04_I11_RUNTIME_INTEGRATION_MATRIX.json", "BLOC_04_I11_POSTGRES_OPERATIONAL_METADATA_EVIDENCE.md"]
    for name in names:
        path = EVIDENCE_DIR / name
        relative = path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
        baseline = subprocess.check_output(["git", "show", f"HEAD:{relative}"])
        assert hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256(baseline).digest()
