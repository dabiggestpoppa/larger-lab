# ALT-DATA-1 DATA QUALITY REPORT

**Checkpoint:** CRYPTO-ALT-DATA-1-CANONICAL-POINT-IN-TIME-UNIVERSE-AND-MULTISCALE-FEATURE-PANEL
**Companion:** ALT_DATA_1_COVERAGE_REPORT.md, ALT_DATA_1_PROVENANCE_MANIFEST.json

This report records every quality check applied to the canonical panel and
every known limitation. It does not claim quality the data does not have.

---

## 1. Checks performed (all passing)

| check | result |
|---|---|
| duplicate rank within a date | none (500 unique ranks per included date) |
| missing rank within a date | none in included dates; excluded dates documented (§3) |
| rank outside 1..500 | none |
| duplicate asset (cmc_id) within a date | none |
| missing market cap | 0 rows in included dates |
| negative price / negative volume | 0 rows |
| market-cap share sums == 1 per date | max deviation < 1e-6 |
| stable identity id uniqueness | identity map has unique internal_asset_id / cmc_id |
| ticker-reuse classification | every reused symbol classified (see identity map) |
| contract pre-listing eligibility | no tradable row before listing_timestamp |
| contract post-delisting eligibility | no tradable row after delisting_timestamp |
| 30-day maturity consistency | mature_30d_at_t == tradable AND age >= 30 (all rows) |
| rolling-window leakage | future-perturbation test: all features before cutoff t are
  byte-identical when observations after t are altered |
| per-window feature causality | return_w, rank_change_w, relative returns
  recomputed from endpoints and matched to 1e-9 |
| sector-rank consistency | sector ranks are exactly 1..n within each
  (date, sector) group |
| sector participation hierarchy | TOP1 ⊆ TOP3 ⊆ TOP5 ⊆ TOP10 ⊆ FULL_SECTOR
  (member counts and mcap shares monotone) |
| feature-registry determinism | registry hash is reproducible from
  FEATURE_DEFINITIONS.json |
| provenance hashes | every raw body sha256 matches its meta sidecar;
  every committed artifact hash matches the manifest |
| non-causal annotations isolated | exited_top500 / days_until_exit exist
  ONLY in ALT_DATA_1_SURVIVORSHIP.parquet, never in the causal feature panel |

## 2. Point-in-time causality

Every row at timestamp t uses only observations with date ≤ t:

- **Rank / mcap / volume** come from the dated CMC snapshot at t
  (lastUpdated tT23:59:59Z).
- **Returns** use endpoint prices at t and t−w; both endpoints must be
  present in the panel, else NaN (INSUFFICIENT_HISTORY).
- **Realized volatility / beta / volume-proxy** use time-windowed rolling
  statistics over (t−w, t] with an 80% calendar-day coverage floor.
- **Peak frequency / rank-curve** features use only history up to t.
- **No backfill**: NaN stays NaN; partial windows are never labeled with
  their full window name.

## 3. Documented exclusions (CMC-side data gaps)

The historical-listing endpoint returns incomplete snapshots for a small
number of dates. Each was re-probed with narrow pagination windows; the
missing ranks are genuinely absent from the source snapshot. These dates
are EXCLUDED from the panel and recorded here:

| date | rows returned | missing ranks (1-500) |
|---|---|---|
| 22 source gaps + 57 pagination-rank-filter gaps, total 79 excluded dates (see build_summary.json for full list) | | |

Exclusion code: `CMC_side_data_gap_YYYYMMDD`. The raw truncated snapshot
bodies and their meta sidecars are preserved under `probes/raw/` so the
gap is auditable, not hidden. All other dates have exactly 500 rows.

## 4. Known limitations (truthful, not hidden)

1. **Rank universe is top-500 only.** An asset ranked 501-1000 on a given
   day is absent that day. Absence is treated as "not top-500" in
   entry/exit, decile hits, and consecutive-day features (frozen rule).
2. **CMC rank/mcap monotonicity is imperfect.** The provider's own rank
   field may disagree with mcap ordering by a small margin (Spearman
   0.88–0.99 observed in DATA-0). `rank` is authoritative; `market_cap_share`
   uses raw mcap.
3. **Historical liquidity is NOT verified.** `liquidity_proxy_status` is
   VOLUME_PROXY_ONLY (HL) or PARTIAL (OKX); `historical_liquidity_verified`
   is FALSE for every row. No L2 depth / executable spread exists in this
   panel. See ALT_DATA_0_1_HISTORICAL_LIQUIDITY_PATH.md.
4. **Perp delisting history is partial.**
   - OKX: delisted swaps are silently omitted from the public instrument
     list; delisting timestamps are NOT available → delisting history
     PARTIAL.
   - Hyperliquid: coins purged from the meta universe are unrecoverable via
     the public API → the ledger under-covers old delisted HL contracts.
   - Binance / Bybit: live APIs are geo-blocked from this environment
     (451 / 403). The archive method (data.binance.vision, 2020-01+,
     incl. delisted contracts and funding) is verified but per-asset
     archive collection is NOT part of DATA-1 → both venues are
     UNVERIFIABLE_FROM_ENV here.
5. **Sector mapping is HISTORICAL_APPROXIMATION.** Sectors come from
   snapshot-associated CMC tags (multi-tag, drifting taxonomy; sparse in
   2020: ~15% tagged, ~100% by 2025). Never promoted to
   POINT_IN_TIME_VERIFIED. Untagged assets are UNMAPPED.
6. **Stablecoin flag is tag/symbol-driven.** Includes governance-adjacent
   tokens tagged as stablecoin-family by CMC (e.g., TRIBE via Fei).
   Used only for context metrics (stablecoin_mcap_share), never for
   universe exclusion.
7. **Snapshot timing is end-of-UTC-day.** All dates use 23:59:59Z
   semantics; no intraday mixing.
8. **ATR is NOT supported.** Daily snapshot resolution has no high/low;
   `atr_14d_true` is all NaN; `volatility_normalized_move_14d` is the
   descriptive substitute.
9. **Beta/residual are simple causal OLS.** 30/60/90d lookbacks with
   min-observation and 80% coverage gates; NaN otherwise. No shrinkage,
   no ML.
10. **Identity joins for dead assets are limited.** CG/CP joins use the
    current coin lists; dead/renamed assets may have LOW or empty matches
    (recorded per row as cg_join/cp_join + collision_class). No
    auto-resolution of UNKNOWN_COLLISION.

## 5. Source authority (unchanged from DATA-0.1)

CMC historical ranking = `PRIMARY_EMPIRICALLY_VERIFIED_WEB_ENDPOINT`
(internal web data-api; NOT an official documented API; no API key;
STABILITY_RISK = INTERNAL_ENDPOINT; TOS review required for long-term
operation). The endpoint was probed for every date in the panel during
collection; schema changes are visible in the preserved meta sidecars.
