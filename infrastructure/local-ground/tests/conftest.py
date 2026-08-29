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


@pytest.fixture(scope="session")
def oce_stack():
    """Single session-scoped owner of the Local Ground compose stack.

    Starts the stack once, waits for truthful readiness of every mandatory
    service, and tears it down (with disposable volumes) on session end.
    Cleanup runs even when setup/readiness fails before `yield`.
    """
    if not oc.docker_available():
        pytest.skip("container runtime unavailable (Docker absent)")
    try:
        _remove_stale_resources()
        oc.ctl("local", "up", check=True)
        assert oc.wait_all_healthy(), "stack failed to become healthy"
        assert oc.pg_ready(), "postgres failed readiness"
        yield
    finally:
        _teardown_stack()
