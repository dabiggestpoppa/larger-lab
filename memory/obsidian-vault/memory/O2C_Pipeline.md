# O2C Pipeline

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

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
| memory/obsidian-vault (default) | larger-lab/memory/obsidian-vault/ | Internal workspace vault, used by OCE API |
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

LINKS:
[[Vault Writer]]
[[Taxonomy]]
[[Pattern Crystallizer]]
[[Note Standard]]
[[Memory Distiller]]
[[Live Sync]]
[[Linker]]
[[Error Intelligence]]
[[Compressor]]
[[Vault]]
[[Loader]]
[[Journal]]
[[Context Injector]]
[[Memory]]
[[System]]
[[Standard]]
[[Skill]]
[[Server]]
[[Patterns]]
[[Modules]]
[[Export Pipeline]]
[[Api Endpoints]]
[[Welcome]]
[[Vault Distillation 20260531 0245]]
[[Tradovate Api Discovery 20260531]]
[[Track A Ninjascript Build 20260531]]
[[Track A Build Status]]
[[Track A Build Complete 20260531]]
[[Test Pattern]]
[[Test Note]]
[[Team Roster]]
[[Team Phase01 Status]]
[[Task Flow]]
[[Srra Oph]]
[[Session Testagent 20260531 0245 Full]]
[[Session Testagent 20260531 0245]]
[[Session 20260531 2200]]
[[Self Heal Report]]
[[Sage Audit Environment Utilization]]
[[Sage Audit 20260531 Environment Utilization V2]]
[[Sage Audit 20260531 Environment Utilization]]
[[Quantlab Bible]]
[[Python Vs Nautilus Tradecount Investigation 20260601]]
[[Progress]]
[[Pm2 Test Note]]
[[Option A Confirmed 20260531]]
[[Operational State 20260531]]
[[Ontology Core Summary]]
[[Oc2 Vault Access Guide]]
[[Oc2 Identity]]
[[Oc2 Gateway Failures]]
[[Observer Core O1 O7]]
[[Module Guide Summary]]
[[Master Plan Assessment 20260531]]
[[Live Deployment Status]]
[[Keyerror Data Validation 20260531 0245]]
[[Journal 20260602T005953Z Task Update]]
[[Journal 20260602T005953Z Task Create]]
[[Journal 20260602T005953Z Spawn Research]]
[[Journal 20260602T005953Z Orchestrated Spawn]]
[[Journal 20260602T005953Z Command Task]]
[[Journal 20260602T005953Z Command Status]]
[[Journal 20260602T005953Z Command Spawn]]
[[Journal 20260602T005953Z Command Report]]
[[Journal 20260602T004841Z Report Oc2 20260602004841]]
[[Journal 20260602T004841Z Report]]
[[Journal 20260602T004841Z Conversation]]
[[Journal 20260602T004840Z Sync]]
[[Journal 20260602T004840Z Graph Summary]]
[[Journal 20260602T004840Z Command Sync]]
[[Journal 20260602T004840Z Command Status]]
[[Journal 20260602T004840Z Command Help]]
[[Journal 20260602T004840Z Command Graph]]
[[Hermes Obsidian Test   Vault Working]]
[[Hermes Agent Test Note]]
[[Hermes Agent Test]]
[[Hermes Agent Activation Note]]
[[Foundational Principles]]
[[Failure Index Oc2]]
[[Executor Crash 20260531]]
[[Errors And Solutions]]
[[Doctor Prescription]]
[[Dashboard Build Complete]]
[[Daily Runtime 20260531]]
[[Cerebus Nt8 Deployment Campaign 20260531]]
[[Cc Phase 01 Build Certification Report]]
[[Build Progress 20260531]]
[[Build Patterns]]
[[Backtest Phase Status]]
[[Backtest Campaign V3 Results]]
[[Backtest Campaign Status 20260531]]
[[Api Test Note]]
[[Api Reference Summary]]
[[Api Execution Architecture 20260531]]
[[Agent Topology]]
[[Active Strategies Performance]]
[[2026 06 01]]
[[2026 05 31]]
[[2026 05 30 Nautilus Fix]]
[[2026 05 30 Evening]]
[[2026 05 30]]
[[2026 05 21]]
[[2026 05 20]]
[[2026 05 18]]
[[2026 05 17]]
[[User]]
[[Operator Rules]]
[[Module Guide]]
[[Api Reference]]
[[Agents]]
[[Architecture]]
[[OC2 (OWL) — Unified Field Operator]]
[[Team Roster — Agent Network]]
[[Obsidian Vault Connection Info]]
[[System Architecture — Complete Guide]]
[[V3 Cognitive Field System]]
[[Operator Rules — Bounded Sovereign Operational Continuity]]
[[KeyError — data_validation — 20260531_0245]]
[[Agent Topology — Relationship Map]]
[[Task Flow — How Work Moves Through the System]]
[[Session Distillation — TestAgent]]
[[Build Patterns — Successful Operational Patterns]]
[[Observer Core — O-1 through O-7]]
[[SRRA-OPH — Observer Patch Substrate]]
[[API Reference — OCE Backend Endpoints]]
[[Module Guide — 78 Modules Reference]]
