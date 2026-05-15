---
name: github-discovery
description: >
  Autonomous GitHub discovery agent. Searches for repos, tools, and code
  relevant to current goals. Finds niche/lesser-known projects alongside
  popular ones. Use when looking for tools, libraries, or implementations
  of any concept.
version: 1.0.0
author: agent
platforms: [linux, macos, windows]
---

# GitHub Discovery Agent

## Overview

This agent autonomously searches GitHub for repositories related to any
concept or technology. It uses multiple search strategies to find both
popular and niche projects, scores them for relevance, and persists
discoveries to the workspace.

It operates as an **observer patch** in the SRRS+OPH cognitive architecture —
contributing tool/code discovery data to the shared overlap channel.

## Prerequisites

1. **GitHub Personal Access Token**
   - Create at: https://github.com/settings/tokens
   - Scopes needed: `repo` (read), `public_repo` (read)
   - Set as environment variable: `GITHUB_TOKEN`

2. **Python dependencies**
   ```
   pip install requests
   ```

## Commands

### `/github-discover <concept>`
Search GitHub for repos related to a concept:
```
/github-discover machine learning
/github-discover RAG retrieval augmented generation
/github-discover MCP model context protocol
/github-discover autonomous agent framework
```

### `/github-discover <concept> --niche`
Find lesser-known but valuable repos (lower star count, recent, focused):
```
/github-discover vector database --niche
/github-discover LLM fine-tuning --niche
```

### `/github-known <query>`
Search already-discovered repos (no API call):
```
/github-known vector
/github-known RAG
/github-known trading
```

### `/github-stats`
Show agent statistics:
```
/github-stats
```
Returns: total known repos, last update time, discoveries log status.

### `/github-top <concept>`
Show top discoveries for a concept from known repos:
```
/github-top Python frameworks
/github-top trading libraries
```

## Output Files

| File | Purpose |
|------|---------|
| `workspace/known-repos.json` | Full repo knowledge base (last 1000 entries) |
| `workspace/github-discoveries.md` | Human-readable markdown log |
| `shared/overlap-log.jsonl` | OPH overlap channel entries |

## Scoring Algorithm

Repos are scored on multiple signals:
- **Recency** — recently updated repos get higher scores
- **Description match** — keyword match in description boosts score
- **License** — licensed repos indicate serious projects (+10)
- **Stars** — popularity signal (capped to avoid bias toward mega-repos)
- **Stars/Forks ratio** — quality vs. popularity balance
- **Topic match** — GitHub topic tags matching the concept
- **README present** — indicates documentation effort (+5)

## Search Strategies

The agent uses multiple search queries per concept to maximize coverage:
1. `{concept} in:name,description stars:10..500` — focused repos
2. `{concept} language:python language:javascript` — implementation repos
3. `{concept} topic:machine-learning` — topic-tagged repos
4. `awesome {concept}` — curated lists
5. `{concept} tutorial example implementation` — learning resources
6. `{concept} library framework tool` — tool-focused
7. `{concept} alternative lightweight` — niche alternatives
8. `{concept} stars:5..50 pushed:>2024-01-01` — fresh niche projects

## Scheduling

For daily discovery, schedule via Hermes cron:
```
/goal every day at 8 AM UTC, run /github-discover for current project topics and report top 10 findings
```

## OPH Integration

Each discovery is written to `shared/overlap-log.jsonl` with:
- `observer_patch`: "github-discovery"
- `overlap_hash`: content-addressable SHA256 for deduplication
- `data`: full repo insight record

Cross-patch reconciliation: If the Twitter agent discovers a tool and
the GitHub agent finds its repo, the overlap hash enables correlation
across patches without centralized state.