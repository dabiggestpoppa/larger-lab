# Triangular Basket Strategy — Progress & Research Log

> **Last Updated:** 2026-08-15
> **Strategy:** Triangular Basis Mean Reversion — GBP/AUD/NZD (GBPNZD = GBPAUD × AUDNZD)
> **Canonical engine:** `quant-lab/engines/triangular_basis_engine.py` (frozen at commit `2435d04e`)
> **Live architecture:** TB-LIVE-ARCH-01 (`683ba901`) — 4-layer isolation, magic `31082026`
> **Current phase:** TB-P6-ENTRY-ANATOMY-01 ✅ COMPLETE — `artifacts/triangular_basis/research/TB_P6_ENTRY_ANATOMY_REPORT.md` (base `7868a67d`)

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
| **TB-P5-NEUTRAL-BASIS-VALIDATION-01 (validation)** | ✅ **COMPLETE** | **TB-B + all TB-C variants STRONG; optimization cleared; no weak year; FORWARD_OOS_PENDING** |
| **TB-P6-ENTRY-ANATOMY-01 (entry research)** | ✅ **COMPLETE** | **z=3.0–3.5 stable plateau: +5 pips EV uplift, holdout-consistent, cost-robust >3x; 15 A/B candidates; p7 cleared** |

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

## TB-P5-NEUTRAL-BASIS-VALIDATION-01 ✅ COMPLETE (2026-08-15)

Validation-only phase (base `303abcdae`). No optimization, no signal changes, no ML/Kelly,
no new instruments, no hedge overlay. All outputs reproducible:
`python quant-lab/engines/tb_p5_validate.py` + `python quant-lab/engines/tb_p5_tests.py`
(deterministic, seed 42). Protocol: `TB_P5_VALIDATION_PROTOCOL.md`.

### 1. Causal signal re-simulation — EXACT
Frozen signal (z-200 rolling, London 3–12 EST, z≥2.5 / exit z→0, stop z=6, costs 10.2 pips)
recomputed causally from raw bars reproduces the canonical log **405/405, 0 mismatches**
(entry/exit times, direction, result, z, sizes, PnL to 1e-9).

### 2. Causal weight audit — ALL CLEAR
TB-B/TB-C weights are pure entry-time functions (entry closes, entry ATR, frozen seal rates).
Tested for future-bar / exit-info / full-sample / future-vol / future-rate / realized-PnL
leakage. Conversion-rate stress (f=1, GBP±10%/AUD∓10%/NZD±10%): max |ΔEV| ≤ 10.7%,
max Δ median residual ≤ 0.02 pp — rate leakage cannot explain the improvement.

### 3. Chronological robustness — neutral sizing wins everywhere
- **Expanding prefixes:** TB-B EV > TB-A EV at **all 16** quarter prefixes.
- **Chronological holdout** (last 94 trades, exit ≥ 2025-07-01): TB-A EV 6.30 / PF 2.14;
  TB-B EV **13.46** / PF 6.44; TB-C-5% EV 12.34 / PF 5.64.
- **Year-by-year:** no weak year for any model (PF > 1 and EV > 0 in all of 2022–2026);
  TB-B/TB-C beat TB-A every single year.

### 4. Headline model comparison (405 trades, same signals)
| Model | EV/trade | PF | WR | MaxDD | Sharpe | residual |
|---|---|---|---|---|---|---|
| TB-A (control) | 8.74 | 2.87 | 70.6% | −133.0 | 6.93 | 34.8% |
| TB-B (exact neutral) | **17.86** | 12.42 | 85.9% | **−35.4** | **14.74** | 0.02% |
| TB-C ε=2.5% | 17.26 | 11.49 | 85.4% | −36.7 | 14.49 | 2.5% |
| TB-C ε=5% | 16.66 | 10.65 | 85.2% | −39.9 | 14.21 | 5.0% |
| TB-C ε=7.5% | 16.05 | 9.80 | 84.4% | −43.4 | 13.90 | 7.5% |
| TB-C ε=10% | 15.45 | 8.97 | 83.5% | −47.0 | 13.53 | 10.0% |

AlphaMultiplier 177–204%, DD reduction 65–73%. AlphaRetention ≥ 177% at every ε ≤ 10%.

### 5. Basis-edge reconfirmed — basis reversion is the PnL source for ALL models
Basis share of gross PnL: TB-A 104.8%, TB-B 103.7%, TB-C 101.4–103.1%. Identity asserted
to 1e-9 per trade. Neutral sizing increases basis capture and cuts rotation drag (rotation
PnL −367 → −147 pips). No single-currency attribution attempted (unidentifiable).

### 6. Cost & execution stress — survives realistic costs
EV-zero cost multiplier: TB-A 1.86x, TB-B **2.75x**, TB-C 2.51–2.69x. All models keep
EV > 0 at 2.0x costs. Per-leg async slippage 0.5 pips: TB-B EV still 16.36 (PF 10.10).

### 7. Broker lot translation — executable
TB-B/TB-C executable at ≥ $10k with 0% rejection and residual ≤ ~5% at $25k (TB-B 1.2%).
TB-A @ $5k degenerates (84% min-lot rejection) — the neutral geometry is *more* executable.

### 8. Robustness — not a small-group artifact
Bootstrap (2000×, seed 42): TB-A EV CI 6.66–10.69 vs TB-B EV CI **15.90–19.84** — no overlap.
Superiority survives dropping top-5% trades; top-10% concentration ~27–28% for all models.

### 9. FORWARD_OOS — PENDING (honest verdict)
Research cutoff 2026-05-29 19:50. Post-cutoff `*_M5_fetched.csv` files are a **different
price source** (mean diff ~0.003 ≈ 30 pips vs canonical) and the only same-source extension
is single-leg AUDNZD — rejected by the data audit. No forward results are mixed into the
historical sample. Shadow collection on the live MT5 demo feed is prepared.

### 10. Verdicts (protocol: TB_P5_VALIDATION_PROTOCOL.md)
**TB-A: VALIDATED** (control). **TB-B: STRONG.** **TB-C 2.5/5/7.5/10%: STRONG.**
`optimization_cleared = true` → `TB-P6-OPTIMIZATION-RESEARCH-PLAN.md` (inventory only;
16 candidate dimensions reserved for human review — no testing).

**STOP FOR HUMAN REVIEW.**

---

## Decision Gate (from verify-04A)

**Acceptance test — exists ε with residual ≤ 10% AND alpha retention ≥ 70%?**
**✅ PASSES at every ε ≤ 10% (retention 177–197%).**

**Actions:**
1. ❌ **Do NOT build the 4th/6th-leg hedge overlay** — not needed; solve inside the 3 legs.
2. ✅ Adopt **TB-C neutral sizing (ε = 5% operating point)** — replace canonical inverse-ATR
   weights in `_enter_trade`; keep all entry/exit rules (London-only, z≥2.5, stop z=6, hard
   exit 12:00 EST, min 120 min).
3. ✅ Re-run the backtest + parity suite with TB-C weights before demo — validated in TB-P5.

---

## TB-P6-ENTRY-ANATOMY-01 ✅ COMPLETE (2026-08-15)

Entry RESEARCH ONLY (base `7868a67d`; TB-P5 accepted, `optimization_cleared = true`).
Frozen elements untouched (exit z=0, stop z=6, session, costs 10.2 pips, causal weights).
Protocol `TB_P6_PROTOCOL.md` pre-registered the split/grid/metrics/gates BEFORE any outcome.
Reproduce: `python quant-lab/engines/tb_p6_anatomy.py --phase all` +
`python quant-lab/engines/tb_p6_tests.py` (411 deterministic checks, exit 0 = pass).
Full report: `TB_P6_ENTRY_ANATOMY_REPORT.md`; machine decision: `TB_P6_DECISION.json`.

### 1. Entry-threshold surface (P6.1) — z grid 1.50–4.00, 11 points × 6 models
Higher entry z monotonically improves EV for every model; frequency falls off fast:

| z | N | coverage | EV TB-B | EV TB-C-5% | PF TB-B | WR | maxDD | MFE | MAE |
|---|---|---|---|---|---|---|---|---|---|
| 2.50 (frozen) | 405 | 100% | 17.86 | 16.65 | 12.42 | 85.9% | −35 | 17.7 | −15.7 |
| 2.75 | 272 | 67% | 20.07 | 18.76 | 13.87 | 85.3% | −50 | 19.1 | −15.4 |
| **3.00** | 194 | 48% | **23.07** | 21.61 | 18.05 | 88.1% | −35 | 21.7 | −14.9 |
| **3.25** | 134 | 33% | 22.94 | 21.53 | 17.64 | 88.1% | −49 | 22.0 | −13.1 |
| **3.50** | 79 | 20% | 24.73 | 22.97 | 13.92 | 87.3% | −49 | 24.7 | −13.3 |
| 3.75 | 49 | 12% | 27.74 | 25.92 | 14.35 | 89.8% | −40 | 27.9 | −12.3 |
| 4.00 | 32 | 8% | 34.44 | 32.04 | 18.85 | 93.8% | −35 | 32.0 | −11.7 |

- **Plateau (pre-registered rule): z ≈ 2.75–3.50** for all neutral models (spread ≤ 15% of
  run max, run max ≥ baseline, chronologically stable).
- z < 2.5 is strictly worse (more noise trades): every 1.50–2.25 cell grades **D**.
- MFE rises with threshold; MAE shrinks — entry quality improves structurally.

### 2. Further-extension anatomy (P6.2) — measurement only
- Path classes (405 baseline trades): IMMEDIATE_CONVERGENCE 33% (EV 26.2), SHALLOW_CONVERGED
  27% (EV 26.0), SHALLOW_FAILED 17% (EV 1.3), IMMEDIATE_PERSISTED 12% (EV 9.0), DEEP_FAILED
  5% (EV −6.0), DEEP_CONVERGED 6% (EV 20.0).
- **Hypothesis A (extension → higher expectancy): NOT supported.** **B: inverted-U present**
  (peak EV at moderate extension, collapse at extreme). **C: extreme extension (|z| ≥ 4.5)
  = regime break** — P(conv) 29% vs 67% below 4.5, EV 8.9 vs 18.0.
- **Hazard:** P(convergence) decays monotonically with time-since-signal at every |z| level
  (e.g. at |z| 2.5–3.0: 67% within 15 min → 38% at 2–4 h). Persistence is a failure signal.
- No entry/exit rule derived — this is the measurement layer for P7 (human-gated).

### 3. Session clock (P6.3)
- Best half-hour: 60–90 min after London open (EV TB-B 33.9, N=20). Dead zones:
  half-hours 12–13 (~4.5–5.5h in) and quarter-hour 26.
- **Early London (40% of trades): EV 24.7, failure 10%. Mid (47%): EV 15.1, failure 42%.
  Late (12%): EV 5.8, failure 84%** — late-session entries are materially worse.

### 4. Dislocation-quality fingerprint (P6.4) — causal, descriptive
Per-trade causal features (velocity, acceleration, duration above threshold, touches,
time-since-prior-signal, 5-min basis vol, leg ATRs, expanding vol tercile, leg contribution
dominance, session/weekday). Future-bar invariance tested (any perturbation of bars after
entry leaves the fingerprint bit-identical). Leg-dominance conditioning shows little
separation; vol/velocity terciles are descriptive inputs for P7.

### 5. Cost stress + execution translation (P6.4)
- **Break-even cost multiplier rises with threshold:** z=2.5 → 2.75x (TB-B); **z ≥ 3.0 keeps
  EV > 0 even at 3.0x costs** (BE > 3.0x) for every neutral model.
- **Lot translation @ z=3.0:** TB-B executable from $10k (residual 5.2%, rejection 0%),
  $25k → 1.2% residual, PnL ratio ≈ 1.00. TB-C-5% similar (5.0% at $25k).

### 6. Candidates (seal) — 50 tested, 15 A/B
1×A (TB-C-10% @ 3.00), 14×B (all neutral models @ 3.00/3.25/3.50), 10×C (3.75/4.00 —
exploratory, coverage 8–12%), 25×D (z < 2.75 — worse than baseline, CI excludes 0 the wrong
way). Every A/B candidate: EV uplift +4.7…+6.9 pips with bootstrap CI excluding 0 (q < 0.02,
BH-FDR per model family), same-direction DISCOVERY/CONFIRMATION/HOLDOUT blocks, P5 date
holdout agrees, plateau member, basis share 99–104% (attribution preserved), survives
top-5% removal, break-even ≥ 2.9x.

### 7. Decision
**`p7_convergence_optimization_cleared = true`** — a broad, stable, holdout-supported entry
improvement exists (raise the z entry threshold into the 3.0–3.5 plateau; 48%→20% coverage).
Original z=2.5 entry is retained until a human authorizes P7 testing of the candidate rules.

**STOP FOR HUMAN REVIEW.** No exit/hold/stop/pyramiding/risk work begins.

---

## Next Phase — TB-P7 (proposed, gated on human review of P6)

1. **Human review** `TB_P6_ENTRY_ANATOMY_REPORT.md` + `TB_P6_DECISION.json` +
   `P6_CANDIDATE_ENTRY_RULES.json` (candidates A/B: z=3.0–3.5 entry for TB-B / TB-C-5%).
2. Candidate entry change (if approved) re-runs the full TB-P5 validation sections 1–12
   before adoption; one dimension at a time.
3. 04B demo forward test with neutral sizing remains the path to convert
   FORWARD_OOS_PENDING → FORWARD_OOS (the live basis-z distribution is the missing evidence).
4. Convergence/exit optimization (P7) uses the P6.2 hazard + path-class measurements only
   after the entry decision is settled.

---

## Related Files

| File | Purpose |
|---|---|
| `quant-lab/engines/verify_tb_04a.py` | 04A independent verification script (reproduce everything) |
| `quant-lab/engines/tb_verify_out/` | 04A outputs (comparison, per-trade, summary) |
| `quant-lab/engines/tb_p5_validate.py` | **P5 validation suite** (reproduces all TB_P5_* outputs) |
| `quant-lab/engines/tb_p5_tests.py` | **P5 deterministic tests** (60+ checks, exit 0 = pass) |
| `quant-lab/engines/tb_p6_anatomy.py` | **P6 entry-anatomy suite** (`--phase p61/p62/p63/p64/seal/all`) |
| `quant-lab/engines/tb_p6_tests.py` | **P6 deterministic tests** (411 checks, exit 0 = pass) |
| `artifacts/triangular_basis/research/TB_RESEARCH_VERIFY_04A_REPORT.md` | 04A audit report |
| `artifacts/triangular_basis/research/TB_P5_VALIDATION_PROTOCOL.md` | P5 frozen protocol (metrics, verdict rules) |
| `artifacts/triangular_basis/research/TB_P5_VALIDATION_REPORT.md` | P5 full validation report |
| `artifacts/triangular_basis/research/TB_P5_DECISION.json` | Machine verdicts + rate sensitivity |
| `artifacts/triangular_basis/research/TB_P5_*.csv` | P5 tables (comparison, walk-forward, yearly, attribution, anatomy, cost/exec stress, bootstrap, lots, forward OOS, weights) |
| `artifacts/triangular_basis/research/TB_P6_PROTOCOL.md` | **P6 pre-registered protocol (split, grid, plateau rule, gates)** |
| `artifacts/triangular_basis/research/TB_P6_ENTRY_ANATOMY_REPORT.md` | **P6 full report** |
| `artifacts/triangular_basis/research/TB_P6_DECISION.json` | **P6 decision (`p7_convergence_optimization_cleared`)** |
| `artifacts/triangular_basis/research/P6_ENTRY_THRESHOLD_SURFACE.csv` | 11 z × 6 models full metrics |
| `artifacts/triangular_basis/research/P6_ENTRY_THRESHOLD_PLATEAUS.md` | Plateau/cliff/saturation analysis |
| `artifacts/triangular_basis/research/P6_FURTHER_EXTENSION_PATHS.csv` | Per-trade post-entry |z| paths + classes |
| `artifacts/triangular_basis/research/P6_EXTENSION_CONVERGENCE_SURFACE.csv` | P(conv)/E[PnL] by max-|z| + z×t hazard |
| `artifacts/triangular_basis/research/P6_EXTENSION_ANATOMY_REPORT.md` | Hypotheses A–D + path classes |
| `artifacts/triangular_basis/research/P6_TIME_OF_DAY_STUDY.csv` / `P6_SESSION_CLOCK_REPORT.md` | Session timing |
| `artifacts/triangular_basis/research/P6_DISLOCATION_FINGERPRINT.csv` | Causal entry fingerprint |
| `artifacts/triangular_basis/research/P6_QUALITY_CONDITIONALS.csv` | Quality bins (velocity/persistence/vol/dominance/session/weekday) |
| `artifacts/triangular_basis/research/P6_COST_STRESS.csv` | 1.0–3.0x costs, break-even per z × model |
| `artifacts/triangular_basis/research/P6_EXECUTION_TRANSLATION.csv` | Lot translation TB-B / TB-C-5% × $5k–$100k |
| `artifacts/triangular_basis/research/P6_CANDIDATE_ENTRY_RULES.json` | 50 candidates with gates/CIs/q/block EVs |
| `artifacts/triangular_basis/research/TB-P6-OPTIMIZATION-RESEARCH-PLAN.md` | Optimization dimension inventory (human review only) |
| `artifacts/triangular_basis/live/bar_parity.csv` | 265,809 synchronized M5 bars (source data) |
| `artifacts/triangular_basis/live/canonical_trade_log.csv` | The real 405 trades (source data) |
| `artifacts/triangular_basis/live/execution/neutrality_gate.json` | Broker seal Gate-K artifact |
| `progress/triangular-basis-research-progress.md` | Prior 04A research-phase log (04A claims) |
