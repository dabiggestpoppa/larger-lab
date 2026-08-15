# TB-RESEARCH-VERIFY-04A — Independent Verification Report

**Status:** ✅ VERIFICATION COMPLETE — 04A claims audited against committed artifacts
**Inputs (all committed on `origin/master`):**
`artifacts/triangular_basis/live/bar_parity.csv` (265,809 synced M5 bars),
`artifacts/triangular_basis/live/canonical_trade_log.csv` (real 405 trades),
`artifacts/triangular_basis/live/execution/neutrality_gate.json`,
`artifacts/triangular_basis/live/execution/canonical_weight_translation_405.csv`,
`artifacts/triangular_basis/live/execution/minimum_viable_notional.json`.

**Reproduction script:** `quant-lab/engines/verify_tb_04a.py`
**Outputs:** `quant-lab/engines/tb_verify_out/` (`tb_abc_comparison.csv`, `tb_verify_per_trade.csv`, `tb_verify_summary.json`, this report)

## How to reproduce (everything below is script-generated, nothing hand-typed)

```bash
# 1. get the committed inputs (they are plain git blobs on origin/master, not LFS):
#    artifacts/triangular_basis/live/bar_parity.csv
#    artifacts/triangular_basis/live/canonical_trade_log.csv
#    artifacts/triangular_basis/live/execution/neutrality_gate.json
# 2. run:
python quant-lab/engines/verify_tb_04a.py
# requires: python 3.10+, numpy, pandas, scipy (trust-constr)
```

The script:
1. Loads bars + the 405-trade log and **re-derives every trade's PnL and basis from the raw
   prices** — it hard-fails (`assert`) if the recomputation does not match the log to 1e-6 pips
   (measured: max diff 8.8e-12 pips, basis 4.2e-16).
2. Builds the USD-normalized currency-exposure matrix `E` for each trade using the **same
   formula as the broker seal** (`triangular_execution_contract.compute_currency_exposure` at
   model level: base side `rate_base/(price·rate_quote)`, quote side 1, per-leg sides from
   trade direction, real seal rates GBP 1.34852 / AUD 0.70583 / NZD 0.58844). The resulting
   TB-A median residual (34.84%) reproduces the broker seal's 34.93% (`neutrality_gate.json`).
3. Solves TB-B (`min ‖q−q_α‖² s.t. E·q=0, Σq=1, q≥0`) and TB-C (`min ‖q−q_α‖² s.t.
   |E·q|∞≤ε, Σq=1, q≥0`) with `scipy.optimize.minimize(method="trust-constr")` +
   `LinearConstraint` + exact quadratic Hessian, and **hard-guards that the ε cap is actually
   satisfied** (raises instead of emitting a violating row). All baskets keep `Σ|s|=3`
   (canonical gross leverage) so the constant 10.2-pips/trade cost model is comparable.
4. Computes the exact trade-level attribution
   `PnL_t = dir·[w_GN·Δb + (w_GA−w_GN)·r_GA + (w_AN−w_GN)·r_AN] + ε_t` (identity verified to
   1e-14 pips), yearly shares, and OLS regressions with SE / 95% CI / R².
5. Emits `tb_verify_per_trade.csv` (405 rows: per-trade PnL, attribution, residuals, MFE/MAE),
   `tb_abc_comparison.csv` (TB-A/B/C + ε-sweep metrics), `tb_verify_summary.json`.

---

## 0. Data integrity (required before any claim)

The 405 trade windows were recomputed from the raw bars:

| Check | Result |
|---|---|
| Bars used | 265,809 M5 snapshots (2022-09-13 → 2026-05-29) |
| Trades re-simulated | 405/405, entry & exit timestamps all found |
| Basis vs log (`max abs diff`) | **4.2e-16** — exact |
| `pnl_gross_pips` vs log (`max abs diff`) | **8.8e-12 pips** — exact |
| Attribution identity `basis+rotGA+rotAN+eps = gross` | 1.4e-14 max deviation |

**The canonical backtest numbers reproduce exactly** (405 trades, +3,539.8 pips net,
70.6% WR, PF 2.87, MaxDD −133.0 pips) — identical to the values claimed in commit
`2435d04e`. Everything below is computed on the **real** trade log and bars, not the
synthetic shadow tables.

> ⚠️ The shadow phase's "historical 405-trade decomposition" (`triangular_basis_shadow_implementation.py`
> `_load_historical_trades`) was built from **synthetic** trades — hardcoded `residual_pct = 34.9`,
> alternating `pnl_pips = 100.0 if i%2==0 else -50.0`, comment: *"This would load from actual
> historical trade records — For now, create sample data based on the issue description."*
> Its residual-bucket table (all 405 trades at "0% win rate") is therefore meaningless and
> should be retracted.

---

## 1. The headline answer: EV_TB-C / EV_TB-A

**EV_TB-C (ε = 2.5%) / EV_TB-A = 197% — and EV_TB-B / EV_TB-A = 204%.**

Constrained three-leg sizing **keeps, and in-sample improves, the full expectancy** while
cutting median currency residual from **34.8% → ≤ 2.5%**. The Pareto frontier is not a
trade-off in this sample — tightening neutrality *increases* EV (see §3).

---

## 2. TB-A / TB-B / TB-C — full 405-trade comparison

| Metric | TB-A (canonical) | TB-B (exact neutral) | TB-C ε=2.5% | TB-C ε=5% | TB-C ε=10% | TB-C ε=20% |
|---|---|---|---|---|---|---|
| Trades | 405 | 405 | 405 | 405 | 405 | 405 |
| Win rate | 70.6% | **85.9%** | 85.4% | 85.2% | 83.5% | 80.2% |
| Net PnL (pips) | 3,539.8 | **7,234.0** | 6,989.1 | 6,745.4 | 6,257.7 | 5,332.9 |
| Expectancy / trade | 8.74 | **17.86** | 17.26 | 16.66 | 15.45 | 13.17 |
| Profit factor | 2.87 | **12.42** | 11.49 | 10.65 | 8.97 | 6.32 |
| Avg win | 18.98 | 22.61 | 22.12 | 21.58 | 20.84 | 19.49 |
| Avg loss | −15.88 | −11.12 | −11.29 | −11.65 | −11.71 | −12.52 |
| Payoff ratio | 1.20 | 2.03 | 1.96 | 1.85 | 1.78 | 1.56 |
| Max DD (pips) | −132.96 | **−35.43** | −36.73 | −39.86 | −46.97 | −61.85 |
| Sharpe (ann.) | 6.93 | **14.74** | 14.49 | 14.21 | 13.53 | 11.79 |
| Sortino (ann.) | 10.26 | **36.25** | 34.57 | 33.02 | 29.66 | 23.59 |
| MFE (avg) | 24.10 | 31.04 | 30.44 | 29.86 | 28.74 | 26.72 |
| MAE (avg) | −11.79 | −9.13 | −9.16 | −9.21 | −9.32 | −9.80 |
| Total R (net/avg\|loss\|) | 223 | 651 | 619 | 579 | 534 | 426 |
| Costs (pips/trade, constant) | 10.2 | 10.2 | 10.2 | 10.2 | 10.2 | 10.2 |
| **Residual (median)** | **34.84%** | **0.02%** | 2.50% | 5.00% | 10.00% | 20.00% |
| Residual p95 / max | 57.2 / 78.6 | — | 2.50 / 2.50 | 5.00 / 5.00 | 10.00 / 10.00 | 20.00 / 20.00 |
| **Alpha retention (EV/EV_A)** | 100% | **204%** | 197% | 191% | 177% | 151% |

**Notes on method**
- All variants re-size the **same 405 realized entry/exit windows** (same signals, same leg
  price moves) with gross leverage held constant (`Σ|s| = 3`, same as canonical), so costs are
  identical (10.2 pips/trade) and every row is directly comparable.
- TB-B = projection of canonical weights onto the exact currency-exposure null space
  (`E·q = 0`, residual ≈ 0.02%). TB-C = `min ‖q − q_α‖² s.t. |E·q|∞ ≤ ε`, same
  exposure matrix `E` as the broker seal pipeline (USD-normalized, real rates
  GBP 1.34852 / AUD 0.70583 / NZD 0.58844, contract 100k).
- **Residual validation:** model-level median residual of TB-A = 34.84% vs. the real-broker
  seal's 34.93% (`neutrality_gate.json`) — the residual machinery reproduces the broker
  economics to ~0.1pp. The 34.9% Gate-K failure is **real and reproduced**.
- Sharpe/Sortino: trade PnL aggregated by exit date, annualized with √252. MFE/MAE:
  intra-trade basket path on M5 closes.

**Interpretation.** Neutralizing the residual does not just "preserve" alpha — it removes a
rotation component that *drags* PnL. The inverse-ATR weighting tilts the basket into the two
rotation factors (r_GA, r_AN); those factors contributed **negative** PnL over the sample
(§4). The pure basis basket (TB-B) is the cleanest expression of the edge.

---

## 3. Epsilon sweep — Pareto frontier

```
ε (%)     median resid (%)   EV/trade   PF     Sharpe   MaxDD    AlphaRetention
2.5       2.50               17.26      11.49  14.49    −36.7    197%
5.0       5.00               16.66      10.65  14.21    −39.9    191%
7.5       7.50               16.05       9.80  13.90    −43.4    184%
10.0      10.00              15.45       8.97  13.53    −47.0    177%
15.0      15.00              14.30       7.53  12.72    −56.4    164%
20.0      20.00              13.17       6.32  11.79    −61.9    151%
TB-A      34.84               8.74       2.87   6.93   −133.0    100%
TB-B      0.02               17.86      12.42  14.74    −35.4    204%
```

The frontier is **monotonic**: in this sample, less residual ⇒ more EV. There is no ε at
which constrained sizing fails the reviewer's acceptance test.

---

## 4. Factor attribution — the 15/25/20/30/10 claim is **retracted**

**Method (exact, per trade, no heuristics).** With `r_i = ln(P_x/P_e)`,
`w_i = s_i·P_e,i/pip` and `Δb = b_x − b_e = r_GA − r_GN + r_AN`:

```
PnL_t = dir·[ w_GN·Δb  +  (w_GA − w_GN)·r_GA  +  (w_AN − w_GN)·r_AN ] + ε_t
        └─ PnL_basis ─┘   └─── PnL_rotGA ───┘   └─── PnL_rotAN ───┘
```

| Component | Σ (pips) | Share of gross PnL | Share of \|PnL\| (risk) |
|---|---|---|---|
| **Basis reversion** (Δb) | **+8,036.7** | **104.8%** | 76.0% |
| Rotation GA (GBP vs AUD) | −277.9 | −3.6% | 7.3% |
| Rotation AN (AUD vs NZD) | −89.1 | −1.2% | 16.6% |
| 2nd-order residual ε | +1.19 | 0.015% | — |

Yearly stability (share of gross PnL): 2022: 99.8% basis · 2023: 101.7% · 2024: 104.2% ·
2025: 107.4% · 2026: 120.8% — the basis dominance is **stable every year**, and rotation is
slightly negative every year.

Regressions (PnL_net, n=405):

| Model | R² | Notes |
|---|---|---|
| `~ 1` | 0.0000 | baseline |
| `~ 1 + Δb` | 0.0002 | constant-slope unfit: weight w_GN varies per trade |
| `~ 1 + r_GA + r_AN` | 0.0024 | rotation factors: β = 175 ± 496, 922 ± 932 (both **not** significant) |
| `~ 1 + r_GA + r_AN + Δb` | 0.0050 | all slopes insignificant (SE ≈ slope) |
| `~ 1 + pnl_basis` | **0.7921** | β = 1.116 ± 0.029 (**significant**); remaining spread = costs + rotation noise |

**Verdict on the 04A attribution**
1. The numbers **15 / 25 / 20 / 30 / 10 appear nowhere in committed code or artifacts**
   (`git grep` across `origin/master` finds no attribution implementation; the scripts listed
   in the progress doc — `triangular_basis_factor_attribution.py`, `..._neutrality_research.py`,
   `..._triangle_study.py`, `..._shadow_comparison.py` — were **never committed**).
2. The claim is **contradicted by the exact decomposition**: ~105% of gross PnL is basis
   reversion, not 15%; rotation/relative-strength is ≈ −5%, not 85%.
3. A GBP/AUD/NZD single-currency split is **not identifiable from three crosses alone**
   (no USD pairs in the data): only the two relative-strength factors `g−a = r_GA` and
   `a−n = r_AN` are observable, plus the basis. The 25/20/30 single-currency shares are
   therefore not merely unproven — they are **unidentified** without GBPUSD/AUDUSD/NZDUSD.
4. **Retract the 15/25/20/30/10 percentages** and replace with the table above.

> Implication for the "two strategies" hypothesis: the realized 405-trade PnL shows **one**
> strategy — basis reversion — with the rotation component as noise/drag. The "TRIANGLE-
> ROTATION" model is not supported by this sample. The 34.8% residual is an *unwanted
> byproduct* of inverse-ATR sizing, and removing it (TB-B/C) *improves* EV.

---

## 5. Hedge-cost unit reconciliation — $17.45/$10.47/$8.78 vs $131.13 **fails**

| Item | Claimed | Audit |
|---|---|---|
| Hedge notional @ $5k | 17.45 + 10.47 + 8.78 = **$36.70** | `17.45 = 34.9% × $5,000 / 100` — the % value was divided by 100 (fraction/percent units error). True max-residual USD at $5k = **$1,745** |
| Hedge notional @ $25k | 87.25 / 52.35 / 43.88 | same `/100` error; true residual = **$8,725** |
| "Spread cost" $87.25 | — | equals the **$25k GBP hedge value** — a cost was fabricated by reusing a hedge figure |
| "Commission" $43.88 | — | equals the **$25k NZD hedge value** |
| **Total $131.13** | "per $5k basket" | mixes the **$25k** row values; **no cost formula exists in code** (`git grep 131` → only the plan doc); economic nonsense vs $36.70 of stated hedge notional |

**Correct economics:** a real 3-leg USD hedge overlay on the max-residual currency at $25k
needs ~0.087 lots GBPUSD (≈ $8,710), costing ≈ **$1.00 per basket round trip**
(spread 0.8 pips × $10/pip/lot + commission $3.5/100k) — two orders of magnitude below the
claimed $131.13. The claim is **retracted**; unit inconsistency confirmed.

---

## 6. N=3 live Gate-K observations — labeled correctly

The 3 live shadow intents are **execution/plumbing validation only** (median = P95 = 34.90%
is trivially degenerate at N=3). The structural evidence is the **405-basket translation**
(`canonical_weight_translation_405.csv`, `neutrality_gate.json`, `minimum_viable_notional.json`)
computed against the real broker (rates, contracts) — and the model-level reproduction here
(median 34.84%, p95 57.2%, max 78.6%). No live distributional statistics are inferred from N=3.

---

## 7. Reviewer gate decision

**Acceptance test: exists ε with residual ≤ 10% AND alpha retention ≥ 70%?**

**✅ PASSES — at every ε ≤ 10% (retention 177–197%).** The acceptance test is met *inside the
original three legs*.

- **Do NOT build the 4th/6th-leg hedge overlay.** TB-C at ε = 2.5–10% already delivers
  residual ≤ 10% with retention ≥ 177%, plus lower DD and higher Sharpe than TB-A.
- **Adopt constrained (neutral) sizing** as the production weight scheme: TB-C ε = 5% is a
  reasonable operating point (residual 5% cap, EV 16.66, PF 10.6, MaxDD −40) — robust to
  small lot-rounding distortion while capturing most of the neutral-basket gain.
- **Replace the canonical inverse-ATR sizing** (it dilutes the edge) — pending out-of-sample
  confirmation.

## 8. Caveats (read before acting)

1. **In-sample re-weighting.** TB-B/C re-size the *same 405 realized signals*. The
   improvement is a sizing counterfactual, not new signal evidence. The claim "neutral sizing
   preserves/improves alpha" needs a forward (paper/demo) confirmation before live capital.
2. **Basis magnitude is data-dependent.** The basis level wanders ±0.003 (≈30 pips) in the
   bar data; that dislocation is what the strategy trades. Whether live broker ticks present
   the same persistent dislocations is the key live-validation question (the shadow runtime
   observed 3 entry intents in 120 min — consistent with expected frequency — but did not
   measure the live basis z-distribution over many trades).
3. **Broker rounding.** Residuals here are model-level (continuous weights). Broker lot
   rounding shifts them slightly (34.84% model vs 34.93% broker median at $25k) and is the
   reason min-lot distortion (rejections at $500–$2,500) exists. TB-C ε should be chosen with
   a margin above the rounding floor (ε = 5% rather than 2.5%) unless larger notionals are used.
4. **Costs are constant per trade in the canonical model** (10.2 pips). Real slippage varies
   with liquidity; the forward test should log actual fills.

## 9. Recommended next phase

**TB-RESEARCH-VERIFY-04B (replaces TB-LIVE-SHADOW-04B "hedge overlay"):**
1. Re-backtest the canonical engine with **TB-C ε=5% neutral sizing** (change only the
   `_enter_trade` size calculation; keep London-only, z≥2.5, stop z=6, hard exit, min 120 min).
2. Re-run the parity suite (TB-LIVE-PARITY-02) with the neutral weights.
3. Forward test on the demo account with TB-C sizing + real fill logging (2–4 weeks).
4. Only if the forward basis reversion under-delivers should a hedge overlay be revisited.

---

*Generated by verify_tb_04a.py from committed origin/master artifacts. Report date:
2026-08-15. Audited code: origin/master @ 504aed9a (includes d4e3118d, f137be3a,
12423b8f, 099a6bba, c5e15f19, 683ba901, 2435d04e).*
