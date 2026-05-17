# AgentMemory Skill

## Purpose
Persistent memory engine for AI agents. Auto-captures session context, compresses into searchable memory, injects relevant context at session start. Works across Claude Code, Cursor, OpenClaw, Hermes, and any MCP client.

## When to Use
- Agent forgets context between sessions (re-explaining architecture, re-discovering bugs)
- Need persistent memory that survives session resets
- Multi-agent coordination (shared memory across agents)
- Long-horizon projects where context window is insufficient

## Installation
```bash
npm install -g @agentmemory/agentmemory  # Global install
agentmemory  # Start server on port 3111
```

## Quick Start
```bash
# Terminal 1: Start memory server
agentmemory

# Terminal 2: Seed demo data
agentmemory demo

# Terminal 3: Connect OpenClaw
agentmemory connect openclaw
```

## Integration with OCE

### As OCE Memory Backend
Replace/augment the current SQLite-based `structural_memory.py` with agentmemory:
- agentmemory provides BM25 + Vector + Graph search (RRF fusion)
- Auto-captures via 12 hooks (zero manual effort)
- 95.2% retrieval accuracy (LongMemEval-S benchmark)
- ~170K tokens/year (vs 19.5M+ for full context paste)

### OCE Memory Architecture with agentmemory
```
OCE Backend → agentmemory MCP → SQLite (via iii-engine)
                           → Vector embeddings (all-MiniLM-L6-v2, local)
                           → Knowledge graph (entity relationships)
                           → Real-time viewer (port 3113)
```

### API Endpoints (agentmemory server at :3111)
```bash
# Store memory
curl -X POST http://localhost:3111/memory/store \
  -H "Content-Type: application/json" \
  -d '{"content": "...", "tags": ["observer", "phase3"], "source": "owl"}'

# Search memories
curl "http://localhost:3111/memory/search?q=observer+runtime&limit=10"

# Get timeline
curl http://localhost:3111/memory/timeline/observer-123

# Compress old memories
curl -X POST http://localhost:3111/memory/compress \
  -d '{"layer": "WORK", "max_entries": 1000}'
```

## Benchmarks
| Metric | agentmemory | mem0 | Letta | CLAUDE.md |
|--------|-------------|------|-------|-----------|
| Retrieval R@5 | 95.2% | 68.5% | 83.2% | N/A |
| Tokens/year | 170K | Varies | Varies | 19.5M+ |
| Cost/year | $10 | Varies | Varies | Impossible |
| Auto-capture | 12 hooks | Manual | Self-edit | Manual |
| Multi-agent | Yes | No | Within Letta | Per-agent |

## Memory Lifecycle
1. **Capture** — Hooks auto-capture session events (tool calls, file edits, decisions)
2. **Compress** — LLM summarizes raw events into compact memories
3. **Store** — SQLite + vector embeddings + knowledge graph
4. **Retrieve** — BM25 + Vector + Graph fusion (RRF) at session start
5. **Decay** — Old memories auto-forget based on TTL and access frequency

## Real-Time Viewer
Open http://localhost:3113 to watch memories build live.

## Constraints
- First run downloads embedding model (~100MB)
- Server must be running for memory persistence
- All agents share same memory server (coordinated via MCP)
- Self-hosted by default (no cloud dependency)
