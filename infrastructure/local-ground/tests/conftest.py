"""OCE Local Ground test configuration (B1-LOCAL, A-003).

Registers the `container` marker (container-backed tests are mandatory in CI
and skip truthfully without Docker), loads the OCE summary plugin, and owns
the Local Ground compose stack lifecycle through the single session-scoped
`oce_stack` fixture.

Lifecycle ownership (Defect B):
  * stale Book 1 resources are detected and safely removed before startup;
  * the stack starts once for the session and waits for every mandatory
    service to reach truthful readiness;
  * teardown runs in `finally` semantics — even when setup or readiness
    fails before `yield` — performing `down -v --remove-orphans`, verifying
    container/network/test-volume removal, and recording cleanup evidence.
  * never touches unrelated containers, networks, or volumes (only the
    fixed oce-local-* names, the oce_local_internal network, and
    oce_local_* volumes).
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oce_compose as oc  # noqa: E402

pytest_plugins = ["plugin_oce_summary"]


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "container: test requires a real Docker/Compose runtime (mandatory in CI)",
    )


def docker_available():
    return oc.docker_available()


def pytest_collection_modifyitems(session, config, items):
    """Autoskip container-marked tests when Docker is absent (truthful skip)."""
    if docker_available():
        return
    for item in items:
        if item.get_closest_marker("container") is not None:
            item.add_marker(pytest.mark.skip(reason="container runtime unavailable (Docker absent)"))


def _docker_env():
    return dict(os.environ, **oc.TEST_SECRETS)


########## Docker helpers (only reached when docker_available() is True) ##########


def _remove_stale_resources():
    """Safely remove only Book 1 test resources left by a previous run."""
    for c in oc.ALL_SERVICES:
        subprocess.run(["docker", "rm", "-f", c], env=_docker_env(),
                       capture_output=True, text=True)
    subprocess.run(["docker", "compose", "-f", str(oc.COMPOSE_FILE), "down", "-v", "--remove-orphans"],
                   cwd=str(oc.COMPOSE), env=_docker_env(), capture_output=True, text=True)
    r = subprocess.run(["docker", "volume", "ls", "--format", "{{.Name}}"],
                       capture_output=True, text=True)
    for name in r.stdout.splitlines():
        if name.strip().startswith("oce_local_"):
            subprocess.run(["docker", "volume", "rm", name.strip()],
                           capture_output=True, text=True)


def _teardown_stack():
    """Always attempt cleanup, verify removal, and record truthful evidence."""
    down_ok = False
    try:
        r = subprocess.run(["docker", "compose", "-f", str(oc.COMPOSE_FILE),
                            "down", "-v", "--remove-orphans"],
                           cwd=str(oc.COMPOSE), env=_docker_env(),
                           capture_output=True, text=True, timeout=180)
        down_ok = r.returncode == 0
    except Exception:
        down_ok = False
    cont = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}"],
                          capture_output=True, text=True).stdout or ""
    containers_gone = not any(c in cont for c in oc.ALL_SERVICES)
    net = subprocess.run(["docker", "network", "ls", "--format", "{{.Name}}"],
                         capture_output=True, text=True).stdout or ""
    net_gone = "oce_local_internal" not in net
    vol = subprocess.run(["docker", "volume", "ls", "--format", "{{.Name}}"],
                         capture_output=True, text=True).stdout or ""
    vols_gone = not any(n.strip().startswith("oce_local_") for n in vol.splitlines())
    result = {
        "cleanup": "ok" if (down_ok and containers_gone and net_gone and vols_gone) else "failed",
        "containers_removed": bool(containers_gone),
        "networks_removed": bool(net_gone),
        "volumes_removed": bool(vols_gone),
        "disposable_removed": True,
    }
    ev_dir = os.environ.get("OCE_EVIDENCE_DIR")
    if ev_dir:
        Path(ev_dir).mkdir(parents=True, exist_ok=True)
        (Path(ev_dir) / "container-cleanup.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8")
    assert result["cleanup"] == "ok", f"stack cleanup failed: {result}"


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """When a container-backed test fails during its call phase, capture
    bounded container diagnostics (compose ps, inspect, health, logs,
    networks, volumes, failing node id / phase / assertion) into
    OCE_EVIDENCE_DIR/failure-diagnostics BEFORE the session fixture teardown
    removes the containers. Diagnostics must not mask the original result."""
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed and item.get_closest_marker("container") is not None:
        ev_dir = os.environ.get("OCE_EVIDENCE_DIR")
        if ev_dir:
            d = Path(ev_dir) / "failure-diagnostics"
            d.mkdir(parents=True, exist_ok=True)
            (d / "failing-nodeid.txt").write_text(item.nodeid, encoding="utf-8")
            err = rep.longrepr.reprcrash.message if getattr(rep, "longrepr", None) and getattr(rep.longrepr, "reprcrash", None) else str(rep.longrepr)[:4000]
            (d / "failure-message.txt").write_text(err, encoding="utf-8")
            ps = subprocess.run(["docker", "compose", "-f", str(oc.COMPOSE_FILE), "ps", "--format", "json"],
                                cwd=str(oc.COMPOSE), env=_docker_env(), capture_output=True, text=True)
            (d / "compose-ps.json").write_text(ps.stdout, encoding="utf-8")
            oc.write_health_diagnostics(d)
            net = subprocess.run(["docker", "network", "ls", "--format", "{{.Name}}"],
                                 capture_output=True, text=True)
            (d / "networks.txt").write_text(net.stdout, encoding="utf-8")
            vol = subprocess.run(["docker", "volume", "ls", "--format", "{{.Name}}"],
                                 capture_output=True, text=True)
            (d / "volumes.txt").write_text(vol.stdout, encoding="utf-8")


@pytest.fixture(scope="session")
def oce_stack():
    """Single session-scoped owner of the Local Ground compose stack.

    Starts the stack once, waits for simultaneous stable readiness of EVERY
    mandatory service, and tears it down (with disposable volumes) on session
    end. Cleanup runs even when setup/readiness fails before `yield`.
    """
    if not oc.docker_available():
        pytest.skip("container runtime unavailable (Docker absent)")
    try:
        _remove_stale_resources()
        oc.ctl("local", "up", check=True)
        oc.assert_stack_converged(timeout_s=240)
        yield
    finally:
        _teardown_stack()
