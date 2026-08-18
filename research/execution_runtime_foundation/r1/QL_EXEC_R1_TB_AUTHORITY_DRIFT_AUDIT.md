# QL_EXEC_R1_TB_AUTHORITY_DRIFT_AUDIT

## Drift

| Item | SHA |
|---|---|
| R0 TB authority | `df5f349e02ac932491cb067df7aff25cb71c50ac` (`TB-R6.2-NATURAL-CANARY-EVIDENCE-PLAN`) |
| R1 TB authority | `d12005988ce61170d9bc5478089baa5ce54cc2a9` (`TB-R6.1B-FIX-WORKER-STATE-LATCH`) |

## Change

`ONLINE_MARKET_CLOSED` no longer latches after market/feed recovery.

- Strategy math: UNCHANGED.
- Runtime tests: 38/38.
- This is an engineering-only state-recovery fix.

## R1 disposition

- Do NOT cherry-pick / merge / modify TB runtime code.
- Update the authority manifest and future parity expectations only.

## Future R2/R4 parity requirement

R2 (`MT5BrokerSession`) and R4 (TB full non-regression) must include the regression:
`market closed -> market recovery -> FLAT/OPEN state recomputation`.
