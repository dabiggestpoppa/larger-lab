# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Implementation Block Plan

Bounded checkpoints for the future build (none authorized automatically):

| block | scope | gate |
|---|---|---|
| E0 | SOURCE / SCHEMA LOCK -- freeze event schema, hashes, parity golden admission | golden admission fixture |
| E1 | PURE R->NOTIONAL TRANSLATOR -- equity x f / (1R/1e4), pure, tested | fixture proofs pass |
| E2 | INSTRUMENT-SPEC + ROUNDING ENGINE -- broker spec, round-toward-lower, MIN_QUANTITY_RISK_OVERSHOOT | rounding contract tests |
| E3 | MODEL/REALIZED HEAT + RESERVATION ENGINE -- atomic reservations, dual-heat invariant | reservation + heat tests |
| E4 | ACCOUNT / MARGIN PRE-FLIGHT -- margin vs buying power gates, foreign-position awareness | margin gate tests |
| E5 | DURABLE LEDGER / RECONCILIATION -- append-only ledger, ownership, restart reconstruction | restart tests |
| E6 | SHADOW ORDER-INTENT GENERATION -- canonical order intent, no broker call | intent schema tests |
| E7 | DEMO / PAPER EXECUTION CANARY -- paper venue only | canary review |
| E8 | FORWARD OPERATIONS SAMPLE -- bounded forward shadow sample | sample review |
| E9 | PRODUCTION REVIEW -- human gate before any real enablement | explicit authorization |

Design principle: ALPHA ENGINE -> CAPITAL ROUTER -> CAPITAL TRANSLATOR ->
EXECUTION GATE -> BROKER ADAPTER -> RECONCILIATION stay separate modules.
No later checkpoint is automatically authorized; E0 begins only after this
planning checkpoint is accepted.
