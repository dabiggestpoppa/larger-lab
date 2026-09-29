# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — PRINCIPAL LINEAGE RECONCILIATION (SINGLE-ROOT DEFECT) v0.1

**Document ID:** CSIA-B5-LIN-001
**Version:** 0.1
**Status:** EXTERNAL-REVIEW DEFECT REPRODUCTION + REPAIR DESIGN — PLANNING ONLY
**Trigger:** operator external-review directive (2026-09-29) — plan v0.1 §5 rule 1 is too strong for pooled/commingled/multi-asset capital; repair required BEFORE Book 5 ratification.
**Scope:** audit of every one-node→one-root assumption in Book 5 planning artifacts; counterexamples; repaired attribution/lineage/conservation/borrowing/multi-asset doctrine. No ratification; no implementation.

---

# 1. Defect reproduction — audit results

| Location (plan v0.1) | Text / structure | Defect class |
|---|---|---|
| §5 rule 1 (line 272) | "every lineage node traces to exactly one economic principal at its root" | **THE DEFECT** — false for multi-root nodes |
| §5 rule 2 (line 273) | "fan-out (one principal → multiple claims…) is represented as branching" | one-directional: covers one→many only; many→one (pooling) unrepresentable |
| §2.1 base field | `principal_lineage_id` (singular) on the position base | forces one lineage identifier per record; multi-component claims cannot be expressed |
| §5 recommendation (a) | "conservation rules enforce one-principal accounting" | "one-principal" ambiguity — true for conservation-by-component, false as universal single-root |
| §19 (5D) | "Every branch references the same `principal_lineage_id`" | valid for ETH→LST→restake (a genuine single-root chain) but presented as the general pattern |
| §6 ALG-8 | aggregation requires "principal lineage + dedup" | dedup semantics undefined for multi-source nodes |
| §22 (5G shapes) | lists `CapitalPrincipalLineage` as a 5G lineage **view** | **SECONDARY DEFECT (name collision)** — canonical record family (§5) and derived 5G output share a name |
| Stress matrix rows 2/3/4/7 | "one principal, N branches" phrasings | correct for those scenarios; doctrine did not generalize |

Expected finding confirmed:

```text
SINGLE_ROOT_PRINCIPAL_DOCTRINE = INVALID_FOR_GENERAL_BOOK5_TOPOLOGY
```

# 2. Concrete counterexamples (directive minimum set)

**A. 50/50 ETH-USDC LP share.** One LP claim represents TWO underlying
principals (ETH component + USDC component) in fixed proportion. A single
`principal_lineage_id` with one root cannot represent the component structure;
forcing one root arbitrarily erases a principal or invents a false merged one.

**B. Multi-asset vault share.** One claim, N underlying assets (N ≥ 2, possibly
dynamic as strategy rebalances). A vault share is a claim on a *basket*;
single-root lineage invents either N phantom shares or 1 false principal.

**C. Pooled lending.** One borrower receives fungible pool assets contributed
by many suppliers. Evidence establishes pool-level backing, NOT depositor-unit
ancestry. Single-root doctrine plus naive resolution invents exact
depositor-unit lineage that no source proves — "invented fungible unit
ancestry."

**D. Multi-collateral account.** One debt position economically supported by
several collateral principals (ETH + wBTC + stablecoin collateral backing one
borrowed amount). The debt's *risk support* is multi-principal even where the
debt quantity itself is single-asset.

**E. Insurance fund.** One fund balance deriving from fees, liquidation
penalties, transfers, and prior gains — mixed contribution sources, fungible
post-commingling, frequently only pool-level observability.

**F. Stablecoin reserve basket.** One claim token (the stablecoin) backed by
multiple reserve principals (cash equivalents, treasuries, other assets) in
methodology-defined proportions.

Verdict in every case: the *claim record* is one; the *principal structure*
underneath is many. The doctrine must represent many-to-one and many-to-many
principal relationships with explicit attribution quality.

# 3. Repair design

## 3.1 Principal attribution states (typed, candidate vocabulary — not auto-ratified)

```text
EXACT              evidence supports direct principal continuity
PROPORTIONAL       claim backed by multiple known principals with explicit
                   proportions (fractions evidenced, not assumed)
COMMINGLED         multiple source principals entered a fungible pool;
                   unit-level attribution is NOT preserved
DERIVED_ALLOCATION attribution exists only under an explicit methodology
                   (methodology_id mandatory on the edge)
UNRESOLVED         evidence insufficient for a safe attribution; may resolve
                   later with new evidence
UNKNOWN            no attribution evidence; terminal unless new evidence
```

Transition law: **UNKNOWN is never upgraded to EXACT.** `UNRESOLVED →
EXACT/PROPORTIONAL` requires new Book 2 evidence; `COMMINGLED → PROPORTIONAL`
requires pool-level composition evidence (e.g., reserve attestations), never
unit tracing. `DERIVED_ALLOCATION` is always weaker than the state its
methodology derives from, and must never be displayed as EXACT (§7.1
dependent-claim pattern).

## 3.2 Repaired lineage graph (D5CAP-2 as OPTION A-REVISED)

`CapitalPrincipalLineage` = typed graph records: **lineage nodes + typed
contribution edges**, supporting ONE-TO-ONE, ONE-TO-MANY, MANY-TO-ONE, and
MANY-TO-MANY principal relationships.

Contribution edge fields (candidates):

```text
source_principal_ref   upstream principal node
target_record_ref      downstream claim/position/record
attribution_state      §3.1 state
quantity, unit         only where evidenced; OPTIONAL per edge
share_fraction         only where evidenced (PROPORTIONAL); never fabricated
methodology_id         mandatory for DERIVED_ALLOCATION; optional elsewhere
valid_time             §12
book2_claim_refs       evidence bindings (mandatory where the edge asserts fact)
```

Required graph properties: queryable; replayable (valid-time parameterized);
cycle-detectable (structural property, not convention); many-to-many;
methodology-aware; UNKNOWN-preserving. Explicitly **not a simple predecessor
chain**.

## 3.3 Repaired conservation doctrine (replaces v0.1 §5 rules 1–5)

```text
CON-1  A representation does not create new principal merely by existing.
CON-2  Exact conservation may be asserted only where Book 2 evidence
       supports exact continuity (EXACT edges).
CON-3  Pooled/commingled capital preserves the SET of possible source
       principals without inventing unit-level identity.
CON-4  Fan-out does not multiply economic principal (one→many = branching).
CON-5  Fan-in does not erase source principals (many→one = contribution set).
CON-6  Multi-asset claims preserve multiple principal components
       (principal_component structure, §3.4).
CON-7  Collapse-to-principal requires an explicit methodology.
CON-8  A collapse result with unresolved attribution propagates
       UNKNOWN/INCOMPLETE — never a fabricated total.
CON-9  Cycles are detected structurally; aggregation over cycles
       de-duplicates or reports UNKNOWN.
CON-10 No consumer may infer exact principal ancestry from a COMMINGLED edge.
```

## 3.4 Multi-asset claims (LP / vault / baskets)

Positions with multi-principal backing do **not** carry a single
`principal_lineage_id`. They carry a typed contribution set:

```text
principal_component_refs
  ├── component: ETH principal   (attribution: EXACT where deposits observed)
  └── component: USDC principal  (attribution: EXACT where deposits observed)
```

A vault share points to N underlying principal components with per-component
attribution states (EXACT / PROPORTIONAL / COMMINGLED / UNKNOWN as evidence
permits). The v0.1 base field becomes `principal_component_refs` (a set) on
positions/claims, with `principal_lineage_id` retained only for genuinely
single-root chains (e.g., ETH→LST→restake, where it was correct).

## 3.5 Borrowing semantics (collateral principal ≠ borrowed principal)

The v0.1 corpus never claimed collateral-principal inheritance for borrows, but
it also never said so; this reconciliation makes it explicit doctrine:

```text
collateral principal != borrowed principal

ETH principal → CollateralPosition (encumbered; EXACT lineage)
USDC pool principal(s) [COMMINGLED from many suppliers]
  → borrowed USDC flow → borrower's DebtPosition

DebtLiability links the borrower's obligation to the market;
it does NOT merge the ETH lineage into the USDC position.
```

Collateral and debt are economically *related* (encumbrance, liquidation
rights) — never the *same principal lineage*. Stress set: single-collateral
borrow; multi-collateral borrow (§2-D); pooled lender sources (§2-C); isolated
market; cross-market redeposit (borrowed USDC redeposited carries the POOL's
commingled attribution forward, not the borrower's collateral lineage).

## 3.6 Canonical vs derived naming separation

Because D5CAP-2 (A-REVISED) makes `CapitalPrincipalLineage` the canonical
record family, the 5G derived output is renamed:

```text
CapitalPrincipalLineage       = canonical Book 5 lineage record family (§5)
CapitalPrincipalLineageView   = derived 5G projection over those records
```

No canonical/derived object may share a name. (Plan v0.1 §22's shape list is
corrected accordingly in v0.2.)

# 4. Disposition

```text
SINGLE_ROOT_DEFECT            = CONFIRMED (plan v0.1 §5 rule 1 + §2.1 + §22)
NAME_COLLISION_DEFECT         = CONFIRMED (plan v0.1 §22 vs §5)
REPAIR                        = attribution states (§3.1) + A-REVISED graph
                                (§3.2) + conservation CON-1..10 (§3.3) +
                                principal_component_refs (§3.4) +
                                borrowing doctrine (§3.5) + rename (§3.6)
PLAN_IMPACT                   = v0.2 required (supersedes v0.1 only after
                                operator ratification; v0.1 preserved unmodified)
BOOK_1_AMENDMENT_REQUIRED     = FALSE (all repairs Book 5-local)
```
