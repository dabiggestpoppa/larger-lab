# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 1 — PRE-RATIFICATION ADVERSARIAL REVIEW

**Document ID:** CSIA-B1-ADVREV-001
**Version:** 0.1
**Status:** REVIEW COMPLETE — EVIDENCE-BASED VERDICTS ONLY
**Method:** Every question is answered strictly with evidence from the planning contracts (Book 1 plan v0.2, stress matrix + ERRATA v0.1.1, extension adjudication, Constitution v0.2, decision packet). No question is declared PASSED without a cited contract mechanism. Questions with unresolved dependencies are marked accordingly — a pass here is a *contract-capability* pass, never a ratification.
**Review scope caveat:** These verdicts assess whether the *planned contract* can represent each case. They are planning-level proofs by construction, not implemented and executed tests. Test execution belongs to post-authorization implementation under each bloc's test plan.

**Verdict enum:**

```text
PASS              = contract mechanism exists and is cited
PASS_CONDITIONAL  = mechanism exists but depends on an open operator decision
FAIL              = no contract mechanism (would require amendment)
```

---

# Q1. Can Bitcoin be represented without pretending it is account/EVM based?

**Verdict: PASS**
Evidence:
- BTC as asset: `NATIVE_TO` edge + deployment with `NATIVE` marker (plan v0.2 1A.6 marker enum; stress matrix P1).
- No fabricated contracts: 1A.7 rule 8 (bridged representatives only), T-1A-12 marker round-trip.
- UTXO semantics: family extension slots (1B.6 "UTXO-set semantics"), never account-model fields; T-1B-6 anti-EVM-bias test mandates no EVM-required field for non-EVM classes.
- Lightning: `STATE_CHANNEL` role tag (E-2, C-5) + `RUNS_ON` without `USES_VM` (ADV-1B-K, T-1B-7).
- Mining security: SECURED_BY `mechanism: POW` (E-1, C-1) — staking edges correctly absent (P4's negative RESTAKED_IN test confirms non-forcing).
Residual: none at contract level. Bitcoin Script is a family attribute (no VM object), per P1 design.

# Q2. Can Ethereum distinguish ETH, Ethereum, EVM, L2s and token contracts?

**Verdict: PASS**
Evidence:
- ETH = TOKEN (`NATIVE_TO` chain); Ethereum = BLOCKCHAIN; EVM = VM object (`USES_VM` edge); L2s = separate BLOCKCHAIN objects with `ROLLUP_*` role tags + `SETTLES_TO`; ERC-20s = TOKEN objects with CONTRACT-marker deployments `ISSUED_ON` (stress matrix P2; plan 1A.6, 1C.6).
- ETH ≠ Ethereum ≠ EVM is exactly Axiom 2's separation with distinct namespaces (1A.7 rule 2).
- Sequencer systemic risk: SEQUENCER_INFRASTRUCTURE class + DEPENDS_ON from rollups (P2; ADV-1B-E).
- Settlement vs bridge: SETTLES_TO vs BRIDGES_TO rule (1C.6, R-1C-2 review point).
Residual: none. (Ethereum is the "inverse stress" — its risk is over-generalization, guarded by the other pilots.)

# Q3. Can XRPL distinguish XRP from XRP Ledger and issued assets?

**Verdict: PASS**
Evidence:
- XRP = TOKEN (`NATIVE_TO` XRPL); XRPL = LEDGER object; issued assets = TOKEN objects with ISSUER_ACCOUNT-marker deployments (E-5 marker enum, C-2; stress matrix P3).
- Trustlines: family extension slot (1B.6; E-6 confirmation) + T-1A-11.
- The XRPL↔EVM sidechain separation is an explicit adversarial finding (P3 "what breaks" item 5) resolved by strict object separation.
Residual: none.

# Q4. Can Solana represent programs/accounts without EVM concepts?

**Verdict: PASS**
Evidence:
- Programs: PROGRAM marker (E-5); SPL mints: MINT_ACCOUNT marker (E-5); state-in-accounts vs stateless-program distinction captured at family-slot level (1B.6 Solana slots; P4).
- Program-level trust assumptions for program-native issuance acknowledged (P4).
- Family MEV (block-engine vs builder/relay): family slots, not tag parameters (E-7 clarification, C-7).
Residual: none at contract level; exact family-slot schemas are Book 3B content by design.

# Q5. Can Cosmos distinguish Cosmos Hub, ATOM, Cosmos SDK, CometBFT and IBC?

**Verdict: PASS**
Evidence:
- Each appchain = own BLOCKCHAIN object; ATOM = TOKEN (`NATIVE_TO` Cosmos Hub); IBC = INTEROP_PROTOCOL object (distinct from any chain); SDK/CometBFT = family attributes/slots (stress matrix P5; plan 1B.6).
- This is the IACER §A2 founding example (ATOM ≠ Cosmos SDK ≠ IBC ≠ Cosmos Hub), verified structurally in P5.
- IBC channels: HE-BRIDGE-ROUTE + route_attributes (E-8, C-3); ICS: HE-SECURITY-SHARE (E-9 confirmation).
- IBC vouchers specifically: **PASS_CONDITIONAL** — representation pending R-1A-5 (see Q13/Q15 note; Option B rejected because it would break Q12's temporal requirements).
Residual: voucher representation conditional on R-1A-5.

# Q6. Can ICP represent canisters/subnets/compute without pretending they are smart contracts on an EVM chain?

**Verdict: PASS**
Evidence:
- Canisters: APPLICATION objects with CANISTER marker (E-5); reverse-gas as family attribute; canisters explicitly "not contracts" in P6 finding.
- Subnets: chain_scope attribute on RUNS_ON/VALIDATED_BY (E-10, C-4) — subnet-level validation is representable, which a flat chain model cannot do.
- NNS: GOVERNANCE_SYSTEM object with executable GOVERNED_BY (P6).
- Chain-key bridging: HE-BRIDGE-ROUTE mechanism THRESHOLD_BFT/CHAIN_KEY (E-8/E-11).
Residual: subnet/shard scope-objects' detailed schemas are Book 3B content (recorded information gap).

# Q7. Can the DAG pilot be represented without forcing block-chain assumptions?

**Verdict: PASS**
Evidence:
- DAG role tag composes with EVM tag on the same BLOCKCHAIN object (P7 composition test) — neither collapsed into "just an EVM chain" nor forced into linear-block language.
- Finality: finality_device slot (E-12, C-6) + finality-anchored valid time (ADV-1D-K, T-1D-11) — non-linear ordering semantics representable.
Residual: finality-device value population deferred to Book 3B (recorded information gap; slot is contractual).

# Q8. Can an asset migrate chains while preserving history?

**Verdict: PASS**
Evidence:
- Migrations: same object_id, new deployments + MIGRATED_FROM/MIGRATED_TO edges with valid-time bounds (1A.7 rule 6); dual-running windows legal (ADV-1D-E, T-1D-6); old token preserved as deprecated object with REDEEMS_FOR/MIGRATED_TO.
- Bitemporal late-discovery: observed_at now, valid_from historical (R8, ADV-1D-A, T-1D-2).
- No deletion: INV-1D-1/INV-1A-4; replay honors both world-change and evidence-failure paths (ADV-1D-B, T-1D-3).
Residual: none.

# Q9. Can a protocol have many deployments without becoming many protocols?

**Verdict: PASS**
Evidence:
- One canonical object + N DeploymentIdentity (1A.6, 1A.7 rule 7; Constitution §8.4); deployments keyed per chain+marker; same address string on different chains = different deployments (T-1A-6, ADV-1A-G).
Residual: none.

# Q10. Can the same ticker refer to unrelated assets safely?

**Verdict: PASS**
Evidence:
- Tickers are contextual attributes with valid windows and collision_groups, never identity (1A.7 rule 3); ticker-keyed dedup/merge forbidden; ADV-1A-A (unrelated "GAS" tokens) + T-1A-2; ADV-1A-C (name reuse across projects) treated as collision, not merge.
Residual: none.

# Q11. Can one relationship be contested by two credible sources?

**Verdict: PASS**
Evidence:
- Claim states attach to claim-evidence pairs, multiple claims per edge (Constitution §7.1); CONTESTED records all sides, never averages (§7, Book 0 packet §5); two different valid_from candidates coexist (ADV-1D-C, T-1D-4); contradictions must remain visible on every surface (Book 0 §5 rule 5).
Residual: none.

# Q12. Can the system represent unknown valid_from/valid_to without inventing dates?

**Verdict: PASS**
Evidence:
- UNKNOWN{earliest_bound, latest_bound, confidence_ref} distinct from null/open (R9, INV-1D-4, T-1D-5, ADV-1D-D); Axiom 6 (missing ≠ false); "never a silently fabricated exact date" (Constitution §12.2).
Residual: none. (Note: this rule is precisely why R-1A-5 Option B was rejected — attribute-level time cannot satisfy it.)

# Q13. Can a multi-party relationship remain atomic where pairwise edges lose meaning?

**Verdict: PASS**
Evidence:
- Hyperedge registry with per-participant roles (1C.6; Constitution §11.1); decomposition prohibition — pairs only as derived views (IR-9, INV-1C-4-role-coverage, T-1C-6); route_attributes preserve channel-level truth that pairwise flattening destroys (E-8, C-3; ADV-1C-K).
- USDC issuance hyperedge is the worked example (HE-ISSUANCE).
Residual: none for registered classes; new hyperedge classes go through the 1B extension mechanism.

# Q14. Can a narrative exist without being promoted to structural truth?

**Verdict: PASS**
Evidence:
- Narrative-evidence promotion firewall (Constitution §20.1): E4 may set narrative state, never claim state; E4-only can never produce OBSERVED/CORROBORATED (§6.1); announcement-only integrations land as narrative references, not edges (ADV-1C-A/G, IR-8, T-1C-4); NARRATIVE is a node class, structurally separate.
Residual: none.

# Q15. Can future Capital Field data attach without altering Book 1 identity truth?

**Verdict: PASS**
Evidence:
- Identity is closed under its own operations: merges/splits/renames are event-mediated with history preserved (1A.6 IdentityResolutionEvent; INV-1A-6); no later book can redefine an object_id's referent (1A.7 rule 1; Constitution §8.2–8.3).
- Capital Field touches: capability edges (COLLATERAL_IN, LIQUIDITY_ON, ROUTED_THROUGH) already typed in 1C with capability/capacity/flow separation (Constitution §19.1) — flow events attach as *event objects referencing edges*, never mutating edge truth; INV-1C-4 forbids magnitudes on capability edges.
- Capital Field reconciliation gate (Constitution §4.3, D7) governs scope, not identity; Book 1 identity is explicitly out of its blast radius.
- Measurement capacity attaches via the measurement layer (Book 6), not identity fields (1C.6 LIQUIDITY_ON note).
Residual: none at identity level; the D7 reconciliation remains a scheduled decision.

---

# SUMMARY

```text
Q1  Bitcoin native modeling            PASS
Q2  Ethereum separations               PASS
Q3  XRPL separations                   PASS
Q4  Solana programs/accounts           PASS
Q5  Cosmos separations                 PASS (voucher form: PASS_CONDITIONAL -> R-1A-5)
Q6  ICP canisters/subnets              PASS
Q7  DAG non-block assumptions          PASS
Q8  Chain migration w/ history         PASS
Q9  Protocol w/ many deployments       PASS
Q10 Ticker collision safety            PASS
Q11 Contested relationships            PASS
Q12 Unknown valid time                 PASS
Q13 Atomic multi-party relationships   PASS
Q14 Narrative containment              PASS
Q15 Capital Field attachment safety    PASS

PASSED             = 14
PASS_CONDITIONAL   = 1 (Q5 voucher sub-case, pending R-1A-5)
FAIL               = 0
```

**Qualification (per session-2 reconciliation discipline):** these are contract-capability verdicts — the planned mechanisms, invariants, and adversarial tests exist and map to each question. The ontology is therefore *representable-by-construction* for all fifteen challenges, with one conditional pending an operator decision. This is not a claim that the ontology is implemented, tested, or ratified; bloc exit gates remain blocked on D1–D6 and R-1A-5, and every Q's underlying test (T-series) awaits post-authorization execution.

End of pre-ratification adversarial review.
