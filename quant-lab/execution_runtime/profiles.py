"""QL-EXEC-R1 — runtime profiles, observed runtime state, and path isolation.

Static RuntimeProfile is separated from dynamic RuntimeObservedState. Paths
are deterministic and isolated per runtime_id; unsafe ids are rejected.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .enums import DesiredState, MachineProfile, RuntimeHealth
from .exceptions import InvalidRuntimeId, PathCollisionError
from .ownership import OwnershipNamespace

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_FORBIDDEN = ("..", ".", "", "/", "\\", ":")


@dataclass(frozen=True)
class RuntimeProfile:
    """Static runtime configuration (no supervisor, no process)."""

    runtime_id: str
    machine_profile: MachineProfile
    account_id: str
    metadata_version: int

    strategy_adapter_ids: tuple[str, ...] = ()
    capital_policy_id: str | None = None
    capital_translation_id: str | None = None

    state_root: str = ""
    ledger_root: str = ""
    log_root: str = ""
    desired_state_key: str = ""
    deployment_generation: str = ""
    ownership_namespace: OwnershipNamespace | None = None

    def __post_init__(self) -> None:
        validate_runtime_id(self.runtime_id)
        if not self.account_id or not self.account_id.strip():
            raise ValueError("account_id must be non-empty")
        if self.metadata_version < 1:
            raise ValueError("metadata_version must be >= 1")


@dataclass(frozen=True)
class RuntimeState:
    """Minimal authority-relevant runtime view (subset of observed state)."""

    runtime_id: str
    desired_state: DesiredState = DesiredState.RUNNING
    safety_blocked: bool = False


@dataclass(frozen=True)
class RuntimeObservedState:
    """Dynamic runtime truth (pid/heartbeat/health)."""

    runtime_id: str
    pid: int | None = None
    process_alive: bool = False
    heartbeat_ts: str = ""
    desired_state: DesiredState = DesiredState.RUNNING
    health: RuntimeHealth = RuntimeHealth.UNKNOWN
    last_error: str = ""
    reconciliation_state: str = ""
    observed_at: str = ""
    safety_blocked: bool = False


@dataclass(frozen=True)
class RuntimePaths:
    """Deterministic, isolated mutable paths for one runtime."""

    runtime_id: str
    state_dir: Path
    ledger_dir: Path
    log_dir: Path

    def all_dirs(self) -> tuple[Path, ...]:
        return (self.state_dir, self.ledger_dir, self.log_dir)


def validate_runtime_id(runtime_id: str) -> None:
    """Reject empty/unsafe ids (path traversal, separators, reserved names)."""
    if not isinstance(runtime_id, str):
        raise InvalidRuntimeId("runtime_id must be a string")
    rid = runtime_id.strip()
    if rid in _FORBIDDEN:
        raise InvalidRuntimeId(f"runtime_id {runtime_id!r} is not allowed")
    if not _ID_RE.match(rid):
        raise InvalidRuntimeId(
            f"runtime_id {runtime_id!r} contains unsafe characters"
        )


def canonical_runtime_id(runtime_id: str) -> str:
    """Normalized collision key: stripped + casefolded."""
    validate_runtime_id(runtime_id)
    return runtime_id.strip().casefold()


def normalize_runtime_id(runtime_id: str) -> str:
    """Return the validated, stripped id (identity-preserving)."""
    validate_runtime_id(runtime_id)
    return runtime_id.strip()


def build_runtime_paths(base_root: str | Path, runtime_id: str) -> RuntimePaths:
    """Deterministic state/ledger/log paths keyed by runtime_id.

    Never creates directories. No two valid runtime ids resolve to the same
    normalized path (casefold + strip collision).
    """
    rid = normalize_runtime_id(runtime_id)
    root = Path(base_root)
    return RuntimePaths(
        runtime_id=rid,
        state_dir=root / "state" / rid,
        ledger_dir=root / "ledger" / rid,
        log_dir=root / "logs" / rid,
    )


def assert_no_path_collision(ids: list[str]) -> None:
    """Fail closed if two runtime ids normalize to the same path."""
    seen: dict[str, str] = {}
    for rid in ids:
        key = canonical_runtime_id(rid)
        if key in seen:
            raise PathCollisionError(
                f"runtime ids {seen[key]!r} and {rid!r} resolve to the same path"
            )
        seen[key] = rid
