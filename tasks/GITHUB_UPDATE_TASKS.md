# GitHub Update Tasks — V3 Cognitive Field System

## Overview
Major documentation and repository update for V3 system. All tasks are documentation/code organization — no new code required.

---

## PM Tasks (Polymorph)

### PM-1: Repository Structure Cleanup
**File:** `tools/operator/repo_cleanup.py`
- [ ] Organize `tools/testing/` directory structure
- [ ] Move chaos tools to `tools/testing/chaos/`
- [ ] Move long horizon tools to `tools/testing/long_horizon/`
- [ ] Create `__init__.py` files for proper imports
- [ ] Update imports in all test files

### PM-2: Stability Database Setup
**File:** `stability/schema.sql`
- [ ] Create SQLite database from schema
- [ ] Add initial data for test runs
- [ ] Create database migration scripts
- [ ] Document database schema in README

### PM-3: Chaos Engine Integration
**File:** `tools/testing/chaos/chaos_engine.py`
- [ ] Add CLI interface with argparse
- [ ] Add scenario presets (observer_death, full_chaos, etc.)
- [ ] Add logging to stability database
- [ ] Create chaos report generator

### PM-4: Monitoring Endpoints
**File:** `tools/testing/long_horizon/metrics_exporter.py`
- [ ] Create `/ws/stability` WebSocket endpoint
- [ ] Create `/api/stability/*` REST endpoints
- [ ] Add Prometheus metrics export
- [ ] Create Grafana dashboard JSON

---

## AS Tasks (Assistant Manager)

### AS-1: README.md Overhaul
**File:** `README.md`
- [ ] Add V3 architecture overview section
- [ ] Add quick start guide
- [ ] Add test instructions
- [ ] Add monitoring setup guide
- [ ] Add Phase 11 validation section

### AS-2: API Documentation
**File:** `docs/API.md`
- [ ] Document all Phase 9 field_core APIs
- [ ] Document all Phase 10 compute APIs
- [ ] Add usage examples for each module
- [ ] Create API reference table

### AS-3: CODEMAP.md Update
**File:** `CODEMAP.md`
- [ ] Add Phase 10 diagrams
- [ ] Add Phase 11 test architecture
- [ ] Update module relationships
- [ ] Add chaos engineering flow

### AS-4: Phase Documentation
**Files:** `docs/phase*.md`
- [ ] Create `docs/phase9.md` — Sovereign Field Emergence
- [ ] Create `docs/phase10.md` — Recursive Field Computation
- [ ] Create `docs/phase11.md` — Operational Validation
- [ ] Add to documentation index

---

## CC Tasks (Claude Code)

### CC-1: V3_ARCHITECTURE.md
**File:** `V3_ARCHITECTURE.md` ✅ DONE
- [x] Core principles section
- [x] Architecture layers (Phases 1-10)
- [x] Key distinctions from current AI
- [x] Use cases
- [x] Phase 11 validation

### CC-2: GitHub Push
**Command:** Git operations
- [ ] Commit all changes
- [ ] Push to GitHub
- [ ] Create release notes
- [ ] Update GitHub Pages

### CC-3: Team Coordination
**File:** `shared-conversations/team-chat.md`
- [ ] Post task assignments
- [ ] Track progress
- [ ] Coordinate reviews

---

## Task Dependencies

```
PM-1 → PM-2 → PM-3 → PM-4
   ↓       ↓       ↓       ↓
AS-1 → AS-2 → AS-3 → AS-4
   ↓       ↓       ↓       ↓
CC-1 → CC-2 → CC-3
```

---

## Estimated Time

| Task | Time |
|------|------|
| PM-1 | 2 hours |
| PM-2 | 1 hour |
| PM-3 | 2 hours |
| PM-4 | 2 hours |
| AS-1 | 2 hours |
| AS-2 | 2 hours |
| AS-3 | 1 hour |
| AS-4 | 2 hours |
| CC-2 | 1 hour |
| CC-3 | 0.5 hours |

**Total:** ~15.5 hours (parallelizable)

---

## Success Criteria

- [ ] All documentation updated
- [ ] Repository structure clean
- [ ] Tests runnable with clear instructions
- [ ] Monitoring endpoints working
- [ ] GitHub updated with release notes