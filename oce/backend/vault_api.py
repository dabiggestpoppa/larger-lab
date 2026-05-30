"""
Vault API Endpoints — Phase 00
FastAPI endpoints for O2C Obsidian Vault.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.obsidian.vault_writer import VaultWriter, DEFAULT_VAULT_PATH
from core.obsidian.linker import Linker
from core.obsidian.compressor import compress_trace
from core.obsidian.note_standard import NoteValidator


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
    async def list_vault_notes(category: str = "", subcategory: str = ""):
        try:
            writer = VaultWriter(vault_path=DEFAULT_VAULT_PATH)
            notes = writer.list_notes(
                category=category or None,
                subcategory=subcategory or None,
            )
            return {"notes": notes, "count": len(notes)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/vault/notes/{category}/{title}")
    async def get_vault_note(category: str, title: str, subcategory: str = ""):
        try:
            writer = VaultWriter(vault_path=DEFAULT_VAULT_PATH)
            note = writer.get_note(category, title, subcategory or None)
            if not note:
                raise HTTPException(status_code=404, detail=f"Note not found: {category}/{title}")
            return note
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/vault/notes")
    async def write_vault_note(request: WriteNoteRequest):
        try:
            writer = VaultWriter(vault_path=DEFAULT_VAULT_PATH)
            result = writer.write_note(
                category=request.category, title=request.title,
                content=request.content, tags=request.tags,
                subcategory=request.subcategory,
            )
            return {"status": "ok", "note": result}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/api/vault/notes/{category}/{title}")
    async def update_vault_note(category: str, title: str, request: WriteNoteRequest, subcategory: str = ""):
        try:
            writer = VaultWriter(vault_path=DEFAULT_VAULT_PATH)
            result = writer.update_note(
                category=category, title=title,
                content=request.content, tags=request.tags,
                subcategory=subcategory or None,
            )
            return {"status": "ok", "note": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/vault/notes/{category}/{title}")
    async def delete_vault_note(category: str, title: str, subcategory: str = ""):
        try:
            writer = VaultWriter(vault_path=DEFAULT_VAULT_PATH)
            success = writer.delete_note(category, title, subcategory or None)
            if not success:
                raise HTTPException(status_code=404, detail=f"Note not found: {category}/{title}")
            return {"status": "deleted"}
        except HTTPException:
            raise
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

    @app.post("/api/vault/compress")
    async def compress_trace_to_note(request: CompressRequest):
        try:
            compressed = compress_trace(trace=request.trace, context=request.context)
            return {"compressed": compressed}
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

    @app.post("/api/vault/validate")
    async def validate_note(request: ValidateRequest):
        try:
            validator = NoteValidator()
            return validator.validate(request.content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
