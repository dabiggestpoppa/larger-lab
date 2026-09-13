# ALT-DATA-0.1 — Foundation Truth Repair — REPORT

**Checkpoint:** `CRYPTO-ALT-DATA-0.1-FOUNDATION-TRUTH-REPAIR`
**Branch:** `agent/crypto-quant-foundry`
**Base SHA (commit parent):** `e8e2a7abe952634696363ea94246a03dc8a627f8`
**Parent checkpoint:** `CRYPTO-ALT-DATA-0-POINT-IN-TIME-RANKING-AND-PERP-UNIVERSE-REALITY-AUDIT`
**Parent reported decision:** `PASS_ALT_POINT_IN_TIME_UNIVERSE_FOUNDATION`
**Human review verdict:** `PARTIAL_ALT_POINT_IN_TIME_UNIVERSE_FOUNDATION`
**Run date:** 2026-08-24 (UTC)
**Recomputed decision:** `PASS_ALT_POINT_IN_TIME_UNIVERSE_FOUNDATION`
(see `ALT_DATA_0_1_DECISION.json` — all eight repair criteria satisfied,
each backed by a persisted artifact and an automated test)

> Data reality only. No alpha, no PnL, no strategy work was performed in
> this checkpoint. No DATA-1 work started.

---

## 0. Scope

Bounded truth-repair pass on ALT-DATA-0 per the human review. The source
audit was NOT rerun; nine repairs were executed, each with a persisted
artifact and a regression test in
`data_0/tests/test_alt_data_0_1.py`.

## 1. Repair 1 — Rank-band coverage denominators (UNIQUE PIT assets)

**Problem observed by reviewer:** per-date band counts (40/60/100/200…)
were venue-multiplied instead of unique assets.

**Confirmed:** the committed DATA-0 coverage CSV counted asset×venue rows
(4× inflation for bands covered by 4 venue rows). Root cause: coverage was
aggregated over the eligibility prototype's asset×venue rows rather than
over the rank prototype's unique asset rows.

**Fix:** coverage recomputed from `ALT_DATA_0_POINT_IN_TIME_RANK_PROTOTYPE.csv`
keyed on unique `(historical_date, cmc_id)`. Per-date denominators are now
exactly 10/15/25/50/100/100/200; per-date band sums == 500; aggregate
(5 dates) == 50/75/125/250/500/500/1000. The CSV now carries
`asset_count_method = UNIQUE_PIT_ASSET`. Tests assert every band's unique
count per date and the 500-per-date sum.

Artifacts: `data_0/ALT_DATA_0_COVERAGE_BY_RANK_BAND.csv` (corrected),
`data_0_1/ALT_DATA_0_1_COVERAGE_RECONCILIATION.csv` (old vs new
denominators/numerators side by side).

## 2. Repair 2 — Coverage claims recomputed

The old prose claim ("top-100 bands ~65-80% perp-eligible") is superseded
by exact unique-asset percentages (section 4 of the DATA-0 report and the
reconciliation CSV):

| band | unique | any perp (HL∪OKX) | mature ≥30d | ELIGIBLE_EX_LIQUIDITY (HL) | OKX maturity-eligible |
|---|---|---|---|---|---|
| 1-10 | 50 | 45 (90.0%) | 44 (88.0%) | 39 (78.0%) | 44 (88.0%) |
| 11-25 | 75 | 60 (80.0%) | 54 (72.0%) | 47 (62.7%) | 53 (70.7%) |
| 26-50 | 125 | 104 (83.2%) | 93 (74.4%) | 74 (59.2%) | 78 (62.4%) |
| 51-100 | 250 | 189 (75.6%) | 169 (67.6%) | 135 (54.0%) | 145 (58.0%) |
| 101-200 | 500 | 298 (59.6%) | 268 (53.6%) | 152 (30.4%) | 249 (49.8%) |
| 201-300 | 500 | 89 (17.8%) | 72 (14.4%) | 40 (8.0%) | 58 (11.6%) |
| 301-500 | 1000 | 263 (26.3%) | 192 (19.2%) | 96 (9.6%) | 161 (16.1%) |

All report language updated in `data_0/ALT_DATA_0_REPORT.md` (section 4).

## 3. Repair 3 — Perp eligibility prototype regenerated (non-empty)

**Reviewer claim:** the committed
`ALT_DATA_0_PERP_ELIGIBILITY_PROTOTYPE.csv` is empty.

**Truth check:** the committed blob (commit `e8e2a7ab`) was in fact
non-empty — 1.9 MB, 10,001 lines, 10,000 data rows. The reviewer's
"empty" claim is factually wrong for the committed state. The file was
nevertheless regenerated to the **canonical 23-column schema** required by
the review (adding `listing_timestamp_authority`,
`delisting_timestamp_authority`, per-dimension data flags,
`liquidity_evidence_status`, and the four eligibility-dimension booleans).

- 10,000 rows (2,000 unique assets × 5 dates × 2 venues — HL + OKX;
  Binance/Bybit rows are `UNVERIFIABLE_FROM_ENV` and not materialized).
- No duplicate `(historical_date, cmc_id, venue, venue_instrument_id)`
  (test-asserted).
- Coverage across all 5 prototype dates (test-asserted).

## 4. Repair 4 — Liquidity truth separated

`FULLY_ELIGIBLE` is **removed**. The taxonomy is now:

- `CONTRACT_EXISTENCE_ELIGIBLE` — contract existed at t (list ≤ t < delist).
- `CONTRACT_MATURITY_ELIGIBLE` — existence + age ≥ 30d at t.
- `HISTORICAL_DATA_ELIGIBLE` — maturity + historical price/funding/volume
  data available at t.
- `HISTORICAL_LIQUIDITY_VERIFIED` — **never TRUE in DATA-0/0.1**; no venue
  has frozen-rule historical liquidity verification in the free stack.
- Terminal status: `ELIGIBLE_EX_LIQUIDITY` (contract+maturity+data
  eligible, liquidity unverified) or `CONTRACT_MATURITY_ELIGIBLE`
  (venue-level data retention partial, e.g. OKX).

Test: `FULLY_ELIGIBLE` cannot appear; `ELIGIBLE_EX_LIQUIDITY` rows must
carry `historical_liquidity_verified = FALSE`.

## 5. Repair 5 — Historical liquidity path (DATA-1 usable sources)

Full document: `ALT_DATA_0_1_HISTORICAL_LIQUIDITY_PATH.md`. Summary:

| venue | historical volume | depth | price | funding | OI | bid/ask | DEX liq |
|---|---|---|---|---|---|---|---|
| Binance archive | YES (klines volume) | 2020-01+ (monthly, delisted kept) | YES | YES (fundingRate files) | NO | NO | n/a |
| Hyperliquid | YES (candle volume post-listing; v=0 pre-listing filter) | 2023-05-12+ per coin | YES | YES (hourly, 232/232) | CURRENT_ONLY | NO | n/a |
| OKX | PARTIAL (retention-limited) | instrument-dependent | PARTIAL | PARTIAL (recent window) | CURRENT_ONLY | NO | n/a |
| Bybit | NO (403 from env) | — | NO | NO | NO | NO | n/a |
| DexPaprika | PARTIAL (30d window) | current | PARTIAL | n/a | n/a | n/a | CURRENT_ONLY |
| DexScreener | NO (unreachable) | — | — | — | — | — | — |

No L2 historical liquidity exists in the free stack; it is not invented.
DATA-1 may use Binance-archive and HL candle volume as liquidity **proxies**
under a preregistered frozen rule, with explicit
`HISTORICAL_LIQUIDITY_VERIFIED` never implied.

## 6. Repair 6 — CMC source authority corrected

CMC historical ranking uses an internal web data-api
(`data-api/v3/cryptocurrency/listings/historical`). It is no longer
classified alongside officially documented public APIs.

New authority label (registry + consensus matrix + report + decision):

```
class                    = PRIMARY_EMPIRICALLY_VERIFIED_WEB_ENDPOINT
official_documentation   = NO / UNVERIFIED
api_key_required         = NO
stability_risk           = INTERNAL_ENDPOINT
tos_review_required_for_long_term_operation = YES
```

This does not invalidate the empirical data evidence (8 dated snapshots,
500-deep, PIT-verified), but it stops infrastructure truth from
overstating source authority. Test asserts the label, the
`official_documentation ∈ {NO, UNVERIFIED}`, and the stability/TOS fields
in both registry and consensus matrix.

## 7. Repair 7 — Earliest verified history

The claim "any date supported" was **removed**. Three meaningfully older
dates were empirically tested via the same keyless CMC data-api:
**2022-06-01, 2021-06-01, 2020-06-01** — all returned 500 ranked rows with
PIT-consistent content (2020-06-01: BTC $10,167.27 / $186.99B, XRP #3,
BCH #5 — matches June 2020 reality; fallen coins BTS #111, XEM #32 at true
ranks).

- **EARLIEST VERIFIED = 2020-06-01**
- Deeper history: **UNVERIFIED** (not extrapolated).
- New probe files persisted with provenance meta (`probes/raw/`), hashed
  into the manifest (probe count 92 → 95).

## 8. Repair 8 — Identity collision audit

The "608 ticker-reuse flags" conflated distinct phenomena. Reclassified
all 949 identities into explicit classes
(`data_0_1/ALT_DATA_0_1_IDENTITY_COLLISION_AUDIT.csv`):

| class | count | meaning |
|---|---|---|
| TRUE_TICKER_REUSE | 22 | same symbol = genuinely different CMC assets (e.g. LUNA/DOGE collisions) |
| PROVIDER_SYMBOL_COLLISION | 450 | symbol matches multiple provider candidates; best name-join resolves the asset |
| UNKNOWN_COLLISION | 136 | must be manually resolved before DATA-1 joins |
| NO_COLLISION | 341 | unambiguous |

Venue-side aliases classified separately: 3 `MULTIPLIER_ALIAS`
(1000PEPE/SHIB/BONK perp naming — Binance archive verified) and 3
`VENUE_ALIAS` (HL legacy MATIC/RNDR/MKR == POL/RENDER/SKY renames).
Tests assert the classes are explicit and that TRUE_TICKER_REUSE is a
small subset (≤ PROVIDER_SYMBOL_COLLISION).

## 9. Repair 9 — Decision recomputed

Recomputed per the review's eight conditions (all satisfied — see
`ALT_DATA_0_1_DECISION.json`):

1. PIT historical ranking remains proven (8 empirically tested dates,
   2020-06-01 → 2026-08-20; no current-survivor dependence).
2. Unique-asset coverage recomputed correctly (test-verified sums).
3. Perp eligibility prototype non-empty, canonical schema (10,000 rows,
   no duplicates).
4. Maturity/tradability terminology corrected (`ELIGIBLE_EX_LIQUIDITY`;
   `FULLY_ELIGIBLE` removed).
5. Historical liquidity limitation explicitly separated (never
   `HISTORICAL_LIQUIDITY_VERIFIED`; path documented).
6. Source authority corrected (`PRIMARY_EMPIRICALLY_VERIFIED_WEB_ENDPOINT`).
7. Required artifacts complete (18 DATA-0 + 5 DATA-0.1 new/updated).
8. All repair tests pass (41 total: 21 original updated + 20 repair).

## 10. Test results

- Original DATA-0 suite (`test_alt_data_0.py`): 21 passed (4 updated to the
  canonical eligibility schema; the determinism test now rebuilds the
  legacy pipeline in a scratch copy so the live repaired artifacts are
  never rewritten by the test run).
- DATA-0.1 repair suite (`test_alt_data_0_1.py`): 20 passed (3
  parametrized date checks).
- Total: **41 passed, 0 failed** (run 2026-08-24; no network).

## 11. Blockers

**None blocking.** Residual limitations are unchanged and documented:
geo-blocked Binance/Bybit live APIs (archive path verified for Binance),
free-tier single-provider rank cross-check before 2025-08, HL purged
coins + OKX delisted swaps unrecoverable via public API, historical
liquidity (perp/DEX) current-only in the free stack.

## 12. Next checkpoint

`CRYPTO-ALT-DATA-1-CANONICAL-POINT-IN-TIME-UNIVERSE-AND-MULTISCALE-FEATURE-PANEL`
— NOT started in this run. DATA-1 may use the liquidity proxies listed in
section 5 under a preregistered frozen rule.
