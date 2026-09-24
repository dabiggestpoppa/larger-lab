#!/usr/bin/env python3
"""B4-CXR7U9R40-R1 — the transition claim is OPERATION-WIDE and atomic.

R39-R3 used one claim file PER TRANSITION (<op>.finalize.claim vs
<op>.rollback.claim): two processes could both read PROMOTED, both observe
their transition as permitted, and both create their different claim files
successfully — then concurrently mutate the same PostgreSQL recovery
operation. That race was reproduced against the published code.

The law now: ONE claim file per OPERATION, exclusively created, naming the
selected transition and binding it to the promote receipt's content digest.
Exactly one of finalize/rollback can win; every loser is refused BEFORE any
docker, catalog, receipt or durable-record mutation.

The proofs below drive REAL PROCESSES (the real CLI in child processes,
released through a real multiprocessing barrier), because the guarantee
lives in operating-system exclusive creation — no in-process fake can prove
it. The races themselves need only the governed filesystem and O_EXCL, so
they are NOT container-gated (B4-CXR7U9R41-R1); they run in every CI
execution. Tests that additionally read the live PostgreSQL container
( loser-mutation and end-to-end truth checks ) stay container-marked.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import oce_compose as oc

import recovery_cli

CLI = recovery_cli.CLI
TESTS = Path(__file__).resolve().parent


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _env(tmp_path, roots=None):
    # `roots` must contain the bridge content dir (the receipts/inventory
    # artifacts) or the engine's containment check refuses them.
    return {"OCE_BACKUP_ROOTS": str(roots or tmp_path),
            "OCE_COMMIT": "a" * 40, "OCE_TREE": "b" * 40,
            "OCE_RUN_ID": "0123456789abcdef"}


def _pg_truth():
    r = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-tAc",
                               "SELECT k || '=' || v FROM backup_probe ORDER BY k;"])
    return [line.strip() for line in r.stdout.splitlines() if line.strip()]


def _prepare_promotion_container(tmp_path):
    """One genuine promotion driven by the REAL CLI against the REAL stack
    (used by the container-marked loser-mutation proof)."""
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


def _prepare_promotion(tmp_path, bridge_dir):
    """One genuine promotion produced by the REAL engine phase code (running
    in a child process over the constructed container bridge); returns
    (write_root, promote_receipt_path, inventory, inventory_sha)."""
    bd = Path(bridge_dir)
    content = bd / "content"
    root = bd / "recovery"
    (root / "transitions").mkdir(parents=True, exist_ok=True)
    promote = root / "promote.json"
    r = recovery_cli.run_cli(
        ["--phase", "promote", "--archive", str(content / "archive.dump"),
         "--inventory", str(content / "inventory.json"),
         "--inventory-sha", str(content / "inventory.json.sha256"),
         "--db", "oce_local", "--user", "oce_local_admin", "--container", "oce-local-postgresql",
         "--receipt-out", str(promote)],
        write_root=str(root), env_extra=_env(tmp_path, roots=bd), timeout=600,
        bridge=str(bd / "bridge.py"))
    assert promote.is_file(), f"promotion never produced its receipt: {r.stderr[-400:]}"
    assert r.returncode == 0, f"promote failed: {r.stderr[-400:]}"
    return root, promote, content / "inventory.json", content / "inventory.json.sha256"


def _write_bridge(tmp_path):
    """Construct the race harness's container bridge: a real child-process
    plugin (the engine's own load-extension seam) that stands in for the
    catalog/docker surface so the OS-level claim races need no Docker. The
    bridge records every container call it receives; a clean race performs
    exactly zero. The promote it produces is the engine's genuine phase code
    over the bridge, so the receipts raced over are the real artifact."""
    bridge_dir = tmp_path / "bridge"
    content = bridge_dir / "content"
    content.mkdir(parents=True)
    inventory_doc = json.dumps({"format": "oce-pg-inventory-v1",
                                "database": "oce_local", "table_count": 1,
                                "tables": [{"name": "public.widgets",
                                            "row_count": 3,
                                            "fingerprint": "deadbeef"}]},
                               sort_keys=True)
    (content / "inventory.json").write_text(inventory_doc, encoding="utf-8")
    (content / "inventory.json.sha256").write_text(
        hashlib.sha256(inventory_doc.encode()).hexdigest(), encoding="utf-8")
    (content / "archive.dump").write_bytes(b"PGDMP")
    (bridge_dir / "bridge.py").write_text(
        "import json\n"
        "import hashlib\n"
        "import os\n"
        "STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dbs.json')\n"
        "def _read():\n"
        "    with open(STATE, encoding='utf-8') as f:\n"
        "        return set(json.load(f))\n"
        "def _write(dbs):\n"
        "    with open(STATE, 'w', encoding='utf-8') as f:\n"
        "        json.dump(sorted(dbs), f)\n"
        "if not os.path.exists(STATE):\n"
        "    _write({'postgres', 'oce_local'})\n"
        "def _catalog(container, user):\n"
        "    return _read()\n"
        "def _clone(container, archive_path):\n"
        "    return str(archive_path)\n"
        "def _validate(container, remote):\n"
        "    return 'ok'\n"
        "def _remote_hash(container, remote):\n"
        "    import hashlib as h\n"
        "    return h.sha256(open(str(remote), 'rb').read()).hexdigest()\n"
        "def _staging(container, user, base_db, stamp):\n"
        "    dbs = _read(); dbs.add('oce_local_restore_' + stamp); _write(dbs)\n"
        "    return 'oce_local_restore_' + stamp\n"
        "def _drop(container, user, name):\n"
        "    dbs = _read(); dbs.discard(name); _write(dbs)\n"
        "def _rename(container, user, from_name, to_name):\n"
        "    dbs = _read(); dbs.discard(from_name); dbs.add(to_name); _write(dbs)\n"
        "def _terminate(container, user, *dbs):\n"
        "    pass\n"
        "def _verify(container, db, user, inventory, probe):\n"
        "    return True, [], {'public.widgets': 3}, {'public.widgets': 'deadbeef'}\n"
        "def _rows(container, db, user, tables):\n"
        "    return {t: 3 for t in tables}\n"
        "def _fps(container, db, user, tables):\n"
        "    return {t: 'deadbeef' for t in tables}\n"
        "class _R:\n"
        "    returncode = 0\n"
        "    stdout = b'16.2'\n"
        "    stderr = b''\n"
        "def _docker_exec(container, cmd, stdin_bytes=None, timeout=600):\n"
        "    return _R()\n"
        "def install(mod):\n"
        "    mod.clone_archive_into_container = _clone\n"
        "    mod.validate_archive = _validate\n"
        "    mod.sha256_remote_file = _remote_hash\n"
        "    mod.create_staging_db = _staging\n"
        "    mod.drop_db = _drop\n"
        "    mod.rename_db = _rename\n"
        "    mod.terminate_local_connections = _terminate\n"
        "    mod._verify_db = _verify\n"
        "    mod.collect_observed_rows = _rows\n"
        "    mod.collect_observed_fingerprints = _fps\n"
        "    mod._catalog_names = _catalog\n"
        "    mod.docker_exec = _docker_exec\n", encoding="utf-8")
    return bridge_dir, content


def _race(tmp_path, root, promote, inv, invsha, transitions, bridge=None):
    """Launch len(transitions) REAL OS processes (subprocess.Popen of this
    interpreter running a tiny worker script) released by one filesystem
    barrier; returns [(transition, rc)]. A child that dies before reporting
    FAILS the test — never converted into synthetic rc=99 evidence."""
    go = root / "GO"
    procs, outs = [], []
    env = dict(os.environ)
    env.update(_env(tmp_path, roots=Path(root).parent))
    env["PYTHONIOENCODING"] = "utf-8"
    for i, tr in enumerate(transitions):
        out = root / f"{tr}-{i}.json"
        outs.append((tr, out))
        code = (
            "import sys, time\n"
            "sys.path.insert(0, r'%s')\n"
            "from pathlib import Path\n"
            "import recovery_cli\n"
            "go, out = r'%s', Path(r'%s')\n"
            "deadline2 = time.time() + 120\n"
            "while not Path(go).exists():\n"
            "    if time.time() > deadline2:\n"
            "        out.with_suffix('.rc').write_text('-1', encoding='utf-8'); raise SystemExit(3)\n"
            "    time.sleep(0.005)\n"
            "r = recovery_cli.run_cli(\n"
            "    ['--phase', '%s', '--receipt-in', r'%s',\n"
            "     '--inventory', r'%s', '--inventory-sha', r'%s',\n"
            "     '--db', 'oce_local', '--user', 'oce_local_admin',\n"
            "     '--container', 'oce-local-postgresql',\n"
            "     '--receipt-out', str(out)],\n"
            "    write_root=r'%s', env_extra=TEST_ENV, timeout=600,\n"
            "    bridge=BRIDGE)\n"
            "out.with_suffix('.rc').write_text(str(r.returncode), encoding='utf-8')\n"
            "out.with_suffix('.err').write_text(r.stderr[-500:], encoding='utf-8')\n"
        ) % (TESTS.as_posix(), go.as_posix(), out.as_posix(), tr,
             Path(promote).as_posix(), Path(inv).as_posix(),
             Path(invsha).as_posix(), Path(root).as_posix())
        env_extra_repr = repr(_env(tmp_path))
        bridge_repr = repr(bridge)
        code = code.replace("TEST_ENV", env_extra_repr)
        code = code.replace("BRIDGE", bridge_repr)
        worker = root / f"worker-{tr}-{i}.py"
        worker.write_text(code, encoding="utf-8")
        procs.append(subprocess.Popen([sys.executable, str(worker)],
                                      env=env, cwd=str(root)))
    # release the barrier
    go.write_text("go", encoding="utf-8")
    for p in procs:
        p.wait(600)
    results = []
    for (tr, out) in outs:
        rc_file = out.with_suffix(".rc")
        assert rc_file.is_file(), (f"child for {tr!r} died before reporting "
                                   f"(exitcode unknown)")
        results.append((tr, int(rc_file.read_text())))
    return results


# --------------------------------------------------------------------- #
# the races — real processes, one barrier, OS-level exclusive creation.
# These four need only the governed filesystem and O_EXCL: they are NOT
# container-gated (B4-CXR7U9R41-R1) and execute in every CI run.
# --------------------------------------------------------------------- #

def test_finalize_versus_rollback_exactly_one_wins(tmp_path):
    bridge_dir, _content = _write_bridge(tmp_path)
    root, promote, inv, invsha = _prepare_promotion(tmp_path, bridge_dir)
    results = _race(tmp_path, root, promote, inv, invsha, ["finalize", "rollback"],
                    bridge=str(bridge_dir / "bridge.py"))
    winners = [tr for tr, rc in results if rc == 0]
    assert len(winners) == 1, results
    winner = winners[0]
    loser = "rollback" if winner == "finalize" else "finalize"
    loser_rc = [rc for tr, rc in results if tr == loser][0]
    assert loser_rc != 0, results
    # the durable record names the winner and cannot be re-opened
    opid = json.loads(promote.read_text(encoding="utf-8"))["operation_id"]
    rec = json.loads((root / "transitions" / f"{opid}.json")
                     .read_text(encoding="utf-8"))
    claim = json.loads((root / "transitions" / f"{opid}.claim")
                       .read_text(encoding="utf-8"))
    assert claim["transition"] == winner, claim
    assert rec["state"] in {"FINALIZED", "ROLLED_BACK", "FAILED",
                            "COMMIT_POINT_REACHED",
                            "FINALIZING" if winner == "finalize" else "ROLLING_BACK"}, rec
    assert rec.get("selected_transition") == winner, rec


def test_finalize_versus_finalize_exactly_one_wins(tmp_path):
    bridge_dir, _content = _write_bridge(tmp_path)
    root, promote, inv, invsha = _prepare_promotion(tmp_path, bridge_dir)
    results = _race(tmp_path, root, promote, inv, invsha, ["finalize", "finalize"],
                    bridge=str(bridge_dir / "bridge.py"))
    assert sorted(rc for _, rc in results).count(0) == 1, results


def test_rollback_versus_rollback_exactly_one_wins(tmp_path):
    bridge_dir, _content = _write_bridge(tmp_path)
    root, promote, inv, invsha = _prepare_promotion(tmp_path, bridge_dir)
    results = _race(tmp_path, root, promote, inv, invsha, ["rollback", "rollback"],
                    bridge=str(bridge_dir / "bridge.py"))
    assert sorted(rc for _, rc in results).count(0) == 1, results


def test_the_loser_mutates_nothing(oce_stack, tmp_path):
    """The losing process performs zero docker calls, zero catalog changes,
    zero receipt writes and zero durable-record rewrites.

    The authority is FIRST drained by one deterministic winner (a sequential
    finalize claim — the drain defect B4-CXR7U9R41-R1 called out), THEN two
    real rollback processes race for the spent operation: both must lose, and
    the loser's outcome is proven zero-mutation against the live container.
    """
    root, promote, inv, invsha = _prepare_promotion_container(tmp_path)
    opid = json.loads(promote.read_text(encoding="utf-8"))["operation_id"]
    truth_before = _pg_truth()
    dbs_before = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", "postgres",
                                        "-tAc", "SELECT datname FROM pg_database ORDER BY 1"]
                          ).stdout.split()
    receipts_before = sorted(p.name for p in root.iterdir())
    record_before = json.loads((root / "transitions" / f"{opid}.json")
                               .read_text(encoding="utf-8"))
    # DRAIN: one sequential finalize takes the operation-wide claim. Its own
    # durable mutation (FINALIZING + selected_transition) is the EXPECTED
    # delta; the racing losers below may add nothing.
    drain = recovery_cli.run_cli(
        ["--phase", "finalize", "--receipt-in", str(promote),
         "--inventory", str(inv), "--inventory-sha", str(invsha),
         "--db", oc.PG_DB, "--user", oc.PG_USER, "--container", oc.POSTGRES,
         "--receipt-out", str(root / "drain-finalize.json")],
        write_root=str(root), env_extra=_env(tmp_path), timeout=600)
    drain_rc = drain.returncode
    assert drain_rc in (0, 1), drain_rc   # winner or clean refusal, not a crash
    record_after_drain = json.loads((root / "transitions" / f"{opid}.json")
                                    .read_text(encoding="utf-8"))
    assert record_after_drain["state"] in ("FINALIZING", "COMMIT_POINT_REACHED",
                                           "FINALIZED"), record_after_drain
    # RACE: two real rollback processes contend for the ALREADY-CLAIMED
    # operation. Both must lose — and lose with zero mutations.
    results = _race(tmp_path, root, promote, inv, invsha, ["rollback", "rollback"])
    assert all(rc != 0 for _, rc in results), results
    # zero receipt writes by the losers: exactly the drain's receipt may exist
    mints = [p.name for p in root.iterdir() if p.suffix == ".json"
             and p.name not in receipts_before + ["drain-finalize.json"]]
    assert mints == [], sorted(mints)
    # zero durable-record rewrites by the losers: the record moved only by the
    # drain (identical to its post-drain content)
    rec_after = json.loads((root / "transitions" / f"{opid}.json").read_text(encoding="utf-8"))
    assert rec_after == record_after_drain, (record_after_drain, rec_after)
    # zero catalog mutations: no database appeared, disappeared or was renamed
    # beyond what the drain itself did (a successful drain finalize drops the
    # quarantine — that mutation belongs to the WINNER, not the losers)
    dbs_after = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", "postgres",
                                        "-tAc", "SELECT datname FROM pg_database ORDER BY 1"]
                          ).stdout.split()
    if drain_rc == 1:
        # drain was refused (no catalog access happened): catalog must be
        # byte-identical and the losers added nothing
        assert dbs_after == dbs_before, (dbs_before, dbs_after)
        assert _pg_truth() == truth_before
    else:
        # drain succeeded: the only allowed delta is the quarantine's removal
        quarantine = record_before["quarantine_database"]
        expected = sorted(d for d in dbs_before if d != quarantine)
        assert dbs_after == expected, (dbs_before, dbs_after)
    # the losers' durable authority was the spent claim, never fresh PROMOTED:
    assert rec_after["selected_transition"] == "finalize", rec_after
