# Api Reference Summary

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

# API Reference — OCE Backend Endpoints

TYPE: architecture
SUMMARY: Summary of all OCE FastAPI backend endpoints across all phases.
CAUSE: Frontend and agent code needs to know available API endpoints.
FUNCTION: Quick API lookup reference.

## Base URL
`http://localhost:8000`

## Chat & Continuity
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /chat | Continuity chat (preserves goals, trajectories, observer state) |
| GET | /health | Health check |

## Observers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /observers | List all observers |
| POST | /observers | Create observer |
| GET | /observers/{id} | Get observer details |
| PUT | /observers/{id} | Update observer |
| DELETE | /observers/{id} | Delete observer |
| GET | /observers/{id}/health | Observer health |

## Events
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /events | Query events (filter by type, source, priority) |
| POST | /events/ingest | Ingest new event |
| GET | /events/types | List event types |
| GET | /events/stats | Event statistics |

## Attractor & Memory
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /attractor | Current attractor state |
| POST | /memory/store | Store memory entry |
| POST | /memory/search | Search memory |
| GET | /memory/timeline | Memory timeline |
| GET | /memory/stats | Memory statistics |

## Vault (Phase 00 + 01)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/vault/notes | List notes |
| GET | /api/vault/notes/{cat}/{title} | Read note |
| POST | /api/vault/write | Write note |
| POST | /api/vault/compress | Compress trace |
| POST | /api/vault/validate | Validate note |
| GET | /api/vault/graph | Knowledge graph |
| GET | /api/vault/search | Search notes |
| GET | /api/vault/categories | List categories |
| GET | /api/vault/stats | Vault statistics |
| POST | /api/vault/sync | Sync to Obsidian |
| GET | /api/vault/sync/status | Sync status |
| GET | /api/vault/errors | Error intelligence |
| POST | /api/vault/errors/index | Index error |
| GET | /api/vault/patterns | Get patterns |
| POST | /api/vault/crystallize | Crystallize pattern |
| POST | /api/vault/distill | Distill session |
| POST | /api/vault/distill/vault | Distill from vault |
| GET | /api/vault/context | Context injection |
| GET | /api/vault/summary | Vault summary |

## Execution & Governance
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /execution/tasks | Submit execution task |
| GET | /execution/tasks/{id} | Task status |
| GET | /governance/proposals | List proposals |
| POST | /governance/proposals | Submit proposal |
| GET | /consensus/status | Consensus status |
| POST | /spawn | Spawn agent |

## WebSocket
| Endpoint | Description |
|--------|-------------|
| /ws/events | Real-time event stream |
| /ws/observers | Observer status stream |

RELATIONSHIPS: [[O2C Pipeline]] [[System Architecture]] [[Module Guide]]

STATUS: active
SOURCE: docs/API_REFERENCE.md

LINKS:
[[Error Intelligence]]
[[Vault]]
[[Observer State]]
[[Memory]]
[[System]]
[[Server]]
[[Rest Api]]
[[Python Api]]
[[Patterns]]
[[Modules]]
[[Github Api Cheatsheet]]
[[Description]]
[[Core Api]]
[[Cal]]
[[Api Evaluation]]
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
[[Obsidian Vault Connection Info]]
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
[[Operator Rules]]
[[Api Reference]]
[[V3 Cognitive Field]]
[[Architecture]]
[[OC2 (OWL) — Unified Field Operator]]
[[Team Roster — Agent Network]]
[[System Architecture — Complete Guide]]
[[API Test Note]]
[[Operator Rules — Bounded Sovereign Operational Continuity]]
[[KeyError — data_validation — 20260531_0245]]
[[Agent Topology — Relationship Map]]
[[Task Flow — How Work Moves Through the System]]
[[Session Distillation — TestAgent]]
[[Build Patterns — Successful Operational Patterns]]
[[O2C Pipeline — Cognitive Filesystem & Obsidian Mesh]]
[[Observer Core — O-1 through O-7]]
[[SRRA-OPH — Observer Patch Substrate]]
[[Module Guide — 78 Modules Reference]]
