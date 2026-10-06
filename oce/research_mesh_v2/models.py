from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class SourceStatus(str, Enum):
    OK = "OK"
    NO_RESULTS = "NO_RESULTS"
    PARTIAL_RESULTS = "PARTIAL_RESULTS"
    RATE_LIMITED = "RATE_LIMITED"
    AUTH_FAILURE = "AUTH_FAILURE"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"
    UNSUPPORTED_QUERY = "UNSUPPORTED_QUERY"
    NOT_CONFIGURED = "NOT_CONFIGURED"


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    source: str
    source_id: str
    title: str
    abstract: str = ""
    url: str = ""
    doi: str = ""
    year: Optional[int] = None
    authors: tuple[str, ...] = ()
    citation_count: Optional[int] = None
    acquired_at: str = ""
    content_sha256: str = ""
    raw_payload_sha256: str = ""
    source_revision: str = "observed"
    parser_version: str = "rmv2-v0"
    rights_class: str = "PUBLIC_METADATA"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["authors"] = list(self.authors)
        return data


@dataclass(frozen=True)
class ResearchResult:
    query: str
    source: str
    status: SourceStatus
    records: tuple[EvidenceRecord, ...] = ()
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "source": self.source,
            "status": self.status.value,
            "records": [r.to_dict() for r in self.records],
            "note": self.note,
        }
