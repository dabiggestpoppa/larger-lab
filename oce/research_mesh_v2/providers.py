from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List

from .identity import canonical_json_bytes, evidence_identity, sha256_bytes
from .models import EvidenceRecord, ResearchResult, SourceStatus

USER_AGENT = "oce-research-mesh-v2/0.1 (institutional-research)"


def _get(url: str, headers: Dict[str, str] | None = None, timeout: int = 30) -> bytes:
    h = {"User-Agent": USER_AGENT}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _record(source: str, source_id: str, title: str, raw: Any, **kwargs: Any) -> EvidenceRecord:
    acquired_at = datetime.now(timezone.utc).isoformat()
    raw_bytes = canonical_json_bytes(raw) if not isinstance(raw, (str, bytes)) else (
        raw.encode("utf-8") if isinstance(raw, str) else raw
    )
    canonical = {
        "source": source,
        "source_id": source_id,
        "title": title,
        **kwargs,
    }
    return EvidenceRecord(
        evidence_id=evidence_identity(source, source_id, title),
        source=source,
        source_id=source_id,
        title=title,
        abstract=kwargs.get("abstract", "") or "",
        url=kwargs.get("url", "") or "",
        doi=kwargs.get("doi", "") or "",
        year=kwargs.get("year"),
        authors=tuple(kwargs.get("authors", ()) or ()),
        citation_count=kwargs.get("citation_count"),
        acquired_at=acquired_at,
        content_sha256=sha256_bytes(canonical_json_bytes(canonical)),
        raw_payload_sha256=sha256_bytes(raw_bytes),
    )


def search_openalex(query: str, limit: int = 10) -> ResearchResult:
    params = urllib.parse.urlencode({"search": query, "per-page": max(1, min(limit, 100))})
    url = f"https://api.openalex.org/works?{params}"
    try:
        data = json.loads(_get(url))
        out: List[EvidenceRecord] = []
        for w in data.get("results", []):
            authors = [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])]
            loc = w.get("primary_location") or {}
            out.append(_record(
                "openalex",
                str(w.get("id", "")).replace("https://openalex.org/", ""),
                w.get("display_name", "") or "",
                w,
                abstract="",
                url=loc.get("landing_page_url", "") or "",
                doi=str(w.get("doi") or "").replace("https://doi.org/", ""),
                year=w.get("publication_year"),
                authors=authors,
                citation_count=w.get("cited_by_count"),
            ))
        return ResearchResult(query, "openalex", SourceStatus.OK if out else SourceStatus.NO_RESULTS, tuple(out))
    except urllib.error.HTTPError as e:
        status = SourceStatus.RATE_LIMITED if e.code == 429 else SourceStatus.PROVIDER_FAILURE
        return ResearchResult(query, "openalex", status, note=f"HTTP {e.code}")
    except Exception as e:
        return ResearchResult(query, "openalex", SourceStatus.PROVIDER_FAILURE, note=type(e).__name__)


def search_semantic_scholar(query: str, limit: int = 10) -> ResearchResult:
    params = urllib.parse.urlencode({
        "query": query,
        "limit": max(1, min(limit, 100)),
        "fields": "paperId,title,abstract,authors,year,url,citationCount,externalIds",
    })
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?{params}"
    try:
        data = json.loads(_get(url))
        out: List[EvidenceRecord] = []
        for w in data.get("data", []):
            ext = w.get("externalIds") or {}
            out.append(_record(
                "semantic_scholar",
                w.get("paperId", "") or "",
                w.get("title", "") or "",
                w,
                abstract=w.get("abstract", "") or "",
                url=w.get("url", "") or "",
                doi=ext.get("DOI", "") or "",
                year=w.get("year"),
                authors=[a.get("name", "") for a in w.get("authors", [])],
                citation_count=w.get("citationCount"),
            ))
        return ResearchResult(query, "semantic_scholar", SourceStatus.OK if out else SourceStatus.NO_RESULTS, tuple(out))
    except urllib.error.HTTPError as e:
        status = SourceStatus.RATE_LIMITED if e.code == 429 else SourceStatus.PROVIDER_FAILURE
        return ResearchResult(query, "semantic_scholar", status, note=f"HTTP {e.code}")
    except Exception as e:
        return ResearchResult(query, "semantic_scholar", SourceStatus.PROVIDER_FAILURE, note=type(e).__name__)


def search_arxiv(query: str, limit: int = 10) -> ResearchResult:
    params = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max(1, min(limit, 100)),
        "sortBy": "relevance",
        "sortOrder": "descending",
    })
    url = f"https://export.arxiv.org/api/query?{params}"
    try:
        raw = _get(url)
        root = ET.fromstring(raw)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        out: List[EvidenceRecord] = []
        for entry in root.findall("a:entry", ns):
            title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip().replace("\n", " ")
            source_url = entry.findtext("a:id", default="", namespaces=ns) or ""
            source_id = source_url.rsplit("/", 1)[-1]
            abstract = (entry.findtext("a:summary", default="", namespaces=ns) or "").strip().replace("\n", " ")
            published = entry.findtext("a:published", default="", namespaces=ns) or ""
            authors = [
                (a.findtext("a:name", default="", namespaces=ns) or "").strip()
                for a in entry.findall("a:author", ns)
            ]
            year = int(published[:4]) if len(published) >= 4 and published[:4].isdigit() else None
            out.append(_record(
                "arxiv",
                source_id,
                title,
                ET.tostring(entry, encoding="unicode"),
                abstract=abstract,
                url=source_url,
                year=year,
                authors=authors,
            ))
        return ResearchResult(query, "arxiv", SourceStatus.OK if out else SourceStatus.NO_RESULTS, tuple(out))
    except urllib.error.HTTPError as e:
        status = SourceStatus.RATE_LIMITED if e.code == 429 else SourceStatus.PROVIDER_FAILURE
        return ResearchResult(query, "arxiv", status, note=f"HTTP {e.code}")
    except Exception as e:
        return ResearchResult(query, "arxiv", SourceStatus.PROVIDER_FAILURE, note=type(e).__name__)
