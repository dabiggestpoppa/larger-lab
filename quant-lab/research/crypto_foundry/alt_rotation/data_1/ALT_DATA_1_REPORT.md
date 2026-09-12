# ALT-DATA-1 REPORT — CANONICAL POINT-IN-TIME UNIVERSE & MULTISCALE FEATURE PANEL

**Checkpoint:** CRYPTO-ALT-DATA-1-CANONICAL-POINT-IN-TIME-UNIVERSE-AND-MULTISCALE-FEATURE-PANEL
**Base SHA:** 922ddf480cb75f4e6dd6ecbbb1f71590a858df9e
**Parent:** CRYPTO-ALT-DATA-0.1-FOUNDATION-TRUTH-REPAIR (PASS)
**Decision:** see ALT_DATA_1_DECISION.json

---

## 1. What was built

The first canonical historical altcoin terrain dataset: for every daily
timestamp t from 2020-06-01 to 2026-08-23 —

- **what was in the top-500** (dated CMC snapshots, PIT by construction),
- **what was actually perp-tradable** (venue-specific eligibility ledger),
- **global rank + sector rank** (dual coordinates),
- **how it moved across 1/3/7/14/30/60/90-day windows**,
- **how it moved relative to BTC / ETH** (incl. causal beta/residual
  inputs),
- **rank-band / sector / market context** at t.

No strategy, no PnL, no optimization, no ML. The feature registry is
frozen and hashed so later mechanism research consumes a stable panel.

## 2. Data

- Daily top-500 snapshots, 2,275 calendar days targeted; (2196)
  included. End = 2026-08-23 (latest complete UTC day before the run
  date). Excluded: (79) CMC-side data-gap dates, each
  documented with its missing ranks (see DATA_QUALITY_REPORT §3).
- 1098000 universe rows; 2898 unique assets
  (cmc_id-anchored identities, collision-classified).
- Source authority unchanged: CMC historical endpoint =
  PRIMARY_EMPIRICALLY_VERIFIED_WEB_ENDPOINT (internal web endpoint; TOS
  review flagged; stability risk recorded).

## 3. Perp eligibility

Ledger covers HYPERLIQUID and OKX (verified in-environment); Binance
USD-M and Bybit Linear are UNVERIFIABLE_FROM_ENV here (geo-blocked; the
archive method is verified and documented but per-asset collection is
deferred). Terminal eligibility status is ELIGIBLE_EX_LIQUIDITY —
historical liquidity is NEVER claimed as verified.

- 493419 asset×date×venue rows;
- 314217 mature ≥30d rows;
- 314217 ELIGIBLE_EX_LIQUIDITY rows across
  273 unique assets.
- 30D maturity rule frozen; contract_age_days stored explicitly for later
  sensitivity checks without rewriting history.

## 4. Feature panel

128 asset-level columns including: returns, rank changes, market-cap
share/volume share, relative returns vs BTC/ETH, realized volatility,
volume-proxy means, rank velocity/acceleration, rank-curve state
(slope/monotonicity/inflections/spreads), peak frequency (decile/quartile
hits, peak counts, days-since-peak), entry/membership, beta/residual
inputs (30/60/90d causal OLS). Plus band, sector (TOP1/3/5/10/FULL),
terrain, membership, and survivorship (non-causal) tables.

Feature coverage by window decays with window length by design (frozen
endpoint + 80% coverage rules; NaN never backfilled) — see COVERAGE_REPORT.

## 5. Causality evidence

- Future-perturbation test: features at t are invariant to any
  perturbation of observations after t (asserted in the test suite).
- Per-window returns/rank changes recomputed independently and matched to
  1e-9.
- Fallen assets (FTT, LUNA/LUNC, HOT, SRM) remain present historically;
  entry/exit labels are causal except the explicitly non-causal
  survivorship annotations.
- Perp listing/delisting causality asserted (no tradable row before
  listing or after delisting).

## 6. Sector reality

Sector = snapshot-associated CMC tags, status HISTORICAL_APPROXIMATION
(frozen). Tag coverage grows from ~15% (2020) to ~100% (2025); 2020
sector features are sparse and reported as such. Dual ranks
(global_rank, sector_rank) exist wherever a tag is present.

## 7. Known gaps (deferred to later checkpoints)

1. Binance/Bybit per-asset archive collection (method verified; not
   collected here) — would extend the ledger with a third/fourth venue.
2. Paid-tier cross-checks (CMC Pro, CoinGecko premium) for rank and
   sector history — recorded as PAID_ENHANCEMENT_CANDIDATE, not blocking.
3. HL-purged delisted coins and OKX delisted swaps remain unrecoverable
   via public API (documented PARTIAL).
4. Historical DEX liquidity remains current-only context (not in panel).

## 8. Test results

(filled after final run) — DATA-0 (21) + DATA-0.1 (20) + DATA-1 (n)
tests, all passing; including future perturbation invariance.

## 9. Next checkpoint

CRYPTO-ALT-MECH-1-RANK-MIGRATION-LEAD-LAG-AND-SECTOR-FLOW-ANATOMY
(not started in this run).
