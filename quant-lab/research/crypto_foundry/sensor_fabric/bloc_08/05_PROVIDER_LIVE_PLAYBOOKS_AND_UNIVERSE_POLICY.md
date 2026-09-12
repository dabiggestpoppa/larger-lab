# BLOC 8 — PROVIDER LIVE PLAYBOOKS & UNIVERSE POLICY

**Planning status:** COMPLETE FOR THIS CHAPTER  
**Implementation status:** NOT STARTED

---

## 1. Objective

Translate the common live-recorder architecture into provider-specific recording plans without duplicating provider semantics or making any one venue a canonical source of truth.

Final implementation behavior depends on Bloc 2 verified capabilities and Bloc 3 adapter contracts.

These are implementation books, not guarantees that every endpoint remains available.

---

## 2. Provider role principle

Providers contribute complementary live evidence.

No provider is required to cover every sensor.

If one source becomes unavailable, canonical sensor health is evaluated through Bloc 6 rather than by silently substituting another venue as if it were the same market.

---

# 3. KRAKEN FUTURES LIVE PLAYBOOK

## Planned role

Primary candidate for rich analytics-style live mechanics:

- liquidation volume;
- open interest;
- funding;
- aggressor differential / CVD;
- spreads;
- liquidity;
- slippage;
- basis;
- orderbook analytics where verified.

## Preferred modes

```text
analytics REST polling
provider WebSocket feeds where verified useful
periodic server-time/health probes
```

## Priorities

U0:
- full verified analytics set;
- trades/book if operationally justified.

U1:
- liquidation/OI/funding/aggressor analytics.

U2:
- only cheap stats where supported.

## QA

- verify interval publication delay;
- distinguish event vs aggregate liquidation semantics;
- preserve native units;
- monitor analytics endpoint method/schema drift;
- compare CVD/aggressor methodology against reconstructable trade flow where possible.

## Failure behavior

If analytics becomes stale while provider socket remains healthy:

```text
KRAKEN provider may remain healthy
KRAKEN analytics feed becomes STALE
```

Do not collapse them.

---

# 4. GATE FUTURES LIVE PLAYBOOK

## Planned role

Broad-alt mechanical breadth:

- long/short liquidations;
- OI;
- taker buy/sell activity;
- funding;
- positioning ratios where verified.

## Preferred modes

```text
REST stats polling
WebSocket stats/event feeds where verified
public trade streams for selected U0/U1 instruments
```

## Special value

Gate is useful because broad alt coverage may remain richer than BTC/ETH-centric venues.

This should support lower-field/rank-depth work later.

## QA

- confirm contract multiplier and size units;
- preserve long/short liquidation definitions;
- monitor interval alignment;
- distinguish top-trader/user-positioning ratios from OI/funding primitives.

---

# 5. BINANCE USD-M LIVE PLAYBOOK

## Planned role

High-volume public market backbone:

- aggTrades / trades;
- aggressor-side reconstruction inputs;
- funding;
- OI/metrics where live public endpoints support them;
- bookTicker / depth streams;
- book snapshots for U0/U1.

Historical liquidation availability limitations do not prevent using live public liquidation streams if they remain verified and free.

## Preferred modes

```text
WebSocket aggTrade/trade
WebSocket depth/bookTicker
REST OI/funding/metadata polling
live liquidation stream only if verified
```

## Aggressor semantics

`isBuyerMaker`-style semantics must be centralized in tested parser logic.

No notebook-level side inversion.

## Book doctrine

For full-depth reconstruction:

- use provider snapshot+delta sequence rules exactly;
- detect update-ID gaps;
- restart book epoch after invalid continuity.

## Storage

Full-depth restricted to U0 and selected U1.

AggTrades may be preferred over raw trades for broader U1 storage efficiency if the scientific use does not require individual prints.

---

# 6. BYBIT LINEAR LIVE PLAYBOOK

## Planned role

Independent leverage/funding/flow replication:

- OI;
- funding;
- public trades;
- liquidation events where verified;
- orderbook for selected U0.

## Preferred modes

```text
WebSocket public trade/orderbook
REST OI/funding polling
public liquidation stream if capability probe verifies semantics
```

## QA

- preserve category/instrument distinctions;
- confirm units across linear contracts;
- handle symbol launch/delisting dynamically;
- use provider sequence semantics for books.

## Role in redundancy

Bybit should often contribute a genuinely independent OI/funding venue, not merely a fallback for Binance.

---

# 7. OKX SWAP LIVE PLAYBOOK

## Planned role

Trade + funding + liquidity/depth diversification:

- public trades;
- funding;
- OI where verified;
- orderbook / depth;
- spread/liquidity reconstruction.

## Preferred modes

```text
WebSocket trades
WebSocket books
REST funding/OI polling
```

## Special value

OKX is a candidate independent liquidity source for validating depth withdrawal and spread expansion mechanics.

## QA

- instrument IDs and contract values;
- checksum/sequence semantics;
- book channel depth/frequency differences;
- stablecoin settlement distinctions.

---

# 8. DERIBIT LIVE PLAYBOOK

## Planned role

Mechanism microscope primarily for BTC/ETH:

- liquidation-tagged trades;
- taker direction;
- funding;
- OI where public and useful;
- orderbook/spread context.

## Preferred modes

```text
public WebSocket trades
public book feeds for U0 microscope
REST periodic state polls
```

## Unique preservation

Retain provider liquidation marker:

```text
M
T
MT
```

or current provider equivalent as native truth.

Do not flatten into interval liquidation totals until later derived layers.

## Universe

Primarily U0 because coverage is naturally narrower and mechanism-focused.

---

# 9. COINALYZE LIVE PLAYBOOK

## Planned role

Third-party corroboration:

- OI;
- funding;
- liquidation aggregates;
- long/short ratios.

## Preferred mode

```text
REST polling under free API limits
```

## Restrictions

- third-party evidence class;
- dependency graph must prevent fake independence;
- intraday retention limits make our own recorder particularly valuable;
- never count Coinalyze as equivalent to exchange-native source without semantic check.

## Polling

Prioritize a bounded universe so free API call limits are not exhausted by low-value long-tail requests.

---

# 10. BITFINEX COMMUNITY ARCHIVE

This source is historical/community evidence, not a natural live primary recorder feed.

Bloc 8 does not need to manufacture a live collector unless a verified free forward interface becomes part of Bloc 2/3 capability evidence.

Default live status:

```text
HISTORICAL_ONLY
```

Its role remains independent liquidation replication in historical research.

---

## 11. Provider live capability matrix

Implementation must materialize a runtime matrix similar to:

| Provider | Trades | Liquidations | OI | Funding | Book | Positioning | Live role |
|---|---|---|---|---|---|---|---|
| Kraken | verify | strong candidate | strong | strong | analytics/verify | some | rich mechanics |
| Gate | verify | strong | strong | strong | selective | strong | broad alts |
| Binance | strong | verify | strong | strong | strong | metrics | market backbone |
| Bybit | strong | verify | strong | strong | strong U0 | limited | independent leverage |
| OKX | strong | verify | verify | strong | strong | limited | liquidity diversity |
| Deribit | strong | unique tagged | verify | strong | U0 | limited | mechanism microscope |
| Coinalyze | no raw trades | aggregate | aggregate | aggregate | no | ratios | corroboration |
| Bitfinex archive | historical | historical | — | — | — | — | no default live |

The word `verify` must be resolved from actual Bloc 2 capability evidence before implementation enables a feed.

---

## 12. Sensor-first live routing

### Liquidations

Desired live independent evidence:

```text
Kraken
Gate
+ Binance/Bybit where verified
+ Deribit microscope
+ Coinalyze corroboration
```

### Open interest

```text
Bybit
Gate
Kraken
+ Binance/OKX where verified
+ Coinalyze corroboration
```

### Funding

```text
Bybit
Kraken
Gate
Binance
OKX
Deribit
+ Coinalyze corroboration
```

### Aggressor flow

```text
Binance
Kraken analytics
Gate taker stats/trades
Bybit trades
OKX trades
Deribit trades
```

### Liquidity/depth

```text
OKX
Binance
Kraken analytics/books
Bybit/Deribit selected U0
```

---

## 13. Point-in-time live universe

The recorder does not subscribe to “current top N” with no history.

Every membership decision becomes explicit evidence.

Inputs may include later-defined policy such as:

- minimum liquidity/activity;
- research rank tier;
- manual core list;
- exchange availability.

Bloc 8 only freezes the mechanics of versioned membership, not the ranking formula.

---

## 14. Initial U0 planning set

At implementation/pilot time, minimum U0 should include:

```text
BTC
ETH
SOL
```

plus additional highly liquid core assets if storage allows.

This mirrors Bloc 7 pilot coverage and creates immediate cross-check continuity.

Final U0 is config, not hard-coded ontology.

---

## 15. U1 dynamic selection

U1 can be a broad active perpetual universe but subscription count must respect:

- provider connection limits;
- provider subscription limits;
- local bandwidth;
- disk;
- CPU.

If limits bind, prioritize P0 sensor breadth before P2 depth richness.

---

## 16. U2 long-tail policy

U2 should favor cheap interval state sensors:

```text
OI
funding
liquidation stats
coarse positioning
```

Avoid raw trades/full books unless a specific research amendment promotes an asset/tier.

---

## 17. New listing behavior

When a new contract lists:

1. observe provider instrument metadata;
2. create/update Bloc 5 lifecycle identity;
3. determine universe eligibility;
4. start authorized feeds only after identity is valid;
5. preserve first-observed/listing timing.

No feed should begin under an unresolved contract identity if normalization would be ambiguous.

---

## 18. Delisting behavior

At delisting:

- stop new subscription;
- close feed/session lineage;
- mark lifecycle end;
- preserve final evidence;
- do not reinterpret post-delisting absence as feed gap.

---

## 19. Provider rate/subscription budgeting

Live policy must coordinate with the same provider-wide budget used by historical repair/backfill.

Priority:

```text
P0 live capture
→ urgent expiring gap repair
→ normal live P1
→ normal backfill
→ optional P2/deep book
```

Exact scheduler weights are implementation config.

---

## 20. Coexistence with Bloc 7 backfill

Historical backfill and live recording can run concurrently only when:

- rate budgets are shared;
- storage headroom is sufficient;
- P0 live continuity is protected;
- backfill cannot starve live heartbeat/polls.

If resources conflict, live P0 wins by default.

---

## 21. Provider schema drift during live operation

If a live parser sees unexpected schema:

```text
preserve raw bytes
→ flag SCHEMA_DRIFT
→ quarantine normalization
→ keep provider/feed health separate
→ require parser review/version bump
```

Do not discard unknown fields by silently forcing the old schema.

---

## 22. Provider semantic drift

Examples:

- OI units change;
- liquidation side meaning changes;
- book channel depth changes;
- funding interval changes.

Semantic drift may be harder to detect than schema drift.

Use:

- capability-regression smoke tests;
- value-distribution sanity checks;
- documentation evidence updates;
- cross-provider disagreement diagnostics.

---

## 23. Pilot plan

Before full always-on activation, run a bounded live pilot:

```text
BTC + ETH + SOL
Kraken + Gate + Binance + Bybit
```

where verified, for at least:

```text
liquidations
OI
funding
trades/aggressor
one full-book feed
```

Suggested validation duration:

```text
minimum 24h functional
preferred 72h resilience
```

The exact duration is an implementation acceptance parameter, not a market rule.

---

## 24. Pilot must include induced failures

Use fake/test transport or controlled process interruption to demonstrate:

- socket disconnect;
- process restart;
- local network interruption simulation;
- disk WATCH/CONSTRAINED behavior;
- sequence gap;
- REST repair;
- duplicate overlap;
- provider-specific one-feed failure.

Do not wait for real outages to test resilience.

---

## 25. Provider activation gate

A live provider/sensor is enabled only after:

```text
Bloc2 capability verified
Bloc3 adapter ready
Bloc4 T0 sink validated
Bloc5 T1 normalization validated
Bloc6 quality semantics available
Bloc8 live conformance tests pass
```

---

## 26. Planning decision

The live stack is built for complementary coverage: each provider does the job it is actually good at, and missing capabilities are covered at the sensor level rather than hidden behind a fake universal exchange abstraction.
