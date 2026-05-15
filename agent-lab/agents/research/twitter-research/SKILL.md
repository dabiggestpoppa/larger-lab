---
name: twitter-bookmarks
description: >
  Access and organize Twitter/X bookmarks. Use when the user wants Hermes to
  read saved bookmarks, organize posts by topic, extract links, or summarize
  saved content. No API needed — uses browser automation or manual paste.
version: 2.0.0
author: agent
platforms: [linux, macos, windows]
---

# Twitter Bookmarks Agent

## Overview

Simple workflow for Hermes/OpenClaw to access your Twitter bookmarks and
organize the content into the workspace. **No Twitter API needed.**

The agent reads what YOU saved, organizes it, and the team can build on it.

## Workflow

### Step 1: You Save Bookmarks
Save posts to Twitter bookmarks as you normally would.

### Step 2: Agent Accesses Bookmarks

**Option A — Browser Automation (preferred):**
1. Open Twitter bookmarks page (https://twitter.com/i/bookmarks)
2. Scroll through saved posts
3. Extract: text, links, author, date
4. Save structured data to workspace

**Option B — Manual Paste (fallback):**
1. Open Twitter bookmarks in your browser
2. Copy/paste the content into chat with Hermes
3. Agent organizes and saves to workspace

### Step 3: Agent Organizes Content
- Parse each bookmark (text, links, author, timestamp)
- Classify by topic (AI, trading, tools, research, etc.)
- Extract links and summarize content
- Save to `workspace/twitter-bookmarks/`
- Update knowledge base with findings

## Commands

### `/bookmarks`
Process all Twitter bookmarks and organize into workspace.
```
/bookmarks
```

### `/bookmarks --topic <topic>`
Filter bookmarks by topic:
```
/bookmarks --topic AI
/bookmarks --topic trading
/bookmarks --topic tools
```

### `/bookmarks --summarize`
Process bookmarks and produce a summary report:
```
/bookmarks --summarize
```

### `/bookmarks --links`
Extract all links from bookmarks, organized by domain:
```
/bookmarks --links
```

### `/bookmarks --since <date>`
Only process bookmarks saved after a date:
```
/bookmarks --since 2026-05-01
```

### `/bookmarks add <url>`
Manually add a URL to the collection:
```
/bookmarks add https://twitter.com/user/status/12345
```

## Output Structure

```
workspace/twitter-bookmarks/
├── index.md              # Master index of all bookmarks
├── by-topic/
│   ├── ai.md             # AI-related bookmarks
│   ├── trading.md        # Trading-related bookmarks
│   ├── tools.md          # Tool/library bookmarks
│   └── other.md          # Uncategorized
├── by-date/
│   ├── 2026-05.md        # Monthly archives
│   └── 2026-04.md
└── links.md              # All extracted links by domain
```

## Topic Classification

| Topic | Keywords |
|-------|----------|
| AI | AI, LLM, GPT, machine learning, neural, agent, model |
| Trading | forex, trading, pips, strategy, backtest, market |
| Tools | tool, library, framework, github, app, extension |
| Research | paper, study, arxiv, research, findings |
| News | announced, launch, release, update, breaking |

## Team Integration

Once bookmarks are organized, the team can:

1. **GitHub Agent** — Find repos/tools mentioned in bookmarks
2. **Research Agent** — Deep-dive into linked articles
3. **Memory Engineer** — Extract key insights into MEMORY.md
4. **Code Reviewer** — Evaluate tools/libraries found
5. **Strategy Team** — Apply trading insights to CEREBUS strategies

## Future Enhancements (Team Builds Over Time)

- [ ] Automatic bookmark monitoring (check for new saves)
- [ ] Deep link analysis (read full articles, not just tweets)
- [ ] Cross-reference with GitHub discoveries
- [ ] Auto-generate skills from tool bookmarks
- [ ] Trading signal extraction from bookmarked analysis
- [ ] Weekly bookmark digest via Telegram

## OPH Integration

Bookmarks are written to `shared/overlap-log.jsonl` as observer patch data,
enabling cross-patch reconciliation with GitHub discoveries and other agents.