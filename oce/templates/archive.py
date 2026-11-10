"""Digest-bound, offline template archive installation (B6-I2, sections C1.S3).

An archive is a typed JSON document, not a tar or zip, so there is no decompressor, no symlink
support and no parser surface that can surprise the caller. Validation is total and ordered:
shape, version, entry count, per-entry path, per-entry mode, per-entry size, total size, duplicate
paths, then the payload digest. Only then does anything touch the filesystem.
"""
from __future__ import annotations

import hashlib
import json
import pathlib

from .refusals import (
    MAX_ENTRIES,
    MAX_ENTRY_BYTES,
    MAX_PATH_CHARS,
    MAX_TOTAL_BYTES,
    Refused,
    refuse,
)

SCHEMA = "oce.template.archive.v1"
VERSION = "v1"
ENTRY_KEYS = frozenset({"path", "content", "mode"})
MANIFEST_KEYS = frozenset({"schema", "template", "version", "payload_digest", "entries"})


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def payload_digest(entries) -> str:
    """Digest over the exact (path, mode, content) triples; order is the declared order."""
    listed = [[entry["path"], entry["mode"], entry["content"]] for entry in entries]
    return hashlib.sha256(canonical(listed)).hexdigest()


def _check_path(path: object) -> str:
    if not isinstance(path, str) or not path:
        refuse("REFUSED_INVALID_MANIFEST", "entry path is not a non-empty string")
    if len(path) > MAX_PATH_CHARS:
        refuse("REFUSED_OVERSIZE", f"entry path longer than {MAX_PATH_CHARS}")
    if path.startswith("/") or path.startswith("\\") or ":" in path.split("/")[0]:
        refuse("REFUSED_ABSOLUTE_ENTRY", path)
    if "\\" in path:
        refuse("REFUSED_PATH_TRAVERSAL", f"backslash separator: {path}")
    parts = path.split("/")
    if any(part in ("..", ".") for part in parts):
        refuse("REFUSED_PATH_TRAVERSAL", path)
    if any(part == "" for part in parts):
        refuse("REFUSED_INVALID_MANIFEST", f"empty path segment: {path}")
    return path


def validate(manifest: object) -> list:
    """Return the validated entries or raise a typed refusal. Never mutates the input."""
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_KEYS:
        refuse("REFUSED_MALFORMED_ARCHIVE", "manifest shape differs from the frozen schema")
    if manifest["schema"] != SCHEMA:
        refuse("REFUSED_MALFORMED_ARCHIVE", manifest["schema"])
    if manifest["version"] != VERSION:
        refuse("REFUSED_UNKNOWN_VERSION", manifest["version"])
    if not isinstance(manifest["template"], str) or not manifest["template"]:
        refuse("REFUSED_INVALID_MANIFEST", "template name is not a non-empty string")
    entries = manifest["entries"]
    if not isinstance(entries, list) or not entries:
        refuse("REFUSED_MALFORMED_ARCHIVE", "entries is not a non-empty list")
    if len(entries) > MAX_ENTRIES:
        refuse("REFUSED_OVERSIZE", f"{len(entries)} entries exceeds {MAX_ENTRIES}")

    total = 0
    seen: set[str] = set()
    checked = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
            refuse("REFUSED_MALFORMED_ARCHIVE", "entry shape differs from the frozen schema")
        if entry["mode"] == "symlink":
            refuse("REFUSED_SYMLINK_ESCAPE", entry.get("path"))
        if entry["mode"] != "file":
            refuse("REFUSED_INVALID_MANIFEST", entry["mode"])
        path = _check_path(entry["path"])
        if path in seen:
            refuse("REFUSED_DUPLICATE_ENTRY", path)
        seen.add(path)
        content = entry["content"]
        if not isinstance(content, str):
            refuse("REFUSED_INVALID_MANIFEST", f"content is not text: {path}")
        size = len(content.encode("utf-8"))
        if size > MAX_ENTRY_BYTES:
            refuse("REFUSED_OVERSIZE", f"{path} is {size} bytes")
        total += size
        checked.append({"path": path, "content": content, "mode": "file"})
    if total > MAX_TOTAL_BYTES:
        refuse("REFUSED_OVERSIZE", f"archive is {total} bytes")
    if manifest["payload_digest"] != payload_digest(checked):
        refuse("REFUSED_DIGEST", manifest["payload_digest"])
    return checked


def install(manifest: object, dest) -> dict:
    """Install a validated archive into an absent or empty directory and return a receipt."""
    target = pathlib.Path(dest)
    entries = validate(manifest)
    if target.exists():
        if not target.is_dir() or any(target.iterdir()):
            refuse("REFUSED_DIRTY_INPUT", str(target))
    target.mkdir(parents=True, exist_ok=True)
    root = target.resolve()
    written = []
    for entry in entries:
        path = target / entry["path"]
        resolved = path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            refuse("REFUSED_PATH_TRAVERSAL", entry["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(entry["content"].encode("utf-8"))
        written.append(entry["path"])
    return {"installed": len(written), "paths": sorted(written),
            "digest": payload_digest(entries), "root": str(target),
            "network": False, "symlinks": 0}


__all__ = ["SCHEMA", "VERSION", "canonical", "install", "payload_digest", "validate", "Refused"]
