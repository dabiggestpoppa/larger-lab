# Phase 6-9 Resource Assessment

> **Author:** AS (Assistant Manager)
> **Date:** 2026-05-16
> **Task:** Evaluate GitHub repos and research papers for SRRA-OPH integration

---

## Executive Summary

Assessment of 12 external resources against SRRA-OPH principles. **8 recommended for integration**, **2 deferred**, **2 require further investigation**. Priority order: Memory layer → Orchestration layer → Spatial cognition.

---

## Memory / Continuity Layer

### Neo4j Agent Memory — 🔴 HIGH Priority — ✅ RECOMMENDED

**SRRA Alignment:** 9/10
- Directly maps to Phase 2 reconstruction mesh and Phase 5 continuity graph
- Graph-native storage aligns with "topology determines cognition"
- Agent memory model maps to observer state persistence
- Relationship topology maps to collar overlap regions

**Integration Effort:** MEDIUM
- Requires Neo4j deployment (Docker available)
- Python driver available (`neo4j` package)
- Need to map SRRA observer model to Neo4j node/relationship schema

**Recommendation:** Use as the primary graph store for observer topology and continuity reconstruction. Replace SQLite-based `recovery_anchors.py` with Neo4j backend in Phase 5.

---

### MemoryGraph MCP — 🔴 HIGH Priority — ✅ RECOMMENDED

**SRRA Alignment:** 8/10
- Local observer memory with relationship persistence
- Sparse reconstruction via graph traversal
- MCP protocol aligns with Phase 4 instrumentation abstraction

**Integration Effort:** LOW
- MCP server — integrates via standard protocol
- Can run alongside existing Python codebase
- Maps to observer memory interface

**Recommendation:** Use as the MCP interface layer for observer memory. Each observer connects to MemoryGraph MCP for persistent state. Enables Phase 4 substrate independence.

---

### Graphonomous — 🔴 HIGH Priority — ✅ RECOMMENDED

**SRRA Alignment:** 9/10
- Attractor stabilization maps directly to Phase 5 temporal attractors
- Reinforcement weighting aligns with Phase 2 anchor weighting
- Adaptive retrieval maps to Phase 6 recursive self-modeling

**Integration Effort:** MEDIUM-HIGH
- May require custom integration
- Need to verify API compatibility
- Maps to multiple phases (5, 6, 8)

**Recommendation:** Evaluate API. If compatible, use as the attractor engine for Phase 5 long-horizon continuity. The reinforcement weighting mechanism directly implements "repair-generated persistence."

---

### ArqonDB — 🔴 HIGH Priority — ⚠️ NEEDS INVESTIGATION

**SRRA Alignment:** 7/10 (potential)
- OPH temporal loops align with SRRA continuity reconstruction
- Entropy-aware persistence maps to Phase 9
- Temporal database model may support event sourcing

**Integration Effort:** UNKNOWN
- Need to evaluate API and data model
- May overlap with Neo4j functionality
- Could replace or complement EventStoreDB

**Recommendation:** Investigate further. If temporal query capabilities exceed Neo4j, use as the event store backend. Otherwise, defer to Neo4j.

---

## Orchestration Layer

### AgentMesh — 🔴 HIGH Priority — ✅ RECOMMENDED

**SRRA Alignment:** 9/10
- SRRA synchronization fields map directly to mesh topology
- Bounded observer patches align with mesh node model
- Distributed cognition topology is the core abstraction

**Integration Effort:** MEDIUM
- Go-based; need Python bindings or gRPC
- Maps to Phase 3 adaptive topology
- Could replace custom `dynamic_coupling.py`

**Recommendation:** Evaluate as the primary orchestration substrate. If API is compatible, use AgentMesh as the runtime for observer topology management. This would significantly accelerate Phase 3-4 implementation.

---

### Open Multi-Agent — 🟡 MEDIUM Priority — ✅ RECOMMENDED

**SRRA Alignment:** 7/10
- Execution routing layer maps to Phase 4 workspace integration
- DAG decomposition aligns with observer task graphs
- Task graphing maps to Phase 1 planner patch

**Integration Effort:** LOW-MEDIUM
- Python-based; easy integration
- Maps to execution layer, not core cognition
- Complements AgentMesh

**Recommendation:** Use for task decomposition and execution routing. Delegates to AgentMesh for topology management. Good fit for Phase 4 workspace integration.

---

### orxhestra — 🟡 MEDIUM Priority — ✅ RECOMMENDED

**SRRA Alignment:** 7/10
- Instrumentation layer maps to Phase 4
- Event streaming aligns with Phase 2 event sourcing
- Workflow composition maps to observer coordination

**Integration Effort:** MEDIUM
- Need to evaluate API
- May overlap with Kafka/EventStoreDB
- Good fit for instrumentation abstraction

**Recommendation:** Use as the workflow composition layer for Phase 4. Complements the event sourcing infrastructure. Evaluate API compatibility.

---

### Skillrunner — 🟡 MEDIUM Priority — ✅ RECOMMENDED

**SRRA Alignment:** 8/10
- Phase 9 entropy economics — cost-aware routing
- Model selection aligns with bounded observer cognition
- Skill execution maps to Phase 4 capability fields

**Integration Effort:** LOW-MEDIUM
- Python-based
- Maps to execution layer
- Good fit for capability field abstraction

**Recommendation:** Use as the cost-aware execution router for Phase 4. Implements "coherence-per-resource optimization" from Phase 9. Evaluate API.

---

## Spatial Cognition

### OpenLoci — 🟢 LOW Priority — ⚠️ DEFER

**SRRA Alignment:** 5/10
- Observer geometry interesting but not core
- Continuity anchoring maps to Phase 5
- Environmental cognition is out of scope for current build

**Integration Effort:** HIGH
- Specialized spatial reasoning
- Not critical for Phases 1-5
- Could be valuable for Phase 7+ multi-scale fields

**Recommendation:** Defer to Phase 7+. Interesting for spatial cognition extension but not needed for core build.

---

### GraphPalace — 🟡 MEDIUM Priority — ✅ RECOMMENDED

**SRRA Alignment:** 7/10
- SRRA reinforcement geometry maps to Phase 5 attractors
- Observer trails align with trajectory reconstruction
- Adaptive reconstruction maps to Phase 6 self-modeling

**Integration Effort:** MEDIUM
- Need to evaluate API
- Maps to multiple phases
- Complements Graphonomous

**Recommendation:** Evaluate API. If compatible, use as the trajectory reconstruction engine for Phase 5. The "observer trails" concept directly implements "identity as trajectory."

---

## Research Papers

### SAGE (Evolving Graph Memory) — 🔴 HIGH Priority — ✅ RECOMMENDED

**SRRA Alignment:** 9/10
- Evolving graph memory maps to Phase 2 reconstruction + Phase 5 continuity
- Recursive reader/writer adaptation maps to Phase 6 self-modeling
- Structure-aware retrieval maps to Phase 3 topology-aware routing

**Key Insights for SRRA:**
- Graph structure evolves with use — aligns with adaptive topology
- Reader/writer adaptation implements "repair-generated persistence"
- Structure-aware retrieval implements "topology determines cognition"

**Recommendation:** Implement SAGE-inspired graph memory evolution in Phase 5. Use as the theoretical foundation for observer memory reconstruction.

---

### VMAO (Verified Multi-Agent Orchestration) — 🔴 HIGH Priority — ✅ RECOMMENDED

**SRRA Alignment:** 9/10
- SRRA repair fields map to verification mechanisms
- Continuity verification maps to Phase 5
- Reconstruction safety maps to Phase 4 execution verification

**Key Insights for SRRA:**
- Formal verification of multi-agent protocols
- Safety properties for reconstruction
- Liveness properties for continuity

**Recommendation:** Use VMAO verification techniques for Phase 4 reconstruction-safe execution. Implement formal verification of observer interaction protocols.

---

### Topology Matters — 🔴 HIGH Priority — ✅ RECOMMENDED

**SRRA Alignment:** 10/10
- Graph topology determines leakage/coherence/synchronization economics
- Directly validates SRRA Principle 6: "topology determines cognition"
- Provides mathematical foundation for Phase 3 adaptive topology

**Key Insights for SRRA:**
- Topology quality metrics (spectral gap, betweenness centrality)
- Coherence bounds based on graph structure
- Synchronization cost models based on topology

**Recommendation:** Use as the theoretical foundation for all topology-related design decisions. Implement topology quality monitoring based on paper's metrics.

---

## Integration Plan

### Immediate (This Week)
1. **Neo4j Agent Memory** — Set up Docker instance, design observer schema
2. **MemoryGraph MCP** — Integrate as observer memory interface
3. **AgentMesh** — Evaluate API, plan topology runtime integration

### Short-Term (Week 2-3)
4. **Graphonomous** — Evaluate API, plan attractor engine integration
5. **Skillrunner** — Integrate as cost-aware execution router
6. **SAGE paper** — Implement graph memory evolution prototype

### Medium-Term (Week 4-6)
7. **GraphPalace** — Evaluate for trajectory reconstruction
8. **VMAO paper** — Implement formal verification of observer protocols
9. **Topology Matters paper** — Implement topology quality monitoring

### Deferred
- **ArqonDB** — Investigate further, compare with Neo4j
- **OpenLoci** — Defer to Phase 7+

---

## External Dependency Diagram

```
SRRA-OPH Core
├── Memory Layer
│   ├── Neo4j Agent Memory (graph store)
│   ├── MemoryGraph MCP (MCP interface)
│   ├── Graphonomous (attractor engine)
│   └── SAGE (graph memory evolution)
├── Orchestration Layer
│   ├── AgentMesh (topology runtime)
│   ├── Open Multi-Agent (task routing)
│   ├── orxhestra (workflow composition)
│   └── Skillrunner (cost-aware execution)
├── Verification Layer
│   ├── VMAO (protocol verification)
│   └── Topology Matters (topology metrics)
└── Spatial Layer (Phase 7+)
    └── GraphPalace (trajectory reconstruction)
```
