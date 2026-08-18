# PFT — Research Lifecycle

Status: RATIFIED (PFT-B0-PROGRAM-CONSTITUTION)

## Truth-state ladder

    HYPOTHESIS
        -> MECHANISM_OBSERVED
        -> DESCRIPTIVE_STRUCTURE
        -> DEVELOPMENT_VALIDATED
        -> CONFIRMATION_VALIDATED
        -> HOLDOUT_VALIDATED
        -> FORWARD_VALIDATED

States are never skipped with language. "The strategy works" is only
permitted after the corresponding evidence class exists; otherwise the
state must be named precisely (e.g. "historical development sample
produced positive expectancy").

## Program checkpoints

    B0  PROGRAM-CONSTITUTION     (governance ratify)
    B1  SPECIFICATION-SEAL       (frozen machine-readable specs)
    B2  DATA-TRUTH-SEAL          (provenance, coverage, hashes, splits)
    B3  MATH-CAUSALITY-SEAL      (reference fixtures, causality, census)
    B4  A0-GENESIS-RAW           (economic evidence of A0 only)
    B5  A1-ATOMIC-EVIDENCE       (kernel-level A1 evidence)
    B6  A1-FULL-STACK            (full A1 pipeline evidence)
    B7  Q0-TRANSMISSION          (Q0 economic evidence)
    B8  ATTRIBUTION-SEAL         (which components contribute)
    B9  CONSISTENCY-TWINS        (registered alternative interpretations)
    B10 FALSIFICATION-SEAL       (preregistered null families)
    B11 ROBUSTNESS-SEAL          (cost stress, subperiods, bootstrap)
    B12 CONFIRMATION             (frozen, untouched)
    B13 HOLDOUT                  (one-use, operator-authorized)
    B14 SYNTHESIS                (only if independently earned)
    B15 FORWARD-EXECUTION        (execution science, then Capital Routing)

B0-B3 are authorized by the current build prompt. B4 onward require
explicit operator authorization; completion of B0-B3 does not authorize B4.

## Checkpoint discipline

1. Build only checkpoint scope.
2. Run tests.
3. Generate artifacts.
4. Inspect artifacts.
5. Verify git diff.
6. Commit bounded checkpoint (message = checkpoint name).
7. Push branch.
8. Record SHA.
9. Stop. No auto-advance.

Repairs are bounded `Sx.1` / `Sx.2` checkpoints; history is never
rewritten.

## Data split (tentative until B2)

- Development: 2020-01-01 .. 2024-12-31
- Confirmation: 2025-01-01 .. 2025-12-31
- Holdout: 2026+

Dates change only for objective data-availability reasons, never because
of PnL. The split is frozen at B2 before any strategy PnL.

## Economic metrics

Until explicit authorization, no strategy PnL, total return, PF, Sharpe,
Sortino, Calmar, win rate, expectancy, max strategy DD for alpha
comparison, trade profitability, or best-strategy combination may be
produced. Drawdown/leg-stop equations may be tested on synthetic NAV
paths solely to prove overlay logic (mathematical unit tests, not
economic evaluation).
