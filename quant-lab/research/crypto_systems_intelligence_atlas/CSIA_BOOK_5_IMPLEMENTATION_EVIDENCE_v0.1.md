# CSIA Book 5 Implementation Evidence v0.1

- **Date:** 2026-09-29
- **Branch:** `agent/crypto-systems-intelligence-atlas-book5-build`
- **Base:** `a2526e8220513b34967ab11f227ddbddc14e7e4a` (Book 4 acceptance commit)
- **Ratified planning authority:** plan v0.3 (anchor `262625fd063a17cfeb845f610a7de29c89f29b27`), ratification commit `b33dc3c76a76228139abb4fe014d3fe404e2cee4`, decision `BOOK5-RATIFICATION-v0.3`

## Status Block

```text
BOOK = 5
TITLE = CAPITAL PLUMBING AND ECONOMIC TOPOLOGY
STATUS = IMPLEMENTATION_COMPLETE_PENDING_OPERATOR_REVIEW
BOOK_5_IMPLEMENTATION_ACCEPTED = FALSE (self-acceptance forbidden)
BOOK_5_TESTS = 78 PASS
TOTAL_CSIA = 606 PASS (528 baseline + 78)
PROPOSED_BOOK_GATE = PASS_CSIA_BOOK5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_KERNEL
BOOK5_CROSS_ASSET_VALUATION_AUTHORITY = FALSE
5G_CANONICAL_WRITE_COUNT = 0
5G_CROSS_ASSET_VALUATION_COUNT = 0
LIVE_ACQUISITION_AUTHORITY = FALSE
```

## Module Inventory (6 kernel modules, 1833 added lines, zero upstream mutations)

| Module | Contents |
|---|---|
| `book5_provenance.py` | Fail-closed `Book5Provenance` over Book 2 ClaimStore/EvidenceStore; qualifier-specific economics resolution; no second epistemic engine |
| `book5_core.py` | `AttributionState` (6 states + arithmetic law), `EconomicSite` (Book 1-anchored), `EconomicLocation` (UNKNOWN-precise), `PrincipalComponent`/`PrincipalComponentSet` (unit-aware vector; no value/numeraire field) |
| `book5_lineage.py` | `CapitalPrincipalLineageGraph` (many-to-many; CON-1..10; structural cycle detection; same-unit-only collapse; `AttributionBasisError` Book 2 basis verification), D5CAP-1 liability family (`DebtLiability`/`ReserveLiability`/`RedemptionClaim` + reconciling projections), `VALUATION_NOT_AUTHORIZED` |
| `book5_records.py` | Position family (9 classes), `Encumbrance`, `EconomicClaim`, `CapitalFlow` (21-type ratified vocabulary), `CapitalTransformation` (8 kinds), `DerivativeExposure`, `SettlementBalance`, `ObservedCommonValueFact`, append-only flow ledger |
| `book5_synthesis.py` | 5G derived-only engine: `CapitalFieldSnapshot`/`CapitalFieldPath`/`CapitalPrincipalLineageView`/`CapitalTopologyView` (INV-5G-1..7; naming seal), `SynthesisWriteLedger` (canonical write count 0 by construction), three-way collapse split, NOT_AUTHORIZED valuation law |
| `book5_support.py` | Deterministic offline fixtures with real Book 2 evidence capture |

## Verification Results

```text
BASELINE (at a2526e82): Book1=107, Book2=108, Book3=83, Book4=230, TOTAL=528 PASS
FINAL:                  Book1=107, Book2=108, Book3=83, Book4=230, Book5=78, TOTAL=606 PASS
RUFF = PASS (0 findings across 43 source files)
MYPY = PASS (0 issues across 43 source files)
SENSOR = 2325 PASS / 14 FAIL / 4 SKIPPED — failure set byte-identical to the
         accepted Book 4 canonical 14-failure equivalence record
BOOK5_INTRODUCED_SENSOR_FAILURES = 0
FREEZE: Book1/2/3/4 contract mutations = 0; Crypto Sensor mutations = 0
        (diff vs base contains only book5_* modules + Book 5 research evidence)
```

## Stress-Corpus Coverage (Phase 22)

All 45 ratified stress rows are mapped row → test → assertion in
`STRESS_ROW_TRACEABILITY` (test_book5_blocs.py) and enforced by
`test_stress_traceability_complete`:

- rows 1–10 (D7 corpus): supplied+borrowed non-additivity, borrowed-redeposit COMMINGLED attribution, ETH→LST→restake single lineage, LP collateral encumbrance, canonical+wrapped non-summing, notional domain separation, RWA equivalence law
- rows 11–25: cycles, fan-out/fan-in conservation, append-only flows, attribution arithmetic law, custody-vs-ownership, UNKNOWN locations, uncontested-claim resolution, site anchoring
- rows 26–35: LP/vault multi-root vectors, pool commingling, multi-collateral, reserve baskets, observed-value display, UNKNOWN propagation, DERIVED_ALLOCATION methodology
- rows 36–45: unit-domain vectors, same-unit merges, observed scalars, NOT_AUTHORIZED pre-Book-6 valuation

## 5G Synthesis Coverage (Phase 23)

- T-1/T-9 heterogeneous vector preservation (no scalar exists on snapshot artifacts)
- T-2 CON-10 commingling law; T-3/T-11 fraction ≠ valuation
- T-4/INV-5G-4 unknown propagation (INCOMPLETE, never zero-fill)
- T-5/INV-5G-1..2 canonical-vs-derived naming seal (CapitalPrincipalLineage vs CapitalPrincipalLineageView) with derivation markers
- T-6/INV-5G-6 liability single-source consumption
- T-7 collateral-vs-borrowed lineage separation
- T-8/T-10 no implicit numeraire
- T-12 NOT_AUTHORIZED vs UNKNOWN state law
- T-13 observed-vs-derived scalar separation
- T-14 same-unit collapse preserved
- `SynthesisWriteLedger.canonical_write_count == 0` by construction; replay consistency at two valid times verified

## Adversarial Coverage (Phases 24–28)

- Frozen-model mutation refused; `model_copy(update=...)` tampers (stripped provenance, changed units, changed attribution states, raw dict edge injection) fail closed at the next authority boundary
- `AttributionBasisError`: EXACT/PROPORTIONAL edges verified against `PRINCIPAL_EXACT_FACT` / `PRINCIPAL_PROPORTIONAL_FACT` Book 2 qualifiers; non-canonical state values refused outright
- Liability projections: conflicting quantities, mismatched observation times, unreferenced liabilities, non-decimal quantities — all fail closed
- Provenance: unknown/unpromotable/detached/qualifier-mismatched claims refused; forged claim objects refused

## Limitations (honest scope statement)

- Offline deterministic kernel only: no live chain acquisition, no RPC, no network collectors, no CEX feeds
- No persistent database; no graph database; no production scheduler
- No Book 6 valuation, no production pricing, no numeraire conversion anywhere in the kernel
- No trading/execution authority of any kind
- Flow vocabulary is the ratified 21-type candidate set; per-bloc production adapters and persistence layers are future implementation work
- 5G composition operates over in-memory canonical records; snapshot persistence/replay-at-scale is implementation-future work

## Proposed Gate

```text
PASS_CSIA_BOOK5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_KERNEL = PROPOSED
The implementation agent does NOT self-accept. Operator review required.
```

---

# HARDENING R1 — LIVE-STATE VALIDATION + NO-FABRICATED-PRINCIPAL SEMANTICS (2026-09-29)

Narrow single-round hardening pass over base `38b758c6015aaee3297d7c49f7637fd7f8917abb`.
No redesign; no Book 6; no live acquisition.

## Demonstrated defects (all reproduced failure-first, commit `651c988a3`)

- **R1-D1** — `PrincipalComponent` attribution upgradeable via `model_copy`:
  UNKNOWN→EXACT survived into `aggregate_same_unit`. Violated B5-P29, CON-2,
  CON-10, ALG-11, and the directive "no attribution state may increase
  epistemic precision beyond its Book 2 basis". (A1–A7)
- **R1-D2** — unit/asset context mutated via `model_copy` without basis
  revalidation: a tampered ETH component was accepted as USDC on
  `aggregate_same_unit("USDC")`. (B1–B4)
- **R1-D3** — `components_for()` fabricated `quantity="0"` for edges with no
  evidenced quantity, and flow-only `compose_snapshot()` manufactured a
  placeholder principal (`csia:token:none` / `0` / `NONE` / fabricated
  `book5-claim-base`). UNKNOWN != ZERO; no missing-input fabrication. (C1–C4, D1–D6)
- **R1-D4** — raw post-construction dicts at `add_edge`/`add_node`/
  `compose_snapshot` crashed with `AttributeError` — not a fail-closed class. (E1–E6)
- **R1-D5** — 5G composition accepted `model_copy`-mutated records with
  stripped or swapped Book 2 claim refs (no provenance closure at 5G). (F1–F5)

## Repairs

- `Book5Provenance.validate_principal_component` — decision-time live-state
  component validation (typed model, canonical attribution enum, resolvable
  current claims, `ATTRIBUTION_BASIS_QUALIFIERS` match for EXACT/PROPORTIONAL,
  decimal quantity, non-empty unit, tz-aware valid time, context bindings).
- `ClaimContextBinding` — typed Book 5-local claim→(asset_ref, realization_ref,
  unit) binding; verifies exactly the dimensions Book 2 can express; claims
  nothing Book 2 cannot.
- `aggregate_same_unit(provenance=...)` seals arithmetic to live Book 2 basis;
  raw-injected states fail closed even without provenance
  (`require_canonical_state`). `AttributionBasisError` on the component path.
- `components_for()` carries `quantity=None` for missing quantities (explicit
  unknown, distinguishable from evidenced `"0"`); aggregation refuses
  attributable components without quantity.
- `CapitalFieldSnapshot.principal_components: PrincipalComponentSet | None` —
  `None` carries an explicit `NO_PRINCIPAL_COMPONENT_OBSERVED` gap; the
  placeholder token/zero/claim-ref fabrication is deleted.
- Typed fail-closed guards before attribute access on `add_node`, `add_edge`,
  and all `compose_snapshot` input families (positions, flows, liabilities,
  observed value facts).
- `CapitalFieldSynthesis(ledger, provenance=...)` revalidates every input
  (including nested components) at compose time; `lineage_view` and
  `collapse_request` forward provenance to lineage decision points;
  `components_for(provenance=...)` revalidates materialized components (Phase 10).

## Evidence

- R1 focused: 37 tests, 23 failing at the failure-first commit.
- Prior Book 5 suite: 78 preserved; one defective assertion replaced with
  documentation (`test_unknown_to_exact_mutation_refused_at_boundary` had
  asserted the defect itself).
- Post-R1: Book 5 = 115; total CSIA = 643 (Book 1 = 107, Book 2 = 108,
  Book 3 = 83, Book 4 = 230 — all unchanged).
- Sensor: 2325 PASS / 14 FAIL / 4 SKIPPED — identical to the accepted baseline;
  Book5-introduced Sensor failures = 0.
- Ruff: PASS on all R1-touched files (9 pre-existing findings in
  `test_book5_adversarial.py` unchanged from baseline — out of R1 scope).
- mypy: no issues in 43 source files.
- Freeze vs `a2526e822…`: only Book 5 modules, Book 5 tests, and append-only
  CSIA evidence/ledger files differ. Books 1–4 mutations = 0; Sensor mutations = 0.

## Status

```text
BOOK_5_HARDENING_R1 = PASS
BOOK_5_IMPLEMENTATION = COMPLETE_HARDENED
PROPOSED_EXIT_GATE = PASS_CSIA_BOOK5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_KERNEL (unchanged, still PROPOSED)
BOOK_5_ACCEPTANCE = NOT_SELF_ACCEPTED
BOOK_6 = NOT_STARTED
LIVE_ACQUISITION_AUTHORITY = FALSE
STATUS = READY_FOR_OPERATOR_ACCEPTANCE
```

Another hardening round (R2) is NOT started: it requires a newly demonstrated
concrete correctness defect.

## Limitations (unchanged, still explicit)

Offline deterministic kernel only — no live acquisition, RPC, CEX feeds,
persistent DB, graph DB, production scheduler, Book 6 valuation, production
pricing, or trading/execution authority.

---

# BOOK 5 HARDENING R2 — MANDATORY AUTHORITY CONTEXT + QUANTITATIVE CONTEXT CLOSURE (2026-09-29)

## Why R2 Existed

R1 made live Book 2 validation AVAILABLE at Book 5 authority boundaries — but
only when a provenance resolver happened to be supplied. R2 exists because
external review demonstrated that the validation was OPTIONAL at the exact
points that produce economic conclusions:

- **R2-D1** — `aggregate_same_unit(..., provenance=None)` downgraded to a bare
  enum check: UNKNOWN→`model_copy`(EXACT) aggregated WITHOUT a resolver.
- **R2-D1B** — `CapitalFieldSynthesis(provenance=None)` composed stripped,
  swapped, and detached-claim positions with no live-state validation.
- **R2-D2** — `validate_principal_component` skipped unbound claims
  (`binding is None: continue`): with a correct exact basis, unit, asset, and
  realization mutations all PASSED authority aggregation.

That distinction — validation available vs validation mandatory — is the core
defect. R2 makes validation MANDATORY at authority-producing boundaries and
closes quantitative context: NO CONTEXT BINDING ≠ CONTEXT VERIFIED.

## Repairs

- Mandatory provenance (no default None; explicit None raises typed
  `Book5ProvenanceError`) at `aggregate_same_unit`, `components_for`,
  `collapse_same_unit`, and `CapitalFieldSynthesis.__init__`; structural-only
  inspection split out as `inspect_components_for` (documented
  non-authoritative). Phase 8 central invariant: forgetting an optional
  argument can never change the epistemic strength of an output.
- Context-binding closure: unbound claims fail closed; bindings must agree
  with AND establish asset/unit context (realization too when present).
- Evidence-bound `ClaimContextBinding`: `basis_claim_refs` resolved through
  Book 2 at registration; raw dicts, duplicate identities, detached basis
  claims, and vacuous bindings refused. Honest limitation: Book 2 proves the
  basis claims canonical/current/evidenced; asset/realization/unit FIELDS are
  a Book 5-local typed contextual interpretation (the Book 2 Proposition
  schema cannot represent those dimensions).
- S4 closure (found by the attack matrix): position claim refs must cover
  nested component claim refs at compose time.

## Attacks Proven

- Phase 9 model_copy matrix D1–D11: every authority-producing operation
  revalidates live state (D7 documents the quantity-magnitude boundary
  honestly: magnitude-vs-claim verification lives in the evidence layer, not
  Book 2's Proposition schema).
- Phase 10 synthesis attacks S1–S10: only S10 (coherent canonical input) passes.

## Evidence

- R2 focused: 44 tests, 12 failing at the failure-first commit
  (R2-D1 ×4, R2-D1B ×4, R2-D2 ×4); all red before the corresponding seal.
- Prior Book 5 suite: 115 preserved; the defective adversarial assertion
  (`test_unknown_to_exact_mutation_refused_at_boundary`, which asserted the
  bypass itself) was replaced with the fail-closed invariant.
- Post-R2: Book 5 = 159 (115 + 44 R2); total CSIA = 687 (Book 1 = 107,
  Book 2 = 108, Book 3 = 83, Book 4 = 230 — unchanged).
- Sensor: 2325 PASS / 14 FAIL / 4 SKIPPED — failure set = i05r2 (3) +
  i05r3 (2) + i05r4 (3) + i06 (3) + i06r1 (3) storage evidence regen,
  identical to the accepted baseline; Book5-introduced Sensor failures = 0.
- Ruff: PASS — full Book 5 tree clean (31 findings fixed lint-only including
  the 9 pre-existing adversarial findings authorized this pass; behavior
  unchanged; no coverage removed; Books 1–4 untouched).
- mypy: no issues in 43 source files.
- Freeze vs `a2526e822…`: only Book 5 modules/tests and append-only CSIA
  evidence/ledger files differ. Books 1–4 mutations = 0; Sensor mutations = 0.

## Status

```text
BOOK_5_HARDENING_R2 = PASS
BOOK_5_IMPLEMENTATION = COMPLETE_HARDENED
PROPOSED_EXIT_GATE = PASS_CSIA_BOOK5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_KERNEL (unchanged, still PROPOSED)
BOOK_5_ACCEPTANCE = NOT_SELF_ACCEPTED
BOOK_6 = NOT_STARTED
LIVE_ACQUISITION_AUTHORITY = FALSE
STATUS = READY_FOR_OPERATOR_ACCEPTANCE
```

No R3 is started: another hardening round requires a newly demonstrated
concrete correctness defect.

## Limitations (unchanged, still explicit)

Offline deterministic kernel only — no live acquisition, RPC, CEX feeds,
persistent DB, graph DB, production scheduler, Book 6 valuation, production
pricing, or trading/execution authority.
---

# BOOK 5 HARDENING R3 — DERIVED-REFERENCE CLOSURE + NON-COMPONENT QUANTITATIVE CONTEXT SEAL (2026-09-29)

- Trigger: four newly demonstrated defect classes on the R2 kernel —
  R3-D1 forged `compose_path` stage refs produced `derived=True` paths
  (only `len(...) > 0` was checked); R3-D2 forged `topology_view`
  node/edge refs produced derived topologies; R3-D3
  `observed_value_display` rendered without live validation (a
  `model_copy(book2_claim_refs=())` fact displayed); R3-D4 the
  flow/liability/observed-fact validators proved only claim existence —
  `model_copy(unit="USDC")` on an ETH flow with identical canonical claim
  refs passed 5G composition.
- Closure: `QuantitativeRecordContextBinding` family (record kinds
  FLOW / LIABILITY / OBSERVED_FACT; asset/realization/unit/site/subject/
  reporter/numeraire dimensions; record-kind required-dimension table;
  NO BINDING != CONTEXT VERIFIED at every 5G non-component boundary) +
  `Book5CanonicalRecordRegistry` (in-memory, deterministic, offline;
  typed-only fail-closed registration after Book 2 + context + identity
  validation; UNKNOWN / DETACHED / WRONG-KIND resolution all REJECT) +
  registry-bound `compose_path` / `topology_view` (every ref resolves;
  duplicates REJECT; path order preserved; endpoint omissions carried as
  explicit Gaps, never fabricated nodes/stages) + `observed_value_display`
  live-validation seal (typed guard + Book 2 refs + context; display-only
  preserved; kind stays OBSERVED_COMMON_VALUE_FACT).
- model_copy R3 attack matrix (16 rows): P1–P3 path, T1–T4 topology,
  F1–F4 flow, L1–L4 liability, O1–O4 observed — every authority-producing
  path revalidates live state.
- Preservation: R1 37/37, R2 44/44, blocs 25/25 (45-row stress
  traceability + write-count-zero intact), adversarial 31/31 (T-1..T-14).
  One side repair in the context-seal commit: `compose_snapshot` no longer
  refuses facts-only inputs (an observed fact IS a canonical input; its
  refs were already isolated out of `liability_refs`).
- Counts: Book1=107, Book2=108, Book3=83, Book4=230 (all unchanged);
  Book5 159 → 205 (R3 adds 46 rows: 27 reproductions A1–A5/B1–B5/C1–C5/
  D1–D12 + 19 attack-matrix rows P/T/F/L/O); Total CSIA 687 → 733.
- Ruff: PASS full Book 5 (44 source files + tests). mypy: 44 files clean.
- Sensor: 2325 PASS / 14 FAIL / 4 SKIPPED — exact pre-existing
  storage-evidence regen set (i05r2×3, i05r3×2, i05r4×3, i06×3, i06r1×3);
  Book5-introduced Sensor failures = 0; Sensor mutations = 0.
- Freeze vs `a2526e822…`: only Book 5 modules/tests and append-only CSIA
  evidence/ledger files differ. Books 1–4 mutations = 0.
- Matrix: `CSIA_BOOK_5_HARDENING_R3_MATRIX.json` (21 gates, all PASS).
- Evidence: `CSIA_BOOK_5_HARDENING_R3_DERIVED_REFERENCE_CONTEXT_CLOSURE.md`.
- Commits: `97270f92` failing reproductions → `869be159` context binding +
  validator seal → `30bd16e5` registry → `ec2d5334` path/topology closure →
  `ddce5186` display seal → `25949c64` attack matrix (this doc + matrix +
  ledger in the final commit).

## Status

```text
BOOK_5_HARDENING_R3 = PASS
BOOK_5_IMPLEMENTATION = COMPLETE_HARDENED
PROPOSED_EXIT_GATE = PASS_CSIA_BOOK5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_KERNEL (unchanged, still PROPOSED)
BOOK_5_ACCEPTANCE = NOT_SELF_ACCEPTED
BOOK_6 = NOT_STARTED
LIVE_ACQUISITION_AUTHORITY = FALSE
STATUS = READY_FOR_OPERATOR_ACCEPTANCE
```

No R4 is started: another hardening round requires a newly demonstrated
concrete correctness defect. Next action: operator acceptance review of
Book 5.

## Limitations (unchanged, still explicit)

Offline deterministic kernel only — no live acquisition, RPC, CEX feeds,
persistent DB, graph DB, production scheduler, Book 6 valuation, production
pricing, or trading/execution authority. Context dimensions bound in R3 are
Book 5-local typed interpretations of canonical Book 2 claims, not fields
Book 2 natively encodes.

---

# BOOK 5 HARDENING R5 — BINDING-BASIS LIVE CURRENTNESS SEAL (2026-09-30)

## Trigger

Narrow, operator-authorized cycle: the R4 contract stated
**"BINDING REGISTRATION != PERMANENT BOOK 2 AUTHORITY"** but no provenance-module
code landed for binding-basis currentness. Both binding families validated their
basis claims **only at registration**; a binding whose subject claim stayed
current kept producing authority after its basis claim decayed through the
accepted Book 2 transition engine (STALE/CONTESTED/REJECTED/SUPERSEDED).
Demonstrated failure-first at base `a687268f`: 10 failed / 7 passed on the repro
matrix (A1×4, B1–B4, C2, Q2 raised DID NOT RAISE) before the seal.

## Doctrine — three independent dimensions

```text
REGISTRY MEMBERSHIP          != CURRENT AUTHORITY            (R4)
BINDING REGISTRATION         != CURRENT BINDING AUTHORITY    (R5)
SUBJECT CLAIM CURRENT        != BINDING BASIS CURRENT        (R5)
```

Central invariant: **BINDING EXISTS != BINDING CURRENTLY AUTHORITATIVE** —
registration proves VALID THEN; decision-time resolution proves VALID NOW.
Authority requires BOTH subject currentness AND binding-basis currentness.

## Seal

`Book5Provenance._validate_binding_basis_live(basis_claim_refs, *,
binding_family)` loops every basis ref through `self.resolve_claim` (live
currentness against CURRENT Book 2) and rejects non-current states with the
`BINDING REGISTRATION != PERMANENT BOOK 2 AUTHORITY — register a new explicit
binding` message. Called from exactly the two authority chokepoints —
`validate_principal_component` (ClaimContextBinding) and
`validate_quantitative_record` (QuantitativeRecordContextBinding) — so all
boundaries inherit it without caller duplication: `aggregate_same_unit`,
`components_for`, `collapse_same_unit`, `lineage_view`, `compose_snapshot`,
`collapse_request`, `observed_value_display`, registry `resolve`. The frozen
binding object is never mutated; context interpretation is immutable, epistemic
authority is not.

Registry position extension (closes the R4 nested gap): `registry.resolve` now
validates the nested `PrincipalComponent` set of a position entry through
`validate_principal_component` (isinstance-narrowed `CapitalPosition`). Chain
complete: registry currentness → record currentness → binding currentness →
binding basis currentness (S1; flows/liabilities/facts S2–S4 via R4 routing).

## Semantics pinned

- **Empty basis (`basis_claim_refs = ()`) is LEGAL**: the subject claim is the
  sole epistemic basis, already live-revalidated via the record/component's own
  claim refs; invariant is IF basis refs are present, ALL must be current
  (E1, E2 — empty basis does not disable subject live-validation).
- **Multi-basis weakest link**: any single decayed basis ref rejects, both
  families (M1–M3, MQ1–MQ2).
- **Supersession no-auto-follow**: a frozen binding referencing a SUPERSEDED
  basis stays REJECTED even though the replacement claim is current in the
  store; same-subject re-binding is refused; recovery = NEW subject claim + NEW
  explicit binding over the replacement (D1–D3).
- **Restoration**: STALE→OBSERVED restores (A6, B6, F2, L2); CONTESTED→
  CORROBORATED via the accepted P-4 route restores (A7) — the binding is not a
  tombstone.
- **Subject vs basis 2×2 distinct** for components (C1–C4) and flows (Q1–Q4).

## Verification

| Check | Prior | After R5 |
|---|---|---|
| Book 1 / 2 / 3 / 4 canonical | 107 / 108 / 83 / 230 | 107 / 108 / 83 / 230 (freeze intact) |
| Book 5 | 256 | 293 (+37 R5 rows) |
| Total CSIA | 784 | 821 |
| R1 / R2 / R3 / R4 focused | 37 / 44 / 46 / 51 | all preserved |
| 45 stress traceability rows | PASS | PASS (enforced by `test_stress_traceability_complete`) |
| ruff (CSIA src+tests) | PASS | PASS |
| mypy (CSIA module) | 44 files clean | 44 files clean |
| Sensor | 2325 P / 14 F / 4 S | 2325 P / 14 F / 4 S — failure set byte-equivalent to baseline (i05r2 ×3, i05r3 ×2, i05r4 ×3, i06 ×3, i06r1 ×3); BOOK5_INTRODUCED_SENSOR_FAILURES = 0 |

Freeze audit (`git diff --name-only a2526e822...HEAD`): only `book5_*` sources,
`test_book5_*` tests, and append-only research artifacts. Books 1–4 mutations =
0; Crypto Sensor mutations = 0.

## R4 evidence reconciliation (honest, no history rewritten)

R4's substantive results were correct and are not rewritten. R4's scope
statement claimed "BINDING REGISTRATION != PERMANENT BOOK 2 AUTHORITY" although
no provenance-module code for binding-basis currentness landed in R4. Recorded
explicitly: **R4 correctly closed registry-record currentness; R5 completes the
separately authorized binding-basis currentness clause that R4 did not
implement.**

## Status

```text
BOOK_5_HARDENING_R5 = PASS
BOOK_5_IMPLEMENTATION = COMPLETE_HARDENED
PROPOSED_EXIT_GATE = PASS_CSIA_BOOK5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_KERNEL (unchanged, still PROPOSED)
BOOK_5_ACCEPTANCE = NOT_SELF_ACCEPTED
BOOK_6 = NOT_STARTED
LIVE_ACQUISITION_AUTHORITY = FALSE
STATUS = READY_FOR_OPERATOR_ACCEPTANCE
```

No R6 is proposed; R6 requires another newly demonstrated concrete correctness
defect. Next action: operator acceptance review of Book 5.

Matrix: `CSIA_BOOK_5_HARDENING_R5_MATRIX.json` (27 gates, all PASS). Evidence:
`CSIA_BOOK_5_HARDENING_R5_BINDING_BASIS_CURRENTNESS.md`.
Commits: `b0778bb7f` failing repros → `dd183a414` seal → `ea4a81545` style →
`6960ada51` restoration/supersession/multi-basis/registry rows → `0a7f83853`
registry nested seal → `e181aa7e8` mypy narrowing → `7a347f34` E-rows (this
append + matrix + evidence + ledger in the final commit).

## Limitations (unchanged, still explicit)

Offline deterministic kernel only — no live acquisition, RPC, CEX feeds,
persistent DB, graph DB, production scheduler, Book 6 valuation, production
pricing, or trading/execution authority. Binding context dimensions remain
Book 5-local typed interpretations of canonical Book 2 claims, not fields Book 2
natively encodes.
