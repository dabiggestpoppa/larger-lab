# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — ECONOMIC PRIMITIVE CANDIDATE MATRIX (D7 RECONNAISSANCE)

**Document ID:** CSIA-B5-D7-PRIM-001
**Version:** 0.1
**Status:** EXPLORATORY CANDIDATE INVENTORY — NOT RATIFIED — NOT A BOOK 5 PLAN
**Gate:** D7 OPEN. No name, record class, or field below is canonical. Nothing here may be implemented before D7 closes and a ratified Book 5 plan exists.

---

# 0. Purpose

Directive Phase 6: identify the minimum economic primitives Book 5 may need, record the identity/ownership questions each must answer, and highlight where identity is missing or ambiguous. These are **candidate asks**, collected so the operator's D7 decision (and later Book 5 planning) has a complete requirements surface. Names are placeholders.

Grounding rules inherited from ratified doctrine:

- object identity per Constitution §8 (namespaced IDs, immutable in meaning, deployments per §8.4);
- realization identity per R-1A-5 (REALIZATION; REALIZES / RECEIVED_VIA edges; INV-1A-9 no realization→realization);
- claim states and evidence per Book 2 (every fact enters via claim-evidence pairs);
- bitemporal fields per §12 (`observed_at`, `valid_from`, `valid_to`, `source_published_at`, `ingested_at`, `superseded_at`);
- capability/capacity/flow classes per §19.1 (Book 6 owns capacity measurement; flows are events);
- UNKNOWN ≠ zero per Axiom 6.

Every candidate record below must answer: **object identity / asset identity / owner-holder identity (if known) / protocol-venue identity / chain-deployment identity / quantity / unit / valid time / observation time / source (Book 2 claim refs) / stock-vs-flow / observed-vs-derived / point-in-time-vs-interval / direct-vs-synthesized.** The "Ambiguity" column marks identity gaps discovered during this reconnaissance.

---

# 1. Candidate primitive inventory

| # | Candidate | Kind (stock/flow/rel/event) | What it would represent | Required identities | Ambiguity / missing identity found |
|---|---|---|---|---|---|
| 1 | CapitalPosition | stock | a holder's claim or liability balance in a protocol | position_id; canonical asset + realization; holder (or UNKNOWN); protocol deployment; chain; qty; unit | Holder attribution is frequently UNKNOWN (proxy/smart wallets, LP NFTs, ERC-4337); "position" vs "balance" boundary needs planning; netting rule (multi-collateral) undefined |
| 2 | CapitalBalance | stock | raw observed balance of an asset at a location (contract/account) | balance_id; asset; location (address or contract slot); chain; qty | Without holder semantics it is location truth only; must not silently be promoted to ownership (P4) |
| 3 | CapitalFlow | flow (event) | observed movement of value between states/locations A→B in valid time T | flow_id; asset (+realizations both sides); from-location; to-location; qty; interval; capability-edge ref (optional) | From/to "location" ontology for CEX/off-chain legs does not exist yet; aggregated "volume" is derived, not an event |
| 4 | LiquidityPosition | stock | LP claim on a pool (fungible LP token or concentrated range) | position_id; pool_id; LP-token/realization; owner; range bounds (CLMM); qty | Range liquidity (CLMM) is not a single scalar; active-vs-idle capital distinction needed; pool_id identity not yet defined anywhere |
| 5 | CollateralPosition | stock | asset posted as collateral in a market | position_id; asset; market; owner; collateral-flag state; qty | Eligibility (capability) vs posted (stock) must be two records (P5); collateral factor is methodology (Book 6) |
| 6 | DebtPosition | stock (liability) | outstanding borrow against a market | position_id; asset; market; debtor; qty | Liability side of #1; bad-debt socialization turns position liability into protocol-level loss event — needs its own flow record |
| 7 | StakePosition | stock | capital bonded to a validator/protocol for security | position_id; asset; validator/operator; delegator; qty; lock/epoch state | Delegation chains (delegator→operator→validator) need multi-hop identity; native vs delegated control split (§7 ownership table) |
| 8 | RestakePosition | stock | restaked claim securing additional AVS/economic-security sets | position_id; base claim (LST or native); operator; AVS set; qty | Second-order collateral graphs (§19.2): slashing liability chains; strategy-token identity for restaking receipts |
| 9 | YieldPosition | stock | claim accruing yield (vault share, staking derivative) | position_id; underlying asset; wrapper/claim token realization; owner; qty | "Yield" itself is a flow (realized) — position is the claim, not the yield (P11); reward-distribution mechanics vary per protocol |
| 10 | YieldRealization | flow | observed yield credited/claimed/compounded | flow_id; position ref; reward asset; qty; interval | Distinguish accrued-but-unclaimed vs claimed vs auto-compounded; all are different observations |
| 11 | DerivativeExposure | stock (derived exposure) | notional/oi/PnL state of a derivative position | position_id; instrument; venue; collateral ref; notional; direction; unrealized PnL | Notional ≠ principal (P12); exposure is derived from collateral+price observations → observation-time coupling; venue (CEX) data often aggregate-only |
| 12 | SettlementBalance | stock | assets held for settlement/clearing (venue, clearing contract, insurance fund) | balance_id; venue/contract; asset; qty | CEX settlement assets are not per-user attributable from public data; insurance-fund ownership semantics (socialized) unclear |
| 13 | StablecoinSupply | stock | circulating supply of a stablecoin (canonical, per realization) | supply_id; canonical stablecoin; realization/deployment; issuer liability ref; qty; methodology | Canonical vs per-chain circulating vs total issuance — three different stocks; mint/burn events are the flows; depeg state is Book 6 measurement |
| 14 | LockedCapital | stock | capital locked in a protocol contract (TVL-like) | balance_id; contract; asset; qty; methodology_id | TVL is a *derived aggregate* of balances under a methodology — must never be a primary record; methodology preserved per §19 ("Every metric must preserve methodology") |
| 15 | CapitalRoute | relation/event | a capital path (capability) or an observed route use (flow) | route_id (capability edge ref); or flow_id for the use | Reuse Book 1 capability edges for capability; Book 5 records only the *use* — do not duplicate route truth (P3) |
| 16 | CapitalTransformation | event | typed form-change: input claim → output claim | transformation_id; input claim id; output claim id; transformation type; valid time | Transformation-type taxonomy (mint, wrap, deposit, borrow, stake, LP, bridge-in…) must be enumerated in Book 5 planning; input/output are distinct identities (§6 of reconciliation doc) |
| 17 | CapitalConcentration | derived stock | distribution of a capital stock across holders/venues (e.g., top-N share) | metric_id; underlying stock set; window; methodology_id | Strictly derived (Book 5 records facts; distribution is a computed view); risk of smuggling judgment — must stay descriptive (P18) |
| 18 | CapitalExit | flow | capital leaving the modeled system boundary (redemption, burn, bridge-out beyond boundary, off-ramp) | flow_id; asset; from-location; exit-mechanism; qty | "Exit" is economic-topology vocabulary only (P17 guard) — must never be rendered as a trade signal; boundary definition ("what is outside the system") needs an explicit operator-ratified definition in Book 5 planning |
| 19 | ReserveLiability | stock (liability) | what a protocol owes against issued claims (LST redemption, vault share backing, bridge backing) | liability_id; issuer/protocol; claim token; backing asset; qty | Backing may be compositional (multi-asset) — netting rules required; insolvency is a state, not an inferred judgment |
| 20 | ClaimTokenRepresentation | relation | links a claim token (LP/LST/restake/vault/RWA) to its underlying claim and issuer | link_id; claim token realization; underlying canonical asset; liability ref | This generalizes REALIZATION: realization covers asset-vs-chain-local form; claim-vs-underlying needs an explicit typed link to avoid double counting (stress matrix #7/#9) |

**Not created here:** any schema, enum, file, or code. These are candidate asks only.

---

# 2. Cross-cutting identity findings

1. **Holder/owner identity is the largest gap.** On-chain positions are often attributable; CEX, SPV, and institutional legs usually are not. Every candidate that names an owner must allow `UNKNOWN` (P16) without downgrading the record's other fields.
2. **Realization vs claim-token distinction.** R-1A-5 REALIZATION covers chain-local manifestations of one canonical asset (wraps, bridges). LP/LST/vault/restake tokens are **claims with liabilities**, not mere realizations; conflating them would double-count principal (stress matrix). Candidate #20 exists precisely to keep these separate.
3. **Pool/market/venue identity is undefined upstream.** Book 1 has PROTOCOL/DEX/LENDING_PROTOCOL classes but no per-market/per-pool/per-vault sub-object identity doctrine. Book 5 planning will need a position-site identity scheme (extension candidate, not an amendment).
4. **Location ontology for off-chain legs.** CapitalFlow needs from/to location semantics that include CEX custody, SPVs, and "outside modeled system" (exit). None exists; Book 5 planning must define it.
5. **Stock-vs-flow is a record-class split, not a field.** Candidates are pre-classified above; aggregation rules (netting, summing, interval selection) must be derived-view-only with methodology pointers (reconciliation doc §5.3).
6. **All quantitative fields are observations.** Quantities enter as Book 2-backed claims with tier, claim state, and methodology; Book 5 adds no truth channel (P1).

---

# 3. Directive alignment

- This matrix answers Phase 6 "identify minimum economic primitives… For each candidate record ask…" and Phase 5's per-candidate identity checklist.
- It ratifies nothing; names are placeholders pending D7 and a ratified Book 5 plan.
- It feeds, and is cross-referenced by, the double-counting stress matrix (which stress-tests these candidates against the 10 mandatory scenarios) and the boundary review (Book 1/Book 6 ownership of the gaps found here).
