#!/usr/bin/env python3
"""B4-CXR7U9R39-R4 — transition closure against the REAL stack. CONTAINER-BACKED
(mandatory in CI).

The transition law is proven deterministically in-process
(test_b4_cxr7u9r39r3_transition_authority.py). This module proves the same
one-time authority when the engine runs as real CLI processes against a real
PostgreSQL container: a genuine promote, a genuine finalize, and then a
REPLAYED finalize of the same receipt, which must be refused before any docker
or catalog call and must leave the committed truth untouched.
"""
import hashlib
import json

import pytest

import oce_compose as oc
import recovery_cli

pytestmark = pytest.mark.container


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _pg_truth():
    r = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-tAc",
                               "SELECT k || '=' || v FROM backup_probe ORDER BY k;"])
    return _sha("\n".join(line.strip() for line in r.stdout.splitlines() if line.strip()))


def _env(tmp_path):
    return {"OCE_BACKUP_ROOTS": str(tmp_path),
            "OCE_COMMIT": "a" * 40, "OCE_TREE": "b" * 40,
            "OCE_RUN_ID": "0123456789abcdef"}


def test_finalize_replay_against_the_real_stack_is_denied(oce_stack, tmp_path):
    oc.assert_stack_converged(timeout_s=180, stable=2)
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "CREATE TABLE IF NOT EXISTS backup_probe"
                           "(k text PRIMARY KEY, v text);"
                           "INSERT INTO backup_probe VALUES('b1','alpha'),('b2','beta') "
                           "ON CONFLICT (k) DO UPDATE SET v=EXCLUDED.v;"])
    bk = tmp_path / "bk"
    oc.run(["bash", str(oc.SCRIPTS / "backup.sh"), "--scope", "full",
            "--out", str(bk)], check=True)
    content = bk / ".backup-content" / "postgres"
    inv, invsha = content / "inventory.json", content / "inventory.json.sha256"
    dump = content / "archive.dump"
    # the write root is the seam the TEST constructs (never an environment
    # channel); the receipts themselves are the engine's own, and every
    # --receipt-out lives INSIDE that governed root (the R2 write boundary)
    root = tmp_path / "recovery"
    (root / "transitions").mkdir(parents=True)
    common = ["--inventory", str(inv), "--inventory-sha", str(invsha)]
    promote_receipt = root / "promote.json"
    finalize_receipt = root / "finalize.json"
    replay_receipt = root / "replay.json"

    promoted = recovery_cli.run_cli(
        ["--phase", "promote", "--archive", str(dump)] + common
        + ["--receipt-out", str(promote_receipt)],
        write_root=root, env_extra=_env(tmp_path), timeout=900)
    assert promoted.returncode == 0, promoted.stdout + promoted.stderr
    pr = json.loads(promote_receipt.read_text(encoding="utf-8"))
    assert pr["promoted"] is True and pr["quarantine_held"] is True, pr
    quarantine = pr["quarantine_database"]

    first = recovery_cli.run_cli(
        ["--phase", "finalize", "--receipt-in", str(promote_receipt)] + common
        + ["--receipt-out", str(finalize_receipt)],
        write_root=root, env_extra=_env(tmp_path), timeout=900)
    assert first.returncode == 0, first.stdout + first.stderr
    fr = json.loads(finalize_receipt.read_text(encoding="utf-8"))
    assert fr["quarantine_dropped"] is True, fr
    committed = _pg_truth()
    names = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", "postgres", "-tAc",
                                   "SELECT datname FROM pg_database;"]).stdout
    assert quarantine not in names, "the quarantine survived finalize"

    # REPLAY: the same receipt is presented again - it is spent authority
    replay = recovery_cli.run_cli(
        ["--phase", "finalize", "--receipt-in", str(promote_receipt)] + common
        + ["--receipt-out", str(replay_receipt)],
        write_root=root, env_extra=_env(tmp_path), timeout=900)
    assert replay.returncode != 0, replay.stdout + replay.stderr
    rf = json.loads(replay_receipt.read_text(encoding="utf-8"))
    assert rf["exit_status"] == 1, rf
    assert "refusing recovery transition authority" in rf["error"], rf
    assert "no longer available" in rf["error"], rf
    # nothing durable moved: the committed truth is byte-identical
    assert _pg_truth() == committed, "a replayed finalize mutated database truth"
    assert quarantine not in oc.dexec(
        oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", "postgres", "-tAc",
                      "SELECT datname FROM pg_database;"]).stdout
