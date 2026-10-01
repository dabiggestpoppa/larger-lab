# CSIA — Book 6 Hardening R1 · Authority Closure

**Document** `CSIA_BOOK_6_HARDENING_R1_AUTHORITY_CLOSURE`
**Version** v0.1 · **Date** 2026-09-30
**Branch** `agent/crypto-systems-intelligence-atlas-book6-build`
**Pre-R1 HEAD** `ebb20674d64740740f4c130ae5c30973ff275002`
**Implementation base** `5c387f42b4a0e01e30d6a8554d8b67a04e4e98e4` (Book 5 acceptance)
**Status** `HARDENING_R1_COMPLETE_PROPOSED` — **not self-accepted**

---

## 1. What R1 was

The accepted Book 6 implementation was reviewed externally and four concrete
authority defects were reported, plus one related gap against the authorized
design. This round did exactly one thing: **close those authority holes**. It
did not generic-harden unrelated surfaces.

All five reported problems shared one root cause, and naming it is most of the
value of this round:

> An authority-bearing check was satisfied by a **bare string**, a
> **self-declared field**, or a **caller-supplied number** — instead of by
> registry-resolved, decision-time state.

The accepted kernel was not careless. It was *correct about Book 2* — every
measurement re-resolved its cited claims live — while simultaneously trusting
three other kinds of evidence that it never re-resolved at all. R1 replaces
each of those with a registry that is consulted at the moment of use.

---

## 2. Reproduced defects

Every defect below was reproduced against the **accepted** code at
`ebb20674` before any repair, using a throwaway probe run from
`quant-lab/scripts/`. That probe was deleted after the repair; the permanent
record is `tests/crypto_systems_intelligence_atlas/test_book6_hardening_r1.py`,
which asserts each defect is now refused.

### R1-D1 · CONDITIONAL COMPARISON METHODOLOGY SPOOF

`authorize_comparison` gated a `CONDITIONAL` corpus row with
`if not methodology_ref: reject`. Nothing else was checked.

| | |
|---|---|
| **Reproducer** | FC-05 `protocol.volume.DEX_NATIVE` vs `protocol.volume.AGGREGATOR_ROUTED`, `methodology_ref="fake:anything"` |
| **Before R1** | `AUTHORIZED` |
| **After R1** | `ComparabilityError: requires methodology routing-attribution-methodology@1` |

Supplying FC-07's row with FC-05's methodology was equally accepted. The corpus
row's `required_methodology` was documentation; nothing read it.

**Repair.** `required_methodology` is now a fully-qualified methodology identity
(`ref@version`) and is *mechanically meaningful*. A comparison authorizes only
when two independent conditions both hold:

1. the supplied identity **equals** the row's required identity exactly — no
   substring match, no alias, no version drift; **and**
2. the methodology itself declares authority for that row via
   `authorized_corpus_row_ids`.

Condition 1 alone is a name. Condition 2 alone is a claim with no ratified name
behind it. Only together is it authority — which is what makes requirement A5
("PASS only if the methodology itself is authorized for that corpus row")
mechanically true rather than aspirational.

A consequence worth stating: because the row pins one exact identity, a **new
methodology version does not inherit the comparison**. Licensing v2 is an
explicit operator act on the corpus, never a side effect of a version bump.

### R1-D2 · VALUATION PRICE SOURCE IS NOT BOOK-2-BACKED

`PriceObservation` carried `source_ref: str` and no Book 2 provenance at all.
`authorize_valuation` checked that `source_ref` was non-empty.

| | |
|---|---|
| **Reproducer** | `source_ref="fake:oracle"`, no cited claim, purpose `PROTOCOL_COLLATERAL_MARK` |
| **Before R1** | `AUTHORIZED` |
| **After R1** | `ValuationError: has no current Book 2 authority` |

This was the most serious of the four: a fabricated attribution string could
authorize a collateral mark. Book 2 remains the epistemic authority for price
evidence; a string is an *attribution*, not evidence.

**Repair.** `PriceObservation.source_claim_refs` is **required**. At valuation
authority time the cited claims resolve through `Book6Provenance` with
`require_current=True`, so an unknown, empty, stale, contested, rejected,
superseded, or detached-evidence claim all fail closed.

The two requirements are kept deliberately separate and both are tested:

```
PRICE EVIDENCE EXISTS  !=  PRICE CLASS IS ADMISSIBLE FOR PURPOSE
```

Book 2 may establish that a price was observed. Book 6 alone decides whether
that price class is admissible for a given purpose. Valid claim + wrong class →
refused. Correct class + fabricated claim → refused. Both correct → authorized.

### R1-D3 · STALE CURRENT PRICE COULD PASS `authorize_valuation()`

`ValuationObservation.is_stale` existed and worked. The engine simply never
consulted it.

| | |
|---|---|
| **Reproducer** | price observed 30 days ago, `staleness_bound_seconds=3600`, evaluated today |
| **Before R1** | `AUTHORIZED` |
| **After R1** | `ValuationError: which is stale at …` |

**Repair.** One ambiguous API was replaced by two explicit ones, and the
evaluation instant is always passed in — never read from a hidden wall clock,
so a replay at a historical instant is reproducible:

- `authorize_current_valuation(valuation, *, as_of)` — current authority.
  Requires a non-stale price at `as_of`.
- `validate_historical_valuation(valuation)` — the bitemporal-preserving path.
  Validates the observation at its **own recorded** `observed_at`, so

  ```
  CURRENT UNAVAILABLE  !=  HISTORICALLY INVALID
  ```

  A price that is stale today was fresh when the valuation was observed, and
  that historical statement stands. A valuation that was *already* stale when
  observed is not historically valid either, and says so.

### R1-D4 · FAKE COVERAGE-SUFFICIENCY REF COULD CREATE `DATA_COMPLETE`

The vector derived its data status from

```python
sufficiency_backed = bool(self.coverage_sufficiency_rule_refs) and all(...)
```

It never checked that those refs named anything that existed.

| | |
|---|---|
| **Reproducer** | `coverage_sufficiency_rule_refs=("fake:rule",)` on a fully-observed vector with coverage ids |
| **Before R1** | `DATA_COMPLETE` |
| **After R1** | `DATA_INCOMPLETE` |

`DATA_COMPLETE` was asserted with **zero** ratified coverage-sufficiency rules
in existence — the exact inversion of the ratified doctrine
(`COVERAGE_OBSERVATION != COVERAGE_SUFFICIENCY_RULE`).

**Repair.** Two layers, and the split is stated rather than hidden:

1. **Conservative local status** — `FundamentalStateVector.data_status` now
   additionally requires a registry-issued `CoverageSufficiencyAttestation`
   whose rule set matches the declared refs and whose scope covers every
   dimension. A hand-written ref tuple can no longer produce `DATA_COMPLETE`.
2. **Authoritative engine status** — `Book6MeasurementEngine.data_status`
   re-resolves every named rule live and requires, for each, that it exists,
   carries a ratification decision for its **current** version, and scopes to
   the metric being judged.

At bootstrap, with zero ratified rules, every vector is `DATA_INCOMPLETE`. A
locally ratified *synthetic* rule may produce `DATA_COMPLETE` in a test — and
that is deliberately distinguishable from canonical operator ratification.

### R1-D5 · METHODOLOGY REGISTRY ABSENT *(the related gap)*

The implementation authorization required **five separated stores**:

```
definition registry | methodology registry | measurement records
| normalization rules | state rules
```

Four existed. There was no methodology store, so **every** methodology reference
in the kernel was a bare `str`. This is the structural cause behind R1-D1 and
would have produced the same class of defect anywhere else.

**Repair.** `book6_methodology.py` adds `Book6MethodologyRegistry` with:

- versioned identity `methodology_ref + "@" + version` — "monthly active
  accounts" under two methodologies are two different observations;
- supersession that retains prior versions as history and makes them
  non-authorizing;
- local invalidation with a recorded reason;
- `register_methodology` / `registered_methodology` / `resolve_methodology`,
  where *resolution* is the authority-bearing path and *registration* is not.

Every authority-bearing surface now resolves against it: metric definitions,
measurements, normalization rules, comparisons, valuation conversion
methodology, and state rules. Methodology registration is structural Book 6
authority — it is **not** a second epistemic engine, mints no claim, and defines
no claim state.

### R1-D6 · NORMALIZED VALUE INTEGRITY *(reproduced during R1)*

Auditing the normalization surface for Phase 10 found the same class of defect:
the engine authorized whatever `value` the caller supplied, ignoring
`rule.transformation`, the declared denominator, and the native inputs.

| | |
|---|---|
| **Reproducer** | native value 10, `PER_TIME` denominator 2 (expected 5), supplied normalized value **999** |
| **Before R1** | `AUTHORIZED` |
| **After R1** | `Book6EngineError: a normalized value is a deterministic function of its inputs and may not be asserted` |

**Repair.** Option A from the brief: deterministic computation.
`compute_normalized_value` derives the product from the rule's declared inputs,
and `Book6MeasurementEngine.normalize` **recomputes and compares**. A caller
cannot assert a normalized number.

To make that total, the rule contract was completed where it had been silent:
`GROWTH_RATE` and `INDEX_TO_BASE` now require an explicit
`base_measurement_ref`, and `SHARE_OF_TOTAL` — which does divide, by the cohort
total — requires that total as its `denominator_ref` instead of leaving the
divisor implicit in a cohort label. Denominator doctrine is inherited: an
observed-zero divisor yields UNDEFINED, never zero, never infinity.

### R1-D7 · RULE STATUS FORGERY *(reproduced during R1)*

Auditing the public ratification paths found that a rule object's own `status`
field *was* the authority.

| | |
|---|---|
| **Reproducer** | `rule.model_copy(update={"status": "RATIFIED", "ratified_by": "operator", "ratified_at": ...})` → `registry.register(forged)` → `authorize()` |
| **Before R1** | `AUTHORIZED` — a Class B state emitted on a forged flag |
| **After R1** | refused **at registration**; a rule object may not even be constructed `RATIFIED` |

`CoverageSufficiencyRule` was worse: `status` was a bare `str` any caller could
set to `"RATIFIED"` at construction, and no registry governed it at all.

**Repair.** Ratified D6M-3 = A (`CENTRALIZED_OPERATOR_RATIFICATION`) is realized
as a single `RatificationLedger` that **both** rule registries embed:

- a rule object may only be constructed and registered `UNRATIFIED`;
- ratification is a **registry decision record**, not a property of untrusted
  input;
- authority is read from the ledger at decision time and bound to one specific
  `(rule_id, version)`, so it **decays on a revision** instead of riding along;
- no delegation register, no bulk path, no automatic ratification.

A `model_copy` forgery, a directly constructed `RATIFIED` object, and a
supersession that inherits a prior ratification are all closed.

---

## 3. Post-construction attack matrix (Phase 12)

Every ratified Book 6 field was attacked from the direction a caller can
actually reach — `model_copy`, raw dict, nested payload — and every authority
boundary re-validates live.

| # | Attack | Result |
|---|---|---|
| C1 | comparison methodology replaced by a fake ref | REFUSED |
| C2 | normalization methodology replaced | REFUSED |
| C3 | valuation conversion methodology replaced | REFUSED |
| C4 | price claim refs stripped | REFUSED |
| C5 | price source swapped | no authority change on its own; forged claim refs REFUSED |
| C6 | price class swapped | REFUSED |
| C7 | staleness bound forged downward | re-read at use, REFUSED |
| C8 | vector coverage rule refs replaced by fake refs | `DATA_INCOMPLETE` |
| C9 | coverage rule status `model_copy` UNRATIFIED→RATIFIED | grants nothing |
| C10 | coverage rule scope swapped | REFUSED |

C5 is worth a note: swapping `source_ref` alone changes *nothing*, because
authority never came from that string. That is the intended outcome, and it is
the cleanest evidence that R1-D2 is actually closed rather than merely
obstructed.

---

## 4. Preserved seals (Phase 15)

R1 regressed none of the 21 established Book 6 seals. Each is re-asserted in
the R1 suite's `R1.PRESERVED_SEALS` family:

missing ≠ zero · denominator undefined semantics · explicit window classes ·
append-preserving revision · native-before-normalized · percentile rejected ·
15-row false-comparison corpus · no global price source · Book 5 no write-back ·
Book 4 no topology rewrite · zero canonical StateRules · Class A only at
bootstrap · Class B/C rule gating · anti-score firewall · D2-6 deferral · no
usage/health research · model_copy frozen-model seal · Book 2 measurement decay ·
methodology sensitivity · cross-source parity.

---

## 5. What R1 did **not** do

Stated plainly, because the boundary is part of the result:

- **No acceptance.** `BOOK_6_ACCEPTANCE = NOT_SELF_ACCEPTED`. The proposed gate
  `PASS_CSIA_BOOK6_FUNDAMENTAL_MEASUREMENT_STATE_KERNEL` is proposed, not taken.
- **No ratification.** `INDIVIDUAL_STATE_RULES_RATIFIED = 0` and
  `COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0` remain exactly zero. R1 did not
  create the authority that makes a Class B state emittable or a vector
  `DATA_COMPLETE`; it created the *mechanism* by which a future operator
  ratification could, and the machinery by which its absence is provable.
- **No new corpus rows.** The fifteen ratified rows are intact. R1 made the
  existing `required_methodology` field enforceable rather than adding to it.
- **No upstream repair.** Books 1–5 and the sensor are byte-identical to the
  Book 5 acceptance commit.
- **No live acquisition, RPC, database, graph database, scheduler, dashboard,
  Book 7, Book 8 or D8.** Nothing here required network access.
- **No usage/health empirical research.** D6M-5 remains `OPEN_DEFERRED`; no
  threshold was estimated and no data was acquired.

### Residual limitation, stated rather than implied

An in-process Python object cannot be made unforgeable against a caller who has
code execution in the same interpreter. R1 closes every forgery reachable
through the **public API** — forged status fields, `model_copy` forgery, direct
`RATIFIED` construction, scope swaps, and lineage stripping. It does not defend
against a caller who reaches into registry privates or patches the interpreter,
and it does not pretend to. The seal is deliberately the same one Book 2 uses for
claims and Books 4/5 use for graph and capital authority: **re-resolve through
the registry at decision time.** That is why `data_status`, `authorize_current_valuation`,
`resolve_current` and `require_comparison_authority` are all registry lookups
rather than cached verdicts.

---

## 6. Evidence index

| Artifact | Path |
|---|---|
| R1 gate matrix | `quant-lab/research/crypto_systems_intelligence_atlas/CSIA_BOOK_6_HARDENING_R1_MATRIX.json` |
| This document | `quant-lab/research/crypto_systems_intelligence_atlas/CSIA_BOOK_6_HARDENING_R1_AUTHORITY_CLOSURE.md` |
| Implementation evidence (R1 section appended) | `quant-lab/research/crypto_systems_intelligence_atlas/CSIA_BOOK_6_IMPLEMENTATION_EVIDENCE_v0.1.md` |
| Validation traceability (generated) | `quant-lab/research/crypto_systems_intelligence_atlas/CSIA_BOOK_6_VALIDATION_TRACEABILITY_MATRIX.json` |
| R1 test suite | `quant-lab/tests/crypto_systems_intelligence_atlas/test_book6_hardening_r1.py` |
| Methodology registry | `quant-lab/src/crypto_systems_intelligence_atlas/book6_methodology.py` |
| Coverage-rule registry | `quant-lab/src/crypto_systems_intelligence_atlas/book6_coverage_rules.py` |
| Ratification ledger | `quant-lab/src/crypto_systems_intelligence_atlas/book6_ratification.py` |

**Traceability.** The matrix is generated from an executable table
(`book6_traceability.TRACEABILITY_ROWS`) and every row is resolved against the
test sources on disk, so a row cannot outlive the assertion it claims to trace
to. R1 added 8 families and 92 rows: **213 rows across 20 families**, up from
121.

---

## 7. Exit state

```
BOOK_6_HARDENING_R1              = PASS
BOOK_6_IMPLEMENTATION            = COMPLETE_HARDENED_R1
BOOK_6_ACCEPTANCE                = NOT_SELF_ACCEPTED
PROPOSED_EXIT_GATE               = PASS_CSIA_BOOK6_FUNDAMENTAL_MEASUREMENT_STATE_KERNEL
BOOK_6_IMPLEMENTATION_AUTHORITY  = TRUE / OFFLINE_KERNEL_SCOPE_ONLY
LIVE_ACQUISITION_AUTHORITY       = FALSE
D6M_5                            = OPEN_DEFERRED
INDIVIDUAL_STATE_RULES_RATIFIED  = 0
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
```

**Exact next operator action:** review `CSIA_BOOK_6_HARDENING_R1_MATRIX.json`
and accept or reject the proposed gate. Do **not** begin live acquisition, and
do not ratify any state rule or coverage-sufficiency rule as a side effect of
accepting this round.
