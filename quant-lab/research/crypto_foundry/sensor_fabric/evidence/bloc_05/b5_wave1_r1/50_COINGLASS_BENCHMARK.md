# CoinGlass exploratory benchmark lane — documented capability review

**Status:** exploratory only. **No subscription purchased. No restricted endpoint
scraped. No account created. No API request issued.** Documentation reviewed
2026-11-27 against CoinGlass public docs and pricing pages.

This lane is kept separate from provider golden evidence. Nothing here enters the
fixture corpus, and CoinGlass is **not** a production dependency.

---

## 1. What "Legend" is

`Legend` is a **UI product on its own subdomain** (`legend.coinglass.com`), marketed
with "elite superchart tools, liquidity heatmaps, and real-time order flow insights
like footprint and large trades". It appears as a `Legend NEW` navigation item on the
main site and the pricing page.

It is **not an API tier**. The API ladder is Hobbyist / Startup / Standard /
Professional / Enterprise. There is no documented Legend API entitlement, key type,
endpoint allowance or rate limit. Any plan to obtain Legend data programmatically
would require an Enterprise agreement, not a Legend purchase.

## 2. Documented API surface

* Base URL `open-api-v4.coinglass.com`; **168 REST endpoints + 4 WebSocket channels**.
* Categories: Futures 63, Spot 18, Options 4, On-Chain 7, ETF 17, Indicators 53,
  Other 5, Account 1.
* Authentication: `CG-API-KEY` header (REST) or `cg-api-key` query parameter
  (WebSocket). No request signing. Failures return HTTP 200 with `code` `"401"`/
  `"400"` in the JSON body.
* Quota headers: `API-KEY-MAX-LIMIT`, `API-KEY-USE-LIMIT`.

| Plan | Monthly | REST endpoints | Requests/min | WebSocket | Usage scope |
| --- | --- | --- | --- | --- | --- |
| Hobbyist | $35 | 83 | 30 | — | personal |
| Startup | $95 | 134 | 80 | — | personal |
| Standard | $379 | 155 | 300 | 4 channels | commercial |
| Professional | $879 | 168 | 1,200 | 4 channels | commercial |
| Enterprise | quote | all/custom | custom | custom | commercial |

Endpoint counts differ slightly between the docs table and the marketing page
("70+/80+/90+"); the docs table is the one that states endpoint-level permissions, so
it is used here.

## 3. Which mechanical sensor families are represented

| Sensor family | Represented? | Documented route family | Minimum plan |
| --- | --- | --- | --- |
| `MECHANICAL_OPEN_INTEREST` | yes | Pair OI history (OHLC), Aggregated OI, Aggregated stablecoin-margin OI, Aggregated coin-margin OI, Exchange list | Hobbyist |
| `MECHANICAL_FUNDING` | yes | Funding-rate history (OHLC), OI-weighted funding rate | Hobbyist |
| `MECHANICAL_POSITIONING` | yes | Long/short account ratio, top-trader account ratio, top-trader position ratio, taker buy/sell ratio | Hobbyist |
| `MECHANICAL_LIQUIDATION` | yes | Pair liquidation history, coin aggregated liquidation history, liquidation orders, liquidation heatmap/map/max pain | Hobbyist (history), Standard (orders), Professional (models) |
| `MECHANICAL_BOOK_SNAPSHOT` | yes | Order-book heatmaps, large orders, tick-level L2/L3 | Standard |
| `MECHANICAL_BOOK_METRIC` | partially | Order-book heatmap / large-order analytics (provider-methodology, undocumented formulas) | Standard |
| `MECHANICAL_TRADE` | yes | Taker buy/sell, futures and spot CVD, footprint charts, tick trades | Startup / Standard |
| `MECHANICAL_BASIS` | **not documented** | no basis endpoint in the reviewed categories; a basis would have to be derived from two prices and would therefore not be provider-native | — |

## 4. Historical coverage, as documented

Coverage is **query depth per interval**, not a guarantee about the underlying venue
history:

| Interval | Hobbyist | Startup | Standard | Professional |
| --- | --- | --- | --- | --- |
| 1m | — | — | 6 d | 12 d |
| 5m | — | — | 30 d | 60 d |
| 30m | — | 90 d | 180 d | 360 d |
| 1h | — | 180 d | 360 d | 720 d |
| 4h | 180 d | 180 d | 360 d | 720 d |
| 1d | full history | full history | full history | full history |

"Full history" means whatever the vendor stores for that pair; start dates differ by
instrument. This is materially shallower than a first-party venue archive for
minute-level research, which is the regime the frozen program targets.

## 5. Venue aggregation limitations

* Aggregated endpoints accept `exchange_list` and **sum across the exchanges you
  specify**; the response does not attribute the total back to a venue.
* Aggregated OI is further split into **stablecoin-margined** and
  **coin-margined** series — a distinction the canonical model keeps as separate
  contract types, not as one number.
* Pair-level endpoints are venue-scoped and therefore usable in principle; aggregated
  ones are not attributable at all.

Consequence under frozen law: `bloc_05/04` §4.4 forbids assigning a multi-venue
aggregate to one venue, and §14 forbids cross-venue synthesis at T1. Therefore:

* aggregated OI → venue-unknown, at best `CORROBORATION_ONLY`;
* pair OI/funding → potentially `NORMALIZABLE_COMPARABLE`, pending methodology review;
* OI-weighted funding → a **vendor-derived** metric, never `EXACT_EQUIVALENT` to any
  venue's native rate;
* liquidation USD history → venue-reporting-definition dependent; not comparable
  across venues without a documented definition per venue.

## 6. Modelled versus realised liquidations

CoinGlass publishes both realised liquidation history/orders and **modeled**
liquidation heatmaps, maps and max-pain levels. The documentation explicitly does not
publish the formulas distinguishing its three liquidation models.

These are different objects. A heatmap is an inference from open interest, leverage
assumptions and price levels; it is **not** a realized liquidation event, has no
position side observed from a venue, and cannot enter `MECHANICAL_LIQUIDATION` as
evidence. Any use would be a separate modeled-signal family with its own methodology
id, and would still be `NOT_COMPARABLE` with realized events. This lane treats the
heatmap as out of scope rather than as a shortcut for missing liquidation data.

## 7. Licensing and access restrictions

* Hobbyist and Startup are **personal use only**; commercial use requires Standard or
  above (per the plan table and FAQ). This program would be commercial use.
* CSV and bulk export are Enterprise-only.
* Redistribution of the data is not granted by the standard plans; the Terms of
  Service govern. Treat any CoinGlass-derived artifact as non-redistributable, and
  therefore as unable to enter a published fixture corpus.
* **There is no free API tier.** The free public web terminal (funding, OI,
  long/short, liquidation history, options OI, exchange rankings, BTC exchange
  balances) requires no account and is human-viewable, but no licence to consume it
  programmatically is documented, and scraping it is prohibited by this mission.

## 8. Is there useful lawful free access?

**Not established.** The documented paths are: (a) paid API subscription; (b) manual
consultation of the public web terminal by a human; (c) an Enterprise agreement.
None of (a)–(c) yields free, lawful, machine-readable access today, and the mission
forbids both purchasing and scraping. So the honest answer is: *no free lawful
programmatic access exists for this program at present*, and the free-only
requirement remains unchanged.

## 9. Assessment for this program

Useful as **optional external corroboration only**, and only under four hard
preconditions:

1. a paid **commercial** plan (Standard or above) — Hobbyist/Startup are personal-use;
2. **venue-scoped endpoints only** — never aggregated series, never assigned to a venue;
3. an explicit semantic-equivalence classification per field, with the vendor
   methodology cited where the field is vendor-derived (OI-weighted funding, CVD,
   heatmaps);
4. modeled liquidation products excluded from realised-liquidation evidence entirely.

Under those preconditions it could serve the Bloc 6 corroboration lane. It cannot
substitute for first-party provider evidence for I20 golden fixtures, because a
redistributable capture is not available and its venue-level granularity is shallower
than the venue's own archive.

**Recommendation: do not adopt now.** Record as a documented, lawful, paid option for
a future corroboration lane; keep the free-only requirement intact; keep CoinGlass
out of the provider registry, the fixture corpus and the production dependency set.
