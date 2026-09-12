# ALT-DATA-0 — Sector / Category Reality Audit (Task 10)

## 1. Provider capability

| provider | sector signal | temporal status | multiple sectors? | drift evidence |
|---|---|---|---|---|
| CoinMarketCap | `tags` on snapshot rows (mineable, pow, defi, meme, ...) | **date-varying** — snapshot responses carry different tag sets per date | yes (many tags per coin) | drift test (probe `cmc_tags_drift_test.json`): BTC tags 2024=30 vs 2026=37; ETH 30→44; BNB 4→12 — tags are NOT current-static; they are snapshot-associated |
| CoinGecko | `coins/categories/list` taxonomy (865 categories) + per-coin `categories` | **CURRENT_ONLY** — no historical categories | yes | taxonomy itself churns (AI/meme labels added over time) |
| CoinPaprika | `type` (coin/token) only | static/weak | no | — |
| DexScreener / DexPaprika | none | — | — | — |

## 2. Classification applied in the prototype

Sector status classes (preregistered):

- `POINT_IN_TIME_VERIFIED` — none available in free stack
- **`HISTORICAL_APPROXIMATION`** — CMC snapshot tags (date-associated,
  taxonomy drift unverified) — applied to all PIT prototype rows
- `CURRENT_ONLY` — CoinGecko categories
- `UNMAPPED` — assets without tags (CoinPaprika/DEX-only assets)

## 3. Rules (fail-closed)

1. **Today's CoinGecko category is NEVER applied to an old date without the
   `CURRENT_ONLY` label.** (Fail-closed rule: current-only sectors presented
   as historical → FAIL.)
2. CMC tags are usable as `HISTORICAL_APPROXIMATION` because they are
   snapshot-date-associated (verified drift), but taxonomy-drift means a
   "defi" tag in 2024 may mean a different membership than in 2026 — DATA-1
   must freeze a dated tag snapshot per asset and document taxonomy changes.
3. Sector terrain features (sector rank, top-N, shares) are buildable on the
   `HISTORICAL_APPROXIMATION` basis with an explicit approximation flag.

## 4. Verdict

No free provider offers true point-in-time sector classification. The
foundation can proceed with `HISTORICAL_APPROXIMATION` (CMC dated tags) +
`CURRENT_ONLY` (CG) — never conflating the two. This satisfies the
"truthfully classified" requirement.
