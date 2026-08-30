"""Book 3 — local worker supervisor and operator controls (B3-C7).

A supervisor is the operator's handle on the local worker fabric: it
admit/start/drain/status/pause/resume/restart/revoke/stop workers, runs a
doctor, and cleans up disposable state — preserving durable accepted
artifacts and PostgreSQL state during ordinary cleanup.

Process ownership uses RUNTIME-OWNED PID files, never broad ``pkill -f``:
the supervisor only ever terminates PIDs that it itself recorded. Stale PID
files are detected (the recorded PID is no longer running) and cleaned.
"""
from __future__ import annotations
import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .worker_contracts import utcnow_iso
from .worker_identity import WorkerAuthority, AdmissionRequest, WorkerIdentity
from .worker_sessions import SessionHost, SessionRevoked, WorkerDraining

# Capabilities the local operator bootstraps for the local worker (Po-admitted).
BOOTSTRAP_CAPABILITIES = ("hash", "compute-python", "repo-inventory",
                          "backtest-synthetic", "analysis-artifact",
                          "file-read", "report-html")

@dataclass
class WorkerRecord:
    worker_id: str
    command: list[str]
    pid: Optional[int] = None
    state: str = "configured"     # configured|admitted|running|paused|draining|stopped
    started_at: str = field(default_factory=utcnow_iso)
    capabilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "worker_id": self.worker_id, "pid": self.pid, "state": self.state,
            "started_at": self.started_at, "capabilities": list(self.capabilities),
            "command": list(self.command),
        }


class WorkerSupervisor:
    """Owns local worker processes and their runtime-pid registry."""

    def __init__(self, runtime_dir: Path, authority: WorkerAuthority,
                 host: Optional[SessionHost] = None):
        self._dir = Path(runtime_dir)
        self._pid_dir = self._dir / "pids"
        self._pid_dir.mkdir(parents=True, exist_ok=True)
        self._authority = authority
        self._host = host or SessionHost()
        self._workers: dict[str, WorkerRecord] = {}
        self._procs: dict[str, subprocess.Popen] = {}
        self._admitted: set[str] = set()
        self._load_existing()

    # -- filesystem helpers -----------------------------------------------------

    def _pid_file(self, worker_id: str) -> Path:
        return self._pid_dir / f"{worker_id}.pid"

    def _read_pid(self, worker_id: str) -> Optional[int]:
        pf = self._pid_file(worker_id)
        if pf.exists():
            try:
                return int(pf.read_text(encoding="utf-8").strip())
            except (ValueError, OSError):
                return None
        return None

    def _write_pid(self, worker_id: str, pid: int) -> None:
        pf = self._pid_file(worker_id)
        tmp = pf.with_suffix(".pid.tmp")
        tmp.write_text(str(pid), encoding="utf-8")
        tmp.replace(pf)

    def _clear_pid(self, worker_id: str) -> None:
        self._pid_file(worker_id).unlink(missing_ok=True)

    def _process_alive(self, pid: Optional[int]) -> bool:
        if not pid:
            return False
        try:
            os.kill(pid, 0)     # liveness probe (no kill)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False

    def _stale_pids(self) -> list[str]:
        stale = []
        for pf in self._pid_dir.glob("*.pid"):
            try:
                pid = int(pf.read_text(encoding="utf-8").strip())
            except (ValueError, OSError):
                stale.append(pf.stem)
                continue
            if not self._process_alive(pid):
                stale.append(pf.stem)
        return stale

    # -- lifecycle commands -----------------------------------------------------

    def doctor(self) -> dict:
        reports = {"stale_pids": [], "admitted_workers": [], "ok": True}
        stale = self._stale_pids()
        reports["stale_pids"] = stale
        if stale:
            reports["ok"] = False
        reports["admitted_workers"] = sorted(self._admitted)
        reports["warnings"] = []
        if not self._authority.identities():
            reports["warnings"].append("no workers admitted yet; run worker admit")
        return reports

    def configure(self, worker_id: str, command: list[str],
                  capabilities: Optional[list[str]] = None) -> WorkerRecord:
        rec = WorkerRecord(worker_id=worker_id, command=command,
                           capabilities=list(capabilities or BOOTSTRAP_CAPABILITIES))
        self._workers[worker_id] = rec
        return rec

    def admit(self, worker_id: str, requested: Optional[list[str]] = None,
              actor: str = "operator:po") -> WorkerIdentity:
        """PO-authorized admission. A worker cannot self-authorize."""
        rec = self._workers.get(worker_id)
        caps = (requested or (rec.capabilities if rec else []))
        req = AdmissionRequest(
            worker_id=worker_id,
            public_key_or_nonce=("adm-" + worker_id).ljust(16, "0"),
            requested_capabilities=caps,
            protocol_version="1.0",
            host_os_class={"nt": "windows", "posix": "linux"}.get(os.name, os.name),
            runtime_class="python", trust_zone="worker-local", worker_version="1.0",
        )
        ident = self._authority.approve(req, actor)
        self._admitted.add(worker_id)
        if rec:
            rec.state = "admitted"
            rec.capabilities = caps
        return ident

    def _authorize(self, worker_id: str) -> WorkerRecord:
        if worker_id not in self._admitted:
            raise PermissionError(f"worker '{worker_id}' is not admitted")
        rec = self._workers.get(worker_id)
        if rec is None:
            raise KeyError(f"no worker configured: '{worker_id}'")
        return rec

    def start(self, worker_id: str) -> WorkerRecord:
        rec = self._authorize(worker_id)
        if rec.state == "running" and self._process_alive(rec.pid):
            return rec
        # runtime-owned PID: launch the worker command ourselves
        env = dict(os.environ)
        proc = subprocess.Popen(rec.command, cwd=str(self._dir),
                                env=env, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        self._procs[worker_id] = proc
        self._write_pid(worker_id, proc.pid)
        rec.pid = proc.pid
        rec.state = "running"
        rec.started_at = utcnow_iso()
        return rec

    def status(self, worker_id: Optional[str] = None) -> object:
        if worker_id is not None:
            rec = self._workers.get(worker_id)
            if rec is None:
                return None
            alive = self._process_alive(rec.pid)
            if rec.state == "running" and not alive:
                rec.state = "stopped"
                rec.pid = None
            return {**rec.to_dict(), "alive": alive}
        out = {}
        for wid in sorted(self._workers):
            rec = self._workers[wid]
            alive = self._process_alive(rec.pid)
            out[wid] = {**rec.to_dict(), "alive": alive}
        return out

    def pause(self, worker_id: str) -> WorkerRecord:
        rec = self._authorize(worker_id)
        if rec.state in ("running", "paused"):
            rec.state = "paused"
        return rec

    def resume(self, worker_id: str) -> WorkerRecord:
        rec = self._authorize(worker_id)
        if rec.state == "paused":
            rec.state = "running" if self._process_alive(rec.pid) else "stopped"
        return rec

    def drain(self, worker_id: str) -> WorkerRecord:
        rec = self._authorize(worker_id)
        rec.state = "draining"
        self._host.set_draining(worker_id, True)
        return rec

    def revoke(self, worker_id: str) -> WorkerRecord:
        rec = self._authorize(worker_id)
        self._host.revoke(worker_id)
        self._admitted.discard(worker_id)
        self._authority.revoke_identity(worker_id, "operator:po")
        rec.state = "stopped"
        return rec

    def stop(self, worker_id: str) -> WorkerRecord:
        rec = self._workers.get(worker_id)
        if rec is None:
            raise KeyError(f"no worker '{worker_id}'")
        pid = self._read_pid(worker_id) or rec.pid
        if pid and self._process_alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                pass
        self._procs.pop(worker_id, None)
        self._clear_pid(worker_id)
        rec.pid = None
        rec.state = "stopped"
        return rec

    def restart(self, worker_id: str) -> WorkerRecord:
        self.stop(worker_id)
        return self.start(worker_id)

    def cleanup(self, preserve_artifacts_dir: Optional[Path] = None) -> dict:
        """Clean disposable state, PRESERVING durable artifacts storage and any
        authoritative PostgreSQL state (handled by the control plane)."""
        for worker_id in list(self._workers):
            try:
                self.stop(worker_id)
            except Exception:
                pass
        removed = []
        for pf in self._pid_dir.glob("*.pid"):
            pf.unlink(missing_ok=True)
            removed.append(pf.name)
        return {"cleanup": True, "removed_pid_files": removed,
                "artifacts_preserved": True}

    def workers(self):
        return dict(self.status())

    # -- console views (B3-C7 operator console) --------------------------------

    def operator_view(self) -> dict:
        return {
            "admitted": sorted(self._admitted),
            "capabilities": self._authority.registry.admitted(),
            "sessions": [s for w in self._admitted for s in self._host.sessions(w)],
            "workers": self.status(),
            "doctor": self.doctor(),
            "cloud": "dormant",
        }

    def _load_existing(self) -> None:
        # adopt our own recorded pids as the running set on restart
        for pf in self._pid_dir.glob("*.pid"):
            pid = self._read_pid(pf.stem)
            if pid and self._process_alive(pid):
                rec = WorkerRecord(worker_id=pf.stem, command=[],
                                   pid=pid, state="running")
                self._workers[pf.stem] = rec