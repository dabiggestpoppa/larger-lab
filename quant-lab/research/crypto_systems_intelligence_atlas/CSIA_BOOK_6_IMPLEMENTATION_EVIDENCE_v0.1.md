# CSIA BOOK 6 — IMPLEMENTATION EVIDENCE v0.1

**Status:** `IMPLEMENTATION_COMPLETE_PENDING_OPERATOR_REVIEW`
**Acceptance:** `NOT_SELF_ACCEPTED`
**Date:** 2026-09-30
**Branch:** `agent/crypto-systems-intelligence-atlas-book6-build`
**Base:** `5c387f42b4a0e01e30d6a8554d8b67a04e4e98e4` (Book 5 acceptance commit)
**Proposed exit gate:** `PASS_CSIA_BOOK6_FUNDAMENTAL_MEASUREMENT_STATE_KERNEL`

---

## 1. What was built

The offline, deterministic Book 6 measurement and descriptive-state kernel.
Fourteen source modules and twelve test suites, 803 Book 6 tests, 1624 CSIA
tests total against a 821-test baseline.

Book 6 owns **measurement definitions** and **descriptive measured state**. It
measures OVER accepted truth; it never mints it. Book 2 remains the only
epistemic engine, and every authority-bearing read in Book 6 re-resolves its
cited Book 2 claim live through the accepted `ClaimStateEngine` machinery.

| Module | Responsibility |
|---|---|
| `book6_grammar.py` | 21 non-collapsible grammar categories, 10 missingness states, 6 denominator states, 10 window classes, 10 normalization types, architecture families |
| `book6_frozen.py` | The shared frozen record base that makes `model_copy` schema-safe |
| `book6_provenance.py` | Narrow Book 2 adapter; live currentness, no claim minting (D6M-1 = A) |
| `book6_definitions.py` | `MetricDefinition`, `MeasurementMethodology`, `CoverageObservation`, the 6A family map |
| `book6_records.py` | `MeasurementObservation`, `DenominatorRef`, value/missingness and window and supersession discipline |
| `book6_normalization.py` | The separate `NormalizationRule` contract (D6M-2 = B), `Cohort`, native-lineage validation |
| `book6_comparability.py` | The 15-row false-comparison corpus encoded as refusals |
| `book6_valuation.py` | Purpose-specific price authority (D6M-4 = A), Book 5 write-back refusal |
| `book6_states.py` | `StateRule`, `StateRuleRegistry`, `FundamentalStateVector`; ships zero ratified rules |
| `book6_registry.py` | Five separated in-memory stores with live authority resolution |
| `book6_sensitivity.py` | Methodology sensitivity and cross-source parity, descriptive only |
| `book6_traceability.py` | The executable validation matrix, 127 rows bound to real test functions |
| `book6_core.py` | `Book6MeasurementEngine` — the single fail-closed chokepoint |
| `book6_support.py` | Shared offline fixtures (Book 5 convention: fixtures live in `src/`) |

---

## 2. The five ratified decisions, as implemented

**D6M-1 = A — `BOOK6_LOCAL_DERIVED_RECORD`.** A `MeasurementObservation` is an
immutable Book 6-local record that *cites* Book 2 authority by ref through
`source_claim_refs`. It shares no epistemic field with a Book 2 claim: no
`claim_state`, no `claim_family`, no `claim_bindings`, no `conflicts`. The
`Book6Provenance` public surface is four read methods and nothing else — there is
no code path in Book 6 that can mint, promote or transition a Book 2 claim.

**D6M-2 = B — `SEPARATE_NORMALIZATION_RULE`.** Normalization is a separate
first-class contract binding eleven ratified fields. It is not a flag on a
`MetricDefinition` and not a field on a `MeasurementObservation`; both absences
are asserted by test. `NORMALIZED_WITHOUT_NATIVE_LINEAGE = INVALID` holds at
construction *and* at use, and lineage cannot be stripped or re-pointed after
construction.

`PERCENTILE_WITHIN_COHORT` is absent from `NormalizationType` by design. It is
rejected at four levels: absent from the enum, unconstructible from a raw string,
not injectable via `model_copy`, and not reachable through the engine — which
re-resolves the *registered* rule rather than trusting the caller's object.

**D6M-3 = A — `CENTRALIZED_OPERATOR_RATIFICATION`.**
`INDIVIDUAL_STATE_RULES_RATIFIED = 0` at bootstrap, and the registry holds zero
rules, so there is nothing to ratify by accident. `StateRuleRegistry.authorize`
is the single chokepoint: a Class B or C state cannot be emitted without naming
an individually `RATIFIED` rule. There is no delegation register, no bulk
ratification, no automatic ratification, and no module-level helper that could
constitute one.

Supersession was the one place the governance model was under-implemented — see
B6-D3 below. A new rule version now enters as `UNRATIFIED`, so authority decays
on a revision rather than riding along with it.

**D6M-4 = A — `PURPOSE_SPECIFIC_PRICE_AUTHORITY`.** There is no global
authoritative price-source class. `PRICE_AUTHORITY_MATRIX` maps each of seven
valuation purposes to its admissible price classes, and a test asserts that *no*
price class is admissible for *every* purpose, which is what makes a global
winner structurally unavailable. Divergent classes are preserved side by side;
the module exposes no averaging, blending or consensus combinator to call.

**D6M-5 — `OPEN / DEFERRED`.** No usage threshold, health state, adoption band,
retention threshold, bot/sybil classifier or persistence parameter exists
anywhere in Book 6. The D2-6 names are recorded in `PROHIBITED_STATE_NAMES` so
an attempt to inject one is a refusal rather than an unknown, and an AST scan
asserts that no Book 6 module imports a network, RPC, database or scheduler
client.

---

## 3. Six defects the implementation surfaced and fixed

These are recorded because the *tests* found them, not the other way round. Each
is a source fix, not a test adjustment.

**B6-D1 — `model_copy` was a constructor bypass for the anti-score firewall.**
Pydantic v2's `model_copy(update=...)` does not re-run validators and writes
unknown keys straight into the instance `__dict__`. A caller could execute
`vector.model_copy(update={"score": 0.9})` and then read `vector.score`. The
constructor firewall was real; the copy firewall was not.
`Book6FrozenModel` now re-validates the requested update against the model's own
fields, so an unknown key is a refusal. All sixteen Book 6 record types inherit
it. This is the single most important structural fix in the build: without it
the anti-score firewall would have been a documentation claim.

**B6-D2 — `DATA_COMPLETE` did not fail closed.** The status was computed from
observation missingness alone, so a vector of fully observed dimensions
reported `DATA_COMPLETE` with zero ratified coverage-sufficiency rules. Phase 25
requires that data completeness also need ratified sufficiency support. It now
does, and at bootstrap — where no sufficiency rule exists to name — data status
is `DATA_INCOMPLETE` regardless of how clean the observations are.

**B6-D3 — supersession was documented but unreachable.** `StateRuleRegistry`
described version supersession in its `ratify()` docstring, yet registering a new
version of an existing rule id raised `already registered` and there was no
other path. The registry is now actually able to supersede, retaining prior
versions in an append-only history.

**B6-D4 — the engine leaked a second error type.** `normalize()` raised
`NormalizationRuleError` for lineage failures and `Book6RegistryError` for a
decayed native input, so callers had to know which internal module refused them.
The engine is now a single fail-closed surface.

**B6-D5 — a forged valuation could strip its numeraire.** `authorize_valuation()`
checked only price-class admissibility. A `model_copy` that emptied `numeraire`
or `source_ref` still authorized. Both are now re-read at use.

**B6-D6 — denominator state was enforced at the wrong boundary.** A
non-divisible denominator (observed zero, unknown, unavailable, unstable) was
rejected at *construction*, which wrongly declared a legitimate record invalid.
It is now a valid record whose denominator state is explicit, and it is
*division* that fails closed — through the engine's typed `RatioResult`, which
returns `is_undefined=True` with `ratio=None` rather than infinity, zero, or a
dropped observation. A denominator declared `PRESENT` while carrying an observed
`0.0` is separately refused, because that is `ZERO`, not `PRESENT`.

---

## 4. Where the design refused to be helpful

Several places could have been made more permissive at no immediate cost. Each
was kept restrictive because the permissive version is the specific failure the
ratified plan exists to prevent.

- **No tolerance is invented for float agreement.** Two sources differing by
  `1e-12` are reported as `SOURCES_DIVERGE`. A tolerance is a Class C
  `tolerance_ref` requiring an individually ratified rule, and none is ratified;
  inventing one would smuggle a threshold in through the back door.
- **No preferred methodology.** `compare_methodology_variants` names no winner,
  no severity, no confidence. Preferring one methodology is a state derivation
  and would need a ratified rule.
- **No consensus number.** Divergent sources keep their own values. The naive
  mean of the fixtures does not appear anywhere in the finding.
- **A single source cannot be in parity with itself**, and a single methodology
  cannot be sensitive to itself. Both comparisons refuse.
- **An ungoverned metric pair is refused, not defaulted.** There is no wildcard
  and no implicit "everything numeric is comparable" path.
- **Generic `EXPANDING` / `CONTRACTING` are unwritable as a rule.** They are
  representable as enum members for vocabulary, but no `StateRule` may target
  them, so a label can never inherit its meaning from English.
- **A superseded observation is a separate record.** Nothing mutates a prior
  value; supersession is linear and a forked chain is refused.
- **A reorg is window-bounded.** `CHAIN_REORG` cannot restate measurements
  outside the reorged interval.

---

## 5. The seams hold structurally, not by convention

Both read-only seams are proven by import-graph analysis rather than by comment:

- **No Book 6 module imports a Book 5 module at all.** There is therefore no
  reference through which a numeraire, price or common-value scalar could be
  written back into a frozen Book 5 record. `BOOK5_CROSS_ASSET_VALUATION_AUTHORITY
  = FALSE` is structural.
- **No Book 6 module imports the Book 4 dependency graph.** Book 6 may measure
  degree, betweenness and concentration under a named methodology, but it holds
  no edge object, so `MEASUREMENT_OF_GRAPH != GRAPH_FACT` and no edge can be
  created, deleted or re-weighted.

---

## 6. Test counts

| Suite | Tests |
|---|---|
| `test_book6_core.py` | 20 |
| `test_book6_missingness.py` | 38 |
| `test_book6_normalization.py` | 47 |
| `test_book6_comparability.py` | 69 |
| `test_book6_valuation.py` | 44 |
| `test_book6_state_rules.py` | 82 |
| `test_book6_state_vector.py` | 97 |
| `test_book6_sensitivity.py` | 21 |
| `test_book6_temporal.py` | 40 |
| `test_book6_adversarial.py` | 52 |
| `test_book6_families.py` | 17 |
| `test_book6_traceability.py` | 276 |
| **Book 6 total** | **803** |
| **CSIA total** | **1624** (821 baseline + 803) |

The traceability suite is the largest because it is largely parametrized over the
127 matrix rows, each of which is resolved against the test sources on disk. A row
naming a function that does not exist, or that lives in a different file than it
cites, fails — so deleting an assertion breaks the matrix rather than silently
hollowing it out.

---

## 7. What this implementation does NOT do

- It does not acquire data. No RPC, no network call, no CEX feed, no database, no
  graph database, no scheduler, no dashboard. An AST scan of all fourteen Book 6
  modules asserts the absence of every such import.
- It does not execute any usage, health, bot/sybil, retention, capital-persistence
  or developer-persistence research. D6M-5 remains `OPEN_DEFERRED`; nothing here
  estimates a parameter.
- It does not ratify any state rule. `INDIVIDUAL_STATE_RULES_RATIFIED = 0`. The
  tests that exercise the Class B/C emission path use *synthetic local* fixtures,
  and one test explicitly asserts that such a fixture does not become canonical.
- It does not produce a score, total, rating, grade, rank, weight, buy, sell or
  health reading, in any field, from any direction.
- It does not modify Book 1–5 or the sensor. The freeze diff is 26 files, all
  `book6_*`.
- It does not accept itself.

---

## 8. Operator decisions still open

1. **Accept or reject `PASS_CSIA_BOOK6_FUNDAMENTAL_MEASUREMENT_STATE_KERNEL`.**
   This document proposes it and does not grant it.
2. **D6M-5.** Usage/health research remains deferred. Opening it would be a
   separate authorization, and would require live acquisition authority that is
   currently `FALSE`.
3. **Coverage sufficiency.** A vector cannot reach `DATA_COMPLETE` until an
   operator individually ratifies a coverage-sufficiency rule per metric. Whether
   to ratify any, and under what methodology, is an operator act.
4. **The fifteen false-comparison `CONDITIONAL` rows** each name a required
   methodology (`routing-attribution-methodology`, `native-unit-growth-methodology`,
   `success-semantics-methodology`, and so on). None is ratified, so all fifteen
   currently refuse. Ratifying any of them is an operator decision.
5. **Class B/C state rules.** Zero are ratified. The engine is correct and
   useless for directional state until the operator ratifies specific rules with
   specific benchmarks, tolerances and volatility measures.

---

**Proposed:** `PASS_CSIA_BOOK6_FUNDAMENTAL_MEASUREMENT_STATE_KERNEL`
**Not self-accepted.**

---

# APPENDIX — HARDENING R1 (authority closure)

**Round** Book 6 Hardening R1 · **Pre-R1 HEAD** `ebb20674` · **Status**
`HARDENING_R1_COMPLETE_PROPOSED` — **not self-accepted**

External review of the proposed implementation found four concrete authority
defects plus one related gap against the authorized design. All five shared a
single root cause: an authority-bearing check was satisfied by a bare string, a
self-declared field, or a caller-supplied number rather than by registry-resolved,
decision-time state. Two further defects of the same class were reproduced while
auditing for the repair (R1-D6, R1-D7).

Full narrative in `CSIA_BOOK_6_HARDENING_R1_AUTHORITY_CLOSURE.md`; gates in
`CSIA_BOOK_6_HARDENING_R1_MATRIX.json`.

## A1. Defects, before and after

| Id | Defect | Reproducer | Before | After |
|----|--------|-----------|--------|-------|
| R1-D1 | conditional comparison methodology spoof | FC-05 with `methodology_ref="fake:anything"` | `AUTHORIZED` | REFUSED |
| R1-D2 | valuation price source not Book-2-backed | `source_ref="fake:oracle"`, no cited claim | `AUTHORIZED` | REFUSED |
| R1-D3 | stale current price authorizes | 30-day-old price, 1-hour staleness bound | `AUTHORIZED` | REFUSED |
| R1-D4 | fake coverage-rule ref creates `DATA_COMPLETE` | `coverage_sufficiency_rule_refs=("fake:rule",)` | `DATA_COMPLETE` | `DATA_INCOMPLETE` |
| R1-D5 | methodology registry absent (design gap) | no methodology store on the registry | `NONE` | PRESENT |
| R1-D6 | normalized value accepted unverified | native 10 / divisor 2, supplied 999 | `AUTHORIZED` | REFUSED |
| R1-D7 | rule status forgery via `model_copy` | forged `RATIFIED` rule registered | `AUTHORIZED` | REFUSED AT REGISTRATION |

Each was reproduced against the accepted code at `ebb20674` before repair. The
permanent record is `test_book6_hardening_r1.py`.

## A2. Repairs

- **R1-D5 first, because it is the structural cause.** `book6_methodology.py`
  adds `Book6MethodologyRegistry` with versioned `ref@version` identity,
  supersession that retains history and stops authorizing, and local
  invalidation. Every authority-bearing surface now resolves against it: metric
  definitions, measurements, normalization rules, comparisons, valuation
  conversion methodology, state rules. This is structural Book 6 authority, not
  a second epistemic engine.
- **R1-D1.** A `CONDITIONAL` row requires the **exact** required identity
  (no substring, alias or version drift) **and** the methodology's own
  `authorized_corpus_row_ids` entry for that row. A new methodology version does
  not inherit the comparison.
- **R1-D2.** `PriceObservation.source_claim_refs` is required and resolved via
  `Book6Provenance` at valuation authority time. `source_ref` is an
  attribution, never evidence. Evidence-exists and admissible-for-purpose stay
  separate requirements, both tested in both failure directions.
- **R1-D3.** `authorize_current_valuation(as_of)` and
  `validate_historical_valuation()` replace one ambiguous API. `as_of` is always
  explicit; there is no hidden wall clock. `CURRENT UNAVAILABLE != HISTORICALLY
  INVALID`.
- **R1-D4.** `CoverageRuleRegistry` plus a registry-issued
  `CoverageSufficiencyAttestation`. `vector.data_status` is deliberately
  conservative; `Book6MeasurementEngine.data_status` is the live authority.
- **R1-D6.** `compute_normalized_value` recomputes deterministically and the
  engine refuses disagreement. `NormalizationRule` gained an explicit
  `base_measurement_ref` for `GROWTH_RATE`/`INDEX_TO_BASE`, and
  `SHARE_OF_TOTAL` now declares its cohort total as `denominator_ref`.
- **R1-D7.** Ratification moved into a registry-owned `RatificationLedger`
  shared by both rule registries. Rule objects may only be constructed and
  registered `UNRATIFIED`; authority is a decision record bound to one
  `(rule_id, version)` and decays on a revision.

## A3. Post-construction attack matrix

C1 comparison methodology · C2 normalization methodology · C3 valuation
conversion methodology · C4 price claim refs stripped · C5 price source swapped ·
C6 price class swapped · C7 staleness bound forged · C8 vector coverage rule refs ·
C9 coverage rule status forged · C10 coverage rule scope swapped — **all refused,
all re-validated live at the decision boundary.**

C5 is the informative one: swapping `source_ref` alone changes nothing, because
authority never came from that string.

## A4. Preserved seals

R1 regressed none of the 21 established Book 6 seals; each is re-asserted in the
`R1.PRESERVED_SEALS` traceability family.

## A5. Counts

| | before R1 | after R1 |
|---|---|---|
| Book 6 tests | 803 | **1094** |
| R1 focused suite | — | **93** |
| total CSIA | 1624 | **1915** |
| traceability rows | 121 | **213** (20 families) |
| sensor | 2325 / 14 / 4 | **2325 / 14 / 4** |
| ruff / mypy | pass | **pass** (61 source files) |

Books 1–5 unchanged: 107 / 108 / 83 / 230 / 293.

## A6. Exit state

```text
BOOK_6_HARDENING_R1 = PASS
BOOK_6_IMPLEMENTATION = COMPLETE_HARDENED_R1
BOOK_6_ACCEPTANCE = NOT_SELF_ACCEPTED
PROPOSED_EXIT_GATE = PASS_CSIA_BOOK6_FUNDAMENTAL_MEASUREMENT_STATE_KERNEL
BOOK_6_IMPLEMENTATION_AUTHORITY = TRUE / OFFLINE_KERNEL_SCOPE_ONLY
LIVE_ACQUISITION_AUTHORITY = FALSE
D6M_5 = OPEN_DEFERRED
INDIVIDUAL_STATE_RULES_RATIFIED = 0
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
```

**Still not self-accepted.** R1 created the mechanism by which a future operator
ratification could grant Class B/C authority or `DATA_COMPLETE` — and the
machinery by which its current absence is provable. It did not grant either.

---

# APPENDIX B — BOOK 6 HARDENING R2

> Canonical methodology content + executable state rules + per-metric coverage
> closure + historical authority honesty. Full derivation:
> `CSIA_BOOK_6_HARDENING_R2_DERIVATION_AND_HISTORICAL_AUTHORITY.md`.
> Gate matrix: `CSIA_BOOK_6_HARDENING_R2_MATRIX.json`.

## B1. Reproduced defects (failure-first, all before repair)

- **R2-D1** one caller-created `MeasurementMethodology` (right name, garbage
  formula, `FC-05` self-listed) registered and got the FC-05 comparison
  `AUTHORIZED`. Identity was still a namespace claim.
- **R2-D2** `emit_rule_gated_state` never evaluated `predicate_ref`:
  prior=100, current=50 with predicate `current_gt_prior` emitted `INCREASING`.
- **R2-D3** a forged attestation claiming scope {A,B} with only a live rule for
  A produced `DATA_COMPLETE` for both metrics through the engine.
- **R2-D4** the historical path shared one helper with current authorization and
  revalidated price claims with `require_current=True`, so a claim decayed AFTER
  observation retroactively erased the historical statement.

## B2. Repairs

1. **Content seal** — sha256 over the eleven canonical semantic fields
   (unordered collections sorted), bound at first registration inside the
   registry instance; `assert_content_matches` re-verifies live at every
   methodology-consuming boundary; the six CONDITIONAL corpus rows pin their
   full canonical specification and comparison compares the registered
   methodology's digest against the corpus-pinned digest. Row authority is
   checked against the ratified spec, not the registered object.
2. **Executable predicates** — new `book6_predicates.py`: closed three-member
   `EvaluatorKind` (`CURRENT_GREATER_THAN_PRIOR`, `CURRENT_LESS_THAN_PRIOR`,
   `EXACT_EQUALITY`), explicit `CURRENT_THEN_PRIOR` operand order, no eval/exec,
   no caller callables, registry ships empty,
   `PREDICATES_CANONICALLY_RATIFIED = 0`. Emission now requires
   RULE RATIFIED AND INPUTS CURRENT AND METHODOLOGY CURRENT AND PREDICATE TRUE;
   a false predicate is an explicit `PredicateNotSatisfied` non-emission and
   never inverts into the opposite state.
3. **Per-metric coverage closure** — `data_status` reconstructs sufficiency from
   registry state per metric and demands explicit set equality
   (`covered == required`); the attestation is an audit record, never authority
   (this deliberately supersedes the R1-D4 attestation mechanism, recorded);
   `CoverageReport` makes the equality inspectable; no partial attestations.
4. **Historical authority honesty** — Phase 12 audit: accepted Book 2 exposes raw
   history (`ClaimStore.history`, timestamped `TransitionEvent`s) but
   `can_promote_to_graph` is canonical-CURRENT-ONLY by design; Phase 13B
   therefore split the semantics without inventing a Book 2 feature:
   `validate_recorded_historical_shape` (record shape only, zero Book 2
   consultation) + `historical_authority_status` (reports
   `HISTORICAL_BOOK2_AUTHORITY_REPLAY = NOT_IMPLEMENTED`,
   `replay_available=False`, and `current_claims_backed` as a clearly-labelled
   separate fact). `PRESERVED_HISTORICAL_RECORD != REVALIDATED_HISTORICAL_AUTHORITY`.

## B3. Counts

| | before R2 | after R2 |
|---|---|---|
| Book 6 tests | 1094 | **1230** |
| R1 focused suite | 93 | **93** (preserved) |
| R2 focused suite | — | **46** |
| total CSIA | 1915 | **2051** |
| traceability rows | 213 (20 families) | **255 (25 families; 42 R2 rows)** |
| sensor | 2325 / 14 / 4 | **2325 / 14 / 4** (exact known set) |
| ruff / mypy | pass | **pass** (62 source files) |

Books 1–5 unchanged: 107 / 108 / 83 / 230 / 293.

## B4. Exit state

```text
BOOK_6_HARDENING_R2 = PASS (proposed)
BOOK_6_IMPLEMENTATION = COMPLETE_HARDENED_R2
PROPOSED_EXIT_GATE = PASS_CSIA_BOOK6_FUNDAMENTAL_MEASUREMENT_STATE_KERNEL
BOOK_6_ACCEPTANCE = NOT_SELF_ACCEPTED
LIVE_ACQUISITION_AUTHORITY = FALSE
D6M_5 = OPEN_DEFERRED
INDIVIDUAL_STATE_RULES_RATIFIED = 0 canonical
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0 canonical
PREDICATES_CANONICALLY_RATIFIED = 0
```

**Still not self-accepted.** R2 closed four reproduced caller-assertion defects
and recorded one accepted capability limitation (historical authority replay)
instead of faking it. It granted no authority anywhere.
