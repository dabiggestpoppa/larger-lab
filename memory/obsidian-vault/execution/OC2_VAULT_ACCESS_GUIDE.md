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
