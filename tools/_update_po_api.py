#!/usr/bin/env python3
"""Update po_api.py with Phase 2 endpoints."""
import pathlib

path = pathlib.Path('c:/Users/wifik/Desktop/projects/larger-lab/oce/backend/po_api.py')
content = path.read_text(encoding='utf-8')

# Fix imports
content = content.replace(
    'from typing import List, Dict, Any, AsyncGenerator',
    'from typing import List, Dict, Any, AsyncGenerator, Optional'
)
if 'import uuid' not in content:
    content = content.replace('import logging', 'import logging\nimport uuid')

# Insert new models before Chat Endpoint
old_marker = (
    '# ─── Chat Endpoint (Streaming) ───────────────────────────────────────────────\n'
    '\n'
    '@router.post("/chat")'
)

new_models = (
    'class POContextRequest(BaseModel):\n'
    '    session_id: str = ""\n'
    '    include_workspace: bool = True\n'
    '    include_vault: bool = True\n'
    '    include_memory: bool = True\n'
    '    max_tokens: int = 2000\n'
    '\n'
    '\n'
    'class POContextResponse(BaseModel):\n'
    '    session_id: str\n'
    '    workspace: Dict[str, Any] = {}\n'
    '    vault: Dict[str, Any] = {}\n'
    '    memory: Dict[str, Any] = {}\n'
    '    combined_context: str = ""\n'
    '    sources: List[str] = []\n'
    '\n'
    '\n'
    'class POCommandRequest(BaseModel):\n'
    '    command: str  # "interrupt", "cancel", "reset", "status"\n'
    '    session_id: str = ""\n'
    '    params: Dict[str, Any] = {}\n'
    '\n'
    '\n'
    'class POCommandResponse(BaseModel):\n'
    '    ok: bool\n'
    '    command: str\n'
    '    result: Any = None\n'
    '    error: Optional[str] = None\n'
    '\n'
    '\n'
    '# ─── Chat Endpoint (Streaming) ───────────────────────────────────────────────\n'
    '\n'
    '@router.post("/chat")'
)

if old_marker in content:
    content = content.replace(old_marker, new_models)
    print("OK: inserted new models")
else:
    print("WARN: old marker not found for models")

# Add new endpoints before Helpers
old_helpers = '# ─── Helpers ─────────────────────────────────────────────────────────────────\n\n\ndef _sse_chunk'

new_endpoints = (
    '# ─── Cognitive Stream (P2.3+P2.7) ─────────────────────────────────────────\n\n'
    '@router.get("/stream")\n'
    'async def po_stream(session_id: str = "", max_tokens: int = 2048):\n'
    '    """5-stage cognitive streaming endpoint."""\n'
    '    from oce.backend.po_stream import ThoughtStreamer\n'
    '    streamer = ThoughtStreamer()\n'
    '    req = {"messages": [{"role": "user", "content": "begin"}], "model": "po", "session_id": session_id, "max_tokens": max_tokens}\n'
    '    return StreamingResponse(streamer.stream(req, session_id=session_id), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})\n\n'
    '# ─── Context Endpoint (P2.8) ─────────────────────────────────────────────\n\n'
    '@router.post("/context")\n'
    'async def po_context(request: POContextRequest):\n'
    '    """Get current context from workspace, vault, and memory."""\n'
    '    try:\n'
    '        result = {"session_id": request.session_id}\n'
    '        if request.include_workspace:\n'
    '            try:\n'
    '                from oce.backend.po_workspace import WorkspaceScanner\n'
    '                result["workspace"] = WorkspaceScanner().scan().summary()\n'
    '            except Exception as e:\n'
    '                result["workspace"] = {"error": str(e)}\n'
    '        if request.include_vault:\n'
    '            try:\n'
    '                from oce.backend.po_vault import VaultRetriever\n'
    '                r = VaultRetriever().retrieve(request.session_id or "general")\n'
    '                result["vault"] = r.summary()\n'
    '                result["vault"]["context_string"] = r.as_context_string(max_tokens=request.max_tokens)\n'
    '            except Exception as e:\n'
    '                result["vault"] = {"error": str(e)}\n'
    '        if request.include_memory:\n'
    '            try:\n'
    '                from oce.backend.po_session import SessionManager\n'
    '                s = SessionManager().get(request.session_id)\n'
    '                result["memory"] = {"state": s.get_state().__dict__, "context": s.get_context()} if s else {"state": "no_session"}\n'
    '            except Exception as e:\n'
    '                result["memory"] = {"error": str(e)}\n'
    '        result["combined_context"] = "no context"\n'
    '        result["sources"] = [k for k in ["workspace","vault","memory"] if k in result and "error" not in result.get(k,{})]\n'
    '        return result\n'
    '    except Exception as e:\n'
    '        raise HTTPException(status_code=503, detail=str(e))\n\n'
    '# ─── Commands Endpoint (P2.9) ─────────────────────────────────────────────\n\n'
    '@router.post("/commands")\n'
    'async def po_commands(request: POCommandRequest):\n'
    '    """Execute PO commands: interrupt, cancel, reset, status."""\n'
    '    try:\n'
    '        if request.command == "interrupt":\n'
    '            from oce.backend.po_interrupt import InterruptHandler\n'
    '            InterruptHandler().cancel_session(request.session_id, reason="api")\n'
    '            return POCommandResponse(ok=True, command=request.command, result={"action": "interrupted"})\n'
    '        elif request.command == "cancel":\n'
    '            from oce.backend.po_interrupt import InterruptHandler\n'
    '            InterruptHandler().cancel_session(request.session_id, reason="api")\n'
    '            return POCommandResponse(ok=True, command=request.command, result={"action": "cancelled"})\n'
    '        elif request.command == "reset":\n'
    '            import shutil\n'
    '            from oce.backend.po_state import POStateStore\n'
    '            s = POStateStore()\n'
    '            if s._session_dir.exists(): shutil.rmtree(s._session_dir); s._session_dir.mkdir(exist_ok=True)\n'
    '            return POCommandResponse(ok=True, command=request.command, result={"action": "reset_complete"})\n'
    '        elif request.command == "status":\n'
    '            from oce.backend.po_state import POStateStore\n'
    '            from oce.backend.po_router import ModelRouter\n'
    '            return POCommandResponse(ok=True, command=request.command, result={"state": POStateStore().load_state().__dict__, "models": ModelRouter().health_check()})\n'
    '        raise HTTPException(status_code=400, detail=f"Unknown: {request.command}")\n'
    '    except Exception as e:\n'
    '        raise HTTPException(status_code=500, detail=str(e))\n\n'
    '# ─── Helpers ─────────────────────────────────────────────────────────────────\n\n'
    'def _sse_chunk'
)

if old_helpers in content:
    content = content.replace(old_helpers, new_endpoints)
    print("OK: inserted new endpoints")
else:
    print("WARN: helpers marker not found")

path.write_text(content, encoding='utf-8')
print("Done: " + str(path))