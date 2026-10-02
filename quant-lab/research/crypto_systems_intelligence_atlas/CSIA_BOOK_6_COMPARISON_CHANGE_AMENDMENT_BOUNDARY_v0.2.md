# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT BOUNDARY — v0.2

> **Status:** PLANNING / GOVERNANCE ONLY. Successor to
> `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_BOUNDARY_v0.1.md`
> (**preserved unmodified**). Implements nothing. Ratifies nothing.
> **Date:** 2026-10-01
> **Trigger:** `D7N-7 = A`; external review `R6A-D4` / `R6A-D5`; and the
> contract-class count inconsistency found in boundary v0.1.
> **Audit of record:** `CSIA_BOOK_6_COMPARISON_CHANGE_DERIVATION_AUTHORITY_AUDIT_v0.1.md`
> **Authority:** `BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.

---

## 0. Erratum to boundary v0.1

Boundary v0.1 contradicts itself on the amendment's most important claim:

| Line | Text |
|---|---|
| 22 | *"a **single** new contract class: a comparison / change layer"* |
| 35 | `AMENDMENT WIDTH = NARROW, SINGLE CONTRACT CLASS` |
| 189 | `| New contract classes added | 2 (ComparisonRule, ChangeObservation) |` |

**Correction of record:**

```text
incorrect historical wording:  "a single new contract class"
correct value:                NEW CONTRACT CLASSES = 2
                              1. ComparisonRule
                              2. ChangeObservation
```

The "single" wording described a single *layer* of capability and was
conflated with a single contract class. The checklist was right. Boundary
v0.1 is preserved unmodified; this successor is the corrected statement.

The count of 2 is now **verified rather than asserted** — see §3, which had to
resolve whether two "methodology refs" of undetermined type were secretly
contract classes in their own right.

## 1. What this amendment is, and what it is not

Book 6 remains **FUNDAMENTAL MEASUREMENT AND STATE MODELING**. The amendment
adds a comparison / change layer over measurements Book 6 already accepted,
expressed in exactly two new contract classes.

```text
BOOK 6 AMENDED SCOPE   = measurement → comparison → change observation
BOOK 6 UNCHANGED       = every other accepted contract and doctrine
AMENDMENT WIDTH        = NARROW, TWO CONTRACT CLASSES (corrected)
```

## 2. In scope

| # | In-scope element | Nature |
|---|---|---|
| S1 | `ComparisonRule` | new versioned contract; operator-ratified; registry-bound |
| S2 | `ChangeObservation` | new Book 6-local derived record |
| S3 | Baseline selection | reuses the **accepted** Book 6 benchmark-rule namespace |
| S4 | Comparison semantics | required fingerprinted section **of** `ComparisonRule` |
| S5 | Comparability gate set | nine gates; G7 rebuilt on resolved coverage applicability |
| S6 | Numeric change semantics | absolute / relative delta where valid |
| S7 | Change direction semantics | `INCREASE` / `DECREASE` / `NO_CHANGE` / undefined |
| S8 | Missingness treatment | `CHANGE_UNDEFINED` / `INSUFFICIENT_DATA` |
| S9 | Methodology-sensitivity preservation | parallel change records, never averaged |
| S10 | Derivation-binding authority replay | **19** live re-resolutions |
| S11 | Coverage applicability resolution | tri-state, derived upstream, never waived |
| S12 | Book 6 → Book 7 change/response seam | reference-only from Book 7 |
| S13 | Anti-score firewall extension | no materiality/significance/health fields |

## 3. The contract-class audit (Phase 3 of the audit)

The amendment claims two new contract classes. That claim is only honest if
nothing else in the design carries independent identity, versioning,
ratification, supersession, and replay. Two candidate objects did:

| Candidate | Authority-bearing? | Resolution | New class? |
|---|---|---|---|
| `ComparisonRule` | yes | class #1 | **yes** |
| `ChangeObservation` | yes | class #2 | **yes** |
| baseline-selection methodology | would be — it decides which observations are the baseline | mapped to the **accepted** benchmark-rule namespace (`PRIOR_COMPARABLE_WINDOW`, `ROLLING_MEAN`, `ROLLING_MEDIAN`, `HISTORICAL_DISTRIBUTION`, `BASELINE_EPOCH`), already individually operator-ratified under D6M-3 | **no** |
| comparison methodology | would be — it decides how observations combine | **cannot** be a `MeasurementMethodology` without changing that accepted field's meaning; embedded instead as a required fingerprinted section of `ComparisonRule`, ratified with it | **no** |
| coverage-sufficiency rule | yes | **accepted** Book 6 contract, reused unchanged | **no** |
| derivation-binding digest | a digest of already-bound content, not independently versioned or ratifiable | registry-side ratification binding | **no** |

```text
NEW_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
HIDDEN_THIRD_CONTRACT = NONE
```

**Before this audit the honest count was ambiguous.** v0.2 carried two
"methodology refs" whose target type was never stated. If either target had
independent identity, versioning, ratification, supersession, and replay, it
would *have been* a contract class, and the amendment would have added four
authority-bearing objects while claiming two. Resolving ownership is what
makes the count true.

**The trade-off, stated rather than hidden:** embedding comparison semantics
in `ComparisonRule` makes them per-rule rather than shared. Two rules wanting
the same delta semantics carry duplicate copies. That is duplication, not
risk — each copy is independently fingerprinted and independently ratified,
so copies cannot silently diverge through a shared loose reference. Extracting
them into a third, shared, independently versioned class would be a **new
structural decision** requiring the operator to admit a third contract class.
That decision is **not made here**.

## 4. Explicitly out of scope

```text
OUT — any change to MetricDefinition (including adding a coverage-
       applicability field; silence is the fail-closed default)
OUT — any change to MeasurementMethodology or the accepted benchmark namespace
OUT — any change to MeasurementObservation
OUT — any change to ValuationObservation or valuation authority (D6M-4)
OUT — any change to NormalizationRule (D6M-2 remains separate)
OUT — any change to StateRule or state governance (D6M-3 remains A)
OUT — any change to FundamentalStateVector or the anti-score firewall
OUT — any USED / HEALTHY / adoption / usage-sufficiency parameter (D6M-5)
OUT — any D2_6 modification (remains IN_FORCE)
OUT — any Book 2 claim machinery; ChangeObservation is NOT a Book 2 claim
OUT — any Book 5 write-back
OUT — any Book 3 / Book 4 fact creation or mutation
OUT — any narrative, event, catalyst, or causality concept inside Book 6
OUT — any response-link, window, or ladder concept inside Book 6
OUT — any materiality, significance, health, or investment-merit reading
OUT — any composite score, rank, grade, or recommendation
OUT — any new version mechanism for MetricDefinition (a separate amendment)
OUT — any live acquisition, RPC, network collector, database, or scheduler
OUT — any Book 7 or Book 8 implementation
```

## 5. Anti-creep invariants

Carried forward from v0.1 (`AC-1` … `AC-10`), plus the repairs of this round:

```text
AC-1  Book 6 may receive a comparison CONTEXT. It may NOT receive or store
      narrative, catalyst, event, response, or causality semantics.
AC-2  A baseline is never implicit. No default baseline model.
AC-3  No comparison from incomparable inputs. NOT_COMPARABLE only.
AC-4  No numeric delta when the arithmetic is undefined for the unit.
AC-5  Parallel change records preserved. Never averaged, never silently
      selected.
AC-6  ChangeObservation is Book 6-local derived. No Book 2 claim promotion.
AC-7  Change direction is a measurement-domain statement. Never goodness.
AC-8  Book 6 never describes an event, an action, or a response.
AC-9  No new state is emitted. The amendment adds a derived record class and
      a rule class, not a state class.
AC-10 The amendment is additive. No accepted Book 6 record changes meaning.

AC-11 NO LATE-BOUND DERIVATION — every semantic dependency of a ratified
      ComparisonRule is live re-resolved at use time. A byte-identical rule
      over a changed dependency is stale, not current.
AC-12 NO METHODOLOGY AUTO-FOLLOW — a rule bound to methodology X@1 does not
      follow X@2, and X@1 losing authority decays the rule's records.
AC-13 NO COVERAGE WAIVER — a ComparisonRule cannot downgrade COVERAGE_REQUIRED
      to NOT_APPLICABLE, and cannot bypass G7 by omitting the ref.
AC-14 NO NULLABLE COVERAGE AMBIGUITY — `null` does not mean both "not needed"
      and "rule missing". An explicit tri-state replaces it.
AC-15 OBJECT STATUS IS NOT AUTHORITY — neither a rule nor a record confers
      authority by self-declaration.
AC-16 NO HIDDEN THIRD CONTRACT — the amendment adds exactly two authority-
      bearing contract classes, and the count is audited, not asserted.
```

## 6. Interaction with the accepted D6M series

```text
D6M-1  measurement-object authority boundary  — UNAFFECTED; ChangeObservation
       is a Book 6-local derived record
D6M-2  NormalizationRule remains separate      — UNAFFECTED
D6M-3  StateRule governance                   — UNAFFECTED; no new state
       class. Comparison-rule ratification authority is established BY THIS
       AMENDMENT using a D6M-3-CONSISTENT pattern. No authority is inherited
       from D6M-3. The accepted benchmark namespace IS reused under D6M-3's
       existing individual-ratification rule.
D6M-4  valuation authority                    — UNAFFECTED
D6M-5  empirical usage / health governance    — UNAFFECTED and still
       OPEN_DEFERRED
```

No D6M amendment is required. No prior decision is silently expanded.

## 7. Why the amendment requires the full re-acceptance ladder

Unchanged from boundary v0.1, and reinforced by this round: the amendment now
carries a nineteen-check live authority replay rather than a field-presence
checklist, and reopens a frozen book that has already survived three
hardening rounds.

```text
1. amendment planning ratification
2. separate implementation authorization
3. implementation on the accepted Book 6 lineage (no branch divergence)
4. regression + hardening review (2162 CSIA + 1341 Book 6 + 0 accepted-test
   regressions + Sensor unchanged)
5. formal Book 6 re-acceptance → new ACCEPTED_IMPLEMENTATION_ANCHOR
```

Steps 2–5 are **not performed in this session** and are not authorized by it.

## 8. Upstream effect on Book 7

```text
BOOK_7_PLAN_RATIFICATION = BLOCKED_PENDING_BOOK6_AMENDMENT
BOOK_7_RATIFICATION_BLOCKER = BOOK6_COMPARISON_CONTRACT_NOT_YET_ACCEPTED
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```

Unchanged. No Book 7 architecture change, no new D7N decision, and `D7N-7 = A`
remains binding.

## 9. Boundary verification checklist (corrected)

| Check | Expected |
|---|---|
| Book 6 title unchanged | `FUNDAMENTAL MEASUREMENT AND STATE MODELING` |
| New contract classes added | **2** (`ComparisonRule`, `ChangeObservation`) |
| Hidden third contract | **0** (audited, §3) |
| Accepted contracts modified | 0 |
| New state classes | 0 |
| New D6M amendments | 0 |
| New narrative/event concepts in Book 6 | 0 |
| New score/rank/grade fields | 0 |
| Embedded coverage threshold | 0 |
| Rule-author coverage waiver path | 0 |
| Nullable field with multiple meanings | 0 |
| Default baseline model | 0 (explicitly none) |
| Late-bound derivation dependency | 0 |
| Book 5 write-back paths | 0 |
| Book 2 claim promotion paths | 0 |
| Implementation performed | 0 (planning only) |

---

*End of boundary v0.2. v0.1 preserved unmodified; the count is corrected and
now audited rather than asserted.*
