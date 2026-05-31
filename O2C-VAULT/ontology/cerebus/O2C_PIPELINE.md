# O2C Pipeline — Cognitive Filesystem & Obsidian Mesh

TYPE: architecture
SUMMARY: The O2C (Orchestration Cognition) pipeline that provides persistent operational memory through the Obsidian vault.
CAUSE: O2C is the memory continuity spine of the entire system. Without it, agents reset every session.
FUNCTION: Reference for O2C phases, components, API endpoints, and data flow.

## Architecture

```
Agent Execution → Trace Captured → Insights Distilled → Knowledge Stored →
Future Agents Retrieve → Better Execution → More Knowledge → COMPOUNDING
```

## Phase 00 — Cognitive Filesystem Foundation (COMPLETE)

| Component | File | Purpose | Tests |
|-----------|------|---------|-------|
| Vault Writer | core/obsidian/vault_writer.py | Write structured markdown to vault | 19 |
| Compressor | core/obsidian/compressor.py | Compress traces → operational knowledge | 12 |
| Linker | core/obsidian/linker.py | Auto-link knowledge graph ([[WikiLinks]]) | 10 |
| Taxonomy | core/obsidian/taxonomy.py | Enforce vault folder structure | 8 |
| Note Standard | core/obsidian/note_standard.py | Validate CAUSE/FIX/RESULT/LINKS format | 10 |
| Execution Journal | core/execution/journal.py | Track agent execution steps | 8 |
| Skill Loader | core/skills/loader.py | Load/inject skills at runtime | 8 |
| Live Sync | core/obsidian/live_sync.py | Sync O2C-VAULT → Obsidian vault | — |

**Phase 00 Tests: 84/84 passing**

## Phase 01 — Obsidian Cognitive Mesh (COMPLETE)

| Component | File | Purpose | Tests |
|-----------|------|---------|-------|
| Error Intelligence | core/obsidian/error_intelligence.py | Categorize errors into indexed knowledge | 12 |
| Pattern Crystallizer | core/obsidian/pattern_crystallizer.py | Extract recurring operational structures | 5 |
| Memory Distiller | core/obsidian/memory_distiller.py | Compress sessions into operational doctrine | 4 |
| Context Injector | core/obsidian/context_injector.py | Load relevant vault knowledge before execution | 6 |

**Phase 01 Tests: 27 component + 9 integration = 36 additional (149 total with Phase 00)**

## Vault API Endpoints (19 total)

| Endpoint | Method | Phase | Purpose |
|----------|--------|-------|---------|
| /api/vault/notes | GET | 00 | List vault notes |
| /api/vault/notes/{cat}/{title} | GET | 00 | Read specific note |
| /api/vault/write | POST | 00 | Write new note |
| /api/vault/compress | POST | 00 | Compress trace to note |
| /api/vault/validate | POST | 00 | Validate note format |
| /api/vault/graph | GET | 00 | Get knowledge graph |
| /api/vault/search | GET | 00 | Search notes |
| /api/vault/categories | GET | 00 | List categories |
| /api/vault/stats | GET | 00 | Vault statistics |
| /api/vault/sync | POST | 00 | Sync to Obsidian |
| /api/vault/sync/status | GET | 00 | Sync status |
| /api/vault/errors | GET | 01 | Error intelligence |
| /api/vault/errors/index | POST | 01 | Index error |
| /api/vault/patterns | GET | 01 | Pattern crystallization |
| /api/vault/crystallize | POST | 01 | Crystallize pattern |
| /api/vault/distill | POST | 01 | Distill session |
| /api/vault/distill/vault | POST | 01 | Distill from vault |
| /api/vault/context | GET | 01 | Context injection |
| /api/vault/summary | GET | 01 | Vault summary |

## Two-Vault Architecture

| Vault | Path | Purpose |
|-------|------|---------|
| O2C-VAULT (default) | larger-lab/O2C-VAULT/ | Internal workspace vault, used by OCE API |
| Obsidian Vault (real) | C:\Users\wifik\Downloads\o2c | Actual Obsidian vault, synced via Obsidian app |

## Note Standard

Every note follows CAUSE/FIX/RESULT/LINKS format:
```
# TITLE
TYPE: [architecture | doctrine | observer | quant | execution]
SUMMARY: [compressed operational meaning]
CAUSE: [why this exists]
FUNCTION: [what it does]
RELATIONSHIPS: [[Linked Node]]
FIELD ROLE: [where it exists in topology]
STATUS: [active | deprecated | experimental]
SOURCE: [path/to/original/file]
```

RELATIONSHIPS: [[System Architecture]] [[V3 Cognitive Field]] [[API Reference]]

STATUS: active
SOURCE: oce/O2C_PHASE00_BUILD-NOTES.md, oce/O2C_PHASE01_BUILD-NOTES.md
