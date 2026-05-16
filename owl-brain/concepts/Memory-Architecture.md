# Memory Architecture

> How OWL remembers. 3-tier system + Obsidian vault brain.

## Tier 1: Working Memory (Session Context)
- Current conversation context
- Workspace files loaded at startup (AGENTS.md, SOUL.md, MEMORY.md, etc.)
- Auto-injected by OpenClaw

## Tier 2: Persistent Memory (Workspace Files)
- `MEMORY.md` — Curated long-term memory, hand-managed
- `progress/rl-progress.md` — OWL's sub-progress log
- `owl-brain/` — Obsidian vault (structured, linked, searchable)
- `db/owl_health.db` — Error and health tracking DB

## Tier 3: Vault Brain (Obsidian-Style)
- `owl-brain/daily/` — Daily notes, auto-captured
- `owl-brain/concepts/` — Concept maps with bidirectional links
- `owl-brain/systems/` — System documentation
- `owl-brain/people/` — People profiles
- `owl-brain/projects/` — Project tracking
- `owl-brain/archive/` — Compressed old notes
- `owl-brain/index/MOC.md` — Map of Content (auto-generated)

## Continuous Memory Pipeline
- `tools/memory_pipeline.py` — Auto-captures, extracts concepts, updates vault
- Runs on heartbeat
- Compresses notes older than 7 days into archive summaries
- Regenerates MOC on each run

## Memory Compression Rules
- Daily notes → Archive summaries after 7 days
- Working memory → Persistent memory after each session
- Errors → Bug files → Resolved/Archive
- Linear growth is failure — compress or die

## Related
- [[Self-Healing Framework]] — Keeps memory healthy
- [[SRRA-OPH]] — The architecture this serves
- [[Building Philosophy]] — "Memory must compress"
