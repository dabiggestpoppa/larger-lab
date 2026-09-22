# HYPERLIQUID EQUITY SECTOR RESEARCH PANEL — PLAN

**Program:** Quant Lab / Crypto Foundry side research  
**Lane:** research-only sidecar  
**Planning branch:** `agent/hyperliquid-equity-sector-research-panel-plan`  
**Intended build branch:** `agent/hyperliquid-equity-sector-research-panel-build`  
**Date:** 2026-09-22  
**Status:** PLAN FROZEN FOR OPERATOR REVIEW  
**Execution authority:** NONE in this document  
**Trading authority:** NONE  
**Sensor Fabric schema mutation authority:** NONE

---

## 0. Why this exists

Hyperliquid HIP-3 now exposes a sufficiently broad equity-perpetual surface to support a dedicated cross-sector research panel.

The purpose of this lane is to answer questions such as:

- which equity perps are actually live on Hyperliquid;
- which are single-name equities versus ETFs, indices, preferred securities, synthetic/pre-IPO references, or other contract types;
- how the live universe maps into banks/financials, energy, semiconductors, software, healthcare, consumer, industrials, materials, communications, crypto-linked equities, and other useful groups;
- how liquidity, open interest, funding, premium, spread, depth, turnover, and participation distribute by sector;
- whether one sector is expanding while another contracts;
- whether equity-perp behavior is dominated by traditional equity beta, crypto beta, venue mechanics, or a mixture;
- whether cross-sector relationships are stable enough to become future research inputs.

This is NOT an alpha engine and NOT an execution system.

The first deliverable is a trustworthy, point-in-time research panel and evidence substrate.

---

# 1. Current repository context

The active Crypto Sensor Fabric remains the primary mechanical-market build.

Current observed state at planning time:

- Bloc 1 contracts: frozen / ratified.
- Bloc 2: complete / operator ratified.
- Bloc 3: complete, operator accepted, frozen.
- Production provider coverage: Kraken Futures, Gate Futures, OKX Swap, Deribit.
- Cross-provider offline closure: complete.
- Network validation: passed for the frozen Bloc 3 matrix.
- Bloc 4: active immutable T0 raw-evidence lake work.
- Current build checkpoint: `SENSOR-B4-I07R1I`.
- Durable job-state/resume work exists but remains pending operator acceptance.
- Recovery/quarantine checkpoint `SENSOR-B4-I08` is NOT authorized.
- The active Sensor Fabric branch must not be interrupted or used as an experimental equity-research workspace.

Related queued architecture already establishes that:

- Hyperliquid is a high-value future DEX/onchain mechanical venue;
- provider-native premium/oracle/mark, OI, funding, trades, and L2 book are useful observables;
- capital-field/source-atlas expansion is deferred until the mechanical substrate is sufficiently mature;
- source-native semantics must be preserved;
- derived state must never be confused with provider truth.

Therefore this project is a SIDE RESEARCH PANEL, not a new Sensor Fabric bloc.

---

# 2. Governing boundary

The lane MUST remain isolated from `crypto_sensor_fabric` until a later explicit promotion decision.

Initial package boundary:

```text
quant-lab/
  research/
    hyperliquid_equity_sector_panel/
      ...
  src/
    hyperliquid_equity_panel/
      ...
  tests/
    hyperliquid_equity_panel/
      ...
```

The panel MAY read exported Sensor Fabric artifacts in the future.

The panel MUST NOT:

- alter frozen Sensor Fabric contracts;
- add a Hyperliquid provider to the production Sensor Fabric matrix by implication;
- reuse crypto symbols as if they were equity identifiers;
- create trade signals;
- submit orders;
- hold private keys;
- require wallet credentials;
- mutate broker/exchange state;
- silently redefine source-native fields;
- write into the Sensor Fabric T0 lake without a later promotion contract.

Read-only interoperability only.

---

# 3. Primary source doctrine

Hyperliquid protocol/API data is the primary venue truth for the HIP-3 market surface.

Primary discovery surfaces include:

```text
POST https://api.hyperliquid.xyz/info
type = perpDexs
type = allPerpMetas
type = perpCategories
type = meta
type = metaAndAssetCtxs
type = perpDexLimits
type = perpDexStatus
type = fundingHistory
```

HIP-3 instrument identity must preserve the builder DEX namespace.

Canonical venue identity:

```text
{dex}:{coin}
```

Builder-deployed perp asset identity must never be collapsed to a naked ticker when doing storage, lineage, joins, or historical comparison.

Example:

```text
display_symbol = NVDA
venue_instrument_id = xyz:NVDA
builder_dex = xyz
```

A naked `NVDA` may be used only as a display or normalized-underlier field.

---

# 4. The two-layer identity model

Every contract gets two identities.

## 4.1 Venue contract identity

Fields:

```text
venue
builder_dex
venue_instrument_id
coin
asset_id
sz_decimals
max_leverage
margin_mode
collateral_asset
listing_status
oracle_spec_reference
first_seen_at
last_seen_at
source_observed_at
```

This is provider-native and point-in-time.

## 4.2 Economic-underlier identity

Fields:

```text
normalized_symbol
issuer_name
instrument_class
security_type
primary_listing_exchange
primary_listing_country
sector
industry
theme_tags[]
underlier_reference
classification_source
classification_as_of
classification_confidence
```

This is research metadata, NOT Hyperliquid-native truth.

The two layers must remain separate.

---

# 5. Instrument classes

The panel must distinguish at minimum:

```text
COMMON_EQUITY
ADR
PREFERRED_SECURITY
ETF
LEVERAGED_ETF
INDEX
COMMODITY_REFERENCE
FX_REFERENCE
CRYPTO_LINKED_EQUITY
PRIVATE_OR_PREIPO_REFERENCE
OTHER_SECURITY_REFERENCE
UNRESOLVED
```

No contract may enter a single-stock sector basket while `instrument_class = UNRESOLVED`.

ETFs and indices must never be silently counted as individual companies.

Preferred securities must never be silently counted as common equity.

---

# 6. Sector taxonomy

Use two simultaneous classification surfaces.

## 6.1 Conventional sector

A stable GICS-like research field:

```text
FINANCIALS
INFORMATION_TECHNOLOGY
COMMUNICATION_SERVICES
CONSUMER_DISCRETIONARY
CONSUMER_STAPLES
HEALTH_CARE
ENERGY
INDUSTRIALS
MATERIALS
UTILITIES
REAL_ESTATE
OTHER
UNRESOLVED
```

## 6.2 Research theme tags

Sector alone is insufficient.

Examples:

```text
BANK
BROKERAGE
EXCHANGE
ASSET_MANAGER
FINTECH
CRYPTO_EXCHANGE
CRYPTO_TREASURY
BITCOIN_MINER
SEMICONDUCTOR
MEMORY
SEMICAP_EQUIPMENT
OPTICAL_NETWORKING
AI_INFRASTRUCTURE
CLOUD
CYBERSECURITY
QUANTUM
SOCIAL_MEDIA
STREAMING
ECOMMERCE
AUTO_EV
GAMING
BIOTECH
PHARMA
POWER_GENERATION
GRID_ELECTRIFICATION
OIL_GAS
AEROSPACE
SPACE
ROBOTICS
RARE_EARTHS
KOREA_EQUITY
CHINA_TECH
SEMICONDUCTOR_BASKET
ENERGY_BASKET
```

This permits, for example:

- a conventional industrial company to also carry `POWER_GENERATION`;
- SOFI to carry `FINTECH` and `BANK`;
- COIN to carry `FINANCIALS`, `CRYPTO_EXCHANGE`;
- MSTR-like names to be grouped as `CRYPTO_LINKED_EQUITY` without pretending they are a formal sector;
- a semiconductor ETF to be excluded from single-name counts but included in the `SEMICONDUCTOR_BASKET` theme.

---

# 7. Research panel architecture

```text
HYPERLIQUID HIP-3 API
        |
        v
[DISCOVERY SNAPSHOT]
perpDexs / allPerpMetas / categories
        |
        v
[INSTRUMENT REGISTRY]
builder-native identity
        |
        +--------------------+
        |                    |
        v                    v
[UNDERLIER MAP]       [MARKET CONTEXT]
type / issuer /       mark / oracle /
sector / themes       funding / OI /
                      volume / limits
        |                    |
        +---------+----------+
                  |
                  v
          [PIT PANEL STORE]
                  |
          +-------+-------+
          |               |
          v               v
 [SINGLE-NAME VIEW] [ETF/INDEX VIEW]
          |
          v
      [SECTOR PANEL]
          |
          v
 [CROSS-SECTOR RESEARCH]
          |
          v
 [OPERATOR DASHBOARD / EXPORTS]
```

---

# 8. Panel 0 — Universe / security master

First priority.

Output must answer:

- all currently discoverable HIP-3 DEXes;
- every market on each DEX;
- which contracts represent equity-like instruments;
- instrument class;
- normalized underlier;
- conventional sector;
- theme tags;
- active / halted / unresolved status;
- duplicate economic underliers across builders;
- contract identity collisions;
- first-seen / last-seen observations.

Primary artifact:

```text
HYPERLIQUID_EQUITY_UNIVERSE.parquet
```

Human-readable companion:

```text
HYPERLIQUID_EQUITY_UNIVERSE.csv
```

---

# 9. Panel 1 — Market mechanics

Per contract, preserve available venue-native market context.

Candidate fields:

```text
mark_px
oracle_px
mid_px
current_funding
open_interest
day_volume_notional
prev_day_px
premium_or_basis_if_native
oi_cap
dex_oi_cap
is_at_oi_cap
spread_bps
depth_10bps
depth_25bps
depth_50bps
turnover_ratio
observed_at
```

Rules:

- only compute spread/depth from raw book data under an explicit methodology;
- do not rename provider-native values into stronger economic claims;
- missing value != zero;
- unsupported metric != false;
- all timestamps point-in-time;
- all transformations reproducible.

---

# 10. Panel 2 — Sector state

Aggregate only after instrument classification is sealed for the observation.

For each sector and theme:

```text
member_count
active_member_count
total_open_interest
median_open_interest
total_volume
median_volume
oi_weighted_funding
median_funding
funding_dispersion
median_spread_bps
median_depth_25bps
liquidity_concentration_hhi
top_3_oi_share
advancers
decliners
unchanged
breadth
median_return
dispersion
cross_sectional_volatility
```

Support at least:

- equal-weight;
- OI-weight;
- volume-weight;
- liquidity-weight.

Weights must be explicit in every output.

---

# 11. Panel 3 — Cross-sector relative state

Research-only comparisons:

```text
sector_return_spread
sector_funding_spread
sector_oi_growth_spread
sector_volume_share_change
sector_liquidity_share_change
sector_breadth_spread
sector_dispersion_ratio
```

Examples:

- semiconductors vs software;
- financials vs crypto-linked equities;
- energy vs power/electrification;
- consumer vs healthcare;
- high-beta tech vs defensive groups.

No "bullish/bearish" label in the canonical panel.

State descriptions may use mechanical terms such as:

```text
EXPANDING
CONTRACTING
CONCENTRATING
BROADENING
DISPERSING
COMPRESSING
UNRESOLVED
```

only when definitions are frozen and tested.

---

# 12. Panel 4 — Crypto-beta vs equity-beta research

This is the main reason the panel belongs beside Crypto Foundry.

Questions:

- do HIP-3 equity perps respond more to their underlying equity or to crypto-wide risk state during specific sessions;
- do crypto-linked equities form a distinct cluster;
- does BTC/ETH/HYPE volatility alter equity-perp funding or OI;
- does sector dispersion change during crypto stress;
- are weekend / off-primary-equity-session behaviors structurally different;
- do builder-level liquidity conditions dominate sector effects.

Candidate research outputs:

```text
rolling_beta_to_underlier
rolling_beta_to_spx
rolling_beta_to_ndx_or_proxy
rolling_beta_to_btc
rolling_beta_to_eth
rolling_beta_to_hype
partial_correlation_matrix
session_conditioned_correlation
lead_lag_matrix
funding_response_matrix
oi_response_matrix
```

No predictive promotion without separate evidence and operator approval.

---

# 13. Panel 5 — Builder / venue effects

HIP-3 is permissionless builder-deployed market infrastructure.

A security can therefore have:

```text
economic_underlier_effect
sector_effect
crypto_regime_effect
builder_effect
liquidity_effect
oracle_method_effect
contract_spec_effect
```

The panel must preserve enough information to separate them.

Research questions:

- same underlier across different builders;
- similar underliers on different builders;
- sector behavior conditional on builder;
- funding / premium dispersion across builders;
- halted / recycled contracts;
- OI cap pressure;
- oracle divergence;
- collateral differences.

Never average builder disagreement away before storing it.

---

# 14. Time model

Every row must distinguish:

```text
event_time
source_observed_at
ingested_at
classification_as_of
reference_market_session
```

Reference-session tags:

```text
US_PREMARKET
US_REGULAR
US_AFTER_HOURS
US_CLOSED_WEEKDAY
WEEKEND
HOLIDAY_OR_UNRESOLVED
```

Session tagging is descriptive metadata.

It does not imply the HIP-3 contract itself is closed.

---

# 15. Point-in-time / revision doctrine

Universe membership and classification are time-varying.

Store append-only observations of:

- listing appearance;
- listing disappearance;
- halted state;
- DEX status;
- category changes;
- underlier-classification revisions;
- sector-classification revisions;
- contract-spec revisions.

Never overwrite history in-place.

A later corrected classification creates a new version with provenance.

---

# 16. Initial practical baskets

These are RESEARCH BASKET NAMES, not hardcoded membership.

```text
BANKS_AND_FINTECH
BROKERS_EXCHANGES_ASSET_MANAGERS
CRYPTO_LINKED_EQUITIES
SEMICONDUCTORS
MEMORY_STORAGE
AI_INFRASTRUCTURE
SOFTWARE_CLOUD_CYBER
COMMUNICATIONS_INTERNET
CONSUMER_ECOMMERCE
AUTOS_EV
HEALTHCARE_BIOTECH
OIL_GAS
POWER_ELECTRIFICATION
AEROSPACE_SPACE_ROBOTICS
MATERIALS_CRITICAL_MINERALS
COUNTRY_ETFS
SECTOR_ETFS
LEVERAGED_ETFS
```

Membership is generated from the security master.

No manual basket may silently diverge from the canonical registry.

---

# 17. Data products

Machine artifacts:

```text
universe_snapshot.parquet
instrument_master.parquet
instrument_classification_history.parquet
market_context_snapshot.parquet
sector_snapshot.parquet
theme_snapshot.parquet
builder_snapshot.parquet
cross_sector_matrix.parquet
correlation_matrix.parquet
lead_lag_matrix.parquet
data_quality_report.json
source_manifest.json
```

Operator artifacts:

```text
CURRENT_UNIVERSE.md
SECTOR_MAP.md
UNRESOLVED_INSTRUMENTS.md
DATA_QUALITY.md
RESEARCH_FINDINGS.md
IMPLEMENTATION_PROGRESS.md
```

---

# 18. Dashboard / panel surface

A future local operator panel should expose:

## Universe
- active equity-like markets;
- single-name vs ETF/index/preferred;
- builder;
- sector;
- themes;
- unresolved mappings.

## Sector
- OI;
- volume;
- funding;
- breadth;
- dispersion;
- liquidity;
- concentration.

## Instrument
- venue-native identity;
- underlier identity;
- mark/oracle;
- funding;
- OI;
- volume;
- book metrics;
- sector/theme membership.

## Relative
- sector-vs-sector spreads;
- crypto-beta / equity-beta diagnostics;
- correlation;
- lead-lag;
- session-conditioned behavior.

## Quality
- missing fields;
- stale data;
- classification confidence;
- unsupported metrics;
- source/API errors.

The dashboard reads stored evidence.

It is not the source of truth.

---

# 19. Data quality gates

Mandatory gates:

```text
DQ-01 unique venue contract identity
DQ-02 no naked-ticker primary keys
DQ-03 no unresolved contract enters single-name sector aggregates
DQ-04 ETF/index/preferred exclusion from common-equity baskets
DQ-05 builder namespace preserved
DQ-06 missing != zero
DQ-07 source timestamps preserved
DQ-08 classification version preserved
DQ-09 duplicate-underlier detection
DQ-10 deterministic basket membership
DQ-11 deterministic aggregation
DQ-12 stale snapshot detection
DQ-13 no secret/private-key dependency
DQ-14 no order/execution code
DQ-15 no mutation of crypto_sensor_fabric schemas
```

Fail closed.

---

# 20. Build blocks

## HESP-B0 — Charter + frozen schemas

Deliver:

- package skeleton;
- enums;
- typed models;
- identity rules;
- sector/theme taxonomy;
- artifact schemas;
- no live network dependency.

Exit:

`PASS_HESP_B0_CONTRACTS_FROZEN`

## HESP-B1 — HIP-3 discovery probe

Read-only network probe for:

- perpDexs;
- allPerpMetas;
- categories;
- per-DEX metadata/status.

Deliver raw sanitized evidence + capability matrix.

Exit:

`PASS_HESP_B1_DISCOVERY_CHARACTERIZED`

## HESP-B2 — Instrument registry

Implement:

- venue identities;
- dedupe;
- underlier mapping;
- instrument classes;
- sector/theme mapping;
- unresolved queue;
- versioned classification.

Exit:

`PASS_HESP_B2_INSTRUMENT_MASTER_SEALED`

## HESP-B3 — Market context snapshots

Implement read-only observations:

- mark;
- oracle;
- funding;
- OI;
- volume;
- limits/status;
- optional book probes.

Exit:

`PASS_HESP_B3_MARKET_CONTEXT_SEALED`

## HESP-B4 — Sector aggregation

Implement deterministic:

- equal-weight;
- OI-weight;
- volume-weight;
- liquidity-weight;
- breadth;
- dispersion;
- concentration.

Exit:

`PASS_HESP_B4_SECTOR_PANEL_SEALED`

## HESP-B5 — Historical panel

Append-only PIT storage:

- universe history;
- classification history;
- snapshots;
- session tags;
- deterministic replay.

Exit:

`PASS_HESP_B5_PIT_HISTORY_SEALED`

## HESP-B6 — Cross-asset research

Read external reference series through explicit source contracts.

Implement:

- correlations;
- partial correlations;
- betas;
- session conditioning;
- lead/lag.

Exit:

`PASS_HESP_B6_CROSS_ASSET_RESEARCH_SEALED`

## HESP-B7 — Operator dashboard

Local/read-only panel over stored artifacts.

Exit:

`PASS_HESP_B7_OPERATOR_PANEL_SEALED`

## HESP-B8 — Promotion adjudication

Decide whether any component should:

- remain standalone;
- become Quant Lab shared infrastructure;
- become a Sensor Fabric consumer;
- nominate Hyperliquid as a future Sensor Fabric provider;
- feed Capital Field work.

No automatic promotion.

Exit:

`PASS_HESP_B8_HANDOFF_COMPLETE`

---

# 21. Proposed implementation tree

```text
quant-lab/
  research/
    hyperliquid_equity_sector_panel/
      HYPERLIQUID_EQUITY_SECTOR_RESEARCH_PANEL_PLAN.md
      IMPLEMENTATION_PROGRESS.md
      evidence/
        bloc_00/
        bloc_01/
        bloc_02/
        bloc_03/
        bloc_04/
        bloc_05/
        bloc_06/
        bloc_07/
        bloc_08/

  src/
    hyperliquid_equity_panel/
      __init__.py
      contracts/
        enums.py
        models.py
        taxonomy.py
      providers/
        hyperliquid/
          client.py
          discovery.py
          market_context.py
          raw_models.py
      registry/
        identity.py
        underliers.py
        classification.py
        revisions.py
      panels/
        instrument.py
        sector.py
        theme.py
        builder.py
        relative.py
      research/
        correlation.py
        beta.py
        lead_lag.py
        sessions.py
      storage/
        snapshots.py
        manifests.py
      quality/
        gates.py
        reports.py
      cli.py

  tests/
    hyperliquid_equity_panel/
      contracts/
      providers/
      registry/
      panels/
      research/
      storage/
      quality/
```

---

# 22. Test doctrine

Unit tests:

- offline by default;
- frozen fixtures;
- deterministic serialization;
- no secret required;
- no execution actions;
- no wallet signing.

Live tests:

- explicitly marked;
- read-only;
- bounded;
- no high-frequency polling;
- capture sanitized evidence;
- never required for ordinary unit-test success.

Adversarial tests:

- duplicate builder symbols;
- same economic underlier on two DEXes;
- malformed metadata;
- ticker collision;
- sector classification change;
- halted market;
- missing oracle;
- missing OI;
- stale snapshot;
- ETF mislabeled as common stock;
- preferred mislabeled as common stock;
- unresolved instrument;
- builder disappearance;
- reordered API arrays;
- additive unknown provider fields.

---

# 23. Initial acceptance floor

Before calling the panel usable:

1. 100% of discovered contracts retain builder-native identity.
2. 100% of equity-like contracts have an instrument-class state, including UNRESOLVED.
3. 0 unresolved contracts enter single-name sector aggregates.
4. 0 ETFs/indices/preferred securities silently enter common-equity counts.
5. sector aggregation is byte/determinism stable from frozen fixtures.
6. snapshot replay reproduces the same sector output.
7. builder disagreement is visible.
8. missing fields remain explicit.
9. no production Sensor Fabric schema is modified.
10. no execution-capable code exists in the package.

---

# 24. Relationship to existing queued Capital Field work

This project does NOT replace the queued Capital Field atlas.

It is narrower:

```text
HESP
= HIP-3 equity/security universe + sector mechanics + cross-asset research

Capital Field
= cross-chain capital routing + lending + vaults + yield + RWA + broader onchain state
```

Useful overlap:

- Hyperliquid venue discovery;
- OI/funding/premium;
- book metrics;
- cross-venue semantics;
- future RWA/equity-onchain questions.

Any shared capability should be promoted later through an explicit interface.

---

# 25. Relationship to CEREBUS

CEREBUS may later consume sector state as an external conditioning variable.

Examples for FUTURE research only:

- equity-sector risk state vs FX DT->AR behavior;
- energy/power state vs oil geometry;
- semiconductor/AI state vs index behavior;
- financial-sector stress vs USD/rates states;
- crypto-linked equity divergence vs BTC state.

CEREBUS structural rules remain independent until evidence supports a specific integration.

---

# 26. Immediate branch sequence

```text
1. create planning branch from current main
2. freeze this planning charter
3. create build branch from planning head
4. build HESP-B0 only
5. run offline contract tests
6. stop for operator review
7. authorize HESP-B1 live read-only discovery separately
```

Do not jump directly to historical collection.

Do not touch the active Sensor Fabric build branch.

---

# 27. Current decision record

```text
HESP_PROJECT = APPROVED_FOR_PLANNING
HESP_ARCHITECTURE = SIDECAR
HESP_PRIMARY_VENUE = HYPERLIQUID_HIP3
HESP_INITIAL_DOMAIN = EQUITY_LIKE_PERPS
HESP_SINGLE_NAME_AND_FUNDS_SEPARATED = TRUE
HESP_SECTOR_PLUS_THEME_MODEL = TRUE
HESP_POINT_IN_TIME_REQUIRED = TRUE
HESP_PROVIDER_NATIVE_IDENTITY_REQUIRED = TRUE
HESP_SENSOR_FABRIC_MUTATION = FALSE
HESP_EXECUTION_AUTHORITY = FALSE
HESP_ALPHA_AUTHORITY = FALSE
HESP_LIVE_DISCOVERY_AUTHORITY = PENDING_OPERATOR_REVIEW
HESP_BUILD_AUTHORITY = B0_ONLY_AFTER_PLAN_HANDOFF
```

**Planned next checkpoint:** `HESP-B0 — CONTRACTS + PACKAGE SKELETON`.
