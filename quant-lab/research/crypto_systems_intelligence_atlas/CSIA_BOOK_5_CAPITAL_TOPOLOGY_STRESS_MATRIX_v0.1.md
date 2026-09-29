# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — CAPITAL TOPOLOGY STRESS MATRIX v0.1

**Document ID:** CSIA-B5-STRESS-001
**Version:** 0.1
**Status:** PLANNING STRESS MATRIX — NOT RATIFIED
**Purpose:** stress the Book 5 record contracts against the directive's 22 mandatory stress areas. Each row states the attack, the contract defenses engaged, the expected failure mode if the model were naive, and the required correct behavior. Any unresolved failure feeds the pre-ratification review.

**Companion:** plan v0.1 §6 (ALG-1..10), §5 (principal lineage), §10 (double-counting doctrine); D7 stress corpus (10 scenarios — promoted into planning tests per Phase 19).

---

# Legend

```text
DEFENSES:    plan contracts engaged (section refs)
NAIVE-FAIL:  what an unprincipled additive model would do
REQUIRED:    correct behavior under Book 5 contracts
STATUS:      COVERED (contract as planned handles it) | OPEN (design choice pending D5CAP) 
```

---

# Part I — the ten promoted D7 corpus scenarios (Phase 19 mandatory tests)

| # | Stress | Defenses | Naive-fail | Required | Status |
|---|---|---|---|---|---|
| 1 | USDC deposited into lending | §2.2 CollateralPosition/claims; §2.3 liability records; ALG-3/8 | supplied+borrowed summed as 1,800 principal | 1,000 principal; 800 redeployed; 800 liability record | COVERED |
| 2 | Borrowed capital redeposited elsewhere | §5 lineage (fan-out branching); ALG-8 dedup | same USDC counted in two markets' TVL | lineage traces to one principal; cross-market sum de-duplicates or UNKNOWN | COVERED |
| 3 | ETH → LST | §2.3 ClaimTokenRepresentation; §19 lineage branch | ETH staked + LST supply counted twice | one principal, two linked branches (bonded stake + liability-backed claim) | COVERED |
| 4 | LST → restaking | §19 three-branch lineage; §19.2 | three-layer TVL multiplication | three representations, one principal; collapse only via explicit derivation | COVERED |
| 5 | LP token collateralized | §2.2 encumbrance_state; Encumbrance records | pool TVL + collateral value + borrow triple-count | encumbrance typed state; principal counted once with pledge links | COVERED |
| 6 | Canonical + wrapped stablecoin | §16 six-way supply split; §5 lineage | canonical + wrapped summed as total supply | linked realization supply; escrow backing + redemption liability recorded | COVERED |
| 7 | Vault shares over underlying strategy | §4 transformation records; §5 cycle rules | vault AUM + strategy deposits doubled | share = claim record; strategy leg = lineage branch | COVERED |
| 8 | Perp collateral vs notional | §20 exposure domain; ALG-5/9 | notional/OI added to spot capital | exposure-domain records only; never principal | COVERED |
| 9 | RWA token vs off-chain underlying | §21 equivalence-UNKNOWN rule | token cap + underlying value counted separately | equivalence UNKNOWN without redemption/backing evidence | COVERED |
| 10 | Rehypothecation | §2.2 encumbrance REHYPOTHECATED; §5 chain rules | every re-pledge hop inflates total collateral | encumbrance chain typed; unobserved hops → UNKNOWN | COVERED |

---

# Part II — additional structural stress (the directive's 22-area expansion)

| # | Stress | Defenses | Naive-fail | Required | Status |
|---|---|---|---|---|---|
| 11 | Recursion (deep deposit loops) | §5 rules 3–4; ALG-8; cycle detection | n-loop depth inflates n× | cycles detected; dedup or UNKNOWN | COVERED |
| 12 | Cyclic lending (A→B→A) | §5 rule 4; lineage DAG constraint | infinite/looped principal growth | cycle flagged; aggregation de-duplicates | COVERED |
| 13 | Vault-over-vault nesting | §4/§5; claim-link records | per-layer TVL sum | nested claims; single principal at root | COVERED |
| 14 | Leveraged LP loops | §5 cycles + §20 exposure | loop multiplies both TVL and exposure | cycle detection + exposure-domain separation | COVERED |
| 15 | Liquidation chains | §3 LIQUIDATION flows; ALG-2 | silent stock rewrites | each liquidation an append-only flow; stocks re-versioned | COVERED |
| 16 | Bad debt / socialization | §18 records; ALG-6 | loss vanishes or silently scales positions | typed loss event; socialization targets recorded | COVERED |
| 17 | Negative / zero / unknown quantities | ALG-7; P2 (UNKNOWN≠0) | unknown treated as 0 in sums | UNKNOWN propagates; zero only if observed | COVERED |
| 18 | Missing ownership | §2.1 holder UNKNOWN; P17 | custody inferred as ownership | ownership UNKNOWN preserved; custody separate | COVERED |
| 19 | Missing custody | §1.4 UNKNOWN location; §2.1 custody_ref | location guessed from protocol type | UNKNOWN without invented precision | COVERED |
| 20 | Off-chain unknowns | §1.4 OFFCHAIN types; observability marker | on-chain-style precision invented off-chain | observability-marker-typed; UNKNOWN-preserving | COVERED |
| 21 | Disputed backing / contested supply | P1; F-2/F-5 contradiction doctrine | averaged or single-sided truth | CONTESTED states; no averaging | COVERED |
| 22 | Depegged claim token | §2.3 claim records; P15 | token price treated as principal | principal lineage separate from market price; depeg is measurement (Book 6) | COVERED |
| 23 | Protocol migration | §1.1 site lifecycle; Book 1 MIGRATED refs | positions lost or duplicated at migration | site lifecycle links; positions re-pointed with history preserved | COVERED |
| 24 | Position transfer | §3/§4 events | transfer treated as new principal | ownership hand-off event; lineage continuous | COVERED |
| 25 | Cross-chain position migration | §1.4; realizations; §5 | double-count during transit | in-flight state typed; realization swap recorded as transformation | COVERED |

(22 directive areas map to rows 1–25 above; D7 rows 1–10 are the mandatory corpus.)

---

# Result

```text
STRESS_ROWS = 25 (10 promoted D7 corpus + 15 structural expansion)
COVERED     = 25
OPEN        = 0 (D5CAP-1/D5CAP-2 design choices affect record shape, not stress outcomes)
BOOK_5_PLAN_HOLD_TRIGGERED = FALSE
```

Caveat recorded honestly: "COVERED" means the *planned contracts* handle each
case; executable proof belongs to implementation-phase tests. The
pre-ratification review (20 questions) re-attacks the same surface from the
failure side.
