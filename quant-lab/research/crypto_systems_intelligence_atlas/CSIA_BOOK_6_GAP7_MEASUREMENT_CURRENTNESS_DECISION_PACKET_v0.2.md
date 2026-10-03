# CSIA — Book 6 GAP-7 Measurement Currentness Decision Packet v0.2

**Status:** `AWAITING_OPERATOR_DECISION`
**Date:** 2026-10-03
**Decision id:** proposed `BOOK6-GAP7-v0.2` (collision-free; continues the v0.1
namespace, does not reuse `D6M-*`, `D7N-*`, `BOOK6-COMPARE-*` or `BOOK6-GAP6-v0.1`)
**Grants implementation authority:** `FALSE` under every option
**Supersedes:** `CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_DECISION_PACKET_v0.1.md`
(v0.1 is superseded, **not withdrawn** — its evidence stands)

**Evidence:** audit v0.1, clarification v0.1, test spec v0.1, pre-rat review v0.1

---

## 1. What changed from v0.1

| | v0.1 | v0.2 |
|---|---|---|
| Options offered | 7A-KERNEL / 7B / HOLD | **RATIFY_7A_KERNEL_WITH_STATUS_B_STRICT** / HOLD |
| Status semantics | open question (A / B / C) | **B-STRICT decided by operator direction** |
| Source-less missingness | unresolved | **NV-A, resolved from accepted doctrine** |
| Non-value-bearing bypass | not characterised | **characterised; broader than first recorded** |

7B is **not offered**, because the global impact still stands. Recording that is
not the same as suppressing it: §4 states the basis for removing it.

---

## 2. Option A — `RATIFY_7A_KERNEL_WITH_STATUS_B_STRICT`

```text
RECOMMENDED = TRUE

SINGLE_MEANING_OF_CURRENT                   = TRUE
COMPARISON_LOCAL_CURRENTNESS                = PROHIBITED
OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE
OBSERVATION_STATUS_NOT_AUTHORITY_BEARING    = TRUE
SUPERSESSION_CURRENTNESS_SOURCE             = REGISTERED LINEAGE TERMINALITY
TERMINALITY                                 = STRUCTURAL PROPERTY OF REGISTERED LINEAGE
SUPERSEDED_PREDECESSOR_NEVER_RESURRECTS     = TRUE
MULTIPLE_SUCCESSOR_LINEAGE                  = INVALID (fail closed)
NV_OUTCOME                                  = NV-A
```

Supporting measurements:

| Measure | Value |
|---|---|
| `resolve_current` call sites | 8 |
| Of those, outside comparison | 6 |
| Executed stale read outside comparison | `current_value("A")` -> `10.0` |
| Pre-ratification review | **15 / 15 PASS** |
| Test cases specified | 24 (`CURR-1` .. `CURR-24`), 0 implemented |
| Non-value-bearing states measured | 8 of 8 register and resolve with `refs=()` |

---

## 3. Option B — `HOLD`

```text
GAP_7 = OPEN / UNRATIFIED
```

Legitimate reasons to hold:

- The operator wants the `ObservationStatus` incoherence fixed before
  quarantining it, rather than quarantining it now and amending later.
- The operator wants CURR-1 .. CURR-24 executed against a prototype before
  ratifying a doctrine.
- The operator rejects NV-A on policy grounds despite it being accepted
  behaviour — in which case the choice becomes a **new policy decision**, not a
  clarification, and should be recorded as one.

Holding does not reopen anything and grants nothing.

---

## 4. Why 7B is not on the table

```text
7B would repair  2 of 8 call sites.
7B would leave    6 reading superseded predecessors, including
                  current_value, the kernel's own sanctioned value read.
```

Measured, not asserted: `current_value("A")` returned `10.0` while `B = 12.0` was
registered and live. 7B would not change that line. Its removal from the option
set follows from the evidence, not from preference.

---

## 5. Non-value-bearing authority — resolved, not blocking

Phase 22 requires this packet to remain `HOLD` if source-less missingness
authority is unresolved. **It is resolved**, so `HOLD` is not forced:

```text
NV-A:  source-less missingness is STRUCTURAL
       current iff TERMINAL and STRUCTURALLY_VALID and METHODOLOGY_CURRENT
       Book 2 authority applies only where refs are cited
```

Basis, all accepted:

- `book6_records.py:152-155` requires `source_claim_refs` only inside the
  `VALUE_BEARING_MISSINGNESS` branch.
- `test_book6_missingness.py:111` registers a `NOT_COLLECTED` record with
  `claim_refs=()` and asserts only that `current_value` refuses.
- All eight states measured to REGISTER and RESOLVE with empty refs.

**No new policy is invented.** NV-A is written down, not chosen for convenience.

### 5.1 The one sub-choice the operator may still want

```text
NV-A (recommended) : source-less missingness may be current
NV-B               : all authoritative missingness requires Book 2 evidence;
                     source-less missingness is never current-authoritative
```

NV-B would be a **new policy**, and it would invalidate
`test_book6_missingness.py:111`'s implicit acceptance. It is surfaced here so the
choice is explicit; the recommendation is NV-A because it is what the accepted
kernel already does.

---

## 6. What ratification of Option A would and would not do

**Would:**

- ratify the 7A repair surface and B-STRICT status quarantine;
- fix the currentness contract the GAP-6 ordering rule depends on;
- authorise **planning** of an implementation round.

**Would not:**

- grant implementation authority (still `FALSE`, a separate decision);
- edit any source or test;
- ratify GAP-6;
- reverse `BOOK6-COMPARE-SUBSTRATE-v0.2`;
- reopen GAP-1 .. GAP-5;
- fix the `ObservationStatus` incoherence — it is quarantined, not resolved;
- change the non-value-bearing early return, which is an implementation matter.

---

## 7. Unchanged under every option

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
BOOK6-COMPARE-SUBSTRATE-v0.2    = RATIFIED, STANDS
GAP_1..GAP_5                    = CLOSED
GAP_6_6E_TEMPORAL_DESIGN        = VALID
GAP_6_RATIFICATION              = HOLD_PENDING_GAP7_RATIFICATION
CHOIR_PLAN_PRESERVED            = TRUE
```

---

## 8. Exact next operator action

Choose `RATIFY_7A_KERNEL_WITH_STATUS_B_STRICT` or `HOLD`. If Option A, optionally
confirm NV-A over NV-B (§5.1). If Option A is ratified, GAP-6 readiness must
subsequently be **re-run over the new currentness contract**; this session does
not satisfy it.

No implementation round may open until a separate operator decision grants it.
