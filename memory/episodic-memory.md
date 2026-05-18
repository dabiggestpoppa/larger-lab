---
created: 2026-05-17
updated: 2026-05-17
tags: [memory, episodic, events, history]
importance: 5
---

# Episodic Memory

> Past events, decisions, outcomes. Chronological log of significant moments.

## 2026-05-17

### CLI-Hub Installation & Bug Fix
- Installed `cli-anything-hub` via pip
- Discovered Python 3.11 incompatibility: f-string with backslash in `preview.py`
- Fixed by extracting the string literal to a variable before the f-string
- `cli-hub list` now works, showing 76 CLIs across 30 categories
- Most relevant CLIs found: `hacker-feeds-cli`, `chromadb`, `ollama`, `obsidian`, `obsidian-cli`

### MAD Directive: OWL as Orchestrator
- MAD confirmed OWL should be an orchestrator, not execution worker
- All Lab/Farm work goes through Manager → Optimizer/Researcher pipeline
- Max 2 concurrent sub-agents enforced

### Memory Architecture Decision
- MAD requested structured memory system (PAI-inspired)
- Decided on 5-file split: working, episodic, semantic, procedural, identity
- Each file gets YAML frontmatter with created/updated/tags/importance
- Memory index.md links everything together

## 2026-05-16

### Tool Installation Wave
- Installed: CloakBrowser, AgentMemory (npm), TradingView MCP, TensorTrade, Supertonic TTS, LLM Wiki
- Created agent hooks at `tools/agent-hooks/`
- Set up LLM Wiki at `projects/llm_wiki/`

### Skills Audit
- 57 active skills in `skills/`
- 51 agent-specific skills in `.agents/skills/`
- 67 archived dead skills in `archive/skills/`

## Pre-2026-05-16 (Compressed)

- SRRA-OPH: 9 phases, 77/77 tests — complete
- OCE: 9 phases, 426 tests — complete
- V3 P1 RSS: complete
- V3 P2-P9: pending
