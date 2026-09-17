# BLOC 2 — PROVIDER PROBE PLAYBOOK

**Status:** PLANNING COMPLETE CANDIDATE  
**Purpose:** specify exactly how the future execution agent should probe each candidate source without conflating documentation, current access, historical depth, sensor semantics, or provider role.

---

## 1. Global provider-probe rule

Each provider is probed independently.

No provider receives a pass because another provider fills its gaps.

Redundancy matters only **after** provider-specific capability is known.

For every provider, answer:

```text
WHAT can be observed?
WHERE (which venue/market family)?
WHEN (historical depth)?
HOW OFTEN (granularity)?
FOR WHICH instruments?
IN WHAT native units?
WITH WHAT timestamp meaning?
UNDER WHAT access conditions?
WITH WHAT reproducibility?
AT WHAT semantic fidelity?
```

---

## 2. Probe order

Use this sequence to minimize wasted calls and ambiguous failures:

```text
P0  documentation/registry expectation check
P1  endpoint/file existence check
P2  recent-control request
P3  native schema sample
P4  historical checkpoint probes
P5  pagination/history traversal test
P6  timestamp semantics audit
P7  unit semantics audit
P8  symbol breadth sample
P9  gap/continuity sample
P10 free-only/access revalidation
P11 capability claim synthesis
```

If P2 fails due to a hard access condition, do not spam P4-P9.

---

## 3. Common checkpoint matrix

Default historical probes:

```text
2021-06-15
2022-06-15
2024-06-15
2026-06-15
RECENT_CONTROL
```

For interval data, probe a bounded window around each date, not one timestamp only.

Suggested window:

```text
1m/5m/15m data: 24h target window
1h/4h: 7d target window
1d: 30d target window
raw events: bounded 1h-24h depending event density
books: short bounded sample sufficient to verify existence/shape
```

The execution agent may adjust if provider limitations require it, but must document the reason.

---

## 4. Core instrument basket

Default:

```text
BTC
ETH
SOL
MID_TAIL_CONTROL
```

The provider probe module must map these to native instrument names explicitly.

If SOL is not historically available at a tested checkpoint, record listing-history limitation.

`MID_TAIL_CONTROL` should be selected per provider with:

- perpetual/futures relevance,
- non-core asset,
- adequate venue history,
- no special delisting/relaunch ambiguity where avoidable.

---

# PROVIDER PLAYBOOKS

## 5. KRAKEN_FUTURES

### Expected strategic role

Potential high-value all-in-one mechanical analytics source.

Candidate sensors:

```text
MECHANICAL_LIQUIDATION
MECHANICAL_OPEN_INTEREST
MECHANICAL_FUNDING
MECHANICAL_BOOK_METRIC
MECHANICAL_BASIS
MECHANICAL_POSITIONING / FLOW-LIKE ANALYTICS
```

Potential derived/reported analytics include liquidation volume, OI, aggressor differential, CVD, orderbook, spread, liquidity, slippage, funding and basis.

### Probe priorities

1. Determine whether market-analytics history actually reaches 2021/2022.
2. Identify which products have deep history.
3. Verify each analytics type independently; do not assume one endpoint means equal history for all fields.
4. Verify requested `since/to` semantics.
5. Verify intervals individually.
6. Record whether orderbook/liquidity outputs are raw books or precomputed metrics.
7. Determine whether CVD/aggressor metrics can map only to `CORROBORATION_ONLY` or `NORMALIZABLE_COMPARABLE` against reconstructed trade flow.

### Critical failure modes

```text
analytics endpoint works only recently
instrument rename/history split
metric-specific history differences
XBT/BTC identity ambiguity
precomputed methodology opaque
```

### Promotion expectations

Kraken may be promoted per sensor even if other metrics remain opaque.

Do not let an opaque slippage methodology invalidate clean OI history, for example.

---

## 6. GATE_FUTURES

### Expected strategic role

Primary candidate for interval-level liquidation + OI + taker-flow statistics.

Candidate sensors:

```text
MECHANICAL_LIQUIDATION
MECHANICAL_OPEN_INTEREST
MECHANICAL_POSITIONING
MECHANICAL_FUNDING
MECHANICAL_BOOK_METRIC / current depth where supported
```

### Probe priorities

1. Probe `contract_stats` or equivalent statistics history depth.
2. Verify long/short liquidation fields separately.
3. Verify long/short taker-size semantics.
4. Verify OI native units and USD-notional availability.
5. Determine historical interval support.
6. Test whether `from/to` truly traverses deep history or has retention caps.
7. Inspect long-tail symbol breadth.

### Critical failure modes

```text
API docs expose fields but history retention is short
field values are contracts without multiplier metadata
long/short taker semantics differ from aggressor trade reconstruction
contract migrations create discontinuities
```

### Promotion expectations

Gate is especially important for liquidation/OI corroboration if deep history survives probes.

---

## 7. BINANCE_USDM

### Expected strategic role

Historical backbone for trades/aggressor reconstruction, OI/metrics, funding and secondary book data.

Candidate sensors:

```text
MECHANICAL_TRADE
MECHANICAL_OPEN_INTEREST
MECHANICAL_FUNDING
MECHANICAL_BOOK_SNAPSHOT / BOOK_METRIC
MECHANICAL_POSITIONING
```

Historical liquidation capability is explicitly **not assumed**.

### Probe modes

Binance may require multiple data channels:

```text
PUBLIC REST
PUBLIC ARCHIVE / Vision-like bulk files
current WebSocket only for later live work
```

### Probe priorities

1. Enumerate public archive file availability by year/month/symbol.
2. Verify checksums and deterministic file naming.
3. Verify trade/aggTrade schema and maker-side flag semantics.
4. Verify OI/metrics archive history separately.
5. Verify funding archive/API history.
6. Verify bookDepth archive existence, cadence and level semantics.
7. Explicitly probe historical liquidation availability and accept likely failure.
8. Detect known archive holes rather than assuming continuity.

### Critical failure modes

```text
historical files removed for some sensor families
archive gaps
symbol delisting/relisting
API geo restriction
maker flag misinterpreted as aggressor side
bookDepth cadence confused with event L2
```

### Promotion expectations

A liquidation failure must not demote Binance's trade/OI/funding role.

Provider role is sensor-specific.

---

## 8. BYBIT_LINEAR

### Expected strategic role

Independent historical OI + funding + trade backbone, especially useful for cross-venue validation.

Candidate sensors:

```text
MECHANICAL_OPEN_INTEREST
MECHANICAL_FUNDING
MECHANICAL_TRADE
MECHANICAL_BOOK_SNAPSHOT / current-live later
MECHANICAL_LIQUIDATION if valid historical source is verified
```

### Probe priorities

1. Verify OI history to symbol launch using cursor traversal.
2. Measure maximum page window and pagination behavior.
3. Verify OI units by contract type.
4. Probe funding history depth.
5. Probe official/public historical trade archive.
6. Test symbol launch boundaries on SOL and mid-tail.
7. Search for a valid free historical liquidation surface, but do not infer one from current liquidation streams.

### Critical failure modes

```text
endpoint says symbol-launch history but pagination truncates
linear/inverse market mismatch
OI unit ambiguity
archive path differs by product generation
```

### Promotion expectations

Bybit should be considered high-value if OI and funding history validate even if book/liquidation history is limited.

---

## 9. OKX_SWAP

### Expected strategic role

Historical trades/funding plus the most promising deep historical orderbook source among candidates.

Candidate sensors:

```text
MECHANICAL_TRADE
MECHANICAL_FUNDING
MECHANICAL_BOOK_SNAPSHOT
MECHANICAL_BOOK_METRIC
MECHANICAL_OPEN_INTEREST if adequate history exists
```

### Probe priorities

1. Probe historical-data query/download workflow.
2. Verify whether 50/400/5000-level book history is genuinely free and downloadable.
3. Determine earliest historical book date by product.
4. Verify snapshot/event cadence and timestamp semantics.
5. Verify trades and funding history independently.
6. Probe OI only if an official free historical route exists; do not substitute current OI.
7. Estimate raw-book volume implications for later retention planning.

### Critical failure modes

```text
historical download link expires
book archive free but limited era
archive generation asynchronous
book levels are snapshots not updates
contract IDs change
```

### Promotion expectations

A strong book-history result can make OKX the primary liquidity-mechanics historical source even if its OI role is weak.

---

## 10. DERIBIT

### Expected strategic role

Mechanism microscope, especially BTC/ETH trade-level liquidation anatomy and derivatives context.

Candidate sensors:

```text
MECHANICAL_TRADE
MECHANICAL_LIQUIDATION
MECHANICAL_FUNDING
MECHANICAL_OPEN_INTEREST / current or historical if supported
MECHANICAL_BOOK_SNAPSHOT
```

### Probe priorities

1. Verify historical trade traversal by timestamp/sequence.
2. Inspect liquidation flag semantics on real historical trades.
3. Determine whether liquidation-tagged events can be recovered back through 2021/2022.
4. Verify taker direction.
5. Probe funding history.
6. Determine practical pagination rate for deep history.
7. Record narrower asset universe explicitly.

### Critical failure modes

```text
sequence pagination too expensive for broad backfill
BTC/ETH-heavy universe mistaken for broad-market coverage
liquidation flag sparse but valid
option/future/perpetual instrument confusion
```

### Promotion expectations

Deribit can remain a high-quality `MECHANISM_MICROSCOPE` even if not broad enough for cross-alt canonical coverage.

---

## 11. COINALYZE

### Expected strategic role

Free limited aggregator/corroborator for liquidation, OI, funding and long/short context.

Candidate sensors:

```text
MECHANICAL_LIQUIDATION
MECHANICAL_OPEN_INTEREST
MECHANICAL_FUNDING
MECHANICAL_POSITIONING
```

### Probe priorities

1. Verify free API key requirement and rate limits.
2. Probe daily history depth.
3. Measure actual intraday retention at several intervals.
4. Confirm whether old intraday data is deleted as documented.
5. Record venue aggregation semantics.
6. Determine whether instrument/provider attribution is preserved.
7. Classify fields as corroboration vs canonical-compatible.

### Critical failure modes

```text
intraday retention too shallow
aggregated vendor methodology opaque
symbol maps hide venue distinctions
free quota unsuitable for full historical backfill
```

### Promotion expectations

Likely `FREE_LIMITED_AUTOMATED` and `CORROBORATION_ONLY` for some fields.

Do not force it into primary truth.

---

## 12. BITFINEX_COMMUNITY_ARCHIVE

### Expected strategic role

Independent historical liquidation replication source.

Candidate sensor:

```text
MECHANICAL_LIQUIDATION
```

### Evidence class

Likely community-derived/archive evidence, not first-party exchange API truth.

### Probe priorities

1. Verify repository/archive availability.
2. Verify license.
3. Verify dump hash/checksum if published.
4. Verify earliest and latest timestamp in actual file sample.
5. Inspect liquidation side/size/instrument semantics.
6. Verify generation methodology from source code.
7. Detect duplicates/revisions.
8. Assess reproducibility of rebuilding archive from source.

### Critical failure modes

```text
archive disappears
methodology undocumented
partial history
duplicate events
spot/margin/perpetual semantics mixed
```

### Promotion expectations

Never `EXACT_EQUIVALENT` to first-party interval liquidation totals merely because dates overlap.

Likely corroboration/replication role.

---

# CROSS-PROVIDER PLAYBOOK

## 13. Sensor redundancy map to verify

Bloc 2 must end with a measured version of this planned map:

```text
LIQUIDATIONS
  expected: Kraken / Gate
  microscope: Deribit
  corroboration: Coinalyze / Bitfinex

OPEN INTEREST
  expected: Bybit / Gate / Kraken
  fallback: Binance / Coinalyze

FUNDING
  expected: Bybit / Kraken / Gate
  fallback: Binance / OKX / Deribit / Coinalyze

ORDER FLOW
  expected: Binance trades / Kraken analytics
  fallback: Gate / Bybit / OKX trades

DEPTH / LIQUIDITY
  expected: OKX books / Kraken metrics
  fallback: Binance bookDepth
```

The implemented matrix may differ.

No design change is needed if one candidate fails, provided sensor coverage survives elsewhere.

---

## 14. Redundancy classes

For each critical sensor assign:

```text
R0 = no verified free provider
R1 = one verified provider
R2 = two independent verified providers
R3 = three or more independent verified providers
```

Preferred minimum before critical research use:

```text
LIQUIDATION  >= R2 where possible
OPEN_INTEREST >= R2
FUNDING >= R2
ORDER_FLOW >= R2 through native/reconstructed observations
DEPTH >= R1 with secondary corroboration
```

R1 is acceptable for a non-critical local/context sensor but receives a single-source risk flag.

---

## 15. Provider disagreement as future information

Bloc 2 does not synthesize cross-venue values, but it must preserve enough semantics that later T2 work can measure:

```text
source count
venue breadth
cross-provider disagreement
venue concentration
source-specific stress
```

Therefore provider-specific evidence may never be destructively merged during probing.

---

## 16. Probe report format per provider

Every provider report should contain:

1. provider summary,
2. access/free-only status,
3. sensors tested,
4. instruments tested,
5. historical checkpoints,
6. granularities,
7. earliest verified history,
8. timestamp semantics,
9. unit semantics,
10. pagination/archive behavior,
11. gaps,
12. rate limits,
13. known limitations,
14. semantic equivalence,
15. reproducibility evidence,
16. recommended role,
17. production-adapter eligibility.

---

## 17. Recommended provider-role outputs

Possible roles:

```text
PRIMARY
SECONDARY
FALLBACK
CORROBORATOR
MECHANISM_MICROSCOPE
CURRENT_ONLY
ARCHIVE_ONLY
REFERENCE_ONLY
EXCLUDED
```

Roles are **sensor-specific**.

Example:

```text
BINANCE_USDM / TRADE = PRIMARY
BINANCE_USDM / LIQUIDATION = EXCLUDED or CURRENT_ONLY
```

---

## 18. Stop rule

A provider probe stops when:

- hard paid requirement appears,
- repeated deterministic access block occurs,
- requested sensor is definitively unsupported,
- documentation + runtime prove current-only and historical history is absent,
- enough evidence exists to characterize capability.

Do not waste calls trying to force a preferred provider into the architecture.

---

## 19. Final planning decision

`BLOC_02_PROVIDER_PLAYBOOK_READY`

The build agent now has a provider-by-provider verification plan, expected roles, sensor priorities, failure modes and promotion criteria without relying on any single source to cover the complete mechanical stack.

`human_review_required = TRUE`
`implementation_authorized = FALSE`
