# Project Progress & Context — Current Build State

> **Last Updated:** May 16, 2026
> **Purpose:** Current building process and architecture status
> **Current Phase:** Phase 4 — Workspace Integration
> **Tests:** 23 passing (Phase 2: 7/7, Phase 3: 4/4, Book 2: 6/6, Phase 4: 6/6)

---

## 🦉 [RL] OWL — Last Sync: 2026-05-16 13:18 UTC

*Auto-synced from `progress/rl-progress.md`*

#### 🦉 [RL] 2026-05-16 — Scrapling Skill Installed for All Agents
- Installed `scrapling` v0.4.8 + Playwright Chromium
- Created `skills/scrapling/SKILL.md` — concise reference for all agents
- Copied to `.agents/skills/scrapling/SKILL.md` for agent harness loading
- Updated `TOOLS.md` with Scrapling section
- Posted announcement to `shared-conversations/team-chat.md`
- **DSPy evaluation complete**: Recommended integration points identified
  - Skill creator eval loop (automatic prompt optimization)
  - Parallel thought synthesis (cleaner module abstraction)
  - Agent task briefs (type-safe signatures)
  - Workspace integration (adapter pattern alignment)

#### 🦉 [RL] 2026-05-16 — OC1/OC2 Gateway Conflict Diagnosed
- **Root cause found**: OC1's `gateway.cmd` was missing `OPENCLAW_HOME` env var, causing it to default to `%USERPROFILE%\.openclaw` and read OC2's config
- **Symptom**: OC1 kept dying silently or killing OC2's process (stale PID in `gateway-restart-intent.json`)
- **Fix applied**: Updated `C:\Users\wifik\.openclaw\gateway.cmd` to include `OPENCLAW_HOME=C:\Users\wifik\.openclaw` and port 18789
- **Status**: Both gateways can start but OC1 still dies intermittently — needs further investigation
- **Config separation verified**: OC1 (port 18789, bot @finalstrawclawbot) and OC2 (port 18790, bot @OC2BLRBOT) have distinct configs, tokens, and ports
- **Docker option**: No container runtime available on system (no Docker, no Podman). Would need Docker Desktop install + reboot
- **Recommendation**: Run OC2 only (it's stable). OC1 can be revived later with clean gateway.cmd

#### 🦉 [RL] 2026-05-16 — Both Gateways Fixed & Running 24/7
- **Root cause of both gateways failing**: `gateway.cmd` used `openclaw gateway --port X` instead of `openclaw gateway run --port X --allow-unconfigured`
- **Fixes applied**:
  - Fixed `C:\Users\wifik\.openclaw\gateway.cmd` — added `run` subcommand and `--allow-unconfigured`
  - Fixed `C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\gateway.cmd` — same fix
  - Fixed OC2 startup file to properly call its `gateway.cmd` with full path
  - Created `tools\gateway-watchdog.cmd` — checks both gateways every 60s, restarts if down
  - Created `tools\register-gateway-tasks.ps1` — Scheduled Task registration (requires Admin)
  - Added watchdog to startup folder for automatic 24/7 monitoring
- **Status**: ✅ Both gateways live and healthy
  - OC1 (port 18789): `{"ok":true,"status":"live"}` — PID 19844
  - OC2 (port 18790): `{"ok":true,"status":"live"}` — PID 41592
- **Auto-start**: Startup folder entries for both gateways + watchdog
- **Note**: For even more reliable auto-start, run `tools\register-gateway-tasks.ps1` as Administrator to create Windows Scheduled Tasks with restart-on-failure

#### 🦉 [RL] 2026-05-16 — OC1 Telegram Not Responding (Diagnosis)
- **Symptom**: OC1 gateway running (port 18789) but Telegram bot @finalstrawclawbot not responding
- **Root cause 1**: Missing `openrouter` provider in OC1's `openclaw.json` — only had poolside/nvidia/deepseek, causing fallback to `openai` provider → "No API key found" error
- **Root cause 2**: OC1's `models.json` has placeholder `"apiKey": "OPENROUTER_API_KEY"` instead of actual key
- **Root cause 3**: Telegram API connectivity issues — DNS resolution slow, fetch timeouts, event loop delays up to 104s
- **Root cause 4**: 203 Telegram commands registered (limit 100), causing command sync failures
- **Fix applied**: Added openrouter provider to OC1's `openclaw.json`
- **Status**: After restart, OC1 health check failed — needs further investigation in new chat
- **OC2**: Working fine throughout, no changes needed
- **Detailed notes**: See `/memories/session/oc1-gateway-diagnosis.md`

#### 🦉 [RL] 2026-05-16 — Gateway Diagnostics Complete, Ready for Fix
- **Current state**: Both gateways running (OC1 PID 14520, OC2 PID 21768)
- **OC2 issue identified**: Stuck Telegram session `agent:main:telegram:direct:8258195396` blocking event loop for 1000+ seconds
- **Root cause**: Event-loop starvation from stuck session → Telegram polling stalls every ~180s → forced restarts
- **Fixes needed**:
  1. Clear stuck session from OC2's `sessions.json`
  2. Disable native Telegram commands (`channels.telegram.commands.native: false`) to avoid 203-command overload
  3. Restart both gateways cleanly
- **PowerShell spam issue**: `openclaw gateway probe` without `--token` hangs forever → terminal timeout → new terminal spawned → infinite loop
- **Solution**: Use venv-based Python scripts for gateway management instead of CLI commands

---
## 🟠 [OC2] OpenClaw 2 — Last Sync: 2026-05-16 13:18 UTC

*Auto-synced from `progress/openclaw-2-progress.md`*

#### 🟠 [OC2] 2026-05-16 — Agent Fully Online
- Gateway running on port 18790 (OC1 uses 18789)
- Telegram @OC2BLRBOT connected & paired ✅
- 20 skills migrated from Hermes
- Auto-start: Startup folder + Scheduled Task
- Discord channel config pending (schema issue — Telegram working)

---
## 🔴 [PM] Polymorph — Last Sync: 2026-05-16 13:18 UTC

*Auto-synced from `progress/polymorph-progress.md`*

#### 🔴 [PM] 2026-05-16 — External Resource Analysis & Implementation
Analyzed 5 external resources and implemented what we can NOW:

#### 🔴 [PM] 2026-05-16 — Workspace Reorganization Complete
- Created folder structure: `docs/`, `docs/images/`, `docs/phases/`, `all-mermaids/`, `tools/bin/`, `tools/scripts/`, `tools/workspaces/`
- Moved 15+ root files to proper locations (scripts→tools/scripts, binaries→tools/bin, docs→docs/, etc.)
- Created `all-mermaids/` with 15 diagram files organized by phase:
  - `phase1-5-original/` — 7 diagrams from PROJECT_PROGRESS.md
  - `phase1-5-updated/` — 5 diagrams from CODEMAP.md
  - `phase6-9-resources/` — 2 diagrams (full topology + agent integration)
- Created `README.md` with full workspace documentation
- Updated `CODEMAP.md` with new workspace map and quick start
- Root directory cleaned to core config/docs only

#### 🔴 [PM] 2026-05-16 — GitHub Repos Cloned
All 6 repos from `dabiggestpoppa` account now cloned to `C:\Users\wifik\Desktop\projects\`:

#### 🔴 [PM] 2026-05-16 — Full Tool Pipeline + HTML Standard + Agency-Agents Import

#### 🔴 [PM] 2026-05-16 — Motus Agent Framework Installed
- lithosai-motus v0.4.1 installed (Python 3.12+, 21 packages)
- skills/motus/ — Full skill with ReActAgent, task graphs, MCP, serving
- 	ools/motus_agent.py — Build, serve, chat, deploy wrapper
- Source: C:\Users\wifik\Desktop\projects\motus\
- Features: ReActAgent, @agent_task workflows, multi-provider, MCP, Docker, guardrails, memory, cloud deploy

---
## 🟡 [AS] Assistant Manager — Last Sync: 2026-05-16 13:18 UTC

*Auto-synced from `progress/assistant-progress.md`*

#### 🟡 [AS] 2026-05-16 00:30:00Z — Phase 6-9 Resource Assessment Task
- Received Phase 6-9 plan with GitHub repos and research papers
- Created `tasks/PHASE-6-9-RESOURCES.md` with full repo list and assessment criteria
- **Repos to evaluate:** Neo4j Agent Memory, MemoryGraph MCP, Graphonomous, ArqonDB, AgentMesh, Open Multi-Agent, orxhestra, Skillrunner, OpenLoci, GraphPalace
- **Papers to evaluate:** SAGE, VMAO, Topology Matters
- Deliverables: `srrs_opc/docs/resource_assessment.md`, `srrs_opc/docs/integration_plan.md`
- Starting assessment now — will update progress file with findings

#### 🟡 [AS] 2026-05-16 01:30:00Z — Resource Assessment Complete + Delegation
- Completed full resource assessment: 12 repos/papers evaluated
- 8 approved for integration, 2 deferred, 2 need investigation
- Created `srrs_opc/docs/resource_assessment.md` with integration plan
- Created `srrs_opc/docs/resource-reference.md` consolidated reference
- Delegated tasks to OC (API evaluation, Neo4j schema, Phase 4 design) and HR (stress tests, workspace integration)
- All tests verified: Phase 2 (7/7), Phase 3 (4/4), Book 2 (6/6) — all passing
- Next: monitor OC/HR progress, prepare Phase 4 component stubs

#### 🟡 [AS] 2026-05-16 01:00:00Z — Book 2 Integration: Phase 3-5 Updated Architecture
- Read and analyzed updated Phase 3-5 plans (Book 2 integration)
- Updated `srra-oph-build` skill to v2 with overlap-first architecture
- Created new component stubs:
  - `active_collar_fields.py` — Active collar fields (edges as computation)
  - `local_consensus.py` — Local consensus engines (consensus != sync)
  - `capability_fields.py` — Capability fields (tools as topology regions)
  - `trajectory_fields.py` — Trajectory reconstruction fields (identity as trajectory)
- Created design docs: `phase4_design.md`, `phase5_design.md`
- Updated `__init__.py` with all new exports
- Updated CODEMAP.md with Book 2 architecture diagrams
- **Key architectural shifts documented:**
  - Phase 3: Overlap collars are continuity engine (not observer nodes)
  - Phase 4: Tools are capability fields (not isolated endpoints)
  - Phase 5: Identity is reconstructable trajectory (not persistent state)

#### 🟡 [AS] 2026-05-16 02:00:00Z — Cron-Style Monitoring Active
- All tests passing: Phase 2 (7/7), Phase 3 (4/4), Book 2 (6/6) = 17/17 total
- Resource assessment complete: 8/12 repos approved for integration
- Tasks delegated to OC and HR via team-chat.md
- Cron check script created at `tools/as-cron-check.py`
- **Current blockers**: None — all systems green
- **Next check**: Monitor OC/HR progress on delegated tasks

#### 🟡 [AS] 2026-05-16 08:00:00Z — OpenClaw 2 Setup Complete
- Created `.openclaw-2/` config directory with valid OpenClaw schema
- Configured Telegram @OC2BLRBOT (port 18790) — paired and working
- Migrated 20 Hermes skills to `.openclaw-2/skills/`
- Updated `.agent-tags.json` — HR → OC2
- Updated `progress-sync.py` — OC2 added to AGENTS + CLI choices
- Updated `team-chat.md` — OC2 online, Phase 6 tasks cleaned up, Phase 8 planning
- Updated `AGENTS.md` — phase status → Phase 8
- Updated `KEYS.md` — OC1 + OC2 bot tokens documented
- Created startup shortcut `OpenClaw 2 Gateway.cmd` for auto-start
- Discord channel config deferred (schema validation issue — Telegram working)
- All 38 tests still passing ✅
- **Next:** Add Discord config, implement Phase 8 components (Sovereignty Economics, Probabilistic Self-Models, MSR Compression)
- [ ] Prepare Phase 4 component stubs based on resource assessment
- [ ] Run cron check every 30min while stepping away
- [ ] Review Phase 2 test results
- [ ] Monitor team progress files

---
## 🟢 [HR] Hermes — Last Sync: 2026-05-16 06:43 UTC

*Auto-synced from `progress/hermes-progress.md`*

#### 🟢 [HR] 2026-05-16 — v2 Upgrade Complete
- Upgraded from v1 (basic backtesting) to v2 (full agent)
- New agent prompt: `agent_prompt_v2.md` with complete protocol
- Soul file created: `SOUL.md` (identity, personality, hard limits)
- Skills index created: `SKILLS_INDEX.md` (all 22 skills mapped)
- Skills copied to `agent-lab/agents/hermes/skills/` (local skill directory)
- Team chat access: can now write to `shared-conversations/team-chat.md`
- Memory updated: `.hermes/MEMORY.md` logged v2 upgrade
- Ready for Phase 4 workspace integration tasks

#### 🟢 [HR] 2026-05-15 12:10:00Z — Autopilot v2 Results (Iteration 15)
- P90_CFD_Expansion (USDJPY): 0.01% return, 232 trades
- RSI_Reversion (USDJPY): 0.01% return, 352 trades
- Strategy exit logic corrected (mean reversion at -25% Asian Range)
- Position sizing fixed (10 micro lots per trade)

#### 🟢 [HR] 2026-05-15 09:33:00Z — Strategy Logic Fixes
- Fixed P90 exit: -25% pullback (mean reversion) instead of +25% extension
- Fixed position sizing: 10 micro lots with proper pip value
- Updated hermes_autopilot_v3.py with corrected logic

---
## � [CC] Claude Code — Last Sync: 2026-05-15 23:10 UTC

*Auto-synced from `progress/claude-code-progress.md`*

#### 🔵 [CC] 2026-05-15 23:10:00Z — OpenClaw Telegram Bot Live
- Bot token configured: `@finalstrawclawbot` (8718444747:...)
- `openclaw doctor --fix` resolved models config schema issues
- Gateway running with Telegram channel: **configured** ✅
- Windows Scheduled Task installed for auto-start
- User session active: `telegram:direct:8258195396`
- dmPolicy: pairing (secure — requires approval for new DMs)
- Can now talk to OpenClaw from Telegram when away from desk

---

## �🟢 [HR] Hermes — Last Sync: 2026-05-15 22:28 UTC

*Auto-synced from `progress/hermes-progress.md`*

#### 🟢 [HR] 2026-05-15 12:10:00Z — Autopilot v2 Results (Iteration 15)
- P90_CFD_Expansion (USDJPY): 0.01% return, 232 trades
- RSI_Reversion (USDJPY): 0.01% return, 352 trades
- Strategy exit logic corrected (mean reversion at -25% Asian Range)
- Position sizing fixed (10 micro lots per trade)

#### 🟢 [HR] 2026-05-15 09:33:00Z — Strategy Logic Fixes
- Fixed P90 exit: -25% pullback (mean reversion) instead of +25% extension
- Fixed position sizing: 10 micro lots with proper pip value
- Updated hermes_autopilot_v3.py with corrected logic

---
## 🟣 [OC] OpenClaw — Last Sync: 2026-05-16 13:18 UTC

*Auto-synced from `progress/openclaw-progress.md`*

#### 🟣 [OC] 2026-05-15 18:27:00Z — P90 Unified Engine Bug Fix + Results
- **Bug found**: `est_h == 3` classification was DEAD CODE inside Asian session block
  - Asian block: `if est_h >= 19 or est_h < 3` — est_h==3 never enters this block
  - `ar_pips` was never set → all entry signals skipped
  - Fixed by moving classification OUTSIDE the Asian block
- **Fixed all 3 strategies**: cascade_combo, cascade_only, base
- **Results on EUR/USD (50k bars)**:
  - P90_Cascade_Combo: 34.2% WR, -7.71p P&L, 263 trades
  - P90_Cascade: 33.9% WR, -40.51p P&L, 257 trades
  - P90_Base: 35.6% WR, -138.47p P&L, 486 trades
- **Root cause of losses**: Only 11 trades hit TP2 (-50% AR), 143+ hit SL
  - Mean reversion target too far for most trades
  - Need parameter tuning or TP logic adjustment
- **Files**: `nautilus/strategies/p90_unified.py` (unified engine)
- **Results saved**: `nautilus/results/p90_unified_20260515_182727.json`

#### 🟣 [OC] 2026-05-15 20:44:00Z — Initial Setup
- OpenClaw gateway running on ws://127.0.0.1:18789
- Model routing configured with fallbacks
- Skills loaded from `.hermes/skills/` + `nautilus/`
- SRRA-OPH Phase 1 directives added to openclaw_prompt.md

#### 🟣 [OC] 2026-05-15 22:25:00Z — Discord Bot Setup Complete
- **blrr city** bot connected to Discord gateway
- Slash commands registered: `/hermes`, `/openclaw`, `/agent_status`
- @mention routing working — responds as active agent (Hermes default)
- Agent switching via `/hermes` and `/openclaw` commands
- Webhooks pre-configured in .env (Hermes + OpenClaw)
- Windows encoding fix applied (UTF-8 stdout)
- Bot running as background process on blrrr host
- **Note**: Separate Hermes/OpenClaw bot tokens still needed for independent bot instances

---
## 🔵 [CC] Claude Code — Last Sync: 2026-05-16 13:18 UTC

*Auto-synced from `progress/claude-code-progress.md`*

#### 🔵 [CC] 2026-05-15 22:30:00Z — Full Team Workflow Infrastructure
- Created `tools/codemap-updater.py` — auto-generates Mermaid diagrams for CODEMAP.md
- Created `tools/task-runner.py` — lightweight task queue for CC/OC/HR
- Created `tools/phase-gate.py` — SRRA-OPH phase transition manager (Phases 0-5)
- Created `tools/workflow-runner.py` — continuous workflow heartbeat
- Created `skills/agent-team-workflow/SKILL.md` — team SOP
- Updated `.openclaw/openclaw_prompt.md` — full workflow instructions for OC
- Updated `agent-lab/agents/hermes/hermes_workspace/agent_prompt.md` — full workflow for HR
- Fixed Windows encoding (cp1252) for emoji in all tools
- Initialized phase tracking: Phase 1 ✅ → Phase 2 🔄
- Tested full pipeline: all tools working

#### 🔵 [CC] 2026-05-15 23:00:00Z — Phase 2 Core Build + Team Expansion
- Built all Phase 2 components:
  - `srrs_opc/recovery_anchors.py` — SQLite-based sparse persistence
  - `srrs_opc/drift_detector.py` — staleness + weight drift detection
  - `srrs_opc/consistency_validator.py` — direct/temporal contradiction detection
  - `srrs_opc/reconstruction_synthesizer.py` — continuity from sparse anchors
  - `srrs_opc/contradiction_resolver.py` — weight-wins auto-resolution
  - `srrs_opc/constraint_propagator.py` — event-driven constraint propagation
  - `srrs_opc/tests/test_phase2_e2e.py` — 7/7 integration tests passing
- Added Assistant Manager (AS) agent to team registry
- Created `progress/assistant-progress.md` and `shared-conversations/assistant-prompt.md`
- Updated `tools/progress-sync.py` to include AS agent
- Delegated tasks to OC (architecture review), HR (testing), AS (quality/docs)
- Set up `shared-conversations/team-chat.md` as team coordination hub
- Awaiting Phase 6-9 plan file from user

#### 🔵 [CC] 2026-05-16 00:30:00Z — Phase 3 Complete + Phase 4 Kickoff
- Built Phase 3 components:
  - `srrs_opc/dynamic_coupling.py` — adaptive edge weights
  - `srrs_opc/topological_router.py` — entropy-based routing with rerouting
  - `srrs_opc/distributed_consensus.py` — gossip protocol consensus
  - `srrs_opc/tests/test_phase3_e2e.py` — 4/4 tests passing
- Phase 3 → Phase 4 advanced
- Received Phase 6-9 plan with GitHub resources
- Created `tasks/PHASE-6-9-RESOURCES.md` for AS assessment
- Updated team chat with Phase 4 tasks

#### [CC] 2026-05-16 01:30:00Z — All 23 Tests Passing + Phase 4 Complete
- Fixed import issues in AS-created modules (overlap_aware_tooling, reconstruction_safe_exec)
- Fixed Phase 4 test failures (backup adapter health check/execute)
- All 23 tests passing: Phase 2 (7/7), Phase 3 (4/4), Book 2 (6/6), Phase 4 (6/6)
- workspace_integration.py: ToolRole enum, ToolAdapter base, OpenClawAdapter, HermesAdapter, NautilusAdapter, ClaudeAdapter
- WorkspaceIntegrationLayer: route_task(), health_check_all(), get_status()
- Phase 4 criteria: OpenClaw mapped to strategic synthesis, Hermes to execution, Nautilus to verification, Claude to symbolic reasoning
- No workspace tool is central memory/orchestration/identity

#### [CC] 2026-05-16 01:15:00Z — Phase 4 Workspace Integration Built
- Created `srrs_opc/workspace_integration.py` — Tool adapter layer
- ToolRole enum: STRATEGIC_SYNTHESIS, EXECUTION, ENVIRONMENT_VERIFICATION, etc.
- Adapters: OpenClawAdapter, HermesAdapter, NautilusAdapter, ClaudeAdapter
- WorkspaceIntegrationLayer: routes tasks through SRRA roles, not directly to tools
- Health checks for all tools
- All 11 tests still passing after new code
- CC workflow engine running in background (2min cycle)
- AS working on Phase 6-9 resource assessment

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

## SRRA-OPH Phase 1: Foundational Observer Mesh (COMPLETED)

### Completed
- [x] Created `srrs_opc/` module with base patch infrastructure
- [x] Implemented 4 observer patches:
  - PlannerPatch - Strategic planning with bounded horizon
  - ExecutionPatch - Action execution with bounded operations
  - MemoryPatch - Memory with bounded retention
  - RepairPatch - Self-repair monitoring
- [x] Created CollarLayer for structured overlap synchronization
- [x] Created AgentBridge for OpenClaw/Hermes integration
- [x] Tested 3-cycle synchronization - all patches stable

### Architecture
```
┌─────────────────────────────────────────────────────────┐
│              Collar Layer (Coordinator)                │
├─────────────────────────────────────────────────────────┤
│  Planner  →  Execution  →  Memory  →  Repair             │
│    (plans)    (acts)      (stores)    (fixes)           │
└─────────────────────────────────────────────────────────┘
```

### Key Features
- **Bounded State**: Each patch has max limits (history, actions, horizon)
- **Self-Repair**: Patches detect inconsistency and repair locally
- **Collar Protocol**: JSON-based state synchronization between patches
- **Agent Bridge**: Syncs patch states to OpenClaw and Hermes agents

### Next Steps
- [ ] Integrate with Hermes Telegram bot for real-time sync
- [ ] Add Redis/NATS messaging for inter-agent communication
- [ ] Implement Phase 2: Observer Mesh Expansion

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