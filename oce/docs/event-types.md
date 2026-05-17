# OCE Event Type Taxonomy

> **Author:** Sub-OC (Analysis & Planning)
> **Date:** 2026-05-16
> **Phase:** OCE Phase 2 — Event Fabric (OCE-2.7)
> **Status:** Complete
> **Unblocks:** Sub-RL DSPy event classification pipeline

---

## Overview

This document defines the **complete event type taxonomy** for the OCE Event Fabric. Every event emitted by SRRA-OPH subsystems, OCE internal systems, and operator tools is classified here.

### Naming Convention

```
<domain>.<subdomain>.<action>
```

- **domain**: `observer`, `attractor`, `entropy`, `repair`, `system`, `operator`, `chat`, `topology`, `memory`
- **subdomain** (optional): Further classification within domain
- **action**: What happened — `created`, `updated`, `triggered`, `completed`, `failed`, `warning`, `exhausted`, `received`, `responded`, `executed`, `killed`, `modified`, `event`, `change`, `divergence`, `convergence`, `threshold`, `snapshot`, `compressed`, `reconstructed`, `activated`, `suspended`, `destroyed`, `subscribed`, `bound`, `unbound`, `stored`, `searched`, `replayed`, `opened`, `edited`, `command`, `git_commit`, `file_opened`, `file_edited`, `package_installed`, `process_killed`, `command_executed`, `vscode_event`, `startup`, `shutdown`, `error`, `warning`, `info`, `debug`, `state_change`, `update`, `signal`, `budget_warning`, `budget_exhausted`

### Priority Levels

| Level | Name | Meaning | Response |
|-------|------|---------|----------|
| 0 | `low` | Informational, no action needed | Log only |
| 1 | `normal` | Standard operational event | Process normally |
| 2 | `high` | Requires attention, possible intervention | Alert + process |
| 3 | `critical` | Immediate action required | Alert + escalate + process |

---

## Domain: `observer.*` — Observer Lifecycle & State

Events emitted by the Observer Runtime when observers change state or process events.

| Event Type | Priority | Description | Source |
|------------|----------|-------------|--------|
| `observer.created` | 2 (high) | New observer registered in the runtime | `observer_runtime` |
| `observer.destroyed` | 2 (high) | Observer permanently removed | `observer_runtime` |
| `observer.activated` | 1 (normal) | Observer started processing events | `observer_runtime` |
| `observer.suspended` | 1 (normal) | Observer paused (event processing halted) | `observer_runtime` |
| `observer.state_change` | 1 (normal) | Observer transitioned between states | `observer_runtime` |
| `observer.event_processed` | 0 (low) | Observer successfully processed an event | `observer_runtime` |
| `observer.event_error` | 2 (high) | Observer failed to process an event | `observer_runtime` |
| `observer.entropy_threshold` | 3 (critical) | Observer entropy exceeded configured threshold | `observer_runtime` |
| `observer.health_degraded` | 2 (high) | Observer health score dropped below threshold | `observer_runtime` |
| `observer.health_recovered` | 1 (normal) | Observer health score returned to normal | `observer_runtime` |
| `observer.drift_detected` | 2 (high) | Observer behavior drift detected by DriftDetector | `drift_detector` |
| `observer.subscribed` | 0 (low) | Observer subscribed to event types | `observer_runtime` |
| `observer.unsubscribed` | 0 (low) | Observer unsubscribed from event types | `observer_runtime` |
| `observer.config_updated` | 1 (normal) | Observer configuration changed | `observer_runtime` |
| `observer.snapshot_created` | 0 (low) | Observer state snapshot stored | `observer_runtime` |
| `observer.restored` | 1 (normal) | Observer restored from snapshot | `observer_runtime` |

### Payload Schemas: observer.*

#### observer.created
```json
{
  "observer_id": "uuid",
  "observer_type": "trading | repair | entropy | content | system | planner | execution | memory",
  "name": "string",
  "capabilities": ["string"],
  "event_subscriptions": ["event_type"],
  "config": {}
}
```

#### observer.state_change
```json
{
  "observer_id": "uuid",
  "state": "created | active | suspended | destroyed",
  "previous_state": "created | active | suspended",
  "reason": "string (optional)"
}
```

#### observer.event_processed
```json
{
  "observer_id": "uuid",
  "event_id": "uuid",
  "event_type": "string",
  "processing_time_ms": 0.0,
  "result": "success | partial | skipped"
}
```

#### observer.event_error
```json
{
  "observer_id": "uuid",
  "event_id": "uuid",
  "event_type": "string",
  "error": "string",
  "error_type": "string",
  "retry_count": 0
}
```

#### observer.entropy_threshold
```json
{
  "observer_id": "uuid",
  "entropy": 0.0,
  "threshold": 0.0,
  "trend": "rising | stable | falling"
}
```

#### observer.health_degraded / observer.health_recovered
```json
{
  "observer_id": "uuid",
  "health_score": 0.0,
  "previous_health_score": 0.0,
  "reason": "string"
}
```

#### observer.drift_detected
```json
{
  "observer_id": "uuid",
  "drift_score": 0.0,
  "drift_type": "behavioral | parametric | structural",
  "direction": "positive | negative"
}
```

#### observer.subscribed / observer.unsubscribed
```json
{
  "observer_id": "uuid",
  "event_types": ["string"],
  "filter_pattern": "string (optional)"
}
```

#### observer.snapshot_created / observer.restored
```json
{
  "observer_id": "uuid",
  "snapshot_id": "uuid",
  "timestamp": "ISO-8601",
  "size_bytes": 0
}
```

---

## Domain: `attractor.*` — Attractor Reasoning Engine

Events emitted by the Attractor Reasoning Engine when operational goals and convergence states change.

| Event Type | Priority | Description | Source |
|------------|----------|-------------|--------|
| `attractor.update` | 1 (normal) | Attractor state updated (goal, confidence, entropy pressure) | `attractor_reasoning` |
| `attractor.convergence` | 2 (high) | Attractor reached convergence (goal stable) | `attractor_reasoning` |
| `attractor.divergence` | 3 (critical) | Attractor diverged (goal unstable, needs intervention) | `attractor_reasoning` |
| `attractor.goal_set` | 1 (normal) | New operational goal established | `attractor_reasoning` |
| `attractor.goal_achieved` | 2 (high) | Operational goal achieved | `attractor_reasoning` |
| `attractor.goal_abandoned` | 2 (high) | Operational goal abandoned (timeout or superseded) | `attractor_reasoning` |
| `attractor.entropy_pressure` | 1 (normal) | Entropy pressure on attractor changed | `attractor_reasoning` |
| `attractor.reinforcement` | 1 (normal) | Reinforcement signal applied to attractor | `reinforcement_engine` |

### Payload Schemas: attractor.*

#### attractor.update
```json
{
  "goal": "string",
  "confidence": 0.0,
  "entropy_pressure": 0.0,
  "convergence": 0.0,
  "observer_ids": ["uuid"]
}
```

#### attractor.convergence / attractor.divergence
```json
{
  "goal": "string",
  "convergence_score": 0.0,
  "entropy_pressure": 0.0,
  "duration_seconds": 0.0,
  "observer_ids": ["uuid"]
}
```

#### attractor.goal_set / attractor.goal_achieved / attractor.goal_abandoned
```json
{
  "goal": "string",
  "goal_id": "uuid",
  "reason": "string (optional)",
  "superseded_by": "goal_id (optional)"
}
```

#### attractor.entropy_pressure
```json
{
  "pressure": 0.0,
  "trend": "increasing | stable | decreasing",
  "affected_observers": ["uuid"]
}
```

#### attractor.reinforcement
```json
{
  "goal_id": "uuid",
  "signal_strength": 0.0,
  "source": "string",
  "observer_id": "uuid"
}
```

---

## Domain: `entropy.*` — Entropy Budget & Signal System

Events emitted by the Entropy Budget Manager and related entropy tracking systems.

| Event Type | Priority | Description | Source |
|------------|----------|-------------|--------|
| `entropy.signal` | 1 (normal) | Entropy level changed for a subsystem | `entropy_budget` |
| `entropy.budget_warning` | 2 (high) | Entropy budget running low (below 25%) | `entropy_budget` |
| `entropy.budget_exhausted` | 3 (critical) | Entropy budget fully consumed | `entropy_budget` |
| `entropy.budget_replenished` | 1 (normal) | Entropy budget replenished (time-based or manual) | `entropy_budget` |
| `entropy.spike` | 2 (high) | Sudden entropy spike detected | `entropy_budget` |
| `entropy.stable` | 0 (low) | Entropy stabilized after fluctuation | `entropy_budget` |
| `entropy.compression_triggered` | 1 (normal) | Adaptive compression triggered due to entropy | `compression_engine` |
| `entropy.compression_completed` | 0 (low) | Compression cycle completed | `compression_engine` |

### Payload Schemas: entropy.*

#### entropy.signal
```json
{
  "source": "string",
  "entropy": 0.0,
  "previous_entropy": 0.0,
  "delta": 0.0,
  "trend": "rising | stable | falling"
}
```

#### entropy.budget_warning / entropy.budget_exhausted / entropy.budget_replenished
```json
{
  "budget_total": 0.0,
  "budget_consumed": 0.0,
  "budget_remaining": 0.0,
  "percentage_used": 0.0,
  "observer_id": "uuid (optional)"
}
```

#### entropy.spike
```json
{
  "source": "string",
  "entropy_before": 0.0,
  "entropy_after": 0.0,
  "spike_magnitude": 0.0,
  "duration_ms": 0.0
}
```

#### entropy.stable
```json
{
  "source": "string",
  "entropy": 0.0,
  "stabilization_duration_ms": 0.0
}
```

#### entropy.compression_triggered / entropy.compression_completed
```json
{
  "observer_id": "uuid",
  "compression_ratio": 0.0,
  "original_size_bytes": 0,
  "compressed_size_bytes": 0,
  "duration_ms": 0.0
}
```

---

## Domain: `repair.*` — Repair & Self-Healing System

Events emitted by the Repair Patch and self-healing systems.

| Event Type | Priority | Description | Source |
|------------|----------|-------------|--------|
| `repair.triggered` | 2 (high) | Repair process initiated for a failing component | `repair_patch` |
| `repair.completed` | 1 (normal) | Repair completed successfully | `repair_patch` |
| `repair.failed` | 3 (critical) | Repair failed (component may be unrecoverable) | `repair_patch` |
| `repair.verified` | 1 (normal) | Post-repair verification passed | `repair_patch` |
| `repair.rollback` | 2 (high) | Repair rolled back (verification failed) | `repair_patch` |
| `repair.diagnosed` | 1 (normal) | Root cause diagnosis completed | `repair_patch` |
| `repair.pre_check` | 0 (low) | Pre-repair health check completed | `repair_patch` |
| `repair.post_check` | 0 (low) | Post-repair health check completed | `repair_patch` |

### Payload Schemas: repair.*

#### repair.triggered
```json
{
  "repair_id": "uuid",
  "target_type": "observer | attractor | entropy | system",
  "target_id": "uuid",
  "trigger_reason": "string",
  "severity": "low | medium | high | critical",
  "repair_strategy": "string"
}
```

#### repair.completed
```json
{
  "repair_id": "uuid",
  "target_id": "uuid",
  "duration_ms": 0.0,
  "strategy_used": "string",
  "health_before": 0.0,
  "health_after": 0.0
}
```

#### repair.failed
```json
{
  "repair_id": "uuid",
  "target_id": "uuid",
  "error": "string",
  "attempt": 0,
  "max_attempts": 0,
  "fallback_strategy": "string (optional)"
}
```

#### repair.verified / repair.rollback
```json
{
  "repair_id": "uuid",
  "target_id": "uuid",
  "verification_result": "passed | failed",
  "health_score": 0.0
}
```

#### repair.diagnosed
```json
{
  "repair_id": "uuid",
  "target_id": "uuid",
  "root_cause": "string",
  "confidence": 0.0,
  "recommended_strategy": "string"
}
```

#### repair.pre_check / repair.post_check
```json
{
  "repair_id": "uuid",
  "target_id": "uuid",
  "health_score": 0.0,
  "entropy": 0.0,
  "checks_passed": 0,
  "checks_failed": 0
}
```

---

## Domain: `system.*` — OCE System-Level Events

Events emitted by the OCE platform itself (startup, shutdown, errors, config changes).

| Event Type | Priority | Description | Source |
|------------|----------|-------------|--------|
| `system.startup` | 1 (normal) | OCE system started | `main` |
| `system.shutdown` | 1 (normal) | OCE system shutting down | `main` |
| `system.error` | 3 (critical) | System-level error occurred | `main` |
| `system.warning` | 2 (high) | System warning (non-fatal issue) | `main` |
| `system.info` | 0 (low) | Informational system event | `main` |
| `system.config_loaded` | 0 (normal) | Configuration loaded successfully | `main` |
| `system.config_reloaded` | 1 (normal) | Configuration hot-reloaded | `main` |
| `system.phase_transition` | 1 (normal) | OCE phase transition occurred | `phase_gate` |
| `system.agent_connected` | 1 (normal) | Agent connected to OCE | `main` |
| `system.agent_disconnected` | 1 (normal) | Agent disconnected from OCE | `main` |
| `system.fabric_ready` | 1 (normal) | Event Fabric fully initialized | `event_fabric` |
| `system.runtime_ready` | 1 (normal) | Observer Runtime fully initialized | `observer_runtime` |
| `system.memory_ready` | 1 (normal) | Structural Memory fully initialized | `structural_memory` |

### Payload Schemas: system.*

#### system.startup / system.shutdown
```json
{
  "version": "string",
  "phase": "string",
  "uptime_seconds": 0.0,
  "components_loaded": ["string"]
}
```

#### system.error / system.warning / system.info
```json
{
  "component": "string",
  "message": "string",
  "error_code": "string (optional)",
  "stack_trace": "string (optional)",
  "context": {}
}
```

#### system.config_loaded / system.config_reloaded
```json
{
  "config_version": "string",
  "keys_loaded": 0,
  "source": "file | env | remote"
}
```

#### system.phase_transition
```json
{
  "from_phase": "string",
  "to_phase": "string",
  "triggered_by": "agent_id",
  "tests_passing": 0,
  "tests_total": 0
}
```

#### system.agent_connected / system.agent_disconnected
```json
{
  "agent_id": "string",
  "agent_type": "string",
  "channel": "string"
}
```

#### system.fabric_ready / system.runtime_ready / system.memory_ready
```json
{
  "component": "string",
  "initialization_time_ms": 0.0,
  "dependencies": ["string"]
}
```

---

## Domain: `operator.*` — Operator Tool Integration

Events emitted by PM's Operator tools (System Operator, VS Code Controller).

| Event Type | Priority | Description | Source |
|------------|----------|-------------|--------|
| `operator.command.executed` | 1 (normal) | System command executed | `event-integration` |
| `operator.process.killed` | 2 (high) | Process terminated by operator | `event-integration` |
| `operator.file.modified` | 0 (low) | File modified by operator | `event-integration` |
| `operator.file.opened` | 0 (low) | File opened in editor | `vscode-controller` |
| `operator.vscode.command` | 0 (normal) | VS Code command executed | `vscode-controller` |
| `operator.vscode.git_commit` | 1 (normal) | Git commit via VS Code | `vscode-controller` |
| `operator.package.installed` | 1 (normal) | Package installed by operator | `event-integration` |
| `operator.observer.create` | 1 (normal) | Operator created an observer | `observer-integration` |
| `operator.observer.activate` | 1 (normal) | Operator activated an observer | `observer-integration` |
| `operator.observer.suspend` | 1 (normal) | Operator suspended an observer | `observer-integration` |
| `operator.observer.destroy` | 2 (high) | Operator destroyed an observer | `observer-integration` |

### Payload Schemas: operator.*

#### operator.command.executed
```json
{
  "command": "string",
  "exit_code": 0,
  "duration_ms": 0.0,
  "stdout": "string (truncated)",
  "stderr": "string (truncated)"
}
```

#### operator.process.killed
```json
{
  "pid": 0,
  "process_name": "string",
  "signal": "SIGTERM | SIGKILL",
  "reason": "string"
}
```

#### operator.file.modified / operator.file.opened
```json
{
  "file_path": "string",
  "action": "created | modified | deleted | opened",
  "size_bytes": 0
}
```

#### operator.vscode.command / operator.vscode.git_commit
```json
{
  "command": "string",
  "args": {},
  "result": "success | failure"
}
```

#### operator.package.installed
```json
{
  "package_name": "string",
  "version": "string",
  "manager": "pip | npm | cargo",
  "duration_ms": 0.0
}
```

#### operator.observer.create / activate / suspend / destroy
```json
{
  "observer_id": "uuid",
  "observer_type": "string",
  "operator_id": "string"
}
```

---

## Domain: `chat.*` — Chat & Conversation Events

Events emitted by the chat/conversation system.

| Event Type | Priority | Description | Source |
|------------|----------|-------------|--------|
| `chat.message.received` | 0 (low) | User message received | `main` |
| `chat.message.responded` | 0 (low) | Assistant response generated | `main` |
| `chat.session.created` | 0 (low) | New chat session started | `main` |
| `chat.session.ended` | 0 (low) | Chat session ended | `main` |
| `chat.context.compacted` | 1 (normal) | Chat context compacted (token limit) | `main` |
| `chat.error` | 2 (high) | Chat processing error | `main` |

### Payload Schemas: chat.*

#### chat.message.received / chat.message.responded
```json
{
  "session_id": "string",
  "message_id": "uuid",
  "role": "user | assistant",
  "content_length": 0,
  "tokens": 0
}
```

#### chat.session.created / chat.session.ended
```json
{
  "session_id": "string",
  "user_id": "string",
  "duration_seconds": 0.0,
  "message_count": 0
}
```

#### chat.context.compacted
```json
{
  "session_id": "string",
  "original_tokens": 0,
  "compacted_tokens": 0,
  "compression_ratio": 0.0
}
```

#### chat.error
```json
{
  "session_id": "string",
  "error": "string",
  "error_type": "string"
}
```

---

## Domain: `topology.*` — Collar Topology Events

Events emitted by the Collar Topology Engine.

| Event Type | Priority | Description | Source |
|------------|----------|-------------|--------|
| `topology.change` | 1 (normal) | Topology graph changed (node/edge added/removed) | `collar_topology` |
| `topology.stable` | 0 (low) | Topology stabilized after changes | `collar_topology` |
| `topology.fragmentation` | 2 (high) | Topology fragmentation detected | `collar_topology` |
| `topology.merged` | 1 (normal) | Topology fragments merged | `collar_topology` |
| `topology.routing_update` | 1 (normal) | Event routing table updated | `topological_router` |

### Payload Schemas: topology.*

#### topology.change
```json
{
  "change_type": "node_added | node_removed | edge_added | edge_removed | weight_changed",
  "node_id": "string (optional)",
  "edge": {"from": "string", "to": "string"} (optional),
  "topology_metrics": {
    "node_count": 0,
    "edge_count": 0,
    "diameter": 0
  }
}
```

#### topology.stable / topology.fragmentation / topology.merged
```json
{
  "fragment_count": 0,
  "node_count": 0,
  "stability_score": 0.0,
  "duration_ms": 0.0
}
```

#### topology.routing_update
```json
{
  "routes_added": 0,
  "routes_removed": 0,
  "total_routes": 0,
  "trigger": "topology_change | observer_change | manual"
}
```

---

## Domain: `memory.*` — Structural Memory Events

Events emitted by the Structural Memory system (Phase 4).

| Event Type | Priority | Description | Source |
|------------|----------|-------------|--------|
| `memory.snapshot_stored` | 0 (low) | Observer state snapshot stored | `structural_memory` |
| `memory.snapshot_retrieved` | 0 (low) | Observer state snapshot retrieved | `structural_memory` |
| `memory.compression_started` | 1 (normal) | Memory compression cycle started | `structural_memory` |
| `memory.compression_completed` | 0 (low) | Memory compression cycle completed | `structural_memory` |
| `memory.reconstruction_started` | 1 (normal) | State reconstruction started | `structural_memory` |
| `memory.reconstruction_completed` | 1 (normal) | State reconstruction completed | `structural_memory` |
| `memory.reconstruction_failed` | 3 (critical) | State reconstruction failed | `structural_memory` |
| `memory.search_performed` | 0 (low) | Memory search query executed | `structural_memory` |
| `memory.timeline_generated` | 0 (low) | Observer timeline generated | `structural_memory` |
| `memory.anchor_created` | 0 (low) | Recovery anchor created | `structural_memory` |
| `memory.anchor_expired` | 1 (normal) | Recovery anchor expired | `structural_memory` |

### Payload Schemas: memory.*

#### memory.snapshot_stored / memory.snapshot_retrieved
```json
{
  "observer_id": "uuid",
  "snapshot_id": "uuid",
  "timestamp": "ISO-8601",
  "size_bytes": 0,
  "layer": "trajectory | topology | repair | attractor | event | context"
}
```

#### memory.compression_started / memory.compression_completed
```json
{
  "observer_id": "uuid",
  "layer": "string",
  "original_size_bytes": 0,
  "compressed_size_bytes": 0,
  "compression_ratio": 0.0,
  "duration_ms": 0.0
}
```

#### memory.reconstruction_started / memory.reconstruction_completed / memory.reconstruction_failed
```json
{
  "observer_id": "uuid",
  "target_timestamp": "ISO-8601",
  "accuracy": 0.0,
  "anchors_used": 0,
  "events_used": 0,
  "duration_ms": 0.0,
  "error": "string (optional)"
}
```

#### memory.search_performed
```json
{
  "query": "string",
  "layers_searched": ["string"],
  "results_count": 0,
  "duration_ms": 0.0
}
```

#### memory.timeline_generated
```json
{
  "observer_id": "uuid",
  "start_time": "ISO-8601",
  "end_time": "ISO-8601",
  "event_count": 0,
  "snapshot_count": 0
}
```

#### memory.anchor_created / memory.anchor_expired
```json
{
  "anchor_id": "uuid",
  "observer_id": "uuid",
  "timestamp": "ISO-8601",
  "ttl_seconds": 0
}
```

---

## Event Type Summary

| Domain | Count | Priority Range |
|--------|-------|---------------|
| `observer.*` | 16 | 0–3 |
| `attractor.*` | 8 | 1–3 |
| `entropy.*` | 8 | 0–3 |
| `repair.*` | 8 | 0–3 |
| `system.*` | 13 | 0–3 |
| `operator.*` | 11 | 0–2 |
| `chat.*` | 6 | 0–2 |
| `topology.*` | 5 | 0–2 |
| `memory.*` | 11 | 0–3 |
| **Total** | **86** | **0–3** |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-16 | Initial taxonomy — 86 event types across 9 domains |
