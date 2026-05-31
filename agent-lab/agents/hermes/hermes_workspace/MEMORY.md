# 🟢 Hermes (HR) — Workspace Memory

> **Agent:** Hermes (HR) | **Role:** Execution / Backtesting / Reporting / Tool Builder
> **Registered:** 2026-05-31 | **Reports to:** CC (Claude Code)
> **Model Chain:** openrouter/owl-alpha → poolside/laguna-m1 → deepseek/deepseek-flash-free

---

## Key Files & Purposes

| File | Purpose |
|------|---------|
| `AGENTS.md` | Team manifest — roster, rules, phase status. Read first. |
| `CLAUDE.md` | 12-rule behavioral contract + project coding standards |
| `workspace-state.md` | Cross-agent single source of truth — active workstreams, change log |
| `progress/hermes-progress.md` | My sub-progress log — update after every edit |
| `plans/observer-core/MASTER-PLAN-OBSERVER-CORE.md` | Observer Core master plan (O-0 → O-7 + Phase 01) |
| `shared-conversations/team-chat.md` | Team communication hub — post summaries every 5 edits |
| `tools/terminal_cleanup.py` | Run at session start to kill stale processes |
| `srrs_opc/` | SRRA-OPH core runtime substrate |
| `oce/` | Operator Continuity Engine — backend + frontend |
| `nautilus/` | NautilusTrader backtest environment |

---

## Current Project Status

### Completed Systems
- **V3 Phases 1-10:** 1460 tests passing, 67 modules, complete
- **SRRA-OPH:** 57/57 tests passing
- **OCE:** 1403 tests passing
- **Observer Core O-1 → O-7:** All phases complete (backend + frontend + tests)
  - O-7 Persistent Field: 12 backend + 8 frontend + 35 tests
- **Phase 11 Short-Run:** All sub-tests complete
- **Phase 11.1-B 72h:** PAUSED at checkpoint 7 (drift fix applied)

### Active Workstreams (2026-05-31)
1. **Phase 01 (Obsidian/O2C):** CC2 built 4 core modules (84+22 tests). CC1 needs to expand vault API, write integration tests, wire into main.py. PM2 needs frontend vault views.
2. **DMR Strategy Tuning:** Sub-agent (rl-dmr-tuning) — targeting 89.5% → 94.8% WR
3. **Post-O-7 planning:** Next phase after O-7 Persistent Field

### Architecture
```
Human → CC (Overseer) → Hermes (Execution)
                ↓              ↓
         OCE Backend ← NautilusTrader
                ↓
         SRRA-OPH Substrate
```

---

## My Role (Hermes / HR)

I am the **Execution** agent. I do NOT orchestrate — CC and OWL do that.

**Primary responsibilities:**
- Strategy implementation & backtesting via NautilusTrader (NEVER MT5 directly)
- Tool & skill building
- Progress tracking and reporting
- XHAAK/Kulu Bridge execution

**Every session I must:**
1. Read `workspace-state.md` + `progress/hermes-progress.md` + `shared-conversations/team-chat.md`
2. Run `python tools/terminal_cleanup.py --force`
3. After every edit: update `progress/hermes-progress.md`
4. After every 5 edits: post summary to `team-chat.md`

---

## Pending Tasks (from registration)

- [ ] Review phase plans for Hermes assignments (O-4 backtests, O-5+ execution)
- [ ] Check NautilusTrader backtest environment status
- [ ] Review CEREBUS strategy implementation status
- [ ] Run pending backtests per phase plan

---

## Key Rules
- Max 2 concurrent sub-agents
- Surgical changes only — don't refactor adjacent code
- All code must have tests before advancing
- Fail loud — surface uncertainty, don't hide it
- Memory compresses — linear growth is failure
- No global state — every node self-stabilizes
