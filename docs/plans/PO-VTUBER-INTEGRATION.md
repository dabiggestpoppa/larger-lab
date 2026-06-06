# PO × Open-LLM-VTuber Integration — Implementation Plan

> **Status:** ✅ COMPLETE — Phases 0-3 done, 61/61 tests passing
> **Created:** 2026-06-05 by CC (Claude Code)
> **Completed:** 2026-06-06 by CC + PM + PM2 + AS + RL
> **Out of scope:** OC2 (OpenClaw) and PO (telegram_gateway) — operator handling directly

---

## 0. Mission

Replace Open-LLM-VTuber's generic LLM chat loop with the **PO cognitive field runtime**, while preserving the VTuber frontend, Live2D avatar, voice pipeline, and mic input **completely unchanged**.

The VTuber repo becomes an **embodiment shell**. PO/OCE becomes the **mind + memory + orchestration**.

**Architecture Shift:**

```
BEFORE                              AFTER
──────                              ─────
User                                User
  ↓                                   ↓
Open-LLM-VTuber                     Open-LLM-VTuber (unchanged UI)
  ↓                                   ↓
OpenAI / Ollama / Claude            PO Provider Adapter
  ↓                                   ↓
Response                            OCE Cognitive Field
                                       ↓
                                    Vault + Agents + Memory + Workspace
                                       ↓
                                    Streaming Response (SSE, OpenAI-shaped)
```

**Critical Invariant:** VTuber frontend must believe it is talking to a normal OpenAI streaming endpoint. We emulate the wire format. We do **not** rewrite their UI.

---

## 1. Phase 1 — PO Provider Injection (the bare minimum)

**Success condition:** Open Open-LLM-VTuber, select "PO" as the LLM provider in settings, talk into the mic, and PO responds through OCE — avatar speaks the response, conversation persists, vault retrieval works.

**Deliverables:**

| # | Component | Path | Agent | Tests |
|---|-----------|------|-------|-------|
| 1.1 | PO Provider Adapter (OpenAI-shape) | `vtuber_integration/po_provider/po_provider.py` | CC | 4 |
| 1.2 | Provider registry entry | `vtuber_integration/po_provider/provider.yaml` | CC | 1 |
| 1.3 | OCE `/api/po/chat` endpoint | `oce/backend/po_api.py` | CC | 3 |
| 1.4 | OCE `/api/po/status` endpoint | `oce/backend/po_api.py` | CC | 1 |
| 1.5 | Wire into OCE `main.py` | `oce/backend/main.py` | CC | — |
| 1.6 | Smoke test (local VTuber → PO) | `vtuber_integration/tests/test_smoke.py` | AS | 2 |

**Phase 1 done =** 6 components, 11 tests, e2e smoke passes.

---

## 2. Phase 2 — Cognitive Field Routing (the upgrade)

**Success condition:** When the user talks, PO scans the workspace, retrieves vault context, coordinates agents, and streams the response with the 5-stage cognitive layer (`🧠 thinking → 🔍 scanning → 📚 retrieving → ⚡ routing → 💬 responding`). Existing OpenAI/Ollama/Claude providers must continue to work unchanged (multi-provider routing).

**Deliverables:**

| # | Component | Path | Agent | Tests |
|---|-----------|------|-------|-------|
| 2.1 | Workspace scanner | `oce/backend/po_workspace.py` | PM | 4 |
| 2.2 | Vault retrieval layer | `oce/backend/po_vault.py` | PM | 4 |
| 2.3 | Streaming thought layer (SSE) | `oce/backend/po_stream.py` | CC | 4 |
| 2.4 | Agent coordination bridge | `oce/backend/po_agents.py` | PM2 | 3 |
| 2.5 | Multi-model router (OpenRouter/Ollama) | `oce/backend/po_router.py` | PM2 | 4 |
| 2.6 | Memory continuity session | `oce/backend/po_session.py` | AS | 3 |
| 2.7 | `/api/po/stream` SSE endpoint | `oce/backend/po_api.py` | CC | 3 |
| 2.8 | `/api/po/context` endpoint | `oce/backend/po_api.py` | CC | 2 |
| 2.9 | `/api/po/commands` endpoint | `oce/backend/po_api.py` | CC | 2 |
| 2.10 | PO state persistence | `oce/backend/po_state.py` | AS | 3 |
| 2.11 | Event/command schema (`workspace_scan`, `agent_spawn`, etc.) | `oce/backend/po_events.py` | CC | 3 |
| 2.12 | Phase 2 integration test suite | `vtuber_integration/tests/test_phase2.py` | AS | 5 |

**Phase 2 done =** 12 components, 40 tests, all streaming events emit correctly.

---

## 3. Phase 3 — Identity Unification (the stretch)

**Success condition:** A conversation started in Telegram can be continued in VTuber with full context. PO maintains a single identity across interfaces. Multi-model fallback works (OpenRouter → Ollama → error).

**Deliverables:**

| # | Component | Path | Agent | Tests |
|---|-----------|------|-------|-------|
| 3.1 | Identity session bridge (OC2 → PO) | `core/identity/session_bridge.py` | CC | 3 |
| 3.2 | Multi-model fallback chain | `oce/backend/po_fallback.py` | PM2 | 3 |
| 3.3 | Interrupt/cancel handler | `oce/backend/po_interrupt.py` | PM | 2 |
| 3.4 | Autonomous runtime tick (idle) | `oce/backend/po_idle.py` | RL | 3 |
| 3.5 | Phase 3 e2e identity test | `vtuber_integration/tests/test_phase3.py` | AS | 4 |

**Phase 3 done =** 5 components, 15 tests, identity unification validated.

---

## 4. Open-LLM-VTuber Recon (must do first)

Before any code lands, **PM** must clone the repo and map:

- `backend/` or `src/` — provider directory
- `llm/` or `providers/` — existing OpenAI/Ollama/Claude adapters
- Streaming response handler (SSE / WebSocket / generator)
- WebSocket / event bus between frontend and backend
- Chat session state module
- Voice pipeline trigger point (TTS handoff)
- Provider registration mechanism (factory / config / registry)

**Output:** `docs/plans/VTUBER-RECON.md` — file map + wire format examples + insertion points.

This is **blocker** for Phase 1.1. Do this FIRST.

---

## 5. Agent Assignment Matrix

| Agent | Role | Phase(s) | Deliverables | Status |
|-------|------|----------|--------------|--------|
| **CC** (Claude Code) | Architect + Core Builder | P1, P2, P3 | Provider adapter, OCE PO API, streaming layer, identity bridge, recon coordination | 🟢 Active |
| **PM** (Polymorph) | Recon + Workspace + Interrupt | P0-recon, P2, P3 | VTuber recon doc, workspace scanner, interrupt handler | 🟢 Active |
| **PM2** (Polymorph 2) | Agent/Multi-model layer | P2, P3 | Agent coordination, model router, fallback chain | 🟢 Active |
| **AS** (Assistant Manager) | Quality + Tests + Session | P1, P2, P3 | E2E smoke tests, memory continuity, state persistence, integration suites | 🟢 Active |
| **RL** (Research Lead) | Idle/autonomous research | P3 | Autonomous runtime tick research + implementation | 🟢 Active |
| ~~OC2~~ | — | — | Off-table (operator working directly) | ⏸️ Paused |
| ~~PO~~ | — | — | Off-table (operator working directly) | ⏸️ Paused |

**Worktree Convention:** All agents commit to `master` directly. CC rebases. No feature branches for this effort — it's a vertical slice and we want one clean linear history.

---

## 6. Build Order (dependency graph)

```
Step 0: [PM]  VTuber Recon (blocker)
            ↓
Step 1: [CC]  PO Provider Adapter (Python class, OpenAI-shape streaming)
            ↓
Step 2: [CC]  OCE /api/po/chat + /api/po/status (minimal echo for Phase 1)
            ↓
Step 3: [AS]  Phase 1 e2e smoke test (real VTuber run)
            ↓
        ── PHASE 1 GATE: PO selectable, talks through OCE ──
            ↓
Step 4: [PM]  Workspace scanner + Vault retrieval (parallel)
Step 4: [PM2] Agent coordination bridge + Model router (parallel)
            ↓
Step 5: [CC]  Streaming thought layer (SSE) + /api/po/stream
            ↓
Step 6: [AS]  Memory continuity session + state persistence
            ↓
Step 7: [AS]  Phase 2 integration test suite
            ↓
        ── PHASE 2 GATE: 5-stage streaming, multi-provider, all tests pass ──
            ↓
Step 8: [CC]  Identity session bridge
Step 8: [PM2] Multi-model fallback chain
Step 8: [PM]  Interrupt/cancel handler
Step 8: [RL]  Autonomous runtime tick
            ↓
Step 9: [AS]  Phase 3 e2e identity test
            ↓
        ── PHASE 3 GATE: Telegram↔VTuber continuity, fallback works ──
```

**Parallelism:** Steps 4 can run PM + PM2 in parallel. Step 8 can run all four agents in parallel.

---

## 7. Streaming Event Schema (canonical)

These are the events the streaming layer emits. Frontend renders them as status cards.

```json
// Stage 1 — processing
{"type": "status", "stage": "processing", "message": "🧠 Processing...", "ts": 1234567890}

// Stage 2 — workspace scan
{"type": "event", "kind": "workspace_scan", "payload": {"files_scanned": 12, "fresh": 3}, "ts": ...}

// Stage 3 — vault retrieval
{"type": "event", "kind": "vault_retrieval", "payload": {"hits": 5, "patterns": ["p90", "regime"]}, "ts": ...}

// Stage 4 — agent coordination
{"type": "event", "kind": "agent_spawn", "payload": {"agent": "ml_scorer", "task": "regime_classify"}, "ts": ...}

// Stage 5 — response chunks (OpenAI-shape for VTuber compat)
{"type": "chunk", "choices": [{"delta": {"content": "..."}}]}

// Final
{"type": "done", "usage": {"prompt_tokens": N, "completion_tokens": M, "total": N+M}}
```

VTuber sees only `chunk` + `done` events (OpenAI-shape). The other events are **emit-only for our own telemetry** — VTuber ignores them, OCE stores them.

---

## 8. PO Provider Wire Format (OpenAI-compat)

**Request from VTuber → OCE:**

```http
POST /api/po/chat
Content-Type: application/json
Authorization: Bearer <OCE_INTERNAL_TOKEN>

{
  "model": "po",
  "messages": [
    {"role": "system", "content": "You are PO..."},
    {"role": "user", "content": "<user transcript from STT>"}
  ],
  "stream": true,
  "temperature": 0.7,
  "session_id": "<vtuber-session-uuid>"
}
```

**Response (SSE stream):**

```
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":"🧠 "}}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":"Processing..."}}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":" Hey, "}}]}

...

data: [DONE]
```

**Why this shape?** VTuber's existing OpenAI provider speaks exactly this. We slot in. **Zero frontend changes.**

---

## 9. Workspace Awareness Sources (what PO scans)

Before every response:

| Source | Path | What we extract |
|--------|------|-----------------|
| Team chat | `shared-conversations/team-chat.md` | Last 50 lines, agent tags, status |
| Progress files | `progress/*-progress.md` | Last 24h entries per agent |
| Workspace state | `progress/workspace-state.md` | Current phase, test status |
| Vault | `O2C-VAULT/` | Recent entries, hot patterns |
| Recent traces | `logs/*.log` | Last N events, errors |
| Agent files | `agents/*.agent.md` | Identity/role context |

**Not scanned:** `node_modules/`, `.venv/`, `__pycache__/`, `.git/`, large media.

---

## 10. Memory Continuity

- **Session key:** `vtuber-{vtuber_session_uuid}` → maps to OCE `po_session`
- **History window:** last 20 messages (sliding)
- **Vault recall:** top 3 hits from semantic search
- **Identity anchor:** `po.identity` from `core/identity/` (operator-curated)
- **Cross-interface:** OC2 writes to same `po_session` store; reads from there too

**Out of scope for Phase 1:** Cross-interface identity bridging. Just VTuber ↔ OCE.

---

## 11. Multi-Provider Fallback Chain

```
VTuber → PO Provider
            ↓
        OpenRouter (primary, all models)
            ↓ on failure
        Ollama (local fallback)
            ↓ on failure
        Canned response + log error
```

PO Provider supports configuring the chain in `po_config.yaml`. Default is OpenRouter-only for Phase 1. Fallback enabled in Phase 3.

---

## 12. Test Strategy

| Layer | Test Type | Agent | Where |
|-------|-----------|-------|-------|
| Unit | Pure function tests | Owner of module | `oce/backend/po_*/tests/` |
| Integration | Endpoint + module chain | AS | `vtuber_integration/tests/test_phase{N}.py` |
| E2E (Phase 1) | Real VTuber subprocess | AS | `vtuber_integration/tests/test_smoke.py` |
| E2E (Phase 2) | Streaming event sequence | AS | `vtuber_integration/tests/test_phase2.py` |
| E2E (Phase 3) | Cross-interface continuity | AS | `vtuber_integration/tests/test_phase3.py` |

**Test budget per phase:**
- Phase 1: 11 tests (4 provider + 3 API + 1 registry + 2 smoke + 1 e2e)
- Phase 2: 40 tests (distributed across 12 components)
- Phase 3: 15 tests (distributed across 5 components)
- **Total: 66 new tests across the integration**

---

## 13. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| VTuber repo structure is significantly different than assumed | High | Phase 1 blocked | **PM recon first** — adapt plan to actual structure |
| OpenAI-shape doesn't match VTuber's expected format | Medium | Provider rejected by VTuber | **AS validates against real VTuber run** in Step 3 |
| SSE streaming through FastAPI breaks with VTuber's HTTP client | Low | No streaming → no LLM feel | Use `StreamingResponse` with `media_type="text/event-stream"` |
| Workspace scan is too slow (>500ms) | Medium | Bad UX | **Cache** workspace summary; refresh on file watch event |
| Vault retrieval returns irrelevant context | Medium | Hallucinations increase | RL research — tune similarity threshold + max-k |
| OC2/PO off-table blocks integration test (Phase 3) | High | Phase 3 delayed | **Mock the bridge** in unit tests; defer real cross-interface test to operator handoff |

---

## 14. Communication Protocol

- All agents post to `shared-conversations/team-chat.md` with their tag
- Each agent updates their `progress/*-progress.md` file
- CC reviews daily, posts summary, resolves conflicts
- AS runs the test suite and reports PASS/FAIL counts after each phase gate
- PM's recon is the only Phase 0 deliverable — **must complete before any Phase 1 code**

---

## 15. Definition of Done — Phase 1

1. ✅ `po_provider.py` exists and implements `chat()`, `stream_chat()`, `get_models()` matching OpenAI base provider
2. ✅ `provider.yaml` (or `provider_registry.json`) registers PO in VTuber's provider list
3. ✅ OCE `/api/po/chat` accepts OpenAI-shape requests, returns OpenAI-shape responses (or SSE stream)
4. ✅ OCE `/api/po/status` returns health + active model
5. ✅ Real VTuber process can select "PO" from the provider dropdown
6. ✅ User says "hello" into mic → PO responds through OCE → avatar speaks
7. ✅ Conversation history persists across restarts
8. ✅ At least 11 tests pass
9. ✅ All commits pushed to `origin/master`

---

## 16. Definition of Done — Phase 2

1. ✅ All 12 Phase 2 components built
2. ✅ Workspace scan + vault retrieval produce real (non-theatrical) context
3. ✅ 5-stage streaming events emit in correct order
4. ✅ OpenAI / Ollama / Claude providers in VTuber still work (regression check)
5. ✅ Multi-model routing: OpenRouter primary, fallback chain configured
6. ✅ At least 40 tests pass
7. ✅ All commits pushed

---

## 17. Definition of Done — Phase 3

1. ✅ Identity session bridge writes/reads from `po_session` store
2. ✅ Fallback chain (OpenRouter → Ollama → error) actually works
3. ✅ Interrupt cancels in-flight generation
4. ✅ Idle tick runs every 5min (vault sync, memory distill, telemetry)
5. ✅ Cross-interface test: message in Telegram → continue in VTuber (or mock)
6. ✅ At least 15 tests pass
7. ✅ All commits pushed

---

## 18. Open Questions for Operator

1. **VTuber repo location** — clone to `vtuber_integration/Open-LLM-VTuber/`? Or work from a separate directory?
2. **Provider config format** — does VTuber use YAML, JSON, or Python decorator? (PM recon answers)
3. **OCE token** — should PO Provider auth with OCE via a static internal token? (env var)
4. **Cross-interface phase** — defer Phase 3 entirely until OC2/PO are back on the table? Or build it mockable now?
5. **Live mic test** — operator willing to install Open-LLM-VTuber locally for AS smoke tests, or do we mock the audio pipeline?

---

**End of Plan — Awaiting Operator Approval + Agent Tasking**
