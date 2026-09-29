# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — CAPITAL TOPOLOGY STRESS MATRIX v0.2

**Document ID:** CSIA-B5-STRESS-002
**Version:** 0.2
**Status:** PLANNING STRESS MATRIX — NOT RATIFIED
**Extends:** v0.1 (25 rows — preserved there; not repeated here). v0.2 adds the directive's 10 attribution-state scenarios stress-testing the repaired lineage doctrine (plan v0.2 §3–§4, ALG-11..13, CON-1..10).

**Per-row required fields:** known principals / unknown principals / claim structure / liability structure / attribution state / exact collapse allowed? / 5G must remain INCOMPLETE?

---

# Part III — attribution-state stress (v0.2 extension)

| # | Scenario | Known principals | Unknown principals | Claim structure | Liability structure | Attribution state | Exact collapse allowed? | 5G INCOMPLETE required? |
|---|---|---|---|---|---|---|---|---|
| 26 | 50/50 ETH+USDC LP | ETH principal, USDC principal (both E0-observed deposits) | none | LP claim with 2 principal components, evidenced 1/2 fractions | pool owes LP redemption | PROPORTIONAL (or EXACT per component at deposit instant) | only per-component; combined total only via evidenced fractions + methodology | NO (components fully known) |
| 27 | 3-asset vault | the 3 reserve assets at observed composition | none (or per-strategy drift UNKNOWN) | vault share → N components | vault owes share redemption | PROPORTIONAL with evidenced composition; UNKNOWN for unobserved drift windows | per-component; total needs methodology for drift windows | YES for drift windows |
| 28 | Fungible lending pool, 3 depositors → 1 borrower | pool-level aggregate principal; depositor identities on-chain | depositor-unit ancestry of the specific borrowed units | borrower claim (borrowed assets) with pool reference | DebtLiability (canonical) → borrower; market owes depositors | COMMINGLED on the borrowed side; depositor claims EXACT (their own balances) | NO — unit ancestry must not be invented; pool-level totals only | YES for any depositor-attributed output |
| 29 | ETH-collateral borrower takes USDC loan | ETH principal (collateral, EXACT); USDC pool principal (COMMINGLED) | none beyond pool commingling | ETH CollateralPosition + borrowed-USDC position; two separate lineages | DebtLiability links obligation to market | collateral EXACT; borrowed COMMINGLED | NO cross-lineage collapse — the two lineages never merge (plan v0.2 §4.4) | YES for any output implying borrowed-USDC came from the ETH |
| 30 | Multi-collateral debt position | ETH + wBTC + stablecoin collateral principals (EXACT each) | none | one DebtPosition; N collateral components via Encumbrance links | one canonical DebtLiability | collateral components EXACT; debt single-currency | per-collateral-component only; debt is its own lineage | NO (structure fully typed) |
| 31 | Stablecoin reserve basket | reserve assets per attestation (E1/E2 tiers) | composition between attestations | stablecoin claim → N reserve components | ReserveLiability (canonical backing obligation) | PROPORTIONAL per attestation; UNKNOWN in attestation gaps | per-component at attestation times; inter-attestation needs methodology | YES in attestation gaps |
| 32 | Insurance fund, mixed contributions | fee flows, liquidation penalties, transfers (each EXACT as events) | post-commingling unit ancestry of any specific dollar | fund balance (stock) with contribution history | fund's coverage obligation (socialized) | COMMINGLED (post-commingling); contribution history EXACT as events | NO unit-level; aggregate only | YES for unit-ancestry outputs |
| 33 | Commingled CEX settlement pool | venue-attested aggregate (E1/E2) | per-user ownership inside pool; encumbrance state | SettlementBalance with segregability UNKNOWN | venue obligations to users (canonical per-claim where attested, else UNKNOWN) | COMMINGLED/UNKNOWN | NO | YES — outputs must not imply per-user principal knowledge |
| 34 | Partial observability (pool-level backing only) | pool total backing | every unit-level detail | claim → pool reference only | pool liability at aggregate level | COMMINGLED with UNKNOWN composition | NO | YES |
| 35 | Methodology-derived pro-rata allocation | full input set (EXACT components) | none structurally | claim with derived per-source allocation | — | DERIVED_ALLOCATION (methodology ID mandatory) | only as a labeled derived result; never displayed as EXACT | NO if labeled; YES if any consumer could mistake it for EXACT |

# Result

```text
v0.2_ROWS_ADDED = 10 (26–35)
ATTRIBUTION_STATES_EXERCISED = all 6 (EXACT, PROPORTIONAL, COMMINGLED,
                               DERIVED_ALLOCATION, UNRESOLVED via 27/34 gaps,
                               UNKNOWN via 33/34)
CROSS-LINEAGE COLLAPSE CASES (row 29) = fail closed by doctrine
INVENTED-UNIT-ANCESTRY CASES (28/32/33/34) = fail closed by CON-3/CON-10
TOTAL_MATRIX_ROWS (v0.1 + v0.2) = 35
UNRESOLVED_FAILURES = 0
BOOK_5_PLAN_HOLD_TRIGGERED = FALSE
```
