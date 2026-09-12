# BLOC 5 — ACCEPTANCE TESTS & STAGED IMPLEMENTATION COMMITS

**Planning status:** COMPLETE DRAFT FOR FREEZE  
**Implementation status:** NOT STARTED  
**Purpose:** define the execution plan that proves PIT identity, timing, semantic normalization, unit conversion, lineage, duplicate handling, and T1 reproducibility before Bloc 6 may consume canonical observations.

---

## 1. Blocking acceptance gates

Bloc 5 implementation cannot pass unless all blocking gates succeed.

### G1 — PIT identity

- every normalized row resolves to a valid contract instance;
- no future alias/terms knowledge leaks backward;
- listing/delisting/relisting states are handled explicitly;
- symbol reuse cannot collapse separate economic contract instances;
- quote/settlement/margin identity remains separate.

### G2 — Timestamp truth

- UTC/timezone-aware canonical times;
- provider interval semantics are explicit;
- completed interval data cannot become available before interval close without evidence;
- market availability and system ingestion remain separate;
- strict replay blocks unknown availability.

### G3 — Native-value preservation

- provider-native value/unit are always retained;
- normalization adds fields rather than replacing native evidence;
- stablecoins are not silently pegged to USD.

### G4 — Sensor semantics

- trade aggressor side is provider-semantics based;
- liquidation position side differs from execution side;
- OI is treated as stock/snapshot;
- predicted funding differs from realized funding;
- book deltas cannot claim full snapshot without valid reconstruction;
- positioning/basis definitions remain explicit.

### G5 — Unit conversion

- linear/inverse contract terms drive formulas;
- PIT-valid reference prices are required where mathematically necessary;
- blocked conversion yields NULL + reason, never guessed value;
- every derived amount has methodology + input lineage.

### G6 — T1 lineage

Every canonical row resolves to:

```text
T1 → T0B/raw batch → AcquisitionRecord → T0A EvidenceBlob SHA256
```

No broken lineage.

### G7 — Duplicates/revisions

- cross-venue data is not deduped;
- hard provider IDs may collapse same venue event from multiple acquisition paths;
- soft fingerprints only flag candidates;
- revisions append and remain queryable;
- `AS_KNOWN_THEN` differs from `LATEST_VERIFIED` where appropriate.

### G8 — Reproducibility

Identical T0 manifests + code + registry + methodology + revision policy must produce deterministic T1 data/checksums.

### G9 — Fail-closed

Unknown identity, semantics, units, timing, or lineage must not silently become canonical verified data.

---

## 2. Test layers

Use six layers.

```text
N0 MODEL / SCHEMA
N1 PURE NORMALIZATION
N2 PROVIDER SEMANTIC FIXTURES
N3 PIT / LIFECYCLE / REVISION
N4 T0→T1 INTEGRATION
N5 RESEARCH-QUERY / REPLAY SAFETY
```

Normal CI remains network-free.

---

## 3. N0 model/schema tests

Required:

- enum serialization round trip;
- Pydantic model validation;
- Arrow schema compatibility;
- nullable-field correctness;
- Decimal precision preservation;
- timestamp timezone enforcement;
- unknown enum handling fails explicitly;
- methodology/registry versions required where derived fields exist.

Property tests should include impossible combinations such as:

```text
payoff_type=INVERSE with missing contract terms for converted exposure
normalization_status=NORMALIZED with missing lineage
replay_eligibility=ELIGIBLE with market_available_at unknown
```

These must fail validation.

---

## 4. Identity fixture matrix

Minimum golden identity cases:

### Linear USDT perpetual

- BTC/ETH/SOL examples;
- base/quote/settlement verified;
- multiplier changes if available in fixtures.

### Inverse perpetual/future

- price-dependent exposure conversion;
- settlement in base asset;
- exact terms version.

### Alias cases

- `BTC` vs `XBT` documented alias;
- archive symbol differing from API symbol;
- provider-internal ID present/absent.

### Lifecycle boundaries

- just before listing;
- at listing;
- active;
- suspended if fixture exists;
- delisting boundary;
- post-delisting;
- relisting as new contract instance.

### Symbol reuse

Synthetic fixture where same string symbol maps to two non-overlapping contract instances with changed multiplier/settlement.

A current map projected backward must fail.

---

## 5. Provider semantic fixture matrix

Every provider adapter implemented in Bloc 3 must eventually contribute fixture payloads for verified sensors.

Required provider set:

```text
Kraken Futures
Gate Futures
Binance USD-M
Bybit Linear
OKX Swap
Deribit
Coinalyze
Bitfinex community archive
```

Fixture policy:

- raw fixture copied from verified source evidence or minimized without semantic mutation;
- fixture provenance documented;
- sensitive/private credentials excluded;
- expected canonical output checked exactly;
- unsupported sensor explicitly skipped with capability reason, not empty expected output.

---

## 6. Trade tests

Required:

- Binance `isBuyerMaker=true` -> SELL aggressor;
- `isBuyerMaker=false` -> BUY aggressor;
- unknown side remains UNKNOWN;
- provider trade ID preserved;
- quantity native preserved;
- base/notional conversion correct for verified contract;
- same hard trade ID from REST + archive collapses to one economic T1 event with multiple lineage refs;
- different venues with same timestamp/price/qty remain distinct.

---

## 7. Liquidation tests

Required:

- long-liquidated position remains LONG while execution side can be SELL;
- short-liquidated position remains SHORT while execution side can be BUY;
- Deribit maker/taker liquidation role retained;
- interval aggregate differs from trade-level event;
- verified zero interval allowed only when source interval semantics support it;
- missing interval never becomes zero;
- USD conversion respects quote/stablecoin semantics;
- aggregate source cannot masquerade as trade-level count.

---

## 8. OI tests

Required:

- contracts vs base vs quote vs USD native units distinguished;
- linear conversion uses correct contract size;
- inverse conversion uses reference price + contract terms;
- missing price blocks derived exposure but retains native OI;
- point snapshot differs from interval average/last;
- OI decrease is not emitted as liquidation or flow by normalization;
- aggregator multi-venue OI is not assigned to one venue.

---

## 9. Funding tests

Required:

- native funding rate retained;
- interval duration retained;
- 8h simple equivalent works for verified intervals;
- predicted funding remains PREDICTED;
- realized remains REALIZED;
- publication time can precede effective time;
- unknown interval blocks normalized equivalent;
- simple vs compounded methodology IDs cannot be confused.

---

## 10. Book tests

Required:

- full snapshot validates;
- partial snapshot remains partial;
- delta update cannot become standalone full book;
- valid sequence rebuild succeeds;
- missing sequence produces `BOOK_SEQUENCE_GAP` and stops reconstruction;
- bid/ask side preserved;
- native level qty preserved;
- inverse/linear quantity conversion follows terms;
- provider-native spread/liquidity metric does not silently become Fabric-defined common metric.

---

## 11. Positioning/basis tests

Positioning:

- top-trader account ratio differs from top-trader position ratio;
- population scope required;
- unknown population prevents exact cross-provider equivalence.

Basis:

- raw percentage vs annualized percentage remain distinct;
- spot/futures reference identities preserved;
- expiry retained for delivery contracts;
- annualization methodology required when derived.

---

## 12. Stablecoin depeg tests

Synthetic PIT fixture:

```text
USDT/USD = 0.97 at t
```

Verify:

- 1,000 USDT native notional remains 1,000 USDT;
- optional USD equivalent becomes 970 USD under registered PIT conversion;
- no hardcoded 1:1 conversion overwrites the observation;
- replay at time before conversion observation exists cannot use later 0.97 value.

This is blocking because depeg periods may be scientifically important.

---

## 13. Timestamp/replay tests

Required:

- 5m interval timestamped at start cannot be made available at start if value needs complete interval;
- archive row obtained in 2026 but proven contemporaneously public in 2022 can be tagged `HISTORICAL_ARCHIVE_RECONSTRUCTION`;
- late 2025 correction of 2022 value does not enter 2022 `AS_KNOWN_THEN` replay;
- latest retrospective mode may select it explicitly;
- unknown market availability blocks strict replay;
- system ingestion and market availability never collapse accidentally.

---

## 14. Duplicate/revision tests

Scenarios:

1. identical REST + archive hard event ID;
2. identical live + archive event;
3. same soft fingerprint but distinct provider IDs;
4. same request boundary with later changed source bytes;
5. provider-corrected event;
6. normalization methodology rebuild.

Expected:

- hard duplicates unify economically while retaining all lineage;
- soft candidate remains two rows + flag;
- revision creates chain;
- normalization rebuild creates new generation, not source revision.

---

## 15. Property/invariant tests

Use randomized/property tests for:

- lifecycle intervals never overlap for exact same provider instrument unless ambiguity explicitly represented;
- `valid_from < valid_to`;
- known-time rules prevent future mappings;
- native value unchanged through normalization;
- conversion round-trip tolerance where mathematically meaningful;
- null remains null;
- zero remains zero;
- stablecoin conversion source time <= replay cutoff;
- no cross-venue dedupe;
- deterministic T1 ID/generation checksums.

---

## 16. Golden replay slice

Create a small end-to-end offline fixture dataset containing:

- at least 3 providers;
- BTC + one alt;
- trade;
- liquidation;
- OI;
- funding;
- one book snapshot;
- one revision;
- one missing interval;
- one stablecoin conversion case;
- one inverse contract case.

Pipeline:

```text
T0A/T0B fixture
→ RawNormalizationBatch
→ identity
→ time semantics
→ sensor normalization
→ T1 partition
→ T1 query
→ strict replay query
```

Expected output is checksum-pinned.

This becomes a core regression fixture for later blocs.

---

## 17. Evidence outputs

Implementation must generate:

```text
bloc_05_identity_validation.json
bloc_05_time_validation.json
bloc_05_semantic_validation.json
bloc_05_unit_validation.json
bloc_05_lineage_validation.json
bloc_05_duplicate_revision_validation.json
bloc_05_replay_safety_validation.json
bloc_05_acceptance_summary.md
```

Plus T1 generation manifests for the golden fixture.

---

## 18. Planned implementation tree

```text
quant-lab/src/crypto_sensor_fabric/normalization/
  identity/
  time/
  common/
  sensors/
  lineage/
  duplicates/
  quality/
  storage/
  query/

quant-lab/config/crypto_sensor_fabric/
  asset_registry.yaml
  venue_registry.yaml
  identity_registry.yaml
  provider_time_semantics.yaml
  provider_semantics/
  methodology_registry.yaml
  revision_policies.yaml

quant-lab/tests/crypto_sensor_fabric/normalization/
  fixtures/
  test_identity_*.py
  test_time_*.py
  test_trade_*.py
  test_liquidation_*.py
  test_oi_*.py
  test_funding_*.py
  test_book_*.py
  test_positioning_basis_*.py
  test_duplicates_revisions.py
  test_lineage.py
  test_replay_gate.py
  test_end_to_end_golden.py
```

---

## 19. Staged implementation commits

The execution agent must implement Bloc 5 in reviewable commits.

```text
SENSOR-B5-I01
  normalization enums/base models/T1 envelope

SENSOR-B5-I02
  asset/venue/contract identity models + registries

SENSOR-B5-I03
  lifecycle/alias/PIT identity resolver

SENSOR-B5-I04
  contract terms + linear/inverse conversion primitives

SENSOR-B5-I05
  time semantics registry + interval conventions

SENSOR-B5-I06
  market-availability derivation + replay eligibility

SENSOR-B5-I07
  revision policies / AS_KNOWN_THEN handling

SENSOR-B5-I08
  common units / numeric / stablecoin conversion framework

SENSOR-B5-I09
  methodology + semantic-equivalence registries

SENSOR-B5-I10
  trade normalizer + provider side maps

SENSOR-B5-I11
  liquidation normalizer

SENSOR-B5-I12
  OI normalizer

SENSOR-B5-I13
  funding normalizer

SENSOR-B5-I14
  book/book-metric normalizer + sequence guardrails

SENSOR-B5-I15
  positioning + basis normalizers

SENSOR-B5-I16
  lineage + deterministic T1 IDs

SENSOR-B5-I17
  duplicate/revision engine

SENSOR-B5-I18
  T1 generation writer/manifests/atomic publish

SENSOR-B5-I19
  canonical T1 query + strict research/replay filters

SENSOR-B5-I20
  provider golden semantic fixtures

SENSOR-B5-I21
  PIT/leakage/property/regression tests

SENSOR-B5-I22
  T0→T1 golden replay slice + checksum evidence

SENSOR-B5-I23
  acceptance report + Bloc 6 handoff
```

No squashing during staged review.

---

## 20. Commit review expectations

After each implementation commit:

- unit tests for touched module pass;
- no unrelated provider/research changes;
- fixtures added with provenance;
- no direct provider field names leaked into research code;
- no paid data dependency introduced;
- no T0 mutation.

Large provider semantic fixture additions should remain separate from core model commits where practical.

---

## 21. Stop gate before Bloc 6 implementation

Bloc 5 is ready for handoff only when:

```text
IDENTITY_GATE = PASS
TIME_GATE = PASS
SEMANTIC_GATE = PASS
UNIT_GATE = PASS
LINEAGE_GATE = PASS
DUPLICATE_REVISION_GATE = PASS
REPLAY_SAFETY_GATE = PASS
GOLDEN_T0_T1_GATE = PASS
```

And:

```text
blocking_failures = 0
```

Partial provider capabilities may remain, but any available normalized sensor must satisfy the canonical contract.

---

## 22. Bloc 6 handoff requirements

Bloc 6 — Quality / Redundancy / Failover receives:

- T1 canonical query interface;
- component quality dimensions;
- provider/venue/source identity;
- semantic equivalence classes;
- replay eligibility;
- missing reasons;
- provider acquisition/coverage evidence;
- T1 partition manifests;
- source disagreement candidates;
- revision state.

Bloc 6 may score/compare source quality and build sensor-health/failover logic.

Bloc 6 may **not** rewrite T1 semantics to force agreement.

---

## 23. Final implementation principle

> If two sources disagree after honest normalization, preserve the disagreement. Do not normalize harder until they agree.

That disagreement may be data quality, venue-specific mechanics, timing, or real market structure. Bloc 6 decides how it affects sensor health; later research may treat disagreement itself as information.
