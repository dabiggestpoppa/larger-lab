---
name: twitter-research
description: >
  Autonomous Twitter/X research agent. Searches for AI updates, tools, tips,
  and trending research — feeds findings into workspace knowledge base.
  Use when the user wants to discover latest AI developments, find new tools,
  or monitor research trends.
version: 1.0.0
author: agent
platforms: [linux, macos, windows]
---

# Twitter AI Research Agent

## Overview

This agent autonomously searches Twitter/X for AI-related content, classifies
insights by type (tool, tip, research, announcement, trend), and persists
findings to the workspace for other agents to consume.

It operates as an **observer patch** in the SRRS+OPH cognitive architecture —
contributing external signal data to the shared overlap channel.

## Prerequisites

1. **Twitter API Bearer Token**
   - Get one at: https://developer.twitter.com/en/portal/dashboard
   - Set as environment variable: `TWITTER_BEARER_TOKEN`
   - Required for all Twitter API calls

2. **Python dependencies**
   ```
   pip install tweepy
   ```

## Commands

### `/twitter-research`
Run a full AI-focused Twitter search and store findings.

```
/twitter-research
```

Optional parameters:
```
/twitter-research --keywords "AI agent,LLM,RAG" --hours 48 --max 200
```

### `/twitter-research <keywords>`
Search for specific topics:
```
/twitter-research retrieval augmented generation
/twitter-research AI agents frameworks
/twitter-research MCP model context protocol
```

### `/twitter-research --extract-tools`
Run search AND extract tool/repo mentions from results:
```
/twitter-research --extract-tools
```

### `/twitter-top`
Show top insights from existing knowledge base (no API call):
```
/twitter-top
/twitter-top --min-score 5.0
```

### `/twitter-search <query>`
Search already-collected knowledge:
```
/twitter-search vector database
/twitter-search LangChain
```

## Output Files

| File | Purpose |
|------|---------|
| `workspace/twitter-knowledge.json` | Full knowledge base (last 2000 entries) |
| `workspace/recent-discoveries.md` | Human-readable markdown log |
| `shared/overlap-log.jsonl` | OPH overlap channel entries |
| `workspace/seen-tweets.json` | Deduplication cache |

## Architecture Role

```
Twitter API → TwitterResearchAgent → ┬─ Knowledge DB (local patch)
                                      ├─ Discoveries log (human review)
                                      └─ Overlap channel (OPH shared state)
                                            ↓
                                   Other agents read overlap
                                   for cross-patch reconciliation
```

## Scheduling

For continuous research, schedule via Hermes cron:
```
/goal every 6 hours, run /twitter-research and report top 5 findings to me
```

## OPH Integration

Each discovery is written to `shared/overlap-log.jsonl` with:
- `observer_patch`: "twitter-research"
- `overlap_hash`: content-addressable SHA256 for deduplication
- `data`: full insight record

Other agent patches can read this channel to reconcile with their
own observations (e.g., GitHub discoveries about the same tool).