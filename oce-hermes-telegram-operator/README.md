# OCE Hermes Telegram Operator

> **Version:** 0.1.0  
> **Status:** READY_FOR_OPERATOR_SECRET_SETUP  
> **Phase:** Observer Mode (read-only)

A security-first Telegram interface powered by [NousResearch Hermes Agent](https://github.com/NousResearch/hermes-agent) that observes the OCE (Operator Continuity Engine) backend through a filtered MCP facade.

## Architecture

```
Telegram → Hermes Agent → OCE MCP Facade → OCE Backend
   (long      (oce-operator     (10 read-only     (localhost:8000)
   polling)    profile)          tools)
```

**Key principles:**
- OCE is the authority — Hermes never bypasses it
- Read-only by default — no write actions in v0.1
- Fail-closed — missing data returns OFFLINE, never fabricated success
- Local-first — no inbound public ports
- Defense in depth — multiple security layers

## Quick Start

### Prerequisites

- Python 3.11+
- A Telegram bot token (from @BotFather)
- Your numeric Telegram user ID (from @userinfobot)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd oce-hermes-telegram-operator

# Run setup script
./scripts/setup.sh

# Edit .env with your secrets
nano .env

# Validate configuration
python3 scripts/doctor.py

# Start the system
./scripts/start.sh
```

### Secret Gate

Before starting, add these to `.env`:

1. **TELEGRAM_BOT_TOKEN** — Your BotFather token
2. **TELEGRAM_ALLOWED_USERS** — Your numeric Telegram user ID
3. **LLM_PROVIDER_KEY** — (if required by Hermes)
4. **OCE_SERVICE_TOKEN** — (once OCE backend is available)

## Available Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome and identity |
| `/help` | List all commands |
| `/health` | Backend health check |
| `/status` | Full system status |
| `/components` | Component health breakdown |
| `/jobs` | List recent jobs |
| `/job <id>` | Specific job details |
| `/events` | Recent system events |
| `/evidence` | Validation evidence status |
| `/cost` | Cost and usage analytics |
| `/capabilities` | System capabilities |
| `/privacy` | Privacy policy |
| `/audit <id>` | Audit trail for a request |

Natural language questions also work — Hermes routes them to the appropriate tool.

## Security

### What's Exposed

Only 10 read-only observer tools:

1. `oce_health` — Backend health
2. `oce_system_status` — System status
3. `oce_component_status` — Component health
4. `oce_list_jobs` — List jobs
5. `oce_get_job` — Job details
6. `oce_get_recent_events` — Events
7. `oce_get_evidence_status` — Evidence status
8. `oce_get_cost_status` — Cost analytics
9. `oce_get_capability_manifest` — Capabilities
10. `oce_get_backend_version` — Version info

### What's Blocked

- ❌ Terminal / shell execution
- ❌ Filesystem write operations
- ❌ Database queries
- ❌ Docker management
- ❌ SSH access
- ❌ Git push / deployment
- ❌ Trade execution
- ❌ Cloud control APIs

### Security Features

- Telegram user ID allowlist (fail-closed)
- MCP tool filtering (explicit include list)
- Rate limiting (60 req/min)
- Credential redaction in all outputs
- Structured audit logging
- Request ID tracking across all layers
- No inbound public ports
- Container isolation with no Docker socket

## Testing

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test suites
python3 -m pytest tests/unit/ -v          # Unit tests
python3 -m pytest tests/integration/ -v   # Integration tests
python3 -m pytest tests/adversarial/ -v   # Security tests

# With coverage
python3 -m pytest tests/ --cov=src --cov-report=term-missing
```

## Project Structure

```
oce-hermes-telegram-operator/
├── src/
│   └── oce_mcp_facade/
│       ├── facade.py          # MCP server implementation
│       ├── config.py          # Configuration management
│       ├── audit/
│       │   └── logger.py      # Structured audit logging
│       ├── schemas/
│       │   └── tool_schemas.json  # JSON schemas
│       └── tools/             # Tool definitions
├── config/
│   └── hermes-config.yaml     # Hermes configuration
├── hermes_profiles/
│   └── oce-operator/          # Hermes profile
├── tests/
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── adversarial/           # Security tests
├── scripts/
│   ├── setup.sh               # Setup script
│   ├── start.sh               # Start script
│   ├── stop.sh                # Stop script
│   ├── status.sh              # Status script
│   └── doctor.py              # Configuration validator
├── docker/
│   ├── Dockerfile.facade      # Facade container
│   └── Dockerfile.hermes      # Hermes container
├── evidence/                  # Audit logs and validation
├── docs/
│   ├── operator-runbook.md    # Daily operations
│   ├── disaster-recovery.md   # Recovery procedures
│   └── secret-rotation.md     # Secret management
├── architecture.md            # System architecture
├── threat-model.md            # Threat analysis
├── capability-matrix.md       # Tool mapping
├── oce-integration-contract.md # Backend contract
├── docker-compose.yml         # Local deployment
├── pyproject.toml             # Python project config
├── .env.example               # Environment template
└── pinned-version.txt         # Hermes version pin
```

## Documentation

- [Architecture](architecture.md) — System design and principles
- [Threat Model](threat-model.md) — Security analysis
- [Capability Matrix](capability-matrix.md) — Tool mapping
- [OCE Integration Contract](oce-integration-contract.md) — Backend interface
- [Operator Runbook](docs/operator-runbook.md) — Daily operations
- [Disaster Recovery](docs/disaster-recovery.md) — Recovery procedures
- [Secret Rotation](docs/secret-rotation.md) — Secret management

## License

Proprietary — OCE Team internal use only.
