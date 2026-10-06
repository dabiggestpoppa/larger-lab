from __future__ import annotations

from typing import Iterable, List

from .models import ResearchResult, SourceStatus
from .providers import search_arxiv, search_openalex, search_semantic_scholar
from .store import EvidenceStore


PROVIDERS = {
    "openalex": search_openalex,
    "arxiv": search_arxiv,
    "semantic_scholar": search_semantic_scholar,
    "s2": search_semantic_scholar,
}


class ResearchMesh:
    """Small standalone-first service surface for Hermes and local operators."""

    def __init__(self, store_path: str = "data/research_mesh_v2/evidence.sqlite3"):
        self.store = EvidenceStore(store_path)

    def close(self) -> None:
        self.store.close()

    def search(self, query: str, source: str = "openalex", limit: int = 10, persist: bool = True) -> ResearchResult:
        provider = PROVIDERS.get(source)
        if provider is None:
            return ResearchResult(query, source, SourceStatus.NOT_CONFIGURED, note="unknown provider")
        result = provider(query, limit)
        if persist and result.records:
            self.store.put_many(result.records)
        return result

    def search_all(self, query: str, limit_per_source: int = 5, persist: bool = True) -> List[ResearchResult]:
        results = []
        for source in ("openalex", "arxiv", "semantic_scholar"):
            results.append(self.search(query, source, limit_per_source, persist=persist))
        return results

    def query_local(self, query: str, limit: int = 20) -> List[dict]:
        return self.store.search(query, limit)
