# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — CROSS-BOOK BOUNDARY REVIEW (D7 PRE-PLANNING)

**Document ID:** CSIA-B5-D7-BOUNDARY-001
**Version:** 0.1
**Status:** BOUNDARY RECONNAISSANCE — NOT A DECISION — NOT A BOOK 5 PLAN
**Gate:** D7 OPEN. This review verifies the fences Book 5 planning must respect; it moves no fence.

---

# 0. Purpose

Directive Phases 2, 11, 18, 19. Verifies: (1) the frozen Book 4 / Book 5 boundary, (2) the Book 5 / Book 6 boundary, (3) the Book 5 / Book 8 boundary, and (4) whether any **accepted contract contradiction** exists that would force `BOOK_4_AMENDMENT_REQUIRED = TRUE`. Method: direct comparison of the frozen Book 4 plan boundary, the frozen `book4_boundary.py` allowlists, the ratified Book 1 plan contract, the ratified Constitution, and the canonical roadmap.

---

# 1. Book 4 ↔ Book 5 boundary (frozen side verified)

## 1.1 Book 4 plan v0.2 boundary (accepted planning artifact)

> "…Book 5 owns capital routing, liquidity, collateral, stablecoin supply, credit, staking/yield, derivatives, economic flow, value locked, and capital concentration."
> "Book 4 does not absorb Book 5 capital plumbing."

## 1.2 Frozen implementation boundary (anchor `1650ba7c`, `book4_boundary.py`)

- `BOOK4_DEPENDENCY_RELATION_ALLOWLIST` — technical/service/route relations only (`DEPENDS_ON`, `INTEGRATES_WITH`, `BRIDGES_TO`, `ROUTED_THROUGH`, … + Book 3 architecture relations).
- `BOOK5_ECONOMIC_RELATIONS` — `COLLATERAL_IN`, `LIQUIDITY_ON`, `STAKED_IN`, `RESTAKED_IN`, `REDEEMS_FOR`, `ISSUED_ON`, `NATIVE_TO`, `WRAPS` — "Book 1 economic relations that may never authorize a Book 4 record."
- `BOOK5_TERMS` lexical screen ("total value locked", "capital routing", "liquidity depth", "stablecoin supply", …) with `BOOK4ScopeError` — "Book 5 capital-field claim rejected from Book 4."
- Note: the frozen module itself uses the phrase "Book 5 capital-field content" — consistent with reading Capital Field ≈ Book 5 domain content (reconciliation doc M-6).

## 1.3 Verdict

The Book 4 side of the fence is coherent, internally consistent, and matches the roadmap's Book 5 scope with **no contradiction**. Book 4 owns technical dependency / service consumption / infrastructure roles / failure domains / redundancy / substitutability / route mechanics; Book 5 owns the economic content. **BOOK_4_AMENDMENT_REQUIRED = FALSE.** No Book 4 contract is reopened by D7 under any option; only under Option D would the *meaning* of the boundary's "Book 5" side change (the allowlist itself would not change).

---

# 2. Capital route vs technical route (directive Phase 11)

Verified against frozen doctrine:

- Book 4 `BRIDGES_TO` / `ROUTED_THROUGH` = capability facts about technical paths (route mechanics).
- Constitution §19: "Possible capital route does not equal realized flow. Router availability does not equal bridge flow." §19.1: capability edges are standing edges; flows are temporally bounded event objects referencing edges; INV-1C-4 forbids magnitudes on capability edges (per Book 1 review Q15).
- Book 1 plan non-goal: "No capital-flow modeling (Book 5) — only capability-edge vocabulary."

Result: `TECHNICAL ROUTE ≠ OBSERVED CAPITAL FLOW`; `AVAILABLE ROUTE ≠ USED ROUTE`; `SUPPORTED ASSET ≠ TRANSFERRED ASSET` are **already implied by ratified doctrine** and require no Book 1 or Book 4 change. Book 5-local typed flow records (quantity, legs, interval, transformation type) referencing Book 1 capability edges are the compatible architecture. Recorded as doctrine candidate for Book 5 planning; not ratified here.

---

# 3. Book 5 ↔ Book 6 boundary (directive Phase 18)

- Roadmap Book 6: "Turn raw architecture/activity evidence into transparent investor-facing state" (metrics, comparable dimensions, state vectors, validation).
- Constitution §19.1: **capacity** ("a route has measurable size at a time") is a *measurement-layer attribute, Book 6*.
- Constitution §23: fundamental state vectors (CAPITAL_STATE, LIQUIDITY_STATE, …) are later-research descriptive states, with explicit definitions and inspectable source metrics.

Tested rule (recorded, not ratified):

```text
BOOK 5 = canonical economic facts + relations + transformations + topology
BOOK 6 = derived metrics, comparable dimensions, descriptive state vectors
```

Consequence for Book 5 planning: Book 5 must not create investment scores, rankings, composite quality ratings, normalized protocol grades, or market-timing states — those are either Book 6 measurement outputs (descriptive) or forbidden entirely (prescriptive, §5.3a). Ambiguity found and recorded: the **borderline** between "Book 5 canonical fact" and "Book 6 metric" is *derived aggregates* (TVL-like totals, concentration measures, utilization). Primitive #14 (LockedCapital) and #17 (CapitalConcentration) are candidates precisely because raw stocks are Book 5 while methodological aggregates lean Book 6. Resolution belongs to Book 5 planning after D7; flagged here so the operator sees the seam.

---

# 4. Book 5 ↔ Book 8 boundary (directive Phase 19)

- Book 8 (Context Bridge) joins structural context + capital context + market context; D8 (shared-seam ownership, gate: Book 8 planning) remains OPEN and out of scope.
- Book 5 must not emit `BUY / SELL / BULLISH / BEARISH / TARGET / ENTRY / EXIT SIGNAL` as operator conclusions (§5.3a; D4 confirmed the descriptive/prescriptive boundary constitutionally).
- The 5G sequence term **"exit"** is an economic-topology state: capital leaving the modeled system (redemption, burn, bridge-out beyond boundary, off-ramp). It is descriptive; it is not, and must never be implemented as, a trade exit recommendation. This guard is recorded as a standing constraint for Book 5 planning under any D7 option (P17, P18).

Result: no Book 8 seam is touched by D7; §4.2.1 seam assignments remain reserved to D8.

---

# 5. Book 1 / Book 2 dependence

- **Book 1 (frozen):** identity classes (42 incl. REALIZATION), capability edges (`COLLATERAL_IN`, `LIQUIDITY_ON`, `STAKED_IN`, `RESTAKED_IN`, `WRAPS`, `REDEEMS_FOR`, `ISSUED_ON`, `NATIVE_TO`, `ROUTED_THROUGH`, `BRIDGES_TO`), hyperedges, bitemporal fields. Q15 (ratified review): Capital Field data attaches without altering identity truth; D7 governs scope, not identity.
- **Book 2 (frozen):** all capital facts enter as Book 2-backed claims (P1); 14-class source registry; promotion doctrine D2-1..D2-6; contradiction doctrine (F-2, F-5) applies to conflicting capital evidence.

Neither frozen contract is contradicted by any D7 option. Extension candidates found during reconnaissance (below) are recorded, not applied.

---

# 6. Extension candidates discovered (recorded only — no amendment proposed or made)

| # | Candidate | Why Book 1 cannot express it today | Disposition |
|---|---|---|---|
| 1 | Position-site identity (pool/market/vault sub-object IDs) | Book 1 has protocol classes; no per-pool/per-market identity doctrine | BOOK_1_EXTENSION_CANDIDATE — Book 5 planning must define site identity; if raised to Book 1, goes through §9.3/§36, operator-gated |
| 2 | Per-position claim/liability/custody record class | Book 1 edges are entity-level (`OWNED_BY`, `OPERATED_BY`); per-position economic claims are outside identity doctrine | BOOK_1_EXTENSION_CANDIDATE (more likely Book 5-local records referencing Book 1 identities — planning decides) |
| 3 | Off-chain/unknown location ontology for flow legs | No location semantics for CEX custody, SPV, system boundary | Book 5-local candidate vocabulary |
| 4 | Flow-event field contract (qty/unit/legs/interval) | Book 1 defines event-object *principle* (§19.1), not capital-flow fields | Book 5-local (roadmap assigns capital-flow modeling to Book 5) |

`BOOK_1_AMENDMENT_REQUIRED = FALSE` — candidates are planning inputs, not contradictions.

---

# 7. Boundary review result block

```text
BOOK_4_AMENDMENT_REQUIRED        = FALSE
BOOK_1_AMENDMENT_REQUIRED        = FALSE
BOOK_2_AMENDMENT_REQUIRED        = FALSE
BOOK_3_AMENDMENT_REQUIRED        = FALSE
CONSTITUTION_AMENDMENT_REQUIRED  = FALSE (for A/B/C; Option D may require §4.3-adjacent boundary language — operator question, recorded in packet)
BOOK_1_EXTENSION_CANDIDATE_COUNT = 4 (recorded, not applied)
BOOK_5_BOOK_6_SEAM               = derived-aggregate ownership to be settled in Book 5 planning
BOOK_5_BOOK_8_SEAM               = untouched; D8 remains gate for Book 8
ROUTE_VS_FLOW                    = no contradiction; Book 5-local typed flow records required
EXIT_SEMANTICS_GUARD             = economic-topology state only; never a trade signal
```
