# Team Shared Conversation

> **Purpose:** Quick-communication hub for CC/PM/PM2/AS/RL coordination.
> **Current focus:** O2C × MAD LABS Sovereign Research Mesh — Phases L1→L4
> **Plan:** `docs/plans/O2C-RESEARCH-MESH.md`
> **Tasks:** `progress/O2C-RESEARCH-MESH-TASKS.md`
> **Last Updated:** 2026-06-06 18:00 UTC (CC2 — L1 UNBLOCKED)

---

## Agent Roster & Status

| Tag | Agent | Role | Status |
|-----|-------|------|--------|
| 🔵 CC | Claude Code (CC2) | Overseer / Architect / Core Build | 🟢 Active |
| 🟡 AS | Assistant Manager | Quality / Safety / Tests | 🟢 Active |
| 🔴 PM | Polymorph | Sources / Cache / Concepts | 🟢 Active |
| 🔴 PM2 | Polymorph 2 | Graph / Multi-Agent / Frontend | 🟢 Active |
| 🟢 RL | Research Lead | Scheduling / Contradictions | 🟢 Active |
| 🟠 OC2 | OWL (OpenClaw) | — | ⏸️ Off-table (operator handling) |
| 🦦 PO | Telegram Bot | — | ⏸️ Off-table (operator handling) |

---

## Current Mission: O2C × MAD LABS Sovereign Research Mesh

**Context:** MAD attached the MAD LABS sovereign research field plan. The OCE/SRRA-OPH substrate + O2C-VAULT (200+ .md files) + PO/VTuber integration (61/61 tests) are all stable. **The missing piece is the autonomous research mesh** — continuous ingestion of scientific literature, distillation into operational doctrine, recursive research loops on detected knowledge gaps.

**Goal:** Build a 4-layer research mesh (Ingestion → Distillation → Agents → API/UI) on top of the existing OCE/SRRA-OPH substrate. The vault becomes a living research civilization instead of a static knowledge base.

### Phase Map

| Layer | Name | Components | Tests | Status |
|-------|------|------------|-------|--------|
| L1 | Knowledge Acquisition | 8 | ~46 | ⏳ Build (kickoff) |
| L2 | Distillation + Graph | 8 | ~45 | ⏳ Queued (after L1 gate) |
| L3 | Autonomous Research | 8 | ~39 | ⏳ Queued (after L2 gate) |
| L4 | OCE API + Frontend | 8 | ~29 | ⏳ Queued (after L3 gate) |
| **TOTAL** | | **32** | **~159** | |

**Build order (strict):** L1 sources in parallel → L1 GATE → L2 distillation in parallel → L2 GATE → L3 agents in parallel → L3 GATE → L4 API + UI.

**Constraint:** No new L2 work starts until L1 GATE. Build on real OpenAlex/arXiv data, not mocks.

### File Paths

| Path | Purpose |
|------|---------|
| `docs/plans/O2C-RESEARCH-MESH.md` | Master plan |
| `progress/O2C-RESEARCH-MESH-TASKS.md` | Per-agent tasking |
| `core/research/ingestion/` | L1 source clients (L1.1-L1.8) |
| `core/research/distillation/` | L2 distillers, graph, vault writer (L2.1-L2.8) |
| `core/research/agents/` | L3 gap detector, research agent, queue (L3.1-L3.8) |
| `oce/backend/research_api.py` | L4 OCE API (L4.1-L4.8) |
| `oce/frontend/app/research/` | L4 OCE pages (PM2) |
| `data/research/*.db` | SQLite stores (papers, citations, agents) |
| `O2C-VAULT/research/` | Auto-generated paper notes |
| `O2C-VAULT/doctrine/` | Auto-extracted doctrine notes |

### Commit Convention

- All agents commit to `master` directly
- CC rebases at phase gates
- Commit prefix: `[RESEARCH-MESH L{N}] <agent-tag>: <description>`
- Push after every component

---

## Standing Rules (apply to ALL work)

1. **Read BUILD-NOTES.md** before any work — surgical changes only
2. **Test before you update progress** — every progress file update requires a verified test run
3. **Don't edit another agent's files** without posting to chat first
4. **Post to chat BEFORE starting** a new major task
5. **Use real data when available** — simulate only when no real data exists
6. **All agent actions logged to execution journal** — full audit trail

### Hard Rules (AS enforces)

1. **No autonomous recursive skill mutation** — human review required
2. **No unbounded vault writes** — daily cap 200, taxonomy enforced
3. **No LLM cost runaway** — $2/day hard cap, fail-closed
4. **No model weight modification** — orchestration layer only
5. **No production deployment without operator approval** — sandbox + staging only
6. **Every paper note follows CAUSE/METHOD/RESULT/LIMITATIONS/APPLICATION/LINKS** — no exceptions

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

## Archived History

> Full historical entries (PO × VTuber Phases 0-3, Phase 11 testing, CEREBUS ML, etc.) are in the git log + progress files. Keep them there. Don't re-paste.
>
> Last chat archive: 2026-06-06 (CC2) — 351 lines → ~140 lines. Old entries preserved in git history of `shared-conversations/team-chat.md`.

---

## Entries

### 🔵 [CC2] 2026-06-06 — 🟡 NEW MISSION: O2C × MAD LABS Sovereign Research Mesh

**Context:**
- OC2/PO off-table (CC2 working with operator to get telegram back up)
- Operator attached MAD LABS sovereign research field plan
- All other systems stable (PO×VTuber 61/61, O2C Phase 00+01 113/113, OCE V3 1403/1403, SRRA-OPH 57/57)
- O2C-VAULT already exists (200+ .md files in doctrine/architecture/skills/ontology)

**Plan + tasks committed:**
- `docs/plans/O2C-RESEARCH-MESH.md` — 4-layer plan (L1 ingestion, L2 distillation, L3 agents, L4 API+UI)
- `progress/O2C-RESEARCH-MESH-TASKS.md` — per-agent tasking with 32 components, ~159 tests
- 32 components, 4 layers, parallel work where possible
- Build on real data (OpenAlex/arXiv) from day 1, no mocks

**Why this matters:** the missing piece between "smart OCE runtime" and "sovereign research civilization" is the autonomous research loop. Once built, the vault compounds intelligence continuously.

**Tight scope rules:**
- L1.1-L1.8 (ingestion) can all run in parallel after CC ships the package skeleton
- L2 starts only after L1 GATE (500 papers ingested, dedup verified)
- No agent builds anything speculative — every component in the plan lands or gets cut
- AS owns safety reviews and test regression on every PR
- PM2 owns the OCE frontend pages (L4 only, not L1-L3)

**Status:** 🟡 Awaiting operator approval to kickoff L1.

---

### [Standing] ⏸️ PO × Open-LLM-VTuber Integration — ✅ COMPLETE 2026-06-06

All 4 phases done, 61/61 tests passing, desktop pet live. See `docs/plans/PO-VTUBER-INTEGRATION.md` for archive.

---

### 🔵 [CC2] 2026-06-06 — 📋 AGENT TASKING: O2C × MAD LABS Research Mesh

**Full task breakdown lives in `progress/O2C-RESEARCH-MESH-TASKS.md`. Posting highlights here for visibility.**

#### 🔴 [PM] Polymorph — Sources + Cache + Concepts
**Start NOW (no blocker):**
- L1.1 OpenAlex client — `core/research/ingestion/openalex_client.py` (8 tests)
  - **Critical:** pass `mailto=ops@larger-lab.local` in every request for higher rate limit
  - Endpoint: `https://api.openalex.org/works`
  - Filters: 15 INITIAL_DOMAINS from plan §4.2
- L1.3 Semantic Scholar client — `core/research/ingestion/s2_client.py` (6 tests)
- L1.7 Cache + dedup — `core/research/ingestion/cache.py` (6 tests)
  - **Critical:** dedup is write-time gate, see TEAM-NOTES §0
- L2.2 Concept extractor — `core/research/distillation/concepts.py` (6 tests) — after L1 GATE
- L3.2 Research task generator — `core/research/agents/task_gen.py` (5 tests) — after L2 GATE

**Stop and post to chat if:** any L1 client can't get 100+ real papers from the live API.

#### 🔴 [PM2] Polymorph 2 — Graph + Multi-Agent + Frontend
**Start NOW (no blocker):**
- L1.2 arXiv client — `core/research/ingestion/arxiv_client.py` (6 tests)
  - **Critical:** arXiv returns Atom XML, not JSON — use `xml.etree.ElementTree`
- L1.8 Rate limiter — `core/research/ingestion/rate_limit.py` (5 tests)
- L2.3 Citation graph builder — after L1 GATE
- L3.4 Finding evaluator + L3.5 Router — after L2 GATE
- L4 OCE frontend pages — after L3 GATE (you own these)

**Note:** PM2 also owns all L4 OCE frontend pages (Research Hub, Knowledge Graph, Doctrine Library, Research Agents) — but only after L4 API lands. Don't start these until L3 GATE.

#### 🟡 [AS] Assistant Manager — Quality + Safety + Tests
**Start NOW (write safety regression suite first):**
- L2.6 LLM distiller (cost-bounded) — after L1 GATE
- L2.7 Doctrine extractor — after L2.1 lands
- L3.1 Gap detector — after L2 GATE
- L3.6 Agent lifecycle — after L2 GATE
- L4.8 Telemetry + audit — after L4 API
- **Continuous:** review every PR for hard rule violations (see TEAM-NOTES §0 + plan §12)
- **Continuous:** run full test suite after every PR, report PASS/FAIL counts to chat

**Top priority right now:** Define and write the safety regression tests (cost cap, write cap, daily limits, audit logging) BEFORE any LLM-touching or vault-writing code lands. These tests fail-closed.

#### 🟢 [RL] Research Lead — Scheduling + Contradictions
**Start NOW (no blocker):**
- L1.6 Ingestion scheduler — `core/research/ingestion/scheduler.py` (6 tests)
  - APScheduler with daily cron, manual trigger endpoint
- L2.8 Contradiction detector — after L2 lands
- Research doc: `progress/research-mesh-design.md` — domain rationale, thresholds, contradiction patterns

**Don't build:** the research agent (that's CC's L3.3). RL focuses on the autonomous loop's safety valves, not its core.

#### 🛑 [BLOCKEWait-CC] CC2 (me) — Overseer / Skeleton / Gate
**Hour 0 (next 30 min):**
- Ship `core/research/` package skeleton (`__init__.py` in each subdir)
- Ship `data/research/schema.sql` (papers, citations, agents tables)
- Ship `O2C-VAULT/doctrine/meta/research_mesh_principles.md`
- Post this tasking to chat (this entry)
- Update workspace-state.md with new mission

**Then:** stand by for L1 PRs. L1 GATE review when all 8 L1 components land.

**Don't touch:** L1 source clients (PM/PM2 own these), L2 extractors (CC will build distiller + vault_writer later, after L1 GATE), L3 agents (CC will build research_agent + queue after L2 GATE), L4 API (CC will build this after L3 GATE).

#### ⏸️ OC2 / PO — Off-table
Operator handling directly. No work expected from this mission.

---

### 📋 Definition of Done — L1 GATE (everyone reads)

L1 GATE is met when ALL of these are true:
- [ ] All 3 source clients (OpenAlex, arXiv, S2) return real papers from live APIs
- [ ] Cache + dedup prevents duplicate papers on repeat runs (verified with a test)
- [ ] Scheduler runs daily cron + manual trigger
- [ ] Rate limiter survives OpenAlex 429 responses (test by exceeding limit deliberately)
- [ ] All ~46 L1 tests pass
- [ ] All 1582+ existing tests still pass
- [ ] AS safety regression tests written and passing

CC2 will post L1 GATE PASS in chat. **No L2 work starts until that post.**

---
### 🔴 [PM2] 2026-06-06 — ✅ L1.2 + L1.8 SHIPPED

**Commit:** `05aad19a` — `[RESEARCH-MESH L1] PM2: Add arXiv client (L1.2) + rate limiter (L1.8)`

**What landed:**
- `core/research/ingestion/arxiv_client.py` — async arXiv client, Atom XML parser, returns `List[Paper]`
  - `search()` — full-text search with pagination
  - `search_by_category()` — category-based search
  - `fetch_by_id()` — single paper lookup
  - Handles Atom XML namespace correctly (`http://www.w3.org/2005/Atom`)
  - Primary category promoted to level=0, regular categories level=1
- `core/research/ingestion/rate_limit.py` — token bucket rate limiter + exponential backoff
  - Per-source rate limiting (arXiv default: 3 req/s)
  - `execute_with_retry()` — wraps any coroutine with rate limit + retry
  - Honors `Retry-After` header
- Tests: 15/15 passing (6 arXiv + 5 rate limiter + 3 integration + 1 retry-after)

**L1 status:** PM2's L1 components done. Waiting on PM (L1.1, L1.3, L1.7) and RL (L1.6) for L1 GATE.

**Next:** L2.3 Citation graph builder — queued until L1 GATE PASS.

---
### � [CC2] 2026-06-06 18:00 UTC — ✅ L0 SKELETON SHIPPED — L1 UNBLOCKED

**Commit:** `28e4d8ec7` — pushed to `origin/master`

**What landed:**
- `core/research/` — full package skeleton with `__init__.py` in all 3 subdirs + tests
- `core/research/ingestion/models.py` — canonical `Paper`, `Author`, `Concept` schema (dataclasses + `to_sqlite_dict()`)
- `core/research/ingestion/sources.py` — `SourceRegistry` with 15 domains, OpenAlex/arXiv/S2 configs, domain→query mappings
- `data/research/schema.sql` — `papers.db`, `citations.db`, `agents.db`, `daily_caps` tables
- `O2C-VAULT/doctrine/meta/research_mesh_principles.md` — governing philosophy (10 principles, cost controls, file layout)

**L1 is now unblocked. PM, PM2, RL — start your source clients.**

Key interfaces you need:
- All clients return `List[Paper]` from `core.research.ingestion.models`
- `Paper.id` = OpenAlex ID (`W...`) or DOI; `Paper.doi` = DOI if available
- `SourceRegistry` from `core.research.ingestion.sources` — `get_registry()` singleton
- SQLite schema at `data/research/schema.sql` — run against `data/research/papers.db`
- OpenAlex: pass `mailto=ops@larger-lab.local` for polite pool (10 req/s)
- arXiv: returns Atom XML (not JSON) — use `xml.etree.ElementTree`
- S2: 1 req/s free tier

**AS:** your first deliverable is the safety regression test suite. Write it against the `daily_caps` table + `Paper.status` transitions. Gate: all 6 hard rules from `research_mesh_principles.md` §5 must have failing tests that pass when the safety layer is correct.

---

### �🔗 Resource Links

- Master plan: `docs/plans/O2C-RESEARCH-MESH.md`
- Per-agent tasks: `progress/O2C-RESEARCH-MESH-TASKS.md`
- Pitfalls: `progress/TEAM-NOTES.md` §0
- Build principles: `progress/BUILD-NOTES.md`
- 12-rule contract: `docs/meta/CLAUDE.md`

---

### 🟡 [AS] 2026-06-06 — ✅ SAFETY REGRESSION SUITE LANDED

**Commit:** `fc031c78` — `[RESEARCH-MESH L0] AS: Safety regression test suite — 41/41 passing`

**What landed:**
- `core/research/tests/test_safety_regression.py` — 41 tests covering all 6 hard rules

**Test coverage:**
| Rule | Tests | Status |
|------|-------|--------|
| 1. $2/day LLM cost cap | 6 | ✅ PASS |
| 2. 200 vault writes/day cap | 5 | ✅ PASS |
| 3. Max 3 concurrent agents | 5 | ✅ PASS |
| 4. Agent action logging | 7 | ✅ PASS |
| 5. No recursive skill mutation | 4 | ✅ PASS |
| 6. No unauthorized deployment | 4 | ✅ PASS |
| daily_caps integrity | 4 | ✅ PASS |
| Paper status transitions | 6 | ✅ PASS |

**Regression check:** All 92 existing OCE tests still green. ✅

**Safety layer contract for PM/PM2/RL:**
- All LLM-touching code must check `daily_caps.llm_cost_usd < 2.0` BEFORE calling any model
- All vault writes must check `daily_caps.vault_writes < 200` BEFORE writing
- All agent spawns must check `research_tasks WHERE status='running' < 3`
- All actions must write to `agent_log` table
- Use atomic SQL increments (see test patterns) — no read-then-write races
- `RESEARCH_MESH_ENV` defaults to `sandbox` — production requires explicit opt-in

**Next up (waiting on L1 GATE):**
- L2.6 LLM distiller — cost-bounded wrapper
- L2.7 Doctrine extractor — pattern → doctrine note
- L3.1 Gap detector — knowledge gap heuristics
- L3.6 Agent lifecycle — state machine + bounds

---

### 🔵 [CC2] 2026-06-06 — 📋 STATUS CHECK

**What's landed so far:**
- ✅ Plan + tasking + team chat + team notes + workspace state (`3c22647d0`)
- ✅ L0 skeleton: `core/research/` package, models, sources, schema.sql, vault principles (`28e4d8ec7`)
- ✅ AS safety regression suite: 41/41 passing, all 6 hard rules covered (`fc031c781`)

**What's next — PM/PM2/RL, this is your runway:**
- `core/research/ingestion/openalex_client.py` — PM, 8 tests
- `core/research/ingestion/arxiv_client.py` — PM2, 6 tests
- `core/research/ingestion/s2_client.py` — PM, 6 tests
- `core/research/ingestion/cache.py` — PM, 6 tests
- `core/research/ingestion/rate_limit.py` — PM2, 5 tests
- `core/research/ingestion/scheduler.py` — RL, 6 tests

All clients return `List[Paper]` from `core.research.ingestion.models`.
SQLite schema at `data/research/schema.sql`. AS safety tests are the gate.

**CC2 standing by for L1 PRs.**

---

## Open Questions for Operator

1. **LLM for distillation** — use the same model tier as PO/OCE (current default), or specify a particular OpenRouter model?
2. **Domain list** — confirm the 15 initial domains in `O2C-RESEARCH-MESH.md` §4.2?
3. **Daily LLM budget** — confirm $2/day hard cap?
4. **Vault sync** — bidirectional (OCE writes → vault) or one-way (vault → OCE)?
5. **Operator trigger** — should ingestion run automatically on a daily cron, or only on manual OCE trigger?
