# HYPERLIQUID EQUITY SECTOR RESEARCH PANEL — IMPLEMENTATION PROGRESS

**Branch:** `agent/hyperliquid-equity-sector-research-panel-build`  
**Planning parent:** `agent/hyperliquid-equity-sector-research-panel-plan`  
**Planning commit:** `c2040b1cc1ba5a0c26b454c07e651aeaacffdf3b`  
**Date:** 2026-09-22

## Current state

```text
PROJECT = HESP
MODE = SIDECAR_RESEARCH
CURRENT_BLOC = HESP-B0
CURRENT_CHECKPOINT = HESP-B0-00
PLAN_FROZEN = TRUE
IMPLEMENTATION_STARTED = FALSE
LIVE_NETWORK_AUTHORIZED = FALSE
TRADING_AUTHORITY = FALSE
SENSOR_FABRIC_SCHEMA_MUTATION = FALSE
NEXT_AUTHORIZED_SCOPE = CONTRACTS + PACKAGE SKELETON + OFFLINE TESTS ONLY
```

## Repository context at branch creation

Crypto Sensor Fabric remains independently active on:

`agent/crypto-sensor-fabric-build`

Observed active checkpoint:

`SENSOR-B4-I07R1I`

Important boundary:

- do not merge experimental HESP code into the active Sensor Fabric branch;
- do not alter `crypto_sensor_fabric` production contracts;
- do not start Sensor Fabric I08 from this branch;
- do not infer Hyperliquid provider promotion from HESP research work.

## HESP-B0 authorized work

Allowed:

1. create `quant-lab/src/hyperliquid_equity_panel/`;
2. create offline typed contracts and enums;
3. freeze instrument-class taxonomy;
4. freeze sector + theme taxonomy;
5. implement venue-contract identity rules;
6. implement point-in-time research record schemas;
7. create deterministic serialization fixtures/tests;
8. create explicit no-execution guard tests;
9. create explicit no-Sensor-Fabric-mutation guard tests;
10. create HESP evidence directory and B0 contract evidence.

Not allowed yet:

- Hyperliquid live API calls;
- historical backfill;
- websocket collection;
- L2 order-book ingestion;
- sector analytics from live data;
- alpha labels;
- trading signals;
- execution;
- wallet/key handling;
- modification of Sensor Fabric provider matrix;
- Capital Field promotion.

## HESP-B0 intended exit gate

```text
PASS_HESP_B0_CONTRACTS_FROZEN
```

Required proof:

- unique builder-native venue identity model;
- no naked ticker as canonical primary key;
- explicit common equity / ADR / preferred / ETF / leveraged ETF / index / other classes;
- conventional sector field separated from multi-valued research theme tags;
- unresolved classification represented explicitly;
- point-in-time classification/version timestamps;
- deterministic model serialization;
- no network dependency in B0 tests;
- no execution-capable code;
- no imports from private-key/wallet/trading-action surfaces;
- no changes to `quant-lab/src/crypto_sensor_fabric/`.

## Next checkpoint

`HESP-B0-01 — CONTRACT ENUMS + MODELS`

No later checkpoint is authorized by this ledger.
