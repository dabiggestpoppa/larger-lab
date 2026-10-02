# CSIA — BOOK 6 COMPARISON / CHANGE SUBSTRATE RATIFICATION PACKET — v0.1

**Document ID:** CSIA-B6-SRP-001
**Version:** 0.1
**Status:** `AWAITING_OPERATOR_DECISION`
**Date:** 2026-10-02
**Kind:** OPERATOR DECISION PACKET — ratification only, never implementation

**This packet does not ratify anything and does not authorize implementation.**
It presents one ratification choice and one hold choice for the operator.

---

# 1. What is being decided

Ratification of the **implementation-substrate clarification** for the Book 6
Comparison/Change amendment, comprising four successor artifacts:

| # | artifact | status |
|---|---|---|
| 1 | `CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_SUBSTRATE_CLARIFICATION_v0.1.md` | `DRAFT_PENDING_OPERATOR_RATIFICATION` |
| 2 | `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.5.md` | `DRAFT_PENDING_OPERATOR_RATIFICATION` |
| 3 | `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.5.md` | `DRAFT_PENDING_OPERATOR_RATIFICATION` |
| 4 | `CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.2.md` | `DRAFT_PENDING_OPERATOR_RATIFICATION` |

Plus two reviews that gate the decision:

| review | result |
|---|---|
| `..._SUBSTRATE_PRE_RATIFICATION_REVIEW_v0.1.md` | **20 / 20 PASS** |
| `..._IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.2.md` | **READY_PENDING_SUBSTRATE_CLARIFICATION_RATIFICATION** (9 TRUE / 1 NOT_SUPPORTABLE) |

---

# 2. What ratification would mean — and would not mean

```text
RATIFYING WOULD:
  - fix GAP-1 as 1A-STRICT  (stored binary64, exact stored-value equality)
  - fix GAP-2 as 2D         (same-metric exact-unit identity)
  - fix GAP-3 as 3C         (coverage-rule-presence derivation)
  - fix GAP-4 as 4D         (explicit temporal comparability domain)
  - establish grammar v0.5 and plan v0.5 as the governing substrate
  - make the 20-check replay and the 208-case test spec the governing contract

RATIFYING WOULD NOT:
  - authorize any implementation
  - authorize any test code
  - re-accept Book 6
  - ratify any ComparisonRule, benchmark rule, or coverage rule
  - resolve GAP-5
  - create any new authority-bearing contract class
```

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE  (before and after)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

---

# 3. The four resolutions in one table

| gap | resolution | one-line meaning | new contract class? |
|---|---|---|---|
| GAP-1 | `1A-STRICT` | canonical value = finite stored binary64; equality = exact stored `==`; no epsilon | no |
| GAP-2 | `2D` | arithmetic only when both observations carry `MetricDefinition.unit`; mismatch = `NOT_COMPARABLE` | no |
| GAP-3 | `3C` | coverage applicability derived from exact-metric current ratified rule presence; absence = `UNRESOLVED` | no |
| GAP-4 | `4D` | `TemporalComparabilityStatus` = COMPARABLE / NOT_COMPARABLE / UNRESOLVED, produced by new check 19 | no |

```text
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
    ComparisonRule
    ChangeObservation
HIDDEN_THIRD_CONTRACT = NONE
```

---

# 4. Ratified history is preserved

```text
CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.4.md  = RATIFIED, UNCHANGED
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.4.md          = RATIFIED, UNCHANGED
CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_BOUNDARY_v0.3.md = RATIFIED, UNCHANGED
CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_RATIFICATION_RECORD_v0.1.md
                                                      = RATIFIED, UNCHANGED
```

v0.5 is an **additive successor**. It does not reopen, reverse or supersede any
ratified artifact, and it does not call any of them erroneous. The one place it
departs from v0.4 is that it **does not repeat** v0.4's unverifiable
"accepted benchmark-rule namespace" claim.

---

# 5. GAP-5 remains open — ratification does not close it

```text
GAP_5 = OPEN
```

The accepted benchmark-rule namespace does not exist in the codebase. Grammar
v0.4 §2's `baseline_selection_methodology_ref` requirement stands as ratified
and is currently unsatisfiable. **This packet does not decide GAP-5.**

Ratifying the substrate clarification resolves GAP-1..GAP-4 only. GAP-5 requires
its own operator decision before implementation authorization can be considered.

---

# 6. The operator choice

```text
OPTION A   RATIFY_SUBSTRATE_CLARIFICATION
           Ratify artifacts 1-4 as the governing Book 6 Comparison/Change
           implementation substrate. FIXES GAP-1..GAP-4.
           Grants NO implementation authority.
           Leaves GAP-5 OPEN.

OPTION B   HOLD
           Take no ratification action. GAP-1..GAP-4 remain unresolved.
           Grants NO implementation authority.
           Leaves GAP-5 OPEN.
```

**Both options grant no implementation authority and both leave GAP-5 open.**
The difference is whether the four directed gaps are fixed on the record.

---

# 7. Recommended sequencing

```text
1. Decide GAP-5 (it changes what the amendment's scope is)
2. RATIFY_SUBSTRATE_CLARIFICATION or HOLD
3. Re-run the implementation authorization review including GAP-5's resolution
4. Only then consider implementation authorization
```

GAP-5 should be decided first because options 5A and 5B remove the
baseline-bearing surface entirely, which changes what "all 20 replay checks
implementable" means and what the ratification is ratifying.

---

# 8. State at time of packet

```text
GAP_1..GAP_4 = RESOLVED IN DRAFT, NOT RATIFIED
GAP_5        = OPEN
PRE_RATIFICATION_REVIEW        = 20 / 20 PASS
AUTHORIZATION_REVIEW_v0.2      = READY_PENDING_SUBSTRATE_CLARIFICATION_RATIFICATION
SUBSTRATE_CLARIFICATION        = v0.1 DRAFT_PENDING_OPERATOR_RATIFICATION
GRAMMAR                        = v0.5 DRAFT
PLAN                           = v0.5 DRAFT
TEST_SPEC                      = v0.2 DRAFT
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
COMPARISON_RULES_RATIFIED       = 0
BENCHMARK_RULES_RATIFIED        = 0
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
D6M_5                           = OPEN_DEFERRED
```

**Not authorized and not performed by this packet:** any ratification, any
implementation, any source or test change, Book 6 re-acceptance, any rule
ratification, any new policy, Book 7 or Book 8, live acquisition, and any branch
creation, force-push, rebase or history rewrite.

```text
STOP. Do not ratify. Do not implement.
```
