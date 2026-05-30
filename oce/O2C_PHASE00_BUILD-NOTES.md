# O2C + OCE Phase 00 — Build Notes

> **Purpose:** Before any agent works, read this to understand core principles, avoid known errors, and stay aligned.
> **Lead:** CC2 (planning) → CC1 (execution)
> **Last Updated:** 2026-05-30
> **Status:** 📋 Planning Complete — Ready for Build

---

## 1. CORE ARCHITECTURAL PRINCIPLE

**Key Theme:** Filesystem cognition > model intelligence.

**Reason:** Models reset. Models forget. Models hallucinate. The filesystem is the only persistent substrate. Every agent execution must leave behind structured operational intelligence — not raw logs, not conversation history, but distilled operational knowledge.

**Aim:** Every component answers: "Does this make the filesystem smarter?" If not, it shouldn't be built.

---

## 2. O2C ≠ CHATBOT

**Key Theme:** O2C is persistent operational intelligence, not conversation orchestration.

**Reason:** The old O2C pattern was: user asks → system responds → dies. The new pattern is: agents execute → trace process → distill learning → store knowledge → retrieve knowledge → improve future spawn.

**Aim:** When building any O2C component, ask: "Does this survive beyond a single conversation?" If not, it's the wrong abstraction.

---

## 3. COMPRESSION IS KING

**Key Theme:** Raw execution noise must become compressed operational abstractions.

**Reason:** Storing full traces = entropy landfill. Storing nothing = amnesia. The compression engine is the most important component — it converts runtime noise into reusable doctrine.

**Aim:** Every execution produces markdown notes, not JSON blobs. Markdown is universal, LLM-parseable, graph-linkable, and portable.

---

## 4. OBSIDIAN = EXTERNALIZED COGNITION

**Key Theme:** Obsidian is not note storage — it's the cognitive graph substrate.

**Reason:** Folders are not intelligence. A graph-linked markdown vault becomes navigable, searchable, replayable operational memory. Every note links to other notes. Every failure links to its fix. Every pattern links to its successful applications.

**Aim:** All vault writes must include links (`[[Concept]]`), tags (`#failure #fix`), and follow the CAUSE/FIX/RESULT/LINKS standard.

---

## 5. SKILLS ≠ PROMPTS

**Key Theme:** Skills are portable operational capabilities, not prompt templates.

**Reason:** Prompts are static. Skills contain detection logic, fix flows, heuristics, failure patterns, and examples. They're executable markdown procedures that agents load at spawn time.

**Aim:** Every skill follows the structure: SKILL.md + heuristics.md + failures.md + patterns.md + examples/

---

## 6. HUMAN ROLE = STRATEGIC GOVERNOR

**Key Theme:** Human doesn't micromanage execution — human sets direction, constraints, and approval gates.

**Reason:** If the human is in every loop, the system doesn't scale. The human becomes: strategic governor, ontology designer, approval authority, directional architect.

**Aim:** Build approval gates and constraint policies into every autonomous loop. Never allow unbounded recursive self-modification.

---

## 7. SAFETY BOUNDARIES (HARD RULES)

These are non-negotiable:

1. **NO autonomous recursive skill mutation** — human review required
2. **NO unbounded vault writes** — taxonomy enforcement required
3. **NO cross-domain agent spawning without consensus** — observer validation required
4. **NO model weight modification** — orchestration layer only
5. **NO production deployment without approval gates** — sandbox first

---

## 8. PHASE 00 COMPONENT MAP

| # | Component | File | Purpose |
|---|-----------|------|---------|
| 0A | Vault Writer | `core/obsidian/vault_writer.py` | Write structured markdown into vault |
| 0B | Compressor | `core/obsidian/compressor.py` | Convert runtime noise → operational abstractions |
| 0C | Linker | `core/obsidian/linker.py` | Auto-link doctrine, build knowledge graph |
| 0D | Skill System | `skills/` directory | Portable operational capabilities |
| 0E | Skill Loader | `core/skills/loader.py` | Inject relevant doctrine into agent runtime |
| 0F | Execution Journal | `core/execution/journal.py` | Track actions, failures, corrections, retries |
| 0G | Live Sync | Direct markdown writes | Obsidian vault folder sync |
| 0H | Doctrine Taxonomy | `/doctrine /failures /execution /skills` | Vault structure enforcement |
| 0I | Note Standard | CAUSE/FIX/RESULT/LINKS | Every note follows this format |
| 0J | Skill Evolution Pipeline | Future stage | Human-reviewed skill promotion |

---

## 9. VAULT STRUCTURE (TARGET)

```
/O2C-VAULT/
├── agents/
│   ├── quant/
│   ├── research/
│   ├── coding/
│   └── observer/
├── memory/
│   ├── successful_patterns/
│   ├── error_corrections/
│   ├── spawn_history/
│   └── consensus_failures/
├── ontology/
│   ├── cerebus/
│   ├── observer_core/
│   ├── state_machines/
│   └── routing_logic/
├── graphs/
│   ├── agent_relationships/
│   ├── execution_flow/
│   └── knowledge_clusters/
├── journals/
│   ├── daily_runtime/
│   ├── backtest_logs/
│   └── forward_test_logs/
├── doctrine/
├── failures/
├── execution/
├── skills/
├── heuristics/
├── routing/
└── architecture/
```

---

## 10. NOTE STANDARD (MANDATORY)

Every note in the vault MUST follow:

```markdown
# [Title]

CAUSE:
[What caused this]

FIX:
[What fixed it]

RESULT:
[Outcome after fix]

LINKS:
[[Related Concept 1]]
[[Related Concept 2]]
```

No essays. No rambling. No AI sludge. Operational signal only.

---

## 11. EXECUTION ORDER

Build in this order — each phase depends on the previous:

1. **Phase 0A** — Vault Writer (can write markdown to disk)
2. **Phase 0B** — Compressor (can distill execution traces)
3. **Phase 0C** — Linker (can auto-link notes into graph)
4. **Phase 0D** — Skill System (directory structure + first skills)
5. **Phase 0E** — Skill Loader (can inject skills at runtime)
6. **Phase 0F** — Execution Journal (can track agent execution)
7. **Phase 0G** — Live Sync (Obsidian vault integration)
8. **Phase 0H** — Doctrine Taxonomy (enforce vault structure)
9. **Phase 0I** — Note Standard (validate all notes follow format)
10. **Phase 0J** — Skill Evolution Pipeline (future, human-reviewed)

---

## 12. SUCCESS CRITERIA

Phase 00 is complete when:

- [ ] Agents can write structured markdown to vault automatically
- [ ] Execution traces are compressed into operational knowledge (not raw logs)
- [ ] Knowledge graph links are auto-generated between related concepts
- [ ] Skills are loadable at spawn time and improve agent execution
- [ ] Every note follows CAUSE/FIX/RESULT/LINKS standard
- [ ] Vault taxonomy is enforced (no entropy landfill)
- [ ] Human review gate exists for skill promotion

---

## KNOWN PITFALLS (FROM PHASE 00 PLANS)

1. **Don't overengineer Obsidian sync** — direct markdown writes first, no plugins/websockets/APIs initially
2. **Don't build autonomous memory systems yet** — filesystem cognition first
3. **Don't allow recursive skill mutation** — human review required
4. **Don't skip compression** — raw traces become garbage fast
5. **Don't ignore taxonomy** — without it, vault becomes entropy landfill
