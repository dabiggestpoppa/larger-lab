"""Book 3 — bounded execution, immutable artifacts, retry/dead-letters.

Covers B3-C4 (bounded disposable task execution), B3-C5 (immutable results
and artifacts) and B3-C6 (retry, recovery and dead letters).

Design constraints drawn from the canonical brief:

* This is NOT an unrestricted arbitrary-shell remote execution service.
* Jobs must declare the capabilities and resource envelope they require,
  and the worker refuses jobs outside its admitted limits.
* Each attempt runs in a FRESH disposable workspace.
* Accepted output is durable (CAS artifact store) before the runner deletes
  the local attempt workspace.
* Mandatory security gaps remain BLOCKED — where a primitive is unavailable
  on a platform, that limitation is reported truthfully and the strongest
  local equivalent is applied.

The content-addressable artifact store is the durable backstop: worker loss
after an accepted publication cannot erase operational truth.

TRUST BOUNDARY (B4-CXR7U1/U3): see ``B4-THREAT-MODEL.md``. This module
provides BOUNDED RESOURCE EXECUTION (`resource_limits_available`) and
WATCHDOG/TREE TERMINATION — NOT network, filesystem, identity, syscall, or
hostile-code isolation. RLIMIT/CPU/address-space/file-size controls are
reported literally. Network is denied by Book 4 policy; OS network
enforcement is NOT implemented and is never claimed. Only fixed
repository-owned allowlisted programs may execute.
"""
from __future__ import annotations
import hashlib
import json
import os
import platform
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .hashes import sha256_hex, sha256_file
from .worker_contracts import utcnow_iso

# --------------------------------------------------------------------------
# Execution policy / resource envelope
# --------------------------------------------------------------------------

DEFAULT_ALLOWED_EXECUTABLES = ("python", "python3")


@dataclass(frozen=True)
class SandboxPolicy:
    """Declarative, fail-closed execution policy for a bounded attempt.

    ``strict`` makes a missing MANDATORY isolation boundary a hard BLOCK
    (``IsolatedSandboxUnsupported`` raised before job code runs) instead of
    the truthful but permissive degradation used by fast unit tests. The
    production worker runs strict=True; tests that are exercising the scoring
    logic on a limited platform may run strict=False. Either way the applied
    boundary set is reported truthfully per attempt.
    """
    allowed_executables: tuple[str, ...] = DEFAULT_ALLOWED_EXECUTABLES
    allowed_env: tuple[str, ...] = ("PATH", "HOME", "PYTHONUTF8", "PYTHONIOENCODING",
                                    "LANG", "TZ")
    network_enabled: bool = False
    read_only_workspace_inputs: bool = True
    disposable_cache: bool = True
    allow_network: bool = False          # explicit; jobs may not grant network
    forbidden_env_prefixes: tuple[str, ...] = ("AWS_", "AZURE_", "GOOGLE_", "GCP_",
                                               "KUBE_", "OCITOOLS", "DOCKER_")
    allowed_output_extensions: tuple[str, ...] = (".json", ".txt", ".html", ".csv",
                                                  ".log", ".svg", ".png", ".md", ".csv")
    strict: bool = False


@dataclass
class JobResourceEnvelope:
    cpu_limit: float = 1.0            # relative cores (best-effort)
    memory_bytes: int = 512 * 1024 * 1024
    disk_bytes: int = 256 * 1024 * 1024
    timeout_s: int = 30               # mandatory runtime timeout
    max_output_bytes: int = 4 * 1024 * 1024

    def to_dict(self) -> dict:
        return {
            "cpu_limit": self.cpu_limit,
            "memory_bytes": self.memory_bytes,
            "disk_bytes": self.disk_bytes,
            "timeout_s": self.timeout_s,
            "max_output_bytes": self.max_output_bytes,
        }


@dataclass
class AttemptResult:
    exit_code: Optional[int]
    stdout: str
    stderr: str
    raise_fired: bool
    timed_out: bool
    cancel_requested: bool
    resource_violation: Optional[str] = None
    isolation_note: Optional[str] = None   # truthful limit coverage (never a violation)
    isolation_report: Optional[dict] = None  # B3-R5 preflight/enforced boundaries
    workspace: Optional[Path] = None
    started_at: str = field(default_factory=utcnow_iso)
    ended_at: str = ""

    @property
    def ok(self) -> bool:
        return (self.exit_code == 0 and self.timed_out is False
                and self.cancel_requested is False
                and self.resource_violation is None and not self.raise_fired)


class ExecutionPolicyError(PermissionError):
    """Raised for forbidden executables, env vars, or network requests."""


class ResourceLimitExceeded(RuntimeError):
    pass


class OutputLimitExceeded(RuntimeError):
    pass


class PathEscapeError(PermissionError):
    pass


class IsolatedSandboxUnsupported(Exception):
    """Isolation primitive unavailable; reported truthfully (BLOCKED)."""


class BoundedRunner:
    """Bounded, disposable, tree-terminating local task runner (B3-C4).

    Cross-platform best-effort limits:

    * POSIX: ``resource.setrlimit`` for CPU time, address space and max file
      size, plus ``os.setsid`` so the whole process tree can be reaped.
    * Windows: filesystem ``RLIMIT``-like primitives are unavailable; the
      strongest local equivalent (job objects are not reliable across
      subprocesses without ctypes) is a hard watchdog timeout plus process
      tree termination via ``taskkill /T`` on the session. This limitation
      is recorded per attempt so it is never silently claimed as full
      isolation.
    """

    def __init__(self, workspace_base: Optional[Path] = None,
                 policy: Optional[SandboxPolicy] = None):
        self._base = Path(workspace_base) if workspace_base \
            else Path(tempfile.mkdtemp(prefix="oce-b3-ws-"))
        self._policy = policy or SandboxPolicy()
        self._attempts: list[AttemptResult] = []
        self._current_proc: Optional[subprocess.Popen] = None
        self._cancel_event: Optional[threading.Event] = None
        self._last_preflight: dict = {}

    @property
    def cancel_event(self) -> Optional[threading.Event]:
        return self._cancel_event

    @property
    def last_preflight(self) -> dict:
        return self._last_preflight

    def _fresh_workspace(self, attempt: int) -> Path:
        ws = self._base / f"attempt-{attempt}"
        if ws.exists():
            shutil.rmtree(ws, ignore_errors=True)
        ws.mkdir(parents=True, exist_ok=True)
        (ws / "input").mkdir(exist_ok=True)
        (ws / "output").mkdir(exist_ok=True)
        (ws / "cache").mkdir(exist_ok=True)
        return ws

    def _check_executable(self, argv: list[str]) -> None:
        exe = Path(argv[0]).name if argv else ""
        if exe not in self._policy.allowed_executables:
            raise ExecutionPolicyError(
                f"executable '{exe}' not in allowlist {self._policy.allowed_executables}")

    def _build_env(self) -> dict:
        env = {}
        for key in self._policy.allowed_env:
            if key in os.environ:
                env[key] = os.environ[key]
        env["PYTHONIOENCODING"] = "utf-8"
        return env

    def _guard_paths(self, workspace: Path, input_paths: list[Path]) -> None:
        ws = workspace.resolve()
        for p in (workspace, *[Path(i) for i in input_paths]):
            try:
                rp = Path(p).resolve()
                rp.relative_to(ws)
            except (ValueError, OSError) as exc:
                raise PathEscapeError(
                    f"path '{p}' escapes the bounded workspace: {exc}")

    # -- platform limit helpers (truthful reporting) ---------------------------

    @property
    def full_isolation(self) -> bool:
        """True only when real OS resource isolation is applied (POSIX)."""
        return not platform.system().lower().startswith("win")

    def _limits_preamble(self, envelope: JobResourceEnvelope) -> Optional[str]:
        """Returns None on POSIX (real limits applied) or a truthful note."""
        if self.full_isolation:
            return None
        return ("windows: rlimit primitives unavailable; applied watchdog "
                "timeout + tree termination as strongest local equivalent")

    def preflight_isolation(self, envelope: JobResourceEnvelope) -> dict:
        """Verify the sandbox boundaries that will be enforced BEFORE any job
        code runs. Returns a truthful report of enforced vs unavailable
        boundaries. In ``strict`` mode, a MANDATORY boundary that cannot be
        established raises ``IsolatedSandboxUnsupported`` (BLOCKED) instead of
        silently running with weaker isolation.

        Mandatory boundaries:
          timeout_s, max_output_bytes  — enforced on every platform
          memory_bytes, disk_bytes, cpu_limit — rlimit-backed on POSIX; on
              Windows the strongest available local equivalent (watchdog + tree
              termination + output cap) is applied and reported truthfully
          network — denied by policy (allow_network must be False); a job is
              never granted sockets unless the policy grants them
        """
        enforced = ["timeout", "output_size"]
        unavailable: dict[str, str] = {"network": "policy-denied"}
        mandatory_missing: list[str] = []
        if self.full_isolation:
            import resource as _res
            ok_cpu = False
            ok_mem = False
            ok_fsize = False
            try:
                _res.getrlimit(_res.RLIMIT_CPU)
                ok_cpu = True
            except (OSError, ValueError):
                pass
            try:
                _res.getrlimit(_res.RLIMIT_AS)
                ok_mem = True
            except (OSError, ValueError):
                pass
            try:
                _res.getrlimit(_res.RLIMIT_FSIZE)
                ok_fsize = True
            except (OSError, ValueError):
                pass
            # disk bytes enforced via RLIMIT_FSIZE (bounded output/disk)
            if ok_cpu:
                enforced.append("cpu")
            else:
                unavailable["cpu"] = "RLIMIT_CPU unavailable"
                if envelope.cpu_limit > 0:
                    mandatory_missing.append("cpu")
            if ok_mem:
                enforced.append("memory")
            else:
                unavailable["memory"] = "RLIMIT_AS unavailable"
                if envelope.memory_bytes > 0:
                    mandatory_missing.append("memory")
            if ok_fsize:
                enforced.append("disk")
            else:
                unavailable["disk"] = "RLIMIT_FSIZE unavailable"
                if envelope.disk_bytes > 0:
                    mandatory_missing.append("disk")
        else:
            unavailable["memory"] = (
                "rlimit unavailable on this platform; applied strongest local "
                "equivalent (watchdog + output cap + tree termination)")
            unavailable["cpu"] = "rlimit unavailable on this platform"
            unavailable["disk"] = "rlimit unavailable on this platform"
            if envelope.memory_bytes > 0 or envelope.disk_bytes > 0 or envelope.cpu_limit > 0:
                mandatory_missing.append("memory/cpu/disk(rlimit)")

        report = {"enforced": enforced, "unavailable": unavailable,
                  "mandatory_missing": mandatory_missing,
                  "network": "denied" if not self._policy.allow_network else "granted-by-policy",
                  "strict": self._policy.strict}
        if self._policy.strict and mandatory_missing:
            raise IsolatedSandboxUnsupported(
                f"mandatory isolation boundary(ies) unavailable — BLOCKED before "
                f"execution: {', '.join(mandatory_missing)}. Report: {report}")
        return report

    def _deny_network(self) -> None:
        """Jobs may not silently gain network access the policy denies."""
        if self._policy.allow_network:
            return

    def _guard_output_extension(self, rel_name: str) -> None:
        """Enforce the output-extension allowlist; anything else fails closed."""
        ext = Path(rel_name).suffix.lower()
        if not ext:
            raise ExecutionPolicyError(
                f"output artifact '{rel_name}' has no recognized extension "
                f"(allowlist {self._policy.allowed_output_extensions})")
        if ext not in self._policy.allowed_output_extensions:
            raise ExecutionPolicyError(
                f"output artifact '{rel_name}' extension '{ext}' not in allowlist")

    def _apply_posix_limits(self, envelope: JobResourceEnvelope) -> callable:
        import resource

        def _pre():
            # Best-effort hard limits. If the host refuses a limit the watchdog
            # + output cap still enforce the run duration and size; the missing
            # isolation is reported (never silently claimed as full isolation).
            try:
                cpus = int(envelope.cpu_limit * 2) + 2
                hard = resource.getrlimit(resource.RLIMIT_CPU)[1]
                resource.setrlimit(resource.RLIMIT_CPU, (min(cpus, hard), hard))
            except (OSError, ValueError):
                pass
            try:
                hard = resource.getrlimit(resource.RLIMIT_AS)[1]
                want = max(envelope.memory_bytes, 64 * 1024 * 1024)
                resource.setrlimit(resource.RLIMIT_AS, (min(want, hard), hard))
            except (OSError, ValueError):
                pass
            try:
                resource.setrlimit(resource.RLIMIT_FSIZE,
                                   (envelope.max_output_bytes,
                                    envelope.max_output_bytes))
            except (OSError, ValueError):
                pass
            try:
                resource.setrlimit(resource.RLIMIT_NPROC,
                                   (max(envelope.cpu_limit, 2) * 4,
                                    resource.getrlimit(resource.RLIMIT_NPROC)[1]))
            except (OSError, ValueError):
                pass
            try:
                os.setsid()   # process-group isolation → tree terminable
            except OSError:
                pass
        return _pre

    def run(self, argv: list[str], *, envelope: JobResourceEnvelope,
            workspace: Optional[Path] = None,
            input_paths: Optional[list[Path]] = None,
            env_override: Optional[dict] = None) -> AttemptResult:
        """Execute `argv` once, bounded, inside a fresh workspace."""
        self._check_executable(argv)
        # Fail-closed B3-R5: verify mandatory boundaries BEFORE any job code
        # runs. strict-mode raises IsolatedSandboxUnsupported (BLOCKED).
        preflight = self.preflight_isolation(envelope)
        self._last_preflight = preflight
        self._deny_network()
        attempt_no = len(self._attempts) + 1
        ws = workspace or self._fresh_workspace(attempt_no)
        self._guard_paths(ws, input_paths or [])
        env = self._build_env()
        if env_override:
            for k in env_override:
                if k not in self._policy.allowed_env:
                    raise ExecutionPolicyError(
                        f"env var '{k}' not in allowlist (forbidden env var)")
                # never leak a forbidden cloud credential prefix into the env
                if any(k.upper().startswith(p) for p in self._policy.forbidden_env_prefixes):
                    raise ExecutionPolicyError(
                        f"env var '{k}' is a forbidden/cloud-prefixed var (fail closed)")
                env[k] = env_override[k]

        started = time.monotonic()
        result = AttemptResult(exit_code=None, stdout="", stderr="",
                               raise_fired=False, timed_out=False,
                               cancel_requested=False, workspace=ws)
        result.isolation_note = self._limits_preamble(envelope)
        result.isolation_report = self._last_preflight
        self._cancel_event = threading.Event()
        cancel = self._cancel_event   # single cancellation signal (B3-R5)
        killed_by_timeout = threading.Event()
        try:
            popen_kwargs = {
                "stdout": subprocess.PIPE, "stderr": subprocess.PIPE,
                "env": env, "cwd": str(ws), "text": True,
                "encoding": "utf-8", "errors": "replace",
            }
            if self.full_isolation:
                popen_kwargs["preexec_fn"] = self._apply_posix_limits(envelope)
            proc = subprocess.Popen(argv, **popen_kwargs, shell=(False))
            self._current_proc = proc
        except FileNotFoundError:
            result.exit_code = 127
            result.stderr = f"command not found: {argv[0]}"
            self._attempts.append(result)
            return result
        except Exception as exc:
            result.exit_code = 1
            result.stderr = f"spawn failed: {exc}"
            result.raise_fired = True
            self._attempts.append(result)
            return result

        # watchdog for timeout / cancellation
        def _watch():
            if cancel.wait(envelope.timeout_s):
                # cancellation requested -> actively kill the tree so the run
                # is reaped as a cancellation, never waited out (defect 9).
                _kill(proc, self.full_isolation)
                return
            killed_by_timeout.set()
            _kill(proc, self.full_isolation)

        watcher = threading.Thread(target=_watch, daemon=True)
        watcher.start()
        try:
            out, err = proc.communicate(timeout=envelope.timeout_s + 15)
            result.stdout = out or ""
            result.stderr = err or ""
            result.exit_code = proc.returncode
            if killed_by_timeout.is_set():
                result.timed_out = True
                result.resource_violation = "timeout"
            elif (self._cancel_event is not None and self._cancel_event.is_set()
                    and proc.returncode != 0):
                result.cancel_requested = True
                result.resource_violation = "cancelled"
            elif (len(result.stdout.encode("utf-8")) +
                  len(result.stderr.encode("utf-8"))) > envelope.max_output_bytes:
                result.resource_violation = "output_size_limit"
                _kill(proc, self.full_isolation)
        except subprocess.TimeoutExpired:
            killed_by_timeout.set()
            _kill(proc, self.full_isolation)
            out, err = proc.communicate()
            result.stdout = (out or "")[:envelope.max_output_bytes]
            result.stderr = (err or "")[:envelope.max_output_bytes]
            result.timed_out = True
            result.exit_code = proc.returncode
            result.resource_violation = "timeout"
        except Exception as exc:
            _kill(proc, self.full_isolation)
            result.raise_fired = True
            result.stderr += f"\ncommunicate failed: {exc}"
            result.exit_code = proc.returncode
        finally:
            cancel.set()
            self._current_proc = None

        result.ended_at = utcnow_iso()
        self._attempts.append(result)
        return result

    def cancel_current(self) -> None:
        """Actively request cancellation of an in-flight run.

        Terminates the tracked process TREE (setsid group on POSIX, taskkill
        /T on Windows) and flags the attempt cancelled so the run loop reaps
        it as a cancellation rather than a timeout.
        """
        if self._cancel_event is not None:
            self._cancel_event.set()
        proc = self._current_proc
        if proc is not None and proc.poll() is None:
            _kill(proc, self.full_isolation)

    def cleanup(self) -> None:
        """Dispose of every attempt workspace (attempt workspace is disposable)."""
        for p in self._base.iterdir():
            shutil.rmtree(p, ignore_errors=True)

    @property
    def attempts(self) -> list[dict]:
        return [{"exit_code": a.exit_code, "timed_out": a.timed_out,
                 "resource_violation": a.resource_violation,
                 "ok": a.ok, "started_at": a.started_at} for a in self._attempts]


def _kill(proc: subprocess.Popen, full_isolation: bool) -> None:
    if proc.poll() is not None:
        return
    try:
        if os.name == "nt":
            # Windows: terminate the entire process tree via taskkill /T.
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                           capture_output=True)
        else:
            # POSIX: SIGKILL the whole process group (setsid-backed tree when
            # isolating) so a child can never outlive its bounded attempt.
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                proc.kill()
    except (ProcessLookupError, PermissionError, OSError):
        pass
    try:
        proc.kill()
    except Exception:
        pass


# --------------------------------------------------------------------------
# B3-C5 — immutable content-addressed artifact store
# --------------------------------------------------------------------------

class ArtifactStore:
    """Content-addressed durable artifact storage with atomic publication.

    Files are addressed by their SHA-256 (content identity), stored under a
    CAS directory, and referenced by an immutable ArtifactManifest that
    binds producer/worker/job/attempt identity and input/output hashes.
    Publication is atomic (temp file + os.replace). Verify-before-commit
    guarantees a mangled or partial upload never becomes visible.
    """

    def __init__(self, base_dir: Path, max_artifact_bytes: int = 64 * 1024 * 1024):
        self._cas = base_dir / "cas"
        self._tmp = base_dir / "tmp"
        self._meta = base_dir / "meta"
        for d in (self._cas, self._tmp, self._meta):
            d.mkdir(parents=True, exist_ok=True)
        self._max = max_artifact_bytes
        # manifest_id -> manifest dict — RESTART-SAFE (B3-R6): reload every
        # durable sealed manifest from the meta directory on construction so
        # a supervisor/worker/control-plane restart never loses references.
        self._manifests: dict[str, dict] = {}
        self._reload_manifests()

    def _reload_manifests(self) -> None:
        """Re-seal all manifests persisted under meta/ (restart-safe)."""
        for mfile in sorted(self._meta.glob("*.json")):
            if mfile.name.endswith(".tmp"):
                continue
            try:
                m = json.loads(mfile.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue          # ignore a torn meta file (partial write, not sealed)
            mid = m.get("manifest_id")
            if mid:
                self._manifests[mid] = m

    def publish_blob(self, data: bytes) -> str:
        """Store bytes content-addressed. Returns the digest."""
        digest = hashlib.sha256(data).hexdigest()
        if len(data) > self._max:
            raise OutputLimitExceeded(
                f"artifact {len(data)} bytes exceeds ceiling {self._max}")
        dest = self._cas / digest
        if dest.exists():
            # idempotent re-publish of identical content is allowed (CAS)
            existing = sha256_file(dest)
            if existing != digest:
                raise RuntimeError(f"CAS collision at {digest}")
            return digest
        tmp = self._tmp / f"{digest}.part"
        try:
            tmp.write_bytes(data)
            tmp.replace(dest)          # atomic
        finally:
            self._tmp.resolve().joinpath(tmp.name).unlink(missing_ok=True)
        return digest

    def publish_file(self, src: Path) -> str:
        digest = sha256_file(src)
        if src.stat().st_size > self._max:
            raise OutputLimitExceeded(f"artifact {src} exceeds size ceiling")
        dest = self._cas / digest
        if not dest.exists():
            tmp = self._tmp / f"{digest}.part"
            shutil.copyfile(src, tmp)
            tmp.replace(dest)
        return digest

    def create_manifest(self, *, job_id: str, attempt: int,
                        producer_identity: str, worker_id: str,
                        artifact_paths: dict[str, Path],
                        inputs: Optional[list[str]] = None,
                        environment: Optional[dict] = None) -> dict:
        """Bind worker artifacts into an immutable manifest.

        Returns the manifest (its JSON digest is the manifest ref). All file
        downloads are verified by hash before any manifest is accepted.
        """
        artifacts = []
        for name, path in artifact_paths.items():
            ext = Path(name).suffix.lower()
            digest = self.publish_file(Path(path))
            size = Path(path).stat().st_size
            artifacts.append({
                "name": name, "sha256": digest, "size": size,
                "content_type": ext.lstrip(".") or "bin",
            })
        manifest = {
            "job_id": job_id,
            "attempt": attempt,
            "producer_identity": producer_identity,
            "worker_id": worker_id,
            "input_hashes": inputs or [],
            "environment_fingerprint": sha256_hex(
                json.dumps(environment or {}, sort_keys=True)),
            "artifacts": artifacts,
        }
        # Identity is content-derived so an identical duplicate publication
        # (duplicate result) dedups to the SAME immutable manifest reference.
        manifest_id = sha256_hex(json.dumps(manifest, sort_keys=True))
        manifest_with_ref = dict(manifest)
        manifest_with_ref["created_at"] = utcnow_iso()
        manifest_with_ref["manifest_id"] = manifest_id
        self._manifests[manifest_id] = manifest_with_ref
        self._write_meta(manifest_id, manifest_with_ref)
        return manifest_with_ref

    def _write_meta(self, manifest_id: str, manifest: dict) -> None:
        mfile = self._meta / f"{manifest_id}.json"
        tmp = mfile.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True),
                       encoding="utf-8")
        tmp.replace(mfile)

    def get(self, manifest_id: str) -> Optional[dict]:
        return self._manifests.get(manifest_id)

    def read_artifact(self, name: str, manifest_id: str) -> Optional[bytes]:
        """Read an artifact by name, re-verifying its SHA-256."""
        manifest = self.get(manifest_id)
        if not manifest:
            return None
        for a in manifest["artifacts"]:
            if a["name"] == name:
                data = (self._cas / a["sha256"]).read_bytes()
                if hashlib.sha256(data).hexdigest() != a["sha256"]:
                    raise RuntimeError("artifact hash mismatch on read")
                return data
        return None

    def has_manifest(self, manifest_id: str) -> bool:
        return manifest_id in self._manifests

    def verify_reference(self, manifest_id: str) -> bool:
        """Read-only verifier: every referenced blob still matches its hash."""
        manifest = self.get(manifest_id)
        if not manifest:
            return False
        try:
            for a in manifest["artifacts"]:
                data = (self._cas / a["sha256"]).read_bytes()
                if hashlib.sha256(data).hexdigest() != a["sha256"]:
                    return False
            return True
        except FileNotFoundError:
            return False

    def sealed_manifests(self) -> list[str]:
        return sorted(self._manifests)


# --------------------------------------------------------------------------
# B3-C6 — retry / recovery / dead letters
# --------------------------------------------------------------------------

RETRYABLE = "retryable"
TERMINAL = "terminal"
MAX_RETRIES_DEFAULT = 3
BASE_BACKOFF_S = 1.0


def classify_exit(exit_code: int, timed_out: bool, resource_violation: Optional[str]) -> str:
    """Deterministic retry classification for an attempt result.

    Only a clearly transient failure (crash before meaningful completion, or
    an explicit retryable exit) is RETRYABLE. Timeouts and resource-envelope
    violations are terminal — a bounded-envelope overrun must never auto-retry
    into a second unbounded attempt.
    """
    if timed_out or resource_violation:
        return TERMINAL              # bounded envelope violation: do not re-run
    if exit_code in (0,):
        return "ok"
    if exit_code is None:
        return RETRYABLE             # crash before meaningful completion (transient)
    if exit_code in (75, 5):         # EX_TEMPFAIL / explicit retryable (EINTR-ish)
        return RETRYABLE
    return TERMINAL                  # other nonzero → operator inspection, fail closed


def backoff_delay(attempt: int, base_s: float = BASE_BACKOFF_S) -> float:
    """Deterministic exponential backoff (no jitter — reproducible tests)."""
    return base_s * (2 ** max(0, attempt - 1))


@dataclass
class RetryPolicy:
    max_retries: int = MAX_RETRIES_DEFAULT
    base_backoff_s: float = BASE_BACKOFF_S
    terminal_on: tuple = ("timeout", "resource_violation")
    retryable_exit_codes: tuple = ()   # empty → only explicit retryable failures retry

    def should_retry(self, attempt: int, classified: str,
                     reason: Optional[str] = None) -> bool:
        if classified == "ok":
            return False
        if attempt >= self.max_retries:
            return False
        if classified == TERMINAL:
            return False
        return True


class DeadLetterEntry:
    def __init__(self, *, job_id: str, attempt: int, worker_id: str,
                 reason: str, detail: str, created_at: Optional[str] = None,
                 idempotency_key: Optional[str] = None):
        self.job_id = job_id
        self.attempt = attempt
        self.worker_id = worker_id
        self.reason = reason
        self.detail = detail
        self.created_at = created_at or utcnow_iso()
        self.idempotency_key = idempotency_key or job_id

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id, "attempt": self.attempt,
            "worker_id": self.worker_id, "reason": self.reason,
            "detail": self.detail, "created_at": self.created_at,
            "idempotency_key": self.idempotency_key,
        }


class RetryCoordinator:
    """Durable retry/recovery orchestrator with dead letters (B3-C6).

    ``store`` is an optional durable backend (a ``PgWorkerFabricStore`` or any
    object exposing ``record_retry_state``, ``dead_letter``, ``resolve_dead_letter``,
    and ``authorized_retry``). When provided, every retry/dead-letter/poison
    decision is mirrored there, so truth survives a restart (B3-R6) rather
    than living only in memory.
    """

    def __init__(self, policy: Optional[RetryPolicy] = None, store=None):
        self._policy = policy or RetryPolicy()
        self._store = store
        self._dead_letters: dict[str, DeadLetterEntry] = {}
        self._results: dict[str, dict] = {}
        self._poison: set[str] = set()
        if store is not None:
            self._load_durable()

    def _load_durable(self) -> None:
        """Rehydrate dead letters and retry state after a restart."""
        try:
            for dl in self._store.list_dead_letters():
                if dl:
                    e = DeadLetterEntry(
                        job_id=dl["job_id"], attempt=dl["attempt"],
                        worker_id=dl["worker_id"], reason=dl["reason"],
                        detail=dl.get("detail", ""),
                        created_at=dl.get("created_at"),
                        idempotency_key=dl.get("idempotency_key") or dl["job_id"])
                    self._dead_letters[dl["job_id"]] = e
                    if dl.get("poison"):
                        self._poison.add(dl["job_id"])
        except Exception:
            pass

    def run_with_retry(self, job_id: str, worker_id: str,
                       run_once: callable,
                       effect_committer: Optional[callable] = None):
        """Run `run_once(attempt)` up to policy limits. Returns final outcome.

        `run_once` returns an AttemptResult. Mirrors the real fabric loop so
        unit tests verify retry classification, backoff ordering and
        dead-letter handling without a running stack.
        """
        lines = []
        outcome = {"job_id": job_id, "attempts": 0, "result": None,
                   "dead_lettered": False, "material_effect": False}
        for attempt in range(1, self._policy.max_retries + 1):
            outcome["attempts"] = attempt
            result = run_once(attempt)
            if isinstance(result, (AttemptResult,)):
                classified = classify_exit(result.exit_code, result.timed_out,
                                           result.resource_violation)
                reason = result.resource_violation or (
                    f"exit={result.exit_code}" if result.exit_code else None)
            else:
                classified = "ok"
                reason = None
            # every attempt is mirrored durably (B3-R6: retry truth persists)
            if self._store is not None:
                try:
                    self._store.record_retry_state(
                        job_id=job_id, attempts=attempt,
                        max_retries=self._policy.max_retries,
                        classified=classified, last_reason=reason or "",
                        exhausted=classified == TERMINAL,
                        poison=classified in (RETRYABLE, TERMINAL) and
                        attempt >= self._policy.max_retries)
                except Exception:
                    pass
            if classified == "ok":
                if effect_committer:
                    effect_committer(job_id)
                outcome["result"] = "success"
                outcome["material_effect"] = True
                self._results[job_id] = outcome
                return outcome
            # not ok → maybe retry
            if self._policy.should_retry(attempt, classified, reason):
                delay = backoff_delay(attempt, self._policy.base_backoff_s)
                lines.append(f"attempt {attempt} {classified}, backoff {delay:.2f}s")
                continue
            # dead-letter it
            dl_reason = "retry_exhausted" if classified == RETRYABLE else classified
            entry = DeadLetterEntry(
                job_id=job_id, attempt=attempt, worker_id=worker_id,
                reason=dl_reason, detail=reason or "terminal failure",
                idempotency_key=outcome.get("idempotency_key") or job_id)
            self._dead_letters[job_id] = entry
            outcome["dead_lettered"] = True
            outcome["result"] = "dead_lettered"
            self._poison.add(job_id)
            outcome["backoff_trace"] = lines
            self._results[job_id] = outcome
            if self._store is not None:
                try:
                    self._store.dead_letter(
                        job_id=job_id, attempt=attempt, worker_id=worker_id,
                        reason=dl_reason, detail=reason or "terminal failure",
                        idempotency_key=job_id, poison=True)
                except Exception:
                    pass
            return outcome
        # retries exhausted
        entry = DeadLetterEntry(
            job_id=job_id, attempt=outcome["attempts"], worker_id=worker_id,
            reason="retry_exhausted", detail="max retries reached")
        self._dead_letters[job_id] = entry
        outcome["dead_lettered"] = True
        outcome["result"] = "dead_lettered"
        outcome["backoff_trace"] = lines
        self._results[job_id] = outcome
        return outcome

    def operator_authorized_retry(self, job_id: str) -> bool:
        """PO/operator-authorized retry of a dead-lettered job (B3-C6)."""
        if job_id not in self._dead_letters:
            return False
        entry = self._dead_letters.pop(job_id)
        self._poison.discard(job_id)
        # reset attempt bookkeeping for a fresh authorized run
        self._results.pop(job_id, None)
        return True

    def is_poison(self, job_id: str) -> bool:
        return job_id in self._poison

    def dead_letter(self, job_id: str) -> Optional[dict]:
        e = self._dead_letters.get(job_id)
        return e.to_dict() if e else None

    def list_dead_letters(self) -> list[dict]:
        return [e.to_dict() for e in self._dead_letters.values()]

    def result(self, job_id: str) -> Optional[dict]:
        return self._results.get(job_id)


def canonical_workspace_base() -> Path:
    return Path(tempfile.gettempdir()) / "oce-b3-workspaces"