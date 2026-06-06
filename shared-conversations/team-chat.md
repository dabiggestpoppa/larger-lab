# Team Shared Conversation

> Purpose: Quick-communication hub for CC/AS/PM/PM2/RL coordination.
> **Current focus:** PO × Open-LLM-VTuber Integration (Phases 1-3)
> **Plan:** `docs/plans/PO-VTUBER-INTEGRATION.md`
> **Last Updated:** 2026-06-05 15:00 UTC

---

## Agent Roster & Status

| Tag | Agent | Role | Status |
|-----|-------|------|--------|
| 🔵 CC | Claude Code | Overseer / Architect / Core Builder | 🟢 Active |
| 🟡 AS | Assistant Manager | Quality / Tests / Docs / Session | 🟢 Active |
| 🔴 PM | Polymorph | Debugger / Tools / VTuber Recon | 🟢 Active |
| 🔴 PM2 | Polymorph 2 | Agent Coordination / Multi-Model | 🟢 Active |
| 🟢 RL | Research Lead | Idle/Autonomous Research | 🟢 Active |
| 🟠 OC2 | OWL (OpenClaw) | — | ⏸️ Off-table (operator handling) |
| 🦦 PO | Telegram Bot | — | ⏸️ Off-table (operator handling) |

---

## Current Phase: PO × Open-LLM-VTuber Integration

**Mission:** Replace Open-LLM-VTuber's generic LLM chat loop with PO cognitive field runtime. Preserve VTuber frontend/UI completely unchanged. The VTuber becomes an embodiment shell for PO/OCE.

### Phase Map

| Phase | Name | Status | Owner | Tests |
|-------|------|--------|-------|-------|
| 0 | VTuber Recon | ✅ Complete | PM | — |
| 1 | Provider Injection | ⏳ Ready (unblocked) | CC | 11 |
| 2 | Cognitive Field Routing | ⏳ Blocked on Phase 1 | CC + PM + PM2 + AS | 40 |
| 3 | Identity Unification | ⏳ Blocked on Phase 2 | CC + PM2 + PM + RL + AS | 15 |

**Total: 66 new tests across 23 components.**

### Build Order (strict)

```
[PM] VTuber Recon  ─────────────────────────────────┐
                                                     ↓
[CC] PO Provider Adapter (OpenAI-shape)  ───────────┤
                                                     ↓
[CC] OCE /api/po/chat + /api/po/status  ─────────────┤
                                                     ↓
[AS] Phase 1 smoke (real VTuber)  ──────────────────┤
                                                     ↓
                                                PHASE 1 GATE
                                                     ↓
[PM] Workspace scanner  ─┐
[PM] Vault retrieval  ───┤ parallel
[PM2] Agent coordination ─┤
[PM2] Model router  ─────┘
                                                     ↓
[CC] Streaming thought layer + /api/po/stream
                                                     ↓
[AS] Memory continuity + state persistence
                                                     ↓
[AS] Phase 2 integration suite
                                                     ↓
                                                PHASE 2 GATE
                                                     ↓
[CC] Identity session bridge  ──┐
[PM2] Fallback chain  ─────────┤ parallel
[PM] Interrupt handler  ───────┤
[RL] Idle runtime tick  ───────┘
                                                     ↓
[AS] Phase 3 e2e identity test
                                                     ↓
                                                PHASE 3 GATE
```

### Worktree / Commit Convention

- All agents commit to `master` directly (no feature branches for this effort)
- CC rebases/cleans at phase gates
- Commit prefix: `[PO-VTUBER P{N}] <agent-tag>: <description>`
- Push after every phase component completes

### Files / Paths

| Path | Purpose |
|------|---------|
| `docs/plans/PO-VTUBER-INTEGRATION.md` | Master plan (read this first) |
| `docs/plans/VTUBER-RECON.md` | PM's recon output (Phase 0) |
| `vtuber_integration/po_provider/` | PO provider adapter (Phase 1.1) |
| `vtuber_integration/tests/` | E2E tests (Phase 1.6, 2.12, 3.5) |
| `vtuber_integration/Open-LLM-VTuber/` | Cloned upstream (Phase 0) |
| `oce/backend/po_api.py` | OCE PO API surface |
| `oce/backend/po_workspace.py` | Workspace scanner |
| `oce/backend/po_vault.py` | Vault retrieval |
| `oce/backend/po_stream.py` | Streaming thought layer |
| `oce/backend/po_agents.py` | Agent coordination |
| `oce/backend/po_router.py` | Multi-model router |
| `oce/backend/po_session.py` | Memory continuity |
| `oce/backend/po_state.py` | PO state persistence |
| `oce/backend/po_events.py` | Event schema |
| `oce/backend/po_fallback.py` | Fallback chain |
| `oce/backend/po_interrupt.py` | Interrupt handler |
| `oce/backend/po_idle.py` | Autonomous idle tick |
| `core/identity/session_bridge.py` | OC2 ↔ PO identity bridge |

### Definition of Done — Phase 1

- [ ] `po_provider.py` implements OpenAI-shape `chat()`, `stream_chat()`, `get_models()`
- [ ] Provider registered in VTuber's provider list (yaml/json/registry)
- [ ] OCE `/api/po/chat` + `/api/po/status` endpoints live
- [ ] Real VTuber process: select "PO" from dropdown
- [ ] Mic → PO response → avatar speaks (end-to-end)
- [ ] Conversation history persists
- [ ] 11/11 tests pass
- [ ] All pushed to `origin/master`

### Definition of Done — Phase 2

- [ ] All 12 components built
- [ ] 5-stage streaming events emit (processing → scan → retrieve → route → respond)
- [ ] Workspace scan + vault retrieval produce real (non-theatrical) context
- [ ] OpenAI/Ollama/Claude providers still work (regression)
- [ ] Multi-model routing configured
- [ ] 40/40 tests pass
- [ ] All pushed

### Definition of Done — Phase 3

- [ ] Identity session bridge writes/reads `po_session` store
- [ ] Fallback chain (OpenRouter → Ollama → error) works
- [ ] Interrupt cancels in-flight generation
- [ ] Idle tick every 5min (vault sync, memory distill, telemetry)
- [ ] Cross-interface test: Telegram ↔ VTuber (or mock if OC2 still off-table)
- [ ] 15/15 tests pass
- [ ] All pushed

---

## PowerShell/Windows Execution Gotchas

### Encoding Issues
- **Problem:** Windows PowerShell defaults to `cp1252` encoding, breaking emoji and Unicode
- **Fix:** Always set `$env:PYTHONIOENCODING="utf-8"` before running Python scripts
- **Symptom:** 🔄✅⚠️ characters appear as `?` or cause silent failures

### Process Invocation
- **Problem:** `Start-Process "openclaw"` opens .ps1 in VS Code instead of executing
- **Fix:** Use `Start-Process -File "path\to\script.ps1"` or `Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "script.py"`
- **For background processes:** Always use `-WindowStyle Hidden` to avoid terminal timeout

### Terminal Management
- **Problem:** Stale terminals accumulate (76+ hours old), causing port conflicts
- **Fix:** Kill old terminals before starting: `Get-Process powershell | Where-Object {$_.StartTime -lt (Get-Date).AddHours(-1)} | Stop-Process`
- **Best practice:** Use `gateway_watchdog.py` for 24/7 monitoring instead of async terminals

### Working Directory
- **Problem:** Scripts with relative paths fail when terminal CWD differs
- **Fix:** Use full paths: `python "C:\Users\wifik\Desktop\projects\larger-lab\scripts\script.py"`
- **Or:** `Set-Location "C:\Users\wifik\Desktop\projects\larger-lab"` before running

### PID Locking (for Python scripts)
- Always implement PID file locks to prevent duplicate instances
- Check `_PID_FILE` before starting critical services (telegram_gateway, etc.)
- Use `taskkill /F /PID <pid>` to kill stale processes

---

## Entries

### 🔴 [PM] 2026-06-05 16:30 UTC — ✅ PHASE 0 RECON COMPLETE — PHASE 1 UNBLOCKED

**Recon doc:** `docs/plans/VTUBER-RECON.md`
**Commit:** `075c8912` — pushed to `origin/master`

**Key findings:**

1. **WebSocket-based, NOT REST** — Frontend talks to backend over a single persistent WebSocket at `/client-ws`. No HTTP chat endpoint. PO injection must happen at the LLM layer, not by adding endpoints to VTuber.

2. **Provider registration is factory-based** — `LLMFactory.create_llm()` in `stateless_llm_factory.py` switches on string keys (`"openai_compatible_llm"`, `"ollama_llm"`, `"claude_llm"`). We add `"po_llm"` as a new case.

3. **StatelessLLMInterface is the insertion point** — ABC with `chat_completion(messages, system, tools) → AsyncIterator[str]`. Our `po_llm.py` implements this, calls OCE `/api/po/chat` (SSE), parses OpenAI-shape chunks, yields text strings. The entire downstream pipeline (BasicMemoryAgent → sentence segmentation → TTS → WebSocket → frontend) remains untouched.

4. **Config is YAML** — `config_templates/conf.default.yaml` has `llm_configs:` section. We add `po_llm:` with `base_url`, `llm_api_key`, `model`, `temperature`. User sets `llm_provider: 'po_llm'`.

5. **Voice pipeline is downstream** — ASR → text → **LLM** → text → TTS → audio. PO only replaces the LLM layer. Voice/Live2D/TTS all work unchanged.

6. **Dual memory is fine** — BasicMemoryAgent manages VTuber-side chat memory. PO manages cognitive field memory independently. No conflict.

**Phase 1 insertion points (6 total):**
| # | What | Where |
|---|------|-------|
| 1 | PO LLM Provider | `agent/stateless_llm/po_llm.py` (new) |
| 2 | Factory registration | `agent/stateless_llm_factory.py` (add case) |
| 3 | Config schema | `config_manager/stateless_llm.py` (add model) |
| 4 | YAML config | `config_templates/conf.default.yaml` (add section) |
| 5 | OCE PO API | `oce/backend/po_api.py` (new) |
| 6 | OCE main.py wiring | `oce/backend/main.py` (import router) |

**Phase 0 blocker: RESOLVED.** CC, AS, PM2 — Phase 1 is go.

---

### [RL] 2026-06-05 17:00 UTC — ✅ P3.4 SCAFFOLD BUILT: POIdleRuntime

**Commit:** `7b94dec9e` — `[PO-VTUBER P3] RL: POIdleRuntime scaffold + 15 tests + OCE wiring + research doc`

**What landed:**
- `oce/backend/po_idle.py` — Full POIdleRuntime with adaptive cadence (60/300/900s), vault sync, memory distillation, telemetry emission, heartbeat
- `oce/backend/tests/test_po_idle.py` — **15/15 tests passing** (3 test classes: SingleTick, Cadence, StopCleanly)
- `oce/backend/main.py` — Wired: auto-start on startup, clean stop on shutdown, 2 new endpoints
- `progress/rl-vtuber-idle-research.md` — Research doc (thresholds, cadence, telemetry schema, distillation strategy)
- `progress/rl-progress.md` — RL progress file

**New OCE endpoints:**
- `GET /api/po/idle/status` — tick count, uptime, session state, last tick report
- `POST /api/po/idle/notify` — reset active timer (call when PO handles a request)

**Mock stores included** — POIdleRuntime works with MockPOStateStore, MockPOSessionStore, MockEventFabric, MockStructuralMemory, MockVaultIndexer. When AS delivers real P2.6/P2.10 stores, swap in via constructor — zero code changes to the runtime.

**Status:** P3.4 scaffold ✅ complete. Ready for real stores when Phase 2 lands.

---

### [RL] 2026-06-05 16:30 UTC — 🟢 RESEARCH COMPLETE: Idle Runtime Design

---

### [OC2] 2026-06-05 23:30 UTC — 🔴 CEREBUS CLEANUP COMPLETE

**Context:** Executor decommission + full round house cleanup of quant-lab/mt5.

**What happened:**
- `symmetry_trap_executor.py` (old standalone DMR executor) had hardcoded `SYMBOL="EURUSD.PRO"` + magic 20260531 — was causing rogue trades on Sign 7 pairs
- Removed from guardian `PROCESSES` dict — bridge is now SOLE executor
- Deleted debug artifacts: `engine_diff.txt`, `hook_test_msg.txt`, `hook_test_output.txt`
- Archived stale signal files + executor logs to `quant-lab/mt5/archive/`
- Cleaned `live_logs/` — only active bridge data remains

**Rogue trades identified:**
| Ticket | Pair | Dir | PnL | Magic | Source |
|--------|------|-----|-----|-------|--------|
| 109874743 | CHFJPY.PRO | BUY | +$0.51 | 20260601 | Old executor |
| 109890054 | EURUSD.PRO | BUY | -$1.08 | 0 | Unknown/ghost |
| 109898440 | EURUSD.PRO | SELL | +$1.02 | 20260601 | Old executor |

**Bridge status:** ✅ Healthy. Scan #107+, Low Cost Hex pairs (EURJPY/EURNZD/GBPNZD/EURAUD/GBPAUD/GBPCAD), 0 open positions.

---

### [OC2] 2026-06-05 23:45 UTC — 📋 DEMO SETUP PLAN (from MAD 16:04 EDT conversation)

**Goal:** Run Profit Quad on demo alongside live — separate processes, separate logs.

**Config-only changes (no new code):**
1. `mt5/demo_deploy_config.py` — copy of `deploy_config.py` with `.demo` symbol suffixes
2. `mt5/demo_account.json` — demo account login/server/password (FROM MAD)
3. `mt5/demo_bridge.py` — copy of `cerebus_live_bridge.py` with `DEMO_MODE = True`
4. Guardian: add `demo_bridge` as separate monitored process
5. Logs: `demo_logs/` folder already exists — completely separate from `live_logs/`

**Profit Quad demo pairs:** BTCUSD + ETHUSD + EURNZD + GBPNZD

**Key rule:** Demo and live = separate Python processes, no shared state, no mixed signals.

**Deliverable:** `progress/rl-vtuber-idle-research.md`

**Key findings:**

1. **Vault similarity threshold:** FTS5 rank ≥ 0.3, max 5 hits, freshness bias 1.5x for entries <24h old
2. **Adaptive cadence:** Active=60s, Warm=300s, Cold=900s (not fixed 5min) — matches existing `po_heartbeat.py` pattern but smarter
3. **Telemetry events:** 4 event types — `po_idle_tick` (heartbeat), `po_vault_sync`, `po_memory_distill`, `po_health_warning`
4. **Memory distillation:** Rule-based compression (WORK→LEARNED) when WORK >50 entries or entry age >1h. LLM-assisted distill = Phase 4+.
5. **P3.4 design:** Async `POIdleRuntime` class with `start()/stop()/tick()/notify_request()`. Evolves `po_heartbeat.py` into OCE-native async runtime.

**Dependencies:** Waiting on AS's POStateStore (P2.10) + POSessionStore (P2.6) before building P3.4.

**Risk:** Low. Existing `po_heartbeat.py` proves the 5-min loop pattern works. P3.4 is an evolution, not greenfield.

---

### [CC] 2026-06-05 15:00 UTC — 🎯 NEW MISSION: PO × Open-LLM-VTuber Integration

**Context:** Operator confirmed — PO and OC2 are off-table (operator working with them directly). Everything else is up and stable. Time for new territory.

**Task:** Inject PO as the cognitive field runtime behind Open-LLM-VTuber. The VTuber becomes an embodiment shell (avatar, voice, UI). PO/OCE becomes the mind (cognition, memory, orchestration).

**Approach:**
- **Zero frontend changes** — PO emulates OpenAI's streaming wire format
- **OCE acts as the PO gateway** — workspace scan, vault retrieval, agent coordination, model routing
- **Streaming cognitive layer** — 5-stage thought pipeline (processing → scan → retrieve → route → respond) the way OC2 already does
- **Multi-provider preserved** — OpenAI/Ollama/Claude continue to work, PO is one option among them
- **Phased delivery** — Phase 1 = provider injection (works), Phase 2 = cognitive routing (smart), Phase 3 = identity unification (continuous)

**Plan committed:** `docs/plans/PO-VTUBER-INTEGRATION.md`

**Phase 0 (BLOCKER):** PM to clone Open-LLM-VTuber and map the actual provider architecture, streaming protocol, and integration points. Output: `docs/plans/VTUBER-RECON.md`. **Nothing else starts until this is done.**

**Worktree:** All agents commit to `master` directly with `[PO-VTUBER P{N}]` prefix.

**Agent tasking** posted below.

---

### [CC] 2026-06-05 15:00 UTC — 📋 AGENT TASKING

#### 🟡 [AS] Assistant Manager
**You are:** Quality / Tests / Session / Docs
**Primary:**
- P1.6: Smoke test (`vtuber_integration/tests/test_smoke.py`) — 2 tests
- P2.6: Memory continuity session (`oce/backend/po_session.py`) — 3 tests
- P2.10: PO state persistence (`oce/backend/po_state.py`) — 3 tests
- P2.12: Phase 2 integration test suite — 5 tests
- P3.5: Phase 3 e2e identity test — 4 tests
**Standby first:** wait for PM recon + CC provider adapter to exist. Then run smoke.
**Post to:** team-chat when smoke passes.

#### 🔴 [PM] Polymorph
**You are:** VTuber Recon + Workspace/Interrupt
**Primary (Phase 0 — START NOW):**
- P0: Clone Open-LLM-VTuber, map provider architecture, write `docs/plans/VTUBER-RECON.md`
**Then (Phase 2 + 3):**
- P2.1: Workspace scanner (`oce/backend/po_workspace.py`) — 4 tests
- P3.3: Interrupt/cancel handler (`oce/backend/po_interrupt.py`) — 2 tests
**Post to:** team-chat when recon is done. **Nothing else starts until this completes.**

#### 🔴 [PM2] Polymorph 2
**You are:** Agent Coordination / Multi-Model
**Primary (Phase 2):**
- P2.4: Agent coordination bridge (`oce/backend/po_agents.py`) — 3 tests
- P2.5: Multi-model router (`oce/backend/po_router.py`) — 4 tests
**Then (Phase 3):**
- P3.2: Multi-model fallback chain (`oce/backend/po_fallback.py`) — 3 tests
**Standby first:** wait for CC's PO Provider Adapter skeleton to exist (Step 1 in build order). Then start P2.4 and P2.5 in parallel.

#### 🟢 [RL] Research Lead
**You are:** Idle/Autonomous Research
**Primary (Phase 3):**
- P3.4: Autonomous runtime tick (`oce/backend/po_idle.py`) — 3 tests
- Research: vault similarity threshold tuning, idle cadence (5min), telemetry format
**Standby first:** RL has the smallest footprint — research and prep the idle tick design while others build. Document your research in `progress/rl-vtuber-idle-research.md` and post a summary to team-chat.

#### 🔵 [CC] Claude Code (me)
**I am:** Architect + Core Builder
- Phase 0: coordinate with PM on recon
- P1.1: PO Provider Adapter (`vtuber_integration/po_provider/po_provider.py`) — 4 tests
- P1.2: Provider registry entry — 1 test
- P1.3-1.4: OCE `/api/po/chat` + `/api/po/status` — 4 tests
- P1.5: Wire into `oce/backend/main.py`
- P2.3: Streaming thought layer (SSE) — 4 tests
- P2.7-2.9: `/api/po/stream`, `/api/po/context`, `/api/po/commands` — 7 tests
- P2.11: Event schema (`oce/backend/po_events.py`) — 3 tests
- P3.1: Identity session bridge (`core/identity/session_bridge.py`) — 3 tests
- Phase gates: review, test, merge, post status

**Order of operations:** Step 0 (PM recon) → Step 1 (CC adapter) → Step 2 (CC API) → Step 3 (AS smoke) → PHASE 1 GATE → Step 4-7 (parallel) → PHASE 2 GATE → Step 8 (parallel) → PHASE 3 GATE.

---

## Standing Order

- ⏸️ **Phase 0 recon COMPLETE.** Phase 1 is unblocked — CC go.
- ✅ All commits: prefix with `[PO-VTUBER P{N}]`
- 📢 Post to team-chat when each component lands
- 🧪 AS owns the test suite — report PASS/FAIL counts after each phase
- 🛑 If blocked, post to team-chat and tag CC

---

## Open Questions (for Operator)

1. **VTuber repo location** — clone to `vtuber_integration/Open-LLM-VTuber/`?
2. **OCE internal auth** — static env-var token acceptable for PO↔OCE?
3. **Phase 3 defer** — if OC2/PO stay off-table, build Phase 3 mockable now or defer entirely?
4. **Live VTuber test** — operator willing to install VTuber for AS smoke, or do we mock audio?

---
