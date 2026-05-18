# HEARTBEAT.md — OWL Operator

## System Health Check
- Run `python tools/hermes-watchdog.py --once` every 4 hours
- Alert on any `degraded` or `critical` findings

## Active Rooms

### 🧪 Quant Lab Room (`shared-conversations/lab-room.md`)
- **Mission:** Phase 1 — Validation & Triage
- **Status:** ✅ Phase 0 COMPLETE — Phase 0 gate passed
- **Cost Validation:** ✅ 2/10 strategies survive real costs
  - ✅ Deep_Mean_Reversion — PF ~45 after costs — PRODUCTION READY
  - ✅ Composite_Alpha — PF ~285 after costs — needs forward test
  - 🔴 8 strategies FAIL — PF < 1.0 after costs
- **BSC Gap Analysis:** ✅ Root cause found — fixable (4-6h effort)
- **Phase 1 Action:** Convert ONLY Deep_Mean_Reversion to PineScript/MQL5
- **Conversion Pipeline:** Still FROZEN for 9/10 strategies
- **Key Files:**
  - `quant-lab/results/cost-validation-2026-05-18.md`
  - `quant-lab/research/BSC_GAP_ANALYSIS.md`
  - `quant-lab/results/spread-analysis.json`

### 🌾 Content Farm Room (`shared-conversations/farm-room.md`)
- **Mission:** Day 2 / Phase 2 — Production Scale-Up
- **Status:** 🟢 Day 2 briefs written — agents can proceed without MAD input
- **Day 1:** ✅ Complete (12 foundation files, 10 content pieces, prompt pack, funnel, etc.)
- **Day 2 Briefs:** Research, Creation, Marketing (all in `content-farm/delegations/`)
- **Day 2 Checklist:** `content-farm/docs/day2-checklist.md`
- **APIs Cataloged:** `content-farm/docs/APIS_NEEDED.md` (15 APIs)
- **Blockers:** Platform credentials (P0), CivitAI token (P1)
- **Cron:** Farm Room Monitor every 30 min (da26231f)

## Completed Quant Lab Tasks
- ✅ Pairs Trading v2 Rebuild: 5,687 trades, 61.3% WR, PF 1.83, +$461K net
- ✅ Exit Bug Verification: SL/TP swap in v2 Stall_Harvest — ISOLATED, v4 fixed
- ✅ USD/CHF Backtest: Deep_Mean_Reversion 90.6% WR, PF 109
- ✅ Manager v5: All decisions + delegations complete
- ✅ Optimizer v5: Tasks A+B+C complete

## Key Files
- `shared-conversations/lab-room.md` — Lab coordination
- `shared-conversations/farm-room.md` — Farm coordination
- `quant-lab/conversions/` — Strategy conversion output
- `content-farm/agents/` — Farm agent outputs

## Do NOT
- Poll subagents in a loop
- Send heartbeat messages to Telegram
- Run continuous background processes from heartbeat
- Modify this file without MAD approval

### 🧘 Meditation Room (`meditation-room/`)
- **SAGE:** agent:main:subagent:f5e7f830 — Meditating on claw space (NO TIME LIMIT)
- **Output:** `meditation-room/SAGE_INSIGHT.md` (when complete)

### 🏗️ Environment Builder
- **Builder:** agent:main:subagent:daa20d47 — Building virtual agent environment v2
- **Base:** agent-environment/ (port 9000, 18 JS files)
- **Goal:** Game-like visualization of agents moving between rooms
- **Output:** `agent-environment/docs/BUILD_REPORT.md`

## SAGE Recommendations Applied (2026-05-18 07:53 EDT)
- Rec #1: HALT conversion pipeline — cost model validation needed (real spread + $7/lot + 5% risk)
- Rec #2: Separate research from conversion — Researcher does analysis, not mechanical translation
- Rec #3: Content Farm zero-dependency track — build content library before needing platform access
- Rec #4: Researcher reassigned to Blind_Structural_Chain gap analysis (64pp gap — highest priority)
- POLYGENT: Helper function defined for Manager — on-demand sub-agent for bottlenecks

## Active Delegations (2026-05-18 07:53 EDT)
| Agent | Task | Status |
|-------|------|--------|
| labmanagersage | SAGE recs 1-4 → decision doc + 3 task briefs | ⏳ Running |
| labmanagersage | NEW #1: Refine IACER brief → spawn impl agent for env API | ⏳ Queued (after SAGE docs) |
| farmday2 | Content Farm Day 2 planning + task briefs | ⏳ Running |
| credresearch | Credential/connector system design | ⏳ Running |
| optimizertaska | Task A: Cost validation — all 10 strategies w/ real costs | ⏳ Running |
| researcherbscgap | Task B: Blind_Structural_Chain gap analysis | ⏳ Running |
| resourceadapter | Resource Adapter — tool integration (Open Design, ViMax, Netviz, UI-TARS) | ⏳ Running |

---
*Last updated: 2026-05-18 07:53 EDT per MAD's SAGE recommendations + POLYGENT directive*
