# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — ECONOMIC PRIMITIVE CANDIDATE MATRIX v0.2

**Document ID:** CSIA-B5-D7-PRIM-002
**Version:** 0.2
**Status:** PLANNING RECONCILIATION — NOT RATIFIED
**Input:** `CSIA_BOOK_5_ECONOMIC_PRIMITIVE_CANDIDATE_MATRIX_v0.1.md` reconciled after detailed bloc planning (plan v0.1 §1–§4, §16–§22) and the stress matrix.
**Action vocabulary:** KEEP / MERGE / SPLIT / RENAME / DEFER / REJECT. Still planning-only; final names ratify with the plan.

---

# 0. Reconciliation summary

```text
v0.1 CANDIDATES CONSIDERED = 20
KEEP              = 9
MERGE             = 4 (absorbed into 2 records)
SPLIT             = 3 (yield 4 records)
RENAME            = 3
DEFER             = 3
REJECT            = 1
NET RECORD FAMILY = 16 distinct record classes planned
```

---

# 1. Per-candidate disposition

| v0.1 # | v0.1 candidate | Disposition | v0.2 result | Rationale (planning detail) |
|---|---|---|---|---|
| 1 | CapitalPosition | KEEP (renamed role) | **CapitalPosition** = family base record with `position_kind` (CLAIM_SIDE / LIABILITY_SIDE / CUSTODY_OBSERVATION) | plan §2.1–2.2: shared base + specializations; liability-side retained pending D5CAP-1 |
| 2 | CapitalBalance | MERGE | → `CapitalPosition` with `position_kind = CUSTODY_OBSERVATION` + no holder semantics | plan §2.2: location truth ≠ ownership; a plain balance is the custody-observation kind |
| 3 | CapitalFlow | KEEP | **CapitalFlow** — append-only event | plan §3; 21-type candidate enum; not ratified until stress review (done — stress matrix rows pass; enum ratifies at plan review) |
| 4 | LiquidityPosition | KEEP | **LiquidityPosition** (+CLMM range sub-state) | plan §17; range is position state, not a separate pool |
| 5 | CollateralPosition | KEEP | **CollateralPosition** | plan §2.2; eligibility capability ref ≠ posted stock (P7) |
| 6 | DebtPosition | KEEP | **DebtPosition** (liability-side; pairs with DebtLiability per D5CAP-1) | plan §2.2–2.3 |
| 7 | StakePosition | KEEP | **StakePosition** | plan §19; delegation chain refs |
| 8 | RestakePosition | KEEP | **RestakePosition** | plan §19; AVS/security-target sets |
| 9 | YieldPosition | SPLIT | → **YieldPosition** (claim) + **YieldRealization** (flow) | v0.1 ambiguity (#9/#10 in plan terms): the claim and the credited yield are different grammar elements (P10) |
| 10 | YieldRealization | SPLIT (with 9) | → **YieldRealization** flow (YIELD_CREDIT flow type) | plan §3 enum; accrual-vs-claimed-vs-compounded distinction preserved as record states |
| 11 | DerivativeExposure | KEEP | **DerivativeExposure** — exposure-domain record | plan §20; never principal (P12/P13) |
| 12 | SettlementBalance | KEEP | **SettlementBalance** (+segregability state) | plan §20; rehypothecation-relevant |
| 13 | StablecoinSupply | SPLIT | → six-way typed supply observations per plan §16 (TOTAL_ISSUANCE / CANONICAL_CIRCULATING / CHAIN_LOCAL_CIRCULATING / BRIDGED_REALIZATION / ESCROW_BACKING / REDEMPTION_LIABILITY) as supply-record `supply_kind` values | single record class with enforced kind split beats six overlapping classes; summation without methodology is structurally prevented |
| 14 | LockedCapital | RENAME | → **reserved-stocks at sites** (site balance records) + **TVL views demoted to derived** | plan §17/§8.2: TVL-style aggregates are `TOPOLOGY_DERIVATION` (5G) or `MEASUREMENT_METRIC` (Book 6) — never a canonical primitive |
| 15 | CapitalRoute | SPLIT | → capability refs (Book 1 edges, referenced) + **routed-flow observations** (CapitalFlow with `capability_route_ref`) | plan §17/§8.1: route truth stays in Book 1/Book 4; Book 5 records only use |
| 16 | CapitalTransformation | KEEP | **CapitalTransformation** | plan §4; input/output claims distinct; lineage refs mandatory |
| 17 | CapitalConcentration | DEFER | → Book 6 measurement candidate (concentration is a normalized metric) | plan §8.2 dividing line; nothing Book 5-canonical to record |
| 18 | CapitalExit | KEEP (renamed) | → **exit flows** (`OFF_RAMP`/`REDEEM`/`BURN` flows with `OUTSIDE_MODELED_SYSTEM` semantics) | plan §7: exit is a flow/semantics, not a standalone record class |
| 19 | ReserveLiability | KEEP | **ReserveLiability** (+ DebtLiability, RedemptionClaim per D5CAP-1) | plan §2.3; holder-less obligations need their own records |
| 20 | ClaimTokenRepresentation | KEEP | **ClaimTokenRepresentation** (+ **EconomicClaim**, **Encumbrance** as siblings from Phase 11) | plan §2.3/§5; the claim-vs-underlying link that prevents double counting |

# 2. Net planned record family (v0.2)

```text
POSITIONS      CapitalPosition (base) with kinds: CapitalBalance(kind),
               LiquidityPosition, CollateralPosition, DebtPosition,
               StakePosition, RestakePosition, YieldPosition,
               SettlementBalance
EVENTS         CapitalFlow (21-type candidate enum), CapitalTransformation
CLAIMS/LIAB.   EconomicClaim, ReserveLiability, DebtLiability,
               RedemptionClaim, ClaimTokenRepresentation, Encumbrance
LINKS/IDS      EconomicSite (SiteRef), location ontology (§1.4),
               principal_lineage_id (§5)
EXPOSURE       DerivativeExposure
SUPPLY         StablecoinSupply (six-kind split)
DEFERRED       CapitalConcentration (Book 6), CapitalConcentration lineage
```

All names remain planning candidates until plan ratification.

# 3. Reconciliation cross-checks

- Every grammar element (§0.1) has at least one record class; no class spans two grammar elements.
- The 10-scenario D7 corpus and 25-row stress matrix pass against this family (see stress matrix result block).
- Position family shrink (10 → 9 + base) and supply split follow the directive's "determine shared base fields vs specialized fields" requirement (plan §2).
