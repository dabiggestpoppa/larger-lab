# 🦉 OWL Monitoring Dashboard — Quant Lab

> **Created:** 2026-05-17 | **Author:** FARM Agent | **Audience:** OWL (Overseer)
> **Purpose:** Define what OWL should monitor, key metrics, alert thresholds, and file locations.

---

## What OWL Should Monitor

OWL is the overseer of the Quant Lab. You don't run backtests or write code. You **watch, detect, and alert**.

---

## Key Metrics to Track

### 1. Strategy Performance Metrics
| Metric | Location | Frequency | Alert Threshold |
|--------|----------|-----------|-----------------|
| Win Rate | `quant-lab/results/*.json` | Every new result | < 30% or > 95% (suspicious) |
| Profit Factor | `quant-lab/results/*.json` | Every new result | < 0.9 (losing) |
| Expectancy | `quant-lab/results/*.json` | Every new result | < 0 (negative) |
| Max Drawdown | `quant-lab/results/*.json` | Every new result | > 12% (Goal 3 breach) |
| Total Trades | `quant-lab/results/*.json` | Every new result | < 50 (insufficient sample) |

### 2. Agent Activity Metrics
| Metric | Location | Frequency | Alert Threshold |
|--------|----------|-----------|-----------------|
| Optimizer last write | `quant-lab/insights/optimizer-*.md` | Every 30 min | >60 min stale |
| Researcher last write | `quant-lab/findings/researcher-*.md` | Every 30 min | >60 min stale |
| Manager last write | `quant-lab/decisions/manager-*.md` | Every 30 min | >90 min stale |
| BLOCKED files | `quant-lab/agents/*/BLOCKED.md` | Every 15 min | Any file exists |

### 3. Goal Progress Metrics
| Goal | Location | Frequency | Alert Threshold |
|------|----------|-----------|-----------------|
| Goal 1: All backtested | `quant-lab/STATUS.md` | Daily | < 14/14 after 1 week |
| Goal 2: 80% profitable | `quant-lab/STATUS.md` | Daily | < 50% after fixes |
| Goal 3: MaxDD < 12% | `quant-lab/results/*.json` | Every new result | Any profitable strategy > 15% |
| Goal 4: 80% WR + 2/day | `quant-lab/STATUS.md` | Daily | No strategy meeting both |
| Goal 5: USD/CHF backtest | `quant-lab/STATUS.md` | Weekly | Not started after winners found |
| Goal 6: Basket portfolio | `quant-lab/STATUS.md` | Weekly | Not started after Goal 5 |

---

## Alert Thresholds

### 🔴 CRITICAL (Immediate Action Required)
- Any BLOCKED.md file exists for >15 minutes
- A strategy achieves MAD notification criteria (WR > 50%, PF > 1.3, expectancy > 0, trades > 200)
- Max drawdown exceeds 20% on any strategy
- No agent activity for >2 hours

### 🟡 WARNING (Investigate Within 30 Min)
- Agent stale: No new files from any agent for >60 minutes
- Strategy regression: New backtest shows >20% WR drop from previous
- Profit factor drops below 0.95 on a previously profitable strategy
- Manager hasn't made a decision within 2 hours of new results

### 🟢 INFO (Log, No Action)
- New backtest result file created
- New insight or finding file created
- Manager decision file created
- STATUS.md updated

---

## Status File Locations

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `quant-lab/STATUS.md` | Overall strategy status | After every backtest cycle |
| `quant-lab/GOALS.md` | 6 goals and progress | Rarely (goal completion) |
| `quant-lab/PROTOCOL.md` | Communication protocol | Rarely (protocol changes) |
| `quant-lab/results/*.json` | Backtest results | Every backtest run |
| `quant-lab/insights/optimizer-*.md` | Optimizer output | After significant runs |
| `quant-lab/findings/researcher-*.md` | Researcher output | After analysis |
| `quant-lab/decisions/manager-*.md` | Manager decisions | As needed |
| `quant-lab/decisions/escalation-*.md` | Escalations to OWL | As needed |
| `quant-lab/agents/*/BLOCKED.md` | Blocked signals | When stuck |

---

## Monitoring Schedule

### Every 15 Minutes
- Check for BLOCKED.md files
- Check for escalation files

### Every 30 Minutes
- Check agent activity (last write times)
- Check for new result files

### Every 2 Hours
- Review STATUS.md for goal progress
- Review latest Manager decisions
- Check for MAD notification-worthy results

### Daily
- Full dashboard review
- Goal progress assessment
- Agent productivity summary
- Report to MAD if any CRITICAL alerts

---

## MAD Notification Triggers

Notify MAD immediately when:
1. **A strategy meets all GO criteria** — WR ≥ 50%, PF > 1.0, expectancy > 0, MaxDD ≤ 12%, trades ≥ 100
2. **A strategy meets Goal 4 criteria** — WR ≥ 80%, ~2 trades/day, positive expectancy
3. **All goals are complete** — All 6 goals achieved
4. **Critical blocker** — Lab is completely stuck for >2 hours
5. **Breakthrough** — Unexpected finding that changes the strategic direction

---

## Dashboard Summary Template

Use this template for periodic status reports:

```
🦉 OWL Quant Lab Dashboard — [DATE TIME]

## Agent Status
- Optimizer: [Active/Stale/Blocked] — Last activity: [time]
- Researcher: [Active/Stale/Blocked] — Last activity: [time]
- Manager: [Active/Stale/Blocked] — Last activity: [time]

## Strategy Summary
- Total backtested: X/14
- Profitable: X/14 (X%)
- Meeting Goal 4: [strategy name] (if any)
- Max DD concern: [strategy name] at X%

## Alerts
- 🔴 [Critical alerts]
- 🟡 [Warning alerts]
- 🟢 [Info updates]

## Goal Progress
- Goal 1: [status]
- Goal 2: [status]
- Goal 3: [status]
- Goal 4: [status]
- Goal 5: [status]
- Goal 6: [status]

## MAD Notifications
- [Any strategies meeting notification criteria]
```

---

## File Watch List (Priority Order)

1. `quant-lab/agents/*/BLOCKED.md` — Highest priority
2. `quant-lab/decisions/escalation-*.md` — Escalations need immediate attention
3. `quant-lab/results/*.json` — New results need review
4. `quant-lab/decisions/manager-*.md` — Manager decisions affect direction
5. `quant-lab/insights/optimizer-*.md` — Optimizer progress
6. `quant-lab/findings/researcher-*.md` — Researcher findings
7. `quant-lab/STATUS.md` — Overall status
