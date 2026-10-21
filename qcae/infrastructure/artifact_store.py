"""Content-addressed artifact store — Book IV 9.1 / Book V 13.3.

Raw evidence artifacts live outside the metadata database, addressed purely
by their sha256 digest (13.3 Content Addressing):

    <root>/sha256/ab/cd/<full-digest>

Properties (P1 spec §6):

- digest before persistence; identity derives from content, never filename;
- same bytes -> same identity (duplicate put is idempotent);
- different bytes -> different identity (no silent overwrite — a digest/file
  collision is a corruption event and raises);
- atomic write (temp file + rename in the same directory);
- retrieval verifies the digest and detects corruption;
- path traversal is impossible: paths are constructed only from validated
  hex digests, never caller strings.

Artifact bytes are opaque here. Classification/rights metadata belongs to
the EvidenceArtifact metadata records, not the blob store.
"""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path

from qcae.core.errors import QcaeValidationError

__all__ = [
    "DIGEST_ALGORITHM",
    "ArtifactCorruptionError",
    "ArtifactCollisionError",
    "ContentAddressedArtifactStore",
]

DIGEST_ALGORITHM = "sha256"
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class ArtifactCorruptionError(Exception):
    """Stored bytes no longer match their digest (bit rot / tampering)."""


class ArtifactCollisionError(Exception):
    """A stored file under one digest contains different bytes (corruption or
    hash collision). Never silently overwritten."""


def _require_digest(digest: str) -> str:
    if not isinstance(digest, str) or not _DIGEST_RE.fullmatch(digest):
        raise QcaeValidationError(
            f"artifact digest must be a lowercase sha256 hex string (64 chars), got {digest!r}"
        )
    return digest


class ContentAddressedArtifactStore:
    """Filesystem store keyed by sha256. Callers cannot choose destinations."""

    def __init__(self, root: os.PathLike[str] | str) -> None:
        self._root = Path(root)
        self._algo_dir = self._root / DIGEST_ALGORITHM
        self._algo_dir.mkdir(parents=True, exist_ok=True)

    # -- write path --------------------------------------------------------

    def put_bytes(self, data: bytes) -> str:
        """Persist raw bytes; return the digest. Idempotent for same content."""
        digest = hashlib.sha256(data).hexdigest()
        final = self._path_for(digest)
        if final.exists():
            existing = final.read_bytes()
            if existing == data:
                return digest  # idempotent duplicate put
            raise ArtifactCollisionError(
                f"file for digest {digest} exists with different content"
            )
        self._atomic_write(final, data)
        # Re-verify after write: detect on-disk mutation/collision races.
        if final.read_bytes() != data:
            raise ArtifactCollisionError(
                f"post-write verification failed for digest {digest}"
            )
        return digest

    def put_file(self, path: os.PathLike[str] | str) -> str:
        """Digest then persist an existing file's bytes."""
        data = Path(path).read_bytes()
        return self.put_bytes(data)

    # -- read path ---------------------------------------------------------

    def get_bytes(self, digest: str) -> bytes:
        """Retrieve bytes by digest, verifying integrity on every read."""
        _require_digest(digest)
        final = self._path_for(digest)
        if not final.exists():
            raise FileNotFoundError(f"no artifact stored for digest {digest}")
        data = final.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != digest:
            raise ArtifactCorruptionError(
                f"artifact {digest} corrupted: stored bytes hash to {actual}"
            )
        return data

    def verify(self, digest: str) -> bool:
        """Integrity check without materializing bytes into caller code."""
        _require_digest(digest)
        final = self._path_for(digest)
        if not final.exists():
            return False
        h = hashlib.sha256()
        with final.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest() == digest

    def contains(self, digest: str) -> bool:
        _require_digest(digest)
        return self._path_for(digest).exists()

    # -- internals ---------------------------------------------------------

    def _path_for(self, digest: str) -> Path:
        """Filesystem path derived ONLY from a validated hex digest."""
        _require_digest(digest)  # traversal injection rejected here
        return self._algo_dir / digest[:2] / digest[2:4] / digest

    @staticmethod
    def _atomic_write(target: Path, data: bytes) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), prefix=".tmp-")
        try:
            with os.fdopen(fd, "wb") as tmp:
                tmp.write(data)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp_name, target)  # atomic on same filesystem
        except BaseException:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
