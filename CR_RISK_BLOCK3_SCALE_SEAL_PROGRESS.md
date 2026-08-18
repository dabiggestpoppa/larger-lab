# CR-RISK-BLOCK-III-SCALE-SEAL — Progress

**Checkpoint:** CR-RISK-BLOCK-III-SCALE-SEAL
**Base:** `a58f84833b920175f88a5e5c6c127a12bd5cdafe` (frontier, ACCEPTED)
**Status:** ✅ COMPLETE — PASS, committed and pushed

## What this checkpoint did

Froze the scientifically-supported STATIC SCALE OPERATING REGION from the
completed Block-III frontier. Pure **synthesis** — no new optimization, no
new Monte Carlo. Every review table is a deterministic pure function of the
frozen frontier artifacts (SHA-256 locked in
`CR_RISK_BLOCK3_SCALE_SEAL_INPUT_HASHES.json`).

## Sealed operating bands

| region | scale band | evidence |
|---|---|---|
| CONSERVATIVE | 0.25–0.50 | ROBUST_LOW_SCALE (P(DD≥10) ≈ 0) |
| **ROBUST CORE** | **0.75–1.00** | ROBUST_GROWTH_REGION, below knee |
| AGGRESSIVE | 1.50–2.00 | AGGRESSIVE_FRAGILE (tail accelerates) |
| STRESS ONLY | 3.00 | stress / never promoted |

## Key results

- **Knee band:** [1.00, 1.50] — modal over 53 frozen knee cells; robust core
  sits at-or-below the knee start → knee_seal_pass = true.
- **Adjacent-scale seal:** no tail acceleration inside 0.75→1.00 (0 cells);
  boundary 1.00→1.50 accelerates for every operating cell under the relative
  rule (block+episode agree) → adjacent_scale_seal_pass = true. Absolute
  acceleration threshold trips at 1.50→2.00.
- **Allocation:** A1_70_30 has the best tail efficiency (10.0 vs 8.84 A0 vs
  7.31 A2). Moving 70/30→A-only adds only +2.3pp median CAGR for +4.4pp
  P(DD≥10) → A2 (100/0 A) is a concentration reference, diagnostic-only.
  Allowed: A0_50_50, A1_70_30.
- **Heat:** H1-1.00-REJ retained as operating reference — paired evidence
  (common random numbers): median DD −1.5pp, P(H1 DD < H0) = 0.80, growth
  cost −0.2pp. H1-1.50/2.00 buy no protection; H1-3.00 never binds. H0
  documented sufficient.
- **Edge retention:** 100%/75%/50% survive in the band (block+episode);
  25% = recorded ALPHA-LOSS BOUNDARY (not required to survive).
- **Robust core risk contract:** median CAGR 0.48–0.70, p95 DD 4.7–8.3%,
  P(DD≥10) ≤ 0.72%, P(DD≥15) = 0, P(ruin) = 0, 0 dependency-sensitive cells.
- **Preferred research default** (NOT production sizing): A1_70_30 /
  H1-1.00-REJ / f=1.00.

## Authorizations (all locked FALSE)

Kelly, DD-adaptive sizing, production scale, deployment, MT5.

## Files

- `research/capital_routing/risk/block3_scale_seal/` — 13 artifacts
  (protocol, input hashes, 5 review CSVs + transitions, robust core,
  region definition, risk contract, report, decision)
- `src/capital_routing/capital_scale_seal.py` — seal engine
- `scripts/run_risk_block3_scale_seal.py` — deterministic runner
- `tests/test_risk_block3_scale_seal.py` — 16 tests

## Verification

- Seal tests: 16/16 pass
- Risk suite (R1–R6, Block1–3, frontieer): 128/128 pass
- Determinism: byte-identical re-run (SHA-256 of all seal artifacts)
- Phase2 `tests.fixtures` ModuleNotFoundError is pre-existing and unrelated
  (data-normalization fixtures not present in this checkout)

## Next

CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING — NOT started (awaiting
human review per the checkpoint contract).
