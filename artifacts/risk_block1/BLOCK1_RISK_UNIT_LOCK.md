# BLOCK-I RISK-UNIT LOCK

**1R = TARGET_VOL x sqrt(HOLD) = 24.4949 bps** (the sealed strategy's normalized
expected-move unit).

**1R IS NOT A STOP.** It is not a maximum trade loss, not a stop-loss distance,
not a broker risk percentage, not a guaranteed loss cap.

## Frozen account mapping

    account_return ~= trade_return_R x f

where f = static account-risk fraction per R. A trade of -3R at f = 1% costs
approximately -3% of the account.

## Frozen historical extremes (exact, from the sealed ledger)

| family | worst R | worst bps |
|---|---|---|
| A | -3.66R | -89.5 |
| B | -3.31R | -81.2 |

## Forbidden reinterpretations of f

- maximum trade loss
- stop-loss distance
- broker risk percentage
- guaranteed loss cap

Source: `R1_EVENT_RISK_LEDGER.csv` + `R4_RISK_UNIT_DEFINITION.md` (seal-verified).
