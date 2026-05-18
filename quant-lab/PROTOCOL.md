# Quant Lab — Agent Communication Protocol

> **Version:** 2.0 | **Updated:** 2026-05-17 | **Author:** FARM Agent
> Soft rules, not hard chains. Read this, understand your role, contribute naturally.

## The Flow

```
Optimizer → Researcher → Manager → OWL → MAD
   ↑            ↑           ↑
   └── shared file system ──┘
```

Each agent has a role. You communicate by **writing files** and **reading what others wrote**. Think of it like a shared lab notebook — everyone writes in their section, everyone reads the others.

## Roles

### 🔧 Optimizer (The Builder)
- **What you do:** Run backtests, tweak parameters, find what works
- **Config:** `quant-lab/agents/optimizer/OPTIMIZER.md`
- **Where you write:** `quant-lab/insights/optimizer-YYYY-MM-DD.md`
- **What you write:** What you tested, what worked, what didn't, interesting patterns
- **What you read:** Researcher's findings (for new ideas to test), Manager's directives
- **When you write:** After every significant backtest run or when you find something interesting
- **Pass to Researcher:** "Hey, I found X — can you dig deeper?"
- **Skills:** quant-analyst, vectorbt-expert, pandas-pro, test-results-analyzer, rapid-prototyper, minimal-change-engineer, performance-benchmarker

### 🔬 Researcher (The Explorer)
- **What you do:** Dig into Optimizer's findings, research patterns, explore new strategy ideas
- **Config:** `quant-lab/agents/researcher/RESEARCHER.md`
- **Where you write:** `quant-lab/findings/researcher-YYYY-MM-DD.md`
- **What you write:** Deep analysis, pattern discoveries, new strategy concepts, market insights
- **What you read:** Optimizer's insights (for leads), Manager's directives
- **When you write:** When you've found something worth sharing or need Manager input
- **Pass to Manager:** "Here's what I found — worth pursuing?"
- **Skills:** senior-data-scientist, statistical-analysis, variance-analysis, scikit-learn, ai-engineer, ai-data-remediation

### 📊 Manager (The Decider)
- **What you do:** Watch progress, decide when results are good enough to push to MAD, deploy Poly-Agent when stuck
- **Config:** `quant-lab/agents/manager/MANAGER.md`
- **Skills:** `quant-lab/agents/manager/SKILLS.md`
- **Where you write:** `quant-lab/decisions/manager-YYYY-MM-DD.md`
- **What you write:** Decisions, go/no-go calls, bottleneck alerts, Poly-Agent deployment orders
- **What you read:** Everything in insights/ and findings/
- **When you write:** When you need to make a decision or when MAD should know something
- **Deploy Poly-Agent:** When any agent is stuck for >30 min or when you need parallel exploration
- **Escalate to OWL:** When decisions exceed Manager authority or MAD input is needed
- **Skills:** subagent-manager, agent-team-workflow, agent-harness-sop, rapid-prototyper, test-results-analyzer

### 🦉 OWL (The Overseer)
- **What you do:** Monitor the entire lab, detect blockers, alert MAD on breakthroughs
- **Config:** `quant-lab/docs/monitoring-dashboard.md`
- **What you read:** All agent outputs, results, decisions, BLOCKED files
- **When you act:** On a monitoring schedule (every 15-30 min for critical, every 2 hours for full review)
- **Notify MAD:** When strategies meet notification criteria or critical blockers exist

## Skill Assignments

See `quant-lab/docs/skill-assignments.md` for the complete skill assignment plan.

| Agent | Skills Count | Key Skills |
|-------|:------------:|------------|
| Optimizer | 9 | quant-analyst, vectorbt-expert, pandas-pro |
| Researcher | 8 | senior-data-scientist, statistical-analysis, scikit-learn |
| Manager | 7 | subagent-manager, agent-team-workflow, agent-harness-sop |

## File Format (Keep It Simple)

```markdown
# [Role] Update — [DATE]

## Status
[What you're working on right now]

## What I Found
[Key findings, results, patterns]

## What I Need
[What you need from other agents or MAD]

## Next Steps
[What you'll do next]
```

## Bottleneck Rule

If you're stuck for more than 30 minutes:
1. Write a `BLOCKED.md` file in your folder explaining what's blocking you
2. Manager reads it and decides: deploy Poly-Agent, reassign, or escalate to OWL
3. Don't just sit there — signal for help

## Results

All backtest results go in `quant-lab/results/` as JSON files.
Format: `strategy-name_YYYY-MM-DD_HHMMSS.json`

Include: strategy name, pair, timeframe, total trades, wins, losses, win rate, total PnL, avg win/loss, max DD, profit factor, expectancy, by_exit.

## Go/No-Go Criteria

A strategy gets a **GO** when ALL are true:
- Win Rate ≥ 50%
- Profit Factor > 1.0
- Expectancy > 0
- Max Drawdown ≤ 12%
- Sample Size ≥ 100 trades
- No critical bugs

## Manager Decision Authority

The Manager has authority to:
- Assign work to Optimizer and Researcher
- Deploy Poly-Agent (max 2 concurrent)
- Make go/no-go calls on strategies
- Re-prioritize the work queue (within GOALS.md framework)

The Manager must escalate to OWL/MAD when:
- A strategy meets MAD notification criteria
- A bottleneck can't be resolved within 1 hour
- A decision requires MAD's strategic input

## No Strict Rules

- If you see something interesting, write it down — don't wait for permission
- If another agent's work inspires you, pick it up
- If you can help another agent, help them
- The goal is **profitable strategies validated against Nautilus**, not following a rigid process

## V2 Changes (2026-05-17)

1. **Added Manager agent** with full operating instructions and skill manifest
2. **Added OWL monitoring** with dashboard, alert thresholds, and monitoring schedule
3. **Added skill assignments** for all three agents with justifications
4. **Added go/no-go criteria** for standardized strategy evaluation
5. **Added escalation path** from agents → Manager → OWL → MAD
6. **Added Poly-Agent deployment rules** with constraints
7. **Updated file locations** to include new agent config directories
