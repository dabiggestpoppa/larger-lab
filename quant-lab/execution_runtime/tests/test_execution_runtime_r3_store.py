"""QL-EXEC-R3 — runtime store tests (startup/store matrix).

Covers: create store, WAL, schema/version/runtime_id/generation/profile-hash
recording, reopen, incompatible profile hash -> BLOCK, invalid schema -> FAIL.
"""
from __future__ import annotations

from execution_runtime.hashing import config_hash
from execution_runtime.runtime import RUNTIME_SCHEMA_VERSION, RuntimeStore
from execution_runtime.runtime.engine import GenericRuntime
from execution_runtime.runtime.state import RuntimeState

from r3_harness import make_account, make_profile, make_store


def test_01_create_new_runtime_store(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    assert store.connected
    assert store.integrity_check() == []


def test_02_wal_enabled(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    assert store.wal_mode.lower() == "wal"


def test_03_schema_version_recorded(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    assert store.schema_version() == RUNTIME_SCHEMA_VERSION


def test_04_runtime_id_recorded(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    assert store.meta("runtime_id") == profile.runtime_id


def test_05_generation_recorded(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    assert store.meta("deployment_generation") == profile.deployment_generation


def test_06_profile_hash_recorded(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    assert store.meta("profile_hash") == config_hash(profile)
    assert store.meta("account_hash") == config_hash(account)


def test_07_reopen_same_store(tmp_path):
    profile = make_profile()
    account = make_account()
    db = tmp_path / "runtime.sqlite"
    s1 = RuntimeStore(str(db))
    s1.open()
    s1.initialize(
        runtime_id=profile.runtime_id,
        deployment_generation=profile.deployment_generation,
        profile_hash=config_hash(profile),
        account_hash=config_hash(account),
    )
    s1.close()
    s2 = RuntimeStore(str(db))
    s2.open()
    assert s2.schema_version() == RUNTIME_SCHEMA_VERSION
    assert s2.meta("runtime_id") == profile.runtime_id
    assert s2.startup_check(
        runtime_id=profile.runtime_id,
        deployment_generation=profile.deployment_generation,
        profile_hash=config_hash(profile),
        account_hash=config_hash(account),
    ) == []


def test_08_incompatible_profile_hash_blocks(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    other = make_profile(runtime_id="rt-1", account_id="acct-1", metadata_version=2)
    blockers = store.startup_check(
        runtime_id="rt-1",
        deployment_generation=profile.deployment_generation,
        profile_hash=config_hash(other),
        account_hash=config_hash(account),
    )
    assert any("CONFIG_DRIFT" in b or "profile hash" in b for b in blockers)


def test_09_invalid_schema_blocks(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    store.meta  # noqa: B018 - ensure loaded
    # Corrupt the recorded schema version.
    cur = store._conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO runtime_meta(key, value) VALUES('schema_version','999')"
    )
    store._conn.commit()
    blockers = store.startup_check(
        runtime_id=profile.runtime_id,
        deployment_generation=profile.deployment_generation,
        profile_hash=config_hash(profile),
        account_hash=config_hash(account),
    )
    assert any("SCHEMA_VERSION_MISMATCH" in b for b in blockers)


def test_generation_drift_detected(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    blockers = store.startup_check(
        runtime_id=profile.runtime_id,
        deployment_generation="gen-2",
        profile_hash=config_hash(profile),
        account_hash=config_hash(account),
    )
    assert any("GENERATION_DRIFT" in b for b in blockers)


def test_append_only_journal_dedup(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    first = store.append_event("EVENT_OBSERVED", dedup_key="k1", payload={"x": 1})
    second = store.append_event("EVENT_OBSERVED", dedup_key="k1", payload={"x": 1})
    assert first == second  # idempotent
    assert store._conn.execute(
        "SELECT COUNT(*) AS n FROM runtime_events WHERE dedup_key='k1'"
    ).fetchone()["n"] == 1
