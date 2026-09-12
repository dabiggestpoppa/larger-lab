# QCAE Implementation Progress Ledger

**Branch:** `qcae-capability-acquisition-engine`
**Canon:** QCAE v0.1 (Blocks 0–18, COMPLETE / FROZEN) under `qcae/books/`
**Active amendments:** A-001 (Research Mesh Boundary and Economic Experience v1.0)
**Build mode:** BUILD MODE per master prompt; phases P0→P12 strictly sequential.

---

## Current Phase

**P1 — FROZEN / OPERATOR-REVIEWED** (Evidence + Registry Spine + P1-R1 repair; P2 NOT started)

### P1-R1 — Registry Completion + Freeze Truth Repair (supersedes original P1 freeze bookkeeping)

Operator review of `bbbe05a7` identified three exit-gate defects; repaired in
P1-R1 without redesigning any accepted P1 subsystem:

1. **Freeze truth** — original `P1-freeze-manifest.json` had
   `test_results: null`. Preserved byte-for-byte (blob `ab9ab86e…`, introduced
   in `20ee6465`); superseded by `qcae/implementation/P1-R1-freeze-manifest.json`
   whose `test_results` are captured from an actual full-suite run by the
   fail-closed generator (`qcae/implementation/tools/p1r1_freeze_manifest.py`
   + `test_evidence.py`). Generator refuses to emit on test failure,
   unparseable output, or commit mismatch. Counts are never hardcoded.
2. **Canonical status** — this ledger now reads P1 — FROZEN /
   OPERATOR-REVIEWED; P2 is not active.
3. **Registry substrate** — CapabilityRegistry (contracts/atoms/composites/
   candidates, versioned keys, digest-verified rows) and provider-neutral
   RepositoryRegistry (multi-revision coexistence) added in P1-R1-C01/C02;
   linked via the frozen P0 Relationship vocabulary (no new edge types);
   backup/restore covers all registry tables with count verification;
   decision-reuse exposes known capability/candidate state; RepositoryRegistry
   deferral removed from the superseding freeze (P3 populates it).

P1-R1 repair commits: `34d256bf` (I0), `9a990a85` (C01), `53106b1f` (C02),
`e3059465`+`31e5ba20` (C03), `7d541a97` (C04), `1817ed57` (C05), `a8ea1014`
(T01), `7fbf5326`+freeze-commit (FREEZE).

### P1 phase log (original build; superseded bookkeeping per P1-R1 above)

- **P1-I0** `a53b401b` — preflight repairs (ledger test-count 139→141 via
  addendum, vacuous `or True` assertion removed) + **ADR-0006**: SQLite
  (stdlib) metadata engine behind ports; DuckDB declined for OLTP (analytics
  deferred); raw artifacts content-addressed on filesystem.
- **P1-C01** `d5e8882e` — evidence object model: EvidenceObjectType vs
  EvidenceClass kept as separate axes (Book IV 9.1), structured ScopeDimensions,
  FreshnessState, raw/interpretation partitioning.
- **P1-C02** `6890f852` — content-addressed artifact store (sha256,
  `sha256/ab/cd/<digest>` layout, atomic writes, retrieval verification,
  collision/corruption/traversal guards).
- **P1-C03** `93b7a1ea`/`090e7edc`/`f113c396` — persistence ports (core) +
  SQLite adapter (infrastructure): digest-verified rows, INSERT-only factual
  tables, append-only freshness log, forward-compat guard, sqlite3 denial
  scoped to infrastructure only.
- **P1-C04** `01a31a69` — lineage edge store: 9.5 vocabulary, contradiction
  coexistence (no resolution-by-deletion API), idempotent edges.
- **P1-C05** `3aaddeea` — Capability Receipt (9.2): 6 states, scope-bounded,
  authority + rollback required, proof firewall (external-only evidence can
  never satisfy executable proof).
- **P1-C06** `07475b2d` — positive/negative knowledge (9.3/9.4): 11 failure
  categories, causal-detail minimum, mandatory reconsideration conditions,
  material knowledge evidence-linked (notes are non-material).
- **P1-C07** `e59632e7`/`a498a955`/`70c6b306` — knowledge/receipt repositories
  + structured decision-reuse query implementing the 9.7 retrieval order
  (active receipts → positive knowledge → negative blocks → stale evidence →
  external discovery).
- **P1-C08** `e8cfb720` — A-001 cross-registry persistence: ExternalRegistryRef
  durable, owner-domain immutable (laundering rejected), OBSERVE/SUBMIT only.
- **P1-C09** `04983524` — UnitOfWork (BEGIN IMMEDIATE, rollback on any
  failure, no nesting) + atomic evidence+lineage commit service; WAL isolation
  across connections verified.
- **P1-C10** `55ba326d` — migration framework: forward-only runner keyed by
  target version, ledger with pre/post schema digests, v1→v2 mechanism proof,
  rollback and refusal behaviors verified.
- **P1-C11** `772ab794`/`da69813d` — backup/restore: consistent SQLite
  snapshot + flat artifact copies + manifest with digests; restore verifies
  every digest before declaring success (full-cycle exactness tested).
- **P1-T01** `ba9c3e35` — adversarial suite: payload/digest tampering,
  append-only pressure across all stores, restart persistence of the whole
  spine, evidence→receipt firewall chain, classification flow-through.
- **P1-FREEZE** `20ee6465` — `qcae/implementation/P1-freeze-manifest.json`
  (559/559 LOCAL TEST EVIDENCE).

### P1 exit gate (spec §25)

| Criterion | Status | Evidence |
| --- | --- | --- |
| durable local structured persistence | PASS | SQLite adapter + restart tests |
| raw evidence content-addressed, integrity-checked | PASS | test_p1_artifact_store, adversarial binding test |
| evidence provenance-linked, raw/interpretation separate | PASS | EvidenceArtifact validation + lineage store |
| receipts scope-bounded, firewall enforced | PASS | test_p1_receipt |
| positive knowledge evidence-linked | PASS | material flag enforcement |
| negative knowledge durable/searchable | PASS | subject/revision/type retrieval |
| contradictions/lineage preserved | PASS | contradiction coexistence tests |
| cross-registry provenance without ownership collapse | PASS | owner-rewrite rejection, rights visibility |
| transactions rollback correctly | PASS | injected-failure rollback tests |
| schema version/migration mechanism works | PASS | v1→v2 migration + ledger evidence |
| backup restored successfully in test | PASS | full-cycle exactness test |
| registry survives process restart | PASS | complete-spine restart test |
| retrieval detects reusable internal knowledge | PASS | decision-reuse findings tests |
| no provider SDK / Research Mesh / OCE in core | PASS | architecture guards incl. self-verifying engine-free guard |
| all QCAE tests pass | PASS | 559/559 (LOCAL TEST EVIDENCE) |
| ledger + manifest current | PASS | this file + P1-freeze-manifest.json |
| no unresolved high-severity deviation | PASS | deferred items in manifest are MINOR, trigger-tagged |

## Historical: P0 — FROZEN v0.1 + A-001 RECONCILED

### Amendment reconciliation timeline

1. **P0 original freeze** at `6d23c956` (270/270 LOCAL TEST EVIDENCE; manifest
   `qcae/implementation/P0-freeze-manifest.json` — preserved, not overwritten).
2. **A-001 landed** on the branch (`docs(qcae)` commits:
   `66e99505`, `6d98193c`, `a399f525`, `281d1aa9`) — additive amendment register,
   Research Mesh boundary, ResearchCapabilityHandoff + EconomicExperienceRecord
   interface schemas.
3. **P0 amendment reconciliation opened** per operator directive (reconcile
   A-001 §13 P0 obligations; repair reviewed ambiguities).
4. **Reconciliation commits** `983a742e` → (see commit log below).
5. **Amendment tests added** (141 new tests across vocabulary, handoff,
   economic/cross-registry, contract repair, deferred semantics, schema drift;
   count corrected from an earlier 139 transcription error during P1-I0 —
   composition arithmetic in the freeze manifest: 20+31+25+34+7+22 = 139 unit
   + 2 Research Mesh architecture guards = 141).
6. **New freeze** — `qcae/implementation/P0-A001-freeze-manifest.json`
   (411/411 LOCAL TEST EVIDENCE).

### P0-A001 exit gate (reconciliation prompt §17)

| Criterion | Status | Evidence |
| --- | --- | --- |
| all active amendments registered | PASS | A-001 in manifest `active_amendments`; register read in full |
| A-001 P0 obligations have domain/interface representation | PASS | gap taxonomy, resolution vocabulary, handoff contract, EconomicExperienceRecord, ExternalRegistryRef |
| original P0 semantics remain compatible | PASS | all 270 original tests pass unmodified except one terminal-set assertion updated by ADR-0004 (documented, not weakened) |
| no Research Mesh implementation leaked into core | PASS | 2 new architecture guards + fragment scan; interface contracts only |
| no economic/marketplace authority added | PASS | no execution/revenue/mutation code; reference records only |
| customer payment/acceptance cannot become institutional proof | PASS | firewall tests (promotion requires governed refs; PROMOTED requires citation) |
| client-protected material fail-closed | PASS | PROMOTED + protected-rights pre-RIGHTS_FILTERED rejection tests |
| DEFERRED ambiguity resolved | PASS | ADR-0004 interpretation A; consistency tests |
| CapabilityContract validation repair complete | PASS | request_id + all string-tuple fields validated; 34 negative tests |
| schema/interface drift guard exists | PASS | test_p0_a001_schema_drift.py (ADR-0005), self-verifying |
| all qcae tests pass | PASS | 411/411 (LOCAL TEST EVIDENCE) |
| amendment-aware freeze manifest exists | PASS | P0-A001-freeze-manifest.json |
| progress ledger current | PASS | this file |
| no unapproved canon deviation | PASS | ADRs 0003–0005 documented; none contradict canon |

### P0 Checklist — COMPLETE

- [x] P0-I0 progress ledger + implementation decision records (`e1fda033`)
- [x] P0-C01 package skeleton per Book V 15.1 + test wiring (`64b31511`)
- [x] P0-C02 base error taxonomy + schema-versioned serialization base (`22cc49ba`)
- [x] P0-C03 LifecycleState machine + transition guards (canon 0.5) (`42a94352`)
- [x] P0-C04 CapabilityContract (canon 1.1.4 fields, versioning, req/pref/forbidden) (`450308eb`)
- [x] P0-C05 CapabilityAtom (1.2.22), CompositeCapability (1.2.10–11), Candidate (`7451466e`)
- [x] P0-C06 Relationship (1.3.4), EntityRef (1.3.3/1.3.16), EvidenceRef (0.4.2/0.4.3) (`9acd4d2f`)
- [x] P0-C07 AcquisitionDecision (0.5.12), Authority primitives (0.3), Job/Step identity (`102c3c5c`)
- [x] P0-T01 architecture/dependency guard tests (canon 15.2 forbidden deps) (`7ad5277c`)
- [x] P0-FREEZE freeze manifest + full suite green + ledger current

### P0 Exit Gate Evidence (canon 18.2 + master prompt §28)

| Criterion | Status | Evidence |
| --- | --- | --- |
| core package structure exists | PASS | Book V 15.1 tree, topology test (`test_p0_topology.py`) |
| canonical domain objects exist | PASS | 13 versioned record classes (see freeze manifest schema snapshots) |
| schemas are versioned | PASS | `SCHEMA_VERSION` envelope, fail-closed readers, manifest `schema_snapshot_digest` |
| lifecycle rules explicit | PASS | `core/lifecycle/state.py` single authority; 44 transition tests |
| serialization works | PASS | round trips incl. schema-version rejection, unknown-key rejection |
| all P0 tests pass | PASS | 270 passed / 0 failed / 0 skipped |
| no provider leaked into core | PASS | guard-tested: stdlib-only, sqlite3 denied, higher-layer import denied, self-verifying scanner |
| progress ledger current | PASS | this file |
| deviations from canon | NONE | derived points documented below, none contradict canon |
| coherent for P1 | PASS | evidence-ref + digest primitives are the exact substrate P1 needs |

---

## Commit Log

### P0 original freeze (pre-A001, preserved)

| Commit | Phase-Intent | Purpose |
| --- | --- | --- |
| e1fda033 | P0-I0 | progress ledger + ADR-0001/0002 |
| 64b31511 | P0-C01 | package skeleton + test wiring |
| 22cc49ba | P0-C02 | error taxonomy + serialization base |
| 42a94352 | P0-C03 | lifecycle machine + transition guards |
| 450308eb | P0-C04 | capability contract domain |
| 7451466e | P0-C05 | atoms + composites + candidates |
| 9acd4d2f | P0-C06 | relationships + evidence refs |
| 102c3c5c | P0-C07 | acquisition decisions + authority + job/step |
| 7ad5277c | P0-T01 | architecture dependency guards |
| 6d23c956 | P0-FREEZE | freeze manifest + ledger freeze state |

### P0-A001 reconciliation (additive)

| Commit | Phase-Intent | Purpose |
| --- | --- | --- |
| 983a742e | P0-A001-01 | gap taxonomy + economic resolution vocabulary |
| 69b347ef | P0-A001-02 | Research Mesh handoff contract |
| 6eee5fb8 | P0-A001-03 | Economic Experience + cross-registry refs + ADR-0003 |
| 16bb5229 | P0-A001-04 | CapabilityContract validation repair |
| 74993b67 | P0-A001-05 | DEFERRED semantics resolution (ADR-0004) |
| 24d3364c | P0-A001-T02 | schema drift guard + Research Mesh isolation guards (ADR-0005) |
| d82f727f | P0-A001-T02 | malformed provenance rejection tests |
| (this commit) | P0-A001-FREEZE | amendment-aware manifest + ledger freeze state |

---

## Test Ledger

All rows are LOCAL TEST EVIDENCE (`python -m pytest qcae/tests -q`).

| Suite | Tests | Passed | Failed | Skipped | Commit |
| --- | --- | --- | --- | --- | --- |
| qcae/tests (P0 original freeze) | 270 | 270 | 0 | 0 | 6d23c956 |
| qcae/tests (P0 + A-001 reconciliation) | 411 | 411 | 0 | 0 | P0-A001-FREEZE |

Composition: 255 unit + 15 architecture guards.

Important adversarial tests delivered (master prompt §27 mapping):

- illegal lifecycle transition rejected (parametrized across 20+ illegal edges) — `test_p0_lifecycle.py`
- waivable gate (DOMAIN_VERIFIED only) rejected without policy justification — `TestIllegalTransitions::test_gate_skip_without_waiver_rejected`
- contract with behavior both required and forbidden rejected — `test_p0_contract.py`
- contract with empty required behaviors / acceptance / evidence rejected
- atom identity independent of implementation — `test_p0_capabilities.py`
- composite single-member ALTERNATIVE, REQUIRED-in-ALTERNATIVE, only-OPTIONAL, empty, duplicate members rejected
- relationship with type outside controlled vocabulary rejected; direction violations rejected (implements reversed, contained_in non-repo, supersedes cross-type…)
- evidence ref with malformed artifact hash rejected
- schema-version mismatch / unknown object type / unknown field rejected on deserialize
- core importing forbidden provider module fails the architecture guard (scanner self-verified against synthetic violating trees, including relative-escape and dynamic `__import__`)

Pre-existing failure outside QCAE (not introduced by this work, verified identical before P0): `tests/forge/phase_00/test_extension_docs.py` — 2 failures on this branch.

---

## Evidence Artifacts (canon 18.3 Phase 0 matrix + reconciliation §10)

- [x] schema snapshots (22: 13 original + 9 amendment) — both freeze manifests
- [x] lifecycle transition tests — `qcae/tests/unit/test_p0_lifecycle.py`, `test_p0_a001_deferred.py`
- [x] architecture/dependency guards — `qcae/tests/architecture/test_p0_dependency_guards.py`
- [x] serialization round-trip evidence — `qcae/tests/unit/test_p0_serialization.py`, `test_p0_contract.py`, A-001 contract tests
- [x] P0 freeze manifest (preserved) — `qcae/implementation/P0-freeze-manifest.json`
- [x] P0-A001 amendment-aware freeze manifest — `qcae/implementation/P0-A001-freeze-manifest.json`
- [x] ADRs — 0001/0002 (original), 0003 (vocabulary layering), 0004 (DEFERRED), 0005 (drift guard)

---

## Implementation Decision Records

- ADR-0001 — core domain: stdlib dataclasses + explicit validation; zero third-party dependencies in `qcae/core`
- ADR-0002 — `qcae/` package at repo root per Book V 15.1; tests under `qcae/tests/`; root pytest config extended
- ADR-0003 — two-layer acquisition vocabulary: CapabilityResolutionMode (institutional) over AcquisitionForm (implementation); no silent replacement
- ADR-0004 — DEFERRED is terminal for that decision/version; resumption = superseding object (canon 0.5.15 + Book IV 11.6)
- ADR-0005 — amendment interface-schema drift guard via explicit compatibility assertions; no new dependencies

Location: `qcae/implementation/decisions/`

---

## Unresolved Questions / Derived Points (for operator review)

1. **Lifecycle branches derived from canon 0.5** (documented in `core/lifecycle/state.py` module docstring): candidate culling (REJECTED/DEFERRED) permitted from CANDIDATE…ACQUISITION_CANDIDATE; REVIEW_REQUIRED → MONITORED return; REJECTED/SUPERSEDED/RETIRED terminal. Localized change if operator wants different branch legality.
2. **Waivable gate set = {DOMAIN_VERIFIED}** (canon 0.5.10). Enforced strictly: waivers on edges that need none are rejected.
3. **VerificationLevel enum** uses canon 1.3.13 (DISCOVERED…DOMAIN_VERIFIED); master prompt §8's illustrative set is superseded by canon per master prompt §0.
4. **AtomStatus values** (PROPOSED/ACTIVE/DEPRECATED/RETIRED) are a P0 derivation — canon 1.2.22 leaves `status` unvalued. Revisit at P5; field is versioned, additive change is safe.
5. **Job/Step statuses** minimal identity contracts; P2 job runtime (Block 12/13 chapters to be read before P2) may extend additively.
6. **NegativeKnowledge, Evaluation, CapabilityReceipt, MonitoringRecord** intentionally not in P0 (P1/P5/P8 scope per 18.1); their substrates (EvidenceRef, Relationship, digests) exist.
7. **Relationship endpoint-role constraints** are deliberately conservative (load-bearing edges only: implements/composed_of/contained_in/depends_on/normalized_as/supersedes); extend as P4+ refines canon semantics.

## Deviations from Canon

None. All derived points above refine within canon; none contradict a frozen invariant.

## Blockers

None.

## Next Action

P0 — FROZEN v0.1 + A-001 RECONCILED. Awaiting operator authorization for **P1 — Evidence + Registry Spine** (canon 18.1 Phase 1: artifact hashing/store, structured persistence, provenance relationships, Capability Receipts, negative knowledge, repositories/unit-of-work, migrations, backup/restore; plus A-001 §13 P1 obligation: cross-registry provenance without collapsing knowledge/capability ownership). Book IV Block 9 chapters + A-001 to be read before P1 starts.
