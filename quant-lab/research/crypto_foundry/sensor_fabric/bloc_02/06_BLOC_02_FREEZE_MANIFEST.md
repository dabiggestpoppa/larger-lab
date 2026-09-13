# BLOC 2 — FREEZE MANIFEST

**Planning status:** COMPLETE  
**Implementation status:** NOT STARTED  
**Purpose:** freeze the capability-probe design so the eventual execution agent can verify provider behavior without silently redesigning the evidence model, historical matrix, failure logic or promotion gates.

---

## 1. Frozen architectural decisions

### F2.1 — Bloc 2 is verification, not ingestion

Bloc 2 proves what providers can deliver.

It does not build full production adapters, raw-lake backfills, canonical T1 transformations or T2 mechanical observables.

### F2.2 — Documentation does not equal capability

Official docs are supporting evidence only.

Runtime/archive probes decide actual accessibility/history/schema behavior.

### F2.3 — Capability is sensor-specific

A provider may be PRIMARY for one sensor and EXCLUDED for another.

No provider-level blanket pass/fail.

### F2.4 — Historical eras are mandatory

Default historical checkpoints:

```text
2021-06-15
2022-06-15
2024-06-15
2026-06-15
RECENT_CONTROL
```

Legitimate pre-listing/pre-history states must be distinguished from missingness/failure.

### F2.5 — Provider-specific evidence remains immutable

Re-running a probe creates new evidence.

Later capability claims may supersede earlier claims but may not erase the underlying evidence.

### F2.6 — Probe dimensions are explicit

Every capability claim is scoped by:

```text
provider
venue/market
sensor
instrument
date/history
granularity
access mode
query mode
```

### F2.7 — Recent-control-first

Deep-history probing should not proceed blindly when the current endpoint/file surface is already hard blocked.

### F2.8 — Historical boundary is verified, not assumed

Store separately:

```text
earliest_claimed_history
earliest_verified_history
```

### F2.9 — Timestamp semantics gate PIT readiness

A provider/sensor cannot become `PIT_READY` when event/effective/publication timestamp meaning is materially ambiguous.

### F2.10 — Native units must be identified

Unknown OI/liquidation/funding units block normalization-ready promotion.

### F2.11 — Liquidation/order-flow/book semantics remain distinct

Do not conflate:

- trade-level liquidation flags,
- interval liquidation totals,
- liquidation event messages,
- vendor aggregates;

or:

- maker flags,
- taker volumes,
- CVD,
- aggressor differential;

or:

- full event L2,
- periodic L2 snapshots,
- N-level snapshots,
- precomputed liquidity metrics.

### F2.12 — Free-only gate is hard

Paid subscription/payment method/staking/transaction requirements cannot be overridden by capability score.

### F2.13 — Geo restrictions are not bypassed

`GEO_BLOCKED` is a real capability status for the intended deployment environment.

### F2.14 — Unit tests are offline

Live provider access is an explicit integration/probe action, not a prerequisite for default tests.

### F2.15 — Failures are evidence

Unsupported/history-limited/payment-blocked/provider-removed outcomes are valid architectural results and must be committed/reported.

### F2.16 — Unattempted is not unsupported

The system must never silently translate missing probe coverage into a negative capability claim.

### F2.17 — Redundancy counts independent evidence

Multiple derived aliases of one upstream venue do not count as multiple independent sources.

### F2.18 — Provider disagreement is preserved for later T2 research

Bloc 2 does not synthesize cross-venue market values.

It preserves provider/venue semantics so later disagreement can itself become an observable.

---

## 2. Frozen provider candidate set

```text
KRAKEN_FUTURES
GATE_FUTURES
BINANCE_USDM
BYBIT_LINEAR
OKX_SWAP
DERIBIT
COINALYZE
BITFINEX_COMMUNITY_ARCHIVE
```

No later execution agent may drop a candidate merely because it seems redundant before probing.

Likewise, no candidate is guaranteed promotion.

---

## 3. Frozen probe sensor families

```text
MECHANICAL_TRADE
MECHANICAL_LIQUIDATION
MECHANICAL_OPEN_INTEREST
MECHANICAL_FUNDING
MECHANICAL_BOOK_SNAPSHOT
MECHANICAL_BOOK_METRIC
MECHANICAL_POSITIONING
MECHANICAL_BASIS
```

Probe only relevant provider/sensor combinations; unsupported combinations remain explicitly characterized.

---

## 4. Frozen minimum instrument strategy

Probe at minimum:

```text
BTC
ETH
SOL
MID_TAIL_CONTROL
```

with provider-native mapping and listing-history evidence.

Purpose is breadth characterization, not identical-asset enforcement across venues.

---

## 5. Frozen capability evidence levels

```text
E0 CLAIM_ONLY
E1 DOC_CONTRACT_VERIFIED
E2 LIVE_RECENT_VERIFIED
E3 HISTORICAL_CHECKPOINT_VERIFIED
E4 MULTI_ERA_VERIFIED
E5 REPRODUCIBLE_COVERAGE_VERIFIED
```

Production-adapter eligibility must be supported by actual evidence level, not optimistic documentation.

---

## 6. Frozen capability statuses

```text
VERIFIED
VERIFIED_LIMITED
VERIFIED_CURRENT_ONLY
VERIFIED_ARCHIVE_ONLY
UNSUPPORTED
ACCESS_BLOCKED
GEO_BLOCKED
AUTH_BLOCKED
PAYMENT_BLOCKED
HISTORY_BLOCKED
SEMANTICALLY_UNUSABLE
TRANSIENT_FAILURE
UNVERIFIED
```

---

## 7. Frozen failure taxonomy families

The implementation must distinguish at least:

```text
access
network/server
endpoint/archive
symbol/listing
history
pagination
schema
semantic timestamp/unit/method
quality/corruption
documentation-runtime contradiction
unsupported
```

Concrete codes are defined in `03_EVIDENCE_SCORING_COVERAGE_AND_FAILURE_TAXONOMY.md`.

---

## 8. Frozen redundancy classes

```text
R0 no verified free source
R1 one independent verified source
R2 two independent verified sources
R3 three or more independent verified sources
```

Critical sensor research should prefer R2+, while high-quality R1 may remain usable with concentration flags when alternatives do not exist.

---

## 9. Frozen expected redundancy targets

Initial target architecture to verify, not assume:

```text
LIQUIDATIONS
  Kraken / Gate
  + Deribit microscope
  + Coinalyze / Bitfinex corroboration

OI
  Bybit / Gate / Kraken
  + Binance / Coinalyze

FUNDING
  Bybit / Kraken / Gate
  + Binance / OKX / Deribit / Coinalyze

ORDER FLOW
  Binance / Kraken
  + Gate / Bybit / OKX

DEPTH / LIQUIDITY
  OKX / Kraken
  + Binance secondary
```

The implemented result may legitimately differ after probes.

---

## 10. Frozen provider strategic expectations

These are hypotheses for probe prioritization only:

```text
KRAKEN
  broad mechanical analytics candidate

GATE
  liquidation/OI/taker statistics candidate

BINANCE
  trade/aggressor historical backbone; liquidation history uncertain

BYBIT
  OI/funding/trade independent backbone

OKX
  historical book/liquidity candidate

DERIBIT
  trade-level liquidation mechanism microscope

COINALYZE
  free limited aggregator/corroborator

BITFINEX COMMUNITY ARCHIVE
  historical liquidation replication/corroboration
```

No expectation may be promoted to fact without runtime evidence.

---

## 11. Frozen outputs

Bloc 2 implementation must eventually produce machine and human outputs equivalent to:

```text
provider_coverage_matrix.parquet/csv
provider_capability_claims.jsonl
probe_evidence.jsonl
probe_failures.jsonl
provider_coverage_report.md
sensor_gap_matrix.csv
source_promotion_candidates.yaml
free_only_audit.csv
PIT_readiness_matrix.csv
history_boundaries.csv
schema_fingerprints.jsonl
blocking_contradictions.csv
```

---

## 12. Frozen implementation commit sequence

```text
SENSOR-B2-I01 probe-core-models
SENSOR-B2-I02 probe-planner-and-runner
SENSOR-B2-I03 probe-evidence-and-coverage
SENSOR-B2-I04 kraken-capability-probe
SENSOR-B2-I05 gate-capability-probe
SENSOR-B2-I06 binance-capability-probe
SENSOR-B2-I07 bybit-capability-probe
SENSOR-B2-I08 okx-capability-probe
SENSOR-B2-I09 deribit-capability-probe
SENSOR-B2-I10 coinalyze-capability-probe
SENSOR-B2-I11 bitfinex-archive-capability-probe
SENSOR-B2-I12 report-and-gap-matrix
SENSOR-B2-I13 live-capability-evidence-run
SENSOR-B2-I14 provider-role-decision-packet
```

Do not squash provider probes into one implementation commit.

---

## 13. Frozen planning commit sequence

```text
SENSOR-PLAN-B2A
  capability probe architecture

SENSOR-PLAN-B2B
  provider-specific playbook

SENSOR-PLAN-B2C
  evidence/scoring/coverage/failure taxonomy

SENSOR-PLAN-B2D
  acceptance gates/tests/staged commits

SENSOR-PLAN-B2E
  output templates

SENSOR-PLAN-B2F
  freeze manifest
```

---

## 14. Completion checklist

Planning questions answered:

- [x] What exactly does Bloc 2 verify?
- [x] Which providers are probed?
- [x] Which sensors are probed?
- [x] Which instruments are sampled?
- [x] Which historical dates are mandatory?
- [x] How is recent/current capability distinguished from history?
- [x] How is earliest history verified?
- [x] How are gaps sampled?
- [x] How are pagination/archive behaviors tested?
- [x] How are timestamp semantics audited?
- [x] How are native units audited?
- [x] How are liquidation/order-flow/book semantics distinguished?
- [x] How are access/auth/payment/geo states classified?
- [x] How are failures represented?
- [x] What counts as evidence?
- [x] How is capability scored?
- [x] What hard blockers override scoring?
- [x] How is PIT readiness classified?
- [x] How is provider redundancy calculated?
- [x] How are community/aggregator sources distinguished from first party?
- [x] How are documentation/runtime contradictions preserved?
- [x] What reports are generated?
- [x] What tests must pass?
- [x] What staged commits must implementation use?
- [x] What exactly may enter Bloc 3?

---

## 15. Handoff to Bloc 3 planning

Bloc 3 will design the **production provider adapter framework and provider adapter books**.

Bloc 3 planning must assume capability results will arrive as machine-readable claims rather than hard-coded provider expectations.

Every production adapter will inherit:

```text
provider/sensor role
verified access mode
earliest verified history
granularity scope
instrument scope
PIT readiness
native timestamp semantics
native units
pagination/archive method
known gaps/failures
semantic equivalence class
rate-limit behavior
free-only status
```

Bloc 3 must not bypass these inputs.

---

## 16. Final planning decision

`PASS_BLOC_02_PLAN_FROZEN`

Rationale:

Bloc 2 now has a provider-independent probe architecture, detailed provider playbooks, historical matrix, evidence hierarchy, failure taxonomy, coverage/redundancy logic, PIT and free-only gates, output contracts, offline test strategy, granular implementation commits and a strict production-adapter handoff.

The future build agent can execute capability verification without inventing the methodology while it works.

`human_review_required = TRUE`
`next_bloc_planning_authorized = FALSE until operator asks for Bloc 3`
