# Oc2 Vault Access Guide

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

---
title: OC2 Vault Access Guide
date: 2026-05-31
author: OC2/OWL
tags: [vault, obsidian, access, guide, team, subagent]
---

# OC2 Vault Access Guide

> All subagents and team members can write directly to the Obsidian vault.
> No need to route through OWL.

## Two Vault Locations

| Vault | Path | Purpose |
|-------|------|---------|
| **Real Obsidian** | `C:\Users\wifik\Downloads\o2c` | Obsidian app watches this |
| **Default (workspace)** | `O2C-VAULT/` | Internal workspace vault |

## How to Write (Python - from OCE context)

```python
from core.obsidian.vault_writer import VaultWriter
vw = VaultWriter(vault_path='C:/Users/wifik/Downloads/o2c')
vw.write_note(category='execution', title='Agent Report',
    content={'cause':'...','fix':'...','result':'...'},
    tags=['agent','report'])
```

## How to Write (Direct file write - from any context)

```python
import os
from pathlib import Path

VAULT = Path('C:/Users/wifik/Downloads/o2c')

def write_note(category, title, content_text, tags=None):
    folder = VAULT / category
    folder.mkdir(parents=True, exist_ok=True)
    filepath = folder / f"{title}.md"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content_text)
    return str(filepath)
```

## How to Write (REST API)

```
# Real Obsidian vault
POST /api/vault/write?vault=obsidian
# Default workspace vault  
POST /api/vault/write
```

## Available Categories

agents, architecture, doctrine, execution, failures, graphs,
heuristics, journals, memory, ontology, routing, skills

## Subagent Spawn Template

When spawning subagents, include this in their task brief:

```
OBSIDIAN_VAULT = 'C:/Users/wifik/Downloads/o2c'
from pathlib import Path
VAULT = Path(OBSIDIAN_VAULT)

def write_note(category, title, content_text):
    folder = VAULT / category
    folder.mkdir(parents=True, exist_ok=True)
    filepath = folder / f"{title}.md"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content_text)
    return str(filepath)
```

## Vault Structure

```
o2c/
├── agents/          - Agent-specific notes and meditations
├── architecture/    - System architecture docs
├── doctrine/        - Operational doctrine and principles
├── execution/       - Execution logs and reports
├── failures/        - Failure index and error analysis
├── graphs/          - Relationship graphs
├── heuristics/      - Heuristic rules and patterns
├── journals/        - Daily/backtest/forward-test logs
├── memory/          - Memory chains and continuity
├── ontology/        - Strategy ontology
├── routing/         - Routing logic and capital flow
└── skills/          - Skill definitions and documentation
```

LINKS:
[[Architecture]]
[[System Architecture]]
[[V3 Cognitive Field]]
[[Agents]]
[[Module Guide]]
[[Operator Rules]]
[[Principles]]
[[User]]
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
[[Ontology Core Summary]]
[[Operational State 20260531]]
[[Option A Confirmed 20260531]]
[[Pm2 Test Note]]
[[Progress]]
[[Python Vs Nautilus Tradecount Investigation 20260601]]
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
[[Benchmark Guide]]
[[Failures]]
[[Heuristics]]
[[Methods Guide]]
[[Ohmsha Guide]]
[[Patterns]]
[[Rest Api]]
[[Skill]]
[[System]]
[[Writing Guide]]
[[Memory]]
[[Journal]]
[[Vault]]
[[Test Vault Writer]]
[[Vault Writer]]
