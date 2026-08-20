# SW-CTBT-T1.1 — Reference Parity and Gate Enforcement Repair

## Scope

Repair Step 1 of the Canonical TB Transfer Test **before** any Step 2 / 2025
confirmation economics are opened.

- NO 2025 confirmation economics.
- NO 2026 economics.
- NO Step 2 (requires explicit human authorization).
- NO optimization, NO new candidates, NO parameter search.

This checkpoint only repairs / re-executes T1 development evidence.

## Authoritative base

- Repair base commit: `be4ac2f2a105c886611ad9243b1e256ff3069ab9` (the T1 commit)
- Canonical truth source: `tb-forward-engine` branch
  (`canonical_trade_log.csv`, `strategy_freeze.json`, `tb_forward_config.py`,
  `triangular_basis_engine.py`, `triangular_basis_live.py`, `tb_audit_replay.py`).

## The four known T1 problems (repaired)

1. **Reference parity was not proven** (206/288 reported vs canonical 194/405).
   → Repaired by reconstructing the canonical lifecycle from first principles and
   verifying EXACT parity against the canonical 405-trade log.
2. **Cost contract changed** (16.2 pips assumed vs canonical 10.2 pips).
   → Repaired to the canonical frozen `strategy_freeze.json` contract (10.2 pips).
3. **EUR_GBP_USD marked qualified while NON_MONOTONIC**.
   → Repaired with a deterministic monotonicity classifier; NON_MONOTONIC cannot qualify.
4. **Year-stability rule waived**.
   → Repaired with a frozen deterministic interpretation (see below).
5. **Cost source recorded ASSUMED**.
   → Repaired with level-4 documented provider specs for every leg.

## Frozen canonical contract (reconstructed exactly)

| Component | Value |
|---|---|
| basis | `ln(GBPAUD) - ln(GBPNZD) + ln(AUDNZD)` |
| rolling z | 200-bar, population std (ddof=0), previous-bars-only (current excluded) |
| entry | strict `|z| > 2.5` (control) / `> 3.0` (primary) |
| direction | `z>0 -> SHORT`, `z<0 -> LONG` |
| exit (control) | SHORT `z<=0.0`, LONG `z>=0.0` (TP) |
| exit (primary) | SHORT `z<=-0.25`, LONG `z>=+0.25` (TP) |
| stop | SHORT `z>=+6.0`, LONG `z<=-6.0` (SL) |
| hard exit | est_hour >= 12 (TIMEOUT), checked FIRST |
| session | London 3–12 EST, fixed UTC-5 (no DST) |
| min runway | entry only if est_hour <= 10 (>= 120 min to hard exit) |
| lifecycle | max 1 concurrent basket; re-entry after close |
| cost | 10.2 pips round trip (spread 1.5+2.5+2.0 + commission 1.4×3) |

## Reference parity method

The lifecycle was reimplemented independently in
`run_t11_reference_parity.py` and compared field-by-field against
`canonical_trade_log.csv` (405 trades):

- entry/exit timestamp, direction, exit reason, entry/exit z,
  gross PnL, cost, net PnL, and all three leg sizes.

Result: **405/405 exact (max float diff 0.0); PRIMARY 194/194.**

## Challenger screen method

The verified lifecycle was applied to the four preregistered challengers over the
2020–2024 development window (`run_t11_screen.py`). Economics are measured in
unit-free **basis bps** (signed Δbasis × 1e4), directly comparable across triangles
with mixed pip conventions (e.g. JPY legs).

### M5 density gate (data integrity)

The `_fetched.csv` / `PRO` "M5" files are **daily (1 bar/day) before ~2022-08**,
then switch to true M5. Mixing daily bars into the 200-bar causal z would be a
data/microstructure invalidation, so every triangle is cut to the first calendar
day with >= 100 bars (true M5 density).

### Cost model

Basket round-trip cost (bps) = Σ_legs (spread + 1.4 commission) × pip_size / median_price × 1e4.

- Spread: canonical frozen values for reference legs (GBPAUD 1.5, GBPNZD 2.5,
  AUDNZD 2.0); a conservative floor of 1.5 pips for other legs (STRICTER than the
  documented OxSecurities MT5 spec).
- Commission: canonical 1.4 pips/leg.
- The gate is run against the conservative cost (fail-closed); the documented
  OxSecurities cost is reported separately as a sensitivity.

## Hard pass gate (all mandatory)

A: net EV > 0 · B: PF_net >= 1.20 · C: N >= 50 · D: edge/cost >= 1.50 ·
E: break-even multiple >= 1.50 · F: no year > 60% of net PnL ·
G: year stability (frozen) · H: monotonicity ∈ {STRONG, ACCEPTABLE} ·
I: no rollover/spread artifact · J: no data/microstructure invalidation.

### Frozen monotonicity classifier

- `delta_EV > 0 and delta_PF > 0 and delta_edge_cost_ratio > 0` → MONOTONIC_STRONG
- `delta_EV > 0 and delta_edge_cost_ratio > 0 and (delta_PF > 0 or ~0)` → MONOTONIC_ACCEPTABLE
- `delta_EV <= 0 and delta_edge_cost_ratio <= 0 and delta_p5 <= 0` → MECHANISM_COLLAPSE
- otherwise → NON_MONOTONIC (cannot qualify)

### Frozen year-stability (gate G)

At least 3 net-positive calendar years, counting every calendar year that contains
>= 1 completed event. Fewer than 3 calendar years in sample → INSUFFICIENT_DEVELOPMENT_DEPTH.
See DECISION `year_depth_caveat` for the partial-2022 note.
