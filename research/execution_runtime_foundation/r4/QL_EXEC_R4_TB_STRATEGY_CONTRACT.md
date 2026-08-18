# QL_EXEC_R4_TB_STRATEGY_CONTRACT (frozen science, reused not rewritten)

Loaded from the canonical engine at `tb_forward_engine` `b48fd352` (files frozen
in the source manifest). The generic path delegates to the SAME canonical
engine via `TBStrategyAdapter`; there is no independent reimplementation.

## Basis

```
b = ln(GBPAUD) - ln(GBPNZD) + ln(AUDNZD)
```

## Rolling z-score

```
z[i] = (b[i] - mean(b[i-L:i])) / std(b[i-L:i])   L = 200
```

- Window is the previous 200 bars, `[i-200, i)`, **current bar excluded**.
- `std` is population std (`ddof = 0`).
- `std <= 0` => `z = 0`.
- NaN handling: as frozen in the canonical engine (unchanged).

## Direction (canonical)

- `z > 0` (basis rich) => SHORT basket: sell GBPAUD, buy GBPNZD, sell AUDNZD.
- `z < 0` (basis cheap) => LONG basket: buy GBPAUD, sell GBPNZD, buy AUDNZD.

## Thresholds (frozen tb_forward_config)

| model | entry | exit | stop |
|---|---|---|---|
| PRIMARY TB-FWD-V1 | strict `|z| > 3.0` | SHORT `z <= -0.25`, LONG `z >= +0.25` | SHORT `z >= +6`, LONG `z <= -6` |
| CONTROL TB-FROZEN-CONTROL | strict `|z| > 2.5` | SHORT `z <= 0`, LONG `z >= 0` | symmetric 6.0 |

Exit check order (canonical P7): (1) session hard exit TIMEOUT, (2)
convergence/overshoot TP_HIT, (3) structural stop SL_HIT.

## Session

- London `03:00–12:00` EST, fixed UTC-5, **no DST** (`_est_hour = (hour-5) % 24`).
- `min_minutes_to_exit = 120`; hard exit `12:00` EST.
- `TRADE_LONDON_ONLY = True`.

## Model weights (TB-B)

- Inverse-ATR reference shares -> `exposure_matrix` + `project_basket(eps=0)`
  exact-neutral projection; `sum |weights| = 3`.
- Model weights are **NOT lots**. Min-lot clamp that breaks the hedge rejects
  (policy #7).

## Basket lifecycle

- Max one concurrent basket, no pyramiding, re-entry allowed after close.

## Parity result

EXACT (basis, z, thresholds, session, direction, weights) — by construction
(delegation) plus explicit frozen-value assertions in
`test_execution_runtime_r4_strategy.py`.
