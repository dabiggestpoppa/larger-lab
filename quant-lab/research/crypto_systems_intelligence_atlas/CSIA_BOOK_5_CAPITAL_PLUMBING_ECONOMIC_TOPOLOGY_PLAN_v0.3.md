# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — CAPITAL PLUMBING AND ECONOMIC TOPOLOGY — PLAN v0.3

**Document ID:** CSIA-B5-PLAN-003
**Version:** 0.3
**Status:** PLANNING DRAFT — READY_FOR_OPERATOR_RATIFICATION — NOT RATIFIED
**Supersedes:** v0.2 (preserved unmodified) — **supersession effective only upon operator ratification of v0.3**; v0.1 preserved as history
**Defect repairs incorporated:** single-root lineage repair (v0.2) + **cross-unit aggregation repair (v0.3, this version)**
**Repair doctrine source:** `CSIA_BOOK_5_UNIT_DOMAIN_VALUATION_SEAM_DOCTRINE_v0.1.md`; reproduction: `CSIA_BOOK_5_CROSS_UNIT_AGGREGATION_REPRODUCTION_v0.1.md`
**Gates closed:** D7; D5CAP-1/2/3 (Operator Decision Log). No new operator decisions opened by v0.3 — the valuation seam is doctrine-application (P26/§8.2 lineage), not a new structural choice.
**Companion artifacts:** stress matrix v0.3 (45 rows), synthesis matrix v0.3 (T-1..T-14), primitive matrix v0.3, relationship matrix v0.1, pre-ratification review v0.3 (30 questions), lineage reconciliation v0.1, unit-domain doctrine v0.1.

---

# 0. Book goal and grammar (unchanged)

Goal: roadmap-verbatim (issued / routed / held / locked / traded / lent / borrowed / collateralized / staked / restaked / leveraged / transformed / redeemed / exits). Grammar:

```text
CAPABILITY != CAPACITY != FLOW != STOCK != POSITION != CLAIM !=
LIABILITY != EXPOSURE != ECONOMIC PRINCIPAL
```

## 0.1 Planning principles — B5-P1..P32

B5-P1..P31 carry forward unchanged (v0.1 §0.2 + v0.2 additions). v0.3 adds:

```text
B5-P32  ECONOMIC PRINCIPAL IS UNIT-AWARE. Principal quantities denominated
        in different units are not arithmetically additive inside Book 5.
        ETH+ETH and USDC+USDC may sum where identity/attribution permit;
        ETH+USDC (and any cross-unit set) remains a vector / component set.
```

---

# 1. Identity contracts (v0.2 §1 carried forward)

EconomicSite, position identity, flow/transformation identity, location ontology: unchanged from v0.2 §1, including `principal_component_refs` and the liability single-source-of-truth references.

---

# 2. Record contracts (v0.2 §2 carried forward, one refinement)

Position family, liability family (D5CAP-1 single-source-of-truth), attribution states, and flow/transformation contracts stand as in plan v0.2 §2–§5. **Refinement (v0.3):** `principal_component_refs` is formalized as **`PrincipalComponentSet`**:

```text
PrincipalComponentSet {
  component[] {
    asset_ref, realization_ref?, quantity (asset-denominated only),
    unit, attribution_state, book2_claim_refs, valid_time
  }
}
```

Hard rules: no implicit conversion; **no common-value field**; no hidden numeraire. Heterogeneous components are a vector — never flattened to a scalar inside Book 5. (Full doctrine: unit-domain artifact §2.)

---

# 3. Principal-lineage doctrine (v0.2 §4 carried forward, language corrected)

Many-to-many `CapitalPrincipalLineage` graph + `PrincipalContribution` edges, attribution states, CON-1..CON-10, borrowing-vs-collateral separation: all stand. **Corrections (v0.3):**

1. CON-7 (collapse requires explicit methodology) is now scoped: **same-unit collapse** requires lineage + attribution + dedup methodology; **cross-unit scalarization** is not "collapse" at all — it is valuation (Book 6), and no methodology ID minted inside Book 5 can authorize it.
2. All "combined total" phrasing from companion artifacts is superseded: totals are either **same-unit aggregates** (Book 5, rules applying) or **common-numeraire values** (Book 6 product or OBSERVED_COMMON_VALUE_FACT).

---

# 4. Valuation seam (NEW — v0.3 §core; doctrine §3–§5 binding)

```text
BOOK 5 OWNS: asset-denominated principal quantities; PrincipalComponentSet
  vectors; same-unit aggregation (under lineage/attribution/dedup rules);
  principal lineage; claim/liability topology; cross-asset relationships
  (structural); topology composition.

BOOK 6 OWNS: cross-asset valuation; numeraire normalization (USD/BTC/ETH/
  other); valuation methodology; price-source selection; price observations;
  mark-time alignment; comparable capital totals; normalized TVL-like
  measures; capital concentration on a common-value basis.

INVARIANT: BOOK5_CROSS_ASSET_VALUATION_AUTHORITY = FALSE
```

This sharpens plan v0.2 §8.2 (seam unchanged in structure; now enforced at the quantity level by B5-P32 and ALG-14..18). Book 6 is not amended.

**Observed vs derived common value:**

```text
OBSERVED_COMMON_VALUE_FACT  — an externally reported scalar ("issuer reports
  reserve assets = $40B") MAY be stored in Book 5 as an evidence-backed fact
  with reporter attribution, tier, and observation time. It is never treated
  as Book 5 valuation output, never mixed into component vectors, and never
  used as an implicit numeraire.

CSIA_DERIVED_COMMON_VALUE   — belongs to BOOK 6 ONLY. Book 5 never
  reconstructs such a scalar from heterogeneous components.
```

**Proportional attribution clarification:** `SHARE FRACTION != VALUATION`; `PROPORTIONAL != COMMON-NUMERAIRE VALUE`. Fractions authorize per-component attribution, same-unit algebra, and structural decomposition — never scalarization.

---

# 5. Flow / transformation contracts (v0.2 §3, §5 carried forward)

Unchanged; event references use PrincipalComponentSet for multi-principal sides.

# 6. Algebra (v0.2 §6 ALG-1..13 + v0.3 additions)

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

ALG-12 is hereby scoped **same-unit**: component shares enter sums only when evidenced or methodology-derived, **and only within one unit**. The planning theorem of v0.1 §6 stands unchanged. New state law: `UNKNOWN` = missing truth; `NOT_AUTHORIZED` = the computation belongs to another book; never conflated, never substituted for each other.

---

# 7. Exit doctrine, temporal/evidence contracts (v0.2 §7, §9 carried forward)

TRUE ECONOMIC EXIT vs OBSERVABILITY EXIT; bitemporal + replay; Book 2 evidence monopoly: unchanged.

# 8. Cross-book boundaries (v0.2 §8 carried forward, valuation seam added)

Book 4 frozen fence; Book 8 non-absorption (D8 untouched); Book 1 extension dispositions (all BOOK5_LOCAL_SUFFICIENT, no amendment); Book 2 dependence — all unchanged from plan v0.2 §8. **Book 6 seam:** v0.2 §8.2 rule stands, now with the quantity-level enforcement of §4 here (TOPOLOGY_DERIVATION vs MEASUREMENT_METRIC at the field level: a field needing a numeraire is a measurement).

---

# 9. Bloc contracts 5A–5F (v0.2 §8 bloc section carried forward; unit-aware)

All bloc contracts stand with one v0.3 overlay: every place a bloc could express a multi-asset aggregate (5A reserve baskets, 5C multi-collateral accounts, 5D multi-asset vault/yield claims, 5E multi-asset margin, 5F RWA baskets) is a **PrincipalComponentSet vector**; any externally reported aggregate value enters only as OBSERVED_COMMON_VALUE_FACT; no bloc emits internally derived common-value scalars. Exit-gate names unchanged; evidence now includes a unit-awareness demonstration per bloc.

# 10. Bloc 5G (v0.2 §9 carried forward; collapse rule repaired per Phase 7)

Output shapes unchanged (CapitalFieldSnapshot / CapitalFieldPath / CapitalPrincipalLineageView / CapitalTopologyView; naming seal intact). Collapse doctrine now three-way:

```text
A. SAME-UNIT collapse        permitted where lineage + attribution + dedup
                             permit.
B. HETEROGENEOUS-UNIT        5G outputs a component vector / topology;
   composition               never one scalar.
C. VALUATION request         references a Book 6 measurement product when
                             Book 6 exists; before that: NOT_AUTHORIZED
                             (never UNKNOWN, never computed).
```

INV-5G-1..7 stand; synthesis matrix v0.3 T-9..T-14 added. `5G_CANONICAL_WRITE_COUNT = 0`; `5G_CROSS_ASSET_VALUATION_COUNT = 0`.

---

# 11. Double-counting doctrine (v0.2 §10 + unit extension)

Rules 1–8 stand; rule 8 extended by ALG-14..18: attribution-honest AND unit-honest aggregation — no total may silently assume a common unit, and every cross-asset presentation is a labeled vector or an explicitly referenced Book 6/observed product.

# 12. Implementation prohibitions (v0.2 §11 + v0.3 additions)

All prior prohibitions stand, plus:

```text
NO CROSS-ASSET VALUATION IN BOOK 5.
NO IMPLICIT NUMERAIRE.
NO SHARE_FRACTION = VALUE ASSUMPTION.
NO HETEROGENEOUS UNIT SUMMATION.
NO BOOK 6 IMPLEMENTATION (this plan authorizes nothing).
```

# 13. Exit gates (names unchanged; unit-awareness evidence added)

`PASS_CSIA_B5A..B5F…`, `PASS_CSIA_B5_CAPITAL_FIELD_V1` — per-bloc evidence additions per §9–§10.

# 14. Plan status

```text
BOOK_5_PLAN_VERSION = v0.3
BOOK_5_PLAN_v0.2    = SUPERSEDED_PENDING_RATIFICATION (preserved unmodified)
BOOK_5_PLANNING     = READY_FOR_OPERATOR_RATIFICATION
BOOK_5_OPERATOR_RATIFIED = FALSE
BOOK_5_PLAN_HOLD_TRIGGERED = FALSE
OPEN_OPERATOR_DECISION_COUNT = 0
BOOK5_CROSS_ASSET_VALUATION_AUTHORITY = FALSE
```
