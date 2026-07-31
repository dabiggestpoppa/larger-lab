# 🔴 Polymorph 2 (PM2) — PO × VTuber Integration Tasks

> **Agent:** Polymorph 2 (PM2)
> **Plan:** `docs/plans/PO-VTUBER-INTEGRATION.md`
> **Start:** 2026-06-05 15:00 UTC
> **Status:** 🟡 STANDBY → wait for PM recon + CC provider adapter skeleton, then start P2.4 + P2.5 in parallel

---

## Mission

Build the **agent coordination bridge** and **multi-model router** that sit inside the OCE PO gateway. The PO Provider in VTuber talks to OCE; OCE talks to your modules; your modules fan out to internal agents and external model providers (OpenRouter, Ollama, Claude, etc.).

## Tasks

### Phase 2 — Cognitive Field Routing (your primary)

| # | Component | File | Tests | Status |
|---|-----------|------|-------|--------|
| P2.4 | Agent coordination bridge | `oce/backend/po_agents.py` | 3 | ⏳ Queued |
| P2.5 | Multi-model router | `oce/backend/po_router.py` | 4 | ⏳ Queued |

### Phase 3 — Identity Unification (your secondary)

| # | Component | File | Tests | Status |
|---|-----------|------|-------|--------|
| P3.2 | Multi-model fallback chain | `oce/backend/po_fallback.py` | 3 | ⏳ Queued |

**Total: 10 tests across 3 components.**

## Component Specs

### P2.4 — Agent Coordination Bridge (`po_agents.py`)

Wraps the OCE agent execution API. PO Provider calls into this when it needs specialized work (regime classification, parameter lookup, etc.).

**Interface:**
```python
class AgentCoordinator:
    def __init__(self, oce_base_url: str, internal_token: str):
        ...

    async def coordinate(
        self,
        task: str,              # "regime_classify", "vault_search", "ml_score"
        payload: dict,          # task-specific args
        session_id: str,
    ) -> dict:
        """Spawn/spawn-and-wait an agent, return result."""
        ...

    async def list_capabilities(self) -> list[dict]:
        """List available agent capabilities."""
        ...
```

**Tests (3):**
1. Coordinate a registered task → returns result
2. Unknown task → graceful error response (no crash)
3. Capability listing returns expected agents

### P2.5 — Multi-Model Router (`po_router.py`)

Decides which model to use for a given request. Reads from `po_config.yaml`. Supports OpenRouter, Ollama, Claude.

**Interface:**
```python
class ModelRouter:
    def __init__(self, config_path: str = "po_config.yaml"):
        ...

    def select_model(
        self,
        request: PORequest,
        session: POSession,
    ) -> ModelSpec:
        """Pick the right model based on task type, cost, capability."""
        ...

    def get_available_models(self) -> list[ModelSpec]:
        ...
```

**Tests (4):**
1. Default selection (OpenRouter, primary model)
2. Cost-aware selection (prefer cheap model for simple task)
3. Capability-aware (force opus for complex reasoning)
4. List available models

### P3.2 — Fallback Chain (`po_fallback.py`)

Wraps the model router with try/fallback logic. If primary fails, try next in chain. If all fail, return graceful error.

**Interface:**
```python
class FallbackChain:
    def __init__(self, primary: ModelRouter, fallbacks: list[ModelSpec]):
        ...

    async def generate(
        self,
        request: PORequest,
    ) -> ModelResponse:
        """Try primary, then fallbacks, then raise."""
        ...
```

**Tests (3):**
1. Primary succeeds → returns primary result
2. Primary fails (mock) → tries fallback → returns fallback result
3. All fail → raises with helpful error

## Build Order

```
Wait for PM recon ✅ AND CC PO Provider Adapter skeleton ✅
              ↓
        P2.4 (AgentCoordinator)  ─┐
        P2.5 (ModelRouter)  ─────┤ parallel
                                  ↓
        P3.2 (FallbackChain)  ── after P2.5 done
```

## Commit Prefix

- `[PO-VTUBER P2] PM2: <description>` for P2.x work
- `[PO-VTUBER P3] PM2: <description>` for P3.2

## Posting to Team Chat

- Post when starting each component ("P2.4 starting")
- Post when each lands with test counts
- Post at end of day with status
