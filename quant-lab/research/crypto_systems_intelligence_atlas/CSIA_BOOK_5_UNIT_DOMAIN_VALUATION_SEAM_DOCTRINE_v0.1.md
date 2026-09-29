# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — UNIT DOMAIN + VALUATION SEAM DOCTRINE v0.1

**Document ID:** CSIA-B5-UOM-002
**Version:** 0.1
**Status:** REPAIR DOCTRINE — INCORPORATED INTO PLAN v0.3 — NOT RATIFIED
**Input:** `CSIA_BOOK_5_CROSS_UNIT_AGGREGATION_REPRODUCTION_v0.1.md`; operator directive (Phases 2–8); plan v0.2; Constitution §22 (metrics remain domain-specific; normalization only at comparison layer).

---

# 1. Unit-domain doctrine (B5-P32 — new principle)

```text
B5-P32  ECONOMIC PRINCIPAL IS UNIT-AWARE.
        Principal quantities denominated in different units are not
        arithmetically additive inside Book 5.
```

- SAME-UNIT aggregation (ETH+ETH, USDC+USDC) may be topology-safe where identity, attribution (§3 attribution states), and dedup rules (ALG-8/11/12) pass.
- CROSS-UNIT aggregation (ETH+USDC, WBTC+ETH+USDC) requires valuation/normalization authority — **Book 6**. Book 5 keeps a vector.

Units: asset-symbol denomination plus realization identity where relevant (3 ETH mainnet ≠ 3 weETH); unit strings are part of record identity semantics, never normalized silently.

# 2. PrincipalComponentSet (canonical vector representation)

Refines plan v0.2 §4.2 component structure into the explicit canonical shape:

```text
PrincipalComponentSet {
  component[] {
    asset_ref          canonical economic asset
    realization_ref    where chain-local form matters
    quantity           asset-denominated only
    unit               asset symbol / denomination
    attribution_state  EXACT | PROPORTIONAL | COMMINGLED |
                       DERIVED_ALLOCATION | UNRESOLVED | UNKNOWN
    book2_claim_refs   evidence bindings
    valid_time
  }
}
```

Hard rules: **no implicit conversion; no common-value field; no hidden numeraire.** A component set with two different units is a vector — full stop. Same-unit components within one set may be merged only under the attribution/dedup rules.

# 3. Valuation seam (Phase 4 — exact division; invariant binding)

```text
BOOK 5 OWNS:
  asset-denominated principal quantities
  PrincipalComponentSet vectors
  same-unit aggregation (under lineage/attribution/dedup rules)
  principal lineage and contribution graph
  claim/liability topology
  cross-asset relationships (structural, not valued)
  topology composition (5G)

BOOK 6 OWNS:
  cross-asset valuation
  normalization to a numeraire (USD / BTC / ETH / other)
  valuation methodology and methodology IDs for valued outputs
  price-source selection and price observations
  mark-time alignment across heterogeneous sources
  comparable capital totals
  normalized TVL-like measures
  capital concentration on a common-value basis

INVARIANT: BOOK5_CROSS_ASSET_VALUATION_AUTHORITY = FALSE
           (and 5G a fortiori: B5-P25; 5G cannot do what Book 5 cannot)
```

This sharpens, and never contradicts, plan v0.2 §8.2: a `TOPOLOGY_DERIVATION` is structural composition over records; the moment an output requires a numeraire or a price, it is a `MEASUREMENT_METRIC` — Book 6 territory.

# 4. Observed vs derived common value (Phase 5)

```text
OBSERVED_COMMON_VALUE_FACT
  an externally reported, evidence-backed scalar ("issuer reports reserve
  assets = $40B") — MAY enter Book 5 as a fact with full Book 2 provenance
  (tier, source, observed_at), explicitly attributed to its reporter.

CSIA_DERIVED_COMMON_VALUE
  a scalar CSIA computes from heterogeneous components — belongs to
  BOOK 6 ONLY. Book 5 must not reconstruct $40B from cash + T-bills +
  repo + crypto components.
```

An observed fact is stored as observation, never treated as Book 5 valuation output, never mixed into component vectors, and never used as implicit numeraire.

# 5. Proportional-attribution clarification (Phase 6)

```text
SHARE FRACTION   != VALUATION
PROPORTIONAL     != COMMON-NUMERAIRE VALUE
```

A 50% ETH / 50% USDC LP share fraction is protocol-defined composition. Unless the source itself defines the fraction in a common economic unit (rare, and then it is an observed fact per §4), Book 5 must not infer dollar value from fractions. Fractions authorize: per-component attribution, same-unit algebra, structural decomposition. They do not authorize scalarization.

# 6. 5G collapse rule repair (Phase 7 — three-way distinction)

```text
A. SAME-UNIT principal collapse
     permitted where lineage + attribution + dedup permit (unchanged rules).

B. HETEROGENEOUS-UNIT topology composition
     5G outputs a component vector / topology structure.
     It does NOT emit one scalar.

C. CROSS-ASSET VALUATION request
     resolves to a Book 6 measurement product when Book 6 exists.
     Before Book 6 exists: NOT_AUTHORIZED.
```

State law: `UNKNOWN` = missing truth; `NOT_AUTHORIZED` = the computation belongs to another book. Never conflated. A `NOT_AUTHORIZED` field is not filled with UNKNOWN to look humble — it names the authority boundary.

# 7. Algebra extensions (Phase 8)

```text
ALG-14  Quantities with different units are not directly additive.
ALG-15  Cross-asset scalarization requires an explicit valuation product
        owned by Book 6.
ALG-16  A share_fraction or attribution proportion does not itself
        establish a common-value basis.
ALG-17  Observed common-value facts may be stored with provenance, but
        Book 5 may not derive them from heterogeneous components.
ALG-18  5G topology composition over heterogeneous assets returns a
        component vector, not an internally valued scalar.
```

Amends the two ambiguous v0.2 readings: ALG-12 is now same-unit-scoped; "combined total" phrases in companion artifacts are superseded by plan v0.3's vector doctrine (v0.1/v0.2 preserved as history).

# 8. Ratification-readiness gates added

```text
BOOK5_CROSS_ASSET_VALUATION_AUTHORITY = FALSE   (blocking readiness invariant)
CROSS_ASSET_AGGREGATION_REVIEW        = PASS    (required for v0.3 readiness)
```
