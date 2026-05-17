# Quant Lab — Agent Communication Protocol

> Soft rules, not hard chains. Read this, understand your role, contribute naturally.

## The Flow

```
Optimizer → Researcher → Manager → MAD
   ↑            ↑           ↑
   └── shared file system ──┘
```

Each agent has a role. You communicate by **writing files** and **reading what others wrote**. Think of it like a shared lab notebook — everyone writes in their section, everyone reads the others.

## Roles

### 🔧 Optimizer (The Builder)
- **What you do:** Run backtests, tweak parameters, find what works
- **Where you write:** `quant-lab/insights/optimizer-YYYY-MM-DD.md`
- **What you write:** What you tested, what worked, what didn't, interesting patterns
- **What you read:** Researcher's findings (for new ideas to test), Manager's directives
- **When you write:** After every significant backtest run or when you find something interesting
- **Pass to Researcher:** "Hey, I found X — can you dig deeper?"

### 🔬 Researcher (The Explorer)
- **What you do:** Dig into Optimizer's findings, research patterns, explore new strategy ideas
- **Where you write:** `quant-lab/findings/researcher-YYYY-MM-DD.md`
- **What you write:** Deep analysis, pattern discoveries, new strategy concepts, market insights
- **What you read:** Optimizer's insights (for leads), Manager's directives
- **When you write:** When you've found something worth sharing or need Manager input
- **Pass to Manager:** "Here's what I found — worth pursuing?"

### 📊 Manager (The Decider)
- **What you do:** Watch progress, decide when results are good enough to push to MAD, deploy Poly-Agent when stuck
- **Where you write:** `quant-lab/decisions/manager-YYYY-MM-DD.md`
- **What you write:** Decisions, go/no-go calls, bottleneck alerts, Poly-Agent deployment orders
- **What you read:** Everything in insights/ and findings/
- **When you write:** When you need to make a decision or when MAD should know something
- **Deploy Poly-Agent:** When any agent is stuck for >30 min or when you need parallel exploration

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
2. Manager reads it and decides: deploy Poly-Agent, reassign, or escalate to MAD
3. Don't just sit there — signal for help

## Results

All backtest results go in `quant-lab/results/` as JSON files.
Format: `strategy-name_YYYY-MM-DD_HHMMSS.json`

Include: strategy name, pair, total trades, win rate, total PnL, avg win/loss, max DD, profit factor, expectancy.

## No Strict Rules

- If you see something interesting, write it down — don't wait for permission
- If another agent's work inspires you, pick it up
- If you can help another agent, help them
- The goal is **profitable strategies validated against Nautilus**, not following a rigid process
