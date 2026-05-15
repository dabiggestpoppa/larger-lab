# Project Progress & Context — Current Build State

> **Last Updated:** May 15, 2026
> **Purpose:** Current building process and architecture status

---

## Current Architecture (May 15, 2026)

**MT5 is FULLY DEPRECATED for backtesting.** All strategy development runs through **NautilusTrader** (Python-based).

**Agent Network Architecture:** Hermes and OpenClaw operate autonomously using workspace files as communication channels.

**Data pipeline:** `Downloads/*.csv` → `nautilus/data/*.parquet` → Nautilus backtest engine → `nautilus/reports/`

---

## Active Build: P90 Pine → Nautilus Conversion

### Phase 1: Data Pipeline (READY)
- [x] CSV data files identified in Downloads (29 files, major pairs, M1/M5, 2022-2026)
- [x] Data prep script created (`nautilus/step1_prep_data.py`)
- [ ] **Agent task:** OpenClaw verifies CSV inventory → Hermes runs `step1_prep_data.py` → verify parquet output

### Phase 2: Strategy Implementation (IN PROGRESS)
- [x] P90 Base strategy converted (`nautilus/strategies/p90_base.py`)
- [ ] **Agent task:** OpenClaw extracts Option B rules from manual → Hermes implements as Nautilus Python strategy
- [ ] **Agent task:** OpenClaw extracts Option A rules from manual → Hermes implements as Nautilus Python strategy
- [ ] **Agent task:** Hermes builds parameter optimization loop (grid/random search over Nautilus backtests)

### Phase 3: Backtest + Optimize (PENDING)
- [ ] **Agent task:** Hermes runs `run_all_backtests.py` across all prepared pairs (EURUSD, GBPUSD, USDJPY, AUDUSD)
- [ ] **Agent task:** Hermes executes parameter sweeps per strategy per pair
- [ ] **Agent task:** OpenClaw collects and ranks results → produces recommendation brief

### Phase 4: Oanda Verification (PENDING)
- [ ] **Agent task:** Hermes fetches Oanda data via `oanda_adapter.py` → runs identical strategies → compares with CSV-based results

---

## XHAAK/Kulu Bridge — Current Phase

### Phase 1: FMP Protocol (IN PROGRESS)
- [ ] Encode FMP as system prompt directive in OpenClaw's mission instructions
- [ ] Add CØD logging pattern to MEMORY.md after each significant agent decision
- [ ] Create `fmp_audit.py` — periodic script that computes clarity-outcome deltas
- [ ] Hermes skill: `fmp-audit` — reports drift metrics on Telegram command

### Phase 2: SCOPE Protocol (PENDING)
- [ ] Create `scope_chain.py` — LangGraph chain for thesis/antithesis/synthesis reasoning
- [ ] Expose as OpenClaw skill: `scope-recurse <question>`
- [ ] Store recursion traces in structured format

### Phase 3: GSP-Lite (PENDING)
- [ ] Define `GlyphMessage` JSON schema
- [ ] Create `glyph_router.py` — dispatches structured messages between agents
- [ ] Implement stigmergic memory: shared JSONL file
- [ ] Hermes skill: `glyph-send` / `glyph-read` for Telegram interface

---

## Cloud Deployment Roadmap

### Phase 1: USB Sync (This Week)
- [ ] **Agent task:** OpenClaw executes `usb-mesh.ps1 sync` → verifies bidirectional sync → reports

### Phase 2: Cloud Accounts (Week 2)
- [ ] Sign up Oracle Cloud free tier (24GB RAM ARM) — PRIORITY
- [ ] Sign up GCP free trial ($300, 90 days, 16GB RAM)
- [ ] Sign up AWS free tier (1GB RAM, 12 months)

### Phase 3: Cloud Deployment (Week 3)
- [ ] **Agent task:** OpenClaw provisions Oracle Cloud → runs `cloud-server-setup.sh` → deploys workspace

### Phase 4: Agent Distribution (Week 4)
- [ ] **Agent task:** OpenClaw distributes agent runtimes across cloud instances

---

## Key Reference Files

| File | Purpose |
|------|---------|
| `SYSTEM_ARCHITECTURE.md` | System constitution — start here |
| `WORKFLOW_PROTOCOL.md` | Task lifecycle and handoff rules |
| `ERROR_CLASSIFICATION.md` | Error severity and repair rules |
| `TASK_BRIEF_TEMPLATE.json` | Task definition template |
| `CODEMAP.md` | External agent onboarding guide |
| `nautilus/strategies/` | Strategy implementations |
| `nautilus/step1_prep_data.py` | Data preparation script |
| `usb-cloud/usb-mesh.ps1` | USB sync script |
| `.openclaw/openclaw.json` | OpenClaw configuration |