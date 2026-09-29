# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — CAPITAL PLUMBING AND ECONOMIC TOPOLOGY — PLAN v0.1

**Document ID:** CSIA-B5-PLAN-001
**Version:** 0.1
**Status:** PLANNING DRAFT — FROZEN FOR OPERATOR REVIEW — NOT RATIFIED
**Authority:** BOOK_5_PLANNING_AUTHORITY = TRUE (post-D7); BOOK_5_IMPLEMENTATION_AUTHORITY = FALSE; LIVE_ACQUISITION_AUTHORITY = FALSE
**Gate closed by:** D7 (Option B) — `CSIA_OPERATOR_DECISION_LOG.md` BOOK 5 DECISION (D7); closure record `CSIA_BOOK_5_CAPITAL_FIELD_D7_DECISION_RECORD_v0.1.md`
**Roadmap dependency:** `CSIA_MASTER_BOOK_BLOC_CHAPTER_ROADMAP_v0.1.md` — BOOK 5 blocs and exit-gate names are used verbatim and unchanged
**Constitution dependency:** v0.2 (§8 identity, §12 temporal, §13 provenance, §19/§19.1 capital plumbing + capability/capacity/flow, §5.3a descriptive boundary, §33–35 status/gates)

---

# 0. Book goal (roadmap-verbatim)

Map how value actually moves and where it becomes:

```text
issued / routed / held / locked / traded / lent / borrowed / collateralized /
staked / restaked / leveraged / transformed / redeemed /
or exits the modeled economic system
```

Book 5 models canonical economic facts (blocs 5A–5F) and derives capital
topology (bloc 5G, per D7 Option B). It remains descriptive (§5.3a); it holds
no trading, execution, or measurement-normalization authority.

## 0.1 Core economic grammar (mechanically preserved everywhere)

```text
CAPABILITY != CAPACITY != FLOW != STOCK != POSITION != CLAIM !=
LIABILITY != EXPOSURE != ECONOMIC PRINCIPAL
```

| Grammar element | Book 5 meaning | Record class |
|---|---|---|
| CAPABILITY | a route/mechanism *exists* (standing fact) | Book 1 capability edges, referenced — never duplicated |
| CAPACITY | measurable size of a capability at a time | NOT a Book 5 record class — measurement (Book 6, §19.1) |
| FLOW | movement observed | append-only event records |
| STOCK | balance observed | temporally versioned observation records |
| POSITION | a holder's persistent claim/liability state at a site | position records (claim-side or liability-side) |
| CLAIM | an entitlement held against a counterparty | typed claim records/roles |
| LIABILITY | an obligation owed by a counterparty | typed liability records/roles |
| EXPOSURE | risk-coupled quantity (notional, OI) | exposure records — never principal |
| ECONOMIC PRINCIPAL | the underlying asset value tracked once | lineage identity — never a summation |

No record may conflate two grammar elements; every cross-reference between
them is a typed pointer, not an equation.

## 0.2 Book 5 planning principles (B5-P1 – B5-P28)

```text
B5-P1  Every capital fact remains Book 2 evidence-backed.
B5-P2  UNKNOWN != ZERO.
B5-P3  Technical route != capital flow.
B5-P4  Route availability != route use.
B5-P5  Supported asset != transferred asset.
B5-P6  Liquidity support != liquidity supplied.
B5-P7  Collateral eligibility != collateral posted.
B5-P8  Borrow capability != debt outstanding.
B5-P9  Staking support != stake outstanding.
B5-P10 Yield capability != yield realized.
B5-P11 Stablecoin deployment != circulating supply.
B5-P12 Derivative notional != economic principal.
B5-P13 Gross exposure != economic principal.
B5-P14 Representation != independent economic principal.
B5-P15 Claim token != underlying asset.
B5-P16 Liability != capital.
B5-P17 Ownership != custody != location != control != liability.
B5-P18 Stocks and flows are separate record classes.
B5-P19 Flows are append-only economic events.
B5-P20 Stocks are temporally versioned observations.
B5-P21 Aggregation is derived and methodology-carrying.
B5-P22 No naive TVL-style summation.
B5-P23 No recursive collateral/deposit multiplication.
B5-P24 Historical capital topology remains replayable.
B5-P25 5G creates no canonical facts.
B5-P26 Book 5 does not absorb Book 6 measurement authority.
B5-P27 Book 5 does not absorb Book 8 market-context authority.
B5-P28 Book 5 has no trading/execution authority.
```

Every bloc contract below cites the principles it enforces. Every stress case
in `CSIA_BOOK_5_CAPITAL_TOPOLOGY_STRESS_MATRIX_v0.1.md` attacks at least one.

---

# 1. Identity contracts

## 1.1 Economic site identity (Phase 7 — first Book 1 extension candidate resolved)

**Decision: Book 5-local typed records** — `EconomicSite` (reference alias
`SiteRef`) — **not** a Book 1 amendment.

- A site is an economic-location object: AMM pool, CLMM pool, lending market, isolated market, vault, staking pool, restaking strategy, perp market, insurance fund, settlement account/domain, RWA issuance vehicle, payment rail endpoint (candidate `site_type` enumeration — not ratified).
- `site_id` is namespaced under the Book 5 record namespace; every site carries mandatory pointers to Book 1 canonical identities: parent protocol/venue `object_id` and, where applicable, `deployment_id` (§8.4). A site never redefines Book 1 identity; it *occupies* it.
- Site lifecycle (migration, deprecation) is expressed with Book 5 temporal fields referencing Book 1 `MIGRATED_FROM/MIGRATED_TO` identity events — never by re-minting Book 1 identities.
- **Escalation criterion to a true Book 1 amendment** (recorded, default not triggered): a site must participate in Book 1 edge domain/range constraints, or require identity-permanence operations (merge/split) at the Book 1 identity-service level. None of the 12 site types requires this for planning; all 12 are classified `BOOK5_LOCAL_SUFFICIENT` (Phase 25 disposition).

## 1.2 Position identity

- `position_id` namespaced; one position = one holder-side (or protocol-side) claim/liability state at one site for one asset/realization.
- Position references: asset `object_id` (canonical economic asset), realization identity where chain-local form matters (R-1A-5: `REALIZES`/`RECEIVED_VIA`), claim-token realization where a wrapper exists, `site_ref`, `location_ref`, custody/control refs where observable.
- Holder/owner: `UNKNOWN` is a legal, first-class value (P2, P17); ownership is never inferred from custody.

## 1.3 Flow / transformation identity

- `flow_id`, `transformation_id`: append-only event identities; immutable once recorded; supersession replaces *records*, never events (P19, §12).
- `principal_lineage_id`: see §5 (principal-lineage doctrine).

## 1.4 Location identity (Phase 23 — candidate ontology, not ratified)

Candidate location types:

```text
ONCHAIN_ACCOUNT  CONTRACT  POOL  MARKET  VAULT  ESCROW  VALIDATOR
CEX  CUSTODIAN  SPV  OFFCHAIN_SETTLEMENT  PAYMENT_ENDPOINT
OUTSIDE_MODELED_SYSTEM  UNKNOWN
```

Rules: UNKNOWN is supported without invented precision (a location is UNKNOWN
or a typed location — never a guessed concrete type); off-chain location types
carry an observability marker so consumers can distinguish observed from
inferred presence; `OUTSIDE_MODELED_SYSTEM` is defined in §7.

---

# 2. Record contracts — canonical position family (Phase 8)

**Candidate family (names are planning candidates, not ratified):**
`CapitalPosition` (family base), `CapitalBalance`, `LiquidityPosition`,
`CollateralPosition`, `DebtPosition`, `StakePosition`, `RestakePosition`,
`YieldPosition`, `SettlementBalance`, `ReserveLiability`.

## 2.1 Shared base fields (all positions)

```text
position_id             identity (1.2)
position_kind           CLAIM_SIDE | LIABILITY_SIDE | CUSTODY_OBSERVATION
asset_ref               canonical economic asset (Book 1 object_id)
realization_ref         chain-local manifestation (optional; REALIZES-backed)
claim_token_ref         wrapper/share token identity (optional)
holder_ref              holder/owner if known; else UNKNOWN
protocol_ref            Book 1 protocol/venue object_id
deployment_ref          Book 1 deployment identity where applicable
site_ref                EconomicSite (1.1)
location_ref            §1.4 location
custody_ref             control/custody identity if observable; else UNKNOWN
liability_counterparty  who owes/is owed (role-linked; nullable by kind)
quantity, unit          observed magnitude + unit (Book 2-backed claim)
valid_from, valid_to    valid time (§12)
observed_at             transaction time (§12)
book2_claim_refs        claim-evidence bindings (mandatory, P1)
encumbrance_state       UNENCUMBERED | PLEDGED | REHYPOTHECATED | UNKNOWN
```

## 2.2 Specializations (added fields only — base is never weakened)

| Specialization | Added fields (candidates) | Governing principles |
|---|---|---|
| CapitalBalance | location-scoped balance; no holder semantics required | P4 (location truth ≠ ownership) |
| LiquidityPosition | pool_ref, range bounds (CLMM: lower/upper or FULL), share quantity | P6 |
| CollateralPosition | collateral_enabled_ref (capability edge ref), posted flag, market_ref | P7 (eligibility edge ≠ posted stock) |
| DebtPosition | market_ref, debtor_ref; liability-side | P8, P16 |
| StakePosition | validator_ref/operator_ref, lock/epoch state, delegation chain refs | P9, §7 separation of delegated control |
| RestakePosition | base_claim_ref (LST or native), operator_ref, AVS/security-target set | principal lineage (§5) |
| YieldPosition | underlying position ref, accrual mechanics ref (descriptive) | P10 (capability ≠ realized) |
| SettlementBalance | venue_ref, segregability state (SEGREGATED | COMMINGLED | UNKNOWN) | P17; rehypothecation stress |
| ReserveLiability | issuer_ref, claim-token ref, backing composition (multi-asset, typed) | P15, P16; liability design — see D5CAP-1 |

## 2.3 Liability representation (Phase 11 design stress — D5CAP-1)

Two designs stressed:

- **(a) Liability as position subtype:** every liability is a `position_kind = LIABILITY_SIDE` record. Pro: uniform query surface. Con: protocol-level obligations exist with no mirror position (bridge backing, LST redemption pool, insurance fund) — forcing them into "positions" invents a phantom holder.
- **(b) Liability as separate typed economic object** (`DebtLiability`, `ReserveLiability`, `RedemptionClaim`) with role-links to positions. Pro: represents holder-less obligations honestly; claims and liabilities remain joinable. Con: two record families to keep consistent.

**Plan recommendation: (b)** — liabilities are separate typed records; positions
carry a `position_kind` and role-links. Recorded as **D5CAP-1** for operator
selection (both designs are defensible; the choice is structural and hard to
reverse). Candidate typed records: `EconomicClaim`, `ReserveLiability`,
`DebtLiability`, `RedemptionClaim`, `ClaimTokenRepresentation`, `Encumbrance`.

**Never flattened (P11 doctrine):** principal ≠ representation ≠ claim ≠
liability ≠ exposure. `Encumbrance` is a typed state linking one asset to the
claims backed by it (LP-collateral, rehypothecation, margin reuse) — never an
additive balance.

---

# 3. Record contracts — flow model (Phase 9)

`CapitalFlow` — append-only economic event. Candidate dimensions:

```text
flow_id                append-only event identity
asset_ref              canonical asset moved (economic principal ref)
realization_ref        chain-local form actually observed moving
quantity, unit         observed magnitude (Book 2-backed)
from_location          §1.4 location (UNKNOWN legal)
to_location            §1.4 location (UNKNOWN legal)
from_position          optional position ref (state before, if modeled)
to_position            optional position ref (state after, if modeled)
from_site, to_site     EconomicSite refs where applicable
capability_route_ref   Book 1 capability edge referenced (optional; P3/P4)
flow_type              candidate enumeration below (NOT ratified)
valid_time/event_time  valid-time instant or interval (§12)
observed_time          transaction time (§12)
book2_claim_refs       claim-evidence bindings (mandatory)
```

Candidate flow types to research (no enum ratified until stress review):

```text
MINT  BURN  TRANSFER  DEPOSIT  WITHDRAWAL  BORROW  REPAY  LIQUIDATION
STAKE  UNSTAKE  RESTAKE  UNRESTAKE  SWAP  BRIDGE_OUT  BRIDGE_IN  REDEEM
YIELD_CREDIT  FEE  SETTLEMENT  PAYMENT  OFF_RAMP
```

Rules: flows never mutate stocks or positions in place (P19); aggregation of
flows (volume) is derived and methodology-carrying (P21); a flow disappearing
from observation is an observability event, never proof of economic exit (§7).

---

# 4. Record contracts — transformation model (Phase 10)

`CapitalTransformation` — a typed form-change with conservation semantics.

Stress forms (all must be representable):

```text
asset → realization            asset → LP claim           asset → vault share
asset → LST                    LST → restaked claim       collateral → debt-backed position
spot collateral → derivative margin                        RWA underlying → tokenized claim
```

Preserved on every transformation:

- `input_claim_ref` and `output_claim_ref` — **distinct identities**, never merged;
- economic principal lineage (`principal_lineage_id`, §5) — the transformation *references* lineage, never mints value;
- liability changes — which liabilities were created/retired/modified (typed refs);
- encumbrance changes — pledges created/released (`Encumbrance` refs);
- custody changes — control hand-offs if observed;
- valid time + observation time (§12);
- Book 2 provenance — transformation facts are claims (P1).

A transformation is never recorded as "capital moved" (that is a flow);
it records that one form became another with principal continuity.

---

# 5. Capital principal-lineage doctrine (Phase 20 — first-class)

**Purpose:** follow ONE underlying economic principal through representation →
claim token → deposit → collateralization → borrowing → restaking → vaulting →
bridge realization → rehypothecation without falsely duplicating value.

**Distinct from Book 1 identity lineage:** Book 1 lineage establishes *the same
object* across space/time (identity permanence, §8.3). Principal lineage
establishes *the same economic value* across forms (asset → claim → exposure).
Book 1 identities are the *nodes' identity anchors*; principal lineage is the
Book 5-specific value-continuity graph.

Candidate representation (**D5CAP-2** — operator selects):

- **(a) typed `CapitalPrincipalLineage` records** forming a DAG: lineage nodes reference claim/representation/position records; edges are transformation/flow events; conservation rules enforce one-principal accounting. Pro: queryable, replayable, cycle-detectable. Con: a new record family.
- **(b) lineage field-chains on transformation/flow records** (each event points to its predecessor lineage pointer). Pro: fewer records. Con: traversal logic lives in consumers; cycle detection and dedup become convention, not contract.

**Plan recommendation: (a).** Conservation rules (either design):

1. every lineage node traces to exactly one economic principal at its root;
2. fan-out (one principal → multiple claims, e.g., LP + collateral + borrow legs) is represented as branching, never as principal multiplication;
3. collapse-to-principal is an explicit, methodology-carrying derivation (5G may perform it; 5A–5F never presume it);
4. cycles (redeposit loops, vault-over-vault, leveraged-LP loops) must be detected; aggregation over a traced cycle reports de-duplicated principal or UNKNOWN — never the naive sum (P22, P23);
5. lineage pointers are mandatory on every position/flow/transformation that participates in multi-form chains.

---

# 6. Stock / flow / exposure algebra (Phase 21 — planning laws, later executable invariants)

```text
ALG-1  STOCK(t) != SUM(FLOW) without an explicit interval + initial state.
ALG-2  A flow never overwrites a historical stock; stocks are versioned (P20).
ALG-3  A liability does not disappear when principal moves (P16).
ALG-4  A claim does not equal its backing asset (P15).
ALG-5  Exposure does not equal capital (P12, P13).
ALG-6  NET cannot be computed without an explicit netting methodology ID.
ALG-7  UNKNOWN cannot participate as zero in any algebra step (P2).
ALG-8  Aggregation over representations requires claim/liability
       classification + principal lineage + dedup (P21, P22, P23).
ALG-9  Gross exposure sums are exposure-domain only; they never enter
       principal-domain totals (P13).
ALG-10 Interval flows require bounded windows; open intervals are UNKNOWN-
       bounded per §12, never silently extended.
```

These are planning laws; executable invariants inherit them at implementation
planning. The double-counting planning theorem (Phase 19) is ALG-8 applied:

> **NO MODEL MAY PRESENT "TOTAL CAPITAL" WITHOUT: claim/liability
> classification, principal lineage, dedup methodology, unknown handling, and
> a methodology ID.**

The ten D7 stress scenarios (USDC→lending; borrowed redeposit; ETH→LST;
LST→restaking; LP collateral; canonical+wrapped; vault shares; perp
collateral-vs-notional; RWA token-vs-underlying; rehypothecation) are promoted
from the D7 stress corpus into **mandatory Book 5 planning tests** — each must
pass under ALG-1..10 before its bloc contract can be considered complete.

---

# 7. System boundary / exit doctrine (Phase 24)

`OUTSIDE_MODELED_SYSTEM` is defined by the modeled-topology boundary: chains,
venues, and sites inside CSIA coverage (Book 3/4 census scope as it evolves).

```text
TRUE ECONOMIC EXIT
  = an observed exit-mechanism event: redemption for fiat, burn without a
    modeled successor, transfer to an off-ramp/payment endpoint beyond the
    modeled topology, transfer to an unmodeled chain/venue.

OBSERVABILITY EXIT
  = a flow disappearing from our data (source gap, scope change, censoring).
```

**This distinction is mandatory.** An observability exit is recorded with
economics UNKNOWN and must never be promoted to a true economic exit; a true
exit requires an observed exit mechanism (P1 evidence, P2 unknown-handling).
Concrete boundary scope (which chains/venues are "modeled") follows coverage
census policy (Books 3C/4 pattern) — not redefined here.

---

# 8. Cross-book boundaries (Phases 22, 26/27 of D7 recon carried forward)

## 8.1 Book 4 ↔ Book 5 (frozen)

Unchanged by D7 and by this plan: Book 4 owns technical dependency, service
consumption, infrastructure roles, failure domains, redundancy,
substitutability, route mechanics; Book 5 owns the economic content. Book 5
*references* Book 4/Book 1 capability edges; it never duplicates route truth
(P3–P5).

## 8.2 Book 5 ↔ Book 6 seam (Phase 22 — resolved rule)

```text
BOOK 5 OWNS (canonical + topology composition):
  raw canonical economic observations, position facts, flow events,
  claim/liability facts, transformations, principal lineage,
  topology composition (5G).

BOOK 6 OWNS (measurement):
  TVL-like aggregate metrics, utilization, concentration, normalized liquidity
  measures, capital efficiency, comparable dimensions, descriptive state
  vectors.
```

Dividing line, exactly: a Book 5 derived aggregate exists to **compose
topology** (its inputs are canonical records; its output is a structural view)
and must be marked `TOPOLOGY_DERIVATION`; a Book 6 metric exists to
**measure/normalize/compare** (its inputs are observations; its output is a
comparable dimension) and is a `MEASUREMENT_METRIC`. Same underlying data may
feed both; authority does not transfer. Book 5 records never carry
measurement-normalization semantics (P26); Book 6 is not amended.

## 8.3 Book 5 ↔ Book 8 seam

Book 5 emits no market-context semantics; no BUY/SELL/BULLISH/BEARISH/TARGET/
ENTRY/EXIT-SIGNAL conclusions (P27, P28; §5.3a; D4). The 5G "exit" term is
bound by the D7-confirmed descriptive exit semantics (§7). D8 (shared-seam
ownership) remains gated at Book 8 planning and is untouched here.

## 8.4 Book 2 dependence

All capital facts are Book 2 claim-evidence pairs (P1). Book 5 introduces no
evidence channel, no source registry, no promotion path. Contradictory capital
evidence follows Book 2 contradiction doctrine (F-2 time-split, F-5
never-average).

## 8.5 Book 1 extension candidates — final dispositions (Phase 25)

| # | Candidate | Disposition |
|---|---|---|
| 1 | position-site identity | BOOK5_LOCAL_SUFFICIENT (EconomicSite, §1.1; escalation criteria recorded) |
| 2 | per-position claim/liability/custody | BOOK5_LOCAL_SUFFICIENT (Book 5 record classes; Book 1 edges remain entity-level) |
| 3 | off-chain/unknown location | BOOK5_LOCAL_SUFFICIENT (§1.4 location ontology is Book 5-local) |
| 4 | flow-event field contract | BOOK5_LOCAL_SUFFICIENT (roadmap assigns capital-flow modeling to Book 5; Book 1 keeps capability-edge vocabulary + event-object principle) |

**BOOK_1_AMENDMENT_REQUIRED = FALSE.** No Book 1 mutation occurs; escalation
remains possible only via the recorded criterion (§1.1) and §36 amendment
procedure with operator ratification.

---

# 9. Temporal and evidence contracts

- **Temporal (§12, binding):** every record carries `valid_from`/`valid_to` (valid time) and `observed_at` (transaction time); `superseded_at` records record-replacement; current state never overwrites prior state (P20, P24); late discovery enters the transaction axis late; UNKNOWN valid time carries explicit uncertainty representation.
- **Replay (P24):** historical topology must be reconstructible at any valid time from canonical records + derived-methodology versions; 5G snapshots are reproducible artifacts (§29 pattern).
- **Evidence (P1):** every quantitative field and every existence claim binds `book2_claim_refs`; quantities are observations with tier + claim state; a missing observation is UNKNOWN (P2); zero requires an observed zero.

---

# 10. Double-counting doctrine (Phase 19 binding summary)

1. Representations are linked, never summed (principal-lineage links).
2. Liabilities are records, not negative capital and not invisible (P16).
3. Exposure quantities never enter principal sums (P12, P13).
4. Off-chain value equivalence requires redemption/backing evidence; absent evidence → UNKNOWN.
5. Recursion loops must be traceable and de-duplicated or reported UNKNOWN (P23).
6. Encumbrance is a typed state; "available" and "pledged" are different stocks.
7. The planning theorem of §6 binds every bloc and 5G.

---

# 11. Bloc 5G derived-only doctrine (D7 binding)

```text
5G MAY DERIVE FROM CANONICAL CAPITAL FACTS.
5G MAY NOT CREATE CANONICAL CAPITAL FACTS.
```

5G consumes 5A–5F records by pointer; its outputs (candidate shapes:
`CapitalFieldSnapshot`, `CapitalFieldPath`, `CapitalPrincipalLineage` views,
`CapitalTopologyView` — names not ratified; representation = D5CAP-3) must
carry input record refs, methodology/version, valid time, observation time,
principal-collapse methodology, liability treatment, exposure treatment, and
unknown propagation. 5G cannot invent an observation; a missing input makes the
dependent output UNKNOWN/INCOMPLETE, never fabricated. Full contract: §12
(Bloc 5G) and `CSIA_BOOK_5_CAPITAL_FIELD_SYNTHESIS_MATRIX_v0.1.md`.

---

# 12. Implementation prohibitions (binding on any future implementation)

```text
NO BOOK 5 IMPLEMENTATION IS AUTHORIZED BY THIS PLAN.
NO LIVE ACQUISITION. NO RPC. NO DATABASE. NO GRAPH DATABASE.
NO BOOK 1/2/3/4 MUTATION. NO SENSOR MUTATION.
NO CAPITAL FIELD INDEPENDENT AUTHORITY. NO 5G CANONICAL WRITES.
NO NAIVE TVL AGGREGATION. NO CLAIM=PRINCIPAL COLLAPSE.
NO NOTIONAL=CAPITAL COLLAPSE. NO UNKNOWN=ZERO.
NO TRADING SIGNALS. NO EXECUTION LOGIC. NO SILENT UPSTREAM AMENDMENT.
```

---

# 13. Exit gates (roadmap-verbatim names)

```text
BLOC 5A  PASS_CSIA_B5A_STABLECOIN_RAILS
BLOC 5B  PASS_CSIA_B5B_LIQUIDITY_TOPOLOGY
BLOC 5C  PASS_CSIA_B5C_CREDIT_TOPOLOGY
BLOC 5D  PASS_CSIA_B5D_YIELD_TOPOLOGY
BLOC 5E  PASS_CSIA_B5E_DERIVATIVE_TOPOLOGY
BLOC 5F  PASS_CSIA_B5F_RWA_PAYMENT_TOPOLOGY
BLOC 5G  PASS_CSIA_B5_CAPITAL_FIELD_V1
```

Per-bloc exit evidence requirements are stated in each bloc contract
(§14–§20). Bloc completion requires exit evidence per Constitution §33–35; no
bloc is complete because documents exist.

---

# 14. Open operator decisions (D5CAP namespace — Phase 31)

Created only where multiple defensible designs exist and the choice is
structural. Details and selection blocks: `CSIA_BOOK_5_OPERATOR_DECISIONS_D5CAP_v0.1.md`.

```text
D5CAP-1  Liability representation: separate typed economic objects
         (recommended) vs liability-as-position-subtype.
D5CAP-2  Principal-lineage representation: typed CapitalPrincipalLineage DAG
         records (recommended) vs lineage field-chains on events.
D5CAP-3  5G output shape: versioned CapitalFieldSnapshot compositions +
         CapitalTopologyView projections (recommended) vs single view model.
```

Explicitly **not** opened as operator decisions (answered by doctrine or
plan-level ratification): site identity location (D7 recon default, §1.1);
flow-type enum closure (candidate enum ratifies at plan review with a §9.3-style
extension procedure); location-type list (§1.4, ratifies at plan review);
Book 6 seam rule (§8.2, doctrine-consistent); exit boundary predicate (§7).

---

# 15. Stress results and plan status (summary; full matrices are companion artifacts)

- Capital topology stress matrix: `CSIA_BOOK_5_CAPITAL_TOPOLOGY_STRESS_MATRIX_v0.1.md` — 22 stress areas; result recorded there and in the pre-ratification review.
- Primitive matrix reconciliation: `CSIA_BOOK_5_ECONOMIC_PRIMITIVE_CANDIDATE_MATRIX_v0.2.md`.
- Relationship support: `CSIA_BOOK_5_RELATIONSHIP_SUPPORT_MATRIX_v0.1.md`.
- 5G synthesis proof: `CSIA_BOOK_5_CAPITAL_FIELD_SYNTHESIS_MATRIX_v0.1.md`.
- Pre-ratification review: `CSIA_BOOK_5_PRE_RATIFICATION_REVIEW_v0.1.md` — 20 adversarial questions; any structural failure sets `BOOK_5_PLAN = HOLD`.

Bloc contracts 5A–5G follow in §16–§22 (appended as planning sessions
complete them; see commit history for the assembled sequence).

---

# 16. BLOC 5A — STABLECOIN RAILS (Phase 12 contract)

**Mission:** model stablecoin economic truth — issuance, distribution,
realization forms, and redemption liabilities — without ever double-counting
supply across representations.

**Scope:** canonical stablecoin identity (Book 1 STABLECOIN class), issuer
entities, deployments (§8.4), REALIZATION forms (R-1A-5), mint/burn,
circulating-supply observation, bridge escrow, wrapped representations,
redemption claims, chain distribution.

**Non-goals:** price/depeg measurement policy (Book 6), issuer credit analysis,
market-share ranking (§5.3a), Sensor seam semantics (D8).

**Canonical records:** `StablecoinSupply` observation (typed, per §12 splits
below); `MINT` / `BURN` flows; `BRIDGE_IN`/`BRIDGE_OUT` flows;
`ReserveLiability` (issuer/bridge redemption); escrow balance records
(location-typed ESCROW); `ClaimTokenRepresentation` links for wrapped forms.

**Derived records:** chain-distribution views (`TOPOLOGY_DERIVATION`),
de-duplicated canonical supply (methodology-carrying only).

**Identity requirements:** canonical stablecoin `object_id`; issuer ENTITY;
per-chain deployments; realization refs (`REALIZES`/`RECEIVED_VIA`); escrow
sites; wrapped-token claim links to canonical asset.

**Explicit separations (mandatory record splits — no summed global supply
without methodology + de-duplication):**

```text
TOTAL ISSUANCE            = all minted units ever (issuer-side observation)
CANONICAL-SIDE CIRCULATING = circulating on the canonical/issuing chain
CHAIN-LOCAL CIRCULATING   = circulating on one specific chain (per realization)
BRIDGED REALIZATION SUPPLY = supply counted as a realization of the canonical
                            asset (linked, never additive to canonical supply)
ESCROW BACKING            = assets locked backing wrapped realizations
REDEMPTION LIABILITY      = what issuer/bridge owes claim holders
```

**Book 2 evidence:** supply observations bind claim refs (issuer dashboards,
E0 on-chain totals where deterministic); mint/burn bind E0 events.
**Stress cases:** multi-chain USDT/USDC-like; DAI-like decentralized
(governance-minted); synthetic-dollar systems (derivative-backed — crosses to
5E semantics); bridged canonical+wrapped (D7 stress 1.6); depegged claim token;
contested supply figures (F-2/F-5 doctrine).
**Principles enforced:** B5-P2, P11, P14, P15, P16, P18–P22.
**Exit gate:** `PASS_CSIA_B5A_STABLECOIN_RAILS` — evidence: the six-way split
is representable without summation for a 3-chain stablecoin + 1 wrapped
realization pilot; canonical+wrapped double-count case fails closed.

---

# 17. BLOC 5B — DEX / LIQUIDITY TOPOLOGY (Phase 13 contract)

**Mission:** model pool-level liquidity truth and observed trading flows,
keeping stocks, claims, and derived volume strictly separate.

**Scope:** AMM pools; CLMM pools; LP positions; vault-managed liquidity;
aggregators; intent systems; actual routed flow.

**Non-goals:** execution routing, price analytics, MEV strategy (structural MEV
value capture per §19.2 is modeled descriptively), aggregator scoring.

**Canonical records:** pool `EconomicSite`s (AMM_POOL, CLMM_POOL); reserve
balances (stocks at sites); `LiquidityPosition` (LP claim incl. CLMM range
state); `SWAP` / `DEPOSIT` / `WITHDRAWAL` flows; intent-fill events;
`ClaimTokenRepresentation` for LP tokens; vault positions where vaults manage
liquidity.

**Derived records:** volume aggregations; depth/active-liquidity views —
`TOPOLOGY_DERIVATION` only; route-use observations (`ROUTED_THROUGH`-
referencing flows).

**Mandatory separations:**

```text
pool reserves      = stock (protocol-controlled balance)
LP claim           = position/claim (LiquidityPosition)
liquidity range    = position state (CLMM sub-field, not a separate pool)
swap               = flow
volume             = derived aggregation (methodology ID required)
route              = capability (Book 1/Book 4 edge, referenced)
routed flow        = observed flow (Book 5 event referencing the capability)
```

P6 (liquidity support ≠ supplied) and P3/P4 (route ≠ use) are structural: an
integrated/pool-existing fact is never recorded as reserves; a routed path is
never inferred from route existence.

**Book 2 evidence:** reserves E0 (contract state); swaps E0 (event logs);
volume aggregation methodology recorded.
**Stress cases:** CLMM active-vs-idle capital; vault-over-pool nesting;
aggregator multi-hop attribution (which hop carries the flow); intent fill vs
route; zero-liquidity pools; UNKNOWN pool ownership.
**Principles enforced:** B5-P3, P4, P6, P14, P18–P22.
**Exit gate:** `PASS_CSIA_B5B_LIQUIDITY_TOPOLOGY` — evidence: reserves/claim/
range/flow/volume/route/routed-flow seven-way split demonstrated on an AMM +
CLMM + aggregator pilot; volume never presented without methodology ID.

---

# 18. BLOC 5C — CREDIT / LENDING (Phase 14 contract)

**Mission:** model lending markets as claims and liabilities — never as
additive pools of capital.

**Scope:** supply positions; collateral positions; debt positions; available
liquidity; borrow/repay flows; liquidation; bad debt; reserves; encumbrance.
Aave-like pools, Morpho-like markets, Compound-like markets, isolated
chain-native money markets.

**Non-goals:** rate/interest-rate modeling policy (rates are protocol
mechanics; realized yield flows cross to 5D semantics where claimed),
risk scoring, liquidator strategy.

**Canonical records:** market `EconomicSite`s (LENDING_MARKET, ISOLATED_MARKET);
`CollateralPosition` (posted stock + encumbrance state);
`DebtPosition` (liability-side); supply claims; `BORROW`/`REPAY`/`DEPOSIT`/
`WITHDRAWAL`/`LIQUIDATION` flows; `DebtLiability` records; bad-debt
socialization events; market reserve stocks; `Encumbrance` links.

**Derived records:** available-liquidity residuals; utilization views —
marked `TOPOLOGY_DERIVATION`; anything normalized is Book 6 territory (P26).

**Forbidden identifications (structural):**

```text
collateral-enabled (capability edge ref)  !=  collateral-posted (stock)
supplied + borrowed                       !=  additive economic principal
                                            (supplied is principal pledged;
                                             borrowed is a liability against it)
```

**Book 2 evidence:** positions/balances E0 (contract state); liquidations E0;
bad-debt events E0/E1; market-configuration facts E0 (deterministic contract
reads).
**Stress cases:** D7 1.1 (deposit), 1.2 (borrowed redeposit — principal
lineage through market B), 1.5 (LP collateral); liquidation chains; bad debt
absorption; isolated-market segmentation (one market's collateral must never
back another market's debt in the model); multi-collateral netting (ALG-6).
**Principles enforced:** B5-P7, P8, P16, P17, P19–P23.
**Exit gate:** `PASS_CSIA_B5C_CREDIT_TOPOLOGY` — evidence: supplied/borrowed/
available/posted/eligibility/liability/socialization split demonstrated;
supplied+borrowed summation case fails closed; borrowed-redeposit lineage
de-duplicates.
