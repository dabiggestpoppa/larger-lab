# TB-R6 — Demo Execution Canary — PROTOCOL

Checkpoint: `TB-R6-DEMO-EXECUTION-CANARY`
Base: `9d0a3951413d153d494b8b1e81afcde5894cd40b` (R5.1)
Environment: **OxSecurities-Demo (DEMO only)** — first order-submitting checkpoint.

## Scope

R6 is the first checkpoint allowed to call `mt5.order_send` — on the approved
**DEMO** environment only. Its purpose is execution mechanics, not alpha
validation:

1. create a three-leg basket via real broker orders
2. submit all legs, identify actual fills
3. verify ownership (magic + comment linkage + broker truth)
4. detect incomplete baskets, rollback/flatten safely
5. close the full basket, verify flat via broker truth
6. measure slippage and legging latency
7. survive restart/reconciliation with broker-open positions
8. never touch unrelated positions
9. keep the z3 primary (TB-FWD-V1) shadow-only

## Roles

| identity | entry | exit | R6 role |
|---|---|---|---|
| `TB-DEMO-EXEC-TEST` (magic 31082027) | harness-controlled | immediate close | Phase A controlled execution tests |
| `TB-FROZEN-CONTROL` (magic 31082026) | strict z>2.5 | z0 canonical | Phase B natural canary (executable) |
| `TB-FWD-V1` (magic 31082026) | strict z>3.0 | signed ±0.25 | **SHADOW ONLY — never executes in R6** |

## Account identity gate

Before ANY `order_send`:

- terminal company == Ox Securities Pty Ltd
- server == OxSecurities-Demo
- trade_mode == 0 (DEMO)
- currency == USD
- symbol resolution exact (GBPAUD.PRO / GBPNZD.PRO / AUDNZD.PRO)

Any mismatch → ABORT.

## Fixed demo notional

`basket_notional_usd = 5000` frozen **before** execution observation
(`basket_notional_source = BROKER_MINIMUM_EXECUTION_TEST`):
smallest notional that clears `volume_min` on all three legs (0.01 / 0.01 /
0.02 lots after rounding), respects `volume_step`, passes Gate K, and is large
enough for meaningful fill/slippage measurement. Not changed because baskets
win or lose. No Kelly/compounding/scale-in.

## Preflight gates (before leg 1)

- quote age ≤ 2000 ms per leg (fresh-tick wait loop; recalibrate each poll)
- cross-leg skew ≤ 1000 ms
- spread ≤ 100 pts per leg (engineering safety gate, pre-registered — not
  PnL-tuned; R5.1 observed Sunday-rollover spreads far above this)
- Gate K post-rounding residual ≤ 10%
- order_check per leg (fill-mode probe) passes
- metadata hash stable; ledger healthy; reconciliation FLAT
- no unknown TB-owned positions

Any failure → NO ORDER (REJECT/WAIT).

## Order sequence (atomic 3-leg)

INTENT_CREATED → PREFLIGHT_PASS → LEG1_SUBMITTING → LEG1_FILLED →
LEG2_SUBMITTING → LEG2_FILLED → LEG3_SUBMITTING → LEG3_FILLED →
BASKET_OPEN_VERIFIED (broker-verified, 3/3 tagged positions) — or safe
rollback. A basket is NOT OPEN on leg-1 success alone.

Fill verification: poll `positions_get()` for **this basket's comment-tagged**
positions (comment linkage is the reliable discriminator — R6 discovered
`positions_get()` can return a stale snapshot under rapid successive fills,
which previously made verification pick up the *previous* basket's tickets).

## Broker truth

Never infer fills from `order_send` return alone. Verify with
positions + history deals (ticket, deal id, volume, price, side, comment tag).
Close verified by positions disappearing after close deals.

## Slippage / latency measurement

Per leg: signal reference price, preflight bid/ask, actual fill price,
slippage vs signal (pts), leg1→leg2, leg2→leg3, leg1→leg3 ms.

## Failure handling

- 0/3 fills → abort, no basket
- 1/3, 2/3 fills → BROKEN_HEDGE → flatten owned legs → verify flat
  (in-sim deterministic injection against the real execution state machine;
  a naturally occurring broker partial is classified separately)
- restart with broker-open basket → ledger integrity → reconstruct →
  real broker read → `reconcile_open_baskets()` from comment tags →
  recover OPEN_VERIFIED → continue/close

## Non-negotiable

- `order_send` only after identity gate + all preflight gates
- foreign/manual positions never touched (magic + comment linkage required)
- no duplicate orders (dedup keys / restart preserves them)
- z3 primary execution calls == 0
- historical parity 194/194 + 405/405 exact, strategy science unchanged
