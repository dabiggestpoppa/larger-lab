# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — ECONOMIC PRIMITIVE CANDIDATE MATRIX v0.3

**Document ID:** CSIA-B5-D7-PRIM-003
**Version:** 0.3
**Status:** PLANNING RECONCILIATION — NOT RATIFIED
**Input:** v0.2 (preserved) reconciled after the single-root repair (`CSIA_BOOK_5_PRINCIPAL_LINEAGE_RECONCILIATION_v0.1.md`), D5CAP-1/2/3 decisions, and plan v0.2.

---

# 0. v0.3 changes from v0.2

```text
ADDED   PrincipalContribution (typed contribution edge)        NEW
ADDED   AttributionState (typed enum on components/edges)      NEW
ADDED   CapitalPrincipalLineageView (derived 5G projection)    NEW (D5CAP-3 rename)
RENAMED lineage field: principal_lineage_id → principal_component_refs
        on multi-principal claims (singular id retained for EXACT chains)
BOUND   CapitalPrincipalLineage = CANONICAL (D5CAP-2 A-REVISED)
BOUND   DebtLiability/ReserveLiability/RedemptionClaim = canonical
        obligation records with single-source-of-truth (D5CAP-1)
CLARIFIED EconomicClaim role: holder-side claim wrapper (redemption,
        deposit, share claims) referencing canonical obligations
UNBRIDGED v0.2 "lineage view (views over §5 records)" ambiguous shape
        → replaced by CapitalPrincipalLineageView
```

# 1. Canonical record family (v0.3 — canonical vs derived unmistakable)

## CANONICAL (Book 5 write authority: blocs 5A–5F)

| Record | Role | Binding notes |
|---|---|---|
| CapitalPrincipalLineage | lineage **nodes** — the principal identities themselves | D5CAP-2: graph, not tree; multi-root legal |
| PrincipalContribution | typed contribution **edge**: source_principal_ref, target_record_ref, attribution_state, quantity?, unit?, share_fraction?, methodology_id, valid_time, book2_claim_refs | no quantity fabricated; DERIVED_ALLOCATION requires methodology_id |
| AttributionState | enum: EXACT / PROPORTIONAL / COMMINGLED / DERIVED_ALLOCATION / UNRESOLVED / UNKNOWN | UNKNOWN never upgraded to EXACT (B5-P29) |
| EconomicClaim | holder-side claim wrapper (deposit claim, share claim, redemption claim) referencing canonical obligations | holder + context; never restates canonical obligation quantities |
| DebtLiability | canonical borrowed-obligation quantity/state | D5CAP-1 single-source-of-truth anchor for credit |
| ReserveLiability | canonical issuer/protocol backing obligation | anchor for 5A/5D/5F backing |
| RedemptionClaim | canonical redemption entitlement | anchor for wrapped/LST/RWA redemption |
| ClaimTokenRepresentation | claim-token ↔ underlying link | anti-double-count link |
| Encumbrance | pledge/rehypothecation state chain | typed, non-additive |
| Positions (10-class family, plan v0.2 §2) | actor/site/context records incl. DebtPosition | reference liabilities; projection-consistency ALG-13 |
| CapitalFlow / CapitalTransformation | events | reference contribution sets for multi-principal sides |
| StablecoinSupply / DerivativeExposure / EconomicSite / locations | as v0.2 | unchanged |

## DERIVED (Book 5 write authority: 5G only, always marked DERIVED)

| Record | Role | Binding notes |
|---|---|---|
| CapitalPrincipalLineageView | 5G lineage projection over canonical CapitalPrincipalLineage + PrincipalContribution | RENAMED from v0.1 colliding shape; never implies more precision than sources (plan v0.2 §9.2) |
| CapitalFieldSnapshot / CapitalFieldPath / CapitalTopologyView | versioned compositions + projections | D5CAP-3; INV-5G-1..7; collapse semantics per attribution state |

**Naming seal:** `CapitalPrincipalLineage` (canonical) vs
`CapitalPrincipalLineageView` (derived) — no other lineage-named object may
exist in the plan namespace.

# 2. Disposition deltas vs v0.2 (complete list)

```text
KEEP  = entire v0.2 canonical family (16 classes) unchanged in membership
ADD   = PrincipalContribution, AttributionState, CapitalPrincipalLineageView
MERGE = none
REJECT= none
CANONICAL FAMILY = 19 record classes
DERIVED FAMILY   = 4 shapes
```

# 3. Cross-checks

- Every canonical class has exactly one authority home (5A–5F or cross-bloc canonical); every derived shape has exactly one producer (5G).
- No canonical/derived name pair collides.
- Liability single-source-of-truth holds: DebtLiability/ReserveLiability/RedemptionClaim are the only authoritative obligation quantities; positions and claims reference them.
- Stress matrix v0.2 Part III (rows 26–35) passes against this family.
