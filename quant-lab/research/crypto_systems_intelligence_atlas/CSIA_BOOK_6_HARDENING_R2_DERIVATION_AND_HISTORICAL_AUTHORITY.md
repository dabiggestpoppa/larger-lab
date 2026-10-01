# CSIA BOOK 6 HARDENING R2 — DERIVATION AND HISTORICAL AUTHORITY

> **Status:** HARDENING_R2_COMPLETE_PROPOSED — **NOT self-accepted**
> **Date:** 2026-10-01
> **Branch:** `agent/crypto-systems-intelligence-atlas-book6-build`
> **Pre-R2 HEAD:** `20cf880cd5e378e7d59ebe727e385a3eeffb5b61`
> **Accepted implementation base:** `5c387f42b4a0e01e30d6a8554d8b67a04e4e98e4`
> **Scope:** Book 6 offline deterministic kernel only. No live acquisition, no RPC,
> no database, no graph DB, no Book 7/8/D8, no ranking, no composite score.
> No Book 1–5 or sensor mutation. No Book 2 historical-feature invention.

---

## 1. Why R2 exists

Independent review of the R1-hardened kernel found four NEW concrete defects.
R1's repairs had each replaced a bare string or self-declared field with a
registry lookup — but in three of the four R2 cases the *registry lookup itself*
could still be satisfied by content the CALLER supplied. The common shape:

> **An authority boundary was checking that a claim was made, not that the claim
> was true of anything the operator ratified.**

| ID | One-line defect | R1 state | R2 state |
|----|-----------------|----------|----------|
| R2-D1 | Methodology identity is caller-self-asserted | `AUTHORIZED` | `REFUSED` |
| R2-D2 | Ratified StateRule emitted without executing its predicate | `INCREASING` emitted for a falling series | `PredicateNotSatisfied` non-emission |
| R2-D3 | Multi-metric `DATA_COMPLETE` trusts a forged attestation scope | `DATA_COMPLETE` | `DATA_INCOMPLETE` |
| R2-D4 | Historical valuation revalidates price claims as CURRENT | `REFUSED` after decay | record PRESERVED, honestly reported |

All four were reproduced with failure-first probes **before** repair
(`quant-lab/scripts/book6_r2_repro_probe.py`, since deleted; the permanent record
is `tests/crypto_systems_intelligence_atlas/test_book6_hardening_r2.py`).

---

## 2. R2-D1 — METHODOLOGY IDENTITY BINDS CONTENT

### 2.1 The reproducer

```
MeasurementMethodology(
    methodology_ref="routing-attribution-methodology",
    version="1",
    formula="garbage", window_rule="garbage", denominator_rule="garbage",
    source_selection="garbage", identity_rule="garbage",
    authorized_corpus_row_ids=("FC-05",),
)
# register it, then authorize the FC-05 comparison with
# methodology_ref="routing-attribution-methodology@1"
```

Under R1: **`AUTHORIZED`**. R1 compared an exact identity (1) and a row list (3),
and one caller-built object satisfied both simultaneously.

### 2.2 Design selected — Design A (content fingerprint, Phase 1/2)

Requirements: no Python object identity, no hidden global mutable singleton,
deterministic canonical ordering, equivalent content ⇒ same digest, any semantic
mutation ⇒ different digest.

**Mechanism** (`book6_methodology.py`):

- `METHODOLOGY_CANONICAL_FIELDS` — the eleven semantic fields:
  `methodology_ref, version, formula, parameters, window_rule, filters,
  denominator_rule, source_selection, identity_rule, input_methodology_refs,
  authorized_corpus_row_ids`.
- `canonical_methodology_spec()` — compact JSON over the fields in fixed order;
  the four unordered collections (`parameters`, `filters`,
  `input_methodology_refs`, `authorized_corpus_row_ids`) are **sorted** first, so
  a cosmetic reordering cannot masquerade as a different methodology.
- `methodology_fingerprint()` — SHA-256 over that serialization.
- `Book6MethodologyRegistry._fingerprints` — identity → digest, bound at FIRST
  registration inside the same registry instance that owns the methodology. No
  globals; each engine's registry carries its own bindings.
- `assert_content_matches(identity, candidate)` — refuses any later object whose
  presented digest differs from the bound one. Because Pydantic v2
  `model_copy(update=...)` does NOT re-run validators, this live re-verification
  at every authority boundary is the only honest check.

### 2.3 Comparison authority (Phase 3)

`require_comparison_authority` now enforces three conditions:

1. the supplied identity **equals** the identity the ratified corpus row
   requires (no substring match, no alias);
2. the registered methodology's **content digest** equals the digest of the
   canonical specification pinned by the ratified corpus row;
3. the **ratified canonical specification itself** lists the corpus row in its
   `authorized_corpus_row_ids`.

Note on condition 3: checking the *registered* object would have been dead code
— condition 2 already pins the registered row set to the corpus row set. As
written, condition 3 is a live self-consistency invariant on the corpus: a
corpus row may never license itself through a methodology specification that
does not name that row.

The six CONDITIONAL corpus rows (FC-05, FC-07, FC-09, FC-12, FC-14, FC-15) each
embed their full canonical `MeasurementMethodology` specification
(`CorpusRow.required_methodology_spec`), with `required_methodology` and
`required_methodology_fingerprint` derived properties so they cannot drift.
The specification lives in the ratified corpus module — ratified data, not
runtime caller input.

### 2.4 Phase 3 failure tests

| Test | Result |
|------|--------|
| A1 exact identity + fake formula | `REFUSED` (content seal) |
| A2 exact identity + fake authorized row set | `REFUSED` (row set is inside the digest) |
| A3 exact identity + altered denominator rule | `REFUSED` |
| A4 exact identity + altered source-selection rule | `REFUSED` |
| A5 canonical exact methodology | `AUTHORIZED` (preserved) |
| A6 canonical methodology superseded | `REFUSED` until the corpus explicitly licenses the new version (R1 governance cost preserved) |

### 2.5 Phase 15/16 — methodology use surfaces re-audited

The content seal is enforced on every methodology-consuming surface, not only
comparison: measurement registration (`register_measurement` →
`_ensure_methodology` → `assert_content_matches`), metric-definition
registration (`register_definition` → `require_canonical_methodology`), the
registry-level `require_canonical_methodology`, and normalization rules
(`validate_rule_methodology` + content seal). Verified by M1/M2/M3 parametrized
`model_copy` attacks (formula, row set, input refs) at registration boundaries.

---

## 3. R2-D2 — EXECUTABLE STATE RULES

### 3.1 The reproducer

```
prior = 100.0, current = 50.0
synthetic StateRule: target=INCREASING, predicate_ref="predicate:current_gt_prior@1"
locally ratified via the existing R1 synthetic mechanism
engine.emit_rule_gated_state(INCREASING, ...)
```

Under R1: **`INCREASING` emitted** — the predicate was never evaluated.

### 3.2 Governing invariant (Phase 4)

```
RATIFIED RULE  !=  TRUE PREDICATE
```

Ratification licenses a derivation METHOD; it does not assert the method's
OUTCOME. Emission requires all four together:

```
RULE RATIFIED  AND  INPUTS CURRENT  AND  METHODOLOGY CURRENT
  AND  PREDICATE EVALUATES TRUE
```

### 3.3 Predicate registry design (Phase 5) — `book6_predicates.py` (new)

- `EvaluatorKind` — closed three-member enumeration:
  `CURRENT_GREATER_THAN_PRIOR`, `CURRENT_LESS_THAN_PRIOR`, `EXACT_EQUALITY`.
  Adding a kind is an explicit code change; a caller cannot introduce an
  evaluator by supplying a string.
- `OperandOrder` — `CURRENT_THEN_PRIOR` (the only member). Operand order belongs
  to the rule's declared measurement refs, not caller convention.
- `StatePredicateDefinition` — frozen model: `predicate_id`, `version`,
  `state_class` (Class B/C only), `target_state`, `required_input_arity`,
  `evaluator_kind`, window/methodology constraints.
- `evaluate_predicate()` — the ONLY place a truth value is produced: a closed
  `match` over the enum. **No `eval`, no `exec`, no code execution from strings,
  no caller-supplied callable at authority time.**
- `PredicateRegistry` — deterministic offline store; ships EMPTY of authority.
- `PredicateNotSatisfied` — explicit non-emission carrying `predicate_id` and
  `operands`, so the refusal is inspectable.
- `PREDICATES_CANONICALLY_RATIFIED = 0` — exactly like
  `INDIVIDUAL_STATE_RULES_RATIFIED = 0`. Synthetic fixtures only; the
  architecture is proven, no authority is granted.

### 3.4 Binding and replay (Phase 6/7)

At `emit_rule_gated_state` the engine now, in order: resolves live rule
authority through the ratification ledger; re-resolves the rule's methodology;
refuses unless `measurement_refs == rule.required_measurement_refs` EXACTLY
(explicit input ordering); resolves each input via `resolve_current` (refusing
absent values — a predicate may not be evaluated through missingness); enforces
the rule's window-class constraint per input; resolves the canonical predicate;
checks predicate target / state class / methodology constraints against the rule
and target; evaluates; and only then emits. A false predicate raises
`PredicateNotSatisfied`. **The opposite state is never inferred:**
`FALSE INCREASING != DECREASING` — inverting a verdict is itself a directional
claim requiring its own separately ratified rule.

### 3.5 Phase 8 — Class C remains locked

No Class C threshold was invented. `STABLE`, `VOLATILE`,
`HIGHER_THAN_OWN_HISTORY`, `LOWER_THAN_OWN_HISTORY` remain unavailable
canonically. `INDIVIDUAL_STATE_RULES_RATIFIED = 0` canonical throughout.

---

## 4. R2-D3 — PER-METRIC COVERAGE CLOSURE

### 4.1 The reproducer

```
metrics A, B (both observed); live ratified rule:A scoped to metric A ONLY
forged CoverageSufficiencyAttestation(
    rule_ids=("rule:A",), scope_metric_ids=("metric:A", "metric:B"), ...)
vector dimensions: A + B; coverage_sufficiency_rule_refs: ("rule:A",)
```

Under R1: `vector.data_status == DATA_COMPLETE` **and**
`engine.data_status(vector) == DATA_COMPLETE` while metric B had no rule.
Under R2: the engine returns **`DATA_INCOMPLETE`** and `coverage_report` names
`metric:B` as uncovered.

### 4.2 Design (Phase 9/10)

`Book6MeasurementEngine.data_status` now RECONSTRUCTS sufficiency from registry
state, per metric:

```
covered = { m in required :
              some named rule is registered,
              currently ratified (live ledger check),
              and scoped EXACTLY to m }
DATA_COMPLETE  iff  covered == required          (explicit SET EQUALITY)
```

- The attestation is demoted to an **audit record**. It may accelerate
  diagnostics; it is never the source of truth:
  `ATTESTATION CLAIMS SCOPE != REGISTRY PROVES SCOPE`.
- `CoverageReport` (new, `book6_coverage_rules.py`) makes the set equality
  inspectable: `required_metric_ids`, `covered_metric_ids`,
  `uncovered_metric_ids`, status, per-metric reasons — with a validator that
  refuses a metric being both covered and uncovered.
- Phase 10 attacks, all failing closed: forged `registry_identity`, forged
  scope, extra metric, missing metric, duplicate rules, unrelated live rule.
- Phase 11: `registry.attest()` still issues NO partial attestation — with one
  metric lacking a live rule it returns `None` rather than letting a rule for A
  stand in for B. Engine-built vectors are unaffected where every metric is
  covered.

Deliberate supersession, recorded: R1's C8 test asserted that stripping the
attestation must flip `data_status` to `DATA_INCOMPLETE` — that WAS the R1-D4
mechanism. R2 Phase 10 reverses exactly that mechanism (attestation = evidence,
not authority), so the R1 assertion now asserts the R2 doctrine and the fake-
rule-refs-fail-closed gate from R1 C8 is preserved in the same test.

---

## 5. R2-D4 — HISTORICAL AUTHORITY HONESTY

### 5.1 The defect

`validate_historical_valuation()` shared one authority helper with current
authorization, and that helper resolved price claims with
`require_current=True`. A price claim valid at the valuation's observation time,
later decayed to STALE / SUPERSEDED / REJECTED through Book 2's own
`ClaimStateEngine`, made the historical validation **REFUSE** — retroactively
erasing a historical statement and contradicting the doctrine:

```
CURRENT UNAVAILABLE  !=  HISTORICALLY INVALID
```

### 5.2 Phase 12 — the decisive Book 2 audit (done BEFORE changing code)

Accepted Book 2 inspected, not assumed:

| Capability | Verdict |
|------------|---------|
| `ClaimStore.history(claim_id) -> tuple[Claim, ...]` | EXISTS — raw history is exposed |
| `ClaimStore.transitions -> tuple[TransitionEvent, ...]` with `transitioned_at` | EXISTS — timestamped transitions are exposed |
| "Was this claim authoritative at valid_time T?" | **DOES NOT EXIST** |
| Bitemporal authority replay | **DOES NOT EXIST** |
| `can_promote_to_graph(claim, claim_store)` (claims.py) | exists, but is **canonical-CURRENT-ONLY by design**: `if claim_store.require(claim.claim_id) != claim: return False` |

**⇒ Phase 13B applies.** Book 2 does not support historical epistemic
validation, and Phase 13B forbids faking it: re-deriving
`can_promote_to_graph` bitemporally inside Book 6 would invent a Book 2
feature, mutate accepted Book 2, and stand up a second epistemic engine. Book 2
was not mutated during R2.

### 5.3 The honest split (Phase 13B / 14)

- **`validate_recorded_historical_shape(valuation)`** proves RECORD SHAPE and
  nothing more: explicit numeraire, non-empty price attribution,
  purpose/class admissibility (D6M-4 = A), resolvable conversion methodology,
  and the price not already stale at the valuation's own `observed_at`. It
  deliberately consults Book 2 ZERO times, so it can neither assert nor deny
  historical epistemic backing.
- **`historical_authority_status(valuation)`** returns a
  `HistoricalAuthorityReport`: `record_shape_valid` (preserved historical
  record), `current_claims_backed` (current authority, clearly labelled as a
  separate fact), and `replay_available = False` with the audit reason.
- **`HISTORICAL_BOOK2_AUTHORITY_REPLAY = "NOT_IMPLEMENTED"`** — recorded
  capability limitation. The report's validator is bound to the MODULE constant,
  so while the capability is absent a forged report claiming
  `replay_available=True` is invalid DATA, not merely a wrong field.
- `authorize_current_valuation(as_of=...)` still hard-requires current Book 2
  price authority (R1-D2 preserved). No hidden wall clock anywhere.

### 5.4 Phase 14 historical matrix results

| Case | Scenario | Result |
|------|----------|--------|
| H1 | current price / current claim | current authorization **PASS** |
| H2 | stale-now claim | current authorization **REJECT** |
| H3 | record once valid, price stale by clock only | record **PRESERVED** |
| H4 | price claim later STALE | record preserved; `current_claims_backed=False`; `replay_available=False` |
| H5 | price claim later SUPERSEDED | exercised via the Book 2 claim matrix (supersession needs a replacement claim under Book 2 law); the reachable decay modes both show: record preserved, current backing gone, no authority claimed |
| H6 | price claim later REJECTED | same honest preservation as H4 |
| — | no false PASS | the historical path cannot be used to obtain current authority (`ValuationError: no current Book 2 authority`) |

**`PRESERVED_HISTORICAL_RECORD != REVALIDATED_HISTORICAL_AUTHORITY`. No false
PASS exists anywhere on this surface.**

---

## 6. Phase 17 — model_copy R2 attack matrix

Every authority boundary re-resolves canonical state live (Pydantic v2
`model_copy(update=...)` does not re-run validators, so boundary revalidation —
not model validators — is the seal):

| Attack | Boundary | Result |
|--------|----------|--------|
| M1 methodology formula mutated | registration + comparison seal | refused |
| M2 methodology authorized row set mutated | registration + comparison seal | refused |
| M3 methodology input refs mutated | registration + normalization seal | refused |
| S1 state rule `predicate_ref` mutated | engine resolves the REGISTERED rule's predicate live | grants nothing |
| S2 state rule target mutated | registry `authorize` checks the registered rule's target | refused |
| S3 measurement ordering swapped | engine requires exact `required_measurement_refs` order | refused |
| S4 predicate target mismatched | engine checks predicate target vs rule target | refused |
| C1 attestation scope widened | engine ignores attestation scope | `DATA_INCOMPLETE` |
| C2 attestation registry identity forged | engine ignores attestation identity | `DATA_INCOMPLETE` |
| C3 coverage rule list reduced | per-metric set equality | `DATA_INCOMPLETE`, metric named |
| C4 unrelated live coverage rule inserted | per-metric scope equality | `DATA_INCOMPLETE` |
| H1 historical/current authority confused | split APIs; historical path cannot authorize currently | refused / honestly reported |

---

## 7. Phase 18 — R1 preservation

All 93 R1-focused tests pass unchanged in intent. R1 gates preserved:
methodology registry; exact comparison methodology identity; price Book 2
provenance; current stale-price rejection; coverage-rule registry; normalized
recomputation; normalization input metric closure; state/coverage rule
status-forgery seal; Book 2 price decay; R1 C1–C10; all 21 prior Book 6 seals.

The ONE deliberate, narrow supersession is documented in §4.2: the R1-D4
attestation mechanism inside C8, which R2 Phase 10 replaces by doctrine with a
demonstrated defect (R2-D3). Nothing else about R1 changed.

Ratification counts remain: `INDIVIDUAL_STATE_RULES_RATIFIED = 0` canonical,
`COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0` canonical,
`PREDICATES_CANONICALLY_RATIFIED = 0`.

---

## 8. Quality gates (Phase 22)

| Gate | Before R2 | After R2 |
|------|-----------|----------|
| Book 6 suite | 1094 PASS | **1140 PASS** (1094 + 46 R2) |
| R1-focused | 93 PASS | **93 PASS** |
| R2-focused | — | **46 PASS** |
| Total CSIA | 1915 PASS | **2045 PASS** |
| Sensor | 2325 / 14 / 4 | **2325 / 14 / 4** (identical known set; 0 Book6-introduced) |
| Ruff | PASS | **PASS** |
| mypy | PASS (61 files) | **PASS (62 files)** |

Freeze vs `5c387f42b4a0e01e30d6a8554d8b67a04e4e98e4`: Book 1–5 and sensor
mutation counts all **0** (verified by path-scoped diff; see
`CSIA_BOOK_6_HARDENING_R2_MATRIX.json` gates BOOK1_FREEZE … SENSOR_BASELINE_EQUIVALENCE).

---

## 9. What R2 deliberately does NOT do

- No canonical StateRule ratified; no canonical coverage rule ratified; no
  canonical predicate ratified.
- No Class C thresholds invented.
- No Book 2 bitemporal replay implemented or simulated.
- No Book 1–5 or sensor mutation.
- No R3: none of these repairs was made without a reproduced defect, and no new
  defect is claimed.
- Book 6 remains NOT self-accepted. `LIVE_ACQUISITION_AUTHORITY = FALSE`;
  `D6M_5 = OPEN_DEFERRED`.

---

## 10. Proposed exit state

```
BOOK_6_HARDENING_R2      = PASS (proposed)
BOOK_6_IMPLEMENTATION    = COMPLETE_HARDENED_R2
PROPOSED_EXIT_GATE       = PASS_CSIA_BOOK6_FUNDAMENTAL_MEASUREMENT_STATE_KERNEL
BOOK_6_ACCEPTANCE        = NOT_SELF_ACCEPTED
LIVE_ACQUISITION_AUTHORITY = FALSE
D6M_5                    = OPEN_DEFERRED
INDIVIDUAL_STATE_RULES_RATIFIED      = 0 canonical
COVERAGE_SUFFICIENCY_RULES_RATIFIED  = 0 canonical
PREDICATES_CANONICALLY_RATIFIED      = 0
```

Exact next operator action: run the sensor baseline comparison and the
45-item review checklist against `CSIA_BOOK_6_HARDENING_R2_MATRIX.json`, then
either accept Book 6 at the proposed exit gate or return it with a NEW concrete
demonstrated defect (which would open R3).
