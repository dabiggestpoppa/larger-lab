# TB-LIVE-EXEC-03 Execution Hardening Report

## Scenarios
| scenario | →state | success | GATE_I |
|---|---|---|---|
| all_three_success | open | True | True |
| leg1_reject | aborted_flat | False | True |
| leg2_reject_partial | aborted_flat | False | True |
| leg3_reject_two_fills | aborted_flat | False | True |
| placed_not_filled | aborted_flat | False | True |
| fill_timeout | aborted_flat | False | True |
| spread_explosion | aborted_precheck | False | True |
| lot_rounding_rejection | open | True | True |

## Lot Translation
weight GBPAUD=0.65 notional=216.67USD raw=0.0012 rounded=0.01 realized=1862.30USD

## Close Recovery
close 3/3 -> closed success=True

## Foreign Isolation
Symmetry positions before=1 after=1 unchanged=True

## Gates
GATE D foreign untouched: PASS
GATE E partial recovers flat: PASS
GATE I no OPEN from PLACED: PASS
GATE J model weight -> lots deterministic: PASS
GATE L CLOSED only after 3 flat: PASS
GATE M order_check all pass before send: PASS

OVERALL: PASS
