# BLOC 1 — DECISION

**Status:** `PASS_BLOC_01_CONTRACTS_FROZEN` — **OPERATOR RATIFIED**

Operator ratification recorded at review head `e61240315314d53d000e4e8ca44566adc11c8cc7`:

    operator_ratified = TRUE
    human_review_required = TRUE
    Bloc 2 implementation_authorized = TRUE

Repair history accepted: SENSOR-B1-R01 (`3f4b97da`), R02 (`381b224b`), R03
(`12750cf1`), R04 (`bc179d53`); revalidation head `e6124031` (177 passed / 0
failed, Ruff clean, JSON-schema drift clean).  The previous
`PASS_BLOC_01_REPAIRS_READY_FOR_OPERATOR_REVIEW` status is superseded by this
ratification.

**Previous decision (superseded by operator review):** `PASS_BLOC_01_CONTRACTS_FROZEN` was
issued at `eaf7a543`.  The operator review (verdict `PASS_WITH_REQUIRED_AMENDMENTS`,
`HOLD_BLOC_02`) required three contract repairs.  All three plus the optional hardening
are implemented as explicit repair commits (no history rewrite) and revalidated.
Operator ratification of `PASS_BLOC_01_CONTRACTS_FROZEN` remains pending.

## Operator repairs applied

| Repair | SHA | Change |
|---|---|---|
| SENSOR-B1-R01 | 3f4b97da | corrected inverted Binance aggressor semantics (isBuyerMaker=true → SELL, false → BUY) in methodology + equivalence registries; machine-readable contract fixture + regression tests |
| SENSOR-B1-R02 | 381b224b | capability vocabulary extended with positioning + basis; Kraken basis / Gate positioning / Coinalyze positioning claimed, all verified=false |
| SENSOR-B1-R03 | 12750cf1 | blocking quality flags resolve fail-closed to QualityState.BLOCKED, dominating STALE/DEGRADED/PARTIAL/UNVERIFIED |
| SENSOR-B1-R04 | bc179d53 | (optional) explicit sensor-family mismatch now fails validation instead of silent pin |

All repairs keep mappings PROVISIONAL, add no verified capability, add no network
access, add no T0/T1 ingestion and no Bloc 2 implementation.

## Rationale

Bloc 1's success condition (bloc_01/01 §18) is that a future provider adapter
can be written without inventing any new foundational concept.  The following
foundational concepts are now frozen, tested and committed:

- provider identity (registry-controlled; never erased by fallback)
- instrument identity (InstrumentIdentity; asset ≠ economic contract)
- PIT timestamps (effective_at / observed_at / ingested_at, UTC-normalized)
- access/cost state (FreeOnlyPolicy + F9 gate)
- provenance (ProviderEnvelope → raw_object_uri + raw_checksum traceability)
- raw observation envelope (ProviderEnvelope)
- canonical sensor families (8 frozen enums + schemas)
- normalized vs native values (native always preserved)
- missingness (MissingObservation + MissingReason; no zero-fill)
- quality (QualityFlag vocabulary + QualityState aggregation rules)
- semantic comparability (SemanticEquivalence registry; pooling rules)
- versioning (schema/identity/normalization/methodology versions + JSON-schema snapshots)

## Failure conditions checked (bloc_01/03 §15)

| # | Condition | Status |
|---|---|---|
| 1 | Provider-specific field names leak into research-facing interfaces | NOT PRESENT — research-facing surface is canonical schemas only |
| 2 | Native values destroyed by normalization | NOT PRESENT — native fields mandatory, normalization additive |
| 3 | Missingness can become zero silently | NOT PRESENT — T52 enforces no missing→zero |
| 4 | Provider identity disappears during fallback | NOT PRESENT — provider+venue mandatory on every record; fallback is candidate lists, never identity rewrite |
| 5 | Cross-venue synthesis allowed in T1 | NOT PRESENT — T1 schemas are venue-local; pooling only at T2 with Bloc 6 eligibility |
| 6 | Community aggregate data indistinguishable from first-party | NOT PRESENT — EvidenceClass separates COMMUNITY_ARCHIVE / THIRD_PARTY_AGGREGATOR / FIRST_PARTY_EXCHANGE |
| 7 | Paid/reference-only sources become required dependencies | NOT PRESENT — F9 gate tests fail closed |
| 8 | Timestamps cannot distinguish effective/observed/ingested | NOT PRESENT — three separate UTC fields |
| 9 | OI/funding/liquidation units ambiguous | NOT PRESENT — NativeOIUnit, funding interval, liquidation shape/units explicit |
| 10 | Semantic comparability implicit | NOT PRESENT — registry-controlled with evidence references |
| 11 | Schemas lack versioning | NOT PRESENT — versions + snapshots committed |
| 12 | Bloc 2 would invent a new foundational observation type | NOT PRESENT — probe plan maps onto existing envelopes/schemas |

## Gaps recorded (explicit, non-blocking)

- Provider capability claims are planning claims only; every `verified` flag is
  false until Bloc 2 probes.  This is by design, not a defect.
- Semantic equivalence mappings are provisional (`BLOC2_PROBE_PENDING`); no
  EXACT_EQUIVALENT claimed.
- All methodology entries remain PROVISIONAL until Bloc 2/5 verification.

## Next gate

```
BLOC 1 REPAIRS COMPLETE (this decision)
      ↓
OPERATOR RATIFICATION of PASS_BLOC_01_CONTRACTS_FROZEN
      ↓
BLOC 2 PROBE HARNESS
```

No provider adapter implementation may begin before the probe harness verifies
actual provider behavior (bloc_01/03 §16).  Bloc 2 may rely on Bloc 1 contracts
only after operator ratification.

`human_review_required = TRUE`
`next_bloc_authorized = FALSE` — awaiting operator ratification of Bloc 1 after repairs.
