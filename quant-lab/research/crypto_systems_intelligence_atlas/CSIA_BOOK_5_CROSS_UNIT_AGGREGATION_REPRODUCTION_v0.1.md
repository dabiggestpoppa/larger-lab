# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — CROSS-UNIT PRINCIPAL AGGREGATION DEFECT REPRODUCTION v0.1

**Document ID:** CSIA-B5-UOM-001
**Version:** 0.1
**Status:** EXTERNAL-REVIEW DEFECT REPRODUCTION — PLANNING ONLY
**Trigger:** operator external-review directive (2026-09-29) — cross-asset principal aggregation may silently absorb Book 6 valuation authority; repair required before Book 5 ratification.

---

# 1. Defect reproduction — audit of value-leak paths

| Location | Text (verbatim fragment) | Defect |
|---|---|---|
| Stress matrix v0.2 row 26 (LP) | "combined total only via evidenced fractions + methodology" | **THE DEFECT** — a "combined total" over ETH + USDC components implies a common numeraire; evidenced fractions (1/2, 1/2) are *composition*, not *value*; producing "8,000 USD" from 3 ETH + 5,000 USDC requires price observations, numeraire, mark time, and conversion methodology — Book 6 authority |
| Plan v0.2 §6 ALG-12 | component shares "enter sums only when evidenced… or methodology-derived" | ambiguous: permits cross-unit sums under methodology without stating whose authority — a methodology label alone does not transfer valuation authority from Book 6 |
| Plan v0.2 §9.2 | "PROPORTIONAL may collapse only with explicit evidenced fractions" | same ambiguity: "collapse" is unqualified — legal for same-unit, illegal across units |
| Synthesis matrix v0.2 T-3 | "sums only with evidenced share_fraction or methodology-derived allocation" | same: fraction ≠ valuation |
| Reconciliation v0.1 §3.2 | `share_fraction` field | needs the explicit "fraction is composition, not value" rule |

Structural finding: plan v0.2's own seam rule (§8.2: `TOPOLOGY_DERIVATION` vs `MEASUREMENT_METRIC`; P26) already implies the correct answer, but the component-aggregation language never states that **principal quantities are unit-aware** and that cross-unit scalarization is valuation. The leak is by omission, not contradiction.

```text
HETEROGENEOUS_UNIT_COLLAPSE_REQUIRES_MEASUREMENT = TRUE
BOOK5_CROSS_ASSET_VALUATION_AUTHORITY = FALSE (must be made explicit and invariant)
```

# 2. Counterexamples (directive set)

**A. ETH-USDC LP.** Book 5 knows 3 ETH + 5,000 USDC (E0). It must NOT emit "8,000 USD of capital" — that operation consumed a price observation (ETH/USD), an observation time, a source, and a conversion convention that Book 5 never performed.

**B. 3-asset vault (ETH, USDC, WBTC).** All three components preserved as a vector; no cross-unit scalar inside canonical Book 5 or 5G topology.

**C. Stablecoin reserve basket (cash / T-bills / repo / crypto collateral).** No single backing-value scalar from Book 5 unless the scalar is itself an observed, evidence-backed fact (Phase 5 rule).

**D. Multi-collateral position (ETH, WBTC, USDC).** No internally priced collateral-value scalar; Book 5 keeps the component set (risk interactions remain typed relations, e.g., encumbrance coverage, not numbers).

**E. Insurance fund mixed assets.** Component vector + observed contribution events; no internally derived common-value total.

**F. RWA portfolio basket.** Token/claim structure with component holdings; any "portfolio value" is an observed issuer fact or Book 6 measurement — never Book 5 arithmetic across units.

# 3. Required repair (doctrine written in the companion artifact)

1. **B5-P32** — economic principal is unit-aware; cross-unit quantities are not arithmetically additive inside Book 5.
2. **PrincipalComponentSet** — the canonical vector representation; no common-value field, no hidden numeraire, no implicit conversion.
3. **Valuation seam** — `BOOK5_CROSS_ASSET_VALUATION_AUTHORITY = FALSE`; cross-asset scalarization is a Book 6 measurement product.
4. **OBSERVED_COMMON_VALUE_FACT vs CSIA_DERIVED_COMMON_VALUE** — externally reported totals may be stored as evidence-backed facts; CSIA never derives them in Book 5.
5. **share_fraction ≠ valuation; PROPORTIONAL ≠ common-numeraire value.**
6. **ALG-14..18** — unit-aware algebra; 5G heterogeneous outputs are vectors; valuation requests resolve to a Book 6 product, or NOT_AUTHORIZED before Book 6 exists (distinct from UNKNOWN).

Disposition: plan v0.3 required; v0.2 superseded pending ratification only if v0.3 passes review. All v0.1/v0.2 artifacts preserved unmodified as history.
