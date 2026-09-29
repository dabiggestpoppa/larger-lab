# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — CAPITAL TOPOLOGY STRESS MATRIX v0.3

**Document ID:** CSIA-B5-STRESS-003
**Version:** 0.3
**Status:** PLANNING STRESS MATRIX — NOT RATIFIED
**Extends:** v0.1 (rows 1–25) and v0.2 (rows 26–35) — both preserved unmodified. v0.3 adds rows 36–45, the unit-domain scenarios stress-testing B5-P32, PrincipalComponentSet, the valuation seam, and ALG-14..18 (doctrine: `CSIA_BOOK_5_UNIT_DOMAIN_VALUATION_SEAM_DOCTRINE_v0.1.md`).

---

# Part IV — unit-domain stress (v0.3 extension)

Required outcomes legend: SAME-UNIT-OK (aggregation allowed under lineage/dedup rules) | VECTOR-OK (heterogeneous vector allowed) | SCALAR-NA (cross-asset scalar NOT AUTHORIZED in Book 5) | OBSERVED-OK (externally observed scalar allowed as evidence-backed fact).

| # | Scenario | Book 5 record | Scalar in Book 5? | Verdict |
|---|---|---|---|---|
| 36 | ETH + USDC LP vector | PrincipalComponentSet {ETH: 3.0, USDC: 5000}; fractions 1/2 recorded as composition | NO — "8,000 USD" requires numeraire + price + mark time → Book 6. 3 ETH + 5,000 USDC "≠ 8,000" inside Book 5 | VECTOR-OK; SCALAR-NA |
| 37 | ETH + WBTC + USDC vault | 3-component vector, per-component attribution | NO cross-unit scalar in canonical Book 5 or 5G topology | VECTOR-OK; SCALAR-NA |
| 38 | Multi-collateral lending basket | collateral components {ETH, WBTC, USDC} via Encumbrance links to the DebtLiability | NO internally priced collateral-value scalar | VECTOR-OK; SCALAR-NA |
| 39 | Stablecoin reserve basket | reserve components (cash/T-bills/repo/crypto), tiered evidence | scalar only if OBSERVED_COMMON_VALUE_FACT (issuer-reported); never CSIA-derived from components | VECTOR-OK; SCALAR-NA; OBSERVED-OK |
| 40 | Mixed-asset insurance fund | component vector + contribution event history | NO internally derived common-value total | VECTOR-OK; SCALAR-NA |
| 41 | RWA basket | component holdings + claim structure | portfolio value = observed issuer fact or Book 6 product; never Book 5 arithmetic | VECTOR-OK; SCALAR-NA; OBSERVED-OK |
| 42 | Same-unit USDC components from multiple positions | merge permitted where asset/realization identity match AND attribution rules pass (ALG-8/11/12 dedup) | same-unit scalar allowed under existing rules | SAME-UNIT-OK |
| 43 | Same-unit ETH components across representations | merge permitted only with realization reconciliation (mainnet ETH vs LST vs bridged are distinct units-of-record); realization collapse via lineage methodology | same-unit (same realization) scalar OK; cross-realization needs lineage methodology, still asset-denominated | SAME-UNIT-OK (with lineage rules) |
| 44 | Issuer-reported USD reserve total | OBSERVED_COMMON_VALUE_FACT: scalar stored with reporter attribution, tier, observed_at, never mixed into component vectors, never implicit numeraire | YES — as observed fact, not Book 5 valuation output | OBSERVED-OK |
| 45 | Attempted CSIA-derived USD total before Book 6 | NOT_AUTHORIZED — the computation belongs to Book 6; field state NOT_AUTHORIZED, explicitly distinct from UNKNOWN (missing truth) | NO | SCALAR-NA |

# Result

```text
v0.3_ROWS_ADDED = 10 (36–45)
SAME_UNIT_AGGREGATION   = allowed only under existing lineage/attribution/dedup rules
HETEROGENEOUS_VECTOR    = allowed (PrincipalComponentSet)
CROSS_ASSET_SCALAR      = NOT AUTHORIZED IN BOOK 5
EXTERNALLY_OBSERVED_SCALAR = allowed as evidence-backed fact; never Book 5
                             valuation output; never implicit numeraire
UNRESOLVED_FAILURES = 0
BOOK_5_PLAN_HOLD_TRIGGERED = FALSE
TOTAL_MATRIX_ROWS (v0.1+v0.2+v0.3) = 45
```
