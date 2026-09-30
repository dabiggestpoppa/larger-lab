# CSIA — BOOK 6 USAGE/HEALTH EMPIRICAL RESEARCH DESIGN v0.1

> **Status:** PLANNING DOCUMENT — RESEARCH DESIGN ONLY. **NOT EXECUTED.**
> **No data was collected, fetched, or analyzed to produce this document.**
> **Reconciles:** D2-6 = DEFER_USAGE_HEALTH_PARAMETERS.
> **Grants no implementation authority, no live acquisition authority.**

---

## 1. Purpose and hard boundary

D2-6 deferred usage/health parameters because they "cannot responsibly be
frozen without empirical research." This document **designs that research**.
It does not run it, does not propose thresholds, and does not authorize
acquisition. Its only outputs are (a) the research questions, (b) the data
shape each question needs, (c) how a candidate parameter would have to *emerge*
from a distribution rather than be chosen, and (d) the decision classes the
operator would face afterward.

## 2. Anti-invention clause

No number in this document is a parameter, a threshold, a band, or an estimate
of "healthy." The research is designed so that **candidates emerge from
observed distributions**. Where a question cannot be answered without
acquisition authority that has not been granted, it is marked
`REQUIRES_FUTURE_AUTHORIZATION` and left unanswered.

## 3. Research questions (designed, not answered)

| ID | Question | Data shape needed | Notes |
|---|---|---|---|
| R-U1 | usage persistence | per-subject usage events over long windows | distinguish one-off from sustained use |
| R-U2 | organic vs incentive-driven activity | usage events + incentive/claim events (Book 5) | attribution limit: co-occurrence is not causation; result must stay descriptive |
| R-U3 | bot/sybil sensitivity | identity-graph features (funding links, tx-shape, timing) | output is a *sensitivity band per methodology*, not a verdict |
| R-U4 | retention / repeat usage | cohorted first-use cohorts (explicit cohort, versioned) | cohort identity must be declared, not "all users" |
| R-U5 | economic activity | Book 5 flows + usage (never re-derive Book 5) | measures over Book 5 records only |
| R-U6 | capital persistence | Book 5 stocks over windows | same-unit discipline holds; no cross-unit totals |
| R-U7 | developer persistence | commit/contributor/deploy series (6A.5) | GitHub-only = source-limited; flag, don't judge |
| R-U8 | integration persistence | integration lifecycle events (deployed/used) | D2-6 ladder: used requires usage evidence |
| R-U9 | network security participation | stake/validator activity (6A.1) | consensus-model gated; NOT_COMPARABLE across models |

## 4. How a parameter would have to emerge (method rule)

If the operator later considers ratifying a usage/health parameter, it must
satisfy all of:

1. **Distribution-derived.** The candidate must correspond to a feature of an
   observed distribution (e.g. a knee, a regime change, a bimodality), not a
   round number chosen for legibility.
2. **Methodology-robust.** The candidate must be stable across the plausible
   methodology variants in 6D.2 (window, identity rule, wash filter). A
   candidate that only exists under one arbitrary window is not a parameter; it
   is a window artifact.
3. **Cohort-scoped.** The candidate must be declared per cohort (architecture
   family / economic function). A universal "healthy activity" level across
   heterogeneous architectures is presumed invalid.
4. **Descriptive-only.** The parameter may classify *measured activity*, and
   may not be phrased as fitness, quality, attractiveness, or investment merit
   (§5.3a).
5. **Reversible.** It enters as a versioned methodology + a recorded operator
   decision; changing it supersedes, never rewrites, prior derived states.

A candidate failing any of 1–4 is `REJECTED` in the candidate matrix, not
"pending a better number."

## 5. Sensitivity discipline

Every research output carries the full methodology envelope (window, identity
rule, filters, denominator, source class) so that 6D.2 can re-derive states
under variants. Research that produces a single point number without its
envelope is unusable for ratification.

## 6. Governance of any eventual decision

Namespace: **D6M-*** (Book 0 already owns `D6`). Likely decision classes, to
be surfaced to the operator only if the research actually produces
materially different architectural choices:

- **D6M-5** — empirical usage-state governance (who authors thresholds, at what
  cadence they are revisited, what evidence bar a "used" state must clear).

This document does **not** create D6M-5; it identifies it as a candidate
decision class for the operator packet, consistent with open-decision
discipline (do not manufacture decisions for questions doctrine already
answers).

## 7. What this document deliberately does not contain

- no threshold, band, cutoff, weight, or score;
- no ranking or league table of subjects;
- no "healthy ecosystem" framing;
- no acquired, fetched, or live data of any kind;
- no implication that the deferred parameters can be closed by planning.

## 8. Status

```text
EMPIRICAL_PHASE = DESIGNED, NOT EXECUTED
D2_6_PARAMETERS = STILL DEFERRED
D6M_5 = CANDIDATE DECISION CLASS (operator packet)
LIVE_ACQUISITION_AUTHORITY = FALSE
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
```

The research design stands ready for a future, separately authorized
empirical phase. Until then, D2-6 governs and Book 6 measures usage
descriptively or not at all.
