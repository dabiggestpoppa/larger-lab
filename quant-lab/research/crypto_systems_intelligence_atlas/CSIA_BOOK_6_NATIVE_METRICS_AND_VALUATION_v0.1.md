# CSIA — BOOK 6 NATIVE METRICS AND VALUATION SEAM v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Scope:** Phases 11–13 — Bloc 6A native measurement families, the
> Book 5 → Book 6 valuation contract, and price-source ownership.
> **Governs nothing that is not ratified.** These are planned metric
> *families* and contract *shapes*; the governed metric set lives in the metric
> candidate matrix.

---

## 1. Native before normalized (Axiom 1)

Native measurement is planned and versioned **first**. Normalization is a later
derived act that cites the native measurement. No normalized dimension may be
ratified without its preserved native measurement definition. The comparability
doc (6B) and the validation doc (6D) enforce this mechanically.

**Do not force all families onto every chain.** Each metric family declares
`applies_to_architectures` (Book 3 family vocabulary). A family that is
structurally absent for an architecture is `NOT_APPLICABLE` / `NOT_SUPPORTED` —
never zero, never an emulated EVM-shaped substitute.

## 2. 6A.1 — Chain-specific measurement (native per architecture family)

Candidate families (each to be validated per family, not universally):

```text
transactions / executions    per family-native execution notion (EVM tx, Solana
                              instruction, UTXO spend, DAG event, ledger entry)
successful execution         vs attempted (failure semantics differ per family)
active accounts              identity rule is family-specific and sybil-sensitive
fees / gas                   family-native fee model (gas, compute-unit, resource
                              units, none)
issuance / burn              family-native supply operations
validator / producer count   family-native consensus role
stake / bonded quantity      family-native security stake
security budget              issuance minus burn-down, family-native
block/slot/production rate   family-native cadence (slots, blocks, epochs, waves)
throughput                   family-native executed work per unit time
finality                     family-native finality notion (probabilistic vs
                              deterministic vs BFT)
data-availability usage      family-native DA (rollup blobs, sidechain, none)
state growth                 family-native state accumulation
MEV                          only where the architecture exposes an MEV surface
                              (ordering markets, MEV channels); NOT_SUPPORTED otherwise
```

**Native-first rule examples (from the false-comparison corpus):** Solana
instructions ≠ EVM transactions (an instruction is a program call, not a
transaction; the same economic action compiles to many instructions). UTXO
"transactions" are spends, not state transitions. A PoW chain has no
"validators"; a BFT federation has validators but no "gas".

## 3. 6A.2 — Protocol-specific measurement

Candidate families: users; transactions/interactions; deposits; borrows; swaps;
volume; fees; revenue; liquidity depth; utilization; collateral; liquidations;
integration count.

**Do not assume every protocol shares one economic model.** Each protocol's
economic model is measured through its own native constructs. "Volume" means
different things across AMM, aggregator, perps, and order-book venues; "users"
mean different things across custodial, delegated-staking, and counterparty
services. Metric definitions are per model; cross-model volume is a
comparability question (6B), not a definitional one.

Book 5 supplies the underlying capital facts where a protocol metric is really a
capital record (deposits, borrows, collateral, liquidations are Book 5 economic
records; Book 6 measures over them, never re-derives their truth).

## 4. 6A.3 — Token-specific measurement

Candidate families: supply; issuance; burn; staking; locked amount; circulating
realizations; utility participation; governance participation.

**Do not collapse token activity into protocol activity** (Axiom 2: the system is
not the token). A token can be gas, governance, collateral, staking, or
several; it may capture less value than the protocol. Token metrics are scoped to
the token as an economic object; protocol metrics are scoped to the protocol.
"Token holders" are not "protocol users" (false-comparison corpus #13).

Circulating realizations consume Book 5's realization records (bridged vs native
issuance are distinct; a bridged token is not a native-issued one — Book 1/5
truth).

## 5. 6A.4 — Capital metrics (consume Book 5)

Book 6 measures **over** Book 5 capital truth; it does not re-derive it. Planned
capital metric families:

```text
same-unit capital stocks     measured over Book 5 same-unit aggregates
flows                        measured over Book 5 flow ledger
utilization                  measured over Book 5 supplied/borrowed/collateral
capital concentration        measured over Book 5 component sets (e.g. per-venue,
                             per-collateral distribution)
liquidity depth measures     planned as measurement over Book 5 reserves/components,
                             with a methodology (executable depth is a separate,
                             harder measure than reserves)
credit ratios                measured over Book 5 obligations (DebtLiability etc.)
staking ratios               measured over Book 5 stake/claim records
capital-route activity       measured over Book 5 flows
```

**Common-value (cross-asset) capital metrics are Book 6 measurement products
ONLY under an explicit Book 6 valuation methodology** (§6). They require an
explicit numeraire and a cited price observation. No valuation semantics leak
into Book 5: Book 5 remains `BOOK5_CROSS_ASSET_VALUATION_AUTHORITY = FALSE`, no
numeraire, no common-value field, no hidden scalarization. `SHARE FRACTION !=
VALUATION`; `PROPORTIONAL != COMMON-NUMERAIRE VALUE`.

## 6. 6A.5 — Developer metrics

Candidate research measures: repositories; contributors; commits; releases;
dependency additions; SDK adoption; package usage; deployed apps.

**Do not treat GitHub activity alone as developer health.** GitHub is a
*secondary* source (Tier E3-ish) for developer research; deployed-app counts
and dependency additions are closer to structural evidence. Developer metrics
are descriptive activity measures, never a health judgment (Axiom 8; §5.3a).
Developer "growth" is a normalized comparison within an explicit cohort, never
an absolute ranking.

## 7. Valuation contract (the canonical Book 5 → Book 6 seam)

Book 6 may plan cross-asset valuation. It is a **measurement product**, owned by
Book 6, referencing a Book 5 vector + a numeraire + a price observation.

```text
ValuationObservation (PLANNED, not implemented)
  valuation_id
  subject_ref                 the valued object (Book 5 component / record / subject)
  native_quantity_ref         Book 5 native quantity (never re-typed)
  native_unit                 the Book 5 native unit (e.g. ETH, USDC, stETH)
  numeraire                   explicit (e.g. USD, BTC) — REQUIRED, no default, no hidden
  price_observation_ref       a cited price observation (see §8)
  price_source                the source class + identity of the price
  price_timestamp             the price's own time
  conversion_methodology_ref  the versioned conversion rule
  valid_time                  when the valuation is true
  observed_at                 when it was computed
  coverage                    how much of the subject was actually valued
  staleness                   declared staleness bound vs price_timestamp
  status                      OBSERVED | SUPERSEDED (never overwritten)
```

Hard rules (mechanically checkable):

1. **No hidden USD assumption.** `numeraire` is a required field with no
   default. There is no "value" without a declared numeraire.
2. **No one-price-fits-all timestamp mismatch.** `price_timestamp` is explicit;
   if prices across components are older than a declared staleness bound, the
   valuation is `STALE_PRICE` (and a state derived from it is
   `INSUFFICIENT_DATA`), not silently computed with mixed timestamps.
3. **No valuation from an observed aggregate unless methodology permits.** A
   common-value total is only valid if the methodology explicitly permits
   aggregating heterogeneous units; a heterogeneous component set is a **vector**
   and a total is a separate, methodology-gated product. Book 5's
   `DERIVED_COMMON_VALUE` remains a Book 6 product only.
4. **Coverage is explicit.** Partial valuation of a vector is partial coverage,
   never a total.
5. **Valuation is descriptive.** A valuation is a measured state, not an
   attractiveness (Axiom 8; §5.3a). No buy/sell framing.

## 8. Price-source ownership (Sensor seam)

### 8.1 Provisional ownership (recorded, not a shared-seam decision)

Book 6 may consume, as measurement/valuation inputs:

- evidence-backed reference prices;
- oracle observations (as Book 2-backed evidence);
- official redemption values (evidence of a redemption rate, not a market price);
- Sensor-exported market observations (for the D8-gated seam; Book 6 consumes,
  does not recompute).

### 8.2 Sensor retains authority for

market-state mechanics: price state, funding, open interest, liquidations,
basis, market regime. Book 6 does not redefine, correct, or recompute any of
these. Book 6 is not a trading price engine and does not become a price source
of record.

**No shared-seam ownership is finalized here** — D8 remains deferred to the Book 8
gate. The above is provisional for Book 6 valuation methodology planning only.

## 9. Price-source class authority (open)

Which price-source class is authoritative for a Book 6 valuation (reference
price vs oracle vs redemption vs Sensor) is a genuine operator decision with
materially different architecture consequences (it determines staleness
handling, comparability, and failure behavior on source divergence) — surfaced
as **D6M-4**. This document does not pre-decide it.

## 10. Native-metrics + valuation verdict

```text
6A_NATIVE_FAMILIES = PLANNED (per-family applicability, NOT_SUPPORTED allowed)
6A_VS_NORMALIZED_ORDER = NATIVE_FIRST (Axiom 1)
VALUATION_CONTRACT = PLANNED (numeraire + price + coverage + staleness explicit)
PRICE_SOURCE_OWNERSHIP = PROVISIONAL (Sensor retains market mechanics; D8 deferred)
BOOK_5_AUTHORITY_BLEED = NONE (Book 5 valuation authority stays FALSE)
LIVE_ACQUISITION_AUTHORITY = FALSE (no source is fetched; planning only)
```

All measurements are planned offline over Book 2-backed evidence. No RPC, no live
acquisition, no production metric pipeline is planned as part of this document.
