# CSIA BOOK 6 HARDENING R3 — STATE DERIVATION AUTHORITY BINDING

> **Status:** HARDENING_R3_COMPLETE_PROPOSED — **NOT self-accepted**
> **Date:** 2026-10-01
> **Branch:** `agent/crypto-systems-intelligence-atlas-book6-build`
> **Pre-R3 HEAD:** `392ae784a225c75c3aaac0ac8ec43912f1587e29`
> **Accepted implementation base:** `5c387f42b4a0e01e30d6a8554d8b67a04e4e98e4`
> **Scope:** Book 6 offline deterministic kernel only. No live acquisition, no RPC,
> no database, no graph DB, no Book 7/8/D8, no ranking, no composite score.
> No Book 1–5 or sensor mutation.

---

## 1. Why R3 exists

R2 made the state pipeline REPLAY its predicates and bound methodology identity
to content. Independent review then found the remaining correctness class in
the `StateRule → predicate → emitted StateDimension` chain: **the pipeline
verified names and replayed semantics, but nothing bound an operator's
ratification decision — or an emitted record's provenance — to the exact
executable content those names mean.** Three symptoms, one root:

| ID | Symptom | Before R3 | After R3 |
|----|---------|-----------|----------|
| R3-D1 | Evaluator contradicts its declared target | falling series emitted INCREASING | refused at predicate construction |
| R3-D2 | Ratification binds only a predicate NAME | decision written before the predicate existed | derivation-bound ratification; no late binding |
| R3-D3 | Emitted dimension claims a caller methodology | `methodology_ref='fake:other-methodology@9'` stored | derived from the authorized rule |

All three were reproduced failure-first (`quant-lab/scripts/book6_r3_repro_probe.py`,
deleted after repair; the permanent record is
`tests/crypto_systems_intelligence_atlas/test_book6_hardening_r3.py`).

---

## 2. R3-D1 — the evaluator/target semantic map

### 2.1 Reproducer

```
StatePredicateDefinition(
    predicate_id="predicate:lying-increasing", version="1",
    state_class=B_SPECIFICATION_ONLY,
    target_state=INCREASING,                      # declares INCREASING
    evaluator_kind=CURRENT_LESS_THAN_PRIOR,       # computes 50 < 100 = TRUE
    required_input_arity=2)
# bound to a locally ratified INCREASING rule; inputs prior=100, current=50
```

Under R2 the evaluator returned TRUE and the engine **emitted INCREASING for a
falling series** — every R2 replay check passed, because the lie was upstream of
them, in the declaration itself.

### 2.2 Repair (Phase 1/2)

```
EVALUATOR_TARGET_STATE = {
    CURRENT_GREATER_THAN_PRIOR -> INCREASING,
    CURRENT_LESS_THAN_PRIOR    -> DECREASING,
    EXACT_EQUALITY             -> UNCHANGED,
}
```

- Enforced in `StatePredicateDefinition._check_shape` — **registration-time
  refusal**: a lying predicate is invalid DATA and cannot exist, so no rule can
  ever bind one. (Pydantic v2 surfaces the `PredicateRegistryError` as
  `ValidationError`.)
- Targets outside the map are refused too: **all Class C targets
  (STABLE, VOLATILE, HIGHER_THAN_OWN_HISTORY, LOWER_THAN_OWN_HISTORY) are
  unconstructable as predicates.** No Class C evaluator semantics were invented;
  no generic EXPANDING/CONTRACTING predicate or rule can exist
  (`DEFERRED_GENERIC` + absent from the map).
- Verified: INCREASING+LESS_THAN, INCREASING+EXACT_EQUALITY,
  DECREASING+GREATER_THAN, UNCHANGED+GREATER_THAN → REJECT; the three correct
  pairings → PASS structurally. This grants **no canonical ratification**.

---

## 3. R3-D2 — derivation-bound ratification

### 3.1 Reproducer

```
register StateRule(predicate_ref="predicate:future@1")     # predicate unknown
ratify("staterule:r3:1")                                   # decision WRITTEN
register StatePredicateDefinition("predicate:future", "1") # semantics arrive LATER
```

Under R2 the ratification decision existed **before** the operator could have
seen any derivation. That violates `RATIFICATION LICENSES A DERIVATION METHOD`:
the method need not exist at decision time.

### 3.2 Phase 4 — predicate content fingerprint

The R2 doctrine `IDENTITY != CONTENT`, applied to predicates:
`PREDICATE_IDENTITY_BINDS_CONTENT`. `predicate_fingerprint()` is SHA-256 over a
deterministic serialization of **every** semantic field: `predicate_id`,
`version`, `state_class`, `target_state`, `description` (semantically
meaningful — it is what the operator reads), `required_input_arity`,
`evaluator_kind`, `operand_order`, `permitted_window_classes`,
`permitted_methodology_refs`. Unordered sets are sorted; equivalent content ⇒
same digest, any semantic mutation ⇒ different digest. No object identity, no
global singleton.

### 3.3 Phase 5 — the ratification binding

A new frozen `DerivationBinding` (in the ratification ledger module) records the
exact executable derivation context the operator approved:

```
rule_ref, rule_version,
predicate_identity, predicate_fingerprint,
methodology_identity, methodology_fingerprint,
required_measurement_refs          # the operand-order binding
```

plus a deterministic `digest` over the whole context.
`RULE RATIFIED WITH PREDICATE X != RULE AUTHORIZED WITH DIFFERENT CONTENT UNDER X`.

### 3.4 Phase 3/6/7 — the ratification API and D6M-3 = A

- `StateRuleRegistry.ratify` on a **wired** registry refuses any rule whose
  predicate does not already resolve canonically with matching target and class
  (**B1: no late binding**), and records the binding in the decision.
  Synthetic local fixtures ratify through this same path — there is no
  unbound route on a wired registry, no delegation, no bulk, no auto.
- **Wiring is engine-owned**: `Book6MeasurementRegistry` owns the
  `PredicateRegistry` and wires `state_rules` to it and to the methodology
  registry at construction. A bare `StateRuleRegistry()` (structural tests
  only, unreachable from the engine) still records decisions — honestly, with
  `binding=None` — and a wired `authorize` refuses binding-less decisions:
  **a low-level ledger entry is recorded history but never usable authority**
  (Phase 7 satisfied without leaving a bypass).

### 3.5 Phase 8 — live authorization replay

`authorize` now, on a wired registry: resolves the current rule, requires a
binding on the decision, rebuilds the live derivation binding (predicate
identity + content, methodology identity + R2 content digest, declared input
order) and compares digests. Any drift in a bound component ⇒
`RATIFIED THEN != AUTHORITATIVE NOW`. `RATIFIED THEN != AUTHORITATIVE NOW` is
now mechanical for derivation content, not just for rule versions.

### 3.6 Phase 3 matrix results

| Case | Scenario | Result |
|------|----------|--------|
| B1 | rule names unknown predicate → ratify | REJECT (`may not precede its predicate`) |
| B2 | predicate → rule → ratify | PASS; binding records every Phase 5 component |
| B3 | ratify against x@1; x@2 appears later | binding stays x@1; no silent follow; emission replays x@1 |
| B4 | bound predicate becomes unavailable | `authorize` refuses (`no longer current`); emission refuses |

### 3.7 Phase 13/14 — supersession doctrine

- `PredicateRegistry.supersede` makes a version bump an explicit named act
  (requires a prior version; refuses duplicates). A rule ratified against
  `x@1` remains bound to `x@1` when `x@2` appears; if `x@1` becomes
  unavailable the rule loses current authority. Using `x@2` requires a new
  StateRule version and a new individual ratification.
- Methodologies: a rule ratified against `methodology:m@1` does not follow
  `m@2` — the binding keeps `m@1`, preserving the governance cost deliberately.

---

## 4. R3-D3 — output methodology provenance

### 4.1 Reproducer

```
rule.methodology_ref = "book6-methodology@1"   (used for ALL authorization)
emit_rule_gated_state(..., methodology_ref="fake:other-methodology@9")
```

Under R2 the emitted `StateDimension.methodology_ref` was the caller's string:
`'fake:other-methodology@9'` — the record claimed a derivation that never ran.

### 4.2 Repair (Phase 9/10)

`emit_rule_gated_state` now **derives** the output methodology from the
already-authorized canonical rule; the caller argument survives only as an
exact-equality cross-check (divergence is refused before anything is stored):

```
DERIVATION USED METHODOLOGY A → OUTPUT MAY NOT CLAIM METHODOLOGY B
```

The stored dimension records the canonical resolved rule methodology, never
caller text. Phase 10 coherence is asserted field-by-field: `state`,
`state_class`, `state_rule_ref`, `methodology_ref`, `measurement_refs` all
correspond to the actual derivation (predicate identity is pinned indirectly
through the rule's ratification binding).

---

## 5. Phase 11 — the S1–S10 model_copy attack matrix

| Attack | Boundary that catches it | Result |
|--------|--------------------------|--------|
| S1 rule `predicate_ref` mutated | live binding rebuild → digest mismatch / unresolvable | REJECT |
| S2 rule `methodology_ref` mutated | binding digest mismatch (methodology identity) | REJECT |
| S3 rule `required_measurement_refs` reordered | binding input-order component | REJECT |
| S4 rule target mutated | `authorize` target check | REJECT |
| S5 rule state_class mutated | binding class check | REJECT |
| S6 predicate content drifted (description) | live predicate fingerprint mismatch | REJECT |
| S7 predicate target mutated | unconstructable (R3-D1 map) | REJECT |
| S8 predicate operand_order mutated | one-member closed enum — nothing to mutate into | REJECT (closure asserted) |
| S9 predicate permitted methodology set mutated | live predicate fingerprint mismatch | REJECT |
| S10 emitted methodology_ref forged | derived-provenance cross-check | REJECT |

Plus Phase 15 negative/positive replays (50/100 → no emission; 150/100 →
emission through the full binding; 100/100 → UNCHANGED only under a bound
EXACT_EQUALITY rule) and the standing rule that a FALSE state never inverts
into its opposite.

---

## 6. Phase 16 — dimension_id audit (scoped, closed)

Audited, deliberately **not** expanded. `dimension_id` is caller-supplied in
the current contract — a schema-local label. Facts bounding that audit: (1)
every emitted Class B/C dimension carries its rule ref, ratification-bound
predicate identity, methodology and measurement refs coherently (Phase 10), so
the DERIVATION is fully identified even where the label is free; (2) for
engine-built vectors, `FundamentalStateVector.dimension_metric_ids` treats
`dimension_id` as the metric-definition reference, where it is not free at all.
No reproducer showed a state derived from metric A misrepresented as a
different governed dimension B in a way the ratified plan forbids beyond this
documented contract. **No R3-D4 recorded; no dimension-ontology project
started.** (`test_r3_phase16_dimension_id_is_a_schema_local_label` pins this.)

---

## 7. Phase 17 — R1/R2 preservation

All 93 R1-focused and 46 R2-focused tests pass. The R2 gates were **strengthened,
not weakened**: three R2 tests exercised the now-closed late-binding path and
were updated to assert the earlier (ratification-time) refusal; no R2 assertion
was removed. The comparison content seal, per-metric coverage closure,
attestation-not-authority, historical replay honesty, normalization
recomputation, price provenance and stale-price rejection are all intact
(`test_r3_phase17_r2_seals_survive_at_the_state_boundary`).

Ratification counts remain: `INDIVIDUAL_STATE_RULES_RATIFIED = 0` canonical,
`PREDICATES_CANONICALLY_RATIFIED = 0`, `COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0`
canonical.

---

## 8. Quality gates (Phase 21)

| Gate | Before R3 | After R3 |
|------|-----------|----------|
| Book 6 suite | 1230 PASS | **1341 PASS** |
| R1 / R2 focused | 93 / 46 | **93 / 46** |
| R3 focused | — | **45 PASS** |
| Total CSIA | 2051 PASS | **2162 PASS** |
| Sensor | 2325 / 14 / 4 | **2325 / 14 / 4** (exact canonical failure set) |
| Ruff | PASS | **PASS** |
| mypy | PASS (62 files) | **PASS (62 files)** |

Freeze vs `5c387f42b4a0e01e30d6a8554d8b67a04e4e98e4`: every changed file is a
`book6_*` file or a Book 6 research artifact — Book 1–5 and sensor mutation
counts are all **0**.

---

## 9. What R3 deliberately does NOT do

- No canonical StateRule, predicate, or coverage rule ratified.
- No Class C evaluator semantics invented; no generic EXPANDING/CONTRACTING.
- No dimension ontology; no R3-D4 without a reproducer.
- No Book 1–5 or sensor mutation; no live acquisition, RPC, DB, graph DB.
- No R4: R4 requires another NEW concrete demonstrated defect.

## 10. Proposed exit state

```
BOOK_6_HARDENING_R3      = PASS (proposed)
BOOK_6_IMPLEMENTATION    = COMPLETE_HARDENED
PROPOSED_EXIT_GATE       = PASS_CSIA_BOOK6_FUNDAMENTAL_MEASUREMENT_STATE_KERNEL
BOOK_6_ACCEPTANCE        = NOT_SELF_ACCEPTED
STATUS                   = READY_FOR_OPERATOR_ACCEPTANCE
LIVE_ACQUISITION_AUTHORITY = FALSE
D6M_5                    = OPEN_DEFERRED
INDIVIDUAL_STATE_RULES_RATIFIED      = 0 canonical
PREDICATES_CANONICALLY_RATIFIED      = 0
COVERAGE_SUFFICIENCY_RULES_RATIFIED  = 0 canonical
```

Exact next operator action: **formal Book 6 operator acceptance review** against
`CSIA_BOOK_6_HARDENING_R3_MATRIX.json` and the R1/R2 matrices — accept at the
proposed exit gate, or return with a NEW concrete demonstrated defect (which
alone opens R4).
