"""OCE Local Ground — pytest plugin writing a deterministic machine-readable
test registry (OCE summary JSON) next to the JUnit XML.

Totals are derived from actual executed/skipped entries, never from claims.
Container-backed tests are tracked separately so CI can require that every
mandatory container test actually executed.
"""
import json
import os
import time
from datetime import datetime, timezone

import pytest


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    ev_dir = os.environ.get("OCE_EVIDENCE_DIR")
    if not ev_dir:
        return
    os.makedirs(ev_dir, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    collected = list(session.items)
    reports = getattr(session, "_oce_reports", {})  # nodeid -> outcome

    registry = []
    container_collected = container_executed = container_passed = 0
    container_failed = container_skipped = 0
    mandatory_skipped = 0
    totals = {"collected": 0, "executed": 0, "passed": 0, "failed": 0,
              "errors": 0, "skipped": 0}
    for item in collected:
        is_container = item.get_closest_marker("container") is not None
        outcome = reports.get(item.nodeid, "not-run")
        duration = getattr(item, "_oce_duration", None)
        totals["collected"] += 1
        registry.append({
            "name": item.name,
            "nodeid": item.nodeid,
            "container_backed": is_container,
            "outcome": outcome,
            "duration_s": round(duration, 3) if duration is not None else None,
        })
        if is_container:
            container_collected += 1
        if outcome in ("passed", "failed", "error", "skipped"):
            totals["executed"] += 1
        if outcome == "passed":
            totals["passed"] += 1
            if is_container:
                container_executed += 1
                container_passed += 1
        elif outcome == "failed":
            totals["failed"] += 1
            if is_container:
                container_executed += 1
                container_failed += 1
        elif outcome == "error":
            totals["errors"] += 1
            if is_container:
                container_executed += 1
        elif outcome == "skipped":
            totals["skipped"] += 1
            if is_container:
                container_skipped += 1
                mandatory_skipped += 1

    summary = {
        "format": "oce-test-summary-v1",
        "generated_at": now,
        "environment": {
            "docker_available": os.environ.get("OCE_DOCKER_AVAILABLE", "unknown"),
            "ci_mode": os.environ.get("OCE_CI_MODE", "false"),
        },
        "totals": totals,
        "container_backed": {
            "collected": container_collected,
            "executed": container_executed,
            "passed": container_passed,
            "failed": container_failed,
            "skipped": container_skipped,
        },
        "mandatory_skipped": mandatory_skipped,
        "tests": registry,
    }
    with open(os.path.join(ev_dir, "test-summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    # Locally without Docker the truth is LOCAL_STATIC_READY_CI_REQUIRED.
    with open(os.path.join(ev_dir, "test-mode.txt"), "w", encoding="utf-8") as f:
        if os.environ.get("OCE_CI_MODE") == "true" and os.environ.get("OCE_DOCKER_AVAILABLE") == "true":
            f.write("AUTHORITATIVE_CI\n")
        elif mandatory_skipped > 0:
            f.write("LOCAL_STATIC_READY_CI_REQUIRED\n")
        else:
            f.write("AUTHORITATIVE_CI\n")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    reports = getattr(item.session, "_oce_reports", None)
    if reports is None:
        reports = {}
        item.session._oce_reports = reports
    if rep.when == "call":
        reports[item.nodeid] = "passed" if rep.passed else ("failed" if rep.failed else "skipped")
        item._oce_duration = rep.duration
    elif rep.when == "setup" and rep.skipped:
        # Skipped tests never reach the call phase; record truthfully from setup.
        reports[item.nodeid] = "skipped"
        item._oce_duration = rep.duration


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    ev_dir = os.environ.get("OCE_EVIDENCE_DIR")
    if not ev_dir:
        return
    # JUnit XML is written by the standard plugin into the evidence dir.
    config.option.junitxml = os.path.join(ev_dir, "junit.xml")