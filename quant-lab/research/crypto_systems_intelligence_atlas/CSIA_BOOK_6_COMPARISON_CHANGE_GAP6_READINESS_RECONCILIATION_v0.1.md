# CSIA — Book 6 Comparison/Change GAP-6 Readiness Reconciliation v0.1

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION` — reconciliation recorded; no ratification.
**Date:** 2026-10-03
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`
**Trigger:** GAP-7 reproduced —
`CSIA_BOOK_6_MEASUREMENT_SUPERSESSION_CURRENTNESS_AUDIT_v0.1.md`

---

## 1. Reconciliation record

```text
GAP_6_6E_TEMPORAL_DESIGN      = VALID
GAP_6_RATIFICATION            = HOLD_PENDING_GAP7
PRE_RAT_15_15                 = INCOMPLETE_CURRENTNESS_PREMISE
AUTH_REVIEW_v0.5_10_10        = INCOMPLETE_CURRENTNESS_PREMISE
SUBSTRATE_RATIFICATION        = STANDS
GAP_1..GAP_5                  = CLOSED
GAP_7                         = OPEN / MEASUREMENT_SUPERSESSION_CURRENTNESS
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

---

## 2. What is NOT being done to GAP-6

GAP-6 is **not** discarded. Its temporal-projection design is sound and remains
`VALID`. `6E WINDOW_CLASS_AWARE_ORDERING_KEYS` answers a real question about how
to order windowed observations, and the ordering-key design it specifies is not
shown to be wrong by anything found here.

What changed is one **premise** the ordering rule rests on, not the ordering rule
itself.

---

## 3. The incomplete premise

GAP-6's package establishes the chain:

```text
AUTHORITY_AND_RECORD_ELIGIBILITY  ->  ORDERING
```

`ORDERING` is sound only over records that are *current*. The audit shows
`is_authoritative_now` returns `True` for a superseded predecessor:

```text
A <- B, both OBSERVED, both claims current
is_authoritative_now("A") = True      <-- A is historical, reported current
```

So the eligibility step admits historical records, and the ordering step then
orders a set containing both a live value and its own superseded predecessor.
This is independent of GAP-6's window-class defect: GAP-6 is about *which key*
orders an instantaneous observation; GAP-7 is about *whether that observation
should be in the set at all*.

### 3.1 The two defects compose, they do not conflict

| | GAP-6 (6E) | GAP-7 |
|---|---|---|
| Question | Given an instantaneous observation, which key orders it? | Given an observation set, which members are current? |
| Axis | `window_class` → ordering key | supersession lineage → record eligibility |
| Repairs | ordering clause | registry currentness |

A complete repair needs both. Ratifying 6E alone would fix ordering over a set
that still contains historical records.

---

## 4. Classification of prior PASS results

Neither result is fabricated, useless, nor withdrawn. Both are **accurate within
their stated scope** and **incomplete outside it**.

| Artifact | Prior verdict | Reconciled classification | Why |
|---|---|---|---|
| `..._PRE_RATIFICATION_REVIEW_v0.1` | 15 / 15 PASS | `INCOMPLETE_CURRENTNESS_PREMISE` | All 15 checks were about window-class ordering keys. None asked whether a predecessor belongs in the candidate set. |
| `..._IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.5` | 10 / 10 TRUE | `INCOMPLETE_CURRENTNESS_PREMISE` | All 10 criteria were about the comparison package. None exercised `resolve_current` on a superseded record. |

Neither review tested the substrate's currentness semantics. The gap was never
in their scope, so their verdicts were correct as verdicts. Recording them as
`HOLD` or `FAIL` would misdescribe what was actually verified.

The audit independently re-derives this: the accepted suite is **2162 passed**
while the defect is reproducible, so no accepted check — review-derived or
otherwise — reaches this behaviour.

---

## 5. Required sequence

```text
1. Operator decides GAP-7 shape         (7A-KERNEL / 7B-COMPARISON-LOCAL / HOLD)
2. Operator decides status semantics    (A / B / C)   [required for 7A coherence]
3. Authorized implementation round repairs resolve_current
4. CURR-1 .. CURR-15 pass against the repaired kernel
5. GAP-6 pre-ratification review is re-run with a currentness premise included
6. Only then may GAP-6 ratification be taken up
```

Steps 5 and 6 are **not** authorized by this artifact.

---

## 6. Relationship to the defect-class sweep

A separate tooling pass (`CSIA_DEFECT_CLASS_SWEEP_v0.1.md`, 2026-10-03) found 7
enum-gated fields where ratified governance names a field without naming the
discriminator that governs its presence. GAP-7 is a **different** defect: its
discriminator is not gated by an enum at all, and its fix is executable rather
than documentary. The two are recorded separately and neither subsumes the other.

---

## 7. Choir plan

```text
CHOIR_PLAN_PRESERVED = TRUE
```

`CSIA_BOOK_6_CHOIR_FORMAL_PROOF_PILOT_PLAN_v0.1.md` is present and unedited, and
has zero semantic overlap with this reconciliation. GAP-7 may later be adopted
as an explicit proof premise; no proof work was performed or is proposed here.
