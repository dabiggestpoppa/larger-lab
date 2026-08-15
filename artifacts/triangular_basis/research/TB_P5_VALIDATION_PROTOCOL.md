# TB-P5 — NEUTRAL-BASIS VALIDATION PROTOCOL

**Phase:** TB-P5-NEUTRAL-BASIS-VALIDATION-01 (VALIDATION ONLY)
**Base:** commit `303abcdae` — TB-RESEARCH-VERIFY-04A accepted as truth source.
**Status:** FROZEN. No parameter optimization, no signal changes, no new
instruments, no ML, no Kelly sizing, no CEREBUS filters, no USD hedge overlay.
**Lead evaluator:** independent re-simulation from raw bars (see section R).

This document defines *how* the phase was executed so any reviewer can repeat
it. Results are in `TB_P5_VALIDATION_REPORT.md`; machine verdicts in
`TB_P5_DECISION.json`.

---

## 0. Freeze list (what is NOT allowed to change)

| Item | Frozen value |
|---|---|
| Signal: basis | `X = ln(GBPAUD) − ln(GBPNZD) + ln(AUDNZD)` (log basis) |
| Signal: z-score | rolling mean/std, lookback **200** bars, window excludes current bar |
| Entry | London session (03:00–12:00 EST via UTC−5), z ≥ **2.5** |
| Exit | z ≤ 0 (TP), z ≥ 6 (SL), 12:00 hard exit, min 120 min hold |
| Signal time frame | M5 |
| Cost model | **10.2 pips** total round-trip per trade (frozen) |
| TB-A sizing | canonical inverse-ATR (20-bar), total leverage 3.0 |
| TB-B sizing | exact-neutral projection: min ‖q−q_α‖² s.t. E·q = 0, q ≥ 0, Σq = 1 |
| TB-C sizing | same objective with residual cap ‖E·q‖∞ ≤ ε/100, ε ∈ {2.5, 5, 7.5, 10}% |
| Conversion rates | seal rates 2026-08-10 (GBP 1.34852, AUD 0.70583, NZD 0.58844) |
| Epsilon variants | fixed validation set — **not** selected from results |
| Random seeds | all RNG seeded `SEED = 42` → fully deterministic |

TB-C ceilings are *validation variants*, not tunable parameters. No ε is
selected during this phase; every variant is reported.

## 1. Data

- Inputs: canonical research M5 files in `quant-lab/data/`
  (`GBPAUD_M5.csv`, `GBPNZD_M5.csv`, `AUDNZD_PRO_M5.csv`), OHLC.
- Synchronization: inner join on timestamp (`quant-lab/engines/analyze_triangular_basis.py`
  semantics). Result must equal the parity series (`artifacts/triangular_basis/live/bar_parity.csv`)
  to 1e-9 (asserted, fail-closed).
- Canonical trade log: `artifacts/triangular_basis/live/canonical_trade_log.csv` (405 trades).
- FORWARD data: any series after `research_last_ts` (2026-05-29 19:50) is evaluated
  separately and labeled `FORWARD_OOS`; same-source continuation only. Different
  price sources (e.g. `*_M5_fetched.csv`) are rejected by the data audit.

## 2. Causal weight construction (audit requirement)

For every trade the TB-B/TB-C weight vector is a pure function of **entry-time
information only**:

1. `q_α` — canonical inverse-ATR shares at entry (ATR-20 window ends at entry bar);
2. entry-time closes of the three crosses (for the exposure matrix E);
3. frozen constants (seal rates, contract size, ε).

Explicitly forbidden (tested, see `TB_P5_CAUSAL_WEIGHT_AUDIT.md`):
future bars, exit prices/z/basis, full-sample normalization, future volatility,
future conversion rates, realized PnL. Fail-closed: if weights cannot be shown
causal, the phase fails.

## 3. Chronological evaluation (no shuffling)

- **Expanding** prefixes: every quarter boundary, metrics on all trades up to it.
- **Rolling**: 183-day windows, ≥20 trades.
- **Chronological holdout**: all trades with exit ≥ 2025-07-01 (last 94 trades).
- Year / quarter / month (≥5 trades) / volatility tercile / direction blocks.

## 4. Metrics (apples-to-apples, per model)

trades, win rate, net pips, gross pips, EV/trade, avg win, avg loss, payoff
ratio, profit factor, median trade, Sharpe (annualized, daily resampling,
√252), Sortino, chronological max DD, Calmar, longest losing streak, time in
market, turnover, total modeled cost.

Derived:
- `AlphaRetention = EV_variant / EV_TB-A × 100`
- `AlphaMultiplier = EV_variant / EV_TB-A`
- `DDReduction = 1 − |DD_variant| / |DD_TB-A|`

## 5. Attribution (basis reversion, not rotation)

Per trade, exact decomposition from entry/exit prices and basket weights
(basis leg is GBPNZD):

```
basis_pnl = dir · w_GN · (basis_exit − basis_entry)
rot_pnl   = dir · (w_GA − w_GN) · Δln(GBPAUD) + dir · (w_AN − w_GN) · Δln(AUDNZD)
cost_pnl  = −10.2
pnl       = basis_pnl + rot_pnl + cost_pnl   (identity asserted to 1e-9)
```

Basis share of gross PnL is reported per model and per year. No single-currency
(GBP-only / AUD-only / NZD-only) attribution is attempted — it is not
identifiable from three crosses without USD pairs.

## 6. Dislocation anatomy (measurement only)

Per trade: basis magnitude at signal, entry z, direction, max further
extension, time to max extension, time to 25/50/75/100% convergence, weekday,
volatility regime, time since prior exit, MFE/MAE per model. This dataset feeds
a *future* optimization phase; nothing here alters the strategy.

## 7. Cost & execution stress

- Cost multipliers: 1.0×, 1.25×, 1.5×, 2.0×, 3.0× on the frozen 10.2 pips.
- Report the multiplier at which EV = 0 (linear interpolation between grid points).
- Execution asynchrony: per-leg slippage 0.1 / 0.3 / 0.5 pips (3 legs) on top of
  modeled costs.

## 8. Broker lot translation

Weights → lots at notionals {5k, 10k, 25k, 50k, 100k} USD:
- `lots = notional · q_j / (contract · price · rate_quote)` rounded to 0.01
  with min 0.01;
- report executable residual (recomputed from rounded lots), rejection rate,
  weight distortion, PnL ratio exec/model.
- No notional is *selected* to maximize PnL; the report lists the minimum
  scale at which the intended geometry is representable.

## 9. Robustness

- Bootstrap (2000 draws, SEED 42): EV/PF/win-rate 95% CIs.
- Block bootstrap (block = 20, 500 draws): DD and losing-streak distributions.
- Concentration: top 1% / 5% / 10% of |PnL| share of total |PnL|.
- Superiority of TB-B/C over TB-A must survive dropping the top 5% trades.

## 10. Year-by-year falsification

Every calendar year reported for every model (N, EV, PF, WR, max DD, basis
share, cost drag). Any year with PF ≤ 1 (N ≥ 10) or EV ≤ 0 is flagged — never
hidden inside aggregates.

## 11. Verdict criteria

| Grade | Requirements |
|---|---|
| TB-A: VALIDATED | causal signal reproduction exact; EV > 0; PF > 1.5 |
| TB-A: DEGRADED | otherwise |
| TB-B/TB-C: STRONG | exact signal reproduction; EV > 0; PF > 1.5; positive EV in last year AND chronological holdout; no weak year; basis share ≥ 60%; EV-zero cost multiplier ≥ 1.5×; executable lot translation feasible (rejection < 5% at some notional ≤ $50k); superiority not dominated by top 5% |
| CONDITIONAL | EV > 0 and PF > 1.5 but a STRONG criterion fails |
| FAIL | EV ≤ 0 or PF ≤ 1.5 |

Historical PF 8–12 is **not** required to repeat; the objective is survival of
the *edge*.

## 12. Optimization handoff

If ≥ 1 neutral model is STRONG → `optimization_cleared = true` and
`TB-P6-OPTIMIZATION-RESEARCH-PLAN.md` is written — an *inventory* of candidate
dimensions, explicitly reserved for human review. **No optimization begins
automatically.** Phase stops for human review.

## R. Reproducibility

```
python quant-lab/engines/tb_p5_validate.py   # regenerates all TB_P5_* outputs
python quant-lab/engines/tb_p5_tests.py      # deterministic tests, exit 0 = pass
```

Both scripts are self-contained (numpy/pandas/scipy), seed everything
deterministically, and assert the key integrity identities (basis diff ≤ 1e-9,
PnL diff ≤ 1e-9, decomposition identity ≤ 1e-9). The data files are committed
plain blobs (not LFS pointers), so a fresh checkout reproduces identical bytes.
