# QL_EXEC_R0_CAPITAL_ROUTING_INTEGRATION

Capital Routing remains separate science. The execution substrate only consumes an approved capital decision.

---

## 1. Sealed authority (frozen SHA `40d23712`)

- Checkpoint: `CR-RISK-BLOCK-III-SCALE-SEAL-R1-FAIL-CLOSED-GATE` (PASS).
- Preferred research default: allocation `A1_70_30`, heat `H1-1.00-REJ`, `f_total = 1.00%`.
- Allowed allocations: `A0_50_50`, `A1_70_30`; diagnostic-only: `A2_100_0_A`, `A3_0_100_B`.
- Scale bands: conservative [0.25, 0.5], robust core [0.75, 1.0], aggressive [1.5, 2.0], stress [3.0, 3.0].
- `production_scale_selected = false`, `deployment_authorized = false`, `mt5_authorized = false`, `human_review_required = true`.

## 2. R-risk unit (frozen)

`1R = TARGET_VOL × sqrt(HOLD) = 24.49489742783178 bps` — a normalized expected-move unit. **1R is NOT a stop** and not a maximum loss. `account_return ≈ trade_return_R × f`. Family A historical worst -3.66R; Family B -3.31R.

The substrate must not convert `f = 0.70%` into "maximum loss = 0.70%".

---

## 3. What the infrastructure must NOT change

- A/B family classification;
- family weights (70/30, 50/50);
- f_total;
- H1 gross heat cap and its admission decisions (`ACCEPT_FULL` / `ACCEPT_SCALED` / `REJECT_HEAT_CAP`);
- the robust scale region.

---

## 4. Interaction chain

```
VALID EVENT
  -> strategy identity
  -> family / capital policy  (CapitalRoutingPolicy: family, requested_f, H1 admission)
  -> ACCOUNT ROUTING          (account_id, role, account-state snapshot)
  -> account equity           (the actual denominator)
  -> normalized sensitivity budget
  -> notional
  -> broker quantity
  -> actual translated heat
  -> order intent
```

Percent-of-equity is computed only after account binding. This is the architectural correction to TB's current fixed `BASKET_NOTIONAL_USD = 5000.0`.

---

## 5. Example (research translation only, not production)

Event family A, f_total 1.00, family weight 0.70 → requested_f 0.70 → H1 decision ACCEPTED. The account layer then resolves account_id, equity, event dollar sensitivity, notional, and quantity. The substrate does not recompute A/B weights, f_total, or H1.

---

## 6. R0 scope

R0 only specifies the boundary. Capital Routing execution-translation integration lands in R6 (PORTFOLIO_MASTER + SHARED CAPITAL RESERVATION), with `next_checkpoint_authorized = false`.
