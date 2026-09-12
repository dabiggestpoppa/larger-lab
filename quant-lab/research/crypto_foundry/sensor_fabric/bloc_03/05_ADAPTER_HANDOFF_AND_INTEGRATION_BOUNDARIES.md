# BLOC 3 — ADAPTER HANDOFF & INTEGRATION BOUNDARIES

## 1. Purpose

This document defines what Bloc 3 is allowed to hand downstream and what later blocs must not assume.

The adapter layer is intentionally narrow:

```text
External provider
→ verified acquisition
→ raw provider evidence
→ acquisition metadata
```

Nothing above this boundary may depend on provider-specific quirks.

## 2. Downstream handoff contract

Bloc 3 hands Bloc 4/5:

```text
RawPayloadEnvelope
FetchBatch
ProviderCapabilities
AdapterEvidenceRef
ResumeToken
ProviderHealthSignal
provider README / semantic documentation
provider fixture evidence
adapter readiness matrix
```

It does NOT hand:

```text
canonical asset IDs
canonical OI USD
canonical liquidation USD if not provider-native
cross-venue metrics
research features
provider reliability weights
imputed gaps
```

## 3. T0 boundary

The raw lake later stores evidence produced by adapters without losing:

```text
provider
venue/native endpoint family
native instrument
request fingerprint
raw payload hash
retrieval timestamp
request range
page/cursor/archive identity
adapter version
access/evidence metadata
```

The adapter is therefore the trusted source of acquisition provenance.

## 4. Normalization boundary

Bloc 4/5 may parse provider-native records further, but transformations must cite:

```text
source adapter version
source methodology ID
raw evidence hash
normalization methodology version
```

No normalization can destroy the source-native observation.

## 5. Instrument identity boundary

Adapter accepts and reports native instrument IDs.

Example:

```text
BTCUSDT
BTC_USDT
PI_XBTUSD
BTC-PERPETUAL
BTC-USDT-SWAP
```

Later identity resolution maps these to canonical economic contracts.

This separation prevents provider code from owning system-wide identity logic.

## 6. Unit boundary

Adapter parser may identify/document provider-native unit type, but normalized conversions belong downstream.

Examples:

```text
OI contracts
OI base asset
OI quote value
funding native interval
liquidation native size
```

If provider supplies an explicit USD value, preserve it as provider-native evidence.

If USD must be reconstructed from price × multiplier, that is later methodology.

## 7. Time boundary

Adapter documents provider timestamp meanings.

Later PIT layer maps them into:

```text
effective_at
observed_at
ingested_at
```

The adapter must never guess an unavailable publication timestamp.

## 8. Missingness boundary

Adapter emits acquisition-level missing reason:

```text
UNSUPPORTED_SENSOR
SYMBOL_NOT_LISTED
HISTORY_NOT_AVAILABLE
EMPTY_VALID_RANGE
PROVIDER_GAP
ACCESS_BLOCKED
GEO_RESTRICTED
REQUEST_FAILED
ARCHIVE_MISSING
```

Later layers decide whether a canonical observation is unavailable, degraded, or covered by another provider.

## 9. Failover boundary

Bloc 3 has no automatic economic-source substitution.

If Kraken liquidation history fails, adapter reports failure.

Later provider-orchestration/quality layer may fetch Gate or other sources for the same sensor family, but must not label Gate data as Kraken data.

## 10. Provider disagreement boundary

Bloc 3 never resolves disagreements.

If providers differ, later T2 observables can quantify:

```text
source breadth
dispersion
disagreement
venue concentration
```

Provider disagreement itself may become information.

## 11. Research bridge boundary

LF/MECH research must eventually request mechanical context through canonical/replay services such as:

```text
get_mechanical_snapshot(as_of, universe)
get_liquidation_context(...)
get_leverage_context(...)
get_orderflow_context(...)
```

Research must NOT call `KrakenAdapter.fetch_*()` directly.

That separation is mandatory for reproducibility and provider independence.

## 12. Provider removal

A provider can be removed/demoted later without changing canonical schemas if:

- another source covers the needed sensor;
- old raw evidence remains preserved;
- provider registry validity interval closes;
- research replay can still identify historical source coverage.

Do not delete historical evidence merely because provider becomes unavailable.

## 13. Provider addition

Adding a future provider requires:

```text
Bloc 2-style capability evidence
free-only/access review
new provider adapter package
conformance suite
semantic-equivalence mapping
human review
```

No canonical schema amendment is required unless the source exposes a genuinely new sensor family.

## 14. Adapter versioning

Use semantic versions at provider adapter level where practical.

Changes requiring version bump:

- parser semantic change;
- timestamp interpretation change;
- unit interpretation change;
- endpoint/archive family change;
- pagination semantics change;
- reconstruction annotation change.

Pure performance/internal refactors that preserve output semantics can remain patch-level.

## 15. Validity intervals

Provider capability/methodology may change over time.

Registry should eventually support:

```text
valid_from
valid_to
```

Example:

A historical liquidation archive may exist only through 2024-03-31. Capability after that may be live-only or unsupported.

Do not represent changing provider history as one timeless boolean.

## 16. Provider access reclassification

If access changes FREE→PAID:

- close free validity interval;
- mark current capability `ACCESS_BLOCKED`;
- preserve previous historical evidence;
- trigger fallback coverage review;
- do not delete adapter code immediately if needed to replay archived raw data.

## 17. Raw-reader durability

Provider parser/readers should remain capable of reading historical raw payloads even if live endpoint is removed.

Separate when useful:

```text
ProviderFetcher
ProviderRawParser
```

So future research can replay old archives without network access.

## 18. Handoff evidence package

Bloc 3 implementation final package must contain:

```text
ADAPTER_READINESS_MATRIX.csv
PROVIDER_CAPABILITY_RUNTIME.json
PROVIDER_IMPLEMENTATION_REPORT.md
KNOWN_FAILURES.md
ACCESS_CLASS_REPORT.md
OFFLINE_TEST_REPORT.txt/json
NETWORK_SMOKE_EVIDENCE/ (if run)
BLOC_04_INPUT_MANIFEST.md
```

No secrets/raw massive datasets committed to Git.

## 19. Bloc 4 prerequisites

Bloc 4 planning/build may assume only that:

1. adapters can produce immutable raw envelopes;
2. request fingerprints exist;
3. provider identity/provenance exists;
4. resume tokens exist;
5. adapter readiness is explicit.

Bloc 4 must not assume all providers or all sensors are available.

## 20. Scientific implication

The key benefit of Bloc 3 is not more endpoints. It creates a reproducible evidence boundary so future statements like:

> downside propagation coincides with liquidation cascades

can be traced all the way back to:

```text
research claim
→ canonical feature
→ normalized observation
→ provider raw record
→ request/archive evidence
```

That provenance chain is mandatory for CEREBUS/Quant Box research quality.

## 21. Final handoff principle

> Providers are replaceable acquisition mechanisms. Raw evidence and canonical sensor semantics are durable system assets.

`human_review_required = TRUE`
