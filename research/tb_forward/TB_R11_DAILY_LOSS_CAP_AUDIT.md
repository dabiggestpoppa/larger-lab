# TB-R1.1 — Daily Loss Cap Audit

## Question
The R0 truth lock carries `daily_loss_cap_pips = 500`. The old live wrapper does
not implement it. R1.1 must determine whether it is a canonical strategy rule,
a legacy deployment guard, a stale artifact, or ambiguous — and must NOT blindly
add it.

## Finding

**`daily_loss_cap_status = CANONICAL_ACTIVE`**

Evidence:

1. `tb_p5_validate.py` freezes `MAX_DAILY_LOSS_PIPS = 500.0` and its
   `run_frozen_signal` applies it inside the trade loop (accumulates net PnL per
   session-day, keys by the canonical `_session_date` roll rule).
2. `tb_p6_anatomy.simulate` (the frozen-signal replay used as the P7 truth
   source) applies the identical rule: when the current session-day's
   accumulated `daily[sd] <= -500`, the in-flight trade is abandoned
   (`in_trade=False; t=None; continue`) before any exit check.
3. It is therefore part of the sealed P5/P6/P7 simulation path, NOT a legacy
   MT5-bridge guard (the MT5 bridge files never reference it).

## Semantics (canonical, exactly as implemented)
- Per session-day (session-date = calendar date of the bar, rolled +1 day when
  the fixed-UTC-5 EST hour is `>= 19`).
- Net PnL accumulates from each closed trade's `pnl_net_pips`.
- If at the start of a bar the day's accumulated PnL `<= -500`, the current
  trade is abandoned (no close record) and no further entry happens that day
  while the balance is at/below the cap.

## Does it affect P7 lifecycle parity? **No.**
Measured on the sealed data set (265,809 M5 bars):
- P7 primary (entry 3.0, exit −0.25): minimum per-session-day cumulative net
  PnL = **−92.26** pips (never within 400 pips of −500). 194 events.
- Control (entry 2.5, exit 0.0): minimum per-session-day cumulative net
  PnL = **−92.26** pips. 405 events.

The cap never fires in either event set, so it does not alter R1.1 lifecycle
parity. This is consistent with the sealed research, where the 500-pip cap is a
safety bound that the historical dislocation trades never approached.

## R1.1 decision
- **Do NOT add a daily-loss-cap behavior to the strategy wrapper now.** The
  wrapper's parity with the sealed P7 simulation is exact without it, and adding
  a close/abandon path would be a behavior change with no parity benefit.
- Record it as `CANONICAL_ACTIVE` and defer mechanical implementation to the
  forward runner risk layer (R6/R10), where the same `MAX_DAILY_LOSS_PIPS = 500`
  semantics must be implemented as a *deployment guard* (halt new entries /
  flatten TB positions) — with an explicit, audited mapping to the canonical
  "abandon without close record" research behavior.

## Status
`daily_loss_cap_status = CANONICAL_ACTIVE` (not triggered in the P7 primary or
control event sets; parity unaffected; implementation deferred).
