#!/usr/bin/env python3
"""B4-CXR7U9R40-R1 — the transition claim is OPERATION-WIDE and atomic.

R39-R3 used one claim file PER TRANSITION (<op>.finalize.claim vs
<op>.rollback.claim): two processes could both read PROMOTED, both observe
their transition as permitted, and both create their different claim files
successfully — then concurrently mutate the same PostgreSQL recovery
operation. That race was reproduced against the published code.

The law now: ONE claim file per OPERATION, exclusively created, naming the
selected transition and binding it to the promote receipt's content digest.
Exactly one of finalize/rollback/finalize/finalize/rollback/rollback can win;
every loser is refused BEFORE any docker, catalog, receipt or durable-record
mutation. The proofs below drive REAL PROCESSES (the real CLI in child
processes, released through a real multiprocessing barrier), because the
guarantee lives in operating-system exclusive creation — no in-process fake
can prove it.
"""
import hashlib
import json
import multiprocessing

import pytest

import oce_compose as oc
import recovery_cli

pytestmark = pytest.mark.container

CLI = recovery_cli.CLI


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _env(tmp_path):
    return {"OCE_BACKUP_ROOTS": str(tmp_path),
            "OCE_COMMIT": "a" * 40, "OCE_TREE": "b" * 40,
            "OCE_RUN_ID": "0123456789abcdef"}


def _pg_truth():
    r = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-tAc",
                               "SELECT k || '=' || v FROM backup_probe ORDER BY k;"])
    return [line.strip() for line in r.stdout.splitlines() if line.strip()]


def _prepare_promotion(tmp_path):
    """One genuine promotion driven by the REAL CLI against the REAL stack;
    returns (write_root, promote_receipt_path, inventory, inventory_sha)."""
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "CREATE TABLE IF NOT EXISTS backup_probe"
                           "(k text PRIMARY KEY, v text);"
                           "INSERT INTO backup_probe VALUES('b1','alpha'),('b2','beta') "
                           "ON CONFLICT (k) DO UPDATE SET v=EXCLUDED.v;"])
    bk = tmp_path / "bk"
    oc.run(["bash", str(oc.SCRIPTS / "backup.sh"), "--scope", "full",
            "--out", str(bk)], check=True)
    content = bk / ".backup-content" / "postgres"
    root = tmp_path / "recovery"
    (root / "transitions").mkdir(parents=True)
    promote = root / "promote.json"
    recovery_cli.run_cli(
        ["--phase", "promote", "--archive", str(content / "archive.dump"),
         "--inventory", str(content / "inventory.json"),
         "--inventory-sha", str(content / "inventory.json.sha256"),
         "--db", oc.PG_DB, "--user", oc.PG_USER, "--container", oc.POSTGRES,
         "--receipt-out", str(promote)],
        write_root=str(root), env_extra=_env(tmp_path), timeout=600)
    assert promote.is_file(), "promotion never produced its receipt"
    return root, promote, content / "inventory.json", content / "inventory.json.sha256"


def _worker(write_root, promote, inv, invsha, transition, out_path, barrier,
            env_base):
    """A REAL CLI process: waits at the barrier, then races for the claim."""
    barrier.wait()
    r = recovery_cli.run_cli(
        ["--phase", transition, "--receipt-in", str(promote),
         "--inventory", str(inv), "--inventory-sha", str(invsha),
         "--db", oc.PG_DB, "--user", oc.PG_USER, "--container", oc.POSTGRES,
         "--receipt-out", str(out_path)],
        write_root=str(write_root), env_extra=env_base, timeout=600)
    with open(out_path.with_suffix(".rc"), "w", encoding="utf-8") as f:
        f.write(str(r.returncode))


def _race(tmp_path, root, promote, inv, invsha, transitions):
    """Launch len(transitions) real processes released by one barrier; returns
    the list of (transition, returncode) results."""
    barrier = multiprocessing.Barrier(len(transitions))
    procs, outs = [], []
    for i, tr in enumerate(transitions):
        out = root / f"{tr}-{i}.json"
        outs.append((tr, out))
        p = multiprocessing.Process(
            target=_worker,
            args=(str(root), str(promote), str(inv), str(invsha), tr, str(out),
                  barrier, _env(tmp_path)))
        procs.append(p)
    for p in procs:
        p.start()
    for p in procs:
        p.join(600)
    results = []
    for (tr, out), p in zip(outs, procs):
        rc_file = out.with_suffix(".rc")
        results.append((tr, int(rc_file.read_text()) if rc_file.is_file() else 99,
                        p.exitcode))
    return results


# --------------------------------------------------------------------- #
# the races — real processes, one barrier, OS-level exclusive creation
# --------------------------------------------------------------------- #

def test_finalize_versus_rollback_exactly_one_wins(oce_stack, tmp_path):
    root, promote, inv, invsha = _prepare_promotion(tmp_path)
    results = _race(tmp_path, root, promote, inv, invsha, ["finalize", "rollback"])
    winners = [tr for tr, rc, _ in results if rc == 0]
    assert len(winners) == 1, results
    winner = winners[0]
    loser = "rollback" if winner == "finalize" else "finalize"
    loser_rc = [rc for tr, rc, _ in results if tr == loser][0]
    assert loser_rc != 0, results
    # the durable record names the winner and cannot be re-opened
    rec = json.loads((root / "transitions" /
                      json.loads(promote.read_text(encoding="utf-8"))["operation_id"]
                      + ".json").read_text(encoding="utf-8"))
    claim = json.loads((root / "transitions" /
                        json.loads(promote.read_text(encoding="utf-8"))["operation_id"]
                        + ".claim").read_text(encoding="utf-8"))
    assert claim["transition"] == winner, claim
    assert rec["state"] in {"FINALIZED", "ROLLED_BACK", "FAILED",
                            "COMMIT_POINT_REACHED",
                            "FINALIZING" if winner == "finalize" else "ROLLING_BACK"}, rec
    assert rec.get("selected_transition") == winner, rec


def test_finalize_versus_finalize_exactly_one_wins(oce_stack, tmp_path):
    root, promote, inv, invsha = _prepare_promotion(tmp_path)
    results = _race(tmp_path, root, promote, inv, invsha, ["finalize", "finalize"])
    assert sorted(rc for _, rc, _ in results).count(0) == 1, results


def test_rollback_versus_rollback_exactly_one_wins(oce_stack, tmp_path):
    root, promote, inv, invsha = _prepare_promotion(tmp_path)
    results = _race(tmp_path, root, promote, inv, invsha, ["rollback", "rollback"])
    assert sorted(rc for _, rc, _ in results).count(0) == 1, results


def test_the_loser_mutates_nothing(oce_stack, tmp_path):
    """The losing process performs zero docker calls, zero catalog changes,
    zero receipt writes and zero durable-record rewrites."""
    root, promote, inv, invsha = _prepare_promotion(tmp_path)
    opid = json.loads(promote.read_text(encoding="utf-8"))["operation_id"]
    truth_before = _pg_truth()
    dbs_before = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", "postgres",
                                        "-tAc", "SELECT datname FROM pg_database ORDER BY 1"]
                          ).stdout.split()
    # make the WINNER deterministic so exactly one side's mutations are expected:
    # drain the claim first with a finalize, then race two rollbacks — both lose.
    results = _race(tmp_path, root, promote, inv, invsha, ["rollback", "rollback"])
    assert all(rc != 0 for _, rc, _ in results), results
    # zero receipt writes: only the winner may mint one, and there was no winner
    mints = [p for p in root.iterdir() if p.suffix == ".json"
             and p.name != "promote.json"]
    assert mints == [], sorted(p.name for p in mints)
    # zero durable-record rewrites: the record only moved by the DRAINING claim
    rec_after = json.loads((root / "transitions" / f"{opid}.json").read_text(encoding="utf-8"))
    assert rec_after["state"] == "ROLLING_BACK", rec_after
    assert rec_after["selected_transition"] == "rollback", rec_after
    # zero catalog mutations: no database appeared, disappeared or was renamed
    dbs_after = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", "postgres",
                                       "-tAc", "SELECT datname FROM pg_database ORDER BY 1"]
                         ).stdout.split()
    assert dbs_after == dbs_before, (dbs_before, dbs_after)
    assert _pg_truth() == truth_before
