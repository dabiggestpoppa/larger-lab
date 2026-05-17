# Memory Architecture — OCE Structural Memory

## Three-Layer Architecture

### WORK (Active Context)
- Current task context
- Active observer state
- Recent events (last 24h)
- In-progress decisions
- **TTL**: 24 hours (auto-expire)
- **Location**: `memory/work/`

### LEARNED (Completed Work)
- Completed tasks and lessons learned
- Resolved bugs and their fixes
- Discovered patterns and heuristics
- **TTL**: 30 days (then promoted to KNOWLEDGE)
- **Location**: `memory/learned/`

### KNOWLEDGE (Reference)
- Architecture decisions (ADRs)
- System schemas and APIs
- Entity profiles (people, projects, systems)
- **TTL**: Permanent (manually curated)
- **Location**: `memory/knowledge/`

## Directory Structure
```
memory/
├── README.md           # This file
├── work/               # Active context (auto-managed)
│   ├── current-task.md
│   ├── active-observers.md
│   └── recent-events.md
├── learned/            # Completed work (auto-promoted)
│   ├── lessons/
│   ├── patterns/
│   └── fixes/
├── knowledge/          # Reference (manually curated)
│   ├── adrs/           # Architecture Decision Records
│   ├── schemas/        # System schemas
│   ├── entities/       # People, projects, systems
│   └── wiki/           # LLM Wiki export
├── people/             # People profiles
├── projects/           # Project state
└── log.md              # Chronological operation record
```

## Operations

### Ingest
- Events from Event Fabric → WORK layer
- Completed tasks → LEARNED layer
- Verified facts → KNOWLEDGE layer

### Query
- Semantic search across all layers
- Timeline queries per observer/entity
- Graph traversal for related concepts

### Compress
- WORK → LEARNED: After task completion
- LEARNED → KNOWLEDGE: After 30 days + verification
- Auto-expire: Based on TTL

### Export
- Wiki markdown (for LLM Wiki)
- JSON (for API consumers)
- YAML (for config management)
