# 📚 Research Mesh — Phase 1+2+3

> **Status:** Complete | **Tests:** 106/106 passing | **Components:** Ingestion + Distillation + Agents

---

## Overview

The Research Mesh is the autonomous research ingestion, distillation, and knowledge synthesis system. It continuously ingests scientific literature, distills papers into operational doctrine, and spawns research agents on detected knowledge gaps.

**Entry Point:** `core/research/__init__.py`  
**API:** `/api/v1/research/*` (via OCE backend)  
**Vault:** `C:\Users\wifik\Downloads\o2c\research`

---

## Architecture

```mermaid
graph TB
    subgraph "Ingestion Layer (Phase 1.1)"
        OA[OpenAlex API] --> CLIENT[OpenAlex Client]
        ARXIV[arXiv API] --> ARXIV_CLIENT[arXiv Client]
        S2[Semantic Scholar] --> S2_CLIENT[S2 Client]
        
        CLIENT --> CACHE[SQLite Cache + Dedup]
        ARXIV_CLIENT --> CACHE
        S2_CLIENT --> CACHE
        
        CACHE --> RATE[Rate Limiter<br/>Token bucket + backoff]
        CACHE --> SCHED[Scheduler<br/>APScheduler cron]
    end
    
    subgraph "Parser Layer (Phase 1.2)"
        CACHE --> PARSER[Parser Router]
        PARSER --> ENGINES[Extraction Engines]
        ENGINES --> COGNITION[Cognition Objects]
    end
    
    subgraph "Semantic Memory (Phase 1.3-1.4)"
        COGNITION --> CHUNK[Semantic Chunker]
        CHUNK --> EMBED[Embedding Engine]
        EMBED --> VECTOR[(Vector Store)]
    end
    
    subgraph "Knowledge Graph (Phase 1.5)"
        COGNITION --> ENTITIES[Entity Extractor]
        ENTITIES --> GRAPH[(Graph Store)]
        GRAPH --> ONTOLOGY[Ontology Engine]
        ONTOLOGY --> GAPS[Gap Detector]
    end
    
    subgraph "Distillation (Phase 2)"
        CACHE --> DISTILLER[Research Distiller]
        DISTILLER --> CAUSE[CAUSE:<br/>What problem exists?]
        DISTILLER --> METHOD[METHOD:<br/>How did they solve it?]
        DISTILLER --> RESULT[RESULT:<br/>What changed?]
        DISTILLER --> LIMIT[LIMITATIONS:<br/>Where does it fail?]
        DISTILLER --> APPLY[APPLICATION:<br/>How can OCE/PO use this?]
        DISTILLER --> LINKS[LINKS:<br/>[[Related Concepts]]
        
        CAUSE --> VAULT[Vault Writer]
        METHOD --> VAULT
        RESULT --> VAULT
        LIMIT --> VAULT
        APPLY --> VAULT
        LINKS --> VAULT
        
        DISTILLER --> DOCTRINE[Doctrine Builder]
        DOCTRINE --> DOCTRINE_NOTES[Doctrine Notes]
    end
    
    subgraph "Autonomous Research (Phase 3)"
        GAPS --> RESEARCH_AGENT[Research Agent]
        RESEARCH_AGENT --> TASK_GEN[Task Generator]
        TASK_GEN --> QUEUE[Task Queue]
        QUEUE --> EVALUATOR[Evaluator]
        EVALUATOR --> SYNTHESIS[Synthesis Engine]
        SYNTHESIS --> CONSENSUS[Consensus Layer]
        CONSENSUS --> NEW_DOCTRINE[New Doctrine]
        NEW_DOCTRINE --> VAULT
    end
```

---

## Layer Gates

| Gate | Requirement | Status |
|------|-------------|--------|
| **L1 GATE** | 500 papers ingested, dedup verified, all L1 tests pass | ✅ |
| **L2 GATE** | 500+ graph nodes, ≥50 papers distilled, ≥1 doctrine extracted | ✅ |
| **L3 GATE** | First autonomous research cycle completes end-to-end | ✅ |
| **L4 GATE** | OCE API + frontend pages live | ✅ |

---

## Hard Rules

| Rule | Enforcement |
|------|-------------|
| $2/day LLM spend cap | Fail-closed |
| 200 vault writes/day cap | Cache layer |
| Max 3 concurrent research agents | Queue layer |
| All agent actions logged | Execution journal |
| Every paper note format | CAUSE/METHOD/RESULT/LIMITATIONS/APPLICATION/LINKS |

---

## Ingestion Sources

| Source | Client | API |
|--------|--------|-----|
| OpenAlex | `openalex_client.py` | https://api.openalex.org/works |
| arXiv | `arxiv_client.py` | https://export.arxiv.org/api/query |
| Semantic Scholar | `s2_client.py` | https://api.semanticscholar.org/ |

---

## Distillation Format

Every distilled paper produces:

```markdown
---
object_id: <uuid>
source: <paper_title>
year: <year>
tags: [paper, domain/subdomain]
relevance: <0-1>
---

# <Title>

**Authors:** <authors>

## CAUSE
What problem exists?

## METHOD
How did they solve it?

## RESULT
What changed?

## LIMITATIONS
Where does it fail?

## APPLICATION
How can OCE/PO use this?

## LINKS
- [[Related Concept 1]]
- [[Related Concept 2]]
```

---

## Vault Structure

```
O2C-VAULT/research/
├── papers/           # Raw paper notes
├── distilled/        # Distilled insights
├── concepts/         # Concept notes
├── equations/        # Extracted equations
├── frameworks/       # Framework notes
├── methodologies/    # Method notes
├── contradictions/   # Conflicting findings
├── synthesis/        # Multi-source synthesis
└── doctrine/         # Stable operational doctrine
    ├── market_structure/
    ├── cognition/
    ├── systems/
    ├── topology/
    └── coordination/
```

---

## Agent System

| Agent | Location | Purpose |
|-------|----------|---------|
| Gap Detector | `agents/gap_detector.py` | Detect knowledge gaps |
| Research Agent | `agents/research_agent.py` | Self-directed research |
| Task Generator | `agents/task_gen.py` | Generate research tasks |
| Evaluator | `agents/evaluator.py` | Evaluate research quality |
| Router | `agents/router.py` | Route tasks to agents |
| Lifecycle | `agents/lifecycle.py` | Agent lifecycle management |
| Queue | `agents/queue.py` | Task queue with concurrency limits |
| SRRA Adapter | `agents/srra_adapter.py` | SRRA integration |

---

## Testing

```bash
# Run all research tests
python -m pytest core/research/ingestion/tests/ core/research/distillation/tests/ core/research/agents/tests/ -v

# Run specific layer
python -m pytest core/research/ingestion/tests/ -v
python -m pytest core/research/distillation/tests/ -v
python -m pytest core/research/agents/tests/ -v
```

**Tests:** 106/106 passing

---

## Related Documents

- `ingestion/README.md` — Ingestion layer details
- `distillation/README.md` — Distillation engine details
- `agents/README.md` — Agent system details
- `../../parser/README.md` — Parser orchestration
- `../../semantic/README.md` — Semantic memory
- `../../knowledge/graph/README.md` — Knowledge graph
- `../../ARCHITECTURE.md` — Full system architecture
- `../../../docs/plans/O2C-RESEARCH-MESH.md` — Research mesh plan
