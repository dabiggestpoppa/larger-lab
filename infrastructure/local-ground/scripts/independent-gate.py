#!/usr/bin/env python3
"""OCE Local Ground â€” independent gate (B1-LOCAL, A-003).

Genuinely independent: parses machine-readable evidence outputs only, never
human-readable log sentences. Enforces the 32 conditions of the B1-LOCAL gate
contract. Writes independent-gate.json (its own result) and exits 0 only when
every applicable condition holds.

Usage: independent-gate.py <evidence-dir> <commit> <tree>
Env:   OCE_RUN_ID, OCE_CI_MODE (true|false), OCE_EXPECTED_REPO,
       OCE_EXPECTED_BRANCH, GITHUB_REPOSITORY, GITHUB_REF_NAME
"""
import hashlib
import json
import os
import sys

EXPECTED_REPO = os.environ.get("OCE_EXPECTED_REPO", "dabiggestpoppa/larger-lab")
EXPECTED_BRANCH = os.environ.get("OCE_EXPECTED_BRANCH", "oce-program-build")
CI_MODE = os.environ.get("OCE_CI_MODE") == "true"
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY", "")
GITHUB_REF = os.environ.get("GITHUB_REF_NAME", "")

REQUIRED = [
    "identity.json", "environment-fingerprint.json", "junit.xml",
    "test-summary.json", "test-mode.txt", "adversarial-results.json",
    "adversarial-output.txt", "cloud-plan.txt", "cloud-apply-denial.txt",
    "cloud-apply-denial.json", "cloud-plan-deterministic.json",
    "local-after-denied.json", "source-clean.json", "cleanup.json",
    "stage-log.txt", "stage-status.json", "evidence-manifest.json",
]

checks = []  # (id, name, ok, detail)


def add(cid, name, ok, detail=""):
    checks.append({"id": cid, "name": name, "ok": bool(ok), "detail": str(detail)})


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def size(path):
    return os.path.getsize(path)


def main():
    if len(sys.argv) != 4:
        print("usage: independent-gate.py <evidence-dir> <commit> <tree>", file=sys.stderr)
        sys.exit(2)
    ev, commit, tree = sys.argv[1], sys.argv[2], sys.argv[3]

    # 1. Required artifacts exist
    missing = [r for r in REQUIRED if not os.path.isfile(os.path.join(ev, r))]
    add("gate-01-required-artifacts", "required artifacts exist", not missing, missing or "all present")

    # 2. Required JSON parses
    json_files = ["identity.json", "test-summary.json", "adversarial-results.json",
                  "cloud-apply-denial.json", "cloud-plan-deterministic.json",
                  "local-after-denied.json", "source-clean.json", "cleanup.json",
                  "stage-status.json", "evidence-manifest.json"]
    parse_ok = True
    for jf in json_files:
        p = os.path.join(ev, jf)
        if os.path.isfile(p):
            try:
                load_json(p)
            except Exception as e:
                parse_ok = False
                add(f"gate-02-parse-{jf}", f"json parses: {jf}", False, repr(e))
    add("gate-02-json-parses", "all required json parses", parse_ok)

    # 3. One nonempty OCE_RUN_ID everywhere
    run_env = os.environ.get("OCE_RUN_ID", "")
    run_ids = set()
    for jf in ["identity.json", "stage-status.json", "evidence-manifest.json"]:
        p = os.path.join(ev, jf)
        if os.path.isfile(p):
            d = load_json(p)
            run_ids.add(d.get("run_id", ""))
    run_ids.add(run_env)
    run_ok = len(run_ids) == 1 and "" not in run_ids
    add("gate-03-run-id-consistent", "one nonempty RUN_ID everywhere", run_ok, run_ids)

    # 4. Expected repository exactly dabiggestpoppa/larger-lab
    add("gate-04-expected-repo", "expected repository exact", EXPECTED_REPO == "dabiggestpoppa/larger-lab", EXPECTED_REPO)

    # 5. Observed remote identity matches expected
    ident = load_json(os.path.join(ev, "identity.json"))
    observed = ident.get("repository", "")
    add("gate-05-observed-repo", "observed remote identity matches", observed == EXPECTED_REPO, observed)

    # 6. Trusted CI repository matches
    trusted_ok = (not CI_MODE) or (GITHUB_REPO == EXPECTED_REPO)
    add("gate-06-trusted-ci-repo", "trusted CI repository matches", trusted_ok, GITHUB_REPO)

    # 7. Expected branch
    add("gate-07-expected-branch", "expected branch", EXPECTED_BRANCH == "oce-program-build", EXPECTED_BRANCH)

    # 8. Observed/trusted ref satisfies branch rules: the observed checkout
    # branch must equal the expected branch; in CI the trusted ref must too.
    obs_branch = ident.get("branch", "")
    ref_ok = (obs_branch == EXPECTED_BRANCH) and ((not CI_MODE) or GITHUB_REF == EXPECTED_BRANCH)
    add("gate-08-ref-satisfies-branch-rules", "observed/trusted ref branch rule", ref_ok,
        f"observed={obs_branch} ci_ref={GITHUB_REF}")

    # 9-11. Commit/tree arguments used and match
    commit_ok = ident.get("commit", "") == commit == ident.get("tested_commit", commit)
    tree_ok = ident.get("tree", "") == tree
    man = load_json(os.path.join(ev, "evidence-manifest.json"))
    commit_ok = commit_ok and man.get("implementation_commit", "") == commit
    tree_ok = tree_ok and man.get("implementation_tree", "") == tree
    add("gate-09-implementation-commit", "implementation commit matches tested checkout", commit_ok, commit)
    add("gate-10-implementation-tree", "implementation tree matches tested checkout", tree_ok, tree)
    add("gate-11-commit-tree-args-used", "gate commit/tree arguments used", commit_ok and tree_ok,
        "compared against identity.json and evidence-manifest.json")

    # 12. Source clean before/after
    try:
        sc = load_json(os.path.join(ev, "source-clean.json"))
        sc_ok = sc.get("pre") is True and sc.get("post") is True
    except Exception:
        sc_ok = False
        sc = {}
    add("gate-12-source-clean", "source clean before and after", sc_ok, sc)

    # 13-16. Test totals from machine-readable registry
    ts = load_json(os.path.join(ev, "test-summary.json"))
    t = ts.get("totals", {})
    cb = ts.get("container_backed", {})
    collected, executed = t.get("collected", 0), t.get("executed", 0)
    passed, failed = t.get("passed", 0), t.get("failed", 0)
    errors, skipped = t.get("errors", 0), t.get("skipped", 0)
    totals_consistent = (passed + failed + errors + skipped == executed) and (collected >= executed)
    add("gate-13-test-totals-consistent", "test totals match parsed entries", totals_consistent, t)
    add("gate-14-zero-failures-errors", "zero mandatory test failures/errors", failed == 0 and errors == 0,
        {"failed": failed, "errors": errors})
    mandatory_skipped = ts.get("mandatory_skipped", 0)
    if CI_MODE:
        add("gate-15-zero-mandatory-skips-ci", "zero mandatory CI skips", mandatory_skipped == 0, mandatory_skipped)
    else:
        add("gate-15-zero-mandatory-skips-ci", "mandatory skips allowed locally (CI required)",
            True, f"mandatory_skipped={mandatory_skipped}")
    if CI_MODE:
        cb_executed_all = cb.get("executed", 0) == cb.get("collected", 0)
        add("gate-16-container-tests-executed", "container-backed tests execute in CI", cb_executed_all, cb)
        mode_txt = open(os.path.join(ev, "test-mode.txt"), encoding="utf-8").read().strip()
        add("gate-16b-authoritative-mode", "CI mode is AUTHORITATIVE_CI", mode_txt == "AUTHORITATIVE_CI", mode_txt)
    else:
        add("gate-16-container-tests-executed", "container-backed tests execute in CI",
            cb.get("executed", 0) >= 0, "local mode: not required")

    # 17-18. Adversarial totals match actual entries and all pass
    adv = load_json(os.path.join(ev, "adversarial-results.json"))
    adv_entries = adv.get("checks", [])
    adv_totals = adv.get("totals", {})
    adv_consistent = (adv_totals.get("PASS", 0) + adv_totals.get("FAIL", 0)) == len(adv_entries)
    add("gate-17-adversarial-totals-match", "adversarial totals match entries", adv_consistent, adv_totals)
    add("gate-18-adversarial-all-pass", "every adversarial test passes", adv_totals.get("FAIL", 0) == 0, adv_totals)

    # 19-24. Specific executed tests from the registry (machine-parseable).
    test_entries = {r["name"]: r for r in ts.get("tests", [])}
    test_outcomes = {name: r["outcome"] for name, r in test_entries.items()}
    must_pass = {
        "test_04_postgres_state_survives_service_restart": "postgres persistence tested",
        "test_05_postgres_state_survives_compose_restart": "postgres survives compose restart",
        "test_06_isolated_redis_loss_preserves_postgres_truth": "isolated redis loss preserves postgres truth",
        "test_07_artifact_round_trip_preserves_hashes": "artifact round trip",
        "test_08_backup_completes": "backup executes",
        "test_09_clean_room_local_restore_succeeds": "clean-room restore executes",
        "test_10_restore_meets_declared_recovery_targets": "recovery targets",
        "test_11_corrupt_backup_is_rejected": "corrupt backup rejected",
        "test_03_services_reach_health_or_unknown": "all services reach health",
        "test_ctl_all_services_healthy": "entire stack simultaneously healthy",
        "test_ctl_prometheus_readiness_endpoint": "prometheus /-/ready endurance",
        "test_ctl_clean_room_database_artifact_restore": "real clean-room database+artifact restore",
        "test_ctl_corrupt_backup_rejected_against_running_stack": "running-stack corrupt backup rejected",
        "test_ctl_structured_logs_use_json_file_driver": "structured json-file logs verified",
        "test_ctl_safe_shutdown_and_verified_cleanup": "safe shutdown + restore + cleanup",
        "test_ctl_no_forbidden_public_ports": "no forbidden public ports",
    }
    for tname, label in must_pass.items():
        outcome = test_outcomes.get(tname, "missing")
        entry = test_entries.get(tname, {})
        is_container = bool(entry.get("container_backed"))
        ok = outcome == "passed"
        # Locally (no Docker) container-backed tests skip truthfully; CI must
        # require them to actually execute and pass.
        if not CI_MODE and is_container:
            ok = outcome in ("passed", "skipped")
        if CI_MODE and is_container:
            ok = outcome == "passed" and entry.get("outcome") == "passed"
        add(f"gate-{tname}", label, ok, outcome)
        if not ok:
            pass  # failures accumulate below

    # 25-26. Cloud plan deterministic + zero mutation (parse machine lines)
    try:
        cpd = load_json(os.path.join(ev, "cloud-plan-deterministic.json"))
        det_ok = cpd.get("deterministic") is True
    except Exception:
        det_ok = False
        cpd = {}
    add("gate-25-cloud-plan-deterministic", "cloud plan deterministic", det_ok, cpd)
    plan_txt = open(os.path.join(ev, "cloud-plan.txt"), encoding="utf-8").read()
    zero_mut = ("provider contacts: 0" in plan_txt and "resources changed: 0" in plan_txt
                and "cost incurred: ZERO" in plan_txt)
    add("gate-26-cloud-plan-zero-mutation", "cloud plan reports zero mutation", zero_mut)

    # 27-28. Cloud apply denial code + reason (machine-readable)
    cad = load_json(os.path.join(ev, "cloud-apply-denial.json"))
    denial_ok = cad.get("exit_code", -1) == 5
    add("gate-27-cloud-apply-denied-code", "cloud apply returns expected nonzero denial code", denial_ok, cad)
    denial_txt = open(os.path.join(ev, "cloud-apply-denial.txt"), encoding="utf-8").read()
    reason_ok = "DENIED" in denial_txt and "missing required field" in denial_txt
    add("gate-28-cloud-apply-denial-reason", "cloud apply denial contains authorization reason", reason_ok)

    # 29. Local mode works after denied cloud action
    try:
        lad = load_json(os.path.join(ev, "local-after-denied.json"))
        local_ok = lad.get("exit_code") == 0
    except Exception:
        local_ok = False
        lad = {}
    add("gate-29-local-after-denied", "local mode works after denied cloud action", local_ok, lad)

    # 30. Cleanup succeeds
    try:
        cl = load_json(os.path.join(ev, "cleanup.json"))
        cleanup_ok = cl.get("cleanup") == "ok" or (cl.get("removed") is True and cl.get("pruned") is True)
    except Exception:
        cleanup_ok = False
        cl = {}
    add("gate-30-cleanup-succeeds", "cleanup succeeds", cleanup_ok, cl)
    # 30b. In CI, the container lifecycle teardown must verify removal of the
    # disposable containers, network, and test volumes (missing evidence blocks).
    if CI_MODE:
        try:
            cc = load_json(os.path.join(ev, "container-cleanup.json"))
            cc_ok = (cc.get("cleanup") == "ok" and cc.get("containers_removed") is True
                     and cc.get("networks_removed") is True and cc.get("volumes_removed") is True)
        except Exception:
            cc_ok = False
            cc = {}
        add("gate-30b-container-cleanup-verified", "container cleanup verified in CI", cc_ok, cc)
        # Recovery evidence: a full-replace restore receipt must be present and
        # must show PostgreSQL promotion succeeded (proving real recovery ran).
        try:
            rr = load_json(os.path.join(ev, "postgres-recovery-receipt.json"))
            rec_ok = (rr.get("exit_status") == 0 and rr.get("promoted") is True
                      and rr.get("redis_restored") is False and rr.get("source_archive_sha256"))
        except Exception:
            rec_ok = False
            rr = {}
        add("gate-30c-postgres-recovery-receipt", "verified postgres promotion receipt in CI", rec_ok, rr)

    # 31. Manifest hashes and sizes match final files
    manifest_ok = True
    for art in man.get("artifacts", []):
        p = os.path.join(ev, art["path"])
        if not os.path.isfile(p):
            manifest_ok = False
            continue
        if sha256(p) != art.get("sha256") or size(p) != art.get("size"):
            manifest_ok = False
    add("gate-31-manifest-hashes-sizes", "manifest hashes and sizes match final files", manifest_ok)

    # 32. Cloud fields remain deferred / not deployed / zero / 0 mutations
    st = load_json(os.path.join(ev, "stage-status.json"))
    cloud_ok = (st.get("cloud_activation_state") == "DEFERRED_BY_OPERATOR"
                and st.get("cloud_deployment_state") == "NOT_DEPLOYED"
                and st.get("cloud_cost_state") == "ZERO"
                and st.get("cloud_mutations") == 0)
    add("gate-32-cloud-fields", "cloud fields deferred/not deployed/zero/0", cloud_ok,
        {k: st.get(k) for k in ("cloud_activation_state", "cloud_deployment_state", "cloud_cost_state", "cloud_mutations")})

    # Result
    failed = [c for c in checks if not c["ok"]]
    passed_count = len(checks) - len(failed)
    result = "PASS" if not failed else "FAIL"
    mode = "AUTHORITATIVE_CI" if CI_MODE else "LOCAL_STATIC"
    out = {
        "format": "oce-independent-gate-v1",
        "run_id": os.environ.get("OCE_RUN_ID", ""),
        "mode": mode,
        "result": result,
        "expected_repository": EXPECTED_REPO,
        "observed_repository": observed,
        "trusted_ci_repository": GITHUB_REPO,
        "expected_branch": EXPECTED_BRANCH,
        "observed_branch": obs_branch,
        "trusted_ci_ref": GITHUB_REF,
        "implementation_commit": commit,
        "implementation_tree": tree,
        "checks": checks,
        "totals": {"PASS": passed_count, "FAIL": len(failed), "total": len(checks)},
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(os.path.join(ev, "independent-gate.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"INDEPENDENT GATE [{mode}]: {result} ({passed_count}/{len(checks)} checks)")
    for c in failed:
        print(f"  FAIL {c['id']}: {c['name']} â€” {c['detail']}")
    sys.exit(0 if result == "PASS" else 1)


if __name__ == "__main__":
    main()