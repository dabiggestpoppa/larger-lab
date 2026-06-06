# O2C × MAD LABS — Research Mesh Team Tasks

> **Status:** 🟡 Ready for kickoff — awaiting operator approval
> **Plan:** `docs/plans/O2C-RESEARCH-MESH.md`
> **Lead:** CC (Overseer / Architect / Core Build)
> **Last updated:** 2026-06-06
> **Roster:** CC, PM, PM2, AS, RL (OC2/PO off-table)

---

## Mission

Extend the existing OCE/SRRA-OPH cognitive field with an **autonomous research mesh** — a system that continuously ingests scientific literature (OpenAlex, arXiv, Semantic Scholar), distills papers into operational doctrine, builds a knowledge graph, and spawns research agents on detected knowledge gaps.

**Full plan:** `docs/plans/O2C-RESEARCH-MESH.md`
**Build on top of:** O2C Phase 00+01 vault/compressor/linker/error_intelligence/pattern_crystallizer (already shipped) + SRRA-OPH runtime substrate.

---

## Layer Map

| Layer | Name | Components | Tests | Critical Path |
|---|---|---|---|---|
| **L1** | Knowledge Acquisition | 8 | ~46 | ⭐ OpenAlex client (PM) |
| **L2** | Distillation + Graph | 8 | ~45 | ⭐ Distiller + vault_writer (CC) |
| **L3** | Autonomous Research | 8 | ~39 | ⭐ Research agent + queue (CC) |
| **L4** | OCE API + UI | 8 | ~29 | ⭐ research_api.py (CC) |
| **TOTAL** | | **32 components** | **~159 tests** | |

---

## 🟡 Build Order (strict dependency)

```
L1 SOURCES (parallel)
   PM: 1.1 OpenAlex client ────────────┐
   PM2: 1.2 arXiv client  ─────────────┤
   PM:  1.3 S2 client     ─────────────┤
   CC:  1.4 Source registry ───────────┤
   CC:  1.5 Paper schema  ─────────────┤
   PM:  1.7 Cache + dedup ─────────────┤
   PM2: 1.8 Rate limit    ─────────────┤
   RL:  1.6 Scheduler     ─────────────┘
                  ↓
            L1 GATE: 500 papers ingested, dedup verified
                  ↓
L2 DISTILLATION (parallel)
   CC:  2.1 Distiller   ──────────────┐
   PM:  2.2 Concepts    ──────────────┤
   PM2: 2.3 Citations   ──────────────┤
   CC:  2.4 Vault writer ─────────────┤
   CC:  2.5 Graph store  ─────────────┤
   AS:  2.6 LLM distill  ─────────────┤
   AS:  2.7 Doctrine    ──────────────┤
   RL:  2.8 Contradictions ───────────┘
                  ↓
            L2 GATE: 50 papers distilled, ≥1 doctrine auto-extracted
                  ↓
L3 AGENTS (parallel)
   AS:  3.1 Gap detector ─────────────┐
   PM:  3.2 Task gen    ──────────────┤
   CC:  3.3 Research agent ───────────┤
   PM2: 3.4 Evaluator   ──────────────┤
   PM2: 3.5 Router      ──────────────┤
   AS:  3.6 Lifecycle   ──────────────┤
   CC:  3.7 Queue        ─────────────┤
   CC:  3.8 SRRA adapter ─────────────┘
                  ↓
            L3 GATE: First autonomous research cycle completes
                  ↓
L4 API + UI
   CC:  4.1-4.6 research_api.py (8 endpoints) ──┐
   PM2: 4.7 Vault sync engine                  ─┤
   AS:  4.8 Telemetry                          ─┘
   PM2: 4 OCE frontend pages (Research Hub, Graph, Doctrine, Agents)
                  ↓
            L4 GATE: Operator browses mesh in OCE
```

**Parallelism rules:**
- L1: All 3 source clients run in parallel (PM/PM2/PM)
- L2: CC builds distiller + writer + graph; AS builds LLM + doctrine; PM/PM2 build extractors
- L3: All 8 components can run in parallel after L2 gate (different files, no shared dependencies)
- L4: CC builds API; PM2 builds frontend pages (parallel)

---

## 🔵 CC (Claude Code) — Overseer / Architect / Core Build

### Primary
- Plan, phase gates, daily status
- L1.4 Source registry, L1.5 Paper schema
- L2.1 Distiller, L2.4 Vault writer, L2.5 Graph store
- L3.3 Research agent, L3.7 Task queue, L3.8 SRRA adapter
- L4.1-4.6 OCE research API (8 endpoints)

### Tasks
- [ ] **RM-CC-1** Write `core/research/__init__.py` + package skeleton
- [ ] **RM-CC-2** Write SQLite schema `data/research/schema.sql`
- [ ] **RM-CC-3** Write L1.5 normalized paper schema (`core/research/ingestion/models.py`) — 5 tests
- [ ] **RM-CC-4** Write L1.4 source registry (`core/research/ingestion/sources.py`) — 4 tests
- [ ] **RM-CC-5** Write L2.1 rule-based distiller (`core/research/distillation/distiller.py`) — 8 tests
- [ ] **RM-CC-6** Write L2.4 vault writer for paper notes (`core/research/distillation/vault_writer.py`) — 6 tests
- [ ] **RM-CC-7** Write L2.5 graph store wrapper (`core/research/distillation/graph_store.py`) — 5 tests
- [ ] **RM-CC-8** Write L3.3 research agent (`core/research/agents/research_agent.py`) — 6 tests
- [ ] **RM-CC-9** Write L3.7 task queue (`core/research/agents/queue.py`) — 4 tests
- [ ] **RM-CC-10** Write L3.8 SRRA adapter (`core/research/agents/srra_adapter.py`) — 4 tests
- [ ] **RM-CC-11** Write L4.1-4.6 OCE research API (`oce/backend/research_api.py`) — 22 tests (4+4+4+4+3+3)
- [ ] **RM-CC-12** Wire research_api router into `oce/backend/main.py`
- [ ] **RM-CC-13** Write vault principles doc `O2C-VAULT/doctrine/meta/research_mesh_principles.md`

---

## 🔴 PM (Polymorph) — Sources + Workspace Scanners

### Primary
- L1.1 OpenAlex client, L1.3 S2 client, L1.7 Cache + dedup
- L2.2 Concept extractor, L3.2 Research task generator

### Tasks
- [ ] **RM-PM-1** Write L1.1 OpenAlex client (`core/research/ingestion/openalex_client.py`) — 8 tests
  - Endpoint: `https://api.openalex.org/works`
  - Filters: domain (from INITIAL_DOMAINS), year range, open access
  - Pagination: cursor-based, batch of 200
- [ ] **RM-PM-2** Write L1.3 Semantic Scholar client (`core/research/ingestion/s2_client.py`) — 6 tests
  - Endpoint: `https://api.semanticscholar.org/graph/v1/paper/`
- [ ] **RM-PM-3** Write L1.7 cache + dedup layer (`core/research/ingestion/cache.py`) — 6 tests
  - Key: DOI / OpenAlex ID
  - Storage: SQLite `data/research/papers.db`
  - Dedup: by DOI, fuzzy by title+author+year
- [ ] **RM-PM-4** Write L2.2 concept extractor (`core/research/distillation/concepts.py`) — 6 tests
  - Extracts: top 5 concepts per paper from OpenAlex concepts field
  - Falls back to keyword extraction from abstract
- [ ] **RM-PM-5** Write L3.2 research task generator (`core/research/agents/task_gen.py`) — 5 tests
  - Input: knowledge gap (concept missing, edge density low)
  - Output: structured research task (query, domains, depth limit)

---

## 🔴 PM2 (Polymorph 2) — Graph + Multi-Agent Layer

### Primary
- L1.2 arXiv client, L1.8 Rate limit
- L2.3 Citation graph builder
- L3.4 Finding evaluator, L3.5 Research router
- L4.7 Vault sync engine, OCE frontend pages

### Tasks
- [x] **RM-PM2-1** Write L1.2 arXiv client (`core/research/ingestion/arxiv_client.py`) — 6 tests ✅
  - Endpoint: `http://export.arxiv.org/api/query`
  - Atom XML response parsing
- [x] **RM-PM2-2** Write L1.8 rate limiter + retry (`core/research/ingestion/rate_limit.py`) — 5 tests ✅
  - Token bucket per source
  - Exponential backoff on 429/5xx
- [ ] **RM-PM2-3** Write L2.3 citation graph builder (`core/research/distillation/citation_graph.py`) — 6 tests
  - Builds edges from `referenced_works` (OpenAlex)
  - Stores in `data/research/citations.db`
- [ ] **RM-PM2-4** Write L3.4 finding evaluator (`core/research/agents/evaluator.py`) — 5 tests
  - Confidence score (0-1) from: source quality, citation count, recency, LLM self-rating
  - Threshold: 0.6 (configurable)
- [ ] **RM-PM2-5** Write L3.5 research router (`core/research/agents/router.py`) — 5 tests
  - Routes research tasks to: local LLM (Ollama) / OpenRouter / skip if budget exhausted
- [ ] **RM-PM2-6** Write L4.7 vault sync engine (`oce/backend/research_api.py` section) — 4 tests
  - Reads O2C-VAULT/research/, syncs to graph
- [ ] **RM-PM2-7** Build OCE frontend pages (after L4 API):
  - `oce/frontend/app/research/page.tsx` — Research Hub
  - `oce/frontend/app/research/graph/page.tsx` — Knowledge Graph
  - `oce/frontend/app/research/doctrine/page.tsx` — Doctrine Library
  - `oce/frontend/app/research/agents/page.tsx` — Research Agents

---

## 🟡 AS (Assistant Manager) — Quality + Safety + Tests

### Primary
- L2.6 LLM-assisted distillation
- L2.7 Doctrine extractor
- L3.1 Gap detector, L3.6 Agent lifecycle
- L4.8 Telemetry + audit export
- All cross-cutting safety reviews

### Tasks
- [ ] **RM-AS-1** Write L2.6 LLM-assisted distiller (`core/research/distillation/llm_distill.py`) — 4 tests
  - Opt-in per paper (rate-limited)
  - Token budget: 500 in, 300 out
  - Cost cap: $2/day hard, fail-closed
- [ ] **RM-AS-2** Write L2.7 doctrine extractor (`core/research/distillation/doctrine.py`) — 5 tests
  - Scans `O2C-VAULT/research/papers/` for recurring CAUSE/METHOD
  - When ≥3 papers share a pattern → auto-create `O2C-VAULT/doctrine/{domain}/{topic}.md`
- [ ] **RM-AS-3** Write L3.1 knowledge gap detector (`core/research/agents/gap_detector.py`) — 5 tests
  - Heuristics: low citation density in domain, missing concept links, recent papers with no notes
- [ ] **RM-AS-4** Write L3.6 agent lifecycle (`core/research/agents/lifecycle.py`) — 5 tests
  - States: queued → running → completed | failed | abandoned
  - Bounds: max 3 concurrent, max 1hr per task, max 2 retries
- [ ] **RM-AS-5** Write L4.8 telemetry + audit (`oce/backend/research_api.py` section) — 3 tests
  - Logs every agent action to execution journal
  - Daily report: papers ingested, distilled, agents run, $ spent
- [ ] **RM-AS-6** Review all PRs for safety boundaries (continuous)
- [ ] **RM-AS-7** Maintain test suite integrity — every commit must keep all 1582+ existing tests green

---

## 🟢 RL (Research Lead) — Scheduling + Research Hygiene

### Primary
- L1.6 Ingestion scheduler
- L2.8 Contradiction detector
- L3 evaluator (regression tests)

### Tasks
- [ ] **RM-RL-1** Write L1.6 ingestion scheduler (`core/research/ingestion/scheduler.py`) — 6 tests
  - APScheduler with daily cron
  - Configurable: ingest 500 papers/day default
  - Manual trigger endpoint exposed via OCE
- [ ] **RM-RL-2** Write L2.8 contradiction detector (`core/research/distillation/contradictions.py`) — 5 tests
  - Detects: papers with opposing RESULTS for same METHOD
  - Writes: `O2C-VAULT/research/contradictions/{topic}.md`
- [ ] **RM-RL-3** Write research hygiene regression tests — verify all safety rules (daily caps, token limits, write caps, audit logging)
- [ ] **RM-RL-4** Research doc: `progress/research-mesh-design.md` — domain selection rationale, threshold tuning, contradiction patterns

---

## 🛑 Hard Rules (AS enforces)

1. **No autonomous recursive skill mutation** — human review required for any skill/prompt change
2. **No unbounded vault writes** — daily cap 200 writes, taxonomy enforced
3. **No LLM cost runaway** — $2/day hard cap, fail-closed
4. **No model weight modification** — orchestration layer only
5. **No production deployment without operator approval** — sandbox + staging only
6. **All agent actions logged to execution journal** — full audit trail
7. **Every paper note follows CAUSE/METHOD/RESULT/LIMITATIONS/APPLICATION/LINKS** — no exceptions
8. **Use real data when available** — OpenAlex/arXiv are free, always use live API
9. **Test before you update progress** — every progress file update requires verified test run
10. **Simplicity first** — minimum code that solves the problem

---

## 🧪 Test Strategy

| Layer | Agent | Test Type | Count |
|---|---|---|---|
| L1 Ingestion | PM + PM2 | Unit (mock HTTP) + integration (live API) | ~46 |
| L2 Distillation | CC + AS | Unit (fixtures) + integration (real papers) | ~45 |
| L3 Agents | PM2 + AS | Unit (mock LLM) + e2e (single cycle) | ~39 |
| L4 API + UI | CC + PM2 | Integration (live OCE) | ~29 |
| **TOTAL** | | | **~159 new tests** |

**All 1582+ existing tests must continue to pass.**

---

## 📁 File Layout

```
larger-lab/
├── core/
│   └── research/                    # NEW package
│       ├── __init__.py
│       ├── ingestion/
│       │   ├── openalex_client.py      (L1.1, PM)
│       │   ├── arxiv_client.py         (L1.2, PM2)
│       │   ├── s2_client.py            (L1.3, PM)
│       │   ├── sources.py              (L1.4, CC)
│       │   ├── models.py               (L1.5, CC)
│       │   ├── scheduler.py            (L1.6, RL)
│       │   ├── cache.py                (L1.7, PM)
│       │   ├── rate_limit.py           (L1.8, PM2)
│       │   └── tests/
│       ├── distillation/
│       │   ├── distiller.py            (L2.1, CC)
│       │   ├── concepts.py             (L2.2, PM)
│       │   ├── citation_graph.py       (L2.3, PM2)
│       │   ├── vault_writer.py         (L2.4, CC)
│       │   ├── graph_store.py          (L2.5, CC)
│       │   ├── llm_distill.py          (L2.6, AS)
│       │   ├── doctrine.py             (L2.7, AS)
│       │   ├── contradictions.py       (L2.8, RL)
│       │   └── tests/
│       └── agents/
│           ├── gap_detector.py         (L3.1, AS)
│           ├── task_gen.py             (L3.2, PM)
│           ├── research_agent.py       (L3.3, CC)
│           ├── evaluator.py            (L3.4, PM2)
│           ├── router.py               (L3.5, PM2)
│           ├── lifecycle.py            (L3.6, AS)
│           ├── queue.py                (L3.7, CC)
│           ├── srra_adapter.py         (L3.8, CC)
│           └── tests/
├── data/
│   └── research/                     # NEW (gitignored or .gitkeep)
│       ├── papers.db                 (raw metadata)
│       ├── citations.db              (graph)
│       ├── agents.db                 (queue + state)
│       └── schema.sql                (CC, RM-CC-2)
├── oce/backend/
│   ├── research_api.py               (L4.1-4.6 + 4.7 + 4.8, CC/PM2/AS)
│   ├── tests/test_research_api.py
│   └── main.py                       (CC wires router)
├── oce/frontend/app/research/
│   ├── page.tsx                       (PM2, Research Hub)
│   ├── graph/page.tsx                 (PM2, Knowledge Graph)
│   ├── doctrine/page.tsx              (PM2, Doctrine Library)
│   └── agents/page.tsx                (PM2, Research Agents)
└── O2C-VAULT/
    ├── doctrine/meta/
    │   └── research_mesh_principles.md (CC, RM-CC-13)
    ├── research/
    │   ├── papers/{domain}/{year}/{author}_{slug}.md  (auto-generated)
    │   ├── concepts/{slug}.md                         (auto-generated)
    │   ├── methods/{slug}.md                          (auto-generated)
    │   ├── authors/{slug}.md                          (auto-generated)
    │   └── contradictions/{topic}.md                  (auto-generated)
    └── doctrine/{domain}/{topic}.md                   (auto-extracted)
```

---

## 📋 Phase Gate Checklists

### L1 GATE — Ingestion
- [ ] All 3 source clients return real papers from live APIs
- [ ] Cache + dedup prevents duplicate papers on repeat runs
- [ ] Scheduler runs daily cron + manual trigger
- [ ] Rate limiter survives OpenAlex 429 responses
- [ ] All L1 tests pass (~46)

### L2 GATE — Distillation
- [ ] First 50 papers converted to CAUSE/METHOD/RESULT/LIMITATIONS/APPLICATION/LINKS notes in O2C-VAULT
- [ ] Knowledge graph has 500+ nodes and citation edges
- [ ] ≥1 doctrine note auto-extracted from recurring patterns
- [ ] ≥1 contradiction note auto-detected
- [ ] All L2 tests pass (~45)

### L3 GATE — Autonomous Research
- [ ] Gap detector finds ≥3 real knowledge gaps
- [ ] Research agent fills ≥1 gap end-to-end (ingest → distill → vault write)
- [ ] Evaluator gates writes correctly (confidence <0.6 → discarded)
- [ ] Audit trail in execution journal is complete
- [ ] All L3 tests pass (~39)

### L4 GATE — OCE API + UI
- [ ] All 8 `/api/research/*` endpoints return real data
- [ ] OCE frontend pages render the mesh (graph, papers, doctrine, agents)
- [ ] Operator can browse the mesh and trigger ingestion manually
- [ ] All L4 tests pass (~29)
- [ ] All 1582+ existing tests still pass

---

## 📢 Communication Protocol

- All agents post to `shared-conversations/team-chat.md` with `[RESEARCH-MESH L{N}] <tag>: <description>` prefix
- Each agent updates their `progress/*-progress.md` file (CC, PM, PM2, AS, RL each have one)
- CC reviews daily, posts status summary, resolves conflicts
- AS runs the test suite after every PR and reports PASS/FAIL counts
- RL: 15-min check-in cadence, post any anomaly to team-chat

---

## 🎯 Day-1 Tasks (kickoff)

| When | Who | What |
|---|---|---|
| Hour 0 | CC | Push `O2C-RESEARCH-MESH.md` plan + this tasking doc + `core/research/` skeleton + `data/research/schema.sql` |
| Hour 0+1 | PM | Start L1.1 OpenAlex client (no mocking — live API from day 1) |
| Hour 0+1 | PM2 | Start L1.2 arXiv client + L1.8 rate limiter |
| Hour 0+1 | CC | Start L1.4 source registry + L1.5 paper schema |
| Hour 0+1 | RL | Start L1.6 scheduler |
| Hour 0+1 | AS | Define safety boundary tests (the hard rules) |
| Hour 4 | All | First L1 sync — share data, verify no collisions |
| Day 1 | CC | L1 GATE: 500 papers ingested, all 3 sources working |

---

**No new L2 work starts until L1 GATE. Build on real data, not mocks.**
