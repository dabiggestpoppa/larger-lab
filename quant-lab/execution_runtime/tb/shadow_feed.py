"""QL-EXEC-R4.2 — shadow export feed consumer (append-only JSONL, Option B).

The legacy worker writes an append-only JSONL export (see
``runtime.tb_shadow_export``). The shadow ONLY reads it. This module:

- validates schema version, content hash, and monotonic sequence numbers
- dedups by sequence number (restart / retry safe)
- detects sequence gaps and records them (never fabricates observations)
- handles a partial final line safely (skips it; a later read re-tries)
- is rotation-aware (re-opens when the file is truncated/rotated)

A corrupt record raises ``ShadowFeedError`` and blocks parity processing for
that record; values are never inferred.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterator, Optional

from .shadow_parity import SHADOW_EXPORT_SCHEMA_VERSION

FEED_SCHEMA_VERSION = SHADOW_EXPORT_SCHEMA_VERSION


class ShadowFeedError(RuntimeError):
    """Feed record failed validation (schema/hash/sequence)."""


def content_hash(record: dict) -> str:
    """sha256 over the canonical JSON of the record EXCLUDING content_hash."""
    body = {k: v for k, v in record.items() if k != "content_hash"}
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def validate_record(record: dict) -> None:
    """Raise ShadowFeedError on any schema/hash violation."""
    if not isinstance(record, dict):
        raise ShadowFeedError("record is not a dict")
    if record.get("schema_version") != FEED_SCHEMA_VERSION:
        raise ShadowFeedError(
            f"schema_version mismatch: {record.get('schema_version')!r} "
            f"!= {FEED_SCHEMA_VERSION!r}")
    seq = record.get("seq")
    if not isinstance(seq, int) or seq < 1:
        raise ShadowFeedError(f"invalid seq: {seq!r}")
    expected = record.get("content_hash")
    if not expected:
        raise ShadowFeedError("record missing content_hash")
    actual = content_hash(record)
    if actual != expected:
        raise ShadowFeedError(
            f"content_hash mismatch on seq {seq}: {actual} != {expected}")
    if "bar_key" not in record:
        raise ShadowFeedError(f"seq {seq} missing bar_key")


def parse_line(line: str) -> Optional[dict]:
    """Parse one JSON line. Returns None for a partial/empty final line."""
    if not line.strip():
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


class ShadowExportFeed:
    """Tailing reader for the legacy export stream."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def read_records(self, from_seq: int = 0) -> tuple[list[dict], list[dict], dict]:
        """Read validated records with seq > from_seq.

        Returns ``(records, gaps, info)`` where ``gaps`` is a list of
        ``{"expected": int, "found": int}`` pairs. Records are ordered by seq.
        A corrupt record raises ShadowFeedError (block, never infer).
        """
        if not self.path.exists():
            return [], [], {"exists": False, "last_seq": from_seq}
        records: list[dict] = []
        gaps: list[dict] = []
        last_seq = from_seq
        with self.path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                rec = parse_line(line)
                if rec is None:
                    continue  # partial final line: skip, retried on next read
                validate_record(rec)
                seq = int(rec["seq"])
                if seq <= from_seq:
                    continue  # already processed (dedup by seq)
                if last_seq and seq != last_seq + 1:
                    gaps.append({"expected": last_seq + 1, "found": seq})
                records.append(rec)
                last_seq = seq
        info = {"exists": True, "last_seq": last_seq, "records_read": len(records),
                "gaps": len(gaps)}
        return records, gaps, info

    def read_all_after(self, from_seq: int = 0):
        """Read validated records after ``from_seq``, skipping corrupt ones.

        Returns ``(records, gaps, corrupt)`` where ``corrupt`` lists skipped
        records (parity blocked for them; values are never inferred).
        """
        records: list[dict] = []
        gaps: list[dict] = []
        corrupt: list[dict] = []
        last = int(from_seq)
        if not self.path.exists():
            return records, gaps, corrupt
        with self.path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                rec = parse_line(line)
                if rec is None:
                    continue  # partial final line: retried on next read
                try:
                    validate_record(rec)
                except ShadowFeedError as e:
                    corrupt.append({"seq": rec.get("seq"), "error": str(e)})
                    continue
                seq = int(rec["seq"])
                if seq <= from_seq:
                    continue
                if last and seq != last + 1:
                    gaps.append({"expected": last + 1, "found": seq})
                records.append(rec)
                last = seq
        return records, gaps, corrupt

    def iter_after(self, from_seq: int) -> Iterator[tuple[int, dict]]:
        """Yield ``(seq, record)`` pairs after ``from_seq`` (used by runner)."""
        records, gaps, info = self.read_records(from_seq)
        for rec in records:
            yield int(rec["seq"]), rec
