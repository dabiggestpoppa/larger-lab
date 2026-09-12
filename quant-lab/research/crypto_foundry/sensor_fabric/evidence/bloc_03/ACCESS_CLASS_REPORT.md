# BLOC 3 — ACCESS CLASS REPORT (SENSOR-B3-I11)

Scope: every candidate provider considered for the sensor fabric, its access
class, and its final disposition.  No secrets are exposed; no environment
secrets are enumerated; the only execution opt-in value for network smoke is
`SENSOR_NETWORK_SMOKE=1`.

## 1. Production providers (4)

| Provider | Production | Access class | Auth | Cost | Geo state | Payment/Staking/Transaction | Evidence | Disposition |
|---|---|---|---|---|---|---|---|---|
| KRAKEN_FUTURES | YES | FREE_AUTOMATED | NO_AUTH | $0 | reachable (live-verified I10/I10R1/I10R2) | none required | I10/I10R1/I10R2 results | PRODUCTION, `kraken-adapter-v2` |
| GATE_FUTURES | YES | FREE_AUTOMATED | NO_AUTH | $0 | reachable (live-verified) | none required | I10/I10R1/I10R2 results | PRODUCTION, `gate-adapter-v2` |
| OKX_SWAP | YES | FREE_AUTOMATED | NO_AUTH | $0 | reachable (live-verified I10) | none required | I10 results | PRODUCTION, `okx-adapter-v1` |
| DERIBIT | YES | FREE_AUTOMATED | NO_AUTH | $0 | reachable (live-verified I10) | none required | I10 results | PRODUCTION, `deribit-adapter-v1` |

Every production fetch passes the free-only access gate (`assert_free_only_access`)
BEFORE any transport call: FREE_AUTOMATED, NO_AUTH, PUBLIC_REST, $0, no
payment/staking/transaction/wallet/trading credentials.  No production request
can carry Authorization/Cookie/X-API-KEY/OK-ACCESS-KEY headers (smoke transport
rejects credential headers; adapters are NO_AUTH).

## 2. Non-production / evidence-only providers (4)

| Provider | Production | Access class | Auth | Cost | Geo state | Payment/Staking/Transaction | Evidence | Disposition |
|---|---|---|---|---|---|---|---|---|
| BINANCE_USDM | NO | PUBLIC_REST (claim-only) | NO_AUTH | $0 | REST geo block / archive reference observed (Bloc 2 probe) | none | bloc_02 probes + `12_BLOC_02_IMPLEMENTATION_DECISION.md` | **EXCLUDED** (E0_CLAIM_ONLY, NOT_PIT_READY); historical evidence retained |
| BYBIT_LINEAR | NO | PUBLIC_REST (claim-only) | NO_AUTH | $0 | geo block observed (Bloc 2 probe) | none | bloc_02 probes + decision doc | **EXCLUDED** (E0_CLAIM_ONLY, NOT_PIT_READY); historical evidence retained |
| COINALYZE | NO | FREE_API_KEY (aggregator) | API key (free) | $0 | n/a | none | decision doc; key NEVER read by Bloc 3 | **CORROBORATOR** (E0_CLAIM_ONLY, NOT_PIT_READY); never instanced in production registry; no Bloc 3 code reads `COINALYZE_API_KEY` |
| BITFINEX_COMMUNITY_ARCHIVE | NO | COMMUNITY_ARCHIVE | NO_AUTH | $0 | n/a | none | decision doc (E2_LIVE_RECENT_VERIFIED single-point) | **CORROBORATOR** (NOT_PIT_READY, archive); never instanced; no archive/CDN host allowed by smoke transport |

Non-production providers count toward ZERO of the 17 production paths.  Their
characterization/evidence packages remain in the repository and their
historical evidence remains useful (probe payloads, schema fingerprints).
Exclusion is evidence-adjudicated, not an implementation gap: the production
17-path set preserves required redundancy (funding 4-source, liquidation
3-source, OI 2-source, positioning 2-source, trade 2-source, book snapshot
2-source, basis 1-source, book metric 1-source).

## 3. Free-only enforcement (adversarial, final)

Re-verified in the final offline suite (dedicated adversarial tests +
per-provider conformance, PRODUCTION_CANDIDATE mode, 0 failures):

- paid access policy → blocked before transport
- payment method required → blocked before transport
- staking required → blocked before transport
- transaction required → blocked before transport
- auth-required production mutation → blocked before transport
- foreign provider request → typed `ProviderSemanticError` before transport
- unsupported sensor → typed `CapabilityUnavailable`
- invalid symbol → typed `InvalidInstrument`
- network unavailable (no transport) → typed `ProviderUnavailable`
- schema breaking → raw preserved + typed `SchemaDrift`

## 4. Access invariants

- ZERO API keys used by production acquisition (Bloc 3).
- ZERO paid endpoints; ZERO trading/private/account endpoints.
- Network smoke: HTTPS only, allowlisted hosts only
  (`futures.kraken.com`, `api.gateio.ws`, `www.okx.com`, `www.deribit.com`),
  GET only, TLS verification ON, cross-domain redirects rejected, zero retries,
  sequential, tiny windows, page sizes ≤ 25/50.
- No VPN, no proxy credentials introduced by code, no region switching, no
  alternate-domain bypass.
