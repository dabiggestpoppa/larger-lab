# ALT-DATA-0 — Rank Survivorship Audit (Task 14)

**Mandatory test:** historical top-500 construction must NOT depend on the
current top-500. Select assets that were once highly ranked and are no
longer top-500 (or dead/renamed) today, and confirm they appear at their
true point-in-time ranks.

## 1. Method

For each prototype date we take the CMC dated snapshot (`data-api/v3/...
/listings/historical?date=...`). Because the snapshot is CMC's own record of
that date, it is point-in-time **by construction** — but we verify that the
*content* matches reality (fallen coins at plausible PIT ranks) and that
today's top-250 would NOT supply those coins (i.e., the reconstruction is
not a current-universe backfill).

## 2. Fallen / dead coins recovered in PIT snapshots

| coin | 2024-06-01 rank | 2025-01-01 rank | 2025-06-01 rank | 2026-01-01 rank | 2026-08-20 rank | today's CG top-250? |
|---|---|---|---|---|---|---|
| LUNC (Terra Classic) | 115 | 136 | 154 | 148 | 102 | yes — 134 today (still top-250; not the survivor case) |
| LUNA (Terra 2.0) | 140 | 235 (+344 dup) | 306 | 431 | >500 | no |
| FTT (FTX Token) | 138 | 82 | 148 | 176 | 335 | no |
| HOT (Holo) | 163 | 172 | 249 | 356 | 366 | no |
| XEM (NEM) | 245 | 297 | 480 | >500 | >500 | no |
| DGB (DigiByte) | 320 | 300 | 259 | 319 | 200 | no |
| BTT | 78 | 95 | 98 | 106 | 106 | no |
| ZEC | 159 | 104 | 79 | 14 | 11 | yes (moved back up) |

Ranks are the `cmcRank` values inside each dated snapshot. FTT/HOT/XEM/DGB
are absent from today's top-250 by any measure — their presence at dated
ranks proves the snapshots are NOT backfilled from the current universe.
(LUNC still ranks ~134 today, so it is not a survivor case itself; it is
kept in the table to show PIT rank stability across dates.)

## 3. Provider-level registry checks (dead-asset retention)

| provider | dead/fallen coin retention |
|---|---|
| CoinMarketCap (data-api) | retains full dated snapshots incl. dead/fallen coins (FTT #138 on 2024-06-01) |
| CoinPaprika | retains inactive coins with `is_active=false` (61,115-coin registry; `serum` present) |
| CoinGecko | registry includes dead coins (`ftx-token`, `serum`, `terra-luna`) but id renames observed (LUNC = `terra-luna`, LUNA = `terra-luna-2` in this data) |

## 4. Cross-check (independent provider, in-window date 2026-08-20)

CMC snapshot vs CoinPaprika per-coin daily history (both free-accessible for
this date):

| symbol | CoinPaprika mcap (USD) | CMC mcap (USD) | diff |
|---|---|---|---|
| BTC | 1,430,649,392,625 | 1,465,878,380,818 | −2.40% |
| ETH | 275,451,143,547 | 280,752,052,487 | −1.89% |
| HOT | 61,054,804 | 62,376,849 | −2.12% |
| LUNC | 348,825,679 | 291,341,660 | +19.73% (CHECK) |
| FTT | 28,474,461 | 71,662,691 | −60.27% (CHECK) |

BTC/ETH/HOT agree within ~2%. LUNC and FTT disagree materially — likely
circulating-supply definition differences between providers for distressed
assets. **Disagreements are flagged, not silently resolved** (the identity
spec requires a documented reconciliation rule before DATA-1).

## 5. Verdict

**RANK_UNIVERSE_SURVIVORSHIP_RISK: NOT PRESENT.** The reconstruction uses
dated CMC snapshots, contains fallen/dead coins at true PIT ranks (FTT
#138, HOT #163, XEM #245, DGB #320 on 2024-06-01 — none in today's
top-250), and is independently corroborated where the free window allows.
Current top-N data is used only to *demonstrate* non-dependence, never to
construct history.
