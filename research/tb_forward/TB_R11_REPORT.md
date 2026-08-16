# TB-R1.1 — Prior-Stack Mechanical Repair (Report)

Checkpoint: `TB-R1.1-PRIOR-STACK-MECHANICAL-REPAIR`
Status: **PASS**
Branch: `tb-forward-engine`
Base: `01e6831763ac88c78fd54f6be7673526310795c4`
Canonical research: `6769ad31ac737946dae54e3660e22cb36f72e2b7`

## What was repaired (mechanical only)

1. **Fail-closed execution mode.** `triangular_basis_executor.py` defaulted to
   `--mode trade` (real orders on a bare run). Now defaults to `shadow`; the CLI
   accepts only `shadow`/`demo`; `trade`/`live`/unknown fail closed to shadow;
   `EXECUTION_AUTHORIZED = DEMO_AUTHORIZED = LIVE_AUTHORIZED = False`, so even
   `demo` cannot reach `order_send` in this checkpoint.

2. **Primary/control config separation.** New `tb_forward_config.py` freezes two
   explicit models: PRIMARY `TB-FWD-V1` (entry `|z| > 3.0`, SHORT exit
   `z <= −0.25`, LONG exit `z >= +0.25`) and CONTROL `TB-FROZEN-CONTROL`
   (entry `|z| > 2.5`, exit `z <=/>= 0.0`). Control is `shadow_only=true`,
   `execution_allowed=false` permanently.

3. **Signed P7 exit.** The wrapper's single symmetric `BASIS_EXIT_Z` was replaced
   by per-direction `short_exit_z` / `long_exit_z`. Exit-condition check order
   now matches the canonical P7 `simulate()` exactly: session hard exit
   (TIMEOUT) → convergence/overshoot (TP_HIT) → structural stop (SL_HIT).

4. **Canonical TB-B weights.** `_build_entry_intent` now computes inverse-ATR
   reference shares and projects them through the shared sealed research
   functions (`verify_tb_04a.exposure_matrix` + `tb_p6_anatomy.project_basket`
   at eps=0). `model_weight` = TB-B size (sum = 3), raw inverse-ATR retained as
   `reference_weight`. Model weights remain distinct from MT5 lots. Fail-closed
   on projection failure.

5. **Parity harness for the P7 primary contract** (`tb_r11_parity.py`).

## Parity results (exact, event-for-event)

| Metric | Result |
|---|---|
| P7 primary events (canonical / live) | 194 / 194 |
| P7 entry mismatches | 0 |
| P7 direction mismatches | 0 |
| P7 exit mismatches | 0 |
| P7 exit-reason mismatches | 0 |
| P7 weight mismatches (TB-B) | 0 |
| Control events (canonical / live) | 405 / 405 |
| Control mismatches | 0 |
| max |z| diff (265,809 bars) | 2.252e-12 |
| entry decision mismatches @2.5 / @3.0 | 0 / 0 |

TB-B weight parity is exact: 194/194 cases match `tb_p6_anatomy.enrich` TB-B
sizes to < 1e-6 (median residual exposure ~0.02–0.04%, vs the old raw
inverse-ATR 34.84%).

## Tests

| Suite | collected | passed | failed | skipped |
|---|---|---|---|---|
| `tb_r11_tests.py` (R1.1 strategy/safety/direction/contamination/atomic regression) | 36 | 36 | 0 | 0 |
| `tb_r11_parity.py` (P7 lifecycle + weight + z nonregression) | n/a (harness) | PASS | 0 | 0 |
| `tb_p6_tests.py` (sealed P6 research, unaffected) | 411 | 411 | 0 | 0 |
| `tb_p7_tests.py` (sealed P7 research, unaffected) | 160 | 160 | 0 | 0 |

The R1 audit harness (`tb_r1_audit.py`) is superseded by this checkpoint: its
exit-semantics and weight-residual checks documented the *pre-repair* state and
are intentionally replaced by `tb_r11_tests.py` + `tb_r11_parity.py`.

## Component status (after repair)

strategy_wrapper ADOPTED · normalization_engine ADOPTED · weight_engine ADOPTED ·
execution_contract ADOPTED · atomic_execution_layer ADOPTED ·
market_data_layer PENDING_R2 · persistence_layer PENDING_REPLACEMENT ·
broker_metadata_layer ADOPTED · session_time_layer ADOPTED ·
parity_harness ADOPTED · execution_safety REPAIRED_FAIL_CLOSED.

## Scientific changes

**NONE.** Basis, rolling-z (200 / ddof=0 / previous-bars-only), direction
convention, TB-B weighting definition, stop, session, hard-exit, and re-entry
semantics are all byte-for-byte the sealed research behavior (verified by exact
lifecycle parity). The 2.5/0 → 3.0/±0.25 transition is the deployment
translation of the sealed P6/P7 decisions, not new research.

## Execution authorization

**NOT_AUTHORIZED.** Default mode SHADOW; order_send unreachable in default mode;
control cannot execute; demo/live disabled.

## Next checkpoint

`TB-R2-SYNCHRONIZED-MARKET-DATA` — build the fail-closed synchronized three-leg
market-data layer (closed M5 signal bars, same-timestamp confirmation, execution
bid/ask ticks, quote age, cross-leg skew, stale-quote rejection, no forming-bar
leakage). `r2_cleared = true`.
