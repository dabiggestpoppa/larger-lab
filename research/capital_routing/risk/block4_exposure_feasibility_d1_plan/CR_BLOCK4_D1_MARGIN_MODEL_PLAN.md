# CR-BLOCK4-D1 MARGIN MODEL PLAN

## Truth path

`required_margin` is a broker/instrument-specific function of (actual notional,
instrument, account, side, current price). It is NEVER universally assumed to be
`notional / leverage`.

## Current truth

All margin fields are **UNKNOWN** at D1 planning time:

- margin model / symbol margin mode / margin tiers
- account leverage (FakeMT5 demo fixtures are NOT truth)
- symbol leverage
- buying-power semantics
- hedging/netting mode

## Lane C rule

If actual broker/account margin truth is missing:

**BLOCKED_PENDING_MARGIN_TRUTH.**

Do not make up leverage. Any margin number used in a scenario must carry a
truth class; `HYPOTHETICAL_DIAGNOSTIC` margin scenarios are allowed for
sensitivity exploration but are never labeled faithful.

## Structural vs momentary

- STRUCTURAL feasibility: could the target fit under the contract on an otherwise
  available account?
- MOMENTARY OPERATIONAL feasibility: given current positions/equity/margin usage
  and foreign exposure, can it open right now?

The research feasibility study emphasizes structural truth first; momentary
operational gating belongs to the execution runtime.
