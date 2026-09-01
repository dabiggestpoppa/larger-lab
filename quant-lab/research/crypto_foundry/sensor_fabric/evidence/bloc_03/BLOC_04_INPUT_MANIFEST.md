# BLOC 4 INPUT MANIFEST (SENSOR-B3-I11)

The single most important handoff artifact.  Bloc 4 (IMMUTABLE T0 RAW EVIDENCE
LAKE FOUNDATION) may assume ONLY what is listed in §1, must preserve §2, and
must NEVER assume §3.  Everything else is out of scope until its own
evidence-earned checkpoint.

## 1. What Bloc 4 MAY TRUST (the allowed boundary)

Bloc 3 production adapters (KRAKEN_FUTURES `kraken-adapter-v2`,
GATE_FUTURES `gate-adapter-v2`, OKX_SWAP `okx-adapter-v1`, DERIBIT
`deribit-adapter-v1`) provide, for each of the 17 promoted provider×sensor
paths (18 physical production-symbol checks):

1. **RawPayloadEnvelope** — immutable raw provider response bytes preserved
   BEFORE any parse decision, with deterministic content hash.
2. **Request fingerprints** — deterministic identity of the acquisition
   request (provider, sensor, symbol, endpoint family, params).
3. **Provider/native identity** — `provider_id`, `sensor_family`,
   `native_instrument_id` survive every stage.
4. **Adapter versions** — semantic version distinguishes pre/post-repair
   interpretation (Gate/Kraken v2; OKX/Deribit v1).
5. **Explicit readiness/completion status** — per-path resume/completion
   (LIMITED is a truthful state; `is_complete` never manufactured).
6. **Resume tokens where supported** — Kraken analytics `since`-cursor
   (result.more); nowhere else invented.
7. **Typed unsupported/LIMITED states** — `CapabilityUnavailable`,
   `ProviderSemanticError`, `HistoricalRangeUnavailable`, `SchemaDrift`, etc.;
   no failure collapses to `[]`/`0`/`None`/EMPTY_VALID without justification.
8. **Live validation evidence** — I10/I10R1/I10R2 network smoke, operator-
   accepted: 17/17 logical paths, 18/18 physical symbol checks.
9. **Deterministic raw payload hash** — content addressing is stable.
10. **Free-only acquisition boundary enforced** — FREE_AUTOMATED / NO_AUTH /
    $0; no credentials, no paid/private/trading endpoints.

## 2. What Bloc 4 MUST PRESERVE

Storage must retain, per acquired batch, without loss:

- provider_id, sensor_family, native_instrument_id
- endpoint / request family (endpoint host + path)
- request fingerprint
- raw payload (the preserved bytes) + raw content hash
- retrieval timestamp (UTC)
- requested range (start/end) and actual range (first/last timestamps)
- adapter version
- schema state
- evidence ref (evidence_ref_id)
- resume/page identity where present
- quality flags (EMPTY_VALID, PARTIAL_INTERVAL, GAP_DETECTED,
  SCHEMA_ADDITIVE, NON_MONOTONIC_TIMESTAMPS, ...)

No raw evidence loss.  Raw provider values are never mutated; convenience
datetimes are derived, not authoritative.

## 3. What Bloc 4 MUST NEVER ASSUME

Bloc 4 MUST NOT assume:

- all providers exist (4 exist; excluded providers do not)
- all periods are covered (verified history boundaries are ragged/literal I14)
- all paths are complete (many are LIMITED by frozen authority)
- all historical requests are resumable (LIMITED != resumable)
- all sensor families are economically equivalent (same SensorFamily != same
  numerical observable; Deribit liquidation is a trade-level microscope)
- canonical asset identity already exists
- canonical OI / liquidation / funding units exist
- cross-provider reliability weights exist
- failover exists
- missing values should be filled
- provider disagreements should be averaged or reconciled
- additive/unknown raw fields are research observables

## 4. Normalization is NOT Bloc 4

- Bloc 4 stores immutable T0 evidence.
- Bloc 5 owns PIT identity, contract lifecycle, semantic normalization, unit
  conversion/reconstruction, effective/observed/ingested timing semantics.
- Bloc 3 never performs normalization; Bloc 4 must not sneak Bloc 5 code in.

## 5. Storage design questions passed down (frozen, NOT implemented)

Surface for the next bloc to design (do NOT implement now):

- partition layout
- exact raw-record envelope
- content addressing
- manifest/index strategy
- checksum/integrity
- atomic writes
- append/revision semantics
- durable resume/job state
- storage quotas
- DuckDB discovery
- PostgreSQL operational metadata
- backup/export
- raw evidence reader/replay durability

## 6. Bloc 3 objects Bloc 4 may consume

| Object | Module | Stability | Serialization contract | Important invariants |
|---|---|---|---|---|
| `RawPayloadEnvelope` | `crypto_sensor_fabric.providers.base.models` | FROZEN (Bloc 1) | raw_body bytes + content_hash + provider/sensor/fingerprint/schema_state/evidence_ref/adapter_version | materialized BEFORE parse; hash deterministic; raw never mutated |
| `FetchBatch` | same | FROZEN | provider/sensor/symbol, requested vs actual ranges, row_count, is_complete, quality_flags, resume token, http_status, adapter_version | actual timestamps derived; is_complete truthful per path |
| `ProviderCapabilities` / `SensorCapability` | `providers.base.models` | FROZEN | supported set, symbol scope, roles, access, history scope, PIT, methodology pin, redundancy | derived from I14 + adapter; no fifth provider |
| `AdapterEvidenceRef` | `providers.base.models` | FROZEN | evidence_id + evidence kind | resolves to committed bloc_02 evidence |
| `ResumeToken` | same | FROZEN | mode TIME_RANGE + provider_native_state | only where resume supported (Kraken) |
| `ProviderHealthSignal` | same | FROZEN | provider-level health/rate-limit snapshot | acquisition boundary only |
| `AcquisitionFailure` (typed errors) | `providers.base.errors` | FROZEN | class + provider/sensor + detail + optional raw envelope | never collapses to empty/false data |

## 7. Bloc 4 first checkpoint

Recommended next checkpoint: `SENSOR-B4-I01` — IMMUTABLE T0 RAW EVIDENCE LAKE
FOUNDATION.  NOT begun in this checkpoint; requires its own operator
authorization.
