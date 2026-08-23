# OCE Hermes Telegram Operator — Architecture

> Version: 0.1.0  
> Status: Phase 0 — Observer Mode  
> Date: 2026-08-23

## Overview

The OCE Hermes Telegram Operator is a **read-only observer interface** that connects NousResearch Hermes Agent to the OCE (Operator Continuity Engine) backend via a filtered MCP facade. Telegram serves as the remote interface. OCE remains the authority.

## System Boundary

```
┌─────────────────────────────────────────────────────────┐
│  Telegram (long polling, no inbound port)               │
│  → Telegram API servers (outbound HTTPS)                │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│  Hermes Agent (oce-operator profile)                    │
│  - Dedicated OS user / container                        │
│  - No shell, no filesystem write, no Docker             │
│  - Only OCE MCP tools exposed                          │
│  - TELEGRAM_ALLOWED_USERS enforced                     │
│  - TELEGRAM_ALLOW_ALL_USERS=false                      │
│  - No webhook — long polling only                       │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│  OCE MCP Facade (stdio or HTTP, 127.0.0.1 only)        │
│  - Narrow tool surface (read-only observer tools)       │
│  - JSON schema validation (input + output)              │
│  - Rate limiting                                        │
│  - Credential redaction                                 │
│  - Structured audit logging                             │
│  - Request ID tracking                                  │
│  - Authentication via OCE service token                 │
│  - Explicit states: PASS | DEGRADED | BLOCKED |         │
│    OFFLINE | ERROR                                      │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│  OCE Backend API (localhost:8000)                       │
│  - FastAPI REST endpoints                               │
│  - /health, /observers, /events, /execution/tasks,     │
│    /governance/*, /consensus/*, /coevolution/*          │
│  - Policy and authorization layer                      │
│  - Versioned API                                       │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│  OCE Services (PostgreSQL, Redis, etc.)                │
│  - NEVER directly accessible from Hermes or MCP        │
│  - Only through OCE backend API                        │
└─────────────────────────────────────────────────────────┘
```

## Principles

1. **OCE is the authority.** Hermes never bypasses OCE backend.
2. **Read-only by default.** No write actions are enabled in v0.1.
3. **Fail-closed.** Missing data returns OFFLINE/ERROR, never fabricated success.
4. **Defense in depth.** Multiple layers: Telegram allowlist, Hermes config, MCP filtering, facade auth, OCE auth.
5. **Local-first.** No inbound public ports. Long polling only.
6. **Audit everything.** Every interaction is traceable via request_id.

## Components

### Hermes Agent (oce-operator profile)

- **Version:** Pinned at install time (see `pinned-version.txt`)
- **Profile:** `oce-operator` — isolated from default Hermes
- **Telegram:** Long polling, single allowed user
- **MCP:** Only `oce-observer` server configured
- **Tools:** Filtered to observer-only MCP tools
- **Security:** No terminal, no filesystem write, no Docker, no shell

### OCE MCP Facade

- **Transport:** stdio (subprocess) or HTTP (localhost:9090)
- **Tools:** 10 read-only observer tools
- **Auth:** OCE service token (read-only scope)
- **Rate limit:** 60 requests/minute per tool
- **Timeout:** 30 seconds per request
- **Redaction:** Credentials, paths, tokens masked in output
- **Logging:** Structured JSON audit log

### OCE Backend

- **Existing:** FastAPI backend in `larger-lab/oce/backend/`
- **Access:** Only through localhost:8000
- **Auth:** OCE service token for facade
- **Endpoints used:** Read-only subset (see capability-matrix.md)

## Data Flow

1. User sends Telegram message → Telegram API (outbound HTTPS)
2. Hermes receives via long polling → processes with LLM
3. Hermes calls MCP tool → OCE MCP Facade (stdio or localhost)
4. Facade validates request → authenticates with OCE token
5. Facade calls OCE backend API → localhost:8000
6. OCE returns response → facade validates, redacts, formats
7. Formatted response → Hermes → Telegram → User

## Security Layers

| Layer | Mechanism | Fail Mode |
|-------|-----------|-----------|
| Telegram | User ID allowlist | Deny unauthorized |
| Hermes | Profile isolation | No cross-profile access |
| MCP Config | Tool include list | Only registered tools |
| Facade Auth | Service token | Reject unauthorized |
| Facade Filter | Schema validation | Reject malformed |
| Facade Rate | 60 req/min | Throttle excess |
| OCE Auth | Endpoint auth | Reject if missing |
| Network | localhost only | No remote access |

## Network Topology

- **No inbound public ports** — long polling only
- **MCP facade** binds to 127.0.0.1:9090 (HTTP mode) or runs as stdio subprocess
- **OCE backend** at localhost:8000
- **Telegram API** via outbound HTTPS (api.telegram.org)
- **No Docker socket, no SSH, no cloud APIs**

## Deployment

- Local only (no cloud deployment in v0.1)
- Docker Compose for isolation
- Or direct process with systemd unit
- No public-facing endpoints
