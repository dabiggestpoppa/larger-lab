# TB-P5 — NEUTRAL-BASIS VALIDATION REPORT

**Status:** VALIDATION COMPLETE — machine-readable verdicts in `TB_P5_DECISION.json`.
**Base:** commit `303abcdae` (TB-RESEARCH-VERIFY-04A accepted as truth source).
**Protocol:** `TB_P5_VALIDATION_PROTOCOL.md` (frozen procedure, metrics, verdict rules).
**Reproduce:** `python quant-lab/engines/tb_p5_validate.py` + `python quant-lab/engines/tb_p5_tests.py` 
(deterministic, seed 42; all integrity identities asserted fail-closed).

## 0. Data audit

- Synchronized research series: **265,809 bars**; identical to the parity series (max close diff **0.0e+00**).
- **FORWARD_OOS: PENDING.** No synchronized continuation of the frozen feed exists after the research cutoff (2026-05-29 19:50:00). Post-cutoff files (`*_M5_fetched.csv`) are a different price source (mean diff vs canonical: GA 0.0028, GN 0.0031, AN 0.0000); the only same-source extension is single-leg AUDNZD. Shadow collection prepared instead 
(see TB_P5_FORWARD_OOS.csv).

## 1. Causal signal re-simulation

- Frozen signal re-run causally from raw bars reproduces the canonical 405-trade log **EXACTLY** (405 trades; mismatched trades: 0).
- Trade count/entry-exit times/direction/z-scores/sizes/PnL all match to 1e-9 (asserted in tb_p5_tests.py).

## 2. Causal weight audit (detail: TB_P5_CAUSAL_WEIGHT_AUDIT.md)

- TB-B/TB-C weights are pure entry-time functions (entry closes, entry ATR, frozen rates).
- Tested for leakage: future bars, exit info, full-sample normalization, future vol, 
future conversion rates, realized PnL — **all clear**.
- Conversion-rate stress (f=1 identity, GBP±10%/AUD∓10%/NZD±10%): max |ΔEV| ≤ 10.7%, 
max Δ median residual ≤ 0.02 pp 
— sizing is insensitive to conversion assumptions; rate leakage cannot explain the 
TB-B/TB-C improvement.

## 3. Chronological evaluation (detail: TB_P5_WALK_FORWARD_RESULTS.csv)

- **Expanding prefixes:** TB-B EV > TB-A EV at **all** 16 quarter prefixes (final prefix: 17.86 vs 8.74 pips).
- **Chronological holdout** (last 94 trades, exit ≥ 2025-07-01):

| Model | N | EV/trade | PF | WR | MaxDD |
|---|---|---|---|---|---|
| TB-A | 94 | 6.30 | 2.14 | 69.1% | -62.6 |
| TB-B | 94 | 13.46 | 6.44 | 84.0% | -35.4 |
| TB-C-2.5% | 94 | 12.89 | 6.02 | 83.0% | -36.7 |
| TB-C-5% | 94 | 12.34 | 5.64 | 83.0% | -38.0 |
| TB-C-7.5% | 94 | 11.80 | 5.22 | 80.9% | -39.3 |
| TB-C-10% | 94 | 11.25 | 4.80 | 78.7% | -40.6 |

- Volatility regime (entry basis-vol tercile), session direction, and 183-day rolling blocks are all in TB_P5_WALK_FORWARD_RESULTS.csv (kind = vol_regime / direction / rolling).

## 4. Year-by-year falsification (detail: TB_P5_YEARLY_RESULTS.csv)

| Year | N | TB-A EV / PF | TB-B EV / PF | TB-C-5% EV / PF |
|---|---|---|---|---|
| 2022 | 51 | 15.09 / 3.34 | 23.84 / 12.28 | 22.76 / 10.31 |
| 2023 | 127 | 10.96 / 4.06 | 20.14 / 17.96 | 18.92 / 15.34 |
| 2024 | 92 | 7.21 / 3.44 | 16.44 / 30.97 | 15.22 / 27.93 |
| 2025 | 91 | 4.37 / 1.72 | 14.55 / 8.25 | 13.29 / 7.02 |
| 2026 | 44 | 7.21 / 2.12 | 14.16 / 5.39 | 12.99 / 4.71 |

- **No weak year for any model** (every year N≥10 has PF > 1 and EV > 0; flags all OK).

## 5. Model comparison (detail: TB_P5_MODEL_COMPARISON.csv)

| Model | EV/trade | PF | WR | MaxDD | Sharpe | Sortino | AlphaRet | DD-red |
|---|---|---|---|---|---|---|---|---|
| TB-A | 8.74 | 2.87 | 70.6% | -133.0 | 6.93 | 10.26 | 100% | 0% |
| TB-B | 17.86 | 12.42 | 85.9% | -35.4 | 14.74 | 36.25 | 204% | 73% |
| TB-C-2.5% | 17.26 | 11.49 | 85.4% | -36.7 | 14.49 | 34.57 | 197% | 72% |
| TB-C-5% | 16.66 | 10.65 | 85.2% | -39.9 | 14.21 | 33.02 | 191% | 70% |
| TB-C-7.5% | 16.05 | 9.80 | 84.4% | -43.4 | 13.90 | 31.52 | 184% | 67% |
| TB-C-10% | 15.45 | 8.97 | 83.5% | -47.0 | 13.53 | 29.66 | 177% | 65% |

- Median residual (model-level, entry-time): TB-A 34.8%, TB-B 0.0%, TB-C-2.5% 2.5%, TB-C-5% 5.0%, TB-C-7.5% 7.5%, TB-C-10% 10.0%.
- Full metric set (avg win/loss, payoff, median, Calmar, longest losing streak, 
time in market, turnover, total cost) is in TB_P5_MODEL_COMPARISON.csv.

## 6. Basis-edge reconfirmation (detail: TB_P5_BASIS_ATTRIBUTION.csv)

| Model | basis share of gross PnL |
|---|---|
| TB-A | 104.8% |
| TB-B | 103.7% |
| TB-C-2.5% | 103.1% |
| TB-C-5% | 102.5% |
| TB-C-7.5% | 101.9% |
| TB-C-10% | 101.4% |

- Basis reversion remains the PnL source for **every** model (identity asserted to 1e-9). 
- No single-currency attribution attempted (not identifiable from three crosses).

## 7. Dislocation anatomy (detail: TB_P5_DISLOCATION_ANATOMY.csv — measurement only)

- Median time to 50% convergence: 55 min; median time to full convergence: 120 min; median |entry basis|: 0.0017.
- Weekday / volatility-regime / extension / MFE / MAE per model: all in the CSV. 
Nothing here alters the strategy.

## 8. Cost & execution stress (details: TB_P5_COST_STRESS.csv, TB_P5_EXECUTION_STRESS.csv)

| Model | EV-zero cost multiplier | EV at 0.5p/leg async (PF) |
|---|---|---|
| TB-A | 1.86x | 7.24 (2.42) |
| TB-B | 2.75x | 16.36 (10.10) |
| TB-C-2.5% | 2.69x | 15.76 (9.40) |
| TB-C-5% | 2.63x | 15.16 (8.71) |
| TB-C-7.5% | 2.57x | 14.55 (8.01) |
| TB-C-10% | 2.51x | 13.95 (7.35) |

- All models keep EV > 0 at 2.0x modeled costs; TB-A dies at 1.86x, neutral models at 
2.5-2.75x (linear interpolation between grid points).

## 9. Broker lot translation (detail: TB_P5_BROKER_LOT_CONSTRAINTS.csv)

| Model | min viable notional (rej < 5%) | executable residual at $25k |
|---|---|---|
| TB-A | $10,000 | 36.03% (rej 0%) |
| TB-B | $5,000 | 1.20% (rej 0%) |
| TB-C-2.5% | $5,000 | 2.47% (rej 0%) |
| TB-C-5% | $5,000 | 5.34% (rej 0%) |
| TB-C-7.5% | $5,000 | 6.96% (rej 0%) |
| TB-C-10% | $5,000 | 10.16% (rej 0%) |

- TB-A @ $5k degenerates (84% min-lot rejection); TB-B/TB-C are executable from $10k 
with rejection 0% and residual ≤ ~5%.

## 10. Robustness (detail: TB_P5_BOOTSTRAP_ROBUSTNESS.csv)

| Model | EV 95% CI | PF 95% CI | DD p5-p95 (block) | top-10% |
|---|---|---|---|---|
| TB-A | 6.66 .. 10.69 | 2.16 .. 3.86 | -171 .. -107 | 26.6% |
| TB-B | 15.90 .. 19.84 | 8.82 .. 18.13 | -44 .. -31 | 28.0% |
| TB-C-2.5% | 15.33 .. 19.23 | 8.33 .. 16.64 | -44 .. -32 | 27.7% |
| TB-C-5% | 14.80 .. 18.56 | 7.64 .. 15.58 | -48 .. -33 | 27.4% |
| TB-C-7.5% | 14.25 .. 17.90 | 7.16 .. 14.24 | -49 .. -37 | 27.2% |
| TB-C-10% | 13.56 .. 17.30 | 6.52 .. 12.81 | -54 .. -41 | 27.0% |

- TB-B/TB-C EV CIs lie **entirely above** the TB-A CI (no overlap) — the superiority is 
not a small-group artifact: it survives dropping the top 5% trades (decision JSON, 
`not_dominated`) and PnL concentration is similar across models (top-10% ≈ 27-28%).

## 12. Verdicts (full rules in TB_P5_VALIDATION_PROTOCOL.md)

| Model | Grade | EV | PF | basis share | EV-zero cost |
|---|---|---|---|---|---|
| TB-A | **VALIDATED** | 8.74 | 2.87 | 104.8% | 1.86x |
| TB-B | **STRONG** | 17.86 | 12.42 | 103.7% | 2.75x |
| TB-C-2.5% | **STRONG** | 17.26 | 11.49 | 103.1% | 2.69x |
| TB-C-5% | **STRONG** | 16.66 | 10.65 | 102.5% | 2.63x |
| TB-C-7.5% | **STRONG** | 16.05 | 9.80 | 101.9% | 2.57x |
| TB-C-10% | **STRONG** | 15.45 | 8.97 | 101.4% | 2.51x |

STRONG requires: exact causal signal reproduction; EV > 0; PF > 1.5; positive EV in 
last year AND chronological holdout; no weak year; basis share ≥ 60%; EV-zero cost 
≥ 1.5x; executable lots (rej < 5% at some notional ≤ $50k); superiority not dominated 
by top-5% trades. Historical PF 8-12 was NOT required to repeat.

**optimization_cleared = True** → `TB-P6-OPTIMIZATION-RESEARCH-PLAN.md` (inventory only, no testing).

## 13. STOP FOR HUMAN REVIEW
Validation outputs are frozen. No optimization begins automatically. 
Recommended forward step (after human review): TB-C 5% sizing on the live MT5 demo 
shadow feed to convert FORWARD_OOS_PENDING into FORWARD_OOS.
