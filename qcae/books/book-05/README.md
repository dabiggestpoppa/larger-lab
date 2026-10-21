# QCAE Book V — Agent & Runtime Architecture

**Canon:** QCAE v0.1  
**Status:** IN BUILD

Book V turns the QCAE doctrine into an executable agent system. Books I–IV defined capability semantics, discovery, proving, acquisition, memory, and monitoring. Book V defines the orchestrator, specialized workers, context isolation, handoffs, failure recovery, standalone runtime, local policy/evidence services, OCE integration contract, and implementation package boundaries.

## Blocks

- Block 12 — Agent Architecture
- Block 13 — Standalone Runtime
- Block 14 — OCE Integration Contract
- Block 15 — Implementation Architecture

## Governing law

> **The agent may reason broadly, but every durable action moves through typed artifacts, bounded authority, and explicit lifecycle transitions.**

QCAE must run independently before OCE is complete, but its contracts and evidence envelopes must be designed so OCE can later replace governance plumbing without rewriting the acquisition engine.

## History discipline

Every chapter and block freeze receives its own commit. Agent architecture is especially sensitive to context pollution and hidden coupling, so later amendments must be narrow, explicit, and traceable.
