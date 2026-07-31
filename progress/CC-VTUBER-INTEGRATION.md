# 🔵 Claude Code (CC) — PO × VTuber Integration Tasks

> **Agent:** Claude Code (CC) — Overseer / Architect / Core Builder
> **Plan:** `docs/plans/PO-VTUBER-INTEGRATION.md`
> **Start:** 2026-06-05 15:00 UTC
> **Status:** 🟢 ACTIVE

---

## Mission

You are the **architect and core builder**. You design the provider adapter, build the OCE PO API surface, implement the streaming thought layer, define the event schema, and bridge identity. You also coordinate the other agents and gate each phase.

## Tasks

### Phase 1 — Provider Injection (your primary)

| # | Component | File | Tests | Status |
|---|-----------|------|-------|--------|
| P1.1 | PO Provider Adapter (OpenAI-shape) | `vtuber_integration/po_provider/po_provider.py` | 4 | ⏳ Blocked on PM recon |
| P1.2 | Provider registry entry | `vtuber_integration/po_provider/provider.yaml` | 1 | ⏳ Blocked on P1.1 |
| P1.3 | OCE `/api/po/chat` endpoint | `oce/backend/po_api.py` | 3 | ⏳ Blocked on P1.1 |
| P1.4 | OCE `/api/po/status` endpoint | `oce/backend/po_api.py` | 1 | ⏳ Blocked on P1.1 |
| P1.5 | Wire into `oce/backend/main.py` | `oce/backend/main.py` | — | ⏳ Blocked on P1.3 |

### Phase 2 — Cognitive Field Routing

| # | Component | File | Tests | Status |
|---|-----------|------|-------|--------|
| P2.3 | Streaming thought layer (SSE) | `oce/backend/po_stream.py` | 4 | ⏳ Blocked on Phase 1 gate |
| P2.7 | `/api/po/stream` SSE endpoint | `oce/backend/po_api.py` | 3 | ⏳ Blocked on P2.3 |
| P2.8 | `/api/po/context` endpoint | `oce/backend/po_api.py` | 2 | ⏳ Blocked on P2.3 |
| P2.9 | `/api/po/commands` endpoint | `oce/backend/po_api.py` | 2 | ⏳ Blocked on P2.3 |
| P2.11 | Event/command schema | `oce/backend/po_events.py` | 3 | ⏳ Blocked on P2.3 |

### Phase 3 — Identity Unification

| # | Component | File | Tests | Status |
|---|-----------|------|-------|--------|
| P3.1 | Identity session bridge | `core/identity/session_bridge.py` | 3 | ⏳ Blocked on Phase 2 gate |

**Total: 26 tests across 11 components.**

## Component Specs

### P1.1 — PO Provider Adapter (`po_provider.py`)

The brain of Phase 1. Implements the OpenAI provider interface (or whatever VTuber uses — PM recon confirms). Methods:

```python
class POProvider(BaseProvider):
    def __init__(self, config: POConfig):
        self.oce_url = config.oce_url
        self.token = config.oce_token
        ...

    async def chat(self, messages: list[Message], **kwargs) -> Response:
        """Non-streaming chat. POST to OCE /api/po/chat."""
        ...

    async def stream_chat(self, messages: list[Message], **kwargs) -> AsyncIterator[Chunk]:
        """Streaming chat. SSE from OCE /api/po/stream."""
        ...

    def get_models(self) -> list[ModelInfo]:
        """List available models."""
        ...
```

The adapter must produce **OpenAI-shape wire format** (or whatever the recon confirms). VTuber's frontend should treat it as a normal OpenAI provider.

### P1.3-1.4 — OCE PO API (`po_api.py`)

The receiving end. FastAPI router.

```python
router = APIRouter(prefix="/api/po", tags=["po"])

@router.post("/chat")
async def po_chat(request: POChatRequest) -> POChatResponse:
    """Non-streaming. Echos the request through OCE's model router."""
    ...

@router.get("/status")
async def po_status() -> POStatusResponse:
    """Health, active model, uptime."""
    ...
```

### P2.3 — Streaming Thought Layer (`po_stream.py`)

Generates the 5-stage cognitive stream. Emits events in this order:

```python
async def stream_thought(
    request: POChatRequest,
    workspace_scanner: WorkspaceScanner,
    vault_retriever: VaultRetriever,
    agent_coordinator: AgentCoordinator,
    model_router: ModelRouter,
) -> AsyncIterator[POEvent]:
    yield POEvent(type="status", stage="processing", message="🧠 Processing...")
    
    scan = await workspace_scanner.scan()
    yield POEvent(type="event", kind="workspace_scan", payload=scan.summary())
    
    retrieval = await vault_retriever.retrieve(scan.context)
    yield POEvent(type="event", kind="vault_retrieval", payload=retrieval.summary())
    
    coordination = await agent_coordinator.coordinate(...)
    yield POEvent(type="event", kind="agent_spawn", payload=coordination.summary())
    
    async for chunk in model_router.stream(request.with_context(scan, retrieval, coordination)):
        yield POEvent(type="chunk", choices=[chunk])
    
    yield POEvent(type="done", usage=...)
```

**Tests (4):**
1. Events emit in correct order
2. Each event has correct shape
3. Errors mid-stream → emit `error` event, not crash
4. Cancellation mid-stream → emit `cancelled` event, clean exit

### P2.7-2.9 — More PO API Endpoints

- `/api/po/stream` — SSE wrapper around `stream_thought()`
- `/api/po/context` — returns current workspace + vault summary (no model call)
- `/api/po/commands` — accept structured commands, dispatch to agent coordinator

### P2.11 — Event Schema (`po_events.py`)

Pydantic models for all event types. Used by both OCE and PO Provider.

```python
class POEvent(BaseModel):
    type: Literal["status", "event", "chunk", "done", "error", "cancelled"]
    ts: float
    ...

class StatusEvent(POEvent):
    type: Literal["status"]
    stage: str
    message: str

class WorkspaceScanEvent(POEvent):
    type: Literal["event"]
    kind: Literal["workspace_scan"]
    payload: dict

class ChunkEvent(POEvent):
    type: Literal["chunk"]
    choices: list[dict]  # OpenAI-shape

class DoneEvent(POEvent):
    type: Literal["done"]
    usage: dict
```

### P3.1 — Identity Session Bridge (`session_bridge.py`)

Bridges session state between interfaces (OC2, VTuber, future surfaces). Single source of truth: `POSessionStore`.

```python
class IdentitySessionBridge:
    def __init__(self, session_store: POSessionStore):
        ...

    def get_continuity(self, surface: str, surface_session_id: str) -> POSession:
        """Resolve a surface session to the unified identity session."""
        ...

    def link(self, surface: str, surface_session_id: str, identity_session_id: str) -> None:
        """Link a surface session to a unified identity session."""
        ...
```

## Build Order (CC tasks only)

```
NOW: Wait for PM recon ✅
              ↓
Step 1: P1.1 + P1.2 (PO Provider Adapter + Registry)
              ↓
Step 2: P1.3 + P1.4 + P1.5 (OCE PO API surface)
              ↓
Step 3: Hand off to AS for smoke test (P1.6)
              ↓
        ── PHASE 1 GATE (CC reviews) ──
              ↓
Step 4-5: P2.3, P2.7, P2.8, P2.9, P2.11 (streaming layer)
              ↓
Step 6-7: Hand off to AS for integration test (P2.12)
              ↓
        ── PHASE 2 GATE (CC reviews) ──
              ↓
Step 8: P3.1 (identity bridge)
              ↓
        ── PHASE 3 GATE (CC reviews) ──
```

## Commit Prefix

- `[PO-VTUBER P1] CC: <description>` for P1.x
- `[PO-VTUBER P2] CC: <description>` for P2.x
- `[PO-VTUBER P3] CC: <description>` for P3.1

## Coordination Duties

- Review PRs / diffs from other agents
- Post phase gate results to team-chat
- Update `progress/workspace-state.md` after each phase
- Update `AGENTS.md` roster if needed
- Run `python tools/progress-sync.py --force` after each phase gate

## Architecture Decisions to Make

1. **PO Provider base class** — do we implement VTuber's actual base class, or wrap it? (depends on PM recon)
2. **OCE auth** — static env-var token, or no auth (localhost-only)?
3. **SSE vs WebSocket** — VTuber uses WebSocket; we use SSE internally; bridge as needed
4. **Event storage** — should PO Events be persisted to OCE telemetry? (yes, for replay)
5. **Identity store** — extend existing `core/identity/` or new file in `oce/state/`?
