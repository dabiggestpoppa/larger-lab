"""SENSOR-B4-I05R1A — shared durable atomic JSON catalog primitive.

All immutable T0B catalog truth (projection schema definitions, projection
artifact records, projection context records, projection lineage manifests)
is persisted through this ONE primitive.  It reuses the accepted I03/I03R1
durability contract — it never implements a weaker persistence layer.

Frozen doctrines implemented here (I05R1 §4-§10):

- DURABLE PUBLICATION: durable directory chain -> staging write -> flush ->
  file fsync -> reopen/verify (exact canonical bytes re-parsed) ->
  no-clobber atomic publish -> parent-directory fsync -> success.
- IMMUTABLE HISTORY: no normal overwrite.  Same logical ID + exact same
  canonical content = idempotent reuse.  Same logical ID + differing
  content = typed conflict (``JsonCatalogConflict``).
- CORRUPTION NEVER DISAPPEARS: a corrupt committed fragment (bad JSON,
  missing logical id, tampered binding) raises ``JsonCatalogCorrupt`` on
  load.  A corrupt committed object may never silently become
  "not registered".  I08 later owns quarantine/recovery; I05R1 only
  detects and fails closed.
- SAFE PHYSICAL KEYS: raw logical IDs are arbitrary nonempty strings and
  NEVER become filenames.  The physical locator is
  ``sha256(utf8(logical_id)).hexdigest() + ".json"`` (full 64 lowercase
  hex).  The logical ID remains stored INSIDE the object.
- PHYSICAL KEY BINDING: on reload the physical filename is recomputed from
  the logical ID stored inside the fragment and must match exactly — a
  file cannot masquerade under another logical identity.
- DIRECTORY SAFETY: caller-controlled logical identity never becomes
  directory structure; only the hex digest (plus the fixed suffix) touches
  the filesystem namespace.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from enum import Enum
from pathlib import Path
from typing import Any

from .atomic import (
    AtomicPublishTargetExists,
    FaultError,
    OpRecorder,
    ensure_durable_directory,
    fsync_directory,
    fsync_file,
    publish_no_replace,
)

# ---------------------------------------------------------------------------
# Typed errors
# ---------------------------------------------------------------------------


class JsonCatalogError(RuntimeError):
    """Base class for durable JSON catalog failures."""


class JsonCatalogCorrupt(JsonCatalogError):
    """A committed catalog fragment is corrupt and cannot be trusted.

    Raised (never silently skipped) for: invalid JSON, non-object payloads,
    a missing/mismatched logical-id field, or a physical-key binding
    violation (stored logical ID does not hash to its own filename).
    """


class JsonCatalogConflict(JsonCatalogError):
    """Same logical ID committed with differing canonical content."""

    def __init__(self, logical_id: str) -> None:
        self.logical_id = logical_id
        super().__init__(
            f"catalog logical_id={logical_id!r} already committed with "
            "different content; immutable catalogs never overwrite"
        )


class JsonCatalogInvalidIdentity(JsonCatalogError):
    """Caller-supplied logical identity is unusable (empty/invalid)."""


# ---------------------------------------------------------------------------
# Fault injection (catalog-level crash matrix, I05R1 §46)
# ---------------------------------------------------------------------------


class CatalogFaultPoint(Enum):
    """Deterministic injected-failure boundaries of a catalog commit."""

    BEFORE_STAGED_WRITE = "BEFORE_STAGED_WRITE"
    AFTER_WRITE_BEFORE_FSYNC = "AFTER_WRITE_BEFORE_FSYNC"
    AFTER_FSYNC_BEFORE_VERIFY = "AFTER_FSYNC_BEFORE_VERIFY"
    AFTER_VERIFY_BEFORE_PUBLISH = "AFTER_VERIFY_BEFORE_PUBLISH"
    # The two publication-internal boundaries are forwarded verbatim to
    # ``publish_no_replace`` (atomic.py FaultPoint).
    AFTER_PUBLISH_BEFORE_DIR_FSYNC = "AFTER_PUBLISH_BEFORE_DIR_FSYNC"
    AFTER_DIR_FSYNC_BEFORE_RETURN = "AFTER_DIR_FSYNC_BEFORE_RETURN"


class CatalogFaultHook:
    """Deterministic fault hook: raises :class:`FaultError` at configured points."""

    def __init__(self, *points: CatalogFaultPoint) -> None:
        self._points = set(points)

    def raise_if(self, point: CatalogFaultPoint) -> None:
        if point in self._points:
            raise FaultError(f"injected catalog fault at {point.value}")

    @property
    def points(self) -> frozenset[CatalogFaultPoint]:
        return frozenset(self._points)


# Canonical catalog-commit operation tags (order-contract evidence).
CATALOG_OP_STAGE_WRITE = "catalog_stage_write"
CATALOG_OP_FILE_FSYNC = "catalog_file_fsync"
CATALOG_OP_VERIFY = "catalog_verify"
CATALOG_OP_PUBLISH = "catalog_publish"
CATALOG_OP_DIR_FSYNC = "catalog_dir_fsync"
CATALOG_OP_SUCCESS = "catalog_success"

_CANONICAL_CATALOG_ORDER = [
    CATALOG_OP_STAGE_WRITE,
    CATALOG_OP_FILE_FSYNC,
    CATALOG_OP_VERIFY,
    CATALOG_OP_PUBLISH,
    CATALOG_OP_DIR_FSYNC,
    CATALOG_OP_SUCCESS,
]


def is_canonical_catalog_commit_order(ops: list[str]) -> bool:
    """True iff all six canonical catalog-commit operations appear in order."""
    if any(tag not in ops for tag in _CANONICAL_CATALOG_ORDER):
        return False
    positions = [ops.index(tag) for tag in _CANONICAL_CATALOG_ORDER]
    return positions == sorted(positions)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def catalog_physical_key(logical_id: str) -> str:
    """Deterministic safe physical locator for a logical catalog ID.

    ``sha256(utf8(logical_id)).hexdigest() + ".json"`` — full 64 lowercase
    hex.  The raw logical ID never touches the filesystem namespace, so no
    ``/``, ``..``, backslash, NUL or absolute path can escape the catalog
    root (I05R1 §8/§10).
    """
    if not isinstance(logical_id, str) or not logical_id:
        raise JsonCatalogInvalidIdentity(
            f"catalog logical_id must be a nonempty string, got {logical_id!r}"
        )
    if "\x00" in logical_id:
        raise JsonCatalogInvalidIdentity("catalog logical_id contains NUL")
    digest = hashlib.sha256(logical_id.encode("utf-8")).hexdigest()
    return f"{digest}.json"


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    """Canonical JSON encoding: sorted keys, compact separators, UTF-8."""
    return json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


# ---------------------------------------------------------------------------
# DurableJsonCatalog
# ---------------------------------------------------------------------------


class DurableJsonCatalog:
    """One immutable logical object per hashed filename, durably published.

    The payload MUST carry the logical ID under ``logical_id_field``; the
    binding between stored identity and physical filename is revalidated on
    every load.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        logical_id_field: str,
        fault_hooks: CatalogFaultHook | None = None,
        ops: OpRecorder | None = None,
    ) -> None:
        self._root = Path(root)
        self._logical_id_field = logical_id_field
        self._fault_hooks = fault_hooks
        self._ops = ops
        ensure_durable_directory(self._root)
        # logical_id -> payload (as persisted, canonical form)
        self._cache: dict[str, dict[str, Any]] = {}
        self._load_all()

    # -- paths ---------------------------------------------------------------

    @property
    def root(self) -> Path:
        return self._root

    def _physical_path(self, logical_id: str) -> Path:
        return self._root / catalog_physical_key(logical_id)

    # -- loading -------------------------------------------------------------

    def _parse_fragment(self, path: Path) -> tuple[str, dict[str, Any]]:
        """Parse one committed fragment with full corruption checking.

        Every failure mode raises :class:`JsonCatalogCorrupt` — a corrupt
        committed object never silently becomes "not registered".
        """
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise JsonCatalogCorrupt(
                f"catalog fragment {path.name} is unreadable: {exc}"
            ) from exc
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise JsonCatalogCorrupt(
                f"catalog fragment {path.name} is not valid JSON: {exc}"
            ) from exc
        if not isinstance(payload, dict):
            raise JsonCatalogCorrupt(
                f"catalog fragment {path.name} is not a JSON object"
            )
        logical_id = payload.get(self._logical_id_field)
        if not isinstance(logical_id, str) or not logical_id:
            raise JsonCatalogCorrupt(
                f"catalog fragment {path.name} has no usable "
                f"{self._logical_id_field!r} field"
            )
        # Physical key binding (I05R1 §9): the stored logical identity must
        # hash to exactly the filename it was found under.
        expected_name = catalog_physical_key(logical_id)
        if path.name != expected_name:
            raise JsonCatalogCorrupt(
                f"catalog fragment {path.name} claims logical_id="
                f"{logical_id!r} but its physical key must be "
                f"{expected_name}; masquerading identity rejected"
            )
        return logical_id, payload

    def _load_all(self) -> None:
        for path in sorted(self._root.glob("*.json")):
            logical_id, payload = self._parse_fragment(path)
            if logical_id in self._cache:
                # Two files claiming one logical id cannot both bind to the
                # same physical key, so this only triggers if the cache was
                # pre-populated — treat divergence as corruption.
                if canonical_json_bytes(self._cache[logical_id]) != canonical_json_bytes(
                    payload
                ):
                    raise JsonCatalogCorrupt(
                        f"duplicate divergent fragments for logical_id="
                        f"{logical_id!r}"
                    )
            self._cache[logical_id] = payload

    # -- reads ---------------------------------------------------------------

    def get(self, logical_id: str) -> dict[str, Any] | None:
        """Return the committed payload for ``logical_id``, or None."""
        return self._cache.get(logical_id)

    def has(self, logical_id: str) -> bool:
        return logical_id in self._cache

    def list_ids(self) -> list[str]:
        return sorted(self._cache.keys())

    def __len__(self) -> int:
        return len(self._cache)

    # -- commit --------------------------------------------------------------

    def commit(self, logical_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Durably commit an immutable catalog object (idempotent).

        - Same logical ID + exact same canonical content: idempotent reuse.
        - Same logical ID + differing content: ``JsonCatalogConflict``.
        - New logical ID: staged write -> fsync -> verify -> no-clobber
          publish -> parent-dir fsync -> success.

        Returns the committed payload (the existing one on idempotent reuse).
        """
        if not isinstance(logical_id, str) or not logical_id:
            raise JsonCatalogInvalidIdentity(
                f"catalog logical_id must be a nonempty string, got {logical_id!r}"
            )
        if not isinstance(payload, dict):
            raise TypeError("catalog payload must be a dict")
        stored_id = payload.get(self._logical_id_field)
        if stored_id != logical_id:
            raise JsonCatalogInvalidIdentity(
                f"payload {self._logical_id_field!r}={stored_id!r} does not "
                f"match the committed logical_id={logical_id!r}"
            )

        canonical = canonical_json_bytes(payload)

        if logical_id in self._cache:
            existing = canonical_json_bytes(self._cache[logical_id])
            if existing != canonical:
                raise JsonCatalogConflict(logical_id)
            return self._cache[logical_id]  # idempotent reuse

        final = self._physical_path(logical_id)
        if final.exists():
            # A file exists on disk that this process has not yet cached
            # (e.g. written by a concurrent writer).  Verify and adopt or
            # conflict — never overwrite.
            existing_logical_id, existing_payload = self._parse_fragment(final)
            if existing_logical_id != logical_id:
                raise JsonCatalogCorrupt(
                    f"catalog fragment {final.name} binds to "
                    f"{existing_logical_id!r}, expected {logical_id!r}"
                )
            if canonical_json_bytes(existing_payload) != canonical:
                raise JsonCatalogConflict(logical_id)
            self._cache[logical_id] = existing_payload
            return existing_payload

        # -- durable publication sequence ------------------------------------
        staging_dir = self._root / "_staging"
        ensure_durable_directory(staging_dir)
        staged = staging_dir / f"catalog-{uuid.uuid4().hex}.json"

        if self._fault_hooks is not None:
            self._fault_hooks.raise_if(CatalogFaultPoint.BEFORE_STAGED_WRITE)

        try:
            if self._ops is not None:
                self._ops.record(CATALOG_OP_STAGE_WRITE)
            # I05R2 §26/§27: open staged file -> write canonical bytes ->
            # flush userspace buffers -> close.  NO fsync happens inside the
            # open-file block, so the named AFTER_WRITE_BEFORE_FSYNC fault
            # point genuinely precedes ALL file durability fsyncs.
            with open(staged, "wb") as fh:
                fh.write(canonical)
                fh.flush()

            if self._fault_hooks is not None:
                self._fault_hooks.raise_if(CatalogFaultPoint.AFTER_WRITE_BEFORE_FSYNC)

            if self._ops is not None:
                self._ops.record(CATALOG_OP_FILE_FSYNC)
            fsync_file(staged)  # the ONE file-fsync of the staged artifact

            if self._fault_hooks is not None:
                self._fault_hooks.raise_if(CatalogFaultPoint.AFTER_FSYNC_BEFORE_VERIFY)

            # Reopen/verify: the staged bytes must re-parse to exactly the
            # canonical payload before publication is attempted.
            if self._ops is not None:
                self._ops.record(CATALOG_OP_VERIFY)
            reread_raw = staged.read_bytes()
            if reread_raw != canonical:
                raise JsonCatalogCorrupt(
                    "staged catalog fragment does not round-trip to its "
                    "canonical bytes; refusing to publish"
                )
            reparsed = json.loads(reread_raw.decode("utf-8"))
            if canonical_json_bytes(reparsed) != canonical:
                raise JsonCatalogCorrupt(
                    "staged catalog fragment re-encodes differently; "
                    "refusing to publish"
                )

            if self._fault_hooks is not None:
                self._fault_hooks.raise_if(CatalogFaultPoint.AFTER_VERIFY_BEFORE_PUBLISH)

            # Forward the two publication-internal fault boundaries.
            pub_hook = None
            if self._fault_hooks is not None:

                class _Forward:
                    def __init__(self, hook: CatalogFaultHook) -> None:
                        self._hook = hook

                    def raise_if(self, point: Any) -> None:  # atomic.FaultPoint
                        name = getattr(point, "name", "")
                        if name == "AFTER_PUBLISH_BEFORE_DIR_FSYNC":
                            self._hook.raise_if(
                                CatalogFaultPoint.AFTER_PUBLISH_BEFORE_DIR_FSYNC
                            )
                        elif name == "AFTER_DIR_FSYNC_BEFORE_RETURN":
                            self._hook.raise_if(
                                CatalogFaultPoint.AFTER_DIR_FSYNC_BEFORE_RETURN
                            )

                pub_hook = _Forward(self._fault_hooks)

            if self._ops is not None:
                self._ops.record(CATALOG_OP_PUBLISH)
            try:
                publish_no_replace(staged, final, fault_hooks=pub_hook, ops=self._ops)
            except (FileExistsError, AtomicPublishTargetExists):
                # A concurrent writer won the publish race.  Adopt only if
                # the winner is byte-identical; otherwise typed conflict.
                existing_logical_id, existing_payload = self._parse_fragment(final)
                if existing_logical_id != logical_id:
                    raise JsonCatalogCorrupt(
                        f"concurrent fragment {final.name} binds to "
                        f"{existing_logical_id!r}, expected {logical_id!r}"
                    ) from None
                if canonical_json_bytes(existing_payload) != canonical:
                    raise JsonCatalogConflict(logical_id) from None
                self._cache[logical_id] = existing_payload
                if self._ops is not None:
                    self._ops.record(CATALOG_OP_DIR_FSYNC)
                fsync_directory(final.parent)
                if self._ops is not None:
                    self._ops.record(CATALOG_OP_SUCCESS)
                return existing_payload

            if self._ops is not None:
                self._ops.record(CATALOG_OP_DIR_FSYNC)
            fsync_directory(final.parent)

            if self._ops is not None:
                self._ops.record(CATALOG_OP_SUCCESS)
            self._cache[logical_id] = payload
            return payload
        finally:
            try:
                if staged.exists():
                    staged.unlink()
            except OSError:
                pass


__all__ = [
    "CATALOG_OP_DIR_FSYNC",
    "CATALOG_OP_FILE_FSYNC",
    "CATALOG_OP_PUBLISH",
    "CATALOG_OP_STAGE_WRITE",
    "CATALOG_OP_SUCCESS",
    "CATALOG_OP_VERIFY",
    "CatalogFaultHook",
    "CatalogFaultPoint",
    "DurableJsonCatalog",
    "FaultError",
    "JsonCatalogConflict",
    "JsonCatalogCorrupt",
    "JsonCatalogError",
    "JsonCatalogInvalidIdentity",
    "canonical_json_bytes",
    "catalog_physical_key",
    "is_canonical_catalog_commit_order",
]
