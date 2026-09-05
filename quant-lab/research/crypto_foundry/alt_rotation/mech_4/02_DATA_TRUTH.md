# ALT_MECH_4 — DATA TRUTH & PIT INTEGRITY

**Checkpoint:** CRYPTO-ALT-MECH-4 (Pivot Release Gates, Stall Release, Path Memory &
Propagation Depth). **Role:** AGENT 1 — MAIN FIELD CARTOGRAPHER. Terrain research only.

## Truth lock (re-verified at run start on DATA-1.1)

| Check | Result |
|---|---|
| PIT universe rows == 1,098,000 | PASS |
| unique assets == 2,898 | PASS |
| included dates == 2,196 | PASS |
| V2 feature-hash identity valid | PASS (canonical recomputed hash matches DATA-1.1 frozen registry) |
| registry-definition hash valid | PASS |
| excluded source-gap dates == 79 | PASS |
| DefiLlama flow files present | PASS |

`02_DATA_TRUTH.json` records `all_pass = true` and the per-check booleans.

## Reused infrastructure

MECH-4 reuses, unchanged, the canonical pipelines:
- MECH-1: `load_inputs()` (allow-listed DATA-1.1), `verify_truth_lock()`,
  `assign_routing_state_frame()` (the daily PIT routing-state series),
  `subperiod_of()`, ROUTING_STATES.
- MECH-2: `build_factors()`, `assign_states()`, `_cond_xcorr()`, `_resid_series()`.
- MECH-3: `build_daily()`, `chain_frame()`, `_precursor_frame()` (trailing, shifted so
  strictly before t), `_destination_state()` (first state held >= 5 days).

Point-in-time discipline:
- All precursor observables are trailing-window means shifted one day before the
  event date; no forward-fill of structurally missing data.
- DefiLlama flow features are AVAILABLE_NEXT_DAY-shifted before use (MECH-1 bridge).
- No row-offset benchmark leakage, no modern taxonomy projected backward.
- No silent synthetic cap-flow values.

## Canonical event reconciliation (03)

The re-derived PIT event ledger was compared to MECH-3's canonical
`09_CONCENTRATION_ENTRY_EVENTS.parquet` / `10_CONCENTRATION_EXIT_EVENTS.parquet`:

| Event | MECH-3 canonical | This recount | Full match |
|---|---|---|---|
| ENTRY | 126 | 126 | 126/126 (100%) |
| EXIT | 125 | 125 | 125/125 (100%) |

Destination taxonomy is reproduced exactly: 52 REENTRY, 44 MIXED, 18
BROAD_RISK_EXPANSION, 4 LARGE_ALT, 4 MID_CAP, 1 ETH_BROADENING, 1 CAPITAL_EXIT,
1 STABLECOIN_PARKING (total = 125). Alt family = 9/125.

## PIT-safe ledger (04)

`04_RELEASE_EVENT_LEDGER.parquet`: event_id, entry/exit dates, episode duration,
route into concentration, prior states, state age, first destination, days to
destination, subperiod, regime flags at exit (BTC_UP/DOWN, VOL_HIGH/LOW,
CONC_RISING/FALLING, BREADTH_EXPANDING/CONTRACTING, ETH_STRONG/WEAK, RISK_ON/OFF),
observables at exit (PIT), availability masks, staged-propagation pattern.

No forward-looking field is used to *define* any observation at t. Forward
state-transition labels are recorded only as the outcome being studied.

## Source-gap & missing-data contract

- Source-gap dates (79) remain excluded as in DATA-1.
- ~2-4% of the 10-feature state matrix is missing; fixed median-imputation per
  feature (preregistered) — no drop of events, no result-selected imputation.
- Per-chain P1 data restricted to the top-12 chains by coverage (>= 120 days).