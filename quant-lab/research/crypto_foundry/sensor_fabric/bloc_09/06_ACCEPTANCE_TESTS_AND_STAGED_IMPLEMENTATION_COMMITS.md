# BLOC 9 — ACCEPTANCE TESTS & STAGED IMPLEMENTATION COMMITS

## 1. Purpose

Define the implementation sequence and stop gates for the mechanical observable fabric.

The execution agent must build this bloc in small reviewable commits. No squash until operator review.

---

## 2. Mandatory acceptance domains

### A. Schema / contract

- all seven state families have typed schemas;
- every T2 value carries observable/version/generation;
- physical + normalized values remain distinguishable;
- missing/blocked states are typed;
- quality envelope is present;
- lineage is mandatory.

### B. PIT / temporal

- no future observation enters a window;
- baseline samples are PIT-safe;
- static/rolling horizon labels are unambiguous;
- event-relative windows respect `as_of`;
- historical revisions generate new output generations rather than rewrite silently.

### C. Venue-local semantics

- liquidation side fixtures validated;
- OI stock vs flow semantics preserved;
- funding realized/predicted separation preserved;
- aggressor-side fixtures validated;
- book depth BPS normalization tested;
- positioning/basis methodology IDs preserved.

### D. Cross-venue synthesis

- dependency groups prevent fake redundancy;
- missing venue does not become zero;
- denominator policy is explicit;
- breadth/consensus/dispersion reproduce fixtures;
- high valid dispersion is preserved rather than quarantined;
- notional aggregation is blocked when comparability permission is absent.

### E. Quality gating

- `FULL`, degraded and blocked modes propagate;
- T2 cannot upgrade input quality;
- semantic/PIT/integrity blockers prevent computation;
- partial coverage appears in outputs;
- excluded-source reason is preserved.

### F. Historical/live parity

- batch and incremental computations converge for closed windows;
- restart does not alter outputs;
- late arrival revises only affected windows;
- same observable ID means same semantics in historical and live mode.

### G. Determinism

- same inputs + versions produce checksum-identical or tolerance-equivalent outputs;
- contributor-set hash stable;
- methodology hash stable;
- registry changes force version/generation change where required.

---

## 3. Golden fixtures

Minimum fixture set must include:

```text
BTC
ETH
SOL or another alt

Kraken
Gate
Binance
Bybit
+ OKX/Deribit where available
```

Scenarios:

1. quiet funding/OI period;
2. liquidation burst;
3. broad OI compression;
4. venue-local liquidation event;
5. cross-venue sell-flow consensus;
6. high venue dispersion;
7. liquidity withdrawal/recovery;
8. stablecoin conversion disturbance;
9. one dependent aggregator source;
10. one missing venue;
11. one valid zero;
12. one semantic block;
13. one late-arriving revision;
14. one historical/live equivalence interval.

---

## 4. Adversarial tests

Mandatory:

- provider duplicated through aggregator;
- same source listed twice;
- one source stale but others healthy;
- one source has wrong unit fixture;
- one source uses incompatible liquidation definition;
- OI quote conversion unavailable;
- book sequence gap creates invalid epoch;
- contributor count changes mid-window;
- sparse long-tail asset;
- baseline has insufficient samples;
- cross-venue dispersion extreme but raw inputs valid;
- future row inserted intentionally to verify PIT rejection;
- methodology version altered without observable version bump (must fail).

---

## 5. Performance gates

Bloc 9 is research/runtime infrastructure, so exact thresholds are environment-configurable, but implementation must benchmark:

```text
venue-local batch throughput
cross-venue aggregation throughput
incremental update latency
Parquet scan cost
DuckDB query latency
memory per active live observable
```

No hidden requirement to hold the full historical panel in RAM.

---

## 6. Evidence outputs

Implementation completion packet must include:

```text
observable_registry.json/yaml
baseline_registry.json/yaml
venue_state_schema_report.md
cross_venue_schema_report.md
quality_gate_report.md
golden_fixture_checksums.json
historical_live_parity_report.md
lineage_audit.md
blocked_observable_report.md
performance_report.md
bloc_09_acceptance_summary.md
```

---

## 7. Frozen staged implementation commits

```text
SENSOR-B9-I01
  observable enums/base models

SENSOR-B9-I02
  observable registry + versioning

SENSOR-B9-I03
  baseline registry + PIT windows

SENSOR-B9-I04
  common computation context + lineage

SENSOR-B9-I05
  physical/normalized value contracts

SENSOR-B9-I06
  LiquidationState venue-local

SENSOR-B9-I07
  LeverageState venue-local

SENSOR-B9-I08
  FundingState venue-local

SENSOR-B9-I09
  OrderFlowState venue-local

SENSOR-B9-I10
  LiquidityState venue-local

SENSOR-B9-I11
  PositioningState venue-local

SENSOR-B9-I12
  BasisState venue-local

SENSOR-B9-I13
  static + rolling temporal engine

SENSOR-B9-I14
  state-transition engine

SENSOR-B9-I15
  materiality envelope + distribution helpers

SENSOR-B9-I16
  T2Eligibility / Bloc 6 bridge

SENSOR-B9-I17
  independence-aware breadth engine

SENSOR-B9-I18
  consensus engine

SENSOR-B9-I19
  dispersion/concentration engine

SENSOR-B9-I20
  cross-venue mechanical state schemas

SENSOR-B9-I21
  T2 generation/materialization store

SENSOR-B9-I22
  historical batch compiler

SENSOR-B9-I23
  live incremental compiler

SENSOR-B9-I24
  late-arrival/revision recomputation

SENSOR-B9-I25
  research event-context exporter

SENSOR-B9-I26
  golden/adversarial test suite

SENSOR-B9-I27
  historical/live parity suite

SENSOR-B9-I28
  performance/storage benchmark

SENSOR-B9-I29
  acceptance/evidence packet

SENSOR-B9-I30
  Bloc 10 handoff freeze
```

Each state family gets its own reviewable commit.

---

## 8. Implementation stop gates

### Gate G1 — local states

Do not build cross-venue synthesis until venue-local golden fixtures pass.

### Gate G2 — eligibility

Do not aggregate until Bloc 6 independence/comparability permissions are wired.

### Gate G3 — lineage

Do not materialize runtime T2 if any result lacks T1/T0 lineage.

### Gate G4 — parity

Do not hand to Bloc 10 until historical/live parity passes on closed windows.

### Gate G5 — no strategy contamination

Any direct trade signal, future-return target, PnL optimization or execution logic is blocking scope violation.

---

## 9. Pilot

Before broad runtime promotion, run a bounded T2 pilot over:

```text
BTC / ETH / SOL
2022 stress
2024 ordinary
2026 recent
```

with, where coverage exists:

```text
LiquidationState
LeverageState
FundingState
OrderFlowState
LiquidityState
```

and cross-venue:

```text
LiquidationBreadth
LeverageCompression
FlowConsensus
LiquidityWithdrawalBreadth
FundingConsensus
VenueDispersion
```

Pilot must demonstrate both static horizons and rolling windows.

---

## 10. Completion verdict requirement

Bloc 9 implementation cannot be called complete until all blocking gates pass and the evidence packet exists.

Planning verdict target:

`PASS_BLOC_09_PLAN_FROZEN`
