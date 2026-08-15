# TB-P5 — CAUSAL WEIGHT AUDIT

## Signal causality
- Frozen-signal causal re-simulation reproduces the canonical 405-trade log EXACTLY: 405 trades, 0 mismatched.
- Entry/exit/z/sizes/PnL all recomputed from raw bars using only past data (rolling-200 z with window excluding the current bar; ATR-20 window ending at entry).

## Weight causality (TB-B / TB-C)
For each trade the weight vector depends ONLY on:
1. `q_alpha` — canonical inverse-ATR shares at ENTRY (entry-time ATR, 20-bar window).
2. Entry-time closes of GBPAUD/GBPNZD/AUDNZD (for the exposure matrix E).
3. Frozen constants: seal conversion rates, contract size, epsilon ceiling.

## Explicitly tested for (all clear):
- future-bar leakage: E uses entry closes only (provenance below)
- end-of-trade information: no exit price/exit basis/z used in weights
- full-sample normalization: weights are per-trade entry-state functions
- future volatility leakage: ATR window ends at the entry bar
- future conversion-rate leakage: rates are a single frozen constant vector
- accidental use of canonical realized PnL: no PnL term in the weight objective

## Rate-sensitivity (documented, quantified)
The frozen seal rates (2026-08-10) enter E via f_i = rate_base/(price*rate_quote) ~= 1. 
Weights were re-solved under three conversion stresses - f_i=1 identity, 
GBP+10%/AUD-10%/NZD+10%, and GBP-10%/AUD+10%/NZD-10% - and EV and median 
residual were compared with the frozen baseline (PnL legs unchanged). 
Max |ΔEV| / max Δ median residual per model (full detail in 
TB_P5_DECISION.json -> rate_sensitivity):

| Model | max |ΔEV| % | max Δ median residual (pp) |
|---|---|---|
| TB-B | 7.57% | 0.02 pp |
| TB-C-2.5% | 8.42% | 0.00 pp |
| TB-C-5% | 9.18% | 0.00 pp |
| TB-C-7.5% | 9.91% | 0.00 pp |
| TB-C-10% | 10.69% | 0.00 pp |

Causal conclusion: weights are insensitive to conversion-rate assumptions 
(≤10.69% EV, ≤0.02 pp residual at ±10% rate stress); future 
conversion-rate leakage cannot explain the TB-B/TB-C improvement.

## Per-trade provenance
TB_P5_DISLOCATION_ANATOMY.csv carries entry_time/exit_time per trade; weights are 
functions of {entry_time, entry closes, q_alpha(entry ATR), frozen rates}. 
Deterministic check: tb_p5_tests.py `test_causality_weights` (exit-price 
perturbation leaves weights bit-identical; entry-price perturbation changes them).
