# 🕸️ Knowledge Graph — Phase 1.5

> **Status:** Complete | **Components:** Entities + Relationships + Graph Store + Ontology

---

## Overview

The Knowledge Graph engine transforms semantic retrieval into conceptual cognition. It builds entity-relationship topology from parsed content, enabling inference, abstraction, and gap detection.

---

## Architecture

```mermaid
graph TB
    COGNITION[Cognition Object] --> EXTRACT[Entity Extractor]
    
    subgraph "Entity Extraction (Phase 1.5.1)"
        EXTRACT --> NOUN[Noun/Concept Extraction]
        NOUN --> CANON[Canonicalization]
        CANON --> CLASSIFY[Entity Classification]
        CLASSIFY --> ENTITIES[Entities<br/>concept/system/tool/person/protocol/domain]
    end
    
    subgraph "Relationship Mapping (Phase 1.5.2)"
        ENTITIES --> COOC[Co-occurrence Analysis]
        COOC --> SEM[Semantic Reasoning]
        SEM --> CONF[Confidence Scoring]
        CONF --> EDGES[Typed Edges<br/>depends_on/powers/extends/feeds/contradicts]
    end
    
    subgraph "Graph Store (Phase 1.5.4)"
        EDGES --> GRAPH[(Graph Store<br/>NetworkX → Neo4j)]
        ENTITIES --> GRAPH
        GRAPH --> TRAVERSAL[Graph Traversal<br/>Pathfinding]
        GRAPH --> PERSIST[JSON Persistence]
    end
    
    subgraph "Ontology (Phase 1.5.3)"
        GRAPH --> ONTO[Ontology Engine]
        ONTO --> HIERARCHY[Concept Hierarchy<br/>Parent-Child Trees]
        HIERARCHY --> MERM[Mermaid Export]
    end
    
    subgraph "Inference (Phase 1.5.6)"
        GRAPH --> INFER[Inference Engine]
        INFER --> TRANS[Transitive Reasoning]
        INFER --> EMERGE[Emergent Insights]
    end
    
    subgraph "Abstraction (Phase 1.5.7)"
        INFER --> ABSTRACT[Abstraction Engine]
        ABSTRACT --> META[Meta-Concepts<br/>Higher-order structures]
    end
    
    subgraph "Gap Detection (Phase 1.5.8)"
        GRAPH --> GAPS[Gap Detector]
        GAPS --> VOIDS[Topology Voids]
        GAPS --> CONTRADICTS[Contradictions]
        VOIDS --> RESEARCH[Research Targets]
        CONTRADICTS --> RESEARCH
    end
```

---

## Entity Types

| Type | Description | Example |
|------|-------------|---------|
| `concept` | Abstract idea | "semantic memory", "vector cognition" |
| `system` | Software system | "OCE", "SRRA", "OpenAlex" |
| `framework` | Methodology | "Phase 1.2", "Parser Router" |
| `tool` | Specific tool | "markitdown", "codegraph" |
| `protocol` | Standard/protocol | "MCP", "REST" |
| `domain` | Knowledge domain | "AI", "Quant Finance" |
| `person` | Author, researcher | Paper authors |

## Relationship Types

| Type | Meaning | Example |
|------|---------|---------|
| `depends_on` | Dependency | OCE → observer_runtime |
| `powers` | Capability | markitdown → Parser Router |
| `extends` | Inheritance | OCE → SRRA |
| `related_to` | Soft association | semantic memory ↔ vector cognition |
| `supports` | Evidence | test results → engine validation |
| `contradicts` | Semantic conflict | finding A ↔ finding B |
| `feeds` | Data flow | OpenAlex → research ingestion |
| `abstracts` | Conceptual compression | vector DB + embeddings → semantic cognition |

---

## Usage

```python
from core.knowledge.graph import EntityExtractor, RelationshipMapper, GraphStore, OntologyEngine

# Extract entities
extractor = EntityExtractor()
entities = extractor.extract(text, source_ref="paper_123")

# Map relationships
mapper = RelationshipMapper()
relationships = mapper.map_relationships(entities, text)

# Store in graph
graph = GraphStore()
for entity in entities:
    graph.add_entity(entity)
for rel in relationships:
    graph.add_relationship(rel)

# Query
path = graph.find_path("OpenAlex", "OCE")
# → ["OpenAlex", "research ingestion", "Cognition Objects", "Semantic Memory", "Knowledge Graph", "OCE"]

# Ontology
ontology = OntologyEngine(graph_store=graph)
tree = ontology.build_ontology()
mermaid = ontology.to_mermaid()

# Gap detection
gaps = ontology.detect_gaps()
```

---

## Graph Queries

```python
# Find path between concepts
path = graph.find_path("OpenAlex", "OCE")

# Get neighbors
neighbors = graph.get_neighbors("semantic memory")

# Get all entities in domain
entities = graph.query_nodes(domain="AI Systems")

# Get all relationships
edges = graph.get_all_relationships()
```

---

## Persistence

Graph is stored as JSON for portability:

```python
graph.save("graph.json")  # Save
graph.load("graph.json")  # Load
```

For production scaling, the GraphStore supports Neo4j backend.

---

## Related Documents

- `../README.md` — Core cognition substrate
- `../../semantic/README.md` — Semantic memory layer
- `../../research/README.md` — Research mesh
- `../../../ARCHITECTURE.md` — Full system architecture
