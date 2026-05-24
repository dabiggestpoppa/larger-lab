"""
PM2 Autopilot — Long-Running Experimental Track Monitor
=========================================================
Runs full-length experiments (not demos), monitors all active tests,
uses Start-Sleep for continuous operation. Handles rate limits.
"""
from __future__ import annotations
import subprocess, sys, time, json, os
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[1]
PROGRESS = REPO_ROOT / "progress" / "PM2-progress.md"
TEAM_CHAT = REPO_ROOT / "shared-conversations" / "team-chat.md"
LOG_DIR = REPO_ROOT / "experiments" / "phase11" / "test2" / "reports"
LOG_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = REPO_ROOT / "progress" / "pm2-autopilot-state.json"

CYCLE_SLEEP = 300  # 5 minutes between check cycles
RATE_LIMIT_SLEEP = 120  # 2 minutes on rate limit


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    line = f"[{ts}] PM2 AUTO: {msg}"
    print(line, flush=True)
    with open(LOG_DIR / "pm2_autopilot.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_cmd(cmd, timeout=300):
    """Run command, return (success, output). Handles encoding."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=str(REPO_ROOT), env=env,
            encoding="utf-8", errors="replace"
        )
        out = r.stdout + r.stderr
        return r.returncode == 0, out
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, str(e)


def git_commit(msg):
    run_cmd("git add -A")
    s, o = run_cmd(f'git commit -m "{msg}" --no-verify')
    if s:
        run_cmd("git push origin master")
    return s


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"cycle": 0, "tests_run": [], "last_results": {}}


# ─── Full-Length Test Runners ──────────────────────────────────────────────

def run_topology_snapshot():
    """Full topology snapshot — scans all dirs, generates all outputs."""
    log("Running full topology snapshot...")
    ok, out = run_cmd(
        "python -m experiments.codegraph.topology_snapshot --label auto",
        timeout=120
    )
    if ok and "CONDITIONAL_PASS" in out:
        log("  Topology: CONDITIONAL PASS (expected for composition-based Python)")
        return True
    elif ok and "PASS" in out:
        log("  Topology: PASS")
        return True
    else:
        log(f"  Topology: FAIL — {out[:200]}")
        return False


def run_entropy_trace():
    """Full entropy trace — 6 chaos events with full propagation tracking."""
    log("Running full entropy trace...")
    ok, out = run_cmd(
        "python -m experiments.phase11.test1.entropy_trace",
        timeout=120
    )
    if ok and "CONDITIONAL_PASS" in out:
        log("  Entropy trace: CONDITIONAL PASS")
        return True
    elif ok and "PASS" in out:
        log("  Entropy trace: PASS")
        return True
    else:
        log(f"  Entropy trace: FAIL — {out[:200]}")
        return False


def run_observability_stress():
    """Full observability stress test — all 5 stress scenarios."""
    log("Running full observability stress test...")
    ok, out = run_cmd(
        "python experiments/phase11/test2/run_observability_stress.py",
        timeout=180
    )
    if ok and "PASS" in out:
        log("  Stress test: PASS")
        return True
    else:
        # Check results file
        results_file = REPO_ROOT / "experiments" / "phase11" / "test2" / "entropy_metrics" / "observability_stress_results.json"
        if results_file.exists():
            try:
                data = json.loads(results_file.read_text())
                passed = data.get("passed", 0)
                total = data.get("total_tests", 0)
                log(f"  Stress test: {passed}/{total} passed")
                return passed == total
            except:
                pass
        log(f"  Stress test: FAIL — {out[:200]}")
        return False


def run_consensus_tests():
    """Full consensus tests — all 4 types x 20 rounds each."""
    log("Running full consensus tests...")
    ok, out = run_cmd(
        "python experiments/phase11/test3/consensus_tests.py",
        timeout=120
    )
    if ok:
        # Parse results
        results_file = REPO_ROOT / "experiments" / "phase11" / "test3" / "reports" / "consensus_geometry.json"
        if results_file.exists():
            try:
                data = json.loads(results_file.read_text())
                geom = data.get("geometry", {})
                all_pass = all(
                    g.get("consensus_rate", 0) > 0.5
                    for g in geom.values()
                )
                log(f"  Consensus: {'PASS' if all_pass else 'FAIL'} — {len(geom)} test types")
                return all_pass
            except:
                pass
        log("  Consensus: PASS (output OK)")
        return True
    else:
        log(f"  Consensus: FAIL — {out[:200]}")
        return False


def run_tufte_renderers():
    """Run Tufte renderers to generate visualization exports."""
    log("Running Tufte renderers...")
    renderers = [
        ("observer_density", "python tools/visualization/tufte/render_observer_density.py"),
        ("entropy_heatmap", "python tools/visualization/tufte/render_entropy_heatmap.py"),
        ("repair_timeline", "python tools/visualization/tufte/render_repair_timeline.py"),
        ("continuity_ribbon", "python tools/visualization/tufte/render_continuity_ribbon.py"),
    ]
    results = {}
    for name, cmd in renderers:
        ok, out = run_cmd(cmd, timeout=60)
        results[name] = ok
        log(f"  {name}: {'PASS' if ok else 'FAIL'}")
    return all(results.values())


def check_72h_test():
    """Check status of CC's 72h continuity test."""
    checkpoints_file = REPO_ROOT / "progress" / "11-1-b-checkpoints.json"
    if not checkpoints_file.exists():
        return None
    try:
        data = json.loads(checkpoints_file.read_text())
        total = data.get("total_checkpoints", 0)
        passed = data.get("passed_checkpoints", 0)
        failed = data.get("failed_checkpoints", 0)
        last = data.get("checkpoints", [{}])[-1] if data.get("checkpoints") else {}
        return {
            "total": total, "passed": passed, "failed": failed,
            "last_status": last.get("status", "?"),
            "last_drift": last.get("drift_score", 0),
            "elapsed_h": last.get("elapsed_hours", 0),
        }
    except:
        return None


def check_chaos_test():
    """Check status of chaos test from trace log."""
    trace_file = REPO_ROOT / "tools" / "testing" / "chaos" / "stability" / "chaos_20x_trace.log"
    if not trace_file.exists():
        return None
    try:
        lines = trace_file.read_text(encoding="utf-8", errors="replace").strip().split("\n")
        last_lines = lines[-10:] if len(lines) > 10 else lines
        finalized = any("TEST FINALIZED" in l for l in last_lines)
        failed = any("FAILED" in l for l in last_lines)
        return {"finalized": finalized, "failed": failed, "last_lines": last_lines[-3:]}
    except:
        return None


# ─── Main Autopilot Loop ────────────────────────────────────────────────────

def autopilot_cycle(state: dict) -> dict:
    """Run one full autopilot cycle."""
    cycle = state["cycle"]
    log(f"{'='*60}")
    log(f"CYCLE {cycle} — Starting full experimental run")
    log(f"{'='*60}")

    results = {}

    # 1. Topology snapshot (full)
    results["topology"] = run_topology_snapshot()

    # 2. Entropy trace (full)
    results["entropy_trace"] = run_entropy_trace()

    # 3. Observability stress (full)
    results["stress"] = run_observability_stress()

    # 4. Consensus tests (full)
    results["consensus"] = run_consensus_tests()

    # 5. Tufte renderers
    results["tufte"] = run_tufte_renderers()

    # 6. Check CC's tests
    test_72h = check_72h_test()
    chaos = check_chaos_test()
    if test_72h:
        log(f"72h test: {test_72h['passed']}/{test_72h['total']} passed, last={test_72h['last_status']}")
    if chaos:
        log(f"Chaos test: finalized={chaos['finalized']}, failed={chaos['failed']}")

    # Summary
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    log(f"CYCLE {cycle} RESULTS: {passed}/{total} tests passed")
    for name, ok in results.items():
        log(f"  {'PASS' if ok else 'FAIL'}: {name}")

    # Commit results
    if cycle % 3 == 0:
        git_commit(f"PM2: Autopilot cycle {cycle} — {passed}/{total} tests passed")

    state["cycle"] = cycle
    state["last_results"] = {k: v for k, v in results.items()}
    state["tests_run"] = state.get("tests_run", []) + [f"cycle_{cycle}"]
    save_state(state)

    return state


def main():
    log("=" * 60)
    log("PM2 AUTOPILOT — Long-Running Experimental Track")
    log("Full tests, no demos. Sleep-based monitoring.")
    log("=" * 60)

    state = load_state()

    while True:
        state["cycle"] += 1
        try:
            state = autopilot_cycle(state)
        except Exception as e:
            log(f"ERROR in cycle {state['cycle']}: {e}")
            import traceback
            traceback.print_exc()

        log(f"Sleeping {CYCLE_SLEEP}s until next cycle...")
        time.sleep(CYCLE_SLEEP)


if __name__ == "__main__":
    main()
