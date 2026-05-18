# Quant Lab — Skill Assignment Plan

> **Created:** 2026-05-17 | **Author:** FARM Agent | **Version:** 1.0
> **Purpose:** Map available skills to each agent with justification and priority.

---

## 🔧 Optimizer (The Builder)

**Core Mission:** Run backtests, tweak parameters, find what works. Fast iteration on strategy code.

| Priority | Skill | Justification |
|----------|-------|---------------|
| 1 (CRITICAL) | `quant-analyst` | Core quantitative analysis — expectancy, profit factor, drawdown calculations. The Optimizer's bread and butter. |
| 2 (CRITICAL) | `vectorbt-expert` | VectorBT backtesting expertise — the primary backtest engine used in the lab. Essential for running and interpreting backtests. |
| 3 (HIGH) | `pandas-pro` | Data manipulation for pre/post-processing backtest results, filtering trades, computing metrics. |
| 4 (HIGH) | `agency-testing-test-results-analyzer` | Structured result analysis — parse JSON results, compare across runs, identify regressions. |
| 5 (HIGH) | `agency-engineering-rapid-prototyper` | Fast iteration on strategy variants. The Optimizer needs to test many parameter combinations quickly. |
| 6 (MEDIUM) | `agency-engineering-minimal-change-engineer` | Surgical fixes to strategy code — change one parameter at a time, avoid unintended side effects. |
| 7 (MEDIUM) | `agency-testing-performance-benchmarker` | Benchmark backtest runtime, optimize data loading, ensure tests complete in reasonable time. |
| 8 (LOW) | `agency-engineering-data-engineer` | Data pipeline patterns — useful for understanding data loader and preprocessing. |
| 9 (LOW) | `quantitative-research` | Research methods for designing experiments and parameter sweeps. |

**Skill Load Order:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

---

## 🔬 Researcher (The Explorer)

**Core Mission:** Dig into findings, research patterns, explore new strategy ideas. Deep analysis and pattern discovery.

| Priority | Skill | Justification |
|----------|-------|---------------|
| 1 (CRITICAL) | `senior-data-scientist` | Advanced analytics — the Researcher needs to go beyond surface-level stats into regime detection, correlation analysis, and feature engineering. |
| 2 (CRITICAL) | `statistical-analysis` | Rigorous stats — t-tests, confidence intervals, distribution analysis. Critical for validating whether results are statistically significant. |
| 3 (HIGH) | `variance-analysis` | Variance decomposition — understand what drives strategy performance (time of day, volatility regime, day of week). |
| 4 (HIGH) | `scikit-learn` | ML toolkit — clustering trade outcomes, regime classification, feature importance for strategy selection. |
| 5 (HIGH) | `agency-engineering-ai-engineer` | AI/ML patterns — useful for exploring ML-enhanced strategy signals and automated pattern recognition. |
| 6 (MEDIUM) | `agency-engineering-ai-data-remediation-engineer` | Data quality — ensure the data feeding strategies is clean, no gaps, no outliers corrupting results. |
| 7 (MEDIUM) | `quantitative-research` | Research methodology — structured approach to investigating strategy behavior. |
| 8 (LOW) | `pandas-pro` | Data manipulation for analysis (shared with Optimizer but loaded later). |

**Skill Load Order:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

---

## 📊 Manager (The Decider)

**Core Mission:** Watch progress, decide go/no-go, deploy Poly-Agent when stuck. Project oversight and coordination.

| Priority | Skill | Justification |
|----------|-------|---------------|
| 1 (CRITICAL) | `subagent-manager` | Subagent management — the Manager's core function is coordinating Optimizer and Researcher, deploying Poly-Agent when needed. |
| 2 (CRITICAL) | `agent-team-workflow` | Team coordination — manage the flow between Optimizer → Researcher → Manager, ensure no agent is blocked. |
| 3 (HIGH) | `agent-harness-sop` | Tool building SOP — the Manager may need to create or modify tools for the team. |
| 4 (HIGH) | `agency-engineering-rapid-prototyper` | Fast prototyping — the Manager needs to quickly test coordination workflows and decision frameworks. |
| 5 (MEDIUM) | `agency-testing-test-results-analyzer` | Result analysis — the Manager must read and interpret backtest results to make go/no-go decisions. |
| 6 (MEDIUM) | `agency-engineering-minimal-change-engineer` | Surgical changes — when adjusting team workflows or protocols, make minimal changes. |
| 7 (LOW) | `quant-analyst` | Quantitative literacy — the Manager needs to understand metrics to make informed decisions. |

**Skill Load Order:** 1 → 2 → 3 → 4 → 5 → 6 → 7

---

## Skill Sharing Matrix

| Skill | Optimizer | Researcher | Manager |
|-------|:---------:|:----------:|:-------:|
| quant-analyst | ✅ (1) | — | ✅ (7) |
| vectorbt-expert | ✅ (2) | — | — |
| pandas-pro | ✅ (3) | ✅ (8) | — |
| test-results-analyzer | ✅ (4) | — | ✅ (5) |
| rapid-prototyper | ✅ (5) | — | ✅ (4) |
| minimal-change-engineer | ✅ (6) | — | ✅ (6) |
| performance-benchmarker | ✅ (7) | — | — |
| data-engineer | ✅ (8) | — | — |
| quantitative-research | ✅ (9) | ✅ (7) | — |
| senior-data-scientist | — | ✅ (1) | — |
| statistical-analysis | — | ✅ (2) | — |
| variance-analysis | — | ✅ (3) | — |
| scikit-learn | — | ✅ (4) | — |
| ai-engineer | — | ✅ (5) | — |
| ai-data-remediation | — | ✅ (6) | — |
| subagent-manager | — | — | ✅ (1) |
| agent-team-workflow | — | — | ✅ (2) |
| agent-harness-sop | — | — | ✅ (3) |

---

## Notes

- **Total unique skills assigned:** 18 (out of ~25 relevant skills available)
- **Skills NOT assigned** (reserved for future use): `agency-engineering-code-reviewer`, `agency-engineering-security-engineer`, `agency-engineering-technical-writer` — these are useful but not critical for the current phase
- **Priority system:** CRITICAL = must load first; HIGH = load in second batch; MEDIUM = load as needed; LOW = nice to have
- Skills are assigned based on the **current phase** (V1 — fixing and optimizing existing strategies). As the lab progresses to V2 (new strategy discovery) and V3 (portfolio construction), skill assignments should be revisited.
