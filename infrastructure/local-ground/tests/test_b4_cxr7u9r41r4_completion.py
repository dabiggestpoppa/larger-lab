#!/usr/bin/env python3
"""B4-CXR7U9R41R4 — executable pre-intent recovery and artifact source authority."""
import hashlib
import hmac
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

import oce_compose as oc
import recovery_cli
from test_b4_cxr7u9r35_recovery_authority import (  # noqa: F401 — fixtures
    _promote_receipt,
    _write_inputs,
    bridge,
    pgrec,
    production_recovery_identity,
)
from test_b4_cxr7u9r41r2_crash_coherence import (  # noqa: F401
    BRIDGE_SOURCE,
    Harness,
    _arm,
    _clear,
    _crash_finalize,
    _dbs,
    _env,
    _finalize_argv,
    _kill_at_signal,
    _prepare,
    _record,
    _resume_argv,
)

TESTS = Path(__file__).resolve().parent


@pytest.fixture
def bridge_fixture(monkeypatch):
    return bridge.__wrapped__(monkeypatch)
SCRIPTS = TESTS.parent / "scripts"
LOCK = TESTS.parent / "compose" / "artifact-store" / "source-lock.json"
BASH = shutil.which("bash") or "bash"


def _record_intent(pgrec, receipt):
    opid = receipt["operation_id"]
    pgrec._record_transition(
        opid, pgrec.TRANSITION_STATE_COMMIT_INTENT, receipt,
        extra={"commit_intent": {
            "marker": "forward_commit", "operation_id": opid,
            "receipt_sha256": pgrec._receipt_digest(receipt),
            "database": pgrec.DB, "user": pgrec.USER,
            "container": pgrec.CONTAINER,
            "quarantine_database": receipt["quarantine_database"],
            "at": "2026-09-24T00:00:00Z"}})


def test_existing_finalize_claim_fresh_rollback_remains_refused(
        bridge_fixture, tmp_path, monkeypatch):
    inv, sha, archive = _write_inputs(tmp_path, monkeypatch)
    bridge_fixture.remote_sha = pgrec.sha256_file(str(archive))
    receipt, path = _promote_receipt(bridge_fixture, inv, sha, archive, "promote.json")
    bridge_fixture.reset()
    pgrec._claim_transition(receipt["operation_id"], "finalize", receipt)
    denied = pgrec.phase_rollback(str(path), str(inv), str(sha), pgrec.DB,
                                  pgrec.USER, pgrec.CONTAINER, None)
    assert denied["exit_status"] == 1
    assert "authority" in denied["error"]
    assert bridge_fixture.dropped == [] and bridge_fixture.renamed == []


def test_preintent_abort_admitted_and_converges_state(
        bridge_fixture, tmp_path, monkeypatch):
    inv, sha, archive = _write_inputs(tmp_path, monkeypatch)
    bridge_fixture.remote_sha = pgrec.sha256_file(str(archive))
    receipt, path = _promote_receipt(bridge_fixture, inv, sha, archive, "promote.json")
    pgrec._claim_transition(receipt["operation_id"], "finalize", receipt)
    bridge_fixture.reset()
    out = pgrec.phase_preintent_rollback(str(path), str(inv), str(sha), pgrec.DB,
                                         pgrec.USER, pgrec.CONTAINER, None)
    assert out["exit_status"] == 0, out
    assert out["rollback_succeeded"] is True
    assert out["original_canonical_restored"] is True
    durable = pgrec._load_transition_record(receipt["operation_id"])
    assert durable["state"] == "ROLLED_BACK"
    assert "commit_intent" not in durable and "commit_point" not in durable


@pytest.mark.parametrize("state", ["COMMIT_INTENT_RECORDED", "COMMIT_POINT_REACHED"])
def test_preintent_abort_refused_after_forward_boundary(
        state, bridge_fixture, tmp_path, monkeypatch):
    inv, sha, archive = _write_inputs(tmp_path, monkeypatch)
    bridge_fixture.remote_sha = pgrec.sha256_file(str(archive))
    receipt, path = _promote_receipt(bridge_fixture, inv, sha, archive, "promote.json")
    pgrec._claim_transition(receipt["operation_id"], "finalize", receipt)
    _record_intent(pgrec, receipt)
    if state == "COMMIT_POINT_REACHED":
        pgrec._record_transition(
            receipt["operation_id"], pgrec.TRANSITION_STATE_COMMIT_POINT, receipt,
            extra={"commit_point": {"marker": "quarantine_dropped",
                                    "at": "2026-09-24T00:00:01Z"}})
    bridge_fixture.reset()
    out = pgrec.phase_preintent_rollback(str(path), str(inv), str(sha), pgrec.DB,
                                         pgrec.USER, pgrec.CONTAINER, None)
    assert out["exit_status"] == 1
    assert bridge_fixture.dropped == [] and bridge_fixture.renamed == []
    assert pgrec._load_transition_record(receipt["operation_id"])["state"] == state


def _stalled_bridge(harness, boundary):
    source = BRIDGE_SOURCE.replace(
        'def _exists(container, user, name):\n    result = name in _read()',
        f'def _exists(container, user, name):\n    _boundary("{boundary}")\n'
        '    result = name in _read()')
    source = source.replace(
        '    while True:\n        time.sleep(0.1)',
        '    while not os.path.exists(os.path.join(HERE, "release")):\n'
        '        time.sleep(0.01)')
    harness.bridge.write_text(source, encoding="utf-8")
    harness.signal.unlink(missing_ok=True)
    harness.bridge_dir.joinpath("release").unlink(missing_ok=True)


def _abort_argv(harness, output):
    return ["--phase", "preintent-rollback", "--receipt-in", str(harness.promote),
            "--inventory", str(harness.inventory), "--inventory-sha",
            str(harness.inventory_sha), "--db", "oce_local", "--user",
            "oce_local_admin", "--container", "oce-local-postgresql",
            "--receipt-out", str(output)]


def _spawn(harness, argv, output):
    return subprocess.Popen(
        recovery_cli.cli_argv(argv, str(harness.root), str(harness.bridge)),
        env=harness.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def test_original_finalize_execution_authority_blocks_abort_until_killed(tmp_path):
    h = _prepare(tmp_path)
    _arm(h, "after_claim_before_verification")
    original = _spawn(h, _finalize_argv(h, h.root / "crash.json"), h.root / "crash.json")
    deadline = time.time() + 20
    while not h.signal.exists() and time.time() < deadline:
        time.sleep(0.01)
    assert h.signal.exists()
    blocked = recovery_cli.run_cli(
        _abort_argv(h, h.root / "blocked.json"), write_root=str(h.root),
        bridge=str(h.bridge), env_extra=_env(tmp_path), timeout=60)
    assert blocked.returncode == 1
    assert "execution authority" in blocked.stderr
    assert not (h.root / "blocked.json").exists()
    _clear(h)
    original.kill()
    original.communicate(timeout=10)
    recovered = recovery_cli.run_cli(
        _abort_argv(h, h.root / "recovered.json"), write_root=str(h.root),
        bridge=str(h.bridge), env_extra=_env(tmp_path), timeout=60)
    assert recovered.returncode == 0, recovered.stderr
    assert _record(h)["state"] == "ROLLED_BACK"


def test_two_aborts_exactly_one_executor_and_terminal_result(tmp_path):
    h = _prepare(tmp_path)
    _crash_finalize(h, "after_verification_before_intent", h.root / "crash.json")
    _stalled_bridge(h, "after_abort_lock")
    _arm(h, "after_abort_lock")
    first = _spawn(h, _abort_argv(h, h.root / "abort-1.json"), h.root / "abort-1.json")
    deadline = time.time() + 20
    while not h.signal.exists() and time.time() < deadline:
        time.sleep(0.01)
    assert h.signal.exists()
    second = recovery_cli.run_cli(
        _abort_argv(h, h.root / "abort-2.json"), write_root=str(h.root),
        bridge=str(h.bridge), env_extra=_env(tmp_path), timeout=60)
    h.bridge_dir.joinpath("release").write_text("go", encoding="utf-8")
    first.communicate(timeout=60)
    assert first.returncode == 0
    assert second.returncode == 1
    assert "execution authority" in second.stderr
    assert not (h.root / "abort-2.json").exists()
    assert _record(h)["state"] == "ROLLED_BACK"


def test_resume_and_abort_race_has_one_executor(tmp_path):
    h = _prepare(tmp_path)
    _crash_finalize(h, "after_intent_before_drop", h.root / "crash.json")
    _stalled_bridge(h, "after_abort_lock")
    _arm(h, "after_abort_lock")
    resume = _spawn(h, _resume_argv(h, h.root / "resume.json"), h.root / "resume.json")
    deadline = time.time() + 20
    while not h.signal.exists() and time.time() < deadline:
        time.sleep(0.01)
    assert h.signal.exists()
    denied = recovery_cli.run_cli(
        _abort_argv(h, h.root / "abort.json"), write_root=str(h.root),
        bridge=str(h.bridge), env_extra=_env(tmp_path), timeout=60)
    assert denied.returncode == 1
    assert "requires FINALIZING" in denied.stderr
    refused = json.loads((h.root / "abort.json").read_text(encoding="utf-8"))
    assert refused["exit_status"] == 1
    assert "rollback_attempted" not in refused
    h.bridge_dir.joinpath("release").write_text("go", encoding="utf-8")
    resume.communicate(timeout=60)
    assert resume.returncode == 0
    assert _record(h)["state"] == "FINALIZED"


def test_two_resume_finalize_calls_serialize_to_same_terminal_state(tmp_path):
    h = _prepare(tmp_path)
    _crash_finalize(h, "after_drop_before_commit_point", h.root / "crash.json")
    _stalled_bridge(h, "after_abort_lock")
    _arm(h, "after_abort_lock")
    first = _spawn(h, _resume_argv(h, h.root / "resume-1.json"), h.root / "resume-1.json")
    deadline = time.time() + 20
    while not h.signal.exists() and time.time() < deadline:
        time.sleep(0.01)
    second = recovery_cli.run_cli(
        _resume_argv(h, h.root / "resume-2.json"), write_root=str(h.root),
        bridge=str(h.bridge), env_extra=_env(tmp_path), timeout=60)
    h.bridge_dir.joinpath("release").write_text("go", encoding="utf-8")
    first.communicate(timeout=60)
    assert first.returncode == 0
    # The contender owns no execution authority; the winner alone completes.
    assert second.returncode == 1
    assert "execution authority" in second.stderr
    assert not (h.root / "resume-2.json").exists()
    assert _record(h)["state"] == "FINALIZED"


def _shell_functions():
    text = (SCRIPTS / "restore.sh").read_text(encoding="utf-8")
    names = ["durable_precommit", "pg_abort_finalize_preintent",
             "write_transaction_rollback_receipt", "rollback_precommit"]
    chunks = []
    for name in names:
        match = re.search(rf"{re.escape(name)}\(\) \{{.*?\n\}}", text, re.S)
        assert match, name
        chunks.append(match.group(0))
    return "\n\n".join(chunks)


def _engine_wrapper(harness, tmp_path):
    bindir = tmp_path / "test-bin"
    bindir.mkdir(exist_ok=True)
    path = bindir / "pg-recovery.py"
    path.write_text(
        "#!/usr/bin/env python3\nimport sys\n"
        f"sys.path.insert(0, {str(TESTS)!r})\nimport recovery_cli\n"
        f"r=recovery_cli.run_cli(sys.argv[1:], write_root={str(harness.root)!r}, "
        f"bridge={str(harness.bridge)!r}, env_extra={_env(harness.tmp)!r})\n"
        "sys.stdout.write(r.stdout); sys.stderr.write(r.stderr)\n"
        "raise SystemExit(r.returncode)\n", encoding="utf-8")
    path.chmod(0o755)
    return bindir


def _tree_sha(root):
    h = hashlib.sha256()
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            h.update(str(path.relative_to(root)).encode())
            h.update(path.read_bytes())
    return h.hexdigest()


@pytest.mark.parametrize("boundary", [
    "after_claim_before_verification",
    "after_verification_before_intent",
])
def test_production_shell_preintent_route_converges_old_old(boundary, tmp_path):
    h = _prepare(tmp_path)
    _crash_finalize(h, boundary, h.root / "crash.json")
    bindir = _engine_wrapper(h, tmp_path)
    artifact = tmp_path / "artifact"
    snapshot = tmp_path / "artifact-snapshot"
    artifact.mkdir()
    snapshot.mkdir()
    (artifact / "truth.txt").write_text("new", encoding="utf-8")
    (snapshot / "truth.txt").write_text("old", encoding="utf-8")
    before = _tree_sha(snapshot)
    after = _tree_sha(artifact)
    assert before != after
    script = f'''set -uo pipefail
OCE_PYTHON={shlex_quote(sys.executable)}
BIN={shlex_quote(str(bindir))}
VAR_DIR={shlex_quote(str(h.tmp))}
PROMOTE_RECEIPT={shlex_quote(str(h.promote))}
RECEIPT_DIR={shlex_quote(str(h.root))}
ROLLBACK_RECEIPT={shlex_quote(str(h.root / "rollback-receipt.json"))}
TRANSACTION_RECEIPT={shlex_quote(str(h.root / "transaction-rollback-receipt.json"))}
ARTIFACT_ROOT={shlex_quote(str(artifact))}
ARTIFACT_BEFORE_SHA={shlex_quote(before)}
ARTIFACT_AFTER_SHA={shlex_quote(after)}
ARTIFACT_SWITCHED=true
ARTIFACT_LIVE_SNAPSHOT=true
ARTIFACT_STAGED=true
ARTIFACT_APPLIED=true
PG_PROMOTED=true
PG_FINALIZED=false
COMMITTED=false
TS_FMT="+%Y-%m-%dT%H:%M:%SZ"
PG_COMMON=(--inventory {shlex_quote(str(h.inventory))} --inventory-sha {shlex_quote(str(h.inventory_sha))} --db oce_local --user oce_local_admin --container oce-local-postgresql)
EV_DIR=""
FAIL_NOTE=""
LIVE_SNAPSHOT_DIR={shlex_quote(str(snapshot))}
artifact_stop() {{ return 0; }}
artifact_start() {{ return 0; }}
artifact_volume_sha() {{ "$OCE_PYTHON" -c '{_tree_sha_py()}' "$ARTIFACT_ROOT"; }}
artifact_restore_from() {{ rm -rf "$ARTIFACT_ROOT"; mkdir -p "$ARTIFACT_ROOT"; cp -a "$1"/. "$ARTIFACT_ROOT"/; }}
{_shell_functions()}
rollback_precommit "r41r4 production route"
'''
    result = subprocess.run([BASH, "-c", script], capture_output=True, text=True,
                            env=h.env, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (artifact / "truth.txt").read_text(encoding="utf-8") == "old"
    assert _tree_sha(artifact) == before
    assert _record(h)["state"] == "ROLLED_BACK"
    transaction = json.loads((h.root / "transaction-rollback-receipt.json").read_text(
        encoding="utf-8"))
    assert transaction["converged_old_old"] is True
    assert transaction["postgres_rolled_back"] is True
    assert transaction["artifact_restored"] is True
    ops_root = tmp_path / "operations"
    indexed = subprocess.run(
        [sys.executable, str(SCRIPTS / "recovery-ops.py"), "add",
         "--ops-root", str(ops_root), "--operation-id",
         "0123456789abcdef0123456789abcdef", "--operation-type", "restore",
         "--run-id", "0123456789abcdef", "--commit", "cafe0123" * 5,
         "--tree", "beef4567" * 5, "--started-at", "2026-09-24T00:00:00Z",
         "--finished-at", "2026-09-24T00:01:00Z", "--backup-id", "r41r4-proof",
         "--backup-scope", "full", "--restore-mode", "full-replace",
         "--source-database", "oce_local", "--target-database", "oce_local",
         "--final-result", "blocked", "--rollback-result", "ok",
         "--cloud-mutations", "0", "--cloud-cost-state", "ZERO",
         "--receipt", str(h.root / "transaction-rollback-receipt.json")],
        capture_output=True, text=True, timeout=30)
    assert indexed.returncode == 0, indexed.stdout + indexed.stderr
    verify = subprocess.run(
        [sys.executable, str(SCRIPTS / "recovery-ops.py"), "verify",
         "--ops-root", str(ops_root)], capture_output=True,
        text=True, timeout=30)
    assert verify.returncode == 0, verify.stdout + verify.stderr
    index = json.loads((ops_root / "index.json").read_text(
        encoding="utf-8"))
    indexed = index["operations"][0]["receipts"]
    assert any(item["path"].endswith("transaction-rollback-receipt.json")
               for item in indexed)


def shlex_quote(value):
    import shlex
    return shlex.quote(str(value))


def _tree_sha_py():
    return ("import hashlib,pathlib,sys; root=pathlib.Path(sys.argv[1]); "
            "h=hashlib.sha256(); "
            "[(h.update(str(p.relative_to(root)).encode()),h.update(p.read_bytes())) "
            "for p in sorted(root.rglob(chr(42))) if p.is_file()]; print(h.hexdigest())")


def test_negative_control_r41r2_classifies_legal_but_ordinary_rollback_fails(tmp_path):
    h = _prepare(tmp_path)
    _crash_finalize(h, "after_claim_before_verification", h.root / "crash.json")
    assert _classify(h) == 5
    ordinary = recovery_cli.run_cli(
        ["--phase", "rollback", "--receipt-in", str(h.promote),
         "--inventory", str(h.inventory), "--inventory-sha", str(h.inventory_sha),
         "--db", "oce_local", "--user", "oce_local_admin",
         "--container", "oce-local-postgresql", "--receipt-out",
         str(h.root / "ordinary.json")], write_root=str(h.root),
        bridge=str(h.bridge), env_extra=_env(tmp_path), timeout=60)
    assert ordinary.returncode == 1
    abort = recovery_cli.run_cli(
        _abort_argv(h, h.root / "governed.json"), write_root=str(h.root),
        bridge=str(h.bridge), env_extra=_env(tmp_path), timeout=60)
    assert abort.returncode == 0
    assert _record(h)["state"] == "ROLLED_BACK"


def _classify(harness):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "pg-recovery.py"), "--phase", "reconcile",
         "--classify-rollback", str(harness.promote), "--transition-dir",
         str(harness.transitions)], env=harness.env, capture_output=True,
        text=True, timeout=30).returncode


def test_artifact_source_authority_is_exact_and_registry_independent():
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    dockerfile = (LOCK.parent / "Dockerfile").read_text(encoding="utf-8")
    assert lock["release_tag"] == "RELEASE.2024-05-28T17-19-04Z"
    assert lock["peeled_commit"] == "f79a4ef4d0dc3e6562cad0d1d1db674bc8c75531"
    assert len(lock["source_sha256"]) == 64
    assert "@sha256:" in lock["go_builder"] and "@sha256:" in lock["runtime_base"]
    assert "quay.io/minio/minio" not in dockerfile
    assert "latest" not in dockerfile.lower()
    assert "ADD --checksum=sha256:${SOURCE_SHA256}" in dockerfile
    assert "-mod=readonly" in dockerfile and "GOSUMDB=sum.golang.org" in dockerfile


def _sign(key, msg):
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def _s3_request(method, bucket, key, body=b"", access="oce-local-access",
                 secret="test-secret-artifact-001"):
    now = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    date = now[:8]
    date_only = date.split("T")[0]
    host_header = "localhost:9000"
    payload_hash = hashlib.sha256(body).hexdigest()
    suffix = f"/{key}" if key else "/"
    canonical_headers = (f"host:{host_header}\n"
                         f"x-amz-content-sha256:{payload_hash}\n"
                         f"x-amz-date:{now}\n")
    signed_headers = "host;x-amz-content-sha256;x-amz-date"
    canonical = "\n".join([
        method, f"/{bucket}{suffix}", "", canonical_headers, signed_headers,
        payload_hash,
    ])
    scope = f"{date}/{date_only}/us-east-1/s3/aws4_request"
    string_to_sign = "\n".join([
        "AWS4-HMAC-SHA256", now, scope,
        hashlib.sha256(canonical.encode()).hexdigest()])
    kdate = _sign(("AWS4" + secret).encode(), date)
    kregion = _sign(kdate, date_only)
    kservice = _sign(kregion, "us-east-1")
    ksigning = _sign(kservice, "s3")
    signature = _sign(ksigning, string_to_sign).hex()
    auth = (f"AWS4-HMAC-SHA256 Credential={access}/{scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}")
    url = f"http://{host_header}/{bucket}{suffix}"
    command = ["docker", "exec"]
    if method == "PUT":
        command += ["-i", oc.ARTIFACT, "curl", "-sS", "-o", "/dev/null",
                    "-w", "%{http_code}", "-X", "PUT", "--data-binary", "@-",
                    "-H", f"Host: {host_header}", "-H", f"x-amz-date: {now}",
                    "-H", f"x-amz-content-sha256: {payload_hash}",
                    "-H", f"Authorization: {auth}", url]
    else:
        command += [oc.ARTIFACT, "curl", "-sS", "-w", "\n%{http_code}",
                    "-H", f"Host: {host_header}", "-H", f"x-amz-date: {now}",
                    "-H", f"x-amz-content-sha256: {payload_hash}",
                    "-H", f"Authorization: {auth}", url]
    return subprocess.run(command, input=body if method == "PUT" else None,
                          capture_output=True)


def test_official_source_image_health_s3_and_persistence(oce_stack, tmp_path):
    oc.assert_stack_converged(timeout_s=600, stable=3)
    image = "oce-local/artifact-store:RELEASE.2024-05-28T17-19-04Z-f79a4ef4d0dc"
    inspect = subprocess.run(["docker", "image", "inspect", image], capture_output=True,
                             text=True, timeout=30)
    assert inspect.returncode == 0, inspect.stderr
    metadata = json.loads(inspect.stdout)[0]
    labels = metadata["Config"]["Labels"]
    assert labels["org.opencontainers.image.revision"] == "f79a4ef4d0dc3e6562cad0d1d1db674bc8c75531"
    version = oc.dexec(oc.ARTIFACT, ["minio", "--version"]).stdout
    assert "RELEASE.2024-05-28T17-19-04Z" in version
    # S3 API write/read against the running OCE-owned image.
    body = b"r41r4-official-source"
    bucket = _s3_request("PUT", "r41r4-proof", "", b"")
    assert bucket.stdout == b"200", bucket.stderr
    put = _s3_request("PUT", "r41r4-proof", "payload", body)
    assert put.stdout == b"200", put.stderr
    get = _s3_request("GET", "r41r4-proof", "payload")
    assert get.stdout.endswith(b"\n200"), get.stdout
    assert get.stdout.rsplit(b"\n", 1)[0] == body
    marker = tmp_path / "restart-marker"
    marker.write_text("survives", encoding="utf-8")
    subprocess.run(["docker", "cp", str(marker), f"{oc.ARTIFACT}:/data/"], check=True,
                   timeout=30)
    subprocess.run(["docker", "restart", oc.ARTIFACT], check=True, timeout=120)
    oc.assert_stack_converged(timeout_s=180, stable=2)
    got = subprocess.run(["docker", "exec", oc.ARTIFACT, "cat", "/data/restart-marker"],
                         capture_output=True, text=True, timeout=30)
    assert got.stdout.strip() == "survives"
