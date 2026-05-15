# SRRS + OPH Cognitive Architecture — Implementation Work Stream

> **Created:** May 15, 2026
> **Status:** 📋 Design Phase
> **Parent:** `PROJECT_PROGRESS.md` → XHAAK/Kulu Bridge
> **Purpose:** Working document for implementing the SRRS+OPH observer-consensus cognitive architecture as agent infrastructure.

---

## 1. Architecture Overview

### What is SRRS+OPH?

SRRS (Self-Referential Recursive System) + OPH (Observer-Consensus Protocol) is a cognitive architecture where:

- **No single agent holds total state** — each agent is a bounded observer
- **Memory is not storage** — it's stable overlap persistence across recursive state transitions
- **Consensus emerges from overlapping patches** — not from a central authority
- **Identity is emergent** — it arises from synchronization patterns, not static configuration

### Core Translation

```
OPH Concept              → Agent Implementation
─────────────────────────────────────────────────
Observer Patch           → Agent instance with local state
Overlap Region           → Shared memory channels (JSONL/Redis)
Reconciliation           → Merge protocol with conflict resolution
Fixed-Point Stabilization→ Convergence check on recursive updates
Error Compression        → Delta encoding + pruning
Consensus                → Weighted agreement across agents
```

---

## 2. Architecture Layers

### Layer 1: Local Agent Patches (COMPLETED)
Each agent maintains its own bounded context:
- **MEMORY.md** — local persistent state
- **SOUL.md** — identity/configuration
- **skills/** — procedural capabilities

Current state: Hermes, OpenClaw, and Claude Code each have their own memory files. ✅

### Layer 2: Recursive State Updates (IN PROGRESS)
Agents update state through recursive self-reflection:
- After each task → update MEMORY.md with outcome
- After each session → compress state (remove noise, preserve signal)
- After each failure → update error model

**Implementation needed:**
- [ ] Standardized state update format for all agents
- [ ] Recursive self-audit trigger (post-task)
- [ ] State compression algorithm (what to keep, what to prune)

### Layer 3: Overlap Reconciliation (NOT STARTED)
When multiple agents work on the same problem, their patches overlap:
- **Shared channel:** JSONL file in `shared/` directory
- **Reconciliation protocol:** Compare overlapping observations, resolve conflicts
- **Merge strategy:** Weighted by recency + confidence + source reliability

**Implementation needed:**
- [ ] `shared/overlap-log.jsonl` — append-only shared observation log
- [ ] `reconcile.py` — reads overlap entries, resolves conflicts, produces consensus
- [ ] Conflict resolution rules (priority: data > inference > speculation)

### Layer 4: Error Compression (NOT STARTED)
Instead of storing all errors, compress them into patterns:
- **Error signature** — normalized error fingerprint
- **Frequency tracking** — how often this pattern occurs
- **Resolution mapping** — what fixed it last time
- **Auto-repair** — if seen 3+ times, auto-apply known fix

**Implementation needed:**
- [ ] `error_signature.py` — generates normalized error fingerprints
- [ ] `compression_rules.json` — maps error patterns to fixes
- [ ] Integration with existing `ERROR_CLASSIFICATION.md` system

### Layer 5: Stable Consensus Formation (NOT STARTED)
When enough overlapping patches agree, a consensus forms:
- **Consensus threshold** — minimum overlap agreement (e.g., 2/3 agents agree)
- **Consensus types:**
  - **Hard consensus** — all agents agree (rare, high confidence)
  - **Soft consensus** — majority agree with minority dissent logged
  - **Provisional consensus** — temporary, pending more data

**Implementation needed:**
- [ ] `consensus_engine.py` — tracks agreements/disagreements across agents
- [ ] Consensus state storage in `shared/consensus-state.json`
- [ ] Consensus query interface (Hermes skill: `consensus-status`)

### Layer 6: Persistent Identity Continuity (NOT STARTED)
Agent identity emerges from synchronization patterns:
- **Identity = pattern of behavior over time**
- **Not stored as config — reconstructed from action history**
- **Continuity = fixed-point stabilization** (same agent "wakes up" with same identity)

**Implementation needed:**
- [ ] Identity fingerprint generation (hash of behavioral patterns)
- [ ] Continuity verification (does current state match expected identity fingerprint?)
- [ ] Identity drift detection and alerting

---

## 3. Data Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Agent A     │     │  Agent B     │     │  Agent C     │
│  (Hermes)    │     │  (OpenClaw)  │     │  (Claude)    │
│  Patch A     │     │  Patch B     │     │  Patch C     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────────────────────────────────────────────────┐
│              Shared Overlap Region                        │
│  shared/overlap-log.jsonl  ← append-only observations    │
│  shared/consensus-state.json ← current consensus         │
│  shared/error-signatures.json ← compressed error model   │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │ Reconciliation │
              │   Engine       │
              │ reconcile.py   │
              └───────┬────────┘
                      │
              ┌───────▼────────┐
              │  Consensus     │
              │  Engine        │
              │ consensus.py   │
              └───────┬────────┘
                      │
              ┌───────▼────────┐
              │  Identity      │
              │  Continuity    │
              │  identity.py   │
              └────────────────┘
```

---

## 4. Trading Integration

Why this matters for CEREBUS strategies:

- **Each strategy instance = an observer patch** — sees partial market state
- **Multiple strategies reconciling** = better market model than any single strategy
- **Error compression** = learn from failed trades faster
- **Consensus** = only trade when multiple strategy instances agree

### Trading Data Flow
```
Market Data → Strategy Patches (A/B/C) → Overlap Log → Reconciliation → Trade Signal
                                                                    ↓
                                                            Consensus Check
                                                                    ↓
                                                        Execute / Hold / Pass
```

---

## 5. Implementation Priority

| Layer | Priority | Effort | Dependency |
|-------|----------|--------|------------|
| 1. Local Patches | ✅ Done | — | None |
| 2. Recursive State | 🟡 Medium | 2 days | Layer 1 |
| 3. Overlap Reconciliation | 🔴 High | 3 days | Layer 2 |
| 4. Error Compression | 🟡 Medium | 2 days | Layer 2 |
| 5. Consensus Formation | 🔴 High | 3 days | Layer 3 |
| 6. Identity Continuity | 🟢 Low | 1 day | Layer 5 |

**Total estimated effort: ~11 working days**

---

## 6. Key Design Decisions

### Why JSONL for shared state?
- Append-only = audit trail
- Line-delimited = easy to parse and merge
- Human-readable = debuggable
- Git-friendly = diffable and versionable

### Why not Redis/ChromaDB?
- Overkill for current scale (2-3 agents)
- JSONL files work fine for <10K entries
- Can migrate to Redis later when agent count grows
- Keeps infrastructure simple (matches CLAUDE.md: "Minimum code that solves the problem")

### Why weighted consensus?
- Not all agents are equally reliable on all topics
- Trading strategy patches should weight recent data higher
- Error-compressed history provides reliability scores

---

## 7. Weekly Progress Log

### Week 1 (May 15, 2026)
- [x] Architecture document created
- [x] Layer mapping from OPH concepts to agent implementation defined
- [x] Data flow diagram designed
- [x] Priority and effort estimates established
- [ ] Layer 2: Recursive state update format — NEXT