# ADR-001: OCE Architecture — Event Fabric + Observer Runtime + Structural Memory

## Status: Accepted
## Date: 2026-05-16

## Context
The Operator Continuity Engine (OCE) needed a persistent, queryable memory system that could maintain operational continuity across sessions and agents.

## Decision
Implement a three-layer memory architecture:
1. **Event Fabric** — Real-time event streaming backbone (Phase 2)
2. **Observer Runtime** — Lifecycle management for specialized agents (Phase 3)
3. **Structural Memory** — Three-layer persistent storage (Phase 4)

## Consequences
- Events flow through topology-aware routing to observers
- Observers maintain local state with sparse synchronization
- Memory is automatically compressed and expired based on TTL
- 101 tests validate the entire pipeline

## Alternatives Considered
- Single flat MEMORY.md file (rejected: doesn't scale, no query capability)
- External vector DB (rejected: adds operational complexity)
- Pure event sourcing (rejected: too expensive to reconstruct state)
