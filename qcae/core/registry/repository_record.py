"""RepositoryRecord — a source container, provider-neutral (P1-R1 §6).

A repository is a CONTAINER; capability is the durable semantic object
(master-prompt doctrine §1). This record makes any source container
addressable without making any provider the ontology:

- ``canonical_locator`` is a stable URI-ish string the operator's tooling
  defines (``git+https://...``, ``pkg:pypi/name@version``, ``file:///path``,
  ``paper:arXiv:1234.5678`` — all equally valid);
- ``source_kind`` declares the container class (GIT, PACKAGE, LOCAL_PATH,
  ARCHIVE, PAPER_IMPL, OTHER) without vendor semantics;
- GitHub URLs, package coordinates, and local paths are representable as
  locators, never as identity.

Revision handling (§7): a record is one observed revision. Multiple
revisions of one repository identity coexist; identity is the (source_kind,
canonical_locator) pair. Nothing is overwritten — a new observation is a new
record.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord
from qcae.core.validation import require_identifier, require_non_empty_str

__all__ = ["RepositorySourceKind", "RepositoryStatus", "RepositoryRecord"]


class RepositorySourceKind(StrEnum):
    """Container classes, provider-neutral (canon 1.3.3 source containers)."""

    GIT = "GIT"
    PACKAGE = "PACKAGE"
    LOCAL_PATH = "LOCAL_PATH"
    ARCHIVE = "ARCHIVE"
    PAPER_IMPL = "PAPER_IMPL"
    OTHER = "OTHER"


class RepositoryStatus(StrEnum):
    """Observation lifecycle of the container record itself."""

    KNOWN = "KNOWN"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACQUIRED = "ACQUIRED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True)
class RepositoryRecord(SerializableRecord):
    SCHEMA_VERSION = 1

    # Identity: (source_kind, canonical_locator) names the container;
    # repository_id is the stable internal handle (canon 1.3.16).
    repository_id: str
    source_kind: RepositorySourceKind
    canonical_locator: str
    revision: str

    display_name: str = ""
    provenance: str = ""            # who/what observed this container
    first_seen_at: str = ""
    last_observed_at: str = ""
    status: RepositoryStatus = RepositoryStatus.KNOWN
    metadata_digest: str = ""       # sha256 of external metadata payload, if any
    supersedes_record: str = ""     # prior repository_id when identity migrates

    _COERCIONS = {
        "source_kind": lambda v: RepositorySourceKind(v)
        if isinstance(v, str) and v in {k.value for k in RepositorySourceKind} else v,
        "status": lambda v: RepositoryStatus(v)
        if isinstance(v, str) and v in {k.value for k in RepositoryStatus} else v,
    }

    def validate(self) -> None:
        require_identifier(self.repository_id, "repository_id")
        if not isinstance(self.source_kind, RepositorySourceKind):
            raise QcaeValidationError(
                f"source_kind must be a RepositorySourceKind member, got {self.source_kind!r}"
            )
        require_non_empty_str(self.canonical_locator, "canonical_locator")
        require_non_empty_str(self.revision, "revision")
        if not isinstance(self.status, RepositoryStatus):
            raise QcaeValidationError(
                f"status must be a RepositoryStatus member, got {self.status!r}"
            )
        if self.display_name:
            require_non_empty_str(self.display_name, "display_name")
        if self.metadata_digest and (
            not isinstance(self.metadata_digest, str) or len(self.metadata_digest) < 8
        ):
            raise QcaeValidationError(
                f"metadata_digest must be a content digest, got {self.metadata_digest!r}"
            )
        if self.supersedes_record:
            require_identifier(self.supersedes_record, "supersedes_record")
            if self.supersedes_record == self.repository_id:
                raise QcaeValidationError("repository record cannot supersede itself")
        for ts_field in ("first_seen_at", "last_observed_at"):
            value = getattr(self, ts_field)
            if value and not isinstance(value, str):
                raise QcaeValidationError(f"{ts_field} must be a string timestamp")
