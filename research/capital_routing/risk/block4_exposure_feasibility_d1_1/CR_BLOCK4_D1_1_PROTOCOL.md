# CR-BLOCK4-D1.1 PROTOCOL — Broker-Independent Notional Feasibility Surface

**Checkpoint:** CR-RISK-BLOCK-IV-D1.1-BROKER-INDEPENDENT-NOTIONAL-FEASIBILITY-SURFACE
**Base:** `f52d5f482a3d5ff5b133a6335e9996ab98cb0bb3` (D1 plan)
**Status:** Lane A executed — DESCRIPTIVE / PREREGISTERED / NO OPTIMIZATION

## 1. Question

> Given a HYPOTHETICAL_DIAGNOSTIC maximum notional/equity ratio L, how much of
> the sealed 826-event economic-target book survives WITHOUT
> changing target exposure?

Lane A classifies using `m_t = target_notional / equity`; equity cancels, so
classifications are account-size invariant.

## 2. Non-goals (enforced)

No broker symbol, contract size, lots, margin, leverage API, account size,
currency conversion, volume step, MT5, TradeLocker, execution runtime, or
broker order. No rounding, clipping, or partial sizing. No performance-based
selection. No H1 / family / model-heat recomputation.

## 3. Frozen science

- 890 events (A 432 / B 458)
- ACCEPT_FULL 826 (A 371 / B 455);
  REJECT_HEAT_CAP 64
- A1_70_30, H1-1.00-REJ, f_total 1.00%; A admitted f 0.70%, B 0.30%
- RISK_UNIT_BPS 24.49489742783178 — NOT a hard stop
- Economic target N = E x admitted_f x pos_t x 1e4 / RISK_UNIT_BPS (D0.1 authoritative)

## 4. Frozen grid (EXACTLY these levels — from the D1 plan)

| L | n surviving | expected (D1) | replication |
|---|---|---|---|
| 0.5 | 39 | 39 | PASS |
| 1 | 178 | 178 | PASS |
| 2 | 417 | 417 | PASS |
| 4 | 655 | 655 | PASS |
| 8 | 786 | 786 | PASS |
| 16 | 817 | 817 | PASS |
| 32 | 825 | 825 | PASS |
| 64 | 826 | 826 | PASS |

If any count differs the checkpoint STOPS as
BLOCKED_D1_1_GRID_REPLICATION_MISMATCH (never amend D1).

## 5. Truth class

Every scenario is **HYPOTHETICAL_DIAGNOSTIC** — never actual account leverage, broker
leverage, a production limit, or a recommended leverage. Terminology is
`max_notional_multiple` / `notional_cap_multiple`.

## 6. Engine

`assess_notional_cap(economic_target, max_notional_multiple)` in
`src/capital_routing/feasibility/notional_feasibility.py` — pure,
deterministic, no broker / fs / network dependencies. Inputs are the
authoritative D0.1 event translations; no third translation implementation.
