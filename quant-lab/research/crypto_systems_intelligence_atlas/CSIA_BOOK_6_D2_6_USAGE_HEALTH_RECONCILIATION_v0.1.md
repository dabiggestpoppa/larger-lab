# CSIA — BOOK 6 D2-6 USAGE/HEALTH RECONCILIATION v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No thresholds invented.
> **Reconciles:** operator decision **D2-6 = DEFER_USAGE_HEALTH_PARAMETERS**
> (Operator Decision Log, effective 2026-09-24, binding commit
> `40d391446088280ca5e6bf49dcdbe36428499c98`).
> **Grants no implementation authority.**

---

## 1. The decision being reconciled

```text
D2-6 = DEFER_USAGE_HEALTH_PARAMETERS
```

Ratified consequence: `ANNOUNCED ≠ DEPLOYED ≠ USED` is binding. Concrete
usage/health thresholds were **intentionally deferred** because they could not
responsibly be frozen without empirical research. The three-way distinction is
structural; the parameters remain open until a later recorded operator decision.

Book 6 is the book where "used" and "healthy" would most naturally acquire
numbers. That is precisely why this reconciliation comes before any usage
metric.

## 2. Reconciliation conclusion

**D2-6 remains in force, unratifed parameters remain deferred, and Book 6
planning does not close it.** The reconciliation produces a *layer separation*
that lets Book 6 measure usage descriptively while health interpretation stays
deferred, without ever converting one into the other.

## 3. Four distinct layers (planned)

```text
USAGE OBSERVATION      a measured fact (counts, events, activity) — Book 6 native
USAGE METRIC           a defined, windowed, method-versioned measure over usage
                       observations
USAGE STATE            a descriptive state derived from usage metrics + ratified
                       rules (e.g. INCREASING / STABLE / INSUFFICIENT_DATA)
HEALTH INTERPRETATION  a judgment about fitness/quality — DEFERRED under D2-6
```

The separation is one-directional and strict:

```text
HEALTH INTERPRETATION  !=  USAGE STATE
USAGE STATE            !=  USAGE METRIC
USAGE METRIC           !=  USAGE OBSERVATION
```

**Binding rule:** `USED` is evidence-backed. "Used" is never asserted from
announcement, deployment, integration listing, or documentation. The evidence
ladder:

| Claim level | Evidence required | May Book 6 assert "USED"? |
|---|---|---|
| ANNOUNCED | a claim/roadmap/proposal (narrative tier) | no |
| DEPLOYED | on-chain/system existence evidence | no — deployment is not usage |
| USED | observed usage evidence under a ratified usage methodology | only with a ratified methodology and its evidence; **currently no such parameters are ratified** |

Because D2-6 deferred the usage/health parameters, **no Book 6 state may
currently assert "USED" as a health-like state**. Usage-bearing metrics may
exist descriptively; any "usage state" that implies adoption adequacy is
`INSUFFICIENT_DATA` until the parameters are ratified.

**Binding rule:** `USED` does not silently mean `HEALTHY`. Even after usage
parameters are ratified, health interpretation remains a separate, separately
ratified layer with its own methodology and its own evidence bar.

## 4. What must NOT be invented now

The following are **deferred** and are not drafted, not placeholdered, and not
guessed anywhere in Book 6 v0.1 planning:

- healthy usage thresholds;
- growth thresholds;
- minimum activity levels;
- good/bad utilization bands;
- adoption cutoffs;
- state-vector thresholds;
- comparison weights.

Where a state would need a threshold that is not ratified, the resolution is
`INSUFFICIENT_DATA`, not a default band, not zero, and not "medium".

## 5. States that need no threshold (permitted without D2-6 closure)

These descriptive states are threshold-free: they compare a subject to **its
own history** under one methodology, or report absence of data. They are
permitted now because they invent no cross-subject cutoff:

```text
INCREASING / DECREASING / STABLE   (own-history direction, one methodology,
                                    declared window, declared sensitivity)
VOLATILE / EXPANDING / CONTRACTING (own-history shape, same discipline)
HIGHER_THAN_OWN_HISTORY / LOWER_THAN_OWN_HISTORY
INSUFFICIENT_DATA                  (any required input non-observed, or a
                                    required threshold is unratified)
```

Even these carry methodology sensitivity: if `INCREASING` vs `STABLE` flips
between two reasonable windows, the sensitivity is surfaced, not hidden (6D.2).

**Not permitted without ratified thresholds:** any cross-subject band
("above average", "top tier", "healthy"), and anything ordered across subjects
(§5.3a, and the comparability doc's rejected PERCENTILE normalization).

## 6. Where D2-6 lands inside the Book 6 architecture

- 6A.1/6A.2: usage observations and metrics may be defined (activity, users,
  interactions) — descriptive, method-versioned, no health reading.
- 6B integration growth: usage-bearing comparison stays `INSUFFICIENT_DATA`
  until parameters are ratified (D2-6-sensitive, flagged in the matrix).
- 6C state vectors: usage/health dimensions are **planned but gated**; without
  ratified thresholds they resolve to `INSUFFICIENT_DATA`.
- 6D: methodology sensitivity explicitly includes a "D2-6-deferred parameter"
  row: any state that would have required a deferred threshold must read
  `INSUFFICIENT_DATA` and cite D2-6.

## 7. Governance of the deferred parameters

The empirical phase is designed, not executed (companion document
`CSIA_BOOK_6_USAGE_HEALTH_RESEARCH_DESIGN_v0.1.md`). When the operator later
considers ratifying parameters, the decision namespace is **D6M-\*** (to avoid
collision with Book 0's existing `D6`). Genuine decision classes that may need
operator input are tracked as **D6M-5** (empirical usage-state governance).

Until such a decision is recorded in the Operator Decision Log, D2-6 governs
and no usage/health parameter is binding.

## 8. Reconciliation verdict

```text
D2_6_STATUS = IN_FORCE (unratified parameters remain deferred)
ANNOUNCED != DEPLOYED != USED = BINDING
USED = EVIDENCE_BACKED (no health-like "used" state without ratified parameters)
HEALTH_INTERPRETATION = SEPARATE + DEFERRED
INVENTED_THRESHOLDS = NONE
D6M_NAMESPACE = D6M-* (no collision with existing D6)
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
```

The deferred decision is reconciled by honoring it, not by closing it.
