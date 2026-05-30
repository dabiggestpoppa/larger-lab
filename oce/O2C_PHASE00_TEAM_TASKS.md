# O2C + OCE Phase 00 — Team Tasks

> **Generated:** 2026-05-30
> **Lead:** CC2 (Planning) → CC1 (Execution Lead)
> **Status:** 📋 Ready for Build
> **Depends on:** O-7 Persistent Field (complete) | V3 Phases 1-11 (complete)

---

## PHASE 00 — COGNITIVE FILESYSTEM FOUNDATION

### Objective
Turn O2C from conversation orchestration into persistent operational intelligence. Build the filesystem cognition layer that makes every agent execution leave behind distilled operational knowledge.

### Core Shift
```
OLD: User asks → System responds → Dies
NEW: Agents execute → Trace → Distill → Store → Retrieve → Improve
```

---

## 🔵 CC1 (Claude Code) — Core Build Lead

### Primary Responsibilities
- Phase 00 architecture implementation
- Vault writer, compressor, linker components
- Integration with existing OCE backend
- Phase gate management

### Tasks
#### Phase 0A — Vault Writer
- [ ] **O2C-0A-1** Create `core/obsidian/vault_writer.py` — write_note(), list_notes(), get_note()
- [ ] **O2C-0A-2` Create vault directory structure (`/O2C-VAULT/`)
- [ ] **O2C-0A-3` Write tests for vault_writer (create, read, update, delete notes)

#### Phase 0B — Compressor
- [ ] **O2C-0B-1** Create `core/obsidian/compressor.py` — compress_trace(), extract_signal()
- [ ] **O2C-0B-2` Implement noise filtering (remove fluff, chain-of-thought, conversational noise)
- [ ] **O2C-0B-3` Write tests for compressor (raw trace → compressed markdown)

#### Phase 0C — Linker
- [ ] **O2C-0C-1** Create `core/obsidian/linker.py` — auto_link(), get_related(), build_graph()
- [ ] **O2C-0C-2` Implement `[[WikiLink]]` auto-detection and creation
- [ ] **O2C-0C-3` Write tests for linker (link detection, graph building)

#### Phase 0F — Execution Journal
- [ ] **O2C-0F-1** Create `core/execution/journal.py` — log_step(), get_journal(), summarize()
- [ ] **O2C-0F-2` Implement journal compression (raw steps → operational summary)
- [ ] **O2C-0F-3` Write tests for journal (logging, retrieval, compression)

---

## 🟠 OC2 (OWL) — Orchestrator / Integration

### Primary Responsibilities
- Coordinate Phase 00 build across agents
- Integration with existing OCE observer runtime
- Monitor progress, detect blockers, escalate to MAD

### Tasks
- [ ] **O2C-OC2-1** Review Phase 00 architecture against existing OCE patterns
- [ ] **O2C-OC2-2** Map Phase 00 components to existing OCE backend structure
- [ ] **O2C-OC2-3** Coordinate agent assignments and phase gates
- [ ] **O2C-OC2-4** Update team-chat.md with Phase 00 progress

---

## 🟡 AS (Assistant Manager) — Skill System + Taxonomy

### Primary Responsibilities
- Skill system directory structure and first skills
- Doctrine taxonomy enforcement
- Note standard validation

### Tasks
#### Phase 0D — Skill System
- [ ] **O2C-0D-1** Create `skills/` directory structure with categories
- [ ] **O2C-0D-2` Create first skill: `skills/observer/chat_response/` (fixes the static response issue)
- [ ] **O2C-0D-3` Create skill template: SKILL.md + heuristics.md + failures.md + patterns.md

#### Phase 0H — Doctrine Taxonomy
- [ ] **O2C-0H-1** Create taxonomy enforcement module (`core/obsidian/taxonomy.py`)
- [ ] **O2C-0H-2` Implement vault structure validation (prevent entropy landfill)
- [ ] **O2C-0H-3` Write tests for taxonomy enforcement

#### Phase 0I — Note Standard
- [ ] **O2C-0I-1** Create note validator (`core/obsidian/note_standard.py`)
- [ ] **O2C-0I-2` Implement CAUSE/FIX/RESULT/LINKS validation
- [ ] **O2C-0I-3` Write tests for note standard validation

---

## 🔴 PM (Polymorph) — Skill Loader + Debugging

### Primary Responsibilities
- Skill loader implementation
- Debugging and testing
- Tool integration

### Tasks
#### Phase 0E — Skill Loader
- [ ] **O2C-0E-1** Create `core/skills/loader.py` — load_skill(), classify_task(), inject_context()
- [ ] **O2C-0E-2` Implement task classification (map task → relevant skills)
- [ ] **O2C-0E-3` Write tests for skill loader (classification, injection)

#### Testing + Debugging
- [ ] **O2C-PM-1** Test vault_writer end-to-end (write → read → verify)
- [ ] **O2C-PM-2** Test compressor with real execution traces
- [ ] **O2C-PM-3** Test skill loader with sample tasks

---

## 🟢 RL (Research Lead) — Live Sync + Graph Analysis

### Primary Responsibilities
- Obsidian live sync implementation
- Knowledge graph analysis
- Research on compression algorithms

### Tasks
#### Phase 0G — Live Sync
- [ ] **O2C-0G-1** Implement direct markdown writes to Obsidian vault folder
- [ ] **O2C-0G-2** Create sync monitoring (detect new notes, trigger linking)
- [ ] **O2C-0G-3` Write tests for live sync (write → verify in vault)

#### Research
- [ ] **O2C-RL-1** Research optimal compression ratios for execution traces
- [ ] **O2C-RL-2** Research knowledge graph auto-linking algorithms
- [ ] **O2C-RL-3** Document findings in `O2C-VAULT/research/`

---

## 🔴 PM2 (Polymorph 2) — Frontend Integration

### Primary Responsibilities
- OCE frontend integration with O2C vault
- Vault visualization in OCE chat interface
- Graph visualization

### Tasks
- [ ] **O2C-PM2-1** Add vault viewer component to OCE frontend
- [ ] **O2C-PM2-2** Add knowledge graph visualization (Mermaid or D3)
- [ ] **O2C-PM2-3** Add skill browser to OCE frontend

---

## 🟦 Copilot — Test Monitoring

### Primary Responsibilities
- Test suite monitoring
- Autopilot validation
- CI/CD integration

### Tasks
- [ ] **O2C-CP-1** Create Phase 00 test suite runner
- [ ] **O2C-CP-2** Monitor test coverage across all Phase 00 components
- [ ] **O2C-CP-3** Report test results to team-chat.md

---

## PHASE 00 GATE CHECKLIST

Before advancing to Phase 1, ALL must be true:

- [ ] Vault writer can create/read/update/delete markdown notes
- [ ] Compressor converts raw traces to operational markdown
- [ ] Linker auto-generates `[[WikiLinks]]` between related notes
- [ ] Skill system has at least 1 working skill with full structure
- [ ] Skill loader can classify tasks and inject relevant skills
- [ ] Execution journal tracks agent actions and compresses them
- [ ] Live sync writes to Obsidian vault folder
- [ ] Taxonomy enforcement prevents vault entropy
- [ ] Note validator enforces CAUSE/FIX/RESULT/LINKS
- [ ] All components have tests
- [ ] OCE frontend can view vault contents

---

## FILES TO CREATE

| File | Agent | Purpose |
|------|-------|---------|
| `core/obsidian/__init__.py` | CC1 | Package init |
| `core/obsidian/vault_writer.py` | CC1 | Write structured markdown |
| `core/obsidian/compressor.py` | CC1 | Compress execution traces |
| `core/obsidian/linker.py` | CC1 | Auto-link knowledge graph |
| `core/obsidian/taxonomy.py` | AS | Enforce vault structure |
| `core/obsidian/note_standard.py` | AS | Validate note format |
| `core/skills/__init__.py` | PM | Skills package |
| `core/skills/loader.py` | PM | Load/inject skills |
| `core/execution/__init__.py` | CC1 | Execution package |
| `core/execution/journal.py` | CC1 | Track agent execution |
| `skills/observer/chat_response/SKILL.md` | AS | First skill (static response fix) |
| `O2C-VAULT/` | RL | Vault directory structure |
| `oce/frontend/vault-viewer.tsx` | PM2 | Vault viewer component |
| `oce/frontend/graph-viz.tsx` | PM2 | Knowledge graph visualization |
