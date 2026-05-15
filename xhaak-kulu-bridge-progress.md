# XHAAK / Kulu → Current Implementation Bridge — Progress Tracker

> **Created:** May 15, 2026
> **Parent:** `PROJECT_PROGRESS.md` → XHAAK / Kulu → Current Implementation Bridge
> **Purpose:** Track implementation of legacy XHAAK/Kulu autonomous swarm concepts using OpenClaw + Hermes + Nautilus tooling.

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Complete / Operational |
| ⏳ | In Progress |
| 📋 | Planned / Not Started |
| ⚪ | Deferred / Skipped |

---

## 1. Gap Inventory (from old USB archive)

### 🔴 HIGH PRIORITY

#### FMP Protocol — Fracture Margin Protocol (Clarity-Outcome Delta)
- **Old Design:** Tracks the delta between an agent's stated clarity/confidence and actual outcomes over time. Audits infrastructure intention drift.
- **Old Tech:** Standalone Python microservice, Redis-backed, with Fractal Archive logging
- **New Implementation Path:**
  - [ ] **1a.** Encode FMP as a system prompt directive in OpenClaw's mission instructions (`.openclaw/openclaw_prompt.md`)
  - [ ] **1b.** Add CØD logging pattern to `MEMORY.md` after each significant agent decision
  - [ ] **1c.** Create `fmp_audit.py` — periodic script that reads MEMORY.md entries, computes clarity-outcome deltas, flags drift
  - [ ] **1d.** Hermes skill: `fmp-audit` — reports drift metrics on Telegram command
- **Status:** ⏳ In Progress (Task XKB-001 created)
- **Acceptance Criteria:** Agent can report its own clarity-vs-outcome delta for any recent decision when asked via Telegram

#### SCOPE Protocol — Semantic Causality Operations (Breathfold Recursion)
- **Old Design:** Recursive reasoning engine using LangGraph. Agents decompose problems through semantic oscillation — thesis/antithesis cycles with causal grammar tracking.
- **Old Tech:** LangGraph chains, custom causal grammar DSL, Redis state
- **New Implementation Path:**
  - [ ] **2a.** Create `scope_chain.py` — a LangGraph (or simple Python) chain that:
    - Takes a question
    - Generates thesis response (Model A)
    - Generates antithesis response (Model B)
    - Synthesizes via a third model
    - Tracks causal links between reasoning steps
  - [ ] **2b.** Expose as OpenClaw skill: `scope-recurse <question>`
  - [ ] **2c.** Store recursion traces in structured format for later analysis
- **Status:** 📋 Not Started (Pending FMP completion)
- **Acceptance Criteria:** Can recursively decompose any analytical question through 3+ thesis/antithesis cycles and produce a causal trace

### 🟡 MEDIUM PRIORITY

#### GSP-Lite — Genesis Swarm Protocol (Structured Agent Communication)
- **Old Design:** Glyph-based packet communication between distributed agents. Stigmergic shared memory. ZeroConf discovery.
- **New Implementation Path:**
  - [ ] **3a.** Define `GlyphMessage` JSON schema:
    ```json
    {
      "glyph": "message.type.identifier",
      "timestamp": "ISO8601",
      "source": "agent-name",
      "target": "agent-name | broadcast",
      "payload": { ... },
      "trace": ["previous-glyph-ids"]
    }
    ```
  - [ ] **3b.** Create `glyph_router.py` — dispatches structured messages between OpenClaw and Hermes
  - [ ] **3c.** Implement stigmergic memory: shared JSONL file where agents leave "traces" for each other
  - [ ] **3d.** Hermes skill: `glyph-send` / `glyph-read` for Telegram interface
- **Status:** 📋 Not Started
- **Acceptance Criteria:** Two agents can exchange structured glyph messages via shared file, visible via Telegram

#### Browser Ritual Agent (BRA)
- **Old Design:** Playwright-based web automation agent. Ritual Schema → Ritual Executor → Ritual Memory pipeline.
- **New Implementation Path:**
  - [ ] **4a.** Create `bra_skill.md` — defines available browser rituals (data fetch, form fill, monitoring)
  - [ ] **4b.** Implement `browser_ritual.py` — Playwright wrapper with ritual executor
  - [ ] **4c.** Connect to Hermes via skill: `bra-execute <ritual-name> <params>`
  - [ ] **4d.** Store results in ritual memory (structured JSON)
- **Status:** 📋 Not Started
- **Acceptance Criteria:** Telegram command triggers a browser automation task (e.g., fetch TradingView data, check broker balance)

#### DSPy Optimization Loop
- **Old Design:** Automated prompt optimization using DSPy's compile/optimize cycle against Nautilus backtest results
- **New Implementation Path:**
  - [ ] **5a.** After backtest validation phase, collect strategy performance data
  - [ ] **5b.** Define DSPy signature for strategy parameter optimization
  - [ ] **5c.** Create optimization loop: backtest → evaluate → refine prompt → re-backtest
- **Status:** 📋 Not Started
- **Acceptance Criteria:** Automated loop improves strategy parameters by measurable Sharpe ratio delta

### 🟢 LOW PRIORITY

#### Glyph Communication Schema (Standalone)
- **Old Design:** Symbolic packet format for agent-to-agent messaging
- **New Implementation Path:** Subsumed by GSP-Lite (item 3a above)
- **Status:** ⚪ Merged into GSP-Lite

#### ZeroConf Agent Discovery
- **Old Design:** mDNS-based automatic agent discovery on local network
- **New Implementation Path:** Defer — OpenClaw gateway on :18789 handles all routing. Not needed at current scale.
- **Status:** ⚪ Deferred

### ⚪ DEFERRED / SKIPPED

| Component | Reason |
|-----------|--------|
| Kulu Containerized Orchestration (Podman) | Overkill at current scale; single-instance deployment sufficient |
| Tailscale Mesh Networking | Single cloud instance + SSH tunnels adequate |
| Nightly LoRA Training Pipeline | Requires GPU burst infrastructure; no training data yet |
| Rust Runtime (PyO3 modules) | Python performance is sufficient; optimize only if bottleneck identified |
| LocalAGI Fork | OpenClaw replaces this entirely |
| Multi-server Hetzner Deployment | Start with single CX31; expand if needed |

---

## 2. Implementation Phase Plan

### Phase 1: Consolidation (Now → Week 1)
**Goal:** Wire existing agents to trigger and collect Nautilus backtests
- [ ] Wire Hermes Telegram bot to accept backtest commands
- [ ] Connect OpenClaw to `run_all_backtests.py` as a callable tool
- [ ] Verify data pipeline: CSV → Parquet → Nautilus → Report
- [ ] Run first full backtest batch (EURUSD, GBPUSD, USDJPY, AUDUSD)

### Phase 2: Cerebus Dialectic Brain (Week 2–3)
**Goal:** Implement dual-model reasoning loop for strategy analysis
- [ ] Create dialectic prompt template (primary + devil's advocate + synthesis)
- [ ] Wire into ParallelThoughtSynthesizer
- [ ] Test against historical backtest results for validation
- [ ] Deploy as OpenClaw skill: `cerebus-analyze <strategy-result>`

### Phase 3: FMP Protocol (Week 3–4)
**Goal:** Add clarity-outcome tracking to agent decision-making
- [ ] Implement CØD logging in MEMORY.md
- [ ] Create `fmp_audit.py` analysis script
- [ ] Add Hermes skill for FMP reporting
- [ ] First audit cycle: retroactively analyze recent agent decisions

### Phase 4: GSP-Lite + Agent Communication (Week 4–6)
**Goal:** Structured inter-agent messaging and stigmergic memory
- [ ] Define glyph schema and message format
- [ ] Build glyph router
- [ ] Implement stigmergic shared memory file
- [ ] Test: Hermes sends glyph → OpenClaw reads and acts → result logged

### Phase 5: Browser Ritual Agent (Week 6–8)
**Goal:** Web automation capability for agents
- [ ] Build Playwright ritual executor
- [ ] Create 3 initial rituals: data fetch, broker check, TradingView scrape
- [ ] Connect to Hermes Telegram interface
- [ ] Test end-to-end: Telegram command → browser action → result report

### Phase 6: DSPy Optimization (Week 8+, post-backtest validation)
**Goal:** Automated strategy parameter and prompt optimization
- [ ] Collect sufficient backtest data for training signal
- [ ] Define DSPy signatures
- [ ] Build optimization loop
- [ ] Run first optimization cycle

---

## 3. Key Insight

> **The XHAAK/Kulu vision was 16 weeks of building distributed microservices from scratch. The same vision, reimagined with OpenClaw + Hermes, collapses to ~8 weeks of building agent skills and prompt patterns.** The philosophical architecture (FMP clarity tracking, SCOPE recursive reasoning, GSP swarm communication) is preserved — but implemented as lightweight agent behaviors rather than standalone services. This is the fundamental paradigm shift: **the platform now handles distribution, orchestration, and model routing; we only need to define the behaviors.**

---

## 4. Reference Files

| File | Purpose |
|------|---------|
| `PROJECT_PROGRESS.md` | Master project tracker (parent document) |
| `usb-cloud/xhaak-kulu-inventory.md` | Full inventory of archived USB files |
| `usb-cloud/ARCHITECTURE.md` | Storage architecture for old + new files |
| `parallel_thought/parallel_thought_synthesizer.py` | Multi-model reasoning engine (foundation for SCOPE) |
| `nautilus/strategies/symmetry_trap.py` | Primary Cerebus strategy (already ported) |
| `SYSTEM_ARCHITECTURE.md` | Agent system constitution |
| `WORKFLOW_PROTOCOL.md` | Task lifecycle and handoff rules |

---

## 5. Weekly Log

### Week 1 (May 15, 2026)
- **Action:** Full USB archive review and cataloguing completed
- **Action:** Gap analysis completed — 10 missing components identified, prioritized
- **Action:** PROJECT_PROGRESS.md updated with XHAAK/Kulu bridge subsection
- **Action:** This tracker file created
- **Next:** Begin Phase 1 — wire Hermes to Nautilus backtest pipeline