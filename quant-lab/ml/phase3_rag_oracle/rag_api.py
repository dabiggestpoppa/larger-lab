"""
RAG Oracle — FastAPI Endpoints
================================
Provides API endpoints for the RAG Oracle:
- POST /api/rag/index — Build/rebuild the vector index
- POST /api/rag/query — Query the manual for matching rules
- GET /api/rag/stats — Index statistics
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

from .vector_store import RAGVectorStore
from .query_engine import RAGQueryEngine

router = APIRouter(prefix="/api/rag", tags=["rag-oracle"])

# Global instances (initialized on first use)
_store: Optional[RAGVectorStore] = None
_engine: Optional[RAGQueryEngine] = None


def get_store() -> RAGVectorStore:
    global _store
    if _store is None:
        _store = RAGVectorStore()
    return _store


def get_engine() -> RAGQueryEngine:
    global _engine
    if _engine is None:
        _engine = RAGQueryEngine(get_store())
    return _engine


@router.get("/stats")
async def get_stats():
    """Get index statistics."""
    store = get_store()
    return {
        "total_chunks": store.count(),
        "status": "ready" if store.count() > 0 else "empty",
    }


@router.post("/index")
async def build_index(pdf_dir: str = "quant-lab/reports/predecessor",
                      json_dir: str = "quant-lab/data/holy_grail_extracted"):
    """Build or rebuild the RAG vector index."""
    store = get_store()

    pdf_path = Path(pdf_dir)
    json_path = Path(json_dir)

    total = 0

    # Ingest PDF text files
    if pdf_path.exists():
        count = store.ingest_pdf_directory(str(pdf_path))
        total += count

    # Ingest JSON knowledge bases
    if json_path.exists():
        for json_file in json_path.glob("*.json"):
            count = store.ingest_json_knowledge(str(json_file))
            total += count

    return {
        "status": "ok",
        "chunks_ingested": total,
        "total_chunks": store.count(),
    }


@router.post("/query")
async def query_manual(
    query: str,
    n_results: int = 5,
    asset: Optional[str] = None,
    chunk_type: Optional[str] = None,
):
    """Query the manual for matching rules."""
    engine = get_engine()
    store = get_store()

    if store.count() == 0:
        raise HTTPException(status_code=400, detail="Index is empty. Build index first.")

    results = store.query(
        query_text=query,
        n_results=n_results,
        asset_filter=asset,
        chunk_type_filter=chunk_type,
    )

    return {
        "query": query,
        "results": results,
        "count": len(results),
    }


@router.post("/market-query")
async def query_market_state(
    features: dict,
    symbol: str = "EURUSD",
):
    """Query the manual using current market state features."""
    engine = get_engine()
    store = get_store()

    if store.count() == 0:
        raise HTTPException(status_code=400, detail="Index is empty. Build index first.")

    results = engine.query_market_state(features, symbol)

    return {
        "symbol": symbol,
        "features": features,
        "results": results,
        "count": len(results),
    }
