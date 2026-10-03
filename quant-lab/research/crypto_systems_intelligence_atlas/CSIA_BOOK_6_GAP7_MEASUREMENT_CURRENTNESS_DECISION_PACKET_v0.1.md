# CSIA — Book 6 GAP-7 Measurement Currentness Decision Packet v0.1

**Status:** `AWAITING_OPERATOR_DECISION` — no decision is made or recommended as taken.
**Date:** 2026-10-03
**Decision id:** proposed `BOOK6-GAP7-v0.1` (collision-free; does not reuse the
`D6M-*`, `D7N-*`, `BOOK6-COMPARE-*` or `BOOK6-GAP6-v0.1` namespaces)
**Grants implementation authority:** `FALSE` under every option below
**Evidence:** `CSIA_BOOK_6_MEASUREMENT_SUPERSESSION_CURRENTNESS_AUDIT_v0.1.md`

---

## 1. What the operator is being asked to decide

GAP-7 is reproduced and **kernel-wide**. The question is not *whether* the defect
exists — it is reproducible at `5f94c3f40c` — but **where to repair it** and
**whether to ratify the gap at all**.

Three options are on the table. `HOLD` is a real option, not a formality.

---

## 2. Option 7A-KERNEL — TERMINAL_SUPERSESSION_CURRENTNESS

**Repair `Book6MeasurementRegistry.resolve_current` so it computes currentness
globally.**

```text
CURRENT = OBSERVED
      AND TERMINAL                       (no registered successor names this record)
      AND METHODOLOGY_CURRENT
      AND BOOK2_AUTHORITY_CURRENT
      AND STRUCTURALLY_VALID             (revalidate against the MetricDefinition)
```

```text
RECOMMENDED = TRUE
```

**Why.** The evidence meets the instruction's own precondition — "Recommend 7A
only if global accepted call sites demonstrate impact":

| Measure | Value |
|---|---|
| Accepted call sites of `resolve_current` | 8 |
| Of those, outside comparison | **6** |
| Executed proof outside comparison | `current_value("A")` returned the superseded `10.0` |
| Paths affected | value read, unit read, ratio, normalization, base/divisor lookup, state emission |
| `resolve_current` docstring contract | "Resolve a measurement's CURRENT authority" — already global |
| Precedent in the same kernel | `book6_methodology.py:327` fails closed on a superseded methodology |

A comparison-local filter would fix 2 of 8 sites and leave the kernel's own
sanctioned value read (`book6_core.py:135`) returning historical data. Two
coexisting notions of "current" would be created by precisely the method whose
docstring promises a single one.

---

## 3. Option 7B-COMPARISON-LOCAL — LOCAL TERMINALITY FILTER

**The comparison selector performs its own terminality filtering.**

```text
RECOMMENDED = FALSE
```

It repairs 2 of 8 sites. Sites 1–6 keep returning the superseded predecessor. It
also contradicts the single-meaning-of-current doctrine and creates two
definitions of currentness in one kernel. It is recorded because the operator may
weigh scope containment against coherence, not because the audit supports it.

---

## 4. Option HOLD

```text
GAP_7 = OPEN / UNRATIFIED
```

Legitimate if the operator wants the status-semantics question (§9.1 of the audit,
options A / B / C) settled before choosing a repair surface, since option C is a
prerequisite for 7A being fully coherent.

---

## 5. Option comparison

| | 7A-KERNEL | 7B-COMPARISON-LOCAL | HOLD |
|---|---|---|---|
| Sites fixed | 8 / 8 | 2 / 8 | 0 |
| Single meaning of current | preserved | broken | unchanged |
| Matches methodology precedent | yes | no | n/a |
| Matches `resolve_current` docstring | yes | partially | n/a |
| Surface | broad, one method | narrow, one path | none |
| Reverses `BOOK6-COMPARE-SUBSTRATE-v0.2` | no | no | no |
| Grants implementation authority | **no** | **no** | **no** |

Any option leaves these unchanged:

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
GAP_1..GAP_5                    = CLOSED
SUBSTRATE_RATIFICATION          = STANDS
```

---

## 6. What each option does NOT authorize

- No source edit. Accepted Book 6 stays at `5f94c3f40c`.
- No test code.
- No reopening of GAP-1 .. GAP-5.
- No ratification of GAP-6.
- No reversal of the substrate ratification.

---

## 7. Downstream effect the operator must decide alongside

GAP-6 is **not** blocked by a failed design. Its 6E temporal projection remains
valid. What changes is that its eligibility premise is incomplete:

```text
AUTHORITY_AND_RECORD_ELIGIBILITY -> ORDERING
```

rests on a record-currentness premise that is currently false for superseded
predecessors. The reconciliation is recorded separately in
`CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_READINESS_RECONCILIATION_v0.1.md`.

---

## 8. Exact next operator action

Choose one of `7A-KERNEL`, `7B-COMPARISON-LOCAL`, or `HOLD`, and — if 7A — choose
the status-semantics option (A, B, or C) from the audit §9.1.

No implementation round may open until that choice is recorded as an operator
decision.
