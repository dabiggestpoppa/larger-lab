# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — RELATIONSHIP SUPPORT MATRIX v0.1

**Document ID:** CSIA-B5-REL-001
**Version:** 0.1
**Status:** PLANNING MATRIX — NOT RATIFIED
**Purpose:** map which frozen Book 1 relations Book 5 faithfully reuses, and which semantics must remain typed Book 5 records. **No relation addition without proven need** — this matrix proposes zero new Book 1 relations.

**Sources of truth:** Book 1 plan v0.3 edge dictionary (contractual), frozen `relationships.py` `EdgeType` (42-class registry era incl. REALIZES/RECEIVED_VIA), `book4_boundary.py` (`BOOK5_ECONOMIC_RELATIONS` — the economic set Book 4 may never use), Constitution §10/§19.1.

---

# 1. Reused Book 1 relations

| Relation | Book 5 reuse semantics | Constraint (never violated) | Records that reference it |
|---|---|---|---|
| `COLLATERAL_IN` | standing capability: asset is collateral-eligible at a site | capability ≠ posted (P7); no magnitudes on capability edges (INV-1C-4 doctrine) | CollateralPosition.capability_ref |
| `LIQUIDITY_ON` | standing capability: asset may supply liquidity at a site | support ≠ supplied (P6) | LiquidityPosition capability refs |
| `STAKED_IN` | standing capability: staking supported at validator/pool | support ≠ stake outstanding (P9) | StakePosition capability refs |
| `RESTAKED_IN` | standing capability: restaking supported at strategy/AVS | capability ≠ restaked position | RestakePosition capability refs |
| `REDEEMS_FOR` | standing capability: claim token redeems for underlying | capability ≠ observed redemption (flow) | RedemptionClaim refs; REDEEM flows |
| `ISSUED_ON` | issuance fact: stablecoin/token issued on chain | issuance ≠ circulating supply (P11) | StablecoinSupply context |
| `NATIVE_TO` | nativity fact for canonical assets | — | supply/realization context |
| `WRAPS` | wrapping relation: wrapped form ↔ canonical | wrapped ≠ independent principal (P14) | ClaimTokenRepresentation |
| `ROUTED_THROUGH` | standing route capability | route ≠ flow (P3/P4) | CapitalFlow.capability_route_ref |
| `MIGRATED_FROM` / `MIGRATED_TO` | identity-migration events (Book 1 lifecycle) | site/position migration references these; never re-mints identities | EconomicSite lifecycle; position migration events |
| `OWNED_BY` | entity-level ownership of objects | entity ownership ≠ per-position holder claim (plan §1.2 keeps holder separate) | holder attribution context |
| `OPERATED_BY` | entity-level operation/control | control ≠ ownership (P17) | custody/control attribution context |
| `REALIZES` | canonical asset ↔ chain-local manifestation (R-1A-5) | realization ≠ new economic asset (P14) | realization_ref fields; supply kinds |
| `RECEIVED_VIA` | acquisition of a realization via a route (R-1A-5) | route-receipt ≠ flow amount (P3/P4) | flow context |

**Reuse rule:** Book 5 records *reference* these edges as capability/identity
anchors. Book 5 never populates Book 1 edges with capital magnitudes, never
redefines their semantics, and never duplicates their truth into parallel
relations.

# 2. What must stay in typed Book 5 records (no Book 1 relation exists or should)

| Semantics | Book 5 home | Why not a Book 1 edge |
|---|---|---|
| per-position claims/liabilities (holder ↔ site ↔ asset state) | position family + EconomicClaim/DebtLiability/ReserveLiability | Book 1 edges connect *objects*; positions are stateful economic facts with magnitudes and bitemporal observation — flow/stock domain (§19.1), not identity edges |
| observed flows (movement events with quantities) | CapitalFlow | flows are event objects referencing edges (§19.1; Q15); magnitudes cannot live on edges |
| transformations (form-change with lineage) | CapitalTransformation | not a pairwise object relation; a typed event with input/output claims |
| encumbrance/rehypothecation chains | Encumbrance records | a state chain over positions, not a standing edge |
| exposure (notional/OI) | DerivativeExposure | magnitude-bearing, temporal, exposure-domain — anti-edge by INV-1C-4 doctrine |
| supply observations (six kinds) | StablecoinSupply | measured stock, Book 2-backed |
| principal lineage | principal_lineage_id graph (§5) | value-continuity is Book 5-specific (plan §5); not object identity |
| sites (pools/markets/vaults/…) | EconomicSite | deliberate Book 5-local resolution (plan §1.1) |

# 3. Result

```text
BOOK_1_RELATIONS_REUSED      = 15 (all faithful reuses; zero semantic drift)
NEW_BOOK_1_RELATIONS_PROPOSED = 0
BOOK_5_LOCAL_RECORD_SEMANTICS = 9 groups (table §2)
BOOK_1_AMENDMENT_REQUIRED     = FALSE
PROVEN_NEED_TEST              = applied per candidate; none passed the bar
```
