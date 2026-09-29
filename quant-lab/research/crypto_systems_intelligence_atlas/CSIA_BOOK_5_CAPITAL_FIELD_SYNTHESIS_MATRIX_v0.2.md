# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — CAPITAL FIELD SYNTHESIS MATRIX (BLOC 5G) v0.2

**Document ID:** CSIA-B5-5G-002
**Version:** 0.2
**Status:** PLANNING PROOF MATRIX — NOT RATIFIED
**Extends:** v0.1 (preserved — zero-canonical-write proof and INV-5G-1..7 stand). v0.2 adds the repair-era tests: multi-root lineage, commingling, proportional attribution, unknown propagation, canonical-vs-derived naming separation, and liability single-source-of-truth.

**Binding inputs:** D7 (5G derived-only); D5CAP-2 (canonical many-to-many lineage); D5CAP-3 (versioned snapshots + views; `CapitalPrincipalLineageView` naming seal); plan v0.2 §9.

---

# 1. Standing proof (v0.1, unchanged)

```text
5G_CANONICAL_WRITE_COUNT = 0 (by construction — v0.1 §1 basis 1–4 unchanged)
INV-5G-1..7              = standing derivation invariants
```

# 2. v0.2 extension tests

| # | Test | Attack | Required 5G behavior | Planned defense | Verdict |
|---|---|---|---|---|---|
| T-1 | Multi-root lineage | 5G output presents an LP/vault claim as one principal root | output carries `CapitalPrincipalLineageView` nodes per component with per-component attribution; no merged phantom root | plan v0.2 §9.2 collapse semantics; B5-P31 | PASS |
| T-2 | Commingling | 5G invents depositor-unit ancestry for pooled borrowed assets | pool-level totals only, labeled COMMINGLED; no unit tracing output | CON-3, CON-10; ALG-11 | PASS |
| T-3 | Proportional attribution | 5G sums components without fractions or with invented ones | sums only with evidenced share_fraction or methodology-derived allocation (labeled) | CON-7; ALG-12 | PASS |
| T-4 | Unknown propagation | a missing/UNKNOWN component silently zero-filled in a snapshot | dependent outputs INCOMPLETE with gap list | INV-5G-4; P2 | PASS |
| T-5 | Canonical-vs-derived naming | a consumer (or 5G itself) treats `CapitalPrincipalLineageView` as the canonical lineage | view marked DERIVED; canonical authority remains `CapitalPrincipalLineage` (D5CAP-2); recomputation path present | D5CAP-3 naming seal; primitive matrix v0.3 naming table | PASS |
| T-6 | Liability single-source-of-truth | 5G topology shows a debt quantity diverging from its canonical `DebtLiability` | 5G consumes canonical liabilities by pointer; projections reconcile or fail closed (ALG-13); never authors obligation quantities | D5CAP-1 rule; INV-5G-6 | PASS |
| T-7 | Cross-lineage bleed | exit/topology path implies borrowed-USDC descended from borrower's ETH collateral | collateral and borrowed lineages rendered as distinct components; DebtLiability is the only bridge (obligation, not lineage) | plan v0.2 §4.4 | PASS |
| T-8 | Precision overstatement | a derived total displayed without attribution labeling | every aggregate field carries attribution summary; COMMINGLED/UNKNOWN inputs cannot produce EXACT-looking totals | ALG-11; plan v0.2 §9.2 last rule | PASS |

# 3. Result

```text
5G_CANONICAL_WRITE_COUNT = 0
v0.2_EXTENSION_TESTS = 8 (T-1..T-8) — all PASS at planning level
NAMING_COLLISION_PATHS = 0 (seal held)
UNKNOWN_PROPAGATION = INCOMPLETE (never fabrication)
CROSS-LINEAGE_COLLAPSE = BLOCKED
BOOK_5_PLAN_HOLD_TRIGGERED = FALSE
```

Exit gate `PASS_CSIA_B5_CAPITAL_FIELD_V1` now additionally requires: T-1..T-8
executable, snapshot immutability + version supersession demonstrated, and a
replay across two historical valid times including at least one
multi-component (LP/vault) composition.
