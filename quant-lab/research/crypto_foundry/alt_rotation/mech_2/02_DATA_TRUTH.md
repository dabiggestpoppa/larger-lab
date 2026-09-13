# MECH-2 DATA TRUTH

## Inputs (all canonical DATA-1.1, point-in-time)

| Input | Source | Role |
|---|---|---|
| PIT universe + V2 asset features | DATA-1 (`ALT_DATA_1_V2_*` frozen) | asset-level returns, rank, rank velocity, mcap share, volatility |
| Rank-band features | DATA-1 (`rank_band_features`) | band-level median return, rank velocity, breadth, mcap share, volume share |
| Sector membership + features | DATA-1 | sector assignment (PIT), sector-daily aggregates |
| Market terrain | DATA-1 | BTC/ETH/alt returns, dominance, dispersion, stablecoin share |
| DefiLlama global flow | DATA-1.1 | stablecoin supply changes, DEX volume changes (30d) |
| DefiLlama chain flow | DATA-1.1 | per-chain TVL (aggregate proxy) |
| Chain mapping | DATA-1.1 | CMC platform strings → canonical chain |

## Truth lock (verified at run start)

- PIT universe: **1,098,000 rows / 2,898 assets / 2,196 included dates / 79 excluded source-gap dates** — unchanged from DATA-1.
- V2 feature hash recomputed: `0d666e74c0cf76adf6e6e6f2a6c47b1f52116f070fd1376c83274e6b077703ba` — matches frozen registry (task-brief copy dropped two `e6` characters; no effect on inputs).
- Registry-definition hash: `ea7eca86…9ef` — matches.
- DefiLlama global + chain flow files present.

Full check record: `02_DATA_TRUTH.json` (all checks `True`).

## Point-in-time rules honored

- **Universe**: rank/membership at date *t* only; no modern membership applied backward. Delisted and dead assets remain in the universe through their historical life.
- **No V1 consumption**: V1 relative-return / beta / residual columns were never read. Relative returns used in MECH-2 are computed locally from canonical V2 fields.
- **AVAILABLE_NEXT_DAY**: DefiLlama flow values are shifted +1 day (reported on day *d* become knowable on day *d+1*) before any lead/lag use. The shift is applied **per chain** for chain flow and globally for global flow.
- **Date-bucket normalization**: DefiLlama flow files are midnight-stamped; asset/terrain frames are end-of-day-stamped. All flow frames are normalized to the end-of-day bucket in `load_inputs` before any merge. (MECH-1's flow sections silently all-NaN'd on this mismatch; MECH-2 normalizes once, centrally.)
- **Chain-name bridge**: CMC platform strings (`SOL`, `ETH`, `ARB`, …) are mapped to DefiLlama display names (`Solana`, `Ethereum`, …) via a fixed alias table in `load_inputs`. Fixed engineering bridge, not an outcome choice.
- **No forward-fill** of structurally missing flow data. Gaps are respected; windows with insufficient data produce NaN and are dropped.
- **Meteora**: pool-level liquidity history is NOT usable. Only DefiLlama aggregate chain TVL is used (protocol-level proxy). Pool-level analysis remains deferred (unchanged from MECH-1).

## Events defined causally

- Rank-migration events (workstream C) use band membership at *t-1* → *t* as the event; all precursor features are measured over windows **ending before** the migration date. No outcome-defined starts.
- Sector episodes (workstream D) reuse MECH-1's episode detector (contiguous acceleration runs from point-in-time data), restarted here with leader identified at episode start.
- Failure patterns (workstream F) condition on state at *t* only; forward outcomes are measured from *t*.

## Integrity tests covering these claims

`tests/test_alt_mech_2.py` (31 tests) asserts: input hash matches, PIT row counts, no V1 field consumption, AVAILABLE_NEXT_DAY per-chain shifting, no future columns in any artifact, FDR reproducibility, deterministic seeds, and structural absence of PnL/alpha/weights.
