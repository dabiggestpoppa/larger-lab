"""Book 3 — local worker supervisor and operator controls (B3-C7)."""
from __future__ import annotations
import pathlib
import sys
import time
import pytest

from oce_control.worker_identity import WorkerAuthority, CapabilityRegistry
from oce_control.worker_supervisor import WorkerSupervisor, BOOTSTRAP_CAPABILITIES


@pytest.fixture
def sup(tmp_path):
    reg = CapabilityRegistry()
    for cap in BOOTSTRAP_CAPABILITIES:
        reg.admit_capability(cap, "operator:po")
    au = WorkerAuthority(reg)
    return WorkerSupervisor(tmp_path / "runtime", au)


class TestSupervisor:
    def test_configure_and_po_admit(self, sup):
        sup.configure("wkr-x", command=[sys.executable, "-c", "pass"])
        ident = sup.admit("wkr-x", actor="operator:po")
        assert ident.worker_id == "wkr-x"
        assert set(ident.capabilities).issubset(set(sup._authority.registry.admitted()))
        assert "wkr-x" in sup.operator_view()["admitted"]

    def test_worker_cannot_self_authorize(self, sup):
        # a worker has no right to approve its own admission
        assert not sup._authority.identities()
        with pytest.raises(PermissionError):
            sup._authorize("not-admitted")

    def test_start_stop_runtime_owned_pid(self, sup):
        sup.configure("wkr-y", command=[sys.executable, "-c", "import time; time.sleep(60)"])
        sup.admit("wkr-y")
        sup.start("wkr-y")
        pid = sup._read_pid("wkr-y")
        assert pid and pid > 0
        assert (sup._pid_dir / "wkr-y.pid").exists()
        st = sup.status("wkr-y")
        assert st["alive"] is True
        sup.stop("wkr-y")
        assert not (sup._pid_dir / "wkr-y.pid").exists()
        st = sup.status("wkr-y")
        assert st["alive"] is False
        assert st["state"] == "stopped"

    def test_stale_pid_detected(self, sup):
        (sup._pid_dir / "ghost.pid").write_text("99999999", encoding="utf-8")
        report = sup.doctor()
        assert "ghost" in report["stale_pids"]
        assert report["ok"] is False

    def test_revoke_drops_admission_and_sessions(self, sup):
        sup.configure("wkr-z", command=[sys.executable, "-c", "pass"])
        sup.admit("wkr-z")
        sup.drain("wkr-z")
        assert sup.status("wkr-z")["state"] == "draining"
        sup.revoke("wkr-z")
        assert "wkr-z" not in sup._admitted
        assert sup._authority.get("wkr-z") is None

    def test_doctor_warns_on_no_admitted_workers(self, sup):
        report = sup.doctor()
        assert any("no workers admitted" in w for w in report["warnings"])

    def test_cleanup_preserves_artifacts_and_pid_state(self, sup):
        arts = pathlib.Path("artifacts-cas")
        (sup._pid_dir / "stale.pid").write_text("5", encoding="utf-8")
        result = sup.cleanup(preserve_artifacts_dir=arts)
        assert result["cleanup"] is True
        assert result["artifacts_preserved"] is True

    def test_operator_view_shows_fabric_state(self, sup):
        view = sup.operator_view()
        assert "admitted" in view and "capabilities" in view
        assert "sessions" in view and "workers" in view
        assert view["cloud"] == "dormant"