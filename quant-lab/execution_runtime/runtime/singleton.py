"""QL-EXEC-R3 — local singleton contract (one runtime_id, one active instance).

A simple file lock scoped by ``runtime_id``: the first acquirer writes an owner
token; a second acquirer of the SAME runtime_id raises ``SingletonConflict``.
Different runtime_ids use different lock paths and never conflict. Releasing
removes the lock so it can be reacquired.

This is deliberately NOT a distributed lock system and NOT an OS-level
scheduled-task/service primitive. Process supervision (FleetSupervisor) is R5
work; this contract only guarantees that one runtime object/process holds a
given runtime_id at a time.

Stale-lock reclaim: the lock file stores the owner's PID. If the stored PID is
provably dead (no such process), ``acquire`` reclaims the stale lock. On
platforms where liveness cannot be checked, a stale lock fails closed and must
be released explicitly (documented, never silently broken).
"""
from __future__ import annotations

import os
from pathlib import Path


class SingletonConflict(RuntimeError):
    """A second runtime attempted to acquire an already-held runtime_id."""


def _pid_alive(pid: int) -> bool:
    """Best-effort PID liveness. Returns True when uncertain (fail closed)."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:  # noqa: BLE001 - unknown platform behavior -> assume alive
        return True
    return True


class SingletonLock:
    """File lock keyed by runtime_id. One holder at a time."""

    def __init__(self, lock_path: str | Path) -> None:
        self._path = Path(lock_path)
        self._token: str | None = None

    @property
    def held(self) -> bool:
        return self._token is not None

    @property
    def path(self) -> Path:
        return self._path

    def acquire(self, token: str) -> bool:
        """Acquire the lock. Returns True on success, raises SingletonConflict."""
        if self._token is not None:
            raise SingletonConflict(f"already held by this instance: {self._token!r}")
        if self._path.exists():
            existing = self._read_token()
            if existing:
                pid = self._read_pid()
                if pid is not None and not _pid_alive(pid):
                    self._path.unlink()  # stale holder is dead -> reclaim
                else:
                    raise SingletonConflict(
                        f"singleton already held by {existing!r}"
                    )
            else:
                # Unparseable lock file: fail closed, never silently break it.
                raise SingletonConflict(
                    f"singleton lock exists but is unreadable: {self._path}"
                )
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._token = token
        self._path.write_text(f"{token}\npid={os.getpid()}\n", encoding="utf-8")
        return True

    def release(self) -> None:
        if self._token is not None and self._path.exists():
            try:
                self._path.unlink()
            except FileNotFoundError:
                pass
        self._token = None

    def _read_token(self) -> str | None:
        try:
            text = self._path.read_text(encoding="utf-8")
        except OSError:
            return None
        first = text.splitlines()[0].strip() if text.splitlines() else ""
        return first or None

    def _read_pid(self) -> int | None:
        try:
            text = self._path.read_text(encoding="utf-8")
        except OSError:
            return None
        for line in text.splitlines():
            if line.startswith("pid="):
                return int(line.split("=", 1)[1].strip())
        return None
