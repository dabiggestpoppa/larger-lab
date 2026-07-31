# Phase 6-9 Resources & GitHub Repo Assessment

> **Assigned to:** AS (Assistant Manager)
> **Task:** Evaluate each repo/paper for SRRA-OPH integration potential
> **Output:** Write assessment to `srrs_opc/docs/resource_assessment.md`

---

## GitHub Repos to Evaluate

### Memory / Continuity Layer

| Repo | URL | SRRA Mapping | Priority |
|------|-----|-------------|----------|
| Neo4j Agent Memory | https://github.com/neo4j-labs/agent-memory | Reconstruction mesh, continuity graph, observer relation topology | 🔴 HIGH |
| MemoryGraph MCP | https://github.com/memory-graph/memory-graph | Local observer memory, relationship persistence, sparse reconstruction | 🔴 HIGH |
| Graphonomous | https://graphonomous.com/ | Attractor stabilization, reinforcement weighting, adaptive retrieval (Phases 5-8) | 🔴 HIGH |
| ArqonDB | https://arqondb.com/ | OPH temporal loops, SRRA continuity reconstruction, entropy-aware persistence | 🔴 HIGH |

### Orchestration Layer

| Repo | URL | SRRA Mapping | Priority |
|------|-----|-------------|----------|
| AgentMesh | https://github.com/hupe1980/agentmesh | SRRA synchronization fields, bounded observer patches, distributed cognition topology | 🔴 HIGH |
| Open Multi-Agent | https://github.com/open-multi-agent/open-multi-agent | Execution routing layer, DAG decomposition, task graphing | 🟡 MEDIUM |
| orxhestra | https://orxhestra.com/ | Instrumentation layer, event streaming, workflow composition | 🟡 MEDIUM |
| Skillrunner | https://skillrunner.dev/ | Phase 9 entropy economics, cost-aware routing, model selection | 🟡 MEDIUM |

### Memory Palace / Spatial Cognition

| Repo | URL | SRRA Mapping | Priority |
|------|-----|-------------|----------|
| OpenLoci | https://openloci.org/ | Observer geometry, continuity anchoring, environmental cognition | 🟢 LOW |
| GraphPalace | https://graphpalace.org/ | SRRA reinforcement geometry, observer trails, adaptive reconstruction | 🟡 MEDIUM |

### Research Papers

| Paper | URL | SRRA Mapping | Priority |
|-------|-----|-------------|----------|
| SAGE (evolving graph memory) | https://arxiv.org/abs/2605.12061 | Evolving graph memory, recursive reader/writer adaptation, structure-aware retrieval | 🔴 HIGH |
| Verified Multi-Agent Orchestration | https://arxiv.org/abs/2603.11445 | SRRA repair fields, continuity verification, reconstruction safety | 🔴 HIGH |
| Topology Matters | https://arxiv.org/abs/2512.04668 | Graph topology determines leakage/coherence/synchronization economics | 🔴 HIGH |

---

## Assessment Criteria

For each resource, evaluate:
1. **SRRA Alignment** — How well does it map to SRRA-OPH principles?
2. **Integration Effort** — How hard is it to integrate?
3. **Phase Fit** — Which phase does it contribute to?
4. **Dependency Risk** — Does it create unwanted coupling?
5. **Recommendation** — Use as-is / Adapt / Reference only / Skip

---

## Key Insight from Plan

> "You are not building an AI app. You are building a coherence operating system for distributed cognition."

The repos above are **organs/subsystems/infrastructure primitives** — NOT the core intelligence.
The SRRA substrate is the core. These resources become components within it.

---

## Deliverables

1. `srrs_opc/docs/resource_assessment.md` — Full assessment of each resource
2. `srrs_opc/docs/integration_plan.md` — Which repos to integrate, in what order
3. Update `CODEMAP.md` with external dependency diagram
4. Update `progress/assistant-progress.md` with findings
