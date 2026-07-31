# Phase 2: Reconstruction + Recoverability — Task Breakdown

> **Phase Goal:** Replace static memory with adaptive reconstruction.
> **Success Criteria:**
> 1. Recovery anchors implemented (sparse persistence, not full transcripts)
> 2. Continuity survives sparse memory (delete 90% context, reconstruct)
> 3. Reconstruction mesh operational (drift detector, consistency validator, synthesizer)
> 4. Contradictions self-resolve
> 5. Constraint propagation works (change one constraint, downstream shifts)

---

## Task 2.1: Recovery Anchor Storage (HR)
**Agent:** HR  
**Priority:** High  
**Description:** Build SQLite-based recovery anchor storage system. Stores invariant structures (not full transcripts). Each anchor has: id, content, weight, source, timestamp, tags.

**Deliverables:**
- `srrs_opc/recovery_anchors.py` — Anchor CRUD + storage
- `srrs_opc/tests/test_recovery_anchors.py` — Unit tests
- Schema: anchors(id, content, weight, source, created_at, tags)

**Acceptance Criteria:**
- Can store and retrieve anchors by tag/weight
- Anchors survive process restart
- Deleting 90% of anchors still leaves coherent core

---

## Task 2.2: Reconstruction Mesh (OC)
**Agent:** OC  
**Priority:** High  
**Description:** Design and implement the reconstruction mesh: drift detector, consistency validator, reconstruction synthesizer.

**Deliverables:**
- `srrs_opc/drift_detector.py` — Detects when stored anchors diverge from current state
- `srrs_opc/consistency_validator.py` — Validates anchor consistency
- `srrs_opc/reconstruction_synthesizer.py` — Reconstructs continuity from sparse anchors
- `srrs_opc/tests/test_reconstruction_mesh.py` — Integration tests

**Acceptance Criteria:**
- Drift detector flags outdated/inconsistent anchors
- Validator catches contradictory anchors
- Synthesizer produces coherent continuity output from <10% of original context

---

## Task 2.3: Constraint Propagation Engine (CC)
**Agent:** CC  
**Priority:** High  
**Description:** Build event-driven constraint propagation. When one constraint changes, all dependent patches update automatically.

**Deliverables:**
- `srrs_opc/constraint_propagator.py` — Event-driven constraint propagation
- `srrs_opc/tests/test_constraint_propagation.py` — Tests
- Uses Redis Streams or NATS for messaging (Redis preferred for Phase 2)

**Acceptance Criteria:**
- Changing one high-level constraint propagates to all dependent state
- No manual synchronization needed
- Propagation is bounded (doesn't cascade infinitely)

---

## Task 2.4: Contradiction Resolution (CC)
**Agent:** CC  
**Priority:** Medium  
**Description:** Build contradiction detection and self-resolution into the repair patch.

**Deliverables:**
- `srrs_opc/contradiction_resolver.py` — Detects and resolves anchor contradictions
- Integration with existing RepairPatch
- `srrs_opc/tests/test_contradiction_resolution.py` — Tests

**Acceptance Criteria:**
- Contradictory anchors are flagged automatically
- Resolution strategy: higher weight wins, or flag for human review
- No silent data loss during resolution

---

## Task 2.5: Phase 2 Integration Test (CC)
**Agent:** CC  
**Priority:** Medium  
**Description:** End-to-end test of Phase 2. Delete 90% of context, verify system reconstructs coherent continuity.

**Deliverables:**
- `srrs_opc/tests/test_phase2_e2e.py` — End-to-end test
- Test report in `srrs_opc/reports/phase2_test_report.md`

**Acceptance Criteria:**
- System reconstructs coherent continuity from sparse anchors
- All Phase 2 success criteria verified
- Test report documents results

---

## Dependencies
```
Task 2.1 (HR) ──→ Task 2.2 (OC) ──→ Task 2.5 (CC)
                     ↑
Task 2.3 (CC) ──────┘
Task 2.4 (CC) ──────┘
```

## Estimated Order
1. Task 2.1 (HR) — Foundation: anchor storage
2. Task 2.3 (CC) — Constraint propagation (parallel with 2.1)
3. Task 2.2 (OC) — Reconstruction mesh (depends on 2.1)
4. Task 2.4 (CC) — Contradiction resolution (depends on 2.2)
5. Task 2.5 (CC) — Integration test (depends on all)
