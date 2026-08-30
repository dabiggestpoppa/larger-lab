# BLOC 3 — COMMON FOUNDATION EVIDENCE (SENSOR-B3-I01..I04)

**Checkpoint:** SENSOR-B3-I04 (conformance suite) — common foundation COMPLETE
**Branch:** `agent/crypto-sensor-fabric-build`
**Verdict:** `COMMON_FRAMEWORK_READY` (provider adapters NOT started — awaiting
operator review before SENSOR-B3-I05 Kraken)

## 1. What was built

`quant-lab/src/crypto_sensor_fabric/providers/base/` — the shared acquisition
protocol every promoted provider adapter must implement:

| Checkpoint | Contents | Evidence |
|---|---|---|
| SENSOR-B3-I01 | controlled vocabularies, FetchRequest / FetchBatch / RawPayloadEnvelope / ResumeToken / RateLimitSnapshot / ProviderHealthSignal models, typed error taxonomy, MechanicalProviderAdapter protocol | 19 tests |
| SENSOR-B3-I02 | free-only access gate (runs before transport, fail closed), deterministic request fingerprint, raw payload integrity hash | 25 tests |
| SENSOR-B3-I03 | retry classification + bounded backoff, normalized rate limits, cursor-loop / non-monotonic protection, deterministic resume round-trip | 25 tests |
| SENSOR-B3-I04 | common conformance suite (Q0 contract / Q1 parser / Q2 mechanics) + I14 promotion-file capability binding | 14 tests |

Bloc 2 probe base module renamed `providers/base.py` → `providers/probe_base.py`
to free the `base/` package name (all probe imports updated; Bloc 2 suite green).

## 2. Access-gate invariants

- `cost_usd_required == 0`, no payment-method / staking / transaction requirement
- auth in `{NO_AUTH, FREE_API_KEY, OPTIONAL_PUBLIC_KEY}`; everything else
  (PAID_KEY, TRADING_KEY, WITHDRAWAL_PERMISSION, SIGNING_SECRET,
  WALLET_SIGNATURE, STAKING_UNLOCK, TRANSACTION_REQUIRED) is a hard block
- `UNVERIFIED` fails closed; gate executes before any transport call

## 3. Fingerprint / hash semantics

- deterministic request fingerprint over provider + endpoint family + sensor +
  native instrument + start/end + granularity + page/cursor + adapter version
- identical semantic request -> identical fingerprint; material change -> differs
- ordering/serialization noise is inert
- raw payload content hash is deterministic and byte-verbatim

## 4. Retry / resume semantics

- transient (timeout/DNS/TLS/reset/5xx/429) vs terminal (400/401/403/404/payment/
  invalid symbol/unsupported granularity/history unavailable/schema) classification
- geo/access/payment NEVER retried as transient
- bounded exponential backoff + jitter; Retry-After honored; no infinite loops
- cursor-loop detection, non-monotonic timestamp protection, deterministic
  resume-token round-trip; completion from provider semantics, never short pages

## 5. Conformance harness

`run_conformance_suite()` — Q0 (provider metadata, registry entry,
sensor-specific capabilities, evidence refs, free-only gate, I14 promotion
bounds), Q1 (raw preservation, empty-valid vs unsupported, schema drift
explicit), Q2 (retry classification, resume determinism, native instrument
required).  A full fake adapter passes; degraded adapters fail the exact
invariant they violate.  No provider implementation can bypass the suite.

## 6. I14 evidence integration

`capabilities_from_promotion()` reads `source_promotion_candidates.yaml`
(the ONLY Bloc 3 input list) and binds every declared capability to the I14
authoritative fields: allowed_role, history_mode, verified_history,
redundancy_class, PIT_requirement, methodology_pin, known_hazards,
evidence_basis.  CURRENT_ONLY stays current-only; PIT_READY requires a
verified-history bound; unpromoted providers get zero capabilities.

## 7. Known blockers for provider checkpoints

- Gate ~180-day rolling retention boundary; funding/trades use Unix SECONDS
- Binance REST geo-blocked (archive-only, data semantics unverified)
- Bybit CloudFront geo-blocked
- Kraken Market Analytics history ragged per sensor/instrument
- Coinalyze free key not configured locally
- Bitfinex community archive: SOURCE_AVAILABILITY_VERIFIED only (no 355MB dump)

## 8. Readiness distinction

| Stage | Status |
|---|---|
| COMMON_FRAMEWORK_READY | YES (I01-I04 complete) |
| PROVIDER_ADAPTER_READY | NO — zero provider adapters built |
| test count | 608 passed / 0 failed (cumulative) |
| ruff | clean |

`human_review_required = TRUE`, `bloc_03_implementation_authorized = TRUE`
(common foundation only), `next_checkpoint_authorized = FALSE` — I05 Kraken
NOT authorized until operator review.
