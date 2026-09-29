# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — CAPITAL PLUMBING AND ECONOMIC TOPOLOGY — PLAN v0.2

**Document ID:** CSIA-B5-PLAN-002
**Version:** 0.2
**Status:** PLANNING DRAFT — READY_FOR_OPERATOR_RATIFICATION — NOT RATIFIED
**Supersedes:** `CSIA_BOOK_5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_PLAN_v0.1.md` (preserved unmodified) — **supersession takes effect only upon operator ratification of v0.2**
**Authority:** BOOK_5_PLANNING_AUTHORITY = TRUE; BOOK_5_IMPLEMENTATION_AUTHORITY = FALSE; LIVE_ACQUISITION_AUTHORITY = FALSE
**Gates closed:** D7 (Option B) — Operator Decision Log BOOK 5 DECISION (D7); D5CAP-1/2/3 (Operator Decision Log, BOOK 5 DECISIONS session 2026-09-29 reconciliation)
**Repairs incorporated:** single-root principal-lineage defect (`CSIA_BOOK_5_PRINCIPAL_LINEAGE_RECONCILIATION_v0.1.md`); D5CAP-1 liability single-source-of-truth; canonical/derived lineage naming seal

**Companion artifacts:** stress matrix (`..._CAPITAL_TOPOLOGY_STRESS_MATRIX_v0.2.md`), primitive matrix v0.3, relationship support matrix v0.1, 5G synthesis matrix v0.2, pre-ratification review v0.2, D7 reconciliation set.

---

# 0. Book goal (roadmap-verbatim — unchanged)

Map how value actually moves and where it becomes:

```text
issued / routed / held / locked / traded / lent / borrowed / collateralized /
staked / restaked / leveraged / transformed / redeemed /
or exits the modeled economic system
```

## 0.1 Core economic grammar (unchanged, mechanically preserved)

```text
CAPABILITY != CAPACITY != FLOW != STOCK != POSITION != CLAIM !=
LIABILITY != EXPOSURE != ECONOMIC PRINCIPAL
```

Book 6 owns capacity/measurement; Book 1 owns capability edges and identity;
Book 5 owns canonical economic facts (5A–5F) and derived topology (5G).

## 0.2 Planning principles (B5-P1 – B5-P31)

B5-P1..P28 carry over from v0.1 unchanged. v0.2 adds three:

```text
B5-P29 Principal attribution must state its evidence quality
       (attribution state). UNKNOWN is never upgraded to EXACT.
B5-P30 A canonical liability/obligation quantity has exactly one
       authoritative record; positions reference it and never independently
       restate it.
B5-P31 Multi-asset claims preserve their principal components; no claim is
       forced into a single principal root.
```

---

# 1. Identity contracts (v0.1 §1 carried forward, with repairs)

- **EconomicSite / SiteRef:** Book 5-local, anchored to Book 1 protocol/deployment identities; lifecycle via Book 1 MIGRATED refs; escalation criterion unchanged (plan v0.1 §1.1). Unchanged by v0.2.
- **Position identity:** unchanged (v0.1 §1.2) **except** the base lineage field: positions carry `principal_component_refs` (a typed contribution set) instead of a mandatory singular `principal_lineage_id` (§4.2 here). A singular lineage id remains legal only for genuinely EXACT single-principal chains.
- **Flow / transformation identity:** unchanged (v0.1 §1.3); flow and transformation events now reference contribution sets where their source/target claims are multi-principal.
- **Location ontology:** unchanged (v0.1 §1.4).

---

# 2. Record contracts — position family (v0.1 §2 with D5CAP-1 + lineage repairs)

Family unchanged in membership: `CapitalPosition` (base; kinds CLAIM_SIDE / LIABILITY_SIDE / CUSTODY_OBSERVATION) with specializations `CapitalBalance`, `LiquidityPosition`, `CollateralPosition`, `DebtPosition`, `StakePosition`, `RestakePosition`, `YieldPosition`, `SettlementBalance`; plus the separate liability/claim family.

## 2.1 Base fields (v2)

v0.1 base fields stand, with two changes:

1. `principal_lineage_id` (singular) → **`principal_component_refs`** — a typed set of principal components `{component_ref, attribution_state, share_fraction?}`; per-component attribution states from §3.1; share_fraction present only where evidenced (PROPORTIONAL).
2. New optional reference: `liability_refs` — typed pointers to the canonical liability records this position relates to (per D5CAP-1, below).

All other v0.1 base fields (identity, asset/realization/claim-token refs, holder UNKNOWN-legal, protocol/deployment/site/location/custody refs, quantity+unit, valid/observation time, `book2_claim_refs`, `encumbrance_state`) carry over unchanged.

## 2.2 D5CAP-1 binding: liability single-source-of-truth (B5-P30)

```text
CANONICAL OBLIGATION RECORDS (the only authoritative quantity/state):
  DebtLiability       — canonical borrowed-obligation quantity and state
  ReserveLiability    — canonical issuer/protocol backing obligation
  RedemptionClaim     — canonical redemption entitlement

POSITION RECORDS (actor/site/context):
  DebtPosition        — references its DebtLiability; carries debtor, market,
                        site, encumbrance context
  (any position)      — may reference canonical liability records

RULE (mechanical consistency):
  A position may restate a liability quantity ONLY as a typed
  reference-projection of the canonical value at a stated observation time.
  Divergence between a projection and its canonical source at equal
  observation parameters is a contract violation and fails closed.
  No two records may hold independently authored canonical obligation
  quantities for the same obligation.
```

Specializations otherwise unchanged from v0.1 §2.2 (eligibility-vs-posted, debt-liability pairing, delegation chains, AVS sets, segregability states).

## 2.3 Claim/liability model (v0.1 §2.3 finalized by D5CAP-1)

Liabilities are **separate typed economic objects** — the Option-B design is
now decision-bound, closing the v0.1 design question. Never flattened:
principal ≠ representation ≠ claim ≠ liability ≠ exposure. `Encumbrance`
remains the typed pledge/rehypothecation state record.

---

# 3. Principal attribution states (new — B5-P29)

Candidate vocabulary (binding semantics; names final at ratification):

```text
EXACT               evidence supports direct principal continuity
PROPORTIONAL        backed by multiple known principals with explicit,
                    evidenced proportions
COMMINGLED          multiple source principals entered a fungible pool;
                    unit-level attribution is NOT preserved
DERIVED_ALLOCATION  attribution exists only under an explicit methodology
                    (methodology_id mandatory)
UNRESOLVED          evidence insufficient for safe attribution; may resolve
UNKNOWN             no attribution evidence; terminal absent new evidence
```

Transition law: UNKNOWN is never upgraded to EXACT; UNRESOLVED→EXACT/PROPORTIONAL requires new Book 2 evidence; COMMINGLED→PROPORTIONAL requires pool-composition evidence, never unit tracing; DERIVED_ALLOCATION never displays as EXACT. No consumer may infer unit ancestry from COMMINGLED edges (CON-10).

---

# 4. Principal-lineage doctrine (v0.2 — REPAIRS v0.1 §5; D5CAP-2 A-REVISED binding)

## 4.1 The v0.1 defect (recorded, repaired)

v0.1 §5 rule 1 — "every lineage node traces to exactly one economic principal
at its root" — is **void**: false for LP shares, multi-asset vaults, pooled
lending, multi-collateral accounts, insurance funds, and reserve baskets
(reconciliation artifact §2). v0.2 replaces it with a many-to-many graph.

## 4.2 Repaired model

`CapitalPrincipalLineage` (canonical record family — **canonical**; the derived 5G projection is named `CapitalPrincipalLineageView`, per the D5CAP-3 naming seal) = lineage **nodes** + typed **contribution edges**:

```text
contribution edge {
  source_principal_ref, target_record_ref,
  attribution_state            (§3),
  quantity, unit               (optional per edge — never fabricated),
  share_fraction               (only where evidenced),
  methodology_id               (mandatory for DERIVED_ALLOCATION),
  valid_time, book2_claim_refs
}
```

Supported relationships: ONE-TO-ONE, ONE-TO-MANY, MANY-TO-ONE, MANY-TO-MANY.
Graph properties (binding): queryable, replayable, cycle-detectable
(structurally), many-to-many, methodology-aware, UNKNOWN-preserving.
Explicitly **not a simple predecessor chain**.

Multi-asset claims:

```text
LP CLAIM  ├── ETH principal component (attribution per evidence)
          └── USDC principal component
VAULT SHARE → N principal components (per-component attribution states)
```

## 4.3 Conservation doctrine (CON-1..CON-10 — replaces v0.1 §5 rules)

```text
CON-1  A representation does not create new principal merely by existing.
CON-2  Exact conservation is assertable only where Book 2 evidence supports
       exact continuity (EXACT edges).
CON-3  Pooled/commingled capital preserves the SET of possible source
       principals without inventing unit-level identity.
CON-4  Fan-out does not multiply economic principal.
CON-5  Fan-in does not erase source principals.
CON-6  Multi-asset claims preserve multiple principal components.
CON-7  Collapse-to-principal requires an explicit methodology.
CON-8  Collapse with unresolved attribution propagates UNKNOWN/INCOMPLETE.
CON-9  Cycles are detected structurally; cycle aggregation de-duplicates
       or reports UNKNOWN.
CON-10 No consumer may infer exact principal ancestry from a COMMINGLED edge.
```

## 4.4 Borrowing semantics (new doctrine — B5-P12-adjacent)

```text
COLLATERAL PRINCIPAL != BORROWED PRINCIPAL

ETH principal → CollateralPosition (encumbered; EXACT where observed)
USDC pool principal(s) [COMMINGLED across suppliers]
  → borrowed-USDC flow → borrower's DebtPosition → DebtLiability (canonical)

The DebtLiability links borrower obligation to the market.
The borrowed USDC does NOT inherit the ETH collateral lineage.
```

Stress coverage: single-collateral borrow; multi-collateral borrow (multi
support principals, one obligation); pooled lender sources (COMMINGLED);
isolated market; cross-market redeposit (borrowed assets carry the pool's
commingled attribution forward, never the borrower's collateral lineage).

## 4.5 Multi-asset / pooled stress closure

LP/vault/basket/insurance/reserve claims preserve principal components with
per-component attribution; exact collapse is allowed only where every component
is EXACT (or PROPORTIONAL with evidenced fractions, under methodology);
COMMINGLED/UNKNOWN components force INCOMPLETE outputs (§9).

---

# 5. Flow and transformation contracts (v0.1 §3–§4 carried forward)

Unchanged except: events reference `principal_component_refs` where source/target claims are multi-principal; transformation "principal lineage" references become contribution-set references; the 21-type candidate flow enum and transformation preservation lists stand as in v0.1 (enum ratifies at plan review).

---

# 6. Stock / flow / exposure algebra (v0.1 §6 ALG-1..10 + v0.2 additions)

ALG-1..10 carry over unchanged. v0.2 adds:

```text
ALG-11 Attribution states participate in algebra: sums over EXACT edges are
       assertable; sums touching COMMINGLED/UNKNOWN edges yield UNKNOWN or
       an explicitly labeled DERIVED_ALLOCATION result — never a silent
       exact total.
ALG-12 A multi-component claim contributes each component to its own
       principal domain; component shares enter sums only when evidenced
       (share_fraction) or methodology-derived (DERIVED_ALLOCATION).
ALG-13 Liability projections must reconcile with their canonical liability
       record (D5CAP-1); unreconciled projections fail closed.
```

The v0.1 planning theorem stands: no "total capital" without claim/liability
classification, principal lineage, dedup methodology, unknown handling, and a
methodology ID.

---

# 7. Exit doctrine, seams, temporal/evidence contracts (v0.1 §7–§9 carried forward)

Unchanged: TRUE ECONOMIC EXIT vs OBSERVABILITY EXIT (§7); Book 4 frozen fence
and route-vs-flow (§8.1); Book 6 `TOPOLOGY_DERIVATION` vs `MEASUREMENT_METRIC`
dividing line (§8.2); Book 8 non-absorption, D8 untouched (§8.3); Book 2
evidence monopoly (§8.4); the four Book 1 extension candidates all
`BOOK5_LOCAL_SUFFICIENT`, no amendment (§8.5); §12 bitemporal + replay (§9).

---

# 8. Bloc contracts 5A–5F (v0.1 §16–§21 carried forward with two v0.2 corrections)

All v0.1 bloc contracts (5A stablecoin rails six-way supply split; 5B
seven-way liquidity split; 5C credit claims/liabilities; 5D lineage branches;
5E exposure domains; 5F UNKNOWN equivalence) stand, with corrections:

1. **5C:** debt records follow D5CAP-1 — `DebtLiability` is the canonical obligation; `DebtPosition` references it (projection-consistency ALG-13). The v0.1 "supplied+borrowed != additive principal" rule stands, now with explicit pool-COMMINGLED semantics for supplied sides.
2. **5D:** the ETH→LST→restake chain remains a valid single-root EXACT chain; v0.2 adds that multi-asset vault/yield claims in 5D use principal components (B5-P31), and borrowed-vs-collateral lineage separation (§4.4) applies wherever 5D positions interact with 5C credit.

Exit-gate names unchanged (`PASS_CSIA_B5A..B5F…`); evidence requirements now
include attribution-state correctness on every multi-principal case.

---

# 9. Bloc 5G — Capital Field synthesis (v0.2; D5CAP-3 binding)

## 9.1 Output shapes (naming sealed)

```text
CapitalFieldSnapshot          immutable, versioned composition at valid time T
CapitalFieldPath              typed issuance→…→exit path (canonical-record refs)
CapitalPrincipalLineageView   DERIVED projection over canonical lineage
                              (RENAMED from v0.1's colliding shape;
                              canonical family owns CapitalPrincipalLineage)
CapitalTopologyView           projected topology surface
```

## 9.2 Collapse semantics (multi-root aware — supersedes v0.1 INV-5G-5 phrasing)

```text
EXACT lineage                  may collapse directly when evidence permits
PROPORTIONAL lineage           may collapse only with explicit evidenced
                               fractions (or methodology-derived allocation)
COMMINGLED lineage             must NOT fabricate unit ancestry; pool-level
                               totals only, labeled as such
UNKNOWN lineage                propagates INCOMPLETE
CYCLIC lineage                 structural detection; de-duplicated or
                               INCOMPLETE (never expanded)
DERIVED_ALLOCATION             requires methodology ID on the output field
```

Binding: no 5G output may imply greater lineage precision than its source
records contain. INV-5G-1..7 stand (synthesis matrix v0.2 extends the tests:
multi-root, commingling, proportional attribution, unknown propagation,
naming separation, liability single-source-of-truth). 5G canonical write
count = 0 unchanged.

---

# 10. Double-counting doctrine (v0.1 §10 + attribution extension)

Rules 1–7 stand; rule 2 extended: liabilities are canonical in exactly one
record (D5CAP-1). New rule 8: **attribution-honest aggregation** — totals over
multi-principal claims must decompose by component/attribution state; a total
that silently assumes EXACT where sources are COMMINGLED/UNKNOWN violates
ALG-11 and fails review.

---

# 11. Implementation prohibitions (v0.1 §12 + v0.2 additions)

All v0.1 prohibitions stand, plus:

```text
NO SINGLE-ROOT LINEAGE ASSUMPTION.
NO INVENTED FUNGIBLE UNIT ANCESTRY.
NO COLLATERAL-PRINCIPAL = BORROWED-PRINCIPAL COLLAPSE.
NO CANONICAL/DERIVED LINEAGE NAME COLLISION.
NO DUPLICATED CANONICAL LIABILITY QUANTITY.
NO UNKNOWN = EXACT.
```

# 12. Exit gates (unchanged names; v0.2 evidence additions noted in bloc §8)

`PASS_CSIA_B5A_STABLECOIN_RAILS` … `PASS_CSIA_B5_CAPITAL_FIELD_V1`.

# 13. Operator decisions (closed this cycle)

```text
D7      = CLOSED (Option B)          — recorded 2026-09-29, commit 9653d8d8
D5CAP-1 = CLOSED / B                 — separate typed liability objects
D5CAP-2 = CLOSED / A-REVISED         — typed many-to-many lineage graph
D5CAP-3 = CLOSED / A                 — versioned snapshots + views
OPEN_OPERATOR_DECISION_COUNT = 0
```

# 14. Plan status

```text
BOOK_5_PLAN_VERSION = v0.2
BOOK_5_PLAN_v0.1    = SUPERSEDED_PENDING_RATIFICATION (preserved unmodified)
BOOK_5_PLANNING     = READY_FOR_OPERATOR_RATIFICATION
BOOK_5_OPERATOR_RATIFIED = FALSE
BOOK_5_PLAN_HOLD_TRIGGERED = FALSE
```
