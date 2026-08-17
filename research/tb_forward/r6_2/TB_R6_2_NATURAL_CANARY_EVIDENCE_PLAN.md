# TB-R6.2-NATURAL-CANARY-EVIDENCE-SEAL

## Purpose

Evidence-only checkpoint to be run **after the first naturally generated TB-FROZEN-CONTROL basket completes end-to-end** on the persistent OxSecurities Demo runtime.

This checkpoint is intentionally stored in-repo now so the forward runtime can remain untouched while waiting. When the trigger occurs, the next agent should pull the latest `tb-forward-engine` branch and execute this plan.

## Authoritative base

- Stable runtime seal: `223fd024418db2e1bb2c6ed9ac7334488f263f5b`
- Deployment generation: `TB-R6-FWD-DEMO-001`
- Runtime path: `C:\Users\wifik\Desktop\larger-lab-tb-forward-engine`
- Dashboard: `http://127.0.0.1:8765`
- Executable demo canary: `TB-FROZEN-CONTROL`
- Primary candidate `TB-FWD-V1`: SHADOW ONLY
- Live trading: NOT AUTHORIZED

## Trigger

Do **not** execute this checkpoint merely because a signal appears.

Execute only when at least one genuine natural control basket has completed the full lifecycle:

`natural closed-M5 signal -> execution-health eligible -> 3/3 demo fills -> OPEN_VERIFIED -> canonical strategy exit -> 3/3 close -> FLAT -> broker/local reconciliation`

If no natural basket has completed, leave the runtime running and do nothing.

## Hard scope

This is an **evidence-only seal**.

Do not change:

- basis math
- z calculation
- entry threshold
- exit threshold
- session rules
- stop logic
- weighting
- lot translation
- execution model
- capital scale
- dashboard/runtime architecture unless a proven defect prevents truthful evidence extraction

Do not force, inject, replay, manually trigger, or manufacture a trade and call it natural evidence.

## Natural basket audit

Identify the first completed natural TB-FROZEN-CONTROL basket from the authoritative runtime ledger and broker-linked evidence.

Audit at minimum:

### Signal

- signal bar-open timestamp
- basis value
- z value
- direction
- session eligibility
- strategy identity
- dedup key

### Execution preflight

- account/server identity
- quote age for each leg
- spread for each leg
- cross-leg quote skew
- model weights
- target notionals
- requested lots
- rounded lots
- post-rounding neutrality residual
- Gate K result
- admission/rejection state

### Broker execution

For all three legs record:

- symbol
- side
- requested volume
- filled volume
- preflight executable price
- fill price
- slippage
- order ticket
- deal ticket
- position ticket
- filling mode
- send-to-response latency
- send-to-fill latency

Also report:

- leg1->leg2 latency
- leg2->leg3 latency
- leg1->leg3 total completion latency
- 3/3 OPEN_VERIFIED state

### Lifecycle / exit

Verify the strategy engine, not a manual action, determined the canonical exit.

Allowed natural lifecycle exit classes are the frozen control equivalents of:

- z0 convergence exit
- z6 structural stop
- hard session exit

Record:

- exit signal timestamp
- exit reason
- exit z
- holding duration
- all close requests
- all close deals
- close slippage
- terminal position state
- final broker/local reconciliation

If a human safety override occurred, classify it explicitly and do **not** count that basket as the natural lifecycle required for PASS.

## Cost audit

Measure actual demo execution friction for the completed basket:

- spread paid
- commission
- slippage
- swap if any
- total broker friction
- comparison versus frozen research cost assumption

This comparison is descriptive only.

Do not alter historical cost assumptions in this checkpoint.

## PnL audit

Record descriptively:

- gross basket PnL
- net basket PnL
- per-leg PnL
- realized TB return for the basket
- dashboard daily TB PnL after close
- dashboard since-deployment TB PnL after close

Do not calculate or infer PF, WR, CAGR, expectancy, or production readiness from one basket.

## Ownership and safety invariants

Required:

- foreign positions modified = 0
- duplicate orders = 0
- primary execution calls = 0
- control basket ownership unambiguous
- no orphan positions
- ledger terminal state valid
- broker/local reconciliation clean

## Historical nonregression

Re-run the frozen historical engine after evidence extraction.

Expected regression fingerprints on the authoritative historical sample:

- PRIMARY: `194 / 194`
- CONTROL: `405 / 405`
- lifecycle mismatches: `0`

These remain historical regression fingerprints only; they are not forward trade-count targets.

Also run the relevant frozen suites:

- R1.1
- R2
- R3
- R6/R6.1/R6.1A runtime invariants
- P6
- P7

Report exact totals.

## Required artifacts

Create under:

`research/tb_forward/r6_2/`

- `TB_R6_2_PROTOCOL.md`
- `TB_R6_2_INPUT_HASH_MANIFEST.json`
- `TB_R6_2_RUNTIME_EVIDENCE_WINDOW.json`
- `TB_R6_2_NATURAL_SIGNAL_AUDIT.json`
- `TB_R6_2_PREFLIGHT_AUDIT.json`
- `TB_R6_2_ORDER_DEAL_AUDIT.csv`
- `TB_R6_2_LEGGING_LATENCY.csv`
- `TB_R6_2_SLIPPAGE.csv`
- `TB_R6_2_EXIT_AUDIT.json`
- `TB_R6_2_COST_AUDIT.json`
- `TB_R6_2_PNL_AUDIT.json`
- `TB_R6_2_OWNERSHIP_AUDIT.json`
- `TB_R6_2_LEDGER_RECONCILIATION.json`
- `TB_R6_2_HISTORICAL_PARITY.json`
- `TB_R6_2_COMPONENT_STATUS.json`
- `TB_R6_2_REPORT.md`
- `TB_R6_2_DECISION.json`

## Decision fields

`TB_R6_2_DECISION.json` must include at minimum:

- checkpoint
- status
- base_commit
- runtime_generation
- natural_signal_count_observed
- natural_control_baskets_opened
- natural_control_baskets_completed
- audited_basket_id
- entry_direction_parity_pass
- preflight_pass
- gate_k_pass
- three_leg_open_verified
- exit_logic_pass
- natural_exit_reason
- three_leg_close_verified
- atomic_close_pass
- actual_cost_measurement_pass
- ledger_integrity_pass
- broker_reconciliation_pass
- foreign_positions_modified
- duplicate_orders
- primary_execution_calls
- historical_parity_pass
- primary_event_count
- control_event_count
- lifecycle_mismatches
- strategy_math_changed
- natural_canary_pass
- r6_full_pass
- r7_ready
- r7_authorized
- live_authorized
- human_review_required
- next_checkpoint_recommended

## PASS gate

Set `natural_canary_pass = true` and `r6_full_pass = true` only if:

1. the signal was naturally produced by the sealed control strategy on real synchronized closed M5 bars;
2. all execution-health gates passed without threshold relaxation;
3. the three intended legs were filled and broker-verified;
4. OPEN_VERIFIED was reached with correct direction and ownership;
5. the canonical strategy lifecycle generated the exit;
6. all three positions closed and broker truth verified FLAT;
7. ledger/broker reconciliation is clean;
8. foreign positions modified = 0;
9. duplicate orders = 0;
10. primary execution calls = 0;
11. historical nonregression remains exact;
12. strategy math remains unchanged;
13. relevant tests pass.

If the basket is incomplete, manually overridden, ambiguous, or reconciliation is not clean, do not force PASS. Record the exact blocker.

## After PASS

Set:

- `r6_full_pass = true`
- `r7_ready = true`
- `r7_authorized = false`
- `live_authorized = false`

Recommend:

`TB-R7-CANARY-DEMO-OPERATIONS-SEAL`

R7 target:

- minimum 10 completed natural control baskets
- preferred 20+

The R6.2 basket may count toward R7 cumulative evidence if the engine/configuration is unchanged.

Do **not** auto-start R7.

## Current instruction to future agent

When told to continue TB forward deployment:

1. pull the latest `tb-forward-engine` branch;
2. read this file first;
3. inspect the existing runtime/ledger evidence;
4. if the trigger has not occurred, leave the engine running and report `WAITING_NATURAL_CANARY`;
5. if a complete natural basket exists, execute this evidence seal exactly;
6. make no strategy changes;
7. commit the evidence checkpoint exactly as:

`TB-R6.2-NATURAL-CANARY-EVIDENCE-SEAL`

Then STOP for human review.
