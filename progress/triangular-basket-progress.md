# Triangular Basket Strategy — Progress & Research Log

> **Last Updated:** 2026-08-15
> **Strategy:** Triangular Basis Mean Reversion — GBP/AUD/NZD (GBPNZD = GBPAUD × AUDNZD)
> **Canonical engine:** `quant-lab/engines/triangular_basis_engine.py` (frozen at commit `2435d04e`)
> **Live architecture:** TB-LIVE-ARCH-01 (`683ba901`) — 4-layer isolation, magic `31082026`
> **Current phase:** TB-RESEARCH-VERIFY-04A ✅ COMPLETE — see `artifacts/triangular_basis/research/TB_RESEARCH_VERIFY_04A_REPORT.md`

---

## Status Summary

| Phase | Status | Result |
|---|---|---|
| Canonical backtest (405 trades, z≥2.5, London-only, 200-bar) | ✅ | +3,540 pips, 70.6% WR, PF 2.87 |
| TB-LIVE-ARCH-01 strategy isolation | ✅ | 4-layer, magic unique, canonical frozen |
| TB-LIVE-PARITY-02 replay parity | ✅ | 265,809 bars / 405 trades, zero divergence |
| TB-LIVE-EXEC-03 + SEAL-03B real-broker execution | ✅ | Gates D/E/F/I/J/L/M pass; **Gate K FAIL** (median residual 34.9% > 10%) |
| TB-LIVE-SHADOW-04A live shadow + neutrality research | ⚠️ | Gate K failure real, but the "405-trade decomposition" tables were **synthetic** (see below) |
| **TB-RESEARCH-VERIFY-04A (independent audit)** | ✅ **COMPLETE** | **Neutral sizing preserves AND improves alpha; hedge overlay NOT needed** |

---

## TB-RESEARCH-VERIFY-04A — Key Insights (2026-08-15)

An independent audit of the 04A claims was performed from committed artifacts only
(`bar_parity.csv`, `canonical_trade_log.csv`, `neutrality_gate.json`). Everything is
reproducible: `python quant-lab/engines/verify_tb_04a.py`.

### 1. Data integrity — the 405 trades reproduce exactly
Re-simulating every trade from the raw bars matches the canonical log to **8.8e-12 pips**
(PnL) and **4.2e-16** (basis). All downstream numbers are grounded in the real trades.

### 2. The headline: EV_TB-C / EV_TB-A = 197% (TB-B = 204%)
Constrained three-leg sizing that caps currency residual at ε ≤ 10% **keeps and improves**
expectancy while cutting residual from 34.8% → ≤2.5%:

| Metric | TB-A | TB-B (neutral) | TB-C ε=5% |
|---|---|---|---|
| EV/trade (pips) | 8.74 | **17.86** | 16.66 |
| Win rate | 70.6% | **85.9%** | 85.2% |
| PF | 2.87 | 12.42 | 10.65 |
| Max DD (pips) | −133.0 | **−35.4** | −39.9 |
| Sharpe | 6.93 | 14.74 | 14.21 |
| Median residual | 34.84% | 0.02% | 5.00% |

### 3. Factor attribution — 15/25/20/30/10 RETRACTED
- The claimed attribution percentages appear **nowhere in committed code** (the attribution
  scripts listed in the 04A progress doc were never committed).
- Exact per-trade decomposition (`PnL_t = dir·[w_GN·Δb + (w_GA−w_GN)·r_GA + (w_AN−w_GN)·r_AN] + ε`)
  shows **basis reversion = 104.8% of gross PnL** (stable 100–121% every year 2022–2026);
  rotation (GBP/AUD/NZD relative strength) ≈ **−5%**.
- A single-currency GBP/AUD/NZD split is **unidentifiable** from three crosses without USD
  pairs. The "85% directional" hypothesis is **not supported** — this is a basis-reversion
  strategy whose inverse-ATR sizing adds a *negative* rotation drag.

### 4. Hedge-cost numbers $17.45/$10.47/$8.78 and $131.13 — RETRACTED
`17.45 = 34.9% × $5,000 / 100` — a percent-vs-fraction units error (true residual at $5k is
**$1,745**). The "$131.13 total cost" literally reuses the $25k-row hedge values; **no cost
formula exists in code**. Honest hedge cost at $25k ≈ **$1.00/basket**.

### 5. Shadow-phase 405-trade decomposition was SYNTHETIC
`triangular_basis_shadow_implementation._load_historical_trades()` hardcodes
`residual_pct = 34.9` and alternates `pnl = +100 / −50` — it never loaded the real trade log
(comment: "For now, create sample data based on the issue description"). Its residual-bucket
tables (0% win rate) are meaningless and should not be cited.

### 6. N=3 live Gate-K observations = plumbing validation only
Median = P95 = 34.90% at N=3 is degenerate. Structural evidence is the 405-basket translation
against the real broker (median 34.93%, max 72.47% at $25k), reproduced at model level here.

---

## Decision Gate (from verify-04A)

**Acceptance test — exists ε with residual ≤ 10% AND alpha retention ≥ 70%?**
**✅ PASSES at every ε ≤ 10% (retention 177–197%).**

**Actions:**
1. ❌ **Do NOT build the 4th/6th-leg hedge overlay** — not needed; solve inside the 3 legs.
2. ✅ Adopt **TB-C neutral sizing (ε = 5% operating point)** — replace canonical inverse-ATR
   weights in `_enter_trade`; keep all entry/exit rules (London-only, z≥2.5, stop z=6, hard
   exit 12:00 EST, min 120 min).
3. ✅ Re-run the backtest + parity suite with TB-C weights before demo.

---

## Next Phase — TB-RESEARCH-VERIFY-04B (proposed)

1. Re-backtest canonical engine with **TB-C ε=5% neutral sizing** (only `_enter_trade` sizes
   change; signals untouched).
2. Re-run TB-LIVE-PARITY-02 replay parity with the neutral weights.
3. Demo forward test (2–4 weeks) with real fill logging; verify the live basis z-distribution
   matches the backtest data (the ±0.003 basis dislocation is the entire edge).
4. Hedge overlay only as a fallback if forward basis reversion under-delivers.

---

## Related Files

| File | Purpose |
|---|---|
| `quant-lab/engines/verify_tb_04a.py` | Independent verification script (reproduce everything) |
| `quant-lab/engines/tb_verify_out/tb_abc_comparison.csv` | TB-A/B/C + ε-sweep metrics |
| `quant-lab/engines/tb_verify_out/tb_verify_per_trade.csv` | 405-row per-trade decomposition |
| `quant-lab/engines/tb_verify_out/tb_verify_summary.json` | Machine-readable summary |
| `artifacts/triangular_basis/research/TB_RESEARCH_VERIFY_04A_REPORT.md` | Full audit report |
| `artifacts/triangular_basis/live/bar_parity.csv` | 265,809 synchronized M5 bars (source data) |
| `artifacts/triangular_basis/live/canonical_trade_log.csv` | The real 405 trades (source data) |
| `artifacts/triangular_basis/live/execution/neutrality_gate.json` | Broker seal Gate-K artifact |
| `progress/triangular-basis-research-progress.md` | Prior 04A research-phase log (04A claims) |
