# Research Mesh Principles

> **Category:** doctrine/meta | Created: 2026-06-06 by CC2
> **Status:** Active — governs all O2C × MAD LABS Research Mesh work
> **Companion docs:** `docs/plans/O2C-RESEARCH-MESH.md` | `progress/O2C-RESEARCH-MESH-TASKS.md`

---

## 1. The Vault Is the Civilization

The primary asset is not the model. The asset is:
- continuity
- memory
- synthesis
- semantic topology

Models are interchangeable. The vault is not. Every research mesh component must ask: **"Does this make the vault smarter?"** If not, it shouldn't be built.

## 2. Compression Creates Intelligence

Raw information has almost zero value. Value emerges from:
- compression
- synthesis
- abstraction
- operationalization
- linkage

The distillation engine is the most important component. Not the API. The API is commodity. Distillation creates asymmetry.

## 3. The Loop Is the System

```
Ingest → Distill → Graph → Detect Gap → Spawn Agent → Research → Update Vault
```

Without the loop, it's just a paper downloader. The loop compounds intelligence. Every component exists to serve the loop.

## 4. Curate Aggressively

Do NOT ingest everything. 15 initial domains. Every paper scored 0-5 on operational relevance. Papers scoring <3 are skipped — they don't enter the vault. The vault is a precious resource.

## 5. Safety Boundaries Are Non-Negotiable

1. **$2/day LLM spend cap** — fail-closed. When the cap is hit, LLM distillation stops. Rule-based distiller continues.
2. **200 vault writes/day cap** — when the cap is hit, no more paper notes. Ingestion continues (metadata only).
3. **Max 3 concurrent research agents** — bounded parallelism.
4. **All agent actions logged to execution journal** — full audit trail.
5. **No autonomous recursive skill mutation** — human review required.
6. **No production deployment without operator approval** — sandbox + staging only.

## 6. Every Note Follows the Standard

```markdown
CAUSE: What problem does this paper address?
METHOD: How did they solve it?
RESULT: What changed? What numbers?
LIMITATIONS: Where does it fail? What assumptions?
APPLICATION: How can OCE/PO use this?
LINKS:
- [[Related Concept 1]]
- [[Related Concept 2]]
- cites:[[Paper X]]

#paper #domain/{subdomain} #year/{year} #operational_relevance/{1-5}
```

No essays. No rambling. No AI sludge. Operational signal only.

## 7. Build on Real Data

OpenAlex and arXiv are free. Always use live APIs. No mocks in production code. Tests may mock, but the real system talks to real sources from day 1.

## 8. Layer Gates Are Real

- **L1 GATE:** 500 papers ingested from 3 sources, dedup verified, all L1 tests pass.
- **L2 GATE:** 500+ graph nodes, ≥50 papers distilled, ≥1 doctrine auto-extracted.
- **L3 GATE:** First autonomous research cycle completes end-to-end.
- **L4 GATE:** OCE API + frontend pages live, operator can browse the mesh.

**No layer starts until the previous layer's gate is passed.** CC posts GATE PASS in team-chat. That's the only signal to start the next layer.

## 9. Agents Are Temporary, the Field Persists

Research agents spawn, execute, and terminate. The field remains. The field accumulates memory and doctrine over time. Design for agent ephemerality.

## 10. Simplicity First

Minimum code that solves the problem. No speculative abstractions. No large architectural pivots. Only build what the plan specifies. If it's not in the plan, it doesn't get built until the plan is updated.

---

## Domain Taxonomy (v1)

| Domain | OpenAlex Query | arXiv Categories |
|--------|---------------|-----------------|
| agent_orchestration | agent orchestration multi-agent | cs.AI, cs.MA |
| memory_systems | memory systems long-term memory neural | cs.AI, cs.LG, cs.CL |
| distributed_cognition | distributed cognition swarm intelligence | cs.AI, cs.MA, cs.NE |
| knowledge_graphs | knowledge graph embedding reasoning | cs.AI, cs.CL, cs.IR |
| vector_retrieval | vector search approximate nearest neighbor | cs.IR, cs.LG, cs.DB |
| reinforcement_learning | reinforcement learning policy optimization | cs.LG, cs.AI, stat.ML |
| attention_mechanisms | attention mechanism transformer | cs.LG, cs.CL, cs.AI |
| inference_optimization | inference optimization quantization pruning | cs.LG, cs.DC, cs.PF |
| llm_systems | large language model LLM systems | cs.CL, cs.AI, cs.LG |
| market_microstructure | market microstructure liquidity | q-fin.TR, q-fin.ST |
| topology_network_theory | network topology graph theory | cs.SI, math.CO, cs.NI |
| entropy_systems | entropy information theory complex systems | cs.IT, math.IT, nlin.CD |
| causal_inference | causal inference causal discovery | cs.LG, stat.ME, cs.AI |
| graph_neural_networks | graph neural network GNN | cs.LG, cs.AI |
| self_supervised_learning | self-supervised learning contrastive | cs.LG, cs.CV, cs.CL |

---

## Cost Controls

| Lever | Limit | Enforcement |
|-------|-------|------------|
| Daily LLM spend | $2 hard cap | AS safety layer, fail-closed |
| Tokens per distillation | 500 input + 300 output | Distiller config |
| Concurrent agents | 3 max | Lifecycle manager |
| Vault writes per day | 200 max | Vault writer gate |
| Failed-task retries | 2 max | Queue manager |
| Graph edge pruning | Top-50 citations per paper | Citation graph builder |

---

## File Layout

```
core/research/
├── __init__.py
├── ingestion/          ← L1: source clients, normalizer, cache, scheduler
│   ├── openalex_client.py      (PM)
│   ├── arxiv_client.py         (PM2)
│   ├── s2_client.py            (PM)
│   ├── sources.py              (CC) ← this file
│   ├── models.py               (CC) ← canonical Paper schema
│   ├── scheduler.py            (RL)
│   ├── cache.py                (PM)
│   ├── rate_limit.py           (PM2)
│   └── tests/
├── distillation/       ← L2: distiller, graph, vault writer, doctrine
│   ├── distiller.py            (CC)
│   ├── concepts.py             (PM)
│   ├── citation_graph.py       (PM2)
│   ├── vault_writer.py         (CC)
│   ├── graph_store.py          (CC)
│   ├── llm_distill.py          (AS)
│   ├── doctrine.py             (AS)
│   ├── contradictions.py       (RL)
│   └── tests/
└── agents/             ← L3: gap detector, research agent, queue
    ├── gap_detector.py         (AS)
    ├── task_gen.py             (PM)
    ├── research_agent.py       (CC)
    ├── evaluator.py            (PM2)
    ├── router.py               (PM2)
    ├── lifecycle.py            (AS)
    ├── queue.py                (CC)
    ├── srra_adapter.py         (CC)
    └── tests/

data/research/
├── papers.db             ← SQLite: raw paper metadata
├── citations.db          ← SQLite: knowledge graph
├── agents.db             ← SQLite: task queue + agent log
└── schema.sql            ← CC

O2C-VAULT/research/
├── papers/{domain}/{year}/{author}_{slug}.md   ← auto-generated
├── concepts/{slug}.md                          ← auto-generated
├── methods/{slug}.md                           ← auto-generated
├── authors/{slug}.md                           ← auto-generated
└── contradictions/{topic}.md                   ← auto-generated

O2C-VAULT/doctrine/{domain}/{topic}.md          ← auto-extracted doctrine
```

---

*This document is the governing philosophy for the research mesh. When in doubt, refer here. When this doc and the plan conflict, the plan wins until this doc is updated.*
