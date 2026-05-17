"""
OCE Phase 4 — Advanced Structural Memory & Observer Memory Integration
=====================================================================
Six advanced endpoints:

1. POST /memory/reconstruct          — Reconstruct observer state from sparse anchors
2. POST /memory/consolidate          — Consolidate memory across layers (WORK→LEARNED→KNOWLEDGE)
3. POST /observers/{id}/memory/bind  — Bind a memory entry to an observer relationship
4. GET  /memory/graph                — Knowledge graph of memory relationships
5. POST /memory/search/advanced      — Advanced search with graph traversal
6. GET  /memory/export/{format}      — Export memory as json, markdown, or yaml

Register all endpoints via ``register_phase4_endpoints(app)``.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from structural_memory import (
    MemoryEntry,
    MemoryLayer,
    StructuralMemory,
    get_structural_memory,
)

logger = logging.getLogger("oce.phase4")

# ─── Binding DB ───────────────────────────────────────────────────────────────
_BINDING_DB: Path = Path(__file__).parent / "data" / "observer_memory_bindings.db"


def _bconn() -> sqlite3.Connection:
    _BINDING_DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(_BINDING_DB))
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c


def _init_bdb():
    with _bconn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS observer_memory_bindings (
            binding_id TEXT PRIMARY KEY, observer_id TEXT NOT NULL,
            entry_id TEXT NOT NULL,
            relationship TEXT NOT NULL CHECK(relationship IN (
                'created_by','processed_by','related_to')),
            created_at TEXT NOT NULL)""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_b_obs ON observer_memory_bindings(observer_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_b_entry ON observer_memory_bindings(entry_id)")


def _sm() -> StructuralMemory:
    try:
        return get_structural_memory()
    except Exception:
        return StructuralMemory()


# ─── Models ───────────────────────────────────────────────────────────────────

class ReconstructRequest(BaseModel):
    observer_id: str
    anchor_ids: List[str] = Field(..., min_length=1)
    include_timeline: bool = False
    timeline_limit: int = Field(50, ge=1, le=500)

class ReconstructResponse(BaseModel):
    observer_id: str
    reconstructed_state: Dict[str, Any]
    confidence: float

class ConsolidateRequest(BaseModel):
    source_layer: str
    target_layer: str
    max_entries: int = Field(100, ge=1, le=10_000)
    compress_first: bool = True
    compress_max: int = 1000

class ConsolidateResponse(BaseModel):
    consolidated: int
    remaining: int

class BindMemoryRequest(BaseModel):
    entry_id: str
    relationship: str  # created_by | processed_by | related_to

class GraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class AdvancedSearchRequest(BaseModel):
    query: str = ""
    graph_depth: int = Field(2, ge=0, le=5)
    min_confidence: float = Field(0.5, ge=0.0, le=1.0)
    layers: List[str] = Field(default_factory=lambda: ["WORK", "LEARNED", "KNOWLEDGE"])
    tags: Optional[List[str]] = None
    limit: int = Field(20, ge=1, le=200)

class AdvancedSearchResponse(BaseModel):
    entries: List[Dict[str, Any]]
    graph_context: List[Dict[str, Any]]
    total_found: int
    returned: int

class ExportFormat(str, Enum):
    json = "json"
    markdown = "markdown"
    yaml = "yaml"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _preview(content: Dict[str, Any], n: int = 120) -> str:
    t = content.get("title", content.get("name", ""))
    if t:
        return str(t)[:n]
    s = json.dumps(content, default=str)
    return s[:n] + ("…" if len(s) > n else "")


def _yaml_escape(v: str) -> str:
    return f'"{v}"' if any(ch in v for ch in ':{}[],"\'#&*?|->!%@`') else v


def _simple_yaml(data: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for item in data:
        lines.append("-")
        for k, v in item.items():
            if isinstance(v, dict):
                lines.append(f"  {k}:")
                for dk, dv in v.items():
                    lines.append(f"    {dk}: {_yaml_escape(str(dv))}")
            elif isinstance(v, list):
                lines.append(f"  {k}:")
                for el in v:
                    lines.append(f"    - {_yaml_escape(str(el))}")
            else:
                lines.append(f"  {k}: {_yaml_escape(str(v))}")
        lines.append("")
    return "\n".join(lines)


def _entry_dict(e: MemoryEntry) -> Dict[str, Any]:
    return {
        "entry_id": e.entry_id, "layer": e.layer.value,
        "content": e.content, "tags": e.tags,
        "created_at": e.created_at.isoformat(), "source": e.source,
    }


# ─── Endpoints ────────────────────────────────────────────────────────────────

async def memory_reconstruct(request: ReconstructRequest) -> ReconstructResponse:
    """POST /memory/reconstruct — Reconstruct observer state from sparse anchors."""
    sm = _sm()
    anchors: List[MemoryEntry] = []
    missing: List[str] = []
    with sm._conn() as conn:
        for aid in request.anchor_ids:
            row = conn.execute("SELECT * FROM memory_entries WHERE entry_id = ?", (aid,)).fetchone()
            if row:
                anchors.append(sm._row_to_entry(row))
            else:
                missing.append(aid)
    if not anchors:
        raise HTTPException(404, f"No anchor entries found for IDs: {request.anchor_ids}")
    confidence = len(anchors) / len(request.anchor_ids)
    merged: Dict[str, Any] = {}
    for entry in sorted(anchors, key=lambda e: e.created_at):
        if isinstance(entry.content, dict):
            merged.update(entry.content)
    if request.include_timeline:
        timeline = sm.get_timeline(request.observer_id, end_time=datetime.now(timezone.utc))
        merged["_timeline"] = [_entry_dict(e) for e in timeline[: request.timeline_limit]]
    merged["_anchors_used"] = len(anchors)
    merged["_anchors_missing"] = len(missing)
    if missing:
        merged["_missing_ids"] = missing
    return ReconstructResponse(observer_id=request.observer_id, reconstructed_state=merged, confidence=round(confidence, 4))


async def memory_consolidate(request: ConsolidateRequest) -> ConsolidateResponse:
    """POST /memory/consolidate — Move entries source_layer → target_layer."""
    try:
        src, tgt = MemoryLayer(request.source_layer.upper()), MemoryLayer(request.target_layer.upper())
    except ValueError as exc:
        raise HTTPException(400, f"Invalid layer: {exc}") from exc
    if src == tgt:
        raise HTTPException(400, "source_layer and target_layer must differ")
    sm = _sm()
    if request.compress_first:
        sm.compress(src, max_entries=request.compress_max)
    with sm._conn() as conn:
        rows = conn.execute(
            "SELECT * FROM memory_entries WHERE layer = ? ORDER BY created_at ASC LIMIT ?",
            (src.value, request.max_entries)).fetchall()
    count = 0
    for row in rows:
        entry = sm._row_to_entry(row)
        entry.layer = tgt
        entry.updated_at = datetime.now(timezone.utc)
        sm.store(entry)
        with sm._conn() as conn:
            conn.execute("DELETE FROM memory_entries WHERE entry_id = ? AND layer = ?",
                         (entry.entry_id, src.value))
        count += 1
    with sm._conn() as conn:
        remaining = conn.execute("SELECT COUNT(*) FROM memory_entries WHERE layer = ?",
                                (src.value,)).fetchone()[0]
    logger.info(f"Consolidated {count} entries {src.value}→{tgt.value}; {remaining} remain")
    return ConsolidateResponse(consolidated=count, remaining=remaining)


async def observer_memory_bind(observer_id: str, request: BindMemoryRequest) -> Dict[str, Any]:
    """POST /observers/{id}/memory/bind — Bind a memory entry to an observer."""
    VALID = {"created_by", "processed_by", "related_to"}
    if request.relationship not in VALID:
        raise HTTPException(400, f"Invalid relationship. Must be one of {VALID}")
    sm = _sm()
    with sm._conn() as conn:
        if not conn.execute("SELECT 1 FROM memory_entries WHERE entry_id = ?",
                            (request.entry_id,)).fetchone():
            raise HTTPException(404, f"Memory entry not found: {request.entry_id}")
    _init_bdb()
    bid = str(uuid.uuid4())
    with _bconn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO observer_memory_bindings VALUES (?,?,?,?,?)",
            (bid, observer_id, request.entry_id, request.relationship,
             datetime.now(timezone.utc).isoformat()))
    return {"binding_id": bid, "observer_id": observer_id,
            "entry_id": request.entry_id, "relationship": request.relationship}


async def memory_graph(
    layer: Optional[str] = None,
    observer_id: Optional[str] = None,
    limit: int = Query(200, ge=1, le=2000),
) -> GraphResponse:
    """GET /memory/graph — Knowledge graph of memory relationships."""
    sm = _sm()
    with sm._conn() as conn:
        sql, params = "SELECT * FROM memory_entries WHERE 1=1", []
        if layer:
            sql += " AND layer = ?"; params.append(layer.upper())
        if observer_id:
            sql += " AND source = ?"; params.append(observer_id)
        sql += " ORDER BY created_at DESC LIMIT ?"; params.append(limit)
        rows = conn.execute(sql, params).fetchall()
    entries = [sm._row_to_entry(r) for r in rows]
    nodes = [{"id": e.entry_id, "layer": e.layer.value,
              "content_preview": _preview(e.content), "tags": e.tags,
              "created_at": e.created_at.isoformat(), "source": e.source} for e in entries]
    edges: List[Dict[str, Any]] = []
    eids: Set[str] = {e.entry_id for e in entries}
    tag_map: Dict[str, List[str]] = {}
    for e in entries:
        for t in e.tags:
            tag_map.setdefault(t, []).append(e.entry_id)
    seen: Set[Tuple[str, str]] = set()
    for tag, ids in tag_map.items():
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                key = tuple(sorted([ids[i], ids[j]]))
                if key not in seen:
                    seen.add(key)
                    edges.append({"source": key[0], "target": key[1], "type": "shared_tag", "tag": tag})
    _init_bdb()
    with _bconn() as conn:
        for br in conn.execute(
            f"SELECT entry_id, observer_id, relationship FROM observer_memory_bindings WHERE entry_id IN ({','.join('?'*len(eids))})",
            list(eids)).fetchall():
            edges.append({"source": br["observer_id"], "target": br["entry_id"], "type": br["relationship"]})
    return GraphResponse(nodes=nodes, edges=edges)


async def memory_search_advanced(request: AdvancedSearchRequest) -> AdvancedSearchResponse:
    """POST /memory/search/advanced — Advanced search with graph traversal."""
    sm = _sm()
    layers = []
    for l in request.layers:
        try:
            layers.append(MemoryLayer(l.upper()))
        except ValueError:
            raise HTTPException(400, f"Invalid layer: {l}")
    all_entries: Dict[str, MemoryEntry] = {}
    for layer in layers:
        for h in sm.search(query=request.query, layer=layer, tags=request.tags, limit=request.limit):
            all_entries[h.entry_id] = h
    graph_ctx: List[Dict[str, Any]] = []
    frontier = set(all_entries.keys())
    visited: Set[str] = set(frontier)
    for depth in range(request.graph_depth):
        if not frontier:
            break
        tag_map: Dict[str, Set[str]] = {}
        for eid in frontier:
            e = all_entries.get(eid)
            if e:
                for t in e.tags:
                    tag_map.setdefault(t, set()).add(eid)
        next_frontier: Set[str] = set()
        for tag, ids in tag_map.items():
            for eid in ids:
                if eid not in visited:
                    visited.add(eid)
                    next_frontier.add(eid)
                    if eid not in all_entries:
                        with sm._conn() as conn:
                            row = conn.execute("SELECT * FROM memory_entries WHERE entry_id = ?",
                                               (eid,)).fetchone()
                        if row:
                            all_entries[eid] = sm._row_to_entry(row)
                for rel in ids:
                    if rel != eid:
                        graph_ctx.append({"from": rel, "to": eid, "via_tag": tag, "depth": depth + 1})
        frontier = next_frontier
    results = [_entry_dict(e) for e in all_entries.values()]
    for r in results:
        r["confidence"] = request.min_confidence
    total = len(results)
    return AdvancedSearchResponse(entries=results[:request.limit], graph_context=graph_ctx,
                                  total_found=total, returned=min(total, request.limit))


async def memory_export(format: str = "json") -> Dict[str, Any]:
    """GET /memory/export/{format} — Export memory as json, markdown, or yaml."""
    fmt = ExportFormat(format.lower())
    sm = _sm()
    with sm._conn() as conn:
        rows = conn.execute("SELECT * FROM memory_entries ORDER BY created_at ASC").fetchall()
    data = [_entry_dict(sm._row_to_entry(r)) for r in rows]
    if fmt == ExportFormat.json:
        return {"format": "json", "entries": data, "count": len(data)}
    if fmt == ExportFormat.markdown:
        return {"format": "markdown", "markdown": sm.export_wiki(), "count": len(data)}
    # yaml
    try:
        import yaml as _yaml  # type: ignore[import-untyped]
        yaml_str = _yaml.dump(data, default_flow_style=False, allow_unicode=True)
    except ImportError:
        yaml_str = _simple_yaml(data)
    return {"format": "yaml", "yaml": yaml_str, "count": len(data)}


# ─── Registration ─────────────────────────────────────────────────────────────

def register_phase4_endpoints(app: FastAPI) -> None:
    """Attach all Phase 4 endpoints to a FastAPI application."""
    _init_bdb()
    app.add_api_route("/memory/reconstruct", memory_reconstruct, methods=["POST"],
                      summary="Reconstruct observer state from sparse anchors")
    app.add_api_route("/memory/consolidate", memory_consolidate, methods=["POST"],
                      summary="Consolidate memory entries across layers")
    app.add_api_route("/observers/{observer_id}/memory/bind", observer_memory_bind, methods=["POST"],
                      summary="Bind a memory entry to an observer")
    app.add_api_route("/memory/graph", memory_graph, methods=["GET"],
                      summary="Knowledge graph of memory relationships")
    app.add_api_route("/memory/search/advanced", memory_search_advanced, methods=["POST"],
                      summary="Advanced memory search with graph traversal")
    app.add_api_route("/memory/export/{format}", memory_export, methods=["GET"],
                      summary="Export memory (json, markdown, yaml)")
    logger.info("Phase 4 endpoints registered")
