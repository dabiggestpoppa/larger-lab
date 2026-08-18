# CR-BLOCK4-D1 REPORT

**Checkpoint:** CR-RISK-BLOCK-IV-D1-EXPOSURE-FEASIBILITY-STUDY-PLAN
**Base:** `3fde3bb1cf590c554241c23daa14e3d2242998aa`
**Status:** PASS (preregistration)

## Frozen science (verified)

- events 890 (A 432 / B 458)
- ACCEPT_FULL 826 (A 371 / B 455);
  REJECT_HEAT_CAP 64
- 1R 24.49489742783178 bps, NOT a hard stop
- economic target: N = E x admitted_f x pos_t x 1e4 / 24.49489742783178 (D0.1 authoritative)

## Frozen economic target distribution (engine-recomputed from source rows)

| stat | pooled | A | B |
|---|---|---|---|
| n | 826 | 371 | 455 |
| min | 0.135190736223 | 0.471320798891 | 0.135190736223 |
| p1 | 0.269311442774 | 0.620249739113 | 0.249964416601 |
| p5 | 0.514544844261 | 1.023122369206 | 0.431330237643 |
| p25 | 1.102337423306 | 2.140660334614 | 0.795200180453 |
| median | 1.984234123119 | 3.351336289995 | 1.284996946428 |
| p75 | 3.513366582731 | 5.305265624127 | 2.011641631920 |
| p95 | 7.610483704796 | 11.440705392953 | 4.123140103434 |
| p99 | 16.036374775248 | 17.206451034822 | 6.710483070067 |
| max | 32.766258738096 | 32.766258738096 | 22.275430454511 |

## Preregistered notional diagnostic grid (lane A stress surface)

| L (notional/equity) | pooled n | pooled % | A % | B % |
|---|---|---|---|---|
| 0.5 | 39 | 4.72% | 0.54% | 8.13% |
| 1 | 178 | 21.55% | 4.58% | 35.38% |
| 2 | 417 | 50.48% | 20.75% | 74.73% |
| 4 | 655 | 79.30% | 61.19% | 94.07% |
| 8 | 786 | 95.16% | 89.76% | 99.56% |
| 16 | 817 | 98.91% | 97.84% | 99.78% |
| 32 | 825 | 99.88% | 99.73% | 100.00% |
| 64 | 826 | 100.00% | 100.00% | 100.00% |

`diagnostic_grid_optimized_on_performance = false` — thresholds anchored to the
observed distribution before any result; all cells shown.

## Concurrency (frozen source)

max concurrency 3, hours 2/3/4+: 565/20/0,
max gross exposure 18.1878 f-units, episodes (12h) 482.

## Study lanes

A pure notional · B quantity · C margin/buying power · D full physical contract.
D1.1 (lane A) needs no broker truth and is ready; D1.2+ blocked until
instrument/margin truth exists (see missing truth register).

## Governance

- rounding primary ROUND_DOWN_TOWARD_ZERO; upward default false; min/max quantity
  blocked by default; clipping never called faithful
- falsification criteria frozen; no coverage target invented yet
- broker execution: FALSE · strategy science changed: FALSE
- d1_1_authorized: FALSE (human review required)

See the sibling artifacts for each contract. Decision: `CR_BLOCK4_D1_DECISION.json`.
