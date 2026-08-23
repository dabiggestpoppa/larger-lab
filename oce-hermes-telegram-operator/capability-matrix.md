# Capability Matrix — OCE Hermes Telegram Operator

> Version: 0.1.0  
> Date: 2026-08-23

## MCP Tool → OCE Endpoint Mapping

| MCP Tool | OCE Endpoint | Method | Description | State |
|----------|-------------|--------|-------------|-------|
| `oce_health` | `/health` | GET | Backend health check | ✅ Active |
| `oce_system_status` | `/` + `/health` | GET | Overall system status | ✅ Active |
| `oce_component_status` | `/observers` | GET | Individual component status | ✅ Active |
| `oce_list_jobs` | `/execution/tasks` | GET | List execution tasks/jobs | ✅ Active |
| `oce_get_job` | `/execution/tasks/{task_id}` | GET | Get specific job details | ✅ Active |
| `oce_get_recent_events` | `/events` | GET | Recent system events | ✅ Active |
| `oce_get_evidence_status` | `/execution/stats` | GET | Evidence/validation status | ✅ Active |
| `oce_get_cost_status` | `/execution/analytics` | GET | Cost and analytics data | ✅ Active |
| `oce_get_capability_manifest` | `/evolution/status` | GET | System capabilities | ✅ Active |
| `oce_get_backend_version` | `/` | GET | Backend version info | ✅ Active |

## Telegram Command → MCP Tool Mapping

| Command | MCP Tool(s) | Description |
|---------|------------|-------------|
| `/start` | — | Welcome message, identity confirmation |
| `/help` | — | List available commands |
| `/health` | `oce_health` | Backend health check |
| `/status` | `oce_system_status` | Full system status |
| `/components` | `oce_component_status` | Individual component health |
| `/jobs` | `oce_list_jobs` | List recent jobs |
| `/job <id>` | `oce_get_job` | Specific job details |
| `/events` | `oce_get_recent_events` | Recent system events |
| `/evidence` | `oce_get_evidence_status` | Validation evidence status |
| `/cost` | `oce_get_cost_status` | Cost and usage analytics |
| `/capabilities` | `oce_get_capability_manifest` | System capabilities |
| `/privacy` | — | Privacy policy and data handling |
| `/audit <id>` | — | Audit trail for a request |

## Natural Language → Tool Selection

| User Says | Tool Called | Notes |
|-----------|------------|-------|
| "Is the system healthy?" | `oce_health` | Direct mapping |
| "What's the status?" | `oce_system_status` | Full status |
| "How are the components?" | `oce_component_status` | Component breakdown |
| "What jobs are running?" | `oce_list_jobs` | Job listing |
| "Tell me about job X" | `oce_get_job` | Specific job |
| "What happened recently?" | `oce_get_recent_events` | Event feed |
| "Show evidence status" | `oce_get_evidence_status` | Evidence check |
| "What are the costs?" | `oce_get_cost_status` | Cost analytics |
| "What can the system do?" | `oce_get_capability_manifest` | Capabilities |
| "What version is running?" | `oce_get_backend_version` | Version info |

## Forbidden Operations (Never Exposed)

| Category | Blocked Tools | Reason |
|----------|--------------|--------|
| Shell | `terminal`, `execute_code` | Arbitrary code execution |
| Filesystem | `write_file`, `delete_file` | Data modification |
| Database | `query_db`, `execute_sql` | Direct data access |
| Docker | `docker_*` | Container escape risk |
| SSH | `ssh_*` | Remote access |
| Git | `git_push`, `git_commit` | Code modification |
| Deployment | `deploy_*`, `rollback` | Production changes |
| Trading | `execute_trade`, `place_order` | Financial risk |
| Cloud | `aws_*`, `gcp_*`, `azure_*` | Infrastructure control |

## Response Format

All responses follow this structure:

```
[STATE] Response content

📋 Request ID: <uuid>
🕐 Timestamp: <ISO-8601>
📦 Backend: <version>
```

States:
- ✅ `PASS` — Data retrieved successfully
- ⚠️ `DEGRADED` — Partial data available
- 🚫 `BLOCKED` — Access denied or policy violation
- 🔴 `OFFLINE` — OCE backend unreachable
- ❌ `ERROR` — Unexpected failure
