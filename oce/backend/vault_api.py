"""
Vault API Endpoints — Phase 00
FastAPI endpoints for O2C Obsidian Vault.

Supports two vaults:
- DEFAULT (O2C-VAULT/): Internal workspace vault for raw operational traces
- OBSIDIAN (C:\\Users\\wifik\\Downloads\\o2c): Real Obsidian vault for user-visible notes

Use query param ?vault=obsidian to target the real Obsidian vault.
"""

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from core.obsidian.vault_writer import VaultWriter, DEFAULT_VAULT_PATH
from core.obsidian.linker import Linker
from core.obsidian.compressor import compress_trace
from core.obsidian.note_standard import NoteValidator


# Real Obsidian vault path
OBSIDIAN_VAULT_PATH = Path("C:/Users/wifik/Downloads/o2c")
_env_path = os.environ.get("OBSIDIAN_VAULT_PATH")
if _env_path:
    OBSIDIAN_VAULT_PATH = Path(_env_path)


def _resolve_vault(vault_param: str = "") -> Path:
    if vault_param.lower() == "obsidian":
        return OBSIDIAN_VAULT_PATH
    return DEFAULT_VAULT_PATH


class WriteNoteRequest(BaseModel):
    category: str = "doctrine"
    title: str = ""
    content: dict = {}
    tags: list[str] = []
    subcategory: str | None = None


class CompressRequest(BaseModel):
    trace: str = ""
    context: str = ""
    category: str = "failures"


class ValidateRequest(BaseModel):
    content: str = ""


def register_vault_endpoints(app: FastAPI):
    """Register all vault endpoints on the given FastAPI app."""

    @app.get("/api/vault/notes")
    async def list_vault_notes(
        category: str = "", subcategory: str = "",
        vault: str = Query(default="", description="'obsidian' for real vault"),
    ):
        try:
            vpath = _resolve_vault(vault)
            writer = VaultWriter(vault_path=vpath)
            notes = writer.list_notes(category=category or None, subcategory=subcategory or None)
            return {"notes": notes, "count": len(notes), "vault": str(vpath)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/vault/notes/{category}/{title}")
    async def get_vault_note(
        category: str, title: str, subcategory: str = "",
        vault: str = Query(default="", description="'obsidian' for real vault"),
    ):
        try:
            vpath = _resolve_vault(vault)
            writer = VaultWriter(vault_path=vpath)
            note = writer.get_note(category, title, subcategory or None)
            if not note:
                raise HTTPException(status_code=404, detail=f"Note not found: {category}/{title}")
            return note
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/vault/write")
    async def write_vault_note(
        request: WriteNoteRequest,
        vault: str = Query(default="", description="'obsidian' for real vault"),
    ):
        try:
            vpath = _resolve_vault(vault)
            writer = VaultWriter(vault_path=vpath)
            result = writer.write_note(
                category=request.category, title=request.title,
                content=request.content, tags=request.tags,
                subcategory=request.subcategory,
            )
            return {"status": "ok", "note": result, "vault": str(vpath)}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/vault/compress")
    async def compress_vault_note(request: CompressRequest):
        try:
            result = compress_trace(request.trace, request.context, request.category)
            return {"status": "ok", "result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/vault/validate")
    async def validate_vault_note(request: ValidateRequest):
        try:
            validator = NoteValidator()
            result = validator.validate(request.content)
            return {"status": "ok", "result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/vault/graph")
    async def get_vault_graph():
        try:
            linker = Linker(vault_path=DEFAULT_VAULT_PATH)
            raw_graph = linker.build_graph()
            nodes = []
            edges = []
            seen_edges = set()
            for source, targets in raw_graph.items():
                nodes.append({"id": source, "label": source, "category": "note", "connections": len(targets)})
                for target in targets:
                    edge_key = tuple(sorted([source, target]))
                    if edge_key not in seen_edges:
                        edges.append({"source": source, "target": target})
                        seen_edges.add(edge_key)
            return {"nodes": nodes, "edges": edges}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/vault/search")
    async def search_vault_notes(q: str = "", category: str = "", limit: int = 50):
        try:
            writer = VaultWriter(vault_path=DEFAULT_VAULT_PATH)
            results = writer.search_notes(query=q, category=category, limit=limit)
            return {"results": results, "count": len(results)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/vault/categories")
    async def list_vault_categories():
        try:
            writer = VaultWriter(vault_path=DEFAULT_VAULT_PATH)
            return {"categories": writer.list_categories()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/vault/stats")
    async def vault_stats():
        """Get vault statistics."""
        try:
            writer = VaultWriter(vault_path=DEFAULT_VAULT_PATH)
            notes = writer.list_notes()
            categories = {}
            tags = {}
            for note in notes:
                cat = note.get("category", "uncategorized")
                categories[cat] = categories.get(cat, 0) + 1
                for tag in note.get("tags", []):
                    tags[tag] = tags.get(tag, 0) + 1
            return {
                "total_notes": len(notes),
                "categories": categories,
                "top_tags": dict(sorted(tags.items(), key=lambda x: x[1], reverse=True)[:20]),
            }
        except Exception as e:
            return {"total_notes": 0, "categories": {}, "top_tags": {}}


    @app.post("/api/vault/sync")
    async def vault_sync():
        """Sync O2C-VAULT files to Obsidian vault."""
        try:
            from core.obsidian.live_sync import sync_to_obsidian
            written, skipped = sync_to_obsidian()
            return {"status": "ok", "written": written, "skipped": skipped}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    @app.get("/api/vault/sync/status")
    async def vault_sync_status():
        """Get sync status."""
        try:
            from core.obsidian.live_sync import get_live_sync
            return get_live_sync().get_status()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    # --- Phase 01: Error Intelligence ---

    @app.get("/api/vault/errors")
    async def get_error_intelligence(category: str = "", limit: int = 50):
        try:
            from core.obsidian.error_intelligence import ErrorIntelligence
            ei = ErrorIntelligence(vault_path=DEFAULT_VAULT_PATH)
            patterns = ei.get_error_patterns()
            similar = ei.find_similar_errors(category, limit=limit) if category else []
            prevention = ei.get_prevention_rules()[:10]
            return {"patterns": patterns, "errors": similar, "prevention_rules": prevention}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/vault/errors/index")
    async def index_error(request: dict):
        try:
            from core.obsidian.error_intelligence import ErrorIntelligence
            ei = ErrorIntelligence(vault_path=DEFAULT_VAULT_PATH)
            result = ei.index_error(
                traceback=request.get("traceback", ""),
                category=request.get("category", ""),
                context=request.get("context", ""),
                fix_applied=request.get("fix_applied", ""),
                result=request.get("result", ""),
            )
            return {"status": "indexed", "error": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # --- Phase 01: Pattern Crystallization ---

    @app.get("/api/vault/patterns")
    async def get_patterns(min_occurrences: int = 2):
        try:
            from core.obsidian.pattern_crystallizer import PatternCrystallizer
            pc = PatternCrystallizer(vault_path=DEFAULT_VAULT_PATH)
            patterns = pc.extract_patterns(min_occurrences=min_occurrences)
            primitives = pc.get_cognitive_primitives()
            co_occurrence = pc.analyze_co_occurrence()
            return {"patterns": patterns, "cognitive_primitives": primitives, "co_occurrence": co_occurrence}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/vault/crystallize")
    async def crystallize_pattern(request: dict):
        try:
            from core.obsidian.pattern_crystallizer import PatternCrystallizer
            pc = PatternCrystallizer(vault_path=DEFAULT_VAULT_PATH)
            result = pc.crystallize_pattern(
                name=request.get("name", ""),
                conditions=request.get("conditions", []),
                result=request.get("result", ""),
                links=request.get("links", []),
            )
            return {"status": "crystallized", "pattern": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # --- Phase 01: Memory Distillation ---

    @app.post("/api/vault/distill")
    async def distill_session(request: dict):
        try:
            from core.obsidian.memory_distiller import MemoryDistiller
            md = MemoryDistiller(vault_path=DEFAULT_VAULT_PATH)
            result = md.distill_session(
                agent_name=request.get("agent_name", "unknown"),
                task=request.get("task", ""),
                journal_entries=request.get("journal_entries", []),
            )
            return {"status": "distilled", "result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/vault/distill/vault")
    async def distill_vault(request: dict):
        try:
            from core.obsidian.memory_distiller import MemoryDistiller
            md = MemoryDistiller(vault_path=DEFAULT_VAULT_PATH)
            days = request.get("days", 7)
            result = md.distill_from_vault(days=days)
            return {"status": "distilled", "result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # --- Phase 01: Context Injection ---

    @app.get("/api/vault/context")
    async def get_context(task: str = "", max_skills: int = 3, max_patterns: int = 5):
        try:
            from core.obsidian.context_injector import ContextInjector
            ci = ContextInjector(vault_path=DEFAULT_VAULT_PATH)
            context = ci.prepare_context(task=task, max_skills=max_skills, max_patterns=max_patterns)
            return {"context": context, "task": task}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/vault/summary")
    async def get_vault_summary():
        try:
            from core.obsidian.context_injector import ContextInjector
            ci = ContextInjector(vault_path=DEFAULT_VAULT_PATH)
            return {"summary": ci.get_vault_summary()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))



