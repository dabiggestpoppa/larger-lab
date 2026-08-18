# QL-EXEC-R4.1 — Evidence Stopping Rule (frozen pre-deployment)

Success is defined by BOTH minimum observation time AND minimum meaningful
event counts. The counts below are frozen NOW, not invented after seeing
results.

## Frozen G1 evidence criteria (all must be satisfied)

| Category | Minimum |
|----------|---------|
| synchronized closed common bars | N = 1,000 |
| decision opportunities (signal-evaluated bars) | N = 1,000 |
| natural CONTROL signals observed | N = 1 (if feasible; no forcing) |
| natural PRIMARY signals observed | N = 1 (if feasible; no forcing) |
| basket open/close observations (if any signal fires) | N = 1 full lifecycle (only if a control signal actually fires) |
| market-close / reopen cycles observed | N = 1 |
| restart/recovery drill | N = 1 |
| minimum wall-clock observation | 5 trading days |

## Rules

- A natural signal is NOT forced. If none occurs, observation continues; the
  shadow canary target is a natural strategy decision with exact parity.
- No synthetic live market data is injected into the production shadow
  process; offline fault fixtures remain separate.
- Event-count evidence is the primary criterion; wall-clock days alone never
  declare success.
- If the criteria are unmet, R4.2 remains NOT complete and the observation
  window extends without redefining the thresholds.
