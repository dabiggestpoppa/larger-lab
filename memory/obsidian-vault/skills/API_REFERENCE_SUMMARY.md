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
