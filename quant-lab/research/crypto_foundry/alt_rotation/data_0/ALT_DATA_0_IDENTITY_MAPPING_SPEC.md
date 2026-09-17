# ALT-DATA-0 — Provider-Neutral Canonical Identity Map (Design Spec, Task 9)

## 1. Principle

**NO SYMBOL-ONLY JOIN.** The canonical identity anchor is the provider-
neutral `internal_asset_id`. In DATA-0 the anchor is **CMC `id`** (stable,
present in every dated snapshot, survives renames). Symbol joins are
permitted ONLY as enrichment with an explicit `mapping_method` and
`mapping_confidence`, and every ambiguous case must be flagged.

## 2. Schema (canonical table)

Persisted working artifact: `identity/canonical_identity_map.csv`
(949 rows built from the 5 prototype snapshots).

| field | description | example |
|---|---|---|
| internal_asset_id | `CMC:<id>` — canonical | `CMC:1` |
| cmc_id / cmc_slug / cmc_name | CMC identity | 1 / bitcoin / Bitcoin |
| canonical_symbol | latest observed symbol | BTC |
| symbols_observed | pipe-separated symbol history across snapshots (rename/ticker-reuse evidence) | `MATIC|POL` |
| coingecko_id | best CG match | bitcoin |
| cg_join | HIGH (name-ratio ≥0.6) / SYMBOL_ONLY / NONE | HIGH |
| coinpaprika_id | best CP match | btc-bitcoin |
| cp_join | HIGH / SYMBOL_ONLY / NONE | HIGH |
| date_added_cmc | CMC listing date (minimum-coin-age proxy, NOT contract creation) | 2010-07-13 |
| first/last_seen_in_snapshots | snapshot presence range | 2024-06-01 / 2026-08-20 |
| ticker_reuse_flagged | >1 CG or CP candidate for the symbol | True |

Join statistics: 949 identities; 915 with CG id, 924 with CP id;
**608 symbols flagged for ticker reuse** (short symbols like `AI`, `LUNA`,
`SRM` collide across providers) — every one of these requires disambiguation
in DATA-1, none is silently joined.

## 3. Handling rules (preregistered)

| case | rule |
|---|---|
| ticker reuse | retain all candidates; canonical join only when name-ratio ≥0.6; else `SYMBOL_ONLY` + flag. Never overwrite `internal_asset_id`. |
| token rebrands | MATIC→POL, RNDR→RENDER, MKR→SKY: keep one `internal_asset_id`; record `symbols_observed`; venue symbols resolved via alias table. |
| chain migration | same contract family, new chain: identity preserved at asset level; chain recorded separately (contract-level rows in DATA-1). |
| wrapped vs native | WBTC/WETH/stETH etc. are DISTINCT assets (separate `internal_asset_id`) — confirmed necessary: CMC 2026-08-20 ranks 201-300 are dominated by wrapped/LST assets with no perps. |
| exchange aliases | 1000x perp naming is a **venue symbol alias, not an asset rename**: `1000PEPEUSDT` → asset PEPE. Binance archive verifies the convention (`1000PEPEUSDT` exists, `PEPEUSDT` does not). `1M*` similar. Alias table: venue_symbol → internal_asset_id + multiplier. |
| HL legacy names | HL meta retains renamed coins as `isDelisted` entries (MATIC, RNDR, MKR) — map legacy → current asset via funding-continuity, not symbol equality. |
| CoinPaprika slug quirks | `luna-terra` carries symbol LUNC; `luna-terra-v2` = LUNA. Slug≠symbol. |
| 1000-token multipliers | strip `1000`/`1M` prefix for canonical join; record multiplier in venue instrument row. |

## 4. Confidence model

- `HIGH`: name similarity ≥ 0.6 (token-set ratio) + symbol equality
- `SYMBOL_ONLY`: symbol equality only — NEVER used as canonical identity
- `NONE`: no match; row remains asset-level only (venue join impossible)

## 5. DATA-1 contract for identity

1. Canonical anchor = `internal_asset_id` (`CMC:<id>`), frozen.
2. Every PIT row must resolve to exactly one `internal_asset_id`; otherwise
   the row is dropped and counted (fail-closed).
3. Venue contract rows carry `venue_symbol` + `multiplier` + resolved
   `internal_asset_id`; unresolved venue symbols are recorded as orphans.
4. All joins recorded with `mapping_source` (provider files + probe
   hashes) and `mapping_confidence`.
