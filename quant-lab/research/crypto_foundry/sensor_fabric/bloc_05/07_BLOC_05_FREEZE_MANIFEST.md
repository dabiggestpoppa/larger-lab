# BLOC 5 — FREEZE MANIFEST

**Planning status:** COMPLETE  
**Implementation status:** NOT STARTED  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Purpose:** freeze PIT identity, timing, semantic normalization, unit conversion, T1 lineage, duplicate/revision handling, and canonical T1 query rules before Bloc 6 designs quality/redundancy/failover.

---

## 1. Frozen architectural decisions

### F1 — Asset identity does not erase contract identity

Every economically normalized observation retains:

```text
provider
venue
native instrument
contract instance
economic contract
canonical underlying asset
```

No single `BTC` label is allowed to destroy venue/payoff/settlement context.

### F2 — Contract identity is point-in-time

Identity mappings use both:

```text
valid time
knowledge time
```

Current symbol metadata cannot silently backcast into history.

### F3 — Exact contract instance is mandatory for economic normalization

A row with ambiguous or unverified contract terms may remain native evidence but cannot be treated as verified comparable T1 data.

### F4 — Listing lifecycle is explicit

```text
PRE_LISTING
ACTIVE
SUSPENDED
DELISTING_ANNOUNCED
DELISTED
RELISTED_NEW_INSTANCE
UNKNOWN
```

Historical absence before listing is not missing data; post-delisting absence is not zero.

### F5 — Linear/inverse/quanto semantics are explicit

No universal futures conversion formula.

Price-dependent inverse conversions require PIT-valid contract terms and reference-price lineage.

### F6 — Base/quote/settlement/margin assets remain separate

No symbol-string shortcut may collapse them without verified provider convention.

### F7 — Stablecoin is not fiat by assumption

`USDT`, `USDC`, and `USD` remain different canonical assets.

Native quote notional is truth; optional USD equivalent requires PIT-safe conversion evidence.

### F8 — Timestamp truth is multi-dimensional

T1 may preserve:

```text
source_event_at
interval_start_at
interval_end_at
effective_at
published_at
market_available_at
observed_at
ingested_at
normalized_at
```

No single timestamp silently substitutes for all meanings.

### F9 — Market availability differs from system ingestion

Historical replay uses the earliest defensible **market-public** availability time, not simply when our system downloaded the file.

### F10 — Archive reconstruction is labeled

Historical archive rows can reconstruct contemporaneous events only when source semantics prove those events were public then.

Late corrections remain revision-aware.

### F11 — Revision mode is explicit

Research/replay chooses among modes such as:

```text
AS_KNOWN_THEN
LATEST_VERIFIED
FIRST_SEEN
EXACT_REVISION
ALL_REVISIONS
ERROR_ON_AMBIGUITY
```

Future corrections cannot leak into past `AS_KNOWN_THEN` state.

### F12 — Native values always survive normalization

Canonical comparability is additive.

No destructive replacement of provider-native amount/unit semantics.

### F13 — Null and zero are different

Verified economic zero may be `0`.

Unavailable/unsupported/unverified values are `NULL` with explicit reason.

No zero-fill.

### F14 — Methodology is versioned

Every non-trivial normalization/conversion has:

```text
methodology_id
methodology_version
required inputs
PIT requirements
known limitations
```

### F15 — Semantic equivalence is operational

Provider mappings retain:

```text
EXACT_EQUIVALENT
NORMALIZABLE_COMPARABLE
CORROBORATION_ONLY
NOT_COMPARABLE
```

A free source does not become scientifically equivalent merely because units look similar.

### F16 — Provider-native analytics remain provider-native evidence

Kraken CVD/slippage/liquidity or other provider-derived analytics can enter T1 with methodology/equivalence metadata but do not automatically become Fabric T2 definitions.

### F17 — Trade aggressor side follows provider semantics

Never infer aggressor direction from price movement.

Provider-side rules such as Binance `isBuyerMaker` are versioned/tested centrally.

### F18 — Liquidation side semantics remain separated

Keep distinct:

```text
position side liquidated
execution side
aggressor side if known
maker/taker liquidation role if known
```

Long liquidation is not stored merely as generic sell flow.

### F19 — OI remains a stock/snapshot object

OI unit and snapshot/interval semantics are explicit.

OI change is not created as liquidation/flow during normalization.

### F20 — Funding native/predicted/effective semantics remain separate

Predicted or indicative funding never overwrites realized funding.

Native interval/rate remains truth; normalized interval equivalents are methodology-backed additions.

### F21 — Book reconstruction fails on sequence gaps

Delta streams cannot claim a full book unless sequence-safe reconstruction succeeds.

### F22 — Positioning metrics retain population definition

Top-trader account ratio, top-trader position ratio, taker ratio, and provider-defined ratios remain distinct.

### F23 — Basis retains reference identity and units

Raw basis, percentage basis, and annualized basis are not silently mixed.

### F24 — Cross-venue synthesis does not occur at T1

T1 stays provider/venue scoped.

Cross-venue consensus/breadth/dispersion belongs to later T2 work.

### F25 — Every T1 row has complete T0 lineage

Required chain:

```text
T1
→ T0B/raw normalization batch
→ AcquisitionRecord
→ T0A EvidenceBlob SHA256
```

Derived fields also retain conversion-input lineage.

### F26 — Hard duplicates differ from soft candidates

Same provider event from REST/archive/live may unify economically only under a hard identity rule.

Soft fingerprints may flag but cannot destructively remove rows.

### F27 — Cross-venue events are never deduped by similarity

Same time/symbol/value on different venues remains separate evidence.

### F28 — Revisions append

Provider corrections, source mutation, identity rebuild, semantic reinterpretation, and normalization rebuild remain explicit/versioned.

No silent in-place rewrite.

### F29 — T1 generations are immutable once published

A generation records code/registry/methodology/revision mode and input manifests.

Methodology changes create new generations.

### F30 — Canonical research query boundary is mandatory

Research consumes the T1 query interface rather than filesystem globs/provider fields.

The query boundary enforces generation, revision, quality, and replay rules.

---

## 2. Frozen core identity objects

```text
CanonicalAsset
Venue
VenueInstrument
EconomicContract
ContractInstance
InstrumentAlias
InstrumentLifecycle
ContractTermsSnapshot
IdentityResolution
UniverseMembership
```

---

## 3. Frozen timing/revision objects

```text
TimeSemantics
AvailabilityResolution
RevisionPolicy
T1RevisionChain
ReplayEligibility
```

Strict replay eligibility values:

```text
ELIGIBLE
RETROSPECTIVE_ONLY
BLOCKED_TIMESTAMP
BLOCKED_REVISION
BLOCKED_IDENTITY
BLOCKED_LINEAGE
```

---

## 4. Frozen semantic/unit objects

```text
T1ObservationEnvelope
NormalizationMethodology
ProviderSemanticMapping
ConversionRateObservation
ConversionLineage
FieldLineage
T1Quality
```

---

## 5. Frozen sensor normalizers

```text
TradeNormalizer
LiquidationNormalizer
OpenInterestNormalizer
FundingNormalizer
BookNormalizer
BookMetricNormalizer
PositioningNormalizer
BasisNormalizer
```

Each is provider-independent at interface level and provider-aware through versioned semantic mapping/config.

---

## 6. Frozen T1 quality dimensions

```text
identity_quality
time_quality
semantic_quality
unit_quality
lineage_quality
source_integrity_quality
coverage_quality
replay_quality
```

Bloc 6 may aggregate/score them operationally but may not overwrite component truth.

---

## 7. Frozen duplicate strength classes

```text
HARD_PROVIDER_ID
HARD_SEQUENCE_KEY
COMPOSITE_EXACT_KEY
SOFT_FINGERPRINT
NO_SAFE_DEDUPE
```

Duplicate outcome classes:

```text
EXACT_SOURCE_DUPLICATE
SAME_PROVIDER_SAME_EVENT_DIFFERENT_ACQUISITION
REST_ARCHIVE_DUPLICATE
LIVE_ARCHIVE_DUPLICATE
REVISION
POSSIBLE_DUPLICATE
NOT_DUPLICATE
NO_SAFE_DEDUPE_KEY
```

---

## 8. Frozen T1 storage principles

```text
Parquet / Arrow-compatible canonical storage
zstd default compression
immutable published generations
atomic publish
partition manifests
provider/venue identity retained
contract remains a column unless measured volume requires further partitioning
```

DuckDB may query T1 later but is not canonical truth.

---

## 9. Frozen planning history

```text
SENSOR-PLAN-B5A
  PIT identity and instrument lifecycle architecture

SENSOR-PLAN-B5B
  timestamp / revision / market-availability truth

SENSOR-PLAN-B5C
  common unit + semantic normalization contracts

SENSOR-PLAN-B5D
  sensor-specific normalization rules

SENSOR-PLAN-B5E
  T1 lineage / duplicates / quality / storage generations

SENSOR-PLAN-B5F
  acceptance tests + staged implementation commits

SENSOR-PLAN-B5G
  freeze manifest + Bloc 6 handoff
```

---

## 10. Frozen future implementation sequence

```text
SENSOR-B5-I01  normalization enums/base models/T1 envelope
SENSOR-B5-I02  asset/venue/contract identity registries
SENSOR-B5-I03  lifecycle/alias/PIT resolver
SENSOR-B5-I04  contract terms + linear/inverse conversion primitives
SENSOR-B5-I05  time semantics registry/interval conventions
SENSOR-B5-I06  market availability + replay eligibility
SENSOR-B5-I07  revision policies / AS_KNOWN_THEN
SENSOR-B5-I08  units/numeric/stablecoin conversion
SENSOR-B5-I09  methodology + semantic-equivalence registries
SENSOR-B5-I10  trade normalizer + side maps
SENSOR-B5-I11  liquidation normalizer
SENSOR-B5-I12  OI normalizer
SENSOR-B5-I13  funding normalizer
SENSOR-B5-I14  book/book-metric normalizer
SENSOR-B5-I15  positioning/basis normalizers
SENSOR-B5-I16  lineage + deterministic T1 IDs
SENSOR-B5-I17  duplicate/revision engine
SENSOR-B5-I18  T1 generation writer/manifests
SENSOR-B5-I19  canonical T1 query/replay filters
SENSOR-B5-I20  provider golden semantic fixtures
SENSOR-B5-I21  PIT/leakage/property/regression tests
SENSOR-B5-I22  T0→T1 golden replay slice/checksum evidence
SENSOR-B5-I23  acceptance report + Bloc 6 handoff
```

No squashing during staged review.

---

## 11. Blocking implementation gates

```text
IDENTITY_GATE
TIME_GATE
SEMANTIC_GATE
UNIT_GATE
LINEAGE_GATE
DUPLICATE_REVISION_GATE
REPLAY_SAFETY_GATE
GOLDEN_T0_T1_GATE
```

Completion requires:

```text
all gates = PASS
blocking_failures = 0
```

Provider-specific sensors may remain unavailable, but any sensor promoted to T1 must satisfy the contract.

---

## 12. Golden regression requirement

A checksum-pinned end-to-end offline fixture must include at minimum:

- 3 providers;
- BTC + alt;
- linear + inverse contract;
- trade;
- liquidation;
- OI;
- funding;
- book;
- one stablecoin depeg conversion;
- one revision;
- one missing interval;
- one duplicate multi-acquisition event.

Pipeline:

```text
T0 fixture
→ raw normalization batch
→ PIT identity
→ time/availability
→ sensor normalization
→ T1 generation
→ canonical query
→ strict historical replay query
```

This fixture becomes a permanent regression substrate for Blocs 6–12.

---

## 13. Bloc 6 handoff

Bloc 6 designs **Quality / Redundancy / Failover** on top of honest T1 observations.

Inputs available from Bloc 5:

```text
provider
venue
contract identity
sensor family
native + normalized values
semantic-equivalence class
component quality dimensions
quality flags
missing reasons
source revision state
replay eligibility
T0/T1 lineage
partition coverage
provider acquisition evidence
```

Bloc 6 must answer:

1. how is provider health represented?
2. how is sensor health represented independently from provider health?
3. how are stale/late/gapped sources detected?
4. how are provider disagreement and venue dispersion measured?
5. when may a fallback provider maintain a sensor?
6. when must the sensor degrade or fail closed?
7. how are independent-source redundancy levels computed?
8. how are aggregators prevented from being counted as independent confirmation of their underlying venue?
9. how are quality/confidence states propagated into T2?
10. what operational decisions occur under partial coverage?
11. how are schema/semantic/access changes surfaced?
12. how does failover preserve provenance rather than silently substitute truth?

Hard handoff principle:

> Bloc 6 may decide whether evidence is healthy enough to use. It may not rewrite evidence until sources agree.

---

## 14. Completion checklist

- [x] canonical identity layers defined
- [x] contract-instance lifecycle defined
- [x] listing/delisting/relisting semantics defined
- [x] symbol alias/reuse policy defined
- [x] linear/inverse/quanto guardrails defined
- [x] base/quote/settlement/margin separation defined
- [x] stablecoin-vs-fiat rule frozen
- [x] PIT knowledge-time rule defined
- [x] timestamp vocabulary defined
- [x] market-vs-system availability defined
- [x] interval semantics defined
- [x] historical archive/revision policy defined
- [x] common T1 envelope defined
- [x] native-value preservation defined
- [x] methodology registry defined
- [x] semantic-equivalence mapping defined
- [x] trade semantics defined
- [x] liquidation semantics defined
- [x] OI semantics defined
- [x] funding semantics defined
- [x] book semantics defined
- [x] positioning/basis semantics defined
- [x] T1→T0 lineage defined
- [x] duplicate/revision policy defined
- [x] T1 generation/storage rules defined
- [x] canonical research query boundary defined
- [x] golden fixture plan defined
- [x] staged implementation commits defined
- [x] Bloc 6 handoff defined

---

## 15. Final planning verdict

`PASS_BLOC_05_PLAN_FROZEN`

Rationale:

Bloc 5 now provides an implementation-grade PIT normalization architecture that can translate heterogeneous derivatives evidence into canonical T1 observations without destroying provider/venue/contract truth. Identity is lifecycle-aware, timestamps distinguish economic/public/system clocks, revisions remain PIT-safe, native values survive normalization, stablecoin depegs are preserved, sensor semantics are explicit, conversions are methodology/lineage backed, duplicates are conservative, T1 generations are reproducible, and research is forced through a canonical replay-safe query boundary.

`human_review_required = TRUE`
`next_bloc_planning_authorized = FALSE until operator asks for Bloc 6`
