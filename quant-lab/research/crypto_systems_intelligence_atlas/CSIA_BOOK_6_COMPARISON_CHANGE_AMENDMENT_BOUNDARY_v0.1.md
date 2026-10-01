# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT BOUNDARY — v0.1

> **Status:** PLANNING / GOVERNANCE ONLY. Implements nothing. Ratifies
> nothing. Grants no implementation authority.
> **Date:** 2026-10-01
> **Trigger:** `D7N-7 = A` (`CHANGE_COMPARISON_OWNER = BOOK_6`,
> `BOOK_6_AMENDMENT_REQUIRED = TRUE`).
> **Book 6 current state:** `FROZEN_ACCEPTED` at accepted implementation
> anchor `3919fb8052e216e94034a753fb258d338c5fa0dc`; acceptance commit
> `5f94c3f40cea4441470c57671f51454da7377361`.
> **Authority:** `BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.

---

## 1. What this amendment is, and what it is not

Book 6 remains **FUNDAMENTAL MEASUREMENT AND STATE MODELING**. Its title, its
identity, its authority, and its accepted doctrine are unchanged by this
amendment. What the amendment adds is a single new contract class: a
**comparison / change layer over measurements Book 6 already accepted**.

The amendment is narrow by construction, and the narrowness is a
requirement, not a stylistic preference. A broad reopening would risk the
frozen state-rule governance, the anti-score firewall, and the D6M decisions
that Book 6 spent three hardening rounds establishing. The whole point of
`FROZEN_ACCEPTED` is that unrelated accepted doctrine must survive an
amendment untouched.

```text
BOOK 6 AMENDED SCOPE   = measurement → comparison → change observation
BOOK 6 UNCHANGED       = every other accepted contract and doctrine
AMENDMENT WIDTH        = NARROW, SINGLE CONTRACT CLASS
```

## 2. The precise gap

```text
Book 6 accepted contracts: MetricDefinition, MeasurementMethodology,
                           MeasurementObservation, ValuationObservation,
                           NormalizationRule, StateRule
Book 6 has:               how to MEASURE a quantity at a valid time
Book 6 lacks:             how to COMPARE two measurements, select a BASELINE,
                           decide COMPARABILITY, and emit a CHANGE
Book 7 has:              how to LINK a change to an event/action window
```

The response-semantics repair made this gap load-bearing. Book 7 must assert
that a *change* occurred inside a response window. It cannot assert a change it
has no authority to compute, and Book 6 — before this amendment — offers no
object to reference. `D7N-7 = A` resolves the ownership question; this
document bounds the resulting work.

## 3. In scope

| # | In-scope element | Nature |
|---|---|---|
| S1 | `ComparisonRule` | new versioned contract; methodology binding |
| S2 | `ChangeObservation` | new Book 6-local derived record |
| S3 | Baseline selection methodology | methodology, not default |
| S4 | Comparability gate set | fail-closed; `NOT_COMPARABLE` on any failure |
| S5 | Numeric change semantics | absolute / relative delta where valid |
| S6 | Change direction semantics | `INCREASE` / `DECREASE` / `NO_CHANGE` / undefined |
| S7 | Missingness treatment | `CHANGE_UNDEFINED` / `INSUFFICIENT_DATA` |
| S8 | Methodology-sensitivity preservation | parallel change records, never averaged |
| S9 | Book 6 → Book 7 change/response seam | reference-only from Book 7 |
| S10 | Anti-score firewall extension | no materiality/significance/health fields |

## 4. Explicitly out of scope

Everything below is **excluded**, and listing it is part of the boundary:

```text
OUT — any change to MetricDefinition
OUT — any change to MeasurementMethodology semantics
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
OUT — any live acquisition, RPC, network collector, database, or scheduler
OUT — any Book 7 or Book 8 implementation
```

## 5. Anti-creep invariants (the amendment's own firewalls)

These are the rules that keep a narrow amendment narrow. Each is a
pre-ratification test question, and each must hold at implementation.

```text
AC-1  Book 6 may receive a comparison CONTEXT (subject ref, requested valid-time
      window, requested comparison intent). It may NOT receive or store
      narrative, catalyst, event, response, or causality semantics.
AC-2  A baseline is never implicit. There is no default baseline model. An
      absent baseline yields BASELINE_UNAVAILABLE, never a substituted value.
AC-3  No comparison is produced from incomparable inputs. NOT_COMPARABLE is the
      only permitted outcome of a failed comparability gate.
AC-4  No numeric delta is emitted when the arithmetic is undefined for the
      unit (ratio baseline of zero for a relative delta, mismatched units,
      missing baseline, missing post observation).
AC-5  Parallel change records from different legitimate methodologies are
      preserved side by side. No averaging, no silent selection, no
      "preferred" flag.
AC-6  ChangeObservation is Book 6-local derived. It does not enter the Book 2
      claim store and cannot be promoted to one.
AC-7  Change direction is a measurement-domain statement. It never carries
      goodness, health, materiality, or merit.
AC-8  Book 6 never describes an event, an action, or a response. Those are
      Book 7 objects that reference Book 6 outputs.
AC-9  No new state is emitted. The amendment adds a derived record class, not a
      state class. StateRule governance is untouched.
AC-10 The amendment is additive. No accepted Book 6 record changes meaning,
      and no accepted test result is invalidated by it.
```

## 6. Interaction with the accepted D6M series

```text
D6M-1  measurement-object authority boundary  — UNAFFECTED; ChangeObservation
       is a Book 6-local derived record, exactly like NormalizationRule output
D6M-2  NormalizationRule remains separate    — UNAFFECTED; comparison consumes
       already-normalized or native values and performs no normalization
D6M-3  StateRule governance (centralized operator ratification only)
                                            — UNAFFECTED; no new state class
D6M-4  valuation authority                   — UNAFFECTED; valuation keeps its
                                               explicit numeraire and Book 2
                                               price-provenance requirements
D6M-5  empirical usage / health governance   — UNAFFECTED and still
                                               OPEN_DEFERRED; a change record
                                               is not a health or adoption
                                               reading
```

No D6M amendment is required. This is verified in full in
`CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.1.md` §9 and re-asserted
question-by-question in the amendment pre-ratification review. **No prior
decision is silently expanded.**

## 7. Why the amendment requires the full re-acceptance ladder

Book 6 is `FROZEN_ACCEPTED`. Frozen does not mean immune — it means *any*
change to accepted state requires the operator to walk it back through
acceptance, because the accepted anchor is a promise about a specific
lineage. A comparison layer that added a materiality field, or a default
baseline, or a silent averaging rule, would invalidate acceptance evidence
that is otherwise still true. The only honest path is:

```text
1. amendment planning ratification   (this document set → operator review)
2. separate implementation authorization
3. implementation on the accepted Book 6 lineage (no branch divergence)
4. regression + hardening review (all 2162 CSIA tests + 1341 Book 6 + new
   amendment tests; 0 accepted-test regressions)
5. formal Book 6 re-acceptance → new ACCEPTED_IMPLEMENTATION_ANCHOR
```

Steps 2–5 are **not performed in this session** and are not authorized by it.

## 8. Upstream effect on Book 7

```text
BOOK_7_PLAN_RATIFICATION = BLOCKED_PENDING_BOOK6_AMENDMENT
BOOK_7_RATIFICATION_BLOCKER = BOOK6_COMPARISON_CONTRACT_NOT_YET_ACCEPTED
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```

Book 7's plan is structurally ready and has passed 45/45 pre-ratification
questions. It is not ratified, and it cannot be ratified while its response
layer references a comparison product that no accepted book provides. The
blocker is upstream and narrow: it resolves when — and only when — Book 6
gains and re-accepts a comparison/change contract.

## 9. Boundary verification checklist

| Check | Expected |
|---|---|
| Book 6 title unchanged | `FUNDAMENTAL MEASUREMENT AND STATE MODELING` |
| New contract classes added | 2 (`ComparisonRule`, `ChangeObservation`) |
| Accepted contracts modified | 0 |
| New state classes | 0 |
| New D6M amendments | 0 |
| New narrative/event concepts in Book 6 | 0 |
| New score/rank/grade fields | 0 |
| Default baseline model | 0 (explicitly none) |
| Book 5 write-back paths | 0 |
| Book 2 claim promotion paths | 0 |
| Implementation performed | 0 (planning only) |

---

*End of boundary. Planning artifact; the amendment is scoped, not started.*
