"""SENSOR-B4-I03 — generic no-clobber atomic durability primitives.

Low-level, filesystem-agnostic building blocks that later checkpoints (I05
T0B projections, I04 manifest records) can reuse.  This module deliberately
contains NO T0A hash semantics — those live in ``blob_store.py``.

Frozen commit doctrine implemented here (03 doc §1, I03 §6):

1. write to staging on the SAME filesystem (caller's job)
2. flush userspace buffers (caller's job, on the staged writer)
3. fsync staged file (caller's job, while the write handle is open)
4. verify staged artifact (caller's job, before publication)
5. atomically publish staging -> final with a NO-REPLACE primitive
   (``os.link``: the final name appears ONLY when the fully-fsynced inode is
   linked — a reader can never observe a half-written final object)
6. fsync the final parent directory so the new name is durable
7. (later checkpoints persist metadata / advance resume — NOT here)

Guarantees:

- The commit boundary NEVER falls back to copy+delete or to an
  overwrite-capable rename.  If ``os.link`` is unavailable or the devices
  differ, the operation FAILS CLOSED with a typed error.
- ``fsync_directory`` is platform-aware: POSIX opens the directory read-only
  and fsyncs it; Windows opens it with ``FILE_FLAG_BACKUP_SEMANTICS`` and
  calls ``FlushFileBuffers`` (the documented way to flush a directory on
  NTFS).  If the platform cannot flush a directory, a truthful
  ``DurabilityUnsupported`` is raised — success is never claimed without
  proof.
- The six fault-injection points are internal-only (not part of the public
  export surface) and deterministic, for crash/crash-matrix tests.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Protocol

# ---------------------------------------------------------------------------
# Typed errors
# ---------------------------------------------------------------------------


class AtomicPublishError(RuntimeError):
    """Base class: the atomic commit boundary failed; nothing was claimed."""


class AtomicPublishTargetExists(AtomicPublishError):
    """The final name already exists; NO overwrite was attempted."""


class CrossFilesystemAtomicityError(AtomicPublishError):
    """Staging and final live on different devices — atomic commit denied."""


class DurabilityUnsupported(AtomicPublishError):
    """The platform cannot provide the required durability semantics."""


class ComponentTooLong(ValueError):
    """A canonical encoded path component exceeds the filesystem limit."""


# ---------------------------------------------------------------------------
# Platform / filesystem probes (dependency-injectable for tests)
# ---------------------------------------------------------------------------


DeviceId = int

DeviceProbe = Callable[[Path], DeviceId]
NameMaxProbe = Callable[[Path], int]


def default_device_probe(path: Path) -> DeviceId:
    """Return the device id of a path's filesystem (``st_dev``).

    ``st_dev`` equality is the accepted same-filesystem proof for the commit
    boundary (I03 §14, POSIX-styled; Windows exposes the volume id here).
    """
    return os.stat(path).st_dev


def default_name_max(path: Path) -> int:
    """Return the supported filename component byte limit for a directory.

    - POSIX: ``os.pathconf(path, 'PC_NAME_MAX')`` is queried where supported;
    - Windows: ``os.pathconf`` is unavailable, so the documented NTFS limit of
      255 UTF-16 units is used.  Our backend-controlled object-key components
      are ASCII after canonical escaping, so units == bytes there; the bound
      is also the conventional POSIX ``NAME_MAX``, keeping behavior portable;
    - any platform that reports a non-positive limit fails closed.
    """
    if hasattr(os, "pathconf"):
        try:
            limit = os.pathconf(path, "PC_NAME_MAX")
        except (OSError, ValueError):
            limit = 255
    else:
        limit = 255
    if not isinstance(limit, int) or limit <= 0:
        raise DurabilityUnsupported(
            f"filesystem at {path!s} reports unusable component limit {limit!r}"
        )
    return limit


def validate_component_length(component: str, limit: int) -> str:
    """Fail closed if a canonical encoded component exceeds the filesystem.

    The encoded (escaped) component's UTF-8 byte length is compared against
    the filesystem component limit.  The canonical I02 escaping keeps
    components byte-for-byte stable, so no truncation/normalization is ever
    applied — an over-limit component simply fails BEFORE any artifact write.
    """
    if not isinstance(component, str):
        raise TypeError(
            f"component must be str, got {type(component).__name__}"
        )
    if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
        raise ValueError(f"limit must be a positive int, got {limit!r}")
    length = len(component.encode("utf-8"))
    if length > limit:
        raise ComponentTooLong(
            f"component {component[:64]!r} is {length} bytes; filesystem limit "
            f"is {limit} bytes"
        )
    return component


# ---------------------------------------------------------------------------
# Operation recorder + fault injection (internal test seams, NOT exported)
# ---------------------------------------------------------------------------


class OpRecorder(Protocol):
    def record(self, op: str) -> None: ...  # pragma: no cover - protocol


class ListOpRecorder:
    """Collects recorded operation tags for order-contract assertions."""

    def __init__(self) -> None:
        self.ops: list[str] = []

    def record(self, op: str) -> None:
        self.ops.append(op)


class FaultPoint(Enum):
    STAGE_WRITE = "STAGE_WRITE"
    BEFORE_FILE_FSYNC = "BEFORE_FILE_FSYNC"
    BEFORE_STAGE_VERIFY = "BEFORE_STAGE_VERIFY"
    BEFORE_PUBLISH = "BEFORE_PUBLISH"
    AFTER_PUBLISH_BEFORE_DIR_FSYNC = "AFTER_PUBLISH_BEFORE_DIR_FSYNC"
    AFTER_DIR_FSYNC_BEFORE_RETURN = "AFTER_DIR_FSYNC_BEFORE_RETURN"


class FaultError(RuntimeError):
    """Raised by an injected fault hook to simulate a crash."""


class FaultHook(Protocol):
    def raise_if(self, point: FaultPoint) -> None: ...  # pragma: no cover - protocol


class RaiseFaultHook:
    """Deterministic fault hook: raises at configured points.

    ``FaultError`` (with the fault point as message) simulates a crash at
    exactly that step, without killing the test runner.
    """

    def __init__(self, *points: FaultPoint) -> None:
        self._points = set(points)

    def raise_if(self, point: FaultPoint) -> None:
        if point in self._points:
            raise FaultError(f"injected fault at {point.value}")

    @property
    def points(self) -> frozenset[FaultPoint]:
        return frozenset(self._points)


# Canonical durable-commit operation tags (I03 §65 order contract).
OP_STAGE_WRITE = "stage_write"
OP_FILE_FLUSH = "file_flush"
OP_FILE_FSYNC = "file_fsync"
OP_STAGE_VERIFY = "stage_verify"
OP_DEVICE_CHECK = "device_check"
OP_ATOMIC_PUBLISH = "atomic_publish"
OP_PARENT_DIR_FSYNC = "parent_dir_fsync"
OP_STAGING_CLEANUP = "staging_cleanup"
OP_SUCCESS_RETURN = "success_return"

_CANONICAL_ORDER = [
    OP_STAGE_WRITE,
    OP_FILE_FLUSH,
    OP_FILE_FSYNC,
    OP_STAGE_VERIFY,
    OP_ATOMIC_PUBLISH,
    OP_PARENT_DIR_FSYNC,
    OP_SUCCESS_RETURN,
]


def is_canonical_durable_order(ops: list[str]) -> bool:
    """True iff ALL seven canonical durable operations appear, in order.

    Extra tags (device_check, staging_cleanup) may sit between them; the
    durability contract forbids both omission and reordering of the
    canonical sequence (I03 §65).
    """
    return all(tag in ops for tag in _CANONICAL_ORDER) and [
        ops.index(tag) for tag in _CANONICAL_ORDER
    ] == sorted(ops.index(tag) for tag in _CANONICAL_ORDER)


# ---------------------------------------------------------------------------
# fsync helpers
# ---------------------------------------------------------------------------


def fsync_file(path: str | Path) -> None:
    """Flush + fsync an existing file (must be openable for writing).

    The staged file's fsync must happen while its write handle is open; this
    helper is for the generic post-hoc path (raw re-sync of an existing
    artifact).  Raises ``DurabilityUnsupported`` only if the platform cannot
    fsync at all; ``OSError`` is surfaced truthfully otherwise.
    """
    with open(path, "r+b") as fh:
        os.fsync(fh.fileno())


def _fsync_directory_windows(path: Path) -> None:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    FILE_SHARE_DELETE = 0x00000004
    OPEN_EXISTING = 3
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    handle = kernel32.CreateFileW(
        str(path),
        GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS,
        None,
    )
    if handle in (None, INVALID_HANDLE_VALUE):
        err = ctypes.get_last_error()
        raise DurabilityUnsupported(
            f"cannot open directory {path!s} for durability flush "
            f"(WinError {err})"
        )
    try:
        ok = kernel32.FlushFileBuffers(handle)
        if not ok:
            err = ctypes.get_last_error()
            raise DurabilityUnsupported(
                f"FlushFileBuffers on directory {path!s} failed (WinError {err}); "
                "platform cannot prove parent-directory durability here"
            )
    finally:
        kernel32.CloseHandle(handle)


def fsync_directory(path: str | Path) -> None:
    """Flush the directory entry namespace so a published name is durable.

    POSIX: open the directory read-only (``O_RDONLY``) and fsync it.
    Windows: open with ``FILE_FLAG_BACKUP_SEMANTICS`` and call
    ``FlushFileBuffers`` (the documented NTFS directory-flush mechanism).

    If the platform/filesystem cannot flush a directory, a truthful
    ``DurabilityUnsupported`` is raised — durability is NEVER claimed without
    proof.  Documented platform truth: verified on Windows 10/11 NTFS and
    Linux; distributed/NFS semantics are not assumed.
    """
    target = Path(path)
    if os.name == "nt":
        _fsync_directory_windows(target)
        return
    try:
        fd = os.open(target, os.O_RDONLY)
    except OSError as exc:
        raise DurabilityUnsupported(
            f"cannot open directory {target!s} for fsync: {exc}"
        ) from exc
    try:
        os.fsync(fd)
    except OSError as exc:
        raise DurabilityUnsupported(
            f"fsync of directory {target!s} failed: {exc}"
        ) from exc
    finally:
        os.close(fd)


def ensure_same_device(
    a: str | Path,
    b: str | Path,
    *,
    device_probe: DeviceProbe = default_device_probe,
) -> None:
    """Fail closed unless ``a`` and ``b`` are on the SAME device.

    No copy+delete fallback ever exists on this boundary.
    """
    dev_a = device_probe(Path(a))
    dev_b = device_probe(Path(b))
    if dev_a != dev_b:
        raise CrossFilesystemAtomicityError(
            f"staging device {dev_a} != final device {dev_b}; "
            "cross-device atomic publication is forbidden"
        )


# ---------------------------------------------------------------------------
# No-clobber atomic publication
# ---------------------------------------------------------------------------


def publish_no_replace(
    staging_path: str | Path,
    final_path: str | Path,
    *,
    device_probe: DeviceProbe = default_device_probe,
    fault_hooks: FaultHook | None = None,
    ops: OpRecorder | None = None,
) -> None:
    """Atomically publish a fully-fsynced staged file at ``final_path``.

    Never overwrites: ``os.link(staging, final)`` creates the final NAME only
    if it does not exist, and the linked inode is already fully written and
    fsynced, so a reader can never observe partial final bytes.

    Sequence: device check -> create parent dirs -> ``os.link`` ->
    (fault E) -> fsync parent directory -> (fault F) -> unlink staging.

    Fault E leaves final + staging (publication happened, durability not yet
    proven).  Fault F leaves final durably committed + staging.  Both are
    intentionally preserved crash evidence — recovery is a later checkpoint.
    """
    sp = Path(staging_path)
    fp = Path(final_path)

    if not sp.is_file():
        raise AtomicPublishError(
            f"staging artifact {sp!s} is missing or not a regular file"
        )
    # Directory creation STRICTLY before final publication (I03 §28) and
    # before the device check (the final parent must exist to be stat'd).
    os.makedirs(fp.parent, exist_ok=True)
    if ops is not None:
        ops.record(OP_DEVICE_CHECK)
    ensure_same_device(sp.parent, fp.parent, device_probe=device_probe)

    if ops is not None:
        ops.record(OP_ATOMIC_PUBLISH)
    try:
        os.link(sp, fp)
    except FileExistsError as exc:
        raise AtomicPublishTargetExists(
            f"final object {fp!s} already exists; no overwrite attempted"
        ) from exc
    except OSError as exc:
        raise AtomicPublishError(
            f"no-clobber publication of {fp!s} failed: {exc}"
        ) from exc

    if fault_hooks is not None:
        fault_hooks.raise_if(FaultPoint.AFTER_PUBLISH_BEFORE_DIR_FSYNC)

    if ops is not None:
        ops.record(OP_PARENT_DIR_FSYNC)
    fsync_directory(fp.parent)

    if fault_hooks is not None:
        fault_hooks.raise_if(FaultPoint.AFTER_DIR_FSYNC_BEFORE_RETURN)

    # Ordinary success: remove the now-hardlinked staging name.  If unlink
    # fails the FINAL name is already durable — the leftover staging name is
    # not an integrity failure and is intentionally left as recoverable
    # evidence for the later recovery checkpoint (I08).
    if ops is not None:
        ops.record(OP_STAGING_CLEANUP)
    try:
        os.unlink(sp)
    except OSError:
        pass


__all__ = [
    "OP_ATOMIC_PUBLISH",
    "OP_DEVICE_CHECK",
    "OP_FILE_FLUSH",
    "OP_FILE_FSYNC",
    "OP_PARENT_DIR_FSYNC",
    "OP_STAGE_VERIFY",
    "OP_STAGE_WRITE",
    "OP_STAGING_CLEANUP",
    "OP_SUCCESS_RETURN",
    "AtomicPublishError",
    "AtomicPublishTargetExists",
    "ComponentTooLong",
    "CrossFilesystemAtomicityError",
    "DeviceId",
    "DeviceProbe",
    "DurabilityUnsupported",
    "NameMaxProbe",
    "default_device_probe",
    "default_name_max",
    "ensure_same_device",
    "fsync_directory",
    "fsync_file",
    "is_canonical_durable_order",
    "publish_no_replace",
    "validate_component_length",
]