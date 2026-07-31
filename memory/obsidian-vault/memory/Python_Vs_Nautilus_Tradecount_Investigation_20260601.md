# Python Vs Nautilus Tradecount Investigation 20260601

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

# Python ST vs Nautilus Trade Count Disinvestigation

> **Date:** 2026-06-01 01:16 EDT
> **Status:** Awaiting Architect Review (MAD sending)
> **Not a bug — Python under-delivering (MAD confirmed)**

## Problem Statement
Python Symmetry Trap engine produces significantly fewer trades than Nautilus backtest on XAUUSD.
- **Nautilus XAUUSD ST:** 1,718 trades at 81.8% WR
- **Python XAUUSD ST:** 604 trades at 84.4% WR
- **Ratio:** 2.84x difference
- **Manual expectation:** 1k+ trades (matches Nautilus)

## Data

### Python XAUUSD Full Funnel
| Metric | Value |
|--------|-------|
| Total days with Asian data | 1,362 |
| NO-GO sessions (AR > 95p) | 1,046 (76.8%) |
| Active sessions | 316 (23.2%) |
| Active with trades | 222 (70.3% of active) |
| Active no trades | 94 (29.7% of active) |
| Total entries | 604 |
| TP hits | 67 (11.2%) |
| SL hits | 533 (88.8%) |
| Kill switches | 131 |

### Trade Funnel
| Stage | Sessions | Conversion |
|-------|---------|------------|
| Active | 316 | — |
| Impulse detected | 243 | 76.9% |
| Retrace qualified | 230 | 94.7% |
| OCC confirmed (entry) | 222 | 96.5% |

## What Was Checked (All Confirmed Identical)
1. Tier configs (T1/T2/T3/AU/trigger) — IDENTICAL
2. NO-GO logic (AR > max tier) — IDENTICAL
3. Session init (swing_origin from first post-init bar) — IDENTICAL
4. Kill switch (80% retracement) — IDENTICAL
5. Loop counting (5 max) — IDENTICAL
6. SL (zero-buffer extreme, close-only) — IDENTICAL
7. TP (1 AU, wick or close) — IDENTICAL
8. DZ thresholds (Loop 1: 32-50%, Loop 2+: 20-50%) — IDENTICAL
9. OCC (close in impulse direction) — IDENTICAL

## Code Differences Found (None Explain Fewer Trades)
1. **Asian bar filtering:** Nautilus returns during Asian hours; Python processes them → Python should have MORE trades, not fewer
2. **Kill switch in Nautilus strategy** calls `self._handle_kill_switch(bar, c)` returning bar close — functionally same as Python

## Unverified Hypotheses
1. **Bar data difference:** Nautilus `BarDataWrangler` might produce different/more bars than Python `load_m5_csv`
2. **EST hour classification:** Different timestamp handling could cause Nautilus to classify more sessions as active
3. **Nautilus strategy init:** `est_offset=-5` hardcoded; Might differ from Python's `(b.timestamp.hour - 5) % 24` for edge cases around midnight

## Files Involved
- `quant-lab/engines/symmetry_trap.py` — Python engine (TRUTH SOURCE)
- `quant-lab/strategies/symmetry_trap_strategy.py` — Nautilus strategy
- `quant-lab/backtests/run_cerebus_backtest_fixed.py` — Nautilus runner
- `quant-lab/configs/asset_configs.py` — Per-asset configs
- `quant-lab/engines/symmetry_trap_backtest.py` — Python CSV loader

## Next Steps
1. Architect (MAD's agent) to review full debug report
2. Identify specific structural difference causing trade count gap
3. Either fix Python engine or accept Nautilus as ground truth
4. Update NT8 C# logic if Python engine changes needed

## Note
Across ALL 19 assets in backtest campaign v3, the Python engine found fewer trades than expected. The XAUUSD gap (604 vs 1,718) is the most extreme case studied. All 94 "no-trade" active sessions had valid tier classification (T1/T2/T3) but produced 0 entries — suggesting the impulse trigger is too restrictive for certain market regimes.

LINKS:
[[System Architecture]]
[[V3 Cognitive Field]]
[[Operator Rules]]
[[2026 05 17]]
[[2026 05 18]]
[[2026 05 20]]
[[2026 05 21]]
[[2026 05 30]]
[[2026 05 30 Evening]]
[[2026 05 30 Nautilus Fix]]
[[2026 05 31]]
[[2026 06 01]]
[[Active Strategies Performance]]
[[Agent Topology]]
[[Api Execution Architecture 20260531]]
[[Api Reference Summary]]
[[Api Test Note]]
[[Backtest Campaign Status 20260531]]
[[Backtest Campaign V3 Results]]
[[Backtest Phase Status]]
[[Build Patterns]]
[[Build Progress 20260531]]
[[Cc Phase 01 Build Certification Report]]
[[Cerebus Nt8 Deployment Campaign 20260531]]
[[Daily Runtime 20260531]]
[[Dashboard Build Complete]]
[[Doctor Prescription]]
[[Errors And Solutions]]
[[Executor Crash 20260531]]
[[Failure Index Oc2]]
[[Foundational Principles]]
[[Hermes Agent Activation Note]]
[[Hermes Agent Test]]
[[Hermes Agent Test Note]]
[[Hermes Obsidian Test   Vault Working]]
[[Journal 20260602T004840Z Command Graph]]
[[Journal 20260602T004840Z Command Help]]
[[Journal 20260602T004840Z Command Status]]
[[Journal 20260602T004840Z Command Sync]]
[[Journal 20260602T004840Z Graph Summary]]
[[Journal 20260602T004840Z Sync]]
[[Journal 20260602T004841Z Conversation]]
[[Journal 20260602T004841Z Report]]
[[Journal 20260602T004841Z Report Oc2 20260602004841]]
[[Journal 20260602T005953Z Command Report]]
[[Journal 20260602T005953Z Command Spawn]]
[[Journal 20260602T005953Z Command Status]]
[[Journal 20260602T005953Z Command Task]]
[[Journal 20260602T005953Z Orchestrated Spawn]]
[[Journal 20260602T005953Z Spawn Research]]
[[Journal 20260602T005953Z Task Create]]
[[Journal 20260602T005953Z Task Update]]
[[Keyerror Data Validation 20260531 0245]]
[[Live Deployment Status]]
[[Master Plan Assessment 20260531]]
[[Module Guide Summary]]
[[O2C Pipeline]]
[[Observer Core O1 O7]]
[[Obsidian Vault Connection Info]]
[[Oc2 Gateway Failures]]
[[Oc2 Identity]]
[[Oc2 Vault Access Guide]]
[[Ontology Core Summary]]
[[Operational State 20260531]]
[[Option A Confirmed 20260531]]
[[Pm2 Test Note]]
[[Progress]]
[[Quantlab Bible]]
[[Sage Audit 20260531 Environment Utilization]]
[[Sage Audit 20260531 Environment Utilization V2]]
[[Sage Audit Environment Utilization]]
[[Self Heal Report]]
[[Session 20260531 2200]]
[[Session Testagent 20260531 0245]]
[[Session Testagent 20260531 0245 Full]]
[[Srra Oph]]
[[Task Flow]]
[[Team Phase01 Status]]
[[Team Roster]]
[[Test Note]]
[[Test Pattern]]
[[Track A Build Complete 20260531]]
[[Track A Build Status]]
[[Track A Ninjascript Build 20260531]]
[[Tradovate Api Discovery 20260531]]
[[Vault Distillation 20260531 0245]]
[[Welcome]]
[[Bug Report]]
[[Cal]]
[[Funnel]]
[[Python Api]]
[[Asset Configs]]
[[Symmetry Trap]]
[[Memory]]
[[Symmetry Trap Engine]]
[[Loader]]
