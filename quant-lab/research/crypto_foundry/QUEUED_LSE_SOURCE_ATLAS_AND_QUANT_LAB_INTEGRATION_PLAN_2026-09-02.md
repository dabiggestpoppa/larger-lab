# QUEUED — London Strategic Edge Source Atlas + Quant Lab Integration Plan

**Date:** 2026-09-02  
**Branch:** `agent/crypto-quant-foundry`  
**Status:** QUEUED / PLANNING ONLY  
**Implementation authorized:** NO  
**Crypto Sensor Fabric impact:** NONE — current crypto work continues unchanged  
**Purpose:** preserve a disciplined plan for evaluating London Strategic Edge (LSE) as a future external multi-asset evidence / parity / research source for Quant Lab without contaminating the active Crypto Sensor Fabric build.

---

## 0. Executive decision

London Strategic Edge is potentially valuable to Quant Lab because it exposes one surface spanning market prices, options/Greeks, futures, FX, crypto, sovereign yields, macro series, COT/corporate datasets, REST history, downloadable files, WebSocket data, backtesting and ML tooling.

It must **not** be treated as canonical market truth merely because the catalogue is broad or the platform is convenient.

The correct role is:

```text
LSE = EXTERNAL SOURCE / REFERENCE / PARITY / RESEARCH VENUE
QUANT LAB = CANONICAL RESEARCH + EVIDENCE AUTHORITY
```

The plan is therefore to characterize LSE with the same evidence-first discipline used in the Crypto Sensor Fabric:

```text
DISCOVER
→ CHARACTERIZE
→ PROBE
→ PRESERVE RAW EVIDENCE
→ TEST TIME / UNIT / REVISION SEMANTICS
→ TEST PIT SUITABILITY
→ CLASSIFY SOURCE ROLE
→ RUN PARITY STUDIES
→ ONLY THEN CONSIDER PROMOTION
```

No LSE-derived field automatically enters CEREBUS, Crypto OS, OCE, QCAE, Strategy Foundry, or any production model.

---

# 1. Why this belongs on `agent/crypto-quant-foundry`

This is intentionally placed on the existing Foundry research/doctrine branch rather than the active sensor-build branch.

Reason:

- the current crypto sensor branch is implementation truth and must remain focused;
- this LSE work is a **future research-source atlas**, not an active provider adapter;
- Foundry already contains queued research ideas, modeling doctrine, Market OS plans and external-source framing;
- no new branch is needed;
- no current crypto checkpoint is changed.

This file is a queued research asset only.

---

# 2. Current public LSE claims to characterize later

The following are **vendor/public-site claims**, not Quant Lab validated facts.

Current public pages advertise some combination of:

- downloadable Parquet / CSV datasets;
- REST historical market-data endpoints;
- a Python client (`lse-data`);
- WebSocket live streaming;
- stocks;
- FX;
- crypto;
- futures;
- ETFs;
- commodities;
- indices;
- options records / chains with implied volatility and Greeks;
- sovereign bond yields;
- macroeconomic series;
- COT / positioning data;
- insider trades;
- dividends;
- stock splits;
- company profiles / fundamentals;
- economic calendar data;
- live charts;
- backtesting;
- ML tooling.

Published scale counts differ across LSE pages, which is itself a reason to treat catalogue metadata as something to characterize rather than assume.

Public references captured for future research:

- https://www.londonstrategicedge.com/
- https://www.londonstrategicedge.com/terminal/
- https://londonstrategicedge.com/free-market-data-api/
- https://londonstrategicedge.com/datasets/economic-calendar
- https://londonstrategicedge.com/philosophy/

Do not freeze vendor catalogue counts into Quant Lab doctrine until measured from source/API metadata at characterization time.

---

# 3. Strategic role inside Quant Lab

LSE should be evaluated for four distinct roles.

## ROLE A — External evidence provider

Potential use:

- historical candles;
- raw/tick series where actually exposed;
- options / IV / Greeks;
- futures;
- rates / yields;
- macro;
- COT / positioning;
- corporate / alternative data.

This role requires source-specific provenance and raw evidence preservation.

## ROLE B — Cross-market field expansion

Potential use for future Quant Lab state research:

```text
FX
+ commodities
+ rates
+ equity indices
+ futures
+ volatility
+ options
+ macro
+ positioning
→ multi-asset constraint-field research
```

Examples:

- EURUSD conditioned on DXY + sovereign/rate curve + ES/NQ + oil + vol;
- oil / CAD / energy-equity constraint relationships;
- volatility/skew conditioning on CEREBUS structural states;
- macro publication-state conditioning;
- cross-asset stress and liquidity propagation;
- quarter-to-quarter regime work.

This is future research, not a signal authorization.

## ROLE C — Independent parity / falsification venue

Quant Lab result:

```text
internal dataset / engine result
→ reproduce on LSE data if semantically comparable
→ compare
```

Possible classifications:

- PARITY_CONFIRMED
- PARITY_APPROXIMATE
- SOURCE_SEMANTICS_DIFFER
- COVERAGE_DIFFERENCE
- TIMESTAMP_DIFFERENCE
- REVISION_DIFFERENCE
- NOT_COMPARABLE
- DATA_BLOCKED

LSE disagreement is an investigation trigger, not an automatic replacement of Quant Lab truth.

## ROLE D — Convenience research environment

LSE backtesting / ML / terminal tools may be used for fast independent experimentation or parity checks.

They are **not** canonical Strategy Foundry authority.

No production strategy should depend on an opaque platform-only result without raw/reproducible Quant Lab evidence.

---

# 4. Non-goals

This plan does NOT authorize:

- replacing current Crypto Sensor Fabric providers;
- adding LSE to the current 17-path crypto production matrix;
- modifying Bloc 4 T0 implementation;
- pausing current crypto work;
- trusting LSE backtests as canonical;
- importing platform ML predictions as alpha;
- downloading the whole advertised archive;
- building a generic 500-TB warehouse;
- paying for infrastructure to mirror the entire service;
- using LSE as execution venue truth;
- routing orders through LSE;
- using LSE marketing statistics as research facts.

---

# 5. Governing doctrine

The future LSE program inherits core Quant Lab doctrine:

1. **Source is evidence, not truth.**
2. **Provider identity survives normalization.**
3. **Raw evidence precedes semantic interpretation.**
4. **No present-universe leakage.**
5. **No silent revision selection.**
6. **Ingestion time != market-known time.**
7. **Missing != zero.**
8. **Coverage != integrity.**
9. **Vendor-derived Greeks / fields require methodology characterization.**
10. **Correlation is not mechanism.**
11. **External parity is falsification evidence, not authority transfer.**
12. **CEREBUS / Quant Lab canonical logic remains internal.**

---

# 6. Proposed future work program

## PHASE LSE-0 — Source Atlas

Goal: map the real surface before any integration.

Deliverables:

- `LSE_SOURCE_ATLAS.md`
- `LSE_DATASET_FAMILY_MATRIX.csv`
- `LSE_ACCESS_AND_LIMITS.md`
- `LSE_OPEN_QUESTIONS.md`

For each advertised family capture:

- dataset family;
- asset class;
- sample instruments;
- delivery surface: file / REST / websocket / terminal-only;
- public/free/auth requirement;
- requested resolution;
- observed resolution;
- claimed history start;
- observed history start;
- fields;
- timestamp columns;
- vendor metadata;
- pagination;
- revision behavior if documented;
- source/provider attribution if exposed;
- license/use constraints;
- export limits;
- update cadence;
- preliminary Quant Lab value.

No promotion decisions in LSE-0.

---

## PHASE LSE-1 — Capability Probe Harness

Build a **small future probe only**, modeled after Sensor Fabric capability characterization.

Probe candidate families:

### Market core
- EUR/USD
- DXY or closest supported currency-index equivalent
- crude oil / energy future or commodity series
- ES / S&P proxy/future
- NQ / Nasdaq proxy/future
- BTC/USD only as cross-domain validation

### Rates
- US 2Y
- US 10Y
- selected European sovereign yields

### Volatility/options
- SPX/SPY or equivalent option-family sample
- IV
- Greeks
- expiration/strike metadata

### Macro/positioning
- economic-calendar sample
- one macro series with revisions if available
- one COT series

Probe MUST capture exact raw response/file bytes where technically possible.

---

# 7. Characterization questions

Every promoted LSE family must answer these before use.

## Identity

- What exact instrument does the symbol represent?
- Spot, CFD, future, continuous future, synthetic, exchange print or vendor composite?
- Venue-specific or consolidated?
- What timezone does the native series use?
- Are symbols stable through history?

## Time

- What does timestamp mean?
- exchange event time?
- aggregation close time?
- publication time?
- vendor observation time?
- file generation time?
- ingestion time?

## Price / market fields

- trade or quote?
- last / mid / bid / ask?
- adjustment policy?
- futures roll policy?
- corporate-action adjustment?
- volume units?

## Options

- raw exchange print or vendor reconstruction?
- Greeks methodology?
- interest-rate source?
- dividend assumptions?
- implied-vol solver?
- American/European model?
- quote-side choice?
- stale-quote treatment?

Vendor-computed Greeks may be stored as native evidence but must not silently become Quant Lab canonical Greeks.

## Macro

- first release vs revised history?
- vintage data available?
- publication timestamp available?
- historical revisions overwritten?

## COT / positioning

- report date vs publication date?
- category definitions?
- revision policy?

## History

- literal earliest observation?
- retention gap?
- missing intervals?
- survivorship?
- delisted symbols retained?

---

# 8. PIT safety program

LSE can be useful only if historical research does not accidentally see information unavailable at the historical decision time.

Required classifications:

```text
PIT_SAFE_DIRECT
PIT_SAFE_WITH_PUBLICATION_LAG
PIT_SAFE_WITH_VINTAGE_SELECTION
NOT_PIT_SAFE_AS_PROVIDED
PIT_UNRESOLVED
```

Particular attention:

- economic data revisions;
- fundamentals;
- corporate actions;
- insider trades;
- COT publication lag;
- options-derived analytics;
- continuous futures;
- instrument universe membership.

No macro/fundamental dataset may be assumed PIT-safe merely because it contains historical timestamps.

---

# 9. Initial priority matrix

## PRIORITY 0 — Highest immediate Quant Lab value

1. FX historical data
2. futures / commodities
3. indices
4. sovereign yields / rates
5. macro series
6. COT

Reason:

These directly extend CEREBUS / cross-market constraint research without immediately requiring complex option methodology reconstruction.

## PRIORITY 1 — High upside

1. options records
2. implied volatility
3. Greeks
4. options chains
5. volatility surface reconstruction

Reason:

Potentially high value for convexity/stress/regime work, but semantic risk is higher.

## PRIORITY 2 — Corporate/alternative

1. fundamentals
2. insider activity
3. dividends/splits
4. corporate profiles
5. economic calendar

Use only after PIT semantics are characterized.

## PRIORITY 3 — Platform parity tools

1. LSE backtester
2. LSE ML studio
3. terminal visualization

These are verification/convenience surfaces, not canonical research engines.

---

# 10. Proposed Quant Data Fabric architecture

Do NOT modify active Crypto Sensor Fabric for this now.

Longer-term abstraction:

```text
                    MULTI-ASSET SOURCES
                           │
          ┌────────────────┼────────────────┐
          │                │                │
     LSE / files       direct APIs      archives
          │                │                │
          └────────────────┼────────────────┘
                           ↓
                 PROVIDER-SPECIFIC ADAPTERS
                           ↓
                 IMMUTABLE SOURCE EVIDENCE
                           ↓
                  PIT / IDENTITY / SEMANTICS
                           ↓
                   QUANT DATA FABRIC
                           ↓
        ┌──────────────────┼───────────────────┐
        ↓                  ↓                   ↓
     CEREBUS         STRATEGY FOUNDRY        QCAE/OCE
 constraint fields      research/parity      agents/tools
```

The current Crypto Sensor Fabric should be treated as the first specialized implementation whose contracts may later inspire this generalized multi-asset fabric.

No generalization should happen until Crypto Sensor Fabric reaches a stable handoff.

---

# 11. Future adapter role

If LSE passes characterization, its adapter should preserve:

- source family;
- original URL/file/API method;
- dataset identifier;
- native instrument;
- asset class;
- exact source bytes where possible;
- request fingerprint;
- native field names;
- timestamp units/semantics;
- dataset/version metadata;
- retrieval time;
- access tier;
- pagination/file boundaries;
- provider/source attribution;
- revision state;
- raw source checksum;
- parser version.

LSE-specific fields must not leak above the adapter before normalization.

---

# 12. Source role classifications

Each LSE dataset family ultimately receives one role:

```text
PRIMARY_EXTERNAL_REFERENCE
SECONDARY_EXTERNAL_REFERENCE
PARITY_ONLY
MECHANISM_MICROSCOPE
CURRENT_ONLY
HISTORICAL_ONLY
RESEARCH_CONVENIENCE_ONLY
EXCLUDED
DATA_BLOCKED
```

These are future evaluation roles, not current promotions.

---

# 13. Cross-source parity experiments

After characterization, high-value parity tests include:

## FX

- OHLC equality/tolerance vs existing Quant Lab FX datasets;
- missing-bar comparison;
- timestamp boundary comparison;
- weekend/session handling;
- spread/quote methodology where present.

## Futures / commodities

- contract-specific vs continuous series;
- roll-date differences;
- back-adjustment differences;
- volume/open-interest semantics.

## Rates

- yield-level parity vs authoritative public sources;
- maturity mapping;
- observation/publication timing.

## Macro

- latest history vs historical vintage;
- revision drift;
- release timestamp parity.

## Options

- option price/quote parity;
- IV parity;
- Greek parity;
- surface topology parity;
- methodology sensitivity.

Disagreement must be stored, not averaged away.

---

# 14. CEREBUS use cases to test later

Potential research questions only:

- Do CEREBUS FX structural states condition differently under rate-curve expansion/compression?
- Does oil geometry change under energy-volatility / futures-curve states?
- Are DT→AR transitions conditioned by DXY/yield/volatility constraint state?
- Do rekey success/failure frequencies vary by macro publication regime?
- Can options skew/IV identify distinct constraint ceilings without becoming a directional predictor?
- Can COT / macro states explain survival/decay of larger multi-day structures?
- Do cross-asset disagreement states expose transitions before price-only state geometry changes?

Manual-first rule remains: external variables may condition or explain CEREBUS states; they do not replace the CEREBUS structural framework without explicit research evidence.

---

# 15. QCAE use case

QCAE may eventually use the LSE catalogue as one discovery target for reusable data capability.

Possible future QCAE tasks:

- discover newly added dataset families;
- compare LSE coverage with internal missing-sensor registry;
- generate capability probes;
- detect documentation/schema drift;
- surface candidate datasets to operator;
- maintain source atlas freshness.

QCAE must never auto-promote LSE fields into canonical science.

Promotion remains evidence-gated.

---

# 16. OCE use case

OCE may eventually operate LSE ingestion/research jobs after a future Quant Data Fabric exists.

Potential role:

- schedule data pulls;
- invoke characterization jobs;
- store evidence;
- monitor source health;
- launch parity experiments;
- summarize source drift;
- enforce cost/access ceilings.

OCE does not gain trading authority from LSE integration.

---

# 17. Cost / resource doctrine

Initial LSE work should remain free/local-first where possible.

Rules:

- do not bulk mirror the entire archive;
- acquire only question-relevant slices;
- estimate storage before large downloads;
- preserve high-value/raw evidence first;
- prefer reproducible sample panels during characterization;
- no recurring paid dependency without operator approval;
- no cloud expansion solely because vendor advertises huge archive scale.

Large advertised archive size is not a reason to ingest everything.

---

# 18. Licensing / terms gate

Before automated large-scale acquisition, future implementation must explicitly review:

- API terms;
- redistribution rights;
- local archival rights;
- automated-download limits;
- commercial-use limits;
- attribution requirements;
- derived-data rights.

Classification:

```text
LICENSE_CLEAR
LICENSE_CLEAR_WITH_ATTRIBUTION
LICENSE_RESTRICTED
LICENSE_UNRESOLVED
```

`LICENSE_UNRESOLVED` blocks bulk ingestion.

---

# 19. Security / credentials

If an API key is required:

- environment/secret store only;
- never commit literal key;
- no key in logs;
- no key in evidence;
- no key in fixtures;
- sanitized request metadata only.

No broker/private-account credentials are required for source characterization.

---

# 20. Acceptance criteria for future promotion

An LSE family may become a Quant Lab promoted external source only if:

- identity characterized;
- literal history bounds measured;
- timestamps characterized;
- units characterized;
- pagination/file semantics characterized;
- revision behavior characterized or explicitly unresolved;
- PIT state classified;
- raw evidence preserved;
- schema drift handling exists;
- missingness explicit;
- source limitations documented;
- licensing acceptable;
- access/cost acceptable;
- parity result known where a reference exists;
- provider/source provenance preserved;
- no canonical semantics invented in adapter.

No single convenience/API-success result is sufficient.

---

# 21. Proposed future commit sequence

Do not execute now.

```text
LSE-QDF-00
freeze source-atlas charter and authority boundaries

LSE-QDF-01
catalogue public dataset families + access surfaces

LSE-QDF-02
build read-only capability probe harness

LSE-QDF-03
characterize market-core history/time/unit semantics

LSE-QDF-04
characterize rates + macro + COT PIT semantics

LSE-QDF-05
characterize options/IV/Greeks methodology

LSE-QDF-06
run cross-source parity matrix

LSE-QDF-07
freeze source-role / promotion candidates

LSE-QDF-08
write Quant Data Fabric integration design
```

Stop after each checkpoint for operator review.

---

# 22. Required future evidence artifacts

Suggested:

```text
quant-lab/research/data_sources/lse/
    LSE_SOURCE_ATLAS.md
    LSE_CAPABILITY_MATRIX.csv
    LSE_HISTORY_BOUNDS.json
    LSE_TIME_SEMANTICS.json
    LSE_UNIT_SEMANTICS.json
    LSE_PIT_CLASSIFICATION.json
    LSE_OPTIONS_METHODOLOGY.md
    LSE_PARITY_MATRIX.csv
    LSE_ACCESS_LICENSE_REPORT.md
    LSE_SOURCE_PROMOTION_CANDIDATES.yaml
    LSE_QUANT_DATA_FABRIC_HANDOFF.md
```

No need to create this directory until future execution is authorized.

---

# 23. Park / resume rule

This plan is now PARKED.

Current priority remains:

```text
CRYPTO SENSOR FABRIC
→ finish active Bloc 4 implementation
→ preserve staged checkpoint discipline
→ continue toward historical/live mechanical evidence substrate
```

LSE work resumes ONLY when the operator explicitly asks.

Nothing in this plan changes the current crypto branch, checkpoint, test floor, adapter set, or Sensor Fabric authority.

---

# 24. Final queued decision

```text
LSE_QUANT_LAB_RELEVANCE = HIGH
LSE_SOURCE_AUTHORITY = EXTERNAL_ONLY
LSE_CANONICAL_AUTHORITY = FALSE
LSE_IMPLEMENTATION_AUTHORIZED = FALSE
LSE_BULK_INGEST_AUTHORIZED = FALSE
LSE_PARITY_RESEARCH_VALUE = HIGH
LSE_MULTI_ASSET_EXPANSION_VALUE = HIGH
CURRENT_CRYPTO_WORK_INTERRUPTED = FALSE
```

**Queued verdict:**

`QUEUE_LSE_SOURCE_ATLAS_FOR_POST_CRYPTO_SENSOR_CHARACTERIZATION`

The value is not that LSE can replace Quant Lab. The value is that it may provide a broad external evidence surface that Quant Lab can interrogate, falsify against, and eventually absorb through the same provenance/PIT/constraint-system discipline already being built in the Crypto Sensor Fabric.
