---
created: 2026-05-17
updated: 2026-05-17
tags: [memory, index, navigation]
importance: 4
---

# Memory Index

> Central navigation hub for the PAI-inspired memory architecture.
> Each file has YAML frontmatter with: `created`, `updated`, `tags`, `importance` (1-5).

## [Working Memory](working-memory.md) ⭐⭐⭐⭐⭐
**Active session context, in-flight tasks, pending decisions.**
Read this first at session start to understand what's currently happening.

## [Episodic Memory](episodic-memory.md) ⭐⭐⭐⭐⭐
**Past events, decisions, outcomes — chronological.**
The history of what happened and why. Most recent events at the top.

## [Semantic Memory](semantic-memory.md) ⭐⭐⭐⭐
**Facts, concepts, relationships — the knowledge graph.**
System architecture, infrastructure, agent roster, key concepts.

## [Procedural Memory](procedural-memory.md) ⭐⭐⭐⭐⭐
**How-to knowledge, workflows, SOPs.**
Step-by-step procedures for common operations. Read before performing standard tasks.

## [Identity Memory](identity-memory.md) ⭐⭐⭐
**Who the system is, preferences, values.**
Core identity, operating principles, what the system is/am not.

---

## Usage

1. **Session start:** Read `working-memory.md` → `episodic-memory.md` (last 3 entries)
2. **Before complex tasks:** Read relevant section of `procedural-memory.md`
3. **Fact lookup:** Search `semantic-memory.md`
4. **Identity check:** Read `identity-memory.md` when drift is suspected
5. **After significant events:** Append to `episodic-memory.md`
6. **After code edits:** Update `working-memory.md`

## Maintenance

- Compress files exceeding 200 lines (archive old entries to `memory/archive/`)
- Update `updated` timestamp in YAML frontmatter on every edit
- Re-index this file when new memory files are added
