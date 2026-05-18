# 📊 Manager — Skill Manifest

> **Agent:** Manager (Decider) | **Version:** 1.0 | **Created:** 2026-05-17

---

## Active Skills

| # | Skill | Priority | Status |
|---|-------|----------|--------|
| 1 | `subagent-manager` | CRITICAL | ⏳ Pending load |
| 2 | `agent-team-workflow` | CRITICAL | ⏳ Pending load |
| 3 | `agent-harness-sop` | HIGH | ⏳ Pending load |
| 4 | `agency-engineering-rapid-prototyper` | HIGH | ⏳ Pending load |
| 5 | `agency-testing-test-results-analyzer` | MEDIUM | ⏳ Pending load |
| 6 | `agency-engineering-minimal-change-engineer` | MEDIUM | ⏳ Pending load |
| 7 | `quant-analyst` | LOW | ⏳ Pending load |

---

## Skill Justifications

### 1. `subagent-manager` (CRITICAL)
The Manager's core function. Must know how to spawn, monitor, and recall sub-agents (Poly-Agent deployments). Includes timeout management, success criteria definition, and structured output parsing.

### 2. `agent-team-workflow` (CRITICAL)
Team coordination patterns. The Manager orchestrates the Optimizer → Researcher → Manager flow. This skill provides the communication and coordination framework.

### 3. `agent-harness-sop` (HIGH)
Tool building SOP. The Manager may need to create or modify coordination tools, status trackers, or decision frameworks for the team.

### 4. `agency-engineering-rapid-prototyper` (HIGH)
Fast prototyping. The Manager needs to quickly test new coordination workflows, decision frameworks, and team structures.

### 5. `agency-testing-test-results-analyzer` (MEDIUM)
Result analysis. The Manager must read and interpret backtest JSON results to make informed go/no-go decisions.

### 6. `agency-engineering-minimal-change-engineer` (MEDIUM)
Surgical changes. When adjusting team protocols or workflows, make minimal changes to avoid disrupting active work.

### 7. `quant-analyst` (LOW)
Quantitative literacy. The Manager needs to understand metrics (expectancy, profit factor, drawdown) to make informed decisions. Lower priority because the Manager interprets rather than computes.

---

## Load Order

Load skills in priority order: 1 → 2 → 3 → 4 → 5 → 6 → 7

CRITICAL skills must be loaded before the Manager begins operation.
HIGH skills should be loaded within the first work cycle.
MEDIUM and LOW skills can be loaded as needed.

---

## Skills NOT Assigned (And Why)

| Skill | Reason |
|-------|--------|
| `vectorbt-expert` | Optimizer's domain — Manager interprets results, doesn't run backtests |
| `pandas-pro` | Optimizer/Researcher domain — Manager reads summaries, doesn't process raw data |
| `senior-data-scientist` | Researcher's domain — Manager doesn't do deep analytics |
| `scikit-learn` | Researcher's domain — Manager doesn't build ML models |
| `statistical-analysis` | Researcher's domain — Manager interprets stats, doesn't compute them |
