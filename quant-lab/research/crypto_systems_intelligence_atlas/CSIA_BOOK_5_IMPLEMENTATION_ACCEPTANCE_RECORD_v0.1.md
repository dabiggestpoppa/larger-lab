# CSIA — BOOK 5 IMPLEMENTATION ACCEPTANCE RECORD v0.1

> **Book:** 5 — CAPITAL PLUMBING AND ECONOMIC TOPOLOGY
> **Ratified plan:** v0.3 (`CSIA_BOOK_5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_PLAN_v0.3.md`)
> **Acceptance authority:** operator-authorized formal Book 5 implementation
> acceptance review (acceptance only — no Book 6, no live acquisition)
> **Review date:** 2026-09-30
> **Decision:** **ACCEPTED** — `PASS_CSIA_BOOK5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_KERNEL`

---

## 1. Identity

```text
BOOK                              = 5
TITLE                             = CAPITAL PLUMBING AND ECONOMIC TOPOLOGY
RATIFIED_PLAN                     = v0.3
RATIFIED_PLAN_COMMIT              = 262625fd063a17cfeb845f610a7de29c89f29b27
PLAN_RATIFICATION_COMMIT          = b33dc3c76a76228139abb4fe014d3fe404e2cee4
BOOK4_BASE                        = a2526e8220513b34967ab11f227ddbddc14e7e4a
ACCEPTED_IMPLEMENTATION_ANCHOR    = 50695ad4ea07b57105e71d04d4e32758849e55e3
BOOK5_TESTS                       = 293
TOTAL_CSIA                        = 821
```

Both plan commits are real commits (`git cat-file -t` = commit) authored on the
planning side; subjects: `plan(csia): add Book 5 plan v0.3 with unit-aware
principal doctrine` and `docs(csia): ratify Book 5 capital plumbing plan v0.3`.
They are intentionally **not** ancestors of the implementation anchor (the plan
lives on `agent/crypto-systems-intelligence-atlas-plan`; implementation source is
not merged into planning).

## 2. Phase 0 — state verified before review

```text
branch            = agent/crypto-systems-intelligence-atlas-book5-build
HEAD              = 50695ad4ea07b57105e71d04d4e32758849e55e3
origin/<branch>   = 50695ad4ea07b57105e71d04d4e32758849e55e3  (local == origin)
worktree          = clean
```

No reset, rebase, amend, force-push, or history rewrite was performed.

## 3. Phase 1 — lineage verified (strict ancestry from accepted Book 4 base)

`a2526e8220513b34967ab11f227ddbddc14e7e4a` **is an ancestor** of
`50695ad4ea07b57105e71d04d4e32758849e55e3`. All 35 named commits resolved to full
SHAs and each is a strict ancestor of the anchor:

| Stage | Full SHAs (all strict ancestors) |
|---|---|
| Initial implementation | `1f87ed4102a5a2108bdf45ee440a10658cfd1525`, `c42420b8f7abdd721babb2c03cdb2338a71983ca`, `4e7808236ef7d0f90a4db90554ccf8d99d0b0fbb`, `0ee1d9cba87111571dd141213f1fd965289266de`, `c3efa6fe81583397a7a9b97c1066efa3d7a221dd`, `fca979d92f64b2e74620249383acfa47cdcd986a`, `38b758c6015aaee3297d7c49f7637fd7f8917abb` |
| R1 | `651c988a3e0bc1e0bef830547a0caa63dd08d016`, `3e67ea2d72c8630769a256782b20b3b191b99fbc`, `e536eedb9acf8a7aa4b47a09dbfe6421df4e2b0a`, `04402bbb4762ede25c31e9244676ce39045427fc`, `10156e3bb1d85454253cf9cee55121ea4acda364`, `ae471db4cb7bbbbb1532d8448c712f35f9faff9f`, `fe4e1ba7dc3367387d898c29bc1f9f62242f6669` |
| R2 | `6c1e0a50d0fb72edf3cebe9258666c748483cc52`, `d292f930417a22dabe44f8d2d99c1b019c406ef8`, `8663298dbc120b89891f74a0fe90a29d685d97be`, `2041689c79de37eec9939296c412f53a2e8ccc16`, `8d152517299ce513ff136e615b4645d4c149cfeb`, `9f5c0ea03a2c6975d5689dbc11d6145fa61a9ddb` |
| R3 | `97270f9220c66b3787455b4d24a555a9099586a3`, `869be159b11e4418fcc2d09f261f85e9045d2940`, `30bd16e561cc3afb1248112a24115f6dd4cdfd0e`, `ec2d5334bd8d0c0079a2cb8bae58c44f122958e3`, `ddce5186ea538283d176b9f12329f9d4d5ac9cc6`, `25949c6484e2106713aedb5025fb54470ee50f4a`, `2a455bcb01f8a2958913380b8164ba7c602c18a9` |
| R4 | `a687268ff0b00bd414b710345f186a2c44f11040` |
| R5 | `b0778bb7f7748b2ea9d08755e2996c9ca9005bf2`, `dd183a414fa2bea6f09ec86cfd008d84655c08eb`, `ea4a81545e481d47caed923d34da75839c6261d6`, `6960ada51f310cdbdacedfc5224a6f68e8366dfd`, `0a7f83853fbac26866f0449f1c92042c68e03d9a`, `e181aa7e81ec66e0a50baec2ca6f8770c700850b`, `7a347f34a1d075fcd4c1534c4179c491c2c41668`, `50695ad4ea07b57105e71d04d4e32758849e55e3` |

## 4. Phase 2 — freeze scope

`git diff --name-only a2526e822..50695ad4e` touches **28 files** and nothing else:

- 7 Book 5 source modules (`book5_core`, `book5_lineage`, `book5_provenance`,
  `book5_records`, `book5_registry`, `book5_support`, `book5_synthesis`)
- 8 Book 5 test modules (`test_book5_*`)
- 13 CSIA implementation-evidence / append-only ledger files under
  `research/crypto_systems_intelligence_atlas/`

Zero Book 1–4 files, zero Crypto Sensor files, zero Book 6 files, zero
live-acquisition/RPC files.

```text
BOOK_1_ACCEPTED_CONTRACT_MUTATIONS = 0
BOOK_2_ACCEPTED_CONTRACT_MUTATIONS = 0
BOOK_3_ACCEPTED_CONTRACT_MUTATIONS = 0
BOOK_4_ACCEPTED_CONTRACT_MUTATIONS = 0
CRYPTO_SENSOR_MUTATIONS            = 0
```

## 5. Phase 3 — canonical test partition (exact selectors, no loose `-k bookN`)

Run from `quant-lab/` with the Book 4 venv interpreter
(`/c/Users/wifik/Desktop/larger-lab-book4-build/.venv/Scripts/python.exe`).
`T = tests/crypto_systems_intelligence_atlas`.

| Partition | Exact selector | Result |
|---|---|---|
| BOOK_1 | `$T/test_adversarial.py $T/test_hardening_r1.py $T/test_hardening_r2.py $T/test_pilots.py` | **107 PASS** |
| BOOK_2 | `$T/test_book2_core.py $T/test_book2_integration.py $T/test_book2_stress.py $T/test_book2_adversarial.py $T/test_book2_hardening_r1.py $T/test_book2_hardening_r2.py $T/test_book2_hardening_r3.py $T/test_book2_hardening_r4.py` | **108 PASS** |
| BOOK_3 | `$T/test_book3_architecture.py $T/test_book3_hardening_r1.py $T/test_book3_hardening_r2.py $T/test_book3_identity_history.py $T/test_book3_pilots_realization.py $T/test_book3_registry.py` | **83 PASS** |
| BOOK_4 | `$T/test_book4_adversarial.py $T/test_book4_dependencies.py $T/test_book4_fail_closed_audit.py $T/test_book4_failure_redundancy.py $T/test_book4_hard_runtime.py $T/test_book4_hardening_r1.py $T/test_book4_hardening_r2.py $T/test_book4_pilots_relations.py $T/test_book4_r2_adversarial_audit.py $T/test_book4_r3_model_copy_adversarial.py $T/test_book4_r3_pair_coverage.py $T/test_book4_substitutability_roles.py` | **230 PASS** |
| BOOK_5 | `$T/test_book5_adversarial.py $T/test_book5_blocs.py $T/test_book5_core.py $T/test_book5_hardening_r1.py $T/test_book5_hardening_r2.py $T/test_book5_hardening_r3.py $T/test_book5_hardening_r4.py $T/test_book5_hardening_r5.py` | **293 PASS** |
| TOTAL_CSIA | `$T` | **821 PASS** |

The partition reconciles exactly: 107 + 108 + 83 + 230 + 293 = 821.

## 6. Phase 4 — hardening preservation (each suite run separately)

```text
R1 = 37 PASS   R2 = 44 PASS   R3 = 46 PASS   R4 = 51 PASS   R5 = 37 PASS
```

No suite silently skipped (each run as its own explicit file selector).

## 7. Phases 5–6 — core doctrine and epistemic authority

- Grammar separation **CAPABILITY != CAPACITY != FLOW != STOCK != POSITION !=
  CLAIM != LIABILITY != EXPOSURE != ECONOMIC PRINCIPAL** is declared in
  `book5_core.py` (module docstring) and enforced by typed records
  (`PositionKind`, `QuantitativeRecordKind`, `TransformationKind`) with no
  cross-domain collapse path; 18 doctrine tests PASS, including
  `test_no_cross_unit_aggregation_exists`, `test_attribution_arithmetic_law`,
  `test_unpromotable_claim_state_fails_closed`,
  `test_unknown_location_never_carries_precision`.
- **Book 2 is the only epistemic engine.** `claims.py` defines
  `Book2ClaimState` with `ClaimState = Book2ClaimState` as an *alias*; Book 5
  modules import `Book2ClaimState` explicitly (`book5_support.py`). There is
  **no Book 5 `ClaimState` class** and no parallel truth machine.
- Every canonical Book 5 economic fact is Book 2-backed; the Book 2 transition
  engine (`LEGAL_TRANSITIONS`, `ClaimStateEngine`) is the only state authority.
- Currentness is checked at decision time, never remembered from construction:

```text
REGISTERED THEN  != AUTHORITATIVE NOW      (R4)
BINDING CREATED THEN != AUTHORITATIVE NOW  (R5)
```

## 8. Phases 7–11 — hardening seal review

| Round | Seals verified | Rows | Result |
|---|---|---|---|
| R1 | no UNKNOWN→EXACT `model_copy` bypass; no unit / asset / realization mutation bypass; no fabricated quantity zero; no `csia:token:none`; no fake claim ref; flow-only snapshot uses explicit incomplete/gap semantics; raw dict inputs fail closed with typed errors; no AttributeError authority path | 37 | PASS |
| R2 | authority operations require explicit provenance; no optional-provenance bypass; `ClaimContextBinding` required for principal-component authority (NO CONTEXT BINDING != CONTEXT VERIFIED); asset/unit/realization context **established**, not merely non-contradicted; `CapitalFieldSynthesis` has no authority mode without `Book5Provenance` | 44 | PASS |
| R3 | `QuantitativeRecordContextBinding` exists for FLOW / LIABILITY / OBSERVED_FACT; flow, liability, observed-value contexts closed; `Book5CanonicalRecordRegistry` exists; `compose_path` and `topology_view` cannot accept arbitrary strings; wrong-kind refs reject; `observed_value_display` live-validates; 5G cannot manufacture a derived artifact from an unresolved pointer | 46 | PASS |
| R4 | registry membership != current authority; `resolve()` requires explicit provenance; registered records revalidated against CURRENT Book 2 state; decay to CONTESTED / STALE / REJECTED / SUPERSEDED rejects current resolution; legal Book 2 restoration restores resolution; path-stage, topology-node, topology-flow, and endpoint currentness enforced; `registered_record` / `registered_refs` remain structural-only | 51 | PASS |
| R5 | binding registration != current binding authority; subject-claim current != binding-basis current; both binding families' basis refs live-revalidated; empty basis refs remain legal; if basis refs present ALL must be current; weakest-link multi-basis rejection; SUPERSEDED basis does not auto-follow replacement; restored basis restores use; registry position resolution checks nested principal components | 37 | PASS |

R5 authority chain confirmed end to end:

```text
REGISTRY CURRENTNESS -> RECORD CURRENTNESS -> BINDING CURRENTNESS -> BINDING BASIS CURRENTNESS
```

Seal land code: `Book5Provenance._validate_binding_basis_live` called from the
two chokepoints `validate_principal_component` and `validate_quantitative_record`
(R5), plus `registry.resolve` live revalidation and nested-component validation
(R4 + R5 gap closure).

## 9. Phases 12–14 — lineage, unit domain, liability source of truth

- **Principal lineage:** many-to-many intact; fan-out to one root many records
  preserved (`test_lineage_fan_out_one_root_many_records`); single-root
  universal doctrine remains VOID (`test_single_root_forcing_impossible_for_lp`);
  no invented fungible unit ancestry; COMMINGLED never becomes EXACT without new
  evidence; cycle detection active (`CapitalPrincipalLineageGraph.detect_cycles`,
  collapse refuses cycle participation); collateral principal != borrowed
  principal (`test_5c_collateral_lineage_never_merges_into_borrowed_lineage`);
  `DebtLiability` relates the obligation without merging lineage. All PASS.
- **Unit domain / Book 6 seam:** `PrincipalComponentSet` is unit-aware;
  heterogeneous assets stay vectors (`test_5g_heterogeneous_vector_preserved_never_scalar`,
  `test_eth_plus_usdc_never_scalarizes`); no common-value field, no hidden
  numeraire; `share_fraction` != valuation (T-3/T-11); PROPORTIONAL != common-value
  scalar; valuation requests are `NOT_AUTHORIZED` pre-Book-6
  (`test_5g_valuation_request_not_authorized`).
  `BOOK5_CROSS_ASSET_VALUATION_AUTHORITY = FALSE`; `5G_CROSS_ASSET_VALUATION_COUNT = 0`.
- **Liability source of truth:** `DebtLiability`, `ReserveLiability`,
  `RedemptionClaim` remain canonical obligation records; no duplicate canonical
  obligation quantity lives independently in a position; divergence fails closed
  (`test_liability_projection_reconciles_or_fails`,
  `test_conflicting_position_liability_quantity_fails`,
  `test_unreferenced_liability_projection_fails`,
  `test_5c_debt_position_projection_reconciles_with_liability`). All PASS.

## 10. Phases 15–16 — Blocs 5A–5F and the 5G capital field

`test_book5_blocs.py` **25/25 PASS**, `test_book5_adversarial.py` **31/31 PASS**,
`test_book5_core.py` **22/22 PASS**.

- **5A** stablecoin issuance / circulation / bridged realization / escrow /
  redemption kept separate — PASS.
- **5B** reserves / LP claims / range / swaps / volume / routes / routed flows
  separate — PASS.
- **5C** supply / collateral / debt / borrow / repay / liquidation / bad debt /
  encumbrance separate (`test_5c_supplied_plus_borrowed_never_additive`,
  `test_5c_collateral_eligibility_is_not_posted`,
  `test_5c_borrowed_redeposit_carries_pool_commingled_attribution`) — PASS.
- **5D** native stake / LST / restake / rewards / slashing preserve principal
  lineage (one root, no 3x TVL) — PASS.
- **5E** collateral / margin / notional / OI / PnL / insurance separate;
  NOTIONAL != PRINCIPAL (`test_5e_notional_never_enters_principal_sums`) — PASS.
- **5F** on-chain token supply != off-chain value without evidence
  (`test_5f_token_supply_never_equals_offchain_value_without_evidence`) — PASS.
- **5G** derived only: `SynthesisWriteLedger.canonical_write_count` returns **0**
  by construction; 5G cannot author Book 2 claims or 5A–5F facts; outputs remain
  `CapitalFieldSnapshot`, `CapitalFieldPath`, `CapitalPrincipalLineageView`,
  `CapitalTopologyView`; every derived ref resolves canonically and currently;
  no arbitrary-string authority, no stale-ref authority, no contextless
  quantitative authority. `5G_CANONICAL_WRITE_COUNT = 0`.

## 11. Phase 17 — stress / synthesis corpus

```text
STRESS_ROWS = 45 / 45
```

All 45 rows of `CSIA_BOOK_5_STRESS_TRACEABILITY_MATRIX.json` are `PASS`, each
carrying **both** a named test and its invariant assertion (no name-only
mapping), enforced mechanically by `test_stress_traceability_complete` (PASS).

```text
5G_T_TESTS = T-1..T-14 PASS
```

T-1..T-14 are covered in the Book 5 synthesis/5G surface
(`test_book5_blocs.py` 25/25) and the adversarial semantics surface
(`test_book5_adversarial.py` 31/31).

Highest-risk cases re-checked and PASS: canonical + wrapped stablecoin, borrowed
redeposit, ETH → LST → restake, LP collateral, rehypothecation, commingled
lending pool, multi-collateral debt, multi-asset LP, multi-asset vault, reserve
basket, insurance fund, RWA basket, and the attempted Book 5 USD scalar
(`test_eth_plus_usdc_never_scalarizes`, `test_5g_valuation_request_not_authorized`).

## 12. Phase 18 — temporal semantics and replay

Flows append-only, stocks versioned, late observation preserved, supersession
preserves history; current authority decays with Book 2 and authority
restoration mirrors Book 2. Historical replay does **not** silently use current
registry membership as proof of historical truth — no point-in-time /
revoked-record replay API exists in the Book 5 modules (verified by absence of
`replay` / `as_of` / `point_in_time` machinery in `book5_*.py`). Recorded as an
**accepted limitation** (§14), not a defect, and not invented during acceptance.

## 13. Phase 19–20 — sensor and quality

```text
SENSOR                             = 2325 PASS / 14 FAIL / 4 SKIPPED
BOOK5_INTRODUCED_SENSOR_FAILURES   = 0
RUFF                               = PASS
MYPY                               = PASS
```

Sensor failure set is exactly the accepted baseline (all pre-existing
storage-evidence regeneration mismatches): `test_i05r2_evidence` ×3,
`test_i05r3_evidence` ×2, `test_i05r4_evidence` ×3, `test_i06_evidence` ×3,
`test_i06r1_evidence` ×3. No reproducible new failure; the single transient
`test_blob_store_adversarial` observation noted in the R5 report did not recur
(the file passes 29/29 in isolation and in this full run).

Quality scope and output:

- `ruff check src/crypto_systems_intelligence_atlas tests/crypto_systems_intelligence_atlas` → `All checks passed!`
- `mypy src/crypto_systems_intelligence_atlas` → `Success: no issues found in 44 source files`

## 14. Phase 22 — accepted limitations (not defects)

1. Offline deterministic kernel only.
2. No live chain acquisition; no live acquisition authority.
3. No RPC.
4. No CEX feeds.
5. No persistent DB.
6. No graph DB.
7. No production scheduler.
8. No Book 6 valuation; Book 5 holds no cross-asset valuation authority.
9. No production pricing.
10. No trading / execution authority.
11. Historical revoked-record (point-in-time) replay is **not implemented** in
    Book 5; the kernel does not claim it.
12. Context dimensions in `ClaimContextBinding` /
    `QuantitativeRecordContextBinding` remain Book 5-local typed interpretations
    where a Book 2 `Proposition` lacks native fields.

No capability beyond the above is implied or claimed.

## 15. Phase 21 — evidence review note (honest, no history rewritten)

All eleven Book 5 evidence artifacts were reviewed and are mutually consistent
(R1–R5 matrices, implementation matrix, stress traceability matrix, evidence
v0.1, R2/R3/R4/R5 hardening documents, implementation ledger). The R4 scope
over-claim regarding binding-basis currentness remains explicitly reconciled by
the R5 evidence document, as previously recorded.

**DOC-NOTE-1 (non-substantive):** in `CSIA_BOOK_5_HARDENING_R5_MATRIX.json` the
`SUPERSEDED_BASIS_NO_AUTO_FOLLOW` gate stores its narrative in the `result` field
instead of the literal `PASS`, so a naive machine count reads 26 PASS + 1
narrative rather than 27 PASS. The gate's substance is verified by rows D1–D3 of
the R5 suite (37/37 PASS). This is a documentation formatting artifact in an
already-committed historical artifact; it is recorded here rather than silently
rewritten, and it changes no gate outcome.

`CSIA_BOOK_5_IMPLEMENTATION_MATRIX.json` retains its pre-acceptance status
(`IMPLEMENTATION_COMPLETE_PENDING_OPERATOR_REVIEW`) as the historical record; this
acceptance document is the authority that supersedes it.

## 16. Phase 23 — acceptance decision

Every verification gate passed and **no new concrete correctness defect was
found** during review. Therefore:

```text
PASS_CSIA_BOOK5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_KERNEL = ACCEPTED

BOOK_5                                = FROZEN_ACCEPTED
BOOK_5_IMPLEMENTATION                 = FROZEN_ACCEPTED
BOOK_5_HARDENING_R1                   = ACCEPTED_LINEAGE
BOOK_5_HARDENING_R2                   = ACCEPTED_LINEAGE
BOOK_5_HARDENING_R3                   = ACCEPTED_LINEAGE
BOOK_5_HARDENING_R4                   = ACCEPTED_LINEAGE
BOOK_5_HARDENING_R5                   = ACCEPTED_LINEAGE
ACCEPTED_IMPLEMENTATION_ANCHOR        = 50695ad4ea07b57105e71d04d4e32758849e55e3
BOOK_6_IMPLEMENTATION_AUTHORITY       = FALSE
LIVE_ACQUISITION_AUTHORITY            = FALSE
```

Not authorized by this acceptance: Book 6 implementation, live acquisition, RPC,
database, graph database, production pricing, trading / execution. No R6 exists
or is authorized without a new concrete demonstrated defect.
