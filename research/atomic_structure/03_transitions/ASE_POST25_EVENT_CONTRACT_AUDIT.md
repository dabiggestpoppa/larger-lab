# ASE_POST25_EVENT_CONTRACT_AUDIT.md

Checkpoint: ASE-2.2-NOON-AND-POST25-EVENT-GEOMETRY-REPAIR
Branch: agent/atomic-structure-foundry
Base: 7d712ccd66ef854f4efa1f8cf9d9501dde02a2c9

## Purpose

The historical "-25 completion / opposite-band lock" claims are ambiguous
about which completion semantics hold. This audit freezes every alternative
implemented, so reversal-rate differences can be attributed to the contract,
not to the data.

## 1. Distribution levels (frozen)

For UP expansion (direction of constraint resolution = UP):

    E25_UP   = AsianHigh + 0.25 * AR
    E50_UP   = AsianHigh + 0.50 * AR
    E100_UP  = AsianHigh + 1.00 * AR

For DOWN:

    E25_DOWN = AsianLow  - 0.25 * AR
    E50_DOWN = AsianLow  - 0.50 * AR
    E100_DOWN= AsianLow  - 1.00 * AR

AR = (AsianHigh - AsianLow) / 0.0001 (pips).

## 2. Completion variants (both computed)

E25_TOUCH            first bar whose high/low reaches the E25 level
E25_CLOSE_BEYOND     first bar whose close is beyond the E25 level

The event_kind column carries a suffix _CLOSE for the close variant.

## 3. Direction / bias contracts

Two event definitions are tested separately and NEVER collapsed:

E25_RAW_FIRST_SIDE: whichever side reaches +/-25% first (with
SAME_BAR_ORDER_UNRESOLVED if both sides hit in one bar).

E25_CEREBUS_VALID: the manual's constraint-resolution direction requires a
bias lock: the first M5 close outside the Asian band after 03:00 sets bias
(UP or DOWN); only that side's E25 counts as a valid event. This is the
deterministic proxy for the manual's "direction of constraint resolution".

Both are recorded per event_kind so the reported reversal rates remain
attribute-able to a specific completion/bias gate.

## 4. Opposite-band lock

For an UP event, opposite band = AsianLow.
For a DOWN event, opposite band = AsianHigh.

OPPOSITE_BAND_TOUCH later (after hit bar)
OPPOSITE_BAND_CLOSE later (close beyond)

## 5. E25 retouch vs E50 extension

"ANOTHER_25_EXTENSION" = E50 (never E25 again).
E25_RETOUCH is a separate first-event candidate only in the direction
pointing back toward the band (a retouch requires low <= E25 for UP events),
so it cannot double-count an ongoing extension.

## 6. Same-bar ambiguity

If the E25 hit bar also touches E50 or the opposite band in the same bar, the
bar's intrabar order is unknowable -> SAME_BAR_ORDER_UNRESOLVED, never
inferred.

## Headline repaired numbers (E25_CEREBUS_VALID touch, opposite band)

- overall opposite-band touch rate: 50.2% (n=404)  -> reversal ~50%
- T1: 59.6% (n=218), T2: 47.6% (n=126), T3: 23.1% (n=52)
- close-completion variant: overall 46.2% (n=385)

Source claim "-25 lock ~95.8% / reversal ~4.2%" is NOT reproduced under any
repaired definition; it is marked DISAGREE_OVERALL_TIER_DEPENDENT
(see ASE_MECHANISM_SOURCE_COMPARISON_REPAIRED.csv).

## Files produced

- ASE_POST25_EVENT_LEDGER_REPAIRED.parquet
- ASE_POST25_REVERSAL_MATRIX_REPAIRED.csv
- ASE_POST25_FIRST_EVENT_ORDERING_REPAIRED.csv
- ASE_POST25_TOUCH_VS_CLOSE.csv