"""Book 3 — persistent local worker supervisor (B3-C7, B3-R4).

A supervisor is the operator's handle on the local worker fabric: it
configure/admit/start/drain/status/pause/resume/restart/revoke/stop/doctor/
cleanup workers and exposes an operator console view.

B3-R4 — PERSISTENT across CLI process invocations:

* configuration and admission are written to a state file under the runtime
  dir (JSON, 0600) and reloaded on every fresh supervisor, so
  ``worker configure`` in one invocation is visible to ``worker admit``,
  ``worker start``, ``worker status``, etc. in later invocations.
* the operator-admitted capability catalogue and every admitted worker
  identity survive a supervisor/CLI restart.
* a stale PID file (recorded pid no longer runs, or the pid was reused by an
  unrelated process) is detected and cleaned without ever signalling the new
  owner.

Process ownership is runtime-owned PID files ONLY — never broad ``pkill``.
Ordinary cleanup preserves durable accepted artifacts, PostgreSQL state, and
the required configuration.
"""
from __future__ import annotations
import json
import os
import signal
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .worker_contracts import utcnow_iso
from .worker_identity import WorkerAuthority, AdmissionRequest, \
    WorkerIdentity, CapabilityRegistry
from .worker_sessions import SessionHost

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

    @classmethod
    def from_dict(cls, d: dict) -> "WorkerRecord":
        return cls(
            worker_id=d["worker_id"], command=list(d.get("command", [])),
            pid=d.get("pid"), state=d.get("state", "configured"),
            started_at=d.get("started_at", utcnow_iso()),
            capabilities=list(d.get("capabilities", [])),
        )


class WorkerSupervisor:
    """Owns local worker processes, their runtime-pid registry, and the
    persisted operator configuration/admission catalogue."""

    STATE_FILE = "state.json"

    def __init__(self, runtime_dir: Path, authority: WorkerAuthority,
                 host: Optional[SessionHost] = None):
        self._dir = Path(runtime_dir)
        self._pid_dir = self._dir / "pids"
        self._pid_dir.mkdir(parents=True, exist_ok=True)
        self._state_file = self._dir / self.STATE_FILE
        self._authority = authority
        self._host = host or SessionHost()
        self._workers: dict[str, WorkerRecord] = {}
        self._procs: dict[str, subprocess.Popen] = {}
        self._admitted: set[str] = set()
        self._load_state()          # durable config/admission across processes
        self._load_existing_pids()

    # -- persistence (B3-R4: state survives CLI process boundaries) -----------

    def _load_state(self) -> None:
        if not self._state_file.exists():
            return
        try:
            data = json.loads(self._state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        for rec in data.get("workers", []):
            wr = WorkerRecord.from_dict(rec)
            # pid is not authoritative across processes; recompute on status.
            wr.pid = None
            self._workers[wr.worker_id] = wr
        for wid in data.get("admitted", []):
            self._admitted.add(wid)
            # rebuild the admitted identity so the authority carries it
            rec = self._workers.get(wid)
            caps = rec.capabilities if rec else list(data.get("capabilities", []))
            ident = WorkerIdentity(
                worker_id=wid, admission_nonce=("adm-" + wid).ljust(16, "0"),
                protocol_version="1.0", host_os_class=_os_class(),
                runtime_class="python", trust_zone="worker-local",
                worker_version="1.0", capabilities=tuple(caps),
                sandbox_profile="default",
            )
            self._authority._identities[wid] = ident  # adopted identity
        for cap in data.get("capabilities", []):
            try:
                self._authority.registry.admit_capability(cap, "operator:po")
            except Exception:
                pass

    def _save_state(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        data = {
            "workers": [w.to_dict() for w in self._workers.values()],
            "admitted": sorted(self._admitted),
            "capabilities": self._authority.registry.admitted(),
            "saved_at": utcnow_iso(),
        }
        tmp = self._state_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self._state_file)
        try:
            self._state_file.chmod(0o600)
        except OSError:
            pass

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
        if os.name == "nt":
            # os.kill(pid, 0) is a no-op/wrong on Windows (SystemError for a
            # dead pid). Probe the command line: empty -> not alive.
            try:
                return bool(_cmdline(pid))
            except Exception:
                return False
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
        except Exception:
            return False

    def _stale_pids(self) -> list[str]:
        stale = []
        for pf in self._pid_dir.glob("*.pid"):
            try:
                pid = int(pf.read_text(encoding="utf-8").strip())
            except (ValueError, OSError):
                stale.append(pf.stem)
                continue
            rec = self._workers.get(pf.stem)
            expected = rec.command[0] if rec and rec.command else ""
            # PID reuse protection: if this pid is alive but does not belong to
            # our expected interpreter, treat the file as stale (never signal).
            if not self._process_alive(pid):
                stale.append(pf.stem)
                continue
            if expected and expected not in _cmdline(pid):
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
        reports["configured_workers"] = sorted(self._workers)
        reports["warnings"] = []
        if not self._admitted:
            reports["warnings"].append("no workers admitted yet; run worker admit")
        if not self._workers:
            reports["warnings"].append("no workers configured; run worker configure")
        return reports

    def configure(self, worker_id: str, command: list[str],
                  capabilities: Optional[list[str]] = None, actor: str = "operator:po") -> WorkerRecord:
        caps = list(capabilities or BOOTSTRAP_CAPABILITIES)
        rec = WorkerRecord(worker_id=worker_id, command=command, capabilities=caps)
        self._workers[worker_id] = rec
        # Configuration alone does not admit; admission is a PO action.
        self._save_state()
        return rec

    def admit(self, worker_id: str, requested: Optional[list[str]] = None,
              actor: str = "operator:po") -> WorkerIdentity:
        """PO-authorized admission. A worker cannot self-authorize."""
        if actor != "operator:po":
            raise PermissionError(
                f"actor '{actor}' cannot admit workers — only operator:po (or a "
                f"permitted PO proxy) may admit a worker")
        rec = self._workers.get(worker_id)
        caps = list(requested or (rec.capabilities if rec else []))
        # unknown/unadmitted capabilities fail closed
        for cap in caps:
            if not self._authority.registry.is_admitted(cap):
                raise PermissionError(f"capability '{cap}' is not operator-admitted")
        req = AdmissionRequest(
            worker_id=worker_id,
            public_key_or_nonce=("adm-" + worker_id).ljust(16, "0"),
            requested_capabilities=caps,
            protocol_version="1.0",
            host_os_class=_os_class(),
            runtime_class="python", trust_zone="worker-local", worker_version="1.0",
        )
        ident = self._authority.approve(req, actor)
        self._admitted.add(worker_id)
        if rec:
            rec.state = "admitted"
            rec.capabilities = caps
            rec.command = rec.command or [sys.executable]
        self._save_state()
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
        env = dict(os.environ)
        proc = subprocess.Popen(rec.command, cwd=str(self._dir), env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._procs[worker_id] = proc
        self._write_pid(worker_id, proc.pid)
        rec.pid = proc.pid
        rec.state = "running"
        rec.started_at = utcnow_iso()
        self._save_state()
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
            self._save_state()
        return rec

    def resume(self, worker_id: str) -> WorkerRecord:
        rec = self._authorize(worker_id)
        if rec.state == "paused":
            rec.state = "running" if self._process_alive(rec.pid) else "stopped"
            self._save_state()
        return rec

    def drain(self, worker_id: str) -> WorkerRecord:
        rec = self._authorize(worker_id)
        rec.state = "draining"
        self._host.set_draining(worker_id, True)
        self._save_state()
        return rec

    def revoke(self, worker_id: str, actor: str = "operator:po") -> WorkerRecord:
        if actor != "operator:po":
            raise PermissionError(f"actor '{actor}' cannot revoke workers")
        rec = self._authorize(worker_id)
        self._host.revoke(worker_id)
        self._admitted.discard(worker_id)
        self._authority.revoke_identity(worker_id, actor)
        rec.state = "stopped"
        self._save_state()
        return rec

    def stop(self, worker_id: str) -> WorkerRecord:
        rec = self._workers.get(worker_id)
        if rec is None:
            raise KeyError(f"no worker '{worker_id}'")
        pid = self._read_pid(worker_id) or rec.pid
        # PID-reuse safety: only signal a live pid whose command line matches
        # this worker's expected interpreter. Never signal an unrelated process
        # that happened to reuse the pid.
        expected = rec.command[0] if rec.command else ""
        if (pid and self._process_alive(pid)
                and (not expected or expected in _cmdline(pid))):
            try:
                os.kill(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                pass
        self._procs.pop(worker_id, None)
        self._clear_pid(worker_id)
        rec.pid = None
        rec.state = "stopped"
        self._save_state()
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
                "artifacts_preserved": True, "state_preserved": True}

    def workers(self):
        return dict(self.status())

    def up(self, worker_id: str) -> WorkerRecord:
        """Start a not-yet-admitted configured worker after admission smoke."""
        return self.start(worker_id)

    # -- console views (B3-C7 operator console) --------------------------------

    def operator_view(self) -> dict:
        return {
            "admitted": sorted(self._admitted),
            "capabilities": self._authority.registry.admitted(),
            "sessions": [s for w in self._admitted for s in self._host.sessions(w)],
            "workers": self.status(),
            "doctor": self.doctor(),
            "state_file": str(self._state_file),
            "cloud": "dormant",
        }

    def _load_existing_pids(self) -> None:
        # Adopt our own recorded pids as the running set on restart, but ONLY
        # when the pid file belongs to a CONFIGURED worker AND the live pid
        # truly matches our expected interpreter command line (PID-reuse /
        # alien-pid safe). A pid file with no configured worker must never be
        # adopted: adoption would later let stop()/cleanup() signal an
        # unrelated process. It is stale and handled by cleanup().
        for pf in self._pid_dir.glob("*.pid"):
            pid = self._read_pid(pf.stem)
            rej = self._workers.get(pf.stem)
            if rej is None or not rej.command:
                continue
            expected = rej.command[0]
            if (pid and self._process_alive(pid)
                    and expected in _cmdline(pid)):
                rec = self._workers[pf.stem]
                rec.pid = pid
                rec.state = "running"


def _os_class() -> str:
    return {"nt": "windows", "posix": "linux"}.get(os.name, os.name)


def _cmdline(pid: int) -> str:
    """Best-effort command-line for PID-reuse safety. Empty on unknown."""
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
        if raw:
            return raw.replace(b"\0", b" ").decode("utf-8", "replace")
    except OSError:
        pass
    try:
        r = subprocess.run(["ps", "-p", str(pid), "-o", "args="],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-CimInstance Win32_Process -Filter \"ProcessId={pid}\").CommandLine"],
            capture_output=True, text=True, timeout=15)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return ""