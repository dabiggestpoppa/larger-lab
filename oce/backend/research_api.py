"""
L4.1-4.6 — OCE Research Mesh API endpoints.

8 endpoints exposing the research mesh through OCE:
- /api/research/ingest — manual trigger for ingestion
- /api/research/papers — search papers
- /api/research/graph — query knowledge graph
- /api/research/agents — list/control research agents
- /api/research/doctrine — browse doctrine notes
- /api/research/gaps — show detected knowledge gaps
- /api/research/stats — research mesh statistics
- /api/research/config — get/set configuration

Usage:
    from .research_api import register_research_endpoints
    register_research_endpoints(app)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Import research mesh components (will be built by CC/PM/PM2/AS/RL)
try:
    from core.research.ingestion.cache import Cache
    from core.research.distillation.graph_store import GraphStore
    from core.research.agents.queue import TaskQueue, ResearchTask
except ImportError:
    # During initial build, these may not exist yet
    Cache = None
    GraphStore = None
    TaskQueue = None
    ResearchTask = None

# L4.7 — Vault sync engine
try:
    from .vault_sync import VaultSync as _VaultSync
    _vault_sync = _VaultSync()
except ImportError:
    _vault_sync = None

router = APIRouter()


# ─── Models ───────────────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    """Request to trigger ingestion."""
    domains: Optional[List[str]] = None
    max_papers: int = 500
    force: bool = False


class IngestResponse(BaseModel):
    """Response from ingestion trigger."""
    triggered: bool
    papers_ingested: int
    papers_new: int
    duration_seconds: float


class PaperSearchRequest(BaseModel):
    """Request to search papers."""
    query: str = ""
    domain: Optional[str] = None
    year: Optional[int] = None
    limit: int = 50


class ResearchTaskRequest(BaseModel):
    """Request to create a research task."""
    query: str
    domains: Optional[List[str]] = None
    priority: int = 3


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/api/research/stats")
async def get_research_stats() -> Dict[str, Any]:
    """Get research mesh statistics."""
    stats = {
        "papers_ingested": 0,
        "papers_distilled": 0,
        "doctrine_notes": 0,
        "contradictions_found": 0,
        "agents_spawned": 0,
        "graph_nodes": 0,
        "graph_edges": 0,
        "last_ingestion": None,
    }
    
    if Cache:
        try:
            cache = Cache()
            conn = cache._get_connection()
            row = conn.execute(
                "SELECT COUNT(*) FROM papers WHERE status = 'distilled'"
            ).fetchone()
            stats["papers_distilled"] = row[0] if row else 0
            conn.close()
        except Exception:
            pass
    
    if GraphStore:
        try:
            graph = GraphStore()
            stats["graph_nodes"] = graph.get_node_count()
            stats["graph_edges"] = graph.get_edge_count()
        except Exception:
            pass
    
    return stats


@router.post("/api/research/ingest", response_model=IngestResponse)
async def trigger_ingest(request: IngestRequest) -> IngestResponse:
    """
    Manually trigger paper ingestion.
    
    Delegates to the ingestion scheduler (RL's L1.6).
    """
    start_time = datetime.now(timezone.utc)
    
    # Placeholder: actual implementation calls scheduler
    # PM/PM2 will implement openalex_client, arxiv_client, s2_client
    # RL will implement scheduler
    
    return IngestResponse(
        triggered=True,
        papers_ingested=0,
        papers_new=0,
        duration_seconds=(datetime.now(timezone.utc) - start_time).total_seconds(),
    )


@router.post("/api/research/ingest/auto")
async def trigger_auto_ingest() -> Dict[str, Any]:
    """
    Trigger automatic ingestion based on configured domains.
    """
    return {"status": "queued", "message": "Auto-ingest scheduled"}


@router.get("/api/research/papers")
async def search_papers(
    query: str = "",
    domain: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
) -> Dict[str, Any]:
    """
    Search ingested papers.
    
    Uses SQLite full-text search on title + abstract.
    """
    papers = []
    
    if Cache:
        try:
            cache = Cache()
            conn = cache._get_connection()
            
            sql = "SELECT id, doi, title, year, source, citation_count FROM papers"
            conditions = []
            params = []
            
            if query:
                conditions.append("(title LIKE ? OR abstract LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])
            if domain:
                conditions.append("vault_path LIKE ?")
                params.append(f"%{domain}%")
            if year:
                conditions.append("year = ?")
                params.append(year)
            
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            
            sql += f" ORDER BY citation_count DESC LIMIT {limit}"
            
            cursor = conn.execute(sql, params)
            papers = [
                {
                    "id": row[0],
                    "doi": row[1],
                    "title": row[2],
                    "year": row[3],
                    "source": row[4],
                    "citation_count": row[5],
                }
                for row in cursor.fetchall()
            ]
            conn.close()
        except Exception:
            pass
    
    return {"papers": papers, "count": len(papers)}


@router.get("/api/research/papers/{paper_id}")
async def get_paper(paper_id: str) -> Dict[str, Any]:
    """Get a specific paper by ID."""
    if not Cache:
        return {"error": "Cache not available"}
    
    try:
        cache = Cache()
        paper = cache.get_paper(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        return {"paper": paper.__dict__}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/research/graph")
async def query_graph(
    node_id: Optional[str] = None,
    kind: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
) -> Dict[str, Any]:
    """
    Query the knowledge graph.
    
    Returns nodes and edges from the SQLite graph store.
    """
    nodes = []
    edges = []
    
    if GraphStore:
        try:
            graph = GraphStore()
            nodes = graph.query_nodes(kind=kind, limit=limit)
            if node_id:
                edges = graph.query_edges(src_id=node_id, limit=limit)
        except Exception:
            pass
    
    return {"nodes": nodes, "edges": edges}


@router.get("/api/research/graph/stats")
async def get_graph_stats() -> Dict[str, Any]:
    """Get knowledge graph statistics."""
    stats = {"nodes": 0, "edges": 0, "by_kind": {}}
    
    if GraphStore:
        try:
            graph = GraphStore()
            stats["nodes"] = graph.get_node_count()
            stats["edges"] = graph.get_edge_count()
        except Exception:
            pass
    
    return stats


@router.get("/api/research/agents")
async def list_agents(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
) -> Dict[str, Any]:
    """
    List research agents and their tasks.
    
    Shows queue status and active tasks.
    """
    agents = []
    tasks = []
    
    if TaskQueue:
        try:
            queue = TaskQueue()
            tasks = queue.list_tasks(status=status, limit=limit)
            agents = [
                {
                    "task_id": t.id,
                    "query": t.query,
                    "status": t.status,
                    "priority": t.priority,
                    "confidence": t.confidence,
                    "created_at": t.created_at,
                }
                for t in tasks
            ]
        except Exception:
            pass
    
    return {
        "agents": agents,
        "running_count": 0,
        "pending_count": len([t for t in tasks if t.status == "pending"]),
    }


@router.post("/api/research/agents/spawn")
async def spawn_agent(request: ResearchTaskRequest) -> Dict[str, Any]:
    """
    Spawn a research agent for a specific query.
    
    Creates a task in the queue for the research agent to execute.
    """
    if not TaskQueue:
        return {"error": "Task queue not available"}
    
    try:
        queue = TaskQueue()
        task = ResearchTask(
            query=request.query,
            domains=request.domains or [],
            priority=request.priority,
        )
        task_id = queue.enqueue(task)
        return {"task_id": task_id, "status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/research/doctrine")
async def list_doctrine(
    domain: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
) -> Dict[str, Any]:
    """
    List auto-extracted doctrine notes.
    
    Doctrine notes are in the Obsidian vault at o2c/doctrine/{domain}/.
    """
    doctrine_notes = []
    doctrine_root = Path(r"C:\Users\wifik\Downloads\o2c\doctrine")
    
    if doctrine_root.exists():
        try:
            for md_file in doctrine_root.rglob("*.md"):
                if domain and domain not in str(md_file):
                    continue
                content = md_file.read_text(encoding="utf-8")
                doctrine_notes.append({
                    "path": str(md_file.relative_to(doctrine_root)),
                    "title": md_file.stem,
                    "preview": content[:200] + "..." if len(content) > 200 else content,
                })
                if len(doctrine_notes) >= limit:
                    break
        except Exception:
            pass
    
    return {"doctrine": doctrine_notes, "count": len(doctrine_notes)}


@router.get("/api/research/gaps")
async def list_gaps(
    threshold: float = Query(0.4, ge=0.0, le=1.0),
    limit: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """
    List detected knowledge gaps.
    
    Gaps are detected by the gap detector (AS's L3.1).
    """
    gaps = []
    
    # Placeholder: actual implementation uses gap_detector
    # AS will implement gap_detector.py
    
    return {"gaps": gaps, "count": len(gaps)}


@router.get("/api/research/config")
async def get_config() -> Dict[str, Any]:
    """
    Get research mesh configuration.
    
    Shows current domain filters, rate limits, and caps.
    """
    return {
        "domains": [],
        "daily_paper_cap": 500,
        "daily_vault_write_cap": 200,
        "daily_llm_cost_cap_usd": 2.0,
        "max_concurrent_agents": 3,
        "max_task_duration_seconds": 3600,
    }


@router.post("/api/research/config")
async def update_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update research mesh configuration.
    
    Operator-only endpoint for tuning parameters.
    """
    # Placeholder: actual implementation updates config
    return {"status": "updated", "config": config}


# ─── L4.7 — Vault Sync Endpoints ─────────────────────────────────────────────

@router.post("/api/research/vault/sync")
async def sync_vault() -> Dict[str, Any]:
    """
    Trigger vault → graph sync.
    
    Scans Obsidian vault (o2c/research/papers/ and o2c/doctrine/),
    upserts nodes and edges into the knowledge graph.
    """
    if not _vault_sync:
        return {"error": "Vault sync not available", "status": "unavailable"}

    try:
        result = await _vault_sync.sync_vault_to_graph()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/research/vault/stats")
async def vault_stats() -> Dict[str, Any]:
    """Get vault statistics (paper notes, doctrine notes, domains)."""
    if not _vault_sync:
        return {"error": "Vault sync not available", "status": "unavailable"}

    try:
        return _vault_sync.get_vault_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── L4.8 — Telemetry Endpoints ─────────────────────────────────────────────

from .telemetry import Telemetry as _Telemetry
_telemetry = _Telemetry()


@router.get("/api/research/telemetry/daily")
async def get_daily_report(day: Optional[str] = None) -> Dict[str, Any]:
    """
    Get daily telemetry report.
    
    Shows papers ingested, distilled, agents run, $ spent, safety status.
    Query param: day=YYYY-MM-DD (defaults to today)
    """
    return await _telemetry.daily_report(day=day)


@router.get("/api/research/telemetry/audit")
async def get_audit_trail(
    agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
    action: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
) -> Dict[str, Any]:
    """
    Export audit trail with optional filters.
    
    Returns agent_log entries filtered by agent, task, action, or time.
    """
    entries = await _telemetry.audit_trail(
        agent_id=agent_id,
        task_id=task_id,
        action=action,
        since=since,
        limit=limit,
    )
    return {"entries": entries, "count": len(entries)}


@router.get("/api/research/telemetry/safety")
async def get_safety_status() -> Dict[str, Any]:
    """
    Get current safety budget status.
    
    Shows remaining LLM budget, vault write budget, and agent slots.
    """
    llm = await _telemetry.check_llm_budget()
    vault = await _telemetry.check_vault_write_budget()
    agents = await _telemetry.check_agent_slots()
    return {
        "llm_budget": llm,
        "vault_budget": vault,
        "agent_slots": agents,
    }


def register_research_endpoints(app) -> None:
    """Register research endpoints on the OCE FastAPI app."""
    app.include_router(router)