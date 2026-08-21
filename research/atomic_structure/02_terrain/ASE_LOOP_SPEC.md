# ASE-1 Raw Loop Specification

Status: FROZEN_FOR_ASE1_TERRAIN

## Scope
This is descriptive terrain reconstruction only. It is not a trading rule and does not compute PnL.

## Time and origin
- Input: completed EURUSD M5 bars normalized to `America/New_York`.
- Research day: calendar date of the 03:00 New York Asian close.
- Daily window: 03:00 inclusive through 12:00 exclusive; 12:00 is terminal.
- `DAILY_ORIGIN`: origin price is the last completed Asian-session close before 03:00.
- `COMPLETION_RESET`: after a completed loop, the next loop begins on the next completed bar with origin equal to the prior completion bar close.
- `FAILURE_RESET`: after a failed loop, the next loop begins on the next completed bar with origin equal to the failure bar close.
- `TERMINAL_RESET`: no new loop is opened after the 12:00 terminal boundary; the next valid research day starts independently.

## Direction
A loop direction is assigned from the first completed bar after its origin whose close differs from the origin price. A close above the origin is `UP`; a close below is `DOWN`. Equal closes are ignored. The bar that establishes direction is not used for excursion completion, so the decision is causal at bar close.

## Completion
For a loop with direction `UP`, completion occurs on the first subsequent completed bar whose high reaches `origin + 1.0 AU`. For `DOWN`, it is the first bar whose low reaches `origin - 1.0 AU`. The completion bar is included in the loop ledger and is the reset bar for the next loop.

## Failure precedence
On each active loop bar, test in this deterministic order:
1. `OPPOSITE_LOOP_FORMATION`: adverse side reaches 1.0 AU before the favorable side reaches 1.0 AU.
2. `RETRACE_INVALIDATION`: adverse side reaches 0.5 AU before completion.
3. `ORIGIN_BREACH`: adverse side reaches the origin price before completion.
The order gives the more severe observable event precedence. If favorable and adverse boundaries are both touched in one OHLC bar, intrabar order is unknowable and the loop is `DATA_INVALID` rather than inventing an order. If neither completion nor failure occurs before 12:00, classify `TERMINAL_12PM`. If data needed to evaluate a day is invalid, classify `DATA_INVALID`.

## Terminal
A loop with no direction by 12:00 is `TERMINAL_12PM` with no next loop. An active loop at 12:00 is also terminated as `TERMINAL_12PM`; terminal close is not fabricated from a future bar.

## No leakage
Only completed-bar OHLC is used. Final daily range, later checkpoint completion, and future distribution fields are retrospective labels and are never used to establish a live loop state.
