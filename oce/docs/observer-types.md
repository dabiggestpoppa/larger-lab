# OCE Observer Type Taxonomy

> **Document:** OCE-3.6 — Observer Type Taxonomy
> **Phase:** OCE Phase 3 — Observer Runtime
> **Status:** Active
> **Last Updated:** May 16, 2026

---

## Overview

The Observer Runtime manages a set of typed observers, each responsible for a distinct domain of system behavior. Observers subscribe to events from the Event Fabric, evaluate state against their domain-specific logic, and emit actions or alerts through the Execution Substrate.

This document defines the canonical observer types, their responsibilities, configuration schemas, event subscriptions, capabilities, and health metrics.

---

## Observer Type Summary

| Type | Domain | Priority | Cadence |
|------|--------|----------|---------|
| `trading` | Market data, strategy execution, position management | Critical | Real-time |
| `repair` | System diagnostics, fault detection, auto-remediation | High | On-demand / 60s |
| `entropy` | Entropy budget monitoring, compression triggers | Medium | 300s |
| `content` | Content farm operations, publishing pipeline | Medium | 120s |
| `system` | System health, resource monitoring, gateway status | High | 30s |
| `planner` | Strategic planning, task decomposition | Medium | On-demand |
| `execution` | Task execution, tool operation, workflow dispatch | High | Real-time |
| `memory` | Memory management, persistence, reconstruction | Medium | 600s |

---

## 1. Trading Observer

### Purpose & Responsibilities

The Trading Observer monitors real-time market data feeds, evaluates active trading strategies, manages open positions, and executes trade signals. It is the primary interface between the Observer Runtime and external market data providers/brokerage APIs.

**Core responsibilities:**
- Subscribe to market data tick streams (price, volume, order book)
- Evaluate strategy conditions against current market state
- Generate and dispatch trade signals (entry, exit, modify, cancel)
- Track open positions, P&L, and exposure limits
- Enforce risk management rules (max drawdown, position sizing, stop-loss)
- Log all trading activity for audit and reconstruction

### Default Configuration Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["enabled", "strategy_ids", "risk_limits"],
  "properties": {
    "enabled": { "type": "boolean", "default": true },
    "strategy_ids": {
      "type": "array",
      "items": { "type": "string" },
      "default": []
    },
    "data_feeds": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "provider": { "type": "string" },
          "endpoint": { "type": "string", "format": "uri" },
          "symbols": { "type": "array", "items": { "type": "string" } },
          "interval_ms": { "type": "integer", "minimum": 100, "default": 1000 }
        }
      },
      "default": []
    },
    "risk_limits": {
      "type": "object",
      "properties": {
        "max_position_size": { "type": "number", "minimum": 0 },
        "max_drawdown_pct": { "type": "number", "minimum": 0, "maximum": 100 },
        "max_open_positions": { "type": "integer", "minimum": 1, "default": 10 },
        "max_daily_loss": { "type": "number", "minimum": 0 },
        "stop_loss_pct": { "type": "number", "minimum": 0, "maximum": 100 },
        "take_profit_pct": { "type": "number", "minimum": 0 }
      },
      "default": {
        "max_open_positions": 10,
        "stop_loss_pct": 5,
        "take_profit_pct": 10
      }
    },
    "execution_mode": {
      "type": "string",
      "enum": ["live", "paper", "backtest"],
      "default": "paper"
    },
    "log_level": {
      "type": "string",
      "enum": ["debug", "info", "warn", "error"],
      "default": "info"
    }
  }
}
```

### Event Subscriptions

| Event Type | Direction | Priority |
|------------|-----------|----------|
| `market.tick` | Subscribe | Critical |
| `market.orderbook` | Subscribe | High |
| `market.candle` | Subscribe | Medium |
| `trade.signal` | Publish | Critical |
| `trade.executed` | Publish | Critical |
| `trade.error` | Publish | High |
| `position.opened` | Publish | High |
| `position.closed` | Publish | High |
| `risk.breached` | Publish | Critical |
| `risk.warning` | Publish | High |
| `system.gateway_status` | Subscribe | Medium |

### Capabilities

| Action | Description |
|--------|-------------|
| `evaluate_strategy` | Run strategy logic against current market state |
| `submit_order` | Send order to brokerage/exchange API |
| `cancel_order` | Cancel a pending order |
| `modify_order` | Modify an existing order parameters |
| `close_position` | Close an open position |
| `get_positions` | Retrieve all open positions |
| `get_pnl` | Calculate current P&L (realized + unrealized) |
| `check_risk` | Evaluate current exposure against risk limits |
| `pause_trading` | Halt all trading activity (emergency) |
| `resume_trading` | Resume trading after pause |

### Health Metrics

| Metric | Type | Warning Threshold | Critical Threshold |
|--------|------|-------------------|-------------------|
| `feed_latency_ms` | Gauge | > 500ms | > 2000ms |
| `tick_processing_time_ms` | Histogram | > 50ms | > 200ms |
| `open_positions` | Gauge | > 80% of max | >= max |
| `daily_pnl_pct` | Gauge | < -2% | < -5% |
| `order_error_rate` | Counter | > 2% | > 5% |
| `strategy_eval_time_ms` | Histogram | > 100ms | > 500ms |
| `last_tick_timestamp` | Gauge | > 30s stale | > 120s stale |
| `risk_breach_count` | Counter | > 0 | > 3 |

---

## 2. Repair Observer

### Purpose & Responsibilities

The Repair Observer continuously monitors system components for faults, degraded performance, and configuration drift. When issues are detected, it runs diagnostic routines and attempts automated remediation before escalating to human operators.

**Core responsibilities:**
- Monitor service health endpoints and process liveness
- Detect configuration drift from expected state
- Run diagnostic sequences on failing components
- Attempt automated repair actions (restart, reconfigure, rollback)
- Escalate unresolvable issues with full diagnostic context
- Maintain a repair history log for pattern analysis

### Default Configuration Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["enabled", "watch_targets"],
  "properties": {
    "enabled": { "type": "boolean", "default": true },
    "watch_targets": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "type": { "type": "string", "enum": ["process", "service", "port", "file", "endpoint"] },
          "target": { "type": "string" },
          "check_interval_s": { "type": "integer", "minimum": 5, "default": 60 },
          "timeout_ms": { "type": "integer", "minimum": 100, "default": 5000 },
          "auto_repair": { "type": "boolean", "default": true },
          "max_repair_attempts": { "type": "integer", "minimum": 1, "default": 3 }
        }
      },
      "default": []
    },
    "repair_policies": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "match": { "type": "string" },
          "action": { "type": "string", "enum": ["restart", "reconfigure", "rollback", "notify", "escalate"] },
          "params": { "type": "object" }
        }
      },
      "default": []
    },
    "escalation_channel": { "type": "string", "default": "system" },
    "diagnostic_depth": {
      "type": "string",
      "enum": ["shallow", "standard", "deep"],
      "default": "standard"
    }
  }
}
```

### Event Subscriptions

| Event Type | Direction | Priority |
|------------|-----------|----------|
| `system.health_check` | Subscribe | High |
| `system.error` | Subscribe | Critical |
| `system.config_drift` | Subscribe | High |
| `system.process_exit` | Subscribe | Critical |
| `repair.started` | Publish | High |
| `repair.completed` | Publish | High |
| `repair.failed` | Publish | Critical |
| `repair.escalated` | Publish | Critical |
| `diagnostic.result` | Publish | Medium |

### Capabilities

| Action | Description |
|--------|-------------|
| `run_diagnostic` | Execute diagnostic sequence on a target component |
| `restart_service` | Restart a named service or process |
| `reconfigure` | Apply corrected configuration to a component |
| `rollback` | Roll back a component to last known good state |
| `kill_process` | Force-terminate a stuck process |
| `check_port` | Verify a network port is listening |
| `check_endpoint` | HTTP health check against an endpoint |
| `check_disk` | Verify disk space and I/O health |
| `check_memory` | Verify memory usage is within bounds |
| `escalate` | Send diagnostic report to escalation channel |

### Health Metrics

| Metric | Type | Warning Threshold | Critical Threshold |
|--------|------|-------------------|-------------------|
| `components_watched` | Gauge | — | — |
| `components_unhealthy` | Gauge | > 0 | > 20% of watched |
| `repair_attempts_total` | Counter | — | — |
| `repair_success_rate` | Gauge | < 80% | < 50% |
| `mean_time_to_repair_s` | Histogram | > 30s | > 120s |
| `escalation_count` | Counter | > 2/hr | > 5/hr |
| `diagnostic_duration_ms` | Histogram | > 5000ms | > 30000ms |
| `config_drift_detected` | Counter | > 0 | > 3 |

---

## 3. Entropy Observer

### Purpose & Responsibilities

The Entropy Observer monitors the entropy budgets of all system components, tracking information density, memory growth rates, and cognitive load. When entropy exceeds configured thresholds, it triggers compression cycles, memory summarization, or data archival to maintain system stability.

**Core responsibilities:**
- Track entropy budgets per component (memory, storage, context windows)
- Monitor memory growth rates and detect unbounded expansion
- Trigger compression cycles when thresholds are exceeded
- Coordinate with the Memory Observer for summarization
- Report entropy economics metrics for system optimization
- Enforce entropy budgets to prevent resource exhaustion

### Default Configuration Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["enabled", "entropy_budgets"],
  "properties": {
    "enabled": { "type": "boolean", "default": true },
    "scan_interval_s": { "type": "integer", "minimum": 60, "default": 300 },
    "entropy_budgets": {
      "type": "object",
      "patternProperties": {
        "^[a-z_]+$": {
          "type": "object",
          "properties": {
            "max_bytes": { "type": "integer", "minimum": 1024 },
            "max_entries": { "type": "integer", "minimum": 10 },
            "growth_rate_limit_bytes_per_hour": { "type": "integer", "minimum": 0 },
            "compression_threshold_pct": { "type": "number", "minimum": 0, "maximum": 100, "default": 80 },
            "archive_threshold_pct": { "type": "number", "minimum": 0, "maximum": 100, "default": 95 }
          }
        }
      },
      "default": {
        "memory": {
          "max_bytes": 104857600,
          "max_entries": 10000,
          "growth_rate_limit_bytes_per_hour": 10485760,
          "compression_threshold_pct": 80,
          "archive_threshold_pct": 95
        },
        "storage": {
          "max_bytes": 1073741824,
          "max_entries": 100000,
          "growth_rate_limit_bytes_per_hour": 52428800,
          "compression_threshold_pct": 75,
          "archive_threshold_pct": 90
        }
      }
    },
    "compression_strategy": {
      "type": "string",
      "enum": ["summarize", "deduplicate", "archive", "prune"],
      "default": "summarize"
    }
  }
}
```

### Event Subscriptions

| Event Type | Direction | Priority |
|------------|-----------|----------|
| `entropy.budget_exceeded` | Publish | High |
| `entropy.compression_started` | Publish | Medium |
| `entropy.compression_completed` | Publish | Medium |
| `memory.size_report` | Subscribe | Medium |
| `memory.growth_rate` | Subscribe | Medium |
| `storage.size_report` | Subscribe | Medium |
| `system.health_check` | Subscribe | Low |

### Capabilities

| Action | Description |
|--------|-------------|
| `measure_entropy` | Calculate current entropy for a named component |
| `trigger_compression` | Initiate compression cycle on a component |
| `summarize_memory` | Run LLM summarization on memory entries |
| `deduplicate` | Remove duplicate entries from a data store |
| `archive_old_data` | Move aged data to cold storage |
| `prune_stale` | Remove entries exceeding TTL |
| `get_budget_status` | Report current budget utilization per component |
| `adjust_budget` | Dynamically adjust entropy budget limits |

### Health Metrics

| Metric | Type | Warning Threshold | Critical Threshold |
|--------|------|-------------------|-------------------|
| `entropy_utilization_pct` | Gauge (per component) | > 70% | > 90% |
| `compression_cycles_total` | Counter | — | — |
| `compression_duration_ms` | Histogram | > 10000ms | > 60000ms |
| `bytes_compressed_total` | Counter | — | — |
| `growth_rate_bytes_per_hour` | Gauge | > 80% of limit | > limit |
| `budget_violations` | Counter | > 0 | > 3 |
| `archive_size_bytes` | Gauge | > 500MB | > 1GB |
| `stale_entries_count` | Gauge | > 1000 | > 10000 |

---

## 4. Content Observer

### Purpose & Responsibilities

The Content Observer manages content farm operations including content generation, editorial review scheduling, publishing pipeline execution, and content performance tracking. It coordinates with external CMS platforms and distribution channels.

**Core responsibilities:**
- Monitor content pipeline stages (draft → review → publish → distribute)
- Track content inventory and publishing schedule
- Trigger content generation workflows based on strategy
- Monitor content performance metrics (views, engagement, SEO)
- Manage content calendar and editorial deadlines
- Coordinate multi-channel publishing (blog, social, newsletter)

### Default Configuration Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["enabled"],
  "properties": {
    "enabled": { "type": "boolean", "default": true },
    "check_interval_s": { "type": "integer", "minimum": 30, "default": 120 },
    "cms_endpoints": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "url": { "type": "string", "format": "uri" },
          "auth_type": { "type": "string", "enum": ["api_key", "oauth", "basic"] }
        }
      },
      "default": []
    },
    "publishing_channels": {
      "type": "array",
      "items": { "type": "string" },
      "default": ["blog"]
    },
    "content_strategy": {
      "type": "object",
      "properties": {
        "posts_per_week": { "type": "integer", "minimum": 1, "default": 3 },
        "topics": { "type": "array", "items": { "type": "string" } },
        "min_word_count": { "type": "integer", "minimum": 100, "default": 800 },
        "seo_enabled": { "type": "boolean", "default": true }
      }
    },
    "performance_thresholds": {
      "type": "object",
      "properties": {
        "min_views_per_post": { "type": "integer", "default": 100 },
        "min_engagement_rate_pct": { "type": "number", "default": 2.0 },
        "alert_on_decline_pct": { "type": "number", "default": 20.0 }
      }
    }
  }
}
```

### Event Subscriptions

| Event Type | Direction | Priority |
|------------|-----------|----------|
| `content.draft_ready` | Subscribe | Medium |
| `content.review_approved` | Subscribe | Medium |
| `content.published` | Publish | Medium |
| `content.performance_report` | Subscribe | Low |
| `content.schedule_missed` | Publish | High |
| `content.generation_requested` | Publish | Medium |
| `content.seo_alert` | Publish | Medium |
| `system.gateway_status` | Subscribe | Low |

### Capabilities

| Action | Description |
|--------|-------------|
| `generate_content` | Trigger content generation for a topic |
| `submit_for_review` | Move draft to review stage |
| `publish` | Publish approved content to configured channels |
| `schedule` | Add content to publishing calendar |
| `get_performance` | Retrieve performance metrics for published content |
| `audit_seo` | Run SEO analysis on content |
| `retire_content` | Archive or unpublish underperforming content |
| `sync_cms` | Synchronize content state with external CMS |

### Health Metrics

| Metric | Type | Warning Threshold | Critical Threshold |
|--------|------|-------------------|-------------------|
| `pipeline_backlog` | Gauge | > 10 items | > 25 items |
| `drafts_pending_review` | Gauge | > 5 | > 15 |
| `posts_published_weekly` | Gauge | < strategy target | < 50% of target |
| `avg_engagement_rate` | Gauge | < 3% | < 1% |
| `seo_score_avg` | Gauge | < 70 | < 50 |
| `schedule_adherence_pct` | Gauge | < 80% | < 50% |
| `cms_sync_errors` | Counter | > 0 | > 3 |
| `content_generation_time_s` | Histogram | > 300s | > 900s |

---

## 5. System Observer

### Purpose & Responsibilities

The System Observer is the foundational health monitor for the entire runtime. It tracks CPU, memory, disk, network, gateway status, and process-level metrics. It provides the base layer of observability that all other observers depend on.

**Core responsibilities:**
- Monitor host-level resources (CPU, memory, disk, network)
- Track gateway process health and responsiveness
- Monitor all registered service endpoints
- Detect resource exhaustion conditions early
- Emit system-level health events for other observers
- Maintain system uptime and availability records

### Default Configuration Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["enabled"],
  "properties": {
    "enabled": { "type": "boolean", "default": true },
    "check_interval_s": { "type": "integer", "minimum": 5, "default": 30 },
    "resource_thresholds": {
      "type": "object",
      "properties": {
        "cpu_warning_pct": { "type": "number", "minimum": 0, "maximum": 100, "default": 75 },
        "cpu_critical_pct": { "type": "number", "minimum": 0, "maximum": 100, "default": 90 },
        "memory_warning_pct": { "type": "number", "minimum": 0, "maximum": 100, "default": 80 },
        "memory_critical_pct": { "type": "number", "minimum": 0, "maximum": 100, "default": 95 },
        "disk_warning_pct": { "type": "number", "minimum": 0, "maximum": 100, "default": 80 },
        "disk_critical_pct": { "type": "number", "minimum": 0, "maximum": 100, "default": 95 }
      }
    },
    "gateway_check": {
      "type": "object",
      "properties": {
        "enabled": { "type": "boolean", "default": true },
        "endpoint": { "type": "string", "default": "http://localhost:3000/health" },
        "timeout_ms": { "type": "integer", "default": 5000 }
      }
    },
    "process_watch": {
      "type": "array",
      "items": { "type": "string" },
      "default": ["python", "node"]
    },
    "network_check": {
      "type": "object",
      "properties": {
        "enabled": { "type": "boolean", "default": true },
        "targets": {
          "type": "array",
          "items": { "type": "string", "format": "uri" },
          "default": ["https://1.1.1.1", "https://8.8.8.8"]
        }
      }
    }
  }
}
```

### Event Subscriptions

| Event Type | Direction | Priority |
|------------|-----------|----------|
| `system.health_check` | Publish | High |
| `system.resource_warning` | Publish | High |
| `system.resource_critical` | Publish | Critical |
| `system.gateway_status` | Publish | High |
| `system.process_exit` | Publish | Critical |
| `system.network_status` | Publish | Medium |

### Capabilities

| Action | Description |
|--------|-------------|
| `get_cpu_usage` | Retrieve current CPU utilization percentage |
| `get_memory_usage` | Retrieve current memory utilization |
| `get_disk_usage` | Retrieve disk usage per mount point |
| `get_network_status` | Check network connectivity |
| `check_gateway` | Verify gateway is responsive |
| `list_processes` | List running processes matching watch list |
| `get_uptime` | Get system uptime |
| `get_load_average` | Get system load average |
| `emit_health_event` | Publish a health check event to the fabric |

### Health Metrics

| Metric | Type | Warning Threshold | Critical Threshold |
|--------|------|-------------------|-------------------|
| `cpu_usage_pct` | Gauge | > 75% | > 90% |
| `memory_usage_pct` | Gauge | > 80% | > 95% |
| `disk_usage_pct` | Gauge | > 80% | > 95% |
| `gateway_latency_ms` | Gauge | > 200ms | > 1000ms |
| `gateway_uptime_pct` | Gauge | < 99% | < 95% |
| `network_latency_ms` | Gauge | > 100ms | > 500ms |
| `process_count` | Gauge | — | — |
| `load_average` | Gauge | > CPU count | > 2x CPU count |

---

## 6. Planner Observer

### Purpose & Responsibilities

The Planner Observer handles strategic planning, task decomposition, dependency resolution, and execution scheduling. It translates high-level goals into actionable task graphs and coordinates with the Execution Observer for dispatch.

**Core responsibilities:**
- Decompose high-level objectives into task DAGs
- Resolve task dependencies and determine execution order
- Estimate resource requirements for planned tasks
- Detect planning conflicts and circular dependencies
- Maintain a planning history for learning and optimization
- Coordinate with Execution Observer for task dispatch

### Default Configuration Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["enabled"],
  "properties": {
    "enabled": { "type": "boolean", "default": true },
    "max_plan_depth": { "type": "integer", "minimum": 1, "default": 5 },
    "max_tasks_per_plan": { "type": "integer", "minimum": 1, "default": 50 },
    "planning_timeout_ms": { "type": "integer", "minimum": 1000, "default": 30000 },
    "retry_policy": {
      "type": "object",
      "properties": {
        "max_retries": { "type": "integer", "minimum": 0, "default": 3 },
        "backoff_ms": { "type": "integer", "minimum": 100, "default": 1000 },
        "backoff_multiplier": { "type": "number", "minimum": 1, "default": 2.0 }
      }
    },
    "dependency_resolution": {
      "type": "string",
      "enum": ["topological", "priority", "deadline"],
      "default": "topological"
    },
    "goal_sources": {
      "type": "array",
      "items": { "type": "string" },
      "default": ["user_input", "system_trigger", "schedule"]
    }
  }
}
```

### Event Subscriptions

| Event Type | Direction | Priority |
|------------|-----------|----------|
| `planning.goal_received` | Subscribe | High |
| `planning.plan_created` | Publish | High |
| `planning.plan_updated` | Publish | Medium |
| `planning.task_ready` | Publish | High |
| `planning.conflict_detected` | Publish | High |
| `execution.task_completed` | Subscribe | Medium |
| `execution.task_failed` | Subscribe | High |
| `system.resource_critical` | Subscribe | Medium |

### Capabilities

| Action | Description |
|--------|-------------|
| `create_plan` | Generate a task DAG from a high-level goal |
| `decompose_task` | Break a task into subtasks |
| `resolve_dependencies` | Determine execution order from task DAG |
| `estimate_resources` | Estimate resource needs for a plan |
| `detect_conflicts` | Find circular dependencies or resource conflicts |
| `update_plan` | Modify an existing plan based on new information |
| `cancel_plan` | Cancel a plan and all its pending tasks |
| `get_plan_status` | Retrieve current status of a plan |
| `prioritize_tasks` | Reorder tasks based on priority/deadline |

### Health Metrics

| Metric | Type | Warning Threshold | Critical Threshold |
|--------|------|-------------------|-------------------|
| `active_plans` | Gauge | > 10 | > 25 |
| `planning_queue_depth` | Gauge | > 5 | > 15 |
| `avg_planning_time_ms` | Histogram | > 5000ms | > 15000ms |
| `plan_completion_rate` | Gauge | < 80% | < 50% |
| `dependency_conflicts` | Counter | > 0 | > 3 |
| `plan_failure_rate` | Gauge | > 10% | > 25% |
| `tasks_per_plan_avg` | Gauge | > 20 | > 40 |
| `retry_rate` | Gauge | > 20% | > 40% |

---

## 7. Execution Observer

### Purpose & Responsibilities

The Execution Observer is the action arm of the Observer Runtime. It receives task dispatch events, executes tool operations, manages workflow state, and reports results back to the planning and system layers.

**Core responsibilities:**
- Receive task dispatch events from the Planner Observer
- Execute tool operations (API calls, file operations, shell commands)
- Manage workflow state and intermediate results
- Handle execution errors with retry logic
- Report task completion/failure events
- Enforce execution timeouts and resource limits

### Default Configuration Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["enabled"],
  "properties": {
    "enabled": { "type": "boolean", "default": true },
    "max_concurrent_tasks": { "type": "integer", "minimum": 1, "default": 5 },
    "default_timeout_ms": { "type": "integer", "minimum": 1000, "default": 30000 },
    "max_timeout_ms": { "type": "integer", "minimum": 1000, "default": 300000 },
    "retry_policy": {
      "type": "object",
      "properties": {
        "max_retries": { "type": "integer", "minimum": 0, "default": 3 },
        "retry_on": {
          "type": "array",
          "items": { "type": "string", "enum": ["timeout", "network_error", "rate_limit", "server_error"] },
          "default": ["timeout", "network_error", "rate_limit"]
        },
        "backoff_ms": { "type": "integer", "minimum": 100, "default": 1000 },
        "backoff_multiplier": { "type": "number", "minimum": 1, "default": 2.0 }
      }
    },
    "tool_allowlist": {
      "type": "array",
      "items": { "type": "string" },
      "default": ["*"]
    },
    "sandbox_mode": {
      "type": "string",
      "enum": ["none", "filesystem", "network", "full"],
      "default": "none"
    },
    "log_all_operations": { "type": "boolean", "default": true }
  }
}
```

### Event Subscriptions

| Event Type | Direction | Priority |
|------------|-----------|----------|
| `planning.task_ready` | Subscribe | High |
| `execution.task_started` | Publish | High |
| `execution.task_completed` | Publish | High |
| `execution.task_failed` | Publish | Critical |
| `execution.tool_called` | Publish | Medium |
| `execution.timeout` | Publish | High |
| `execution.retry` | Publish | Medium |
| `system.resource_critical` | Subscribe | High |

### Capabilities

| Action | Description |
|--------|-------------|
| `execute_task` | Run a task with the specified tool and parameters |
| `call_tool` | Invoke a specific tool by name with arguments |
| `cancel_task` | Cancel a running task |
| `get_task_status` | Retrieve status of a running or completed task |
| `retry_task` | Retry a failed task |
| `batch_execute` | Execute multiple independent tasks concurrently |
| `chain_tasks` | Execute tasks in sequence, passing output to next |
| `sandbox_run` | Execute a tool call within sandbox constraints |

### Health Metrics

| Metric | Type | Warning Threshold | Critical Threshold |
|--------|------|-------------------|-------------------|
| `active_tasks` | Gauge | > 80% of max | >= max |
| `task_queue_depth` | Gauge | > 10 | > 25 |
| `task_completion_rate` | Gauge | < 85% | < 60% |
| `avg_task_duration_ms` | Histogram | > 2x expected | > 5x expected |
| `timeout_rate` | Gauge | > 5% | > 15% |
| `retry_rate` | Gauge | > 20% | > 40% |
| `tool_error_rate` | Gauge | > 3% | > 10% |
| `concurrent_utilization_pct` | Gauge | > 80% | >= 100% |

---

## 8. Memory Observer

### Purpose & Responsibilities

The Memory Observer manages the persistence, compression, and reconstruction of system memory. It ensures that working memory stays within entropy budgets, coordinates with the Entropy Observer for compression cycles, and maintains the integrity of persistent memory stores.

**Core responsibilities:**
- Monitor memory store sizes and growth rates
- Trigger compression/summarization when thresholds are exceeded
- Manage memory persistence (write to disk, sync to stores)
- Handle memory reconstruction after restarts or corruption
- Coordinate with the Entropy Observer for budget enforcement
- Maintain memory versioning and audit trails

### Default Configuration Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["enabled", "stores"],
  "properties": {
    "enabled": { "type": "boolean", "default": true },
    "scan_interval_s": { "type": "integer", "minimum": 60, "default": 600 },
    "stores": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "path": { "type": "string" },
          "format": { "type": "string", "enum": ["json", "jsonl", "markdown", "binary"], "default": "json" },
          "max_size_bytes": { "type": "integer", "minimum": 1024, "default": 10485760 },
          "max_entries": { "type": "integer", "minimum": 10, "default": 5000 },
          "compress_at_pct": { "type": "number", "minimum": 0, "maximum": 100, "default": 80 },
          "backup_count": { "type": "integer", "minimum": 0, "default": 3 }
        }
      },
      "default": [
        { "name": "working_memory", "path": "memory/working.json", "format": "json" },
        { "name": "persistent_memory", "path": "memory/persistent.jsonl", "format": "jsonl" },
        { "name": "progress_log", "path": "progress/", "format": "markdown" }
      ]
    },
    "compression": {
      "type": "object",
      "properties": {
        "strategy": { "type": "string", "enum": ["summarize", "deduplicate", "prune", "archive"], "default": "summarize" },
        "summarize_model": { "type": "string", "default": "default" },
        "min_entries_to_compress": { "type": "integer", "minimum": 5, "default": 20 },
        "preserve_recent_count": { "type": "integer", "minimum": 1, "default": 50 }
      }
    },
    "reconstruction": {
      "type": "object",
      "properties": {
        "enabled": { "type": "boolean", "default": true },
        "verify_checksums": { "type": "boolean", "default": true },
        "max_reconstruction_depth": { "type": "integer", "minimum": 1, "default": 3 }
      }
    }
  }
}
```

### Event Subscriptions

| Event Type | Direction | Priority |
|------------|-----------|----------|
| `memory.write` | Subscribe | Medium |
| `memory.read` | Subscribe | Low |
| `memory.size_report` | Publish | Medium |
| `memory.growth_rate` | Publish | Medium |
| `memory.compression_needed` | Publish | High |
| `memory.compression_completed` | Publish | Medium |
| `memory.reconstruction_started` | Publish | High |
| `memory.reconstruction_completed` | Publish | High |
| `entropy.budget_exceeded` | Subscribe | High |
| `system.process_exit` | Subscribe | Medium |

### Capabilities

| Action | Description |
|--------|-------------|
| `write_entry` | Write an entry to a named memory store |
| `read_entries` | Read entries from a store with optional filtering |
| `compress_store` | Run compression on a memory store |
| `summarize_entries` | Use LLM to summarize a set of entries |
| `reconstruct` | Reconstruct memory state from persistent stores |
| `verify_integrity` | Check store integrity (checksums, structure) |
| `backup` | Create a backup of a memory store |
| `restore` | Restore a store from backup |
| `get_store_stats` | Report size, entry count, growth rate per store |

### Health Metrics

| Metric | Type | Warning Threshold | Critical Threshold |
|--------|------|-------------------|-------------------|
| `store_size_bytes` (per store) | Gauge | > 80% of max | > 95% of max |
| `store_entry_count` (per store) | Gauge | > 80% of max | > 95% of max |
| `write_latency_ms` | Histogram | > 100ms | > 500ms |
| `read_latency_ms` | Histogram | > 50ms | > 200ms |
| `compression_queue_depth` | Gauge | > 3 | > 10 |
| `reconstruction_time_ms` | Histogram | > 5000ms | > 30000ms |
| `integrity_check_failures` | Counter | > 0 | > 2 |
| `backup_age_seconds` | Gauge | > 86400 | > 604800 |

---

## Cross-Observer Interactions

```
┌─────────────────────────────────────────────────────────────┐
│                      Event Fabric                            │
│                                                              │
│  ┌──────────┐  market.tick   ┌──────────┐                   │
│  │ Trading  │◄──────────────►│  System  │                   │
│  │ Observer │  risk.breached │ Observer │                   │
│  └────┬─────┘                └────┬─────┘                   │
│       │                           │                          │
│       │ trade.signal              │ system.health_check      │
│       ▼                           ▼                          │
│  ┌──────────┐  task_ready   ┌──────────┐                   │
│  │Execution │◄──────────────│ Planner  │                   │
│  │ Observer │  completed    │ Observer │                   │
│  └────┬─────┘──────────────►└──────────┘                   │
│       │                                                     │
│       │ tool_error                                          │
│       ▼                                                     │
│  ┌──────────┐  diagnostic  ┌──────────┐                    │
│  │  Repair  │◄─────────────│  Memory  │                    │
│  │ Observer │  repair_done │ Observer │                    │
│  └──────────┘              └────┬─────┘                    │
│                                 │                           │
│                     compression_needed                      │
│                                 ▼                           │
│                          ┌──────────┐                      │
│                          │ Entropy  │                      │
│                          │ Observer │                      │
│                          └──────────┘                      │
│                                 ▲                           │
│                                 │ budget_exceeded           │
│                          ┌──────────┐                      │
│                          │ Content  │                      │
│                          │ Observer │                      │
│                          └──────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Observer Lifecycle

All observers follow a standard lifecycle:

1. **Initialize** — Load configuration, validate schema, establish connections
2. **Subscribe** — Register event subscriptions with the Event Fabric
3. **Activate** — Begin monitoring and processing events
4. **Steady State** — Continuous monitoring, periodic health reporting
5. **Compress** — On entropy trigger, reduce internal state
6. **Checkpoint** — Persist state for recovery
7. **Deactivate** — Graceful shutdown, flush pending state
8. **Reconstruct** — On restart, rebuild state from checkpoints

---

## Configuration Inheritance

All observers inherit from a base configuration:

```json
{
  "base": {
    "enabled": true,
    "log_level": "info",
    "health_report_interval_s": 60,
    "max_event_queue_size": 1000,
    "shutdown_timeout_s": 30
  }
}
```

Type-specific configurations override base values. Observer types cannot remove or change the type of base properties.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | May 16, 2026 | Initial taxonomy — 8 observer types defined |
