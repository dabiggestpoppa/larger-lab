# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 1 — EXTENSION ADJUDICATION (E-SERIES)

**Document ID:** CSIA-B1-ADJ-001
**Version:** 0.1
**Status:** ADJUDICATION COMPLETE — NOT RATIFIED (fold targets set; operator reviews with bloc plans)
**Input:** `CSIA_BOOK_1_PILOT_ONTOLOGY_STRESS_MATRIX.md` (incl. ERRATA v0.1.1) — 13 identifiers, 9 amendment candidates, 4 confirmations
**Adjudication rule (constitutional):** *minimum sufficient ontology + maximum native-architecture fidelity.* Extension is not adoption; every candidate must earn its way in. Ontology inflation is itself a drift vector (a bloated ontology erodes the legibility requirement of Axiom 10).
**Classification enum:**

```text
REQUIRED_BEFORE_BLOC_FREEZE          — bloc exit gates cannot pass without it
USEFUL_BUT_DEFERABLE                 — real gap, but later book/bloc owns it; reserve a slot only
ALREADY_COVERED_BY_EXISTING_CONTRACT — the v0.1 contract already handles it
REJECT                               — would inflate the ontology without sufficient need
REQUIRES_OPERATOR_DECISION           — multiple defensible designs; reserved to operator
```

**Notation:** "changes Constitution?" refers to `CSIA_CONSTITUTION_v0.2.md`; "changes Book 1 only?" refers to the planning contract, not implementation.

---

# CONFIRMATIONS (E-3, E-4, E-6, E-9 — no amendment exists)

## E-3 — ALREADY_COVERED_BY_EXISTING_CONTRACT
- **Originating pilot:** Bitcoin
- **Claimed gap:** native-marker deployment identity
- **Adjudication:** Book 1 v0.1 Bloc 1A.6 already defines `DeploymentIdentity.address: … | NATIVE_MARKER` and 1A.7 rule 8 handles non-contract assets. The pilot itself concluded "no amendment needed"; the identifier was recorded for traceability.
- **Constitution change:** no. **Book 1 change:** no. **Replay/provenance impact:** none.
- **Adversarial test required:** none beyond existing T-1A-6.
- **Target:** none (verification note in Bloc 1A evidence list).

## E-4 — ALREADY_COVERED_BY_EXISTING_CONTRACT
- **Originating pilot:** Ethereum
- **Claimed gap:** sequencer as distinct infrastructure class
- **Adjudication:** `SEQUENCER_INFRASTRUCTURE` is already in the 41-class registry (v0.1 Bloc 1B.6, added from review SG-B), and `ADV-1B-E` covers shared sequencers. Ethereum validated rather than extended.
- **Constitution change:** no. **Book 1 change:** no. **Replay/provenance impact:** none.
- **Adversarial test required:** none beyond existing ADV-1B-E / T-1B tests.
- **Target:** none (verification note in Bloc 1B evidence list).

## E-6 — ALREADY_COVERED_BY_EXISTING_CONTRACT
- **Originating pilot:** XRP Ledger
- **Claimed gap:** trustline/issued-asset family slot
- **Adjudication:** Bloc 1B.6 architecture-extension-slot registry explicitly lists "XRPL trustlines/UNL," and Constitution §16.2 names trustlines as a native-section example. The pilot's own conclusion was "no amendment if slots exist" — they exist. Confirmation recorded.
- **Constitution change:** no. **Book 1 change:** no. **Replay/provenance impact:** none.
- **Adversarial test required:** ADV-1B-B (native DEX without EVM semantics) already exercises the family-slot path; add one trustline-issuance case to Bloc 1A adversarial set as T-1A-11 (see v0.2 changelog).
- **Target:** Bloc 1A adversarial cases (minor addition, in v0.2).

## E-9 — ALREADY_COVERED_BY_EXISTING_CONTRACT
- **Originating pilot:** Cosmos
- **Claimed gap:** ICS shared security via HE-SECURITY-SHARE
- **Adjudication:** `HE-SECURITY-SHARE` with PROVIDER_CHAIN / CONSUMER_CHAIN(s) / MECHANISM roles is already in the v0.1 Bloc 1C.6 hyperedge registry. Confirmation recorded.
- **Constitution change:** no. **Book 1 change:** no. **Replay/provenance impact:** none.
- **Adversarial test required:** none beyond existing hyperedge tests (T-1C-6).
- **Target:** none (verification note in Bloc 1C evidence list).

---

# AMENDMENT CANDIDATES (E-1, E-2, E-5, E-7, E-8, E-10, E-11, E-12, E-13)

## E-1 — REQUIRED_BEFORE_BLOC_FREEZE
- **Originating pilot:** Bitcoin (exercised hard by XRPL and ICP rows)
- **Ontology gap exposed:** `SECURED_BY` carries no security-mechanism attribute; PoW (Bitcoin), BFT-UNL (XRPL), threshold-BFT (ICP), and PoS (Cosmos/Solana) would be indistinguishable at the edge level — a direct Axiom 1 violation risk (mechanism flattening).
- **Proposed amendment:** add mandatory `mechanism` attribute to the SECURED_BY/SECURES edge dictionary entries: enum `POW | POS | DPOS | BFT_FAMILY | THRESHOLD_BFT | HYBRID | FEDERATED | OTHER(defining string)`; family-specific values refine in Book 3B.
- **Generic or architecture-specific:** **generic** (every chain has a security mechanism; the enum is family-neutral with extension points).
- **Changes Constitution?** No — §10.1 already requires domain/range and semantics; this is a dictionary-entry attribute. **Changes Book 1 only?** Yes (Bloc 1C edge dictionary).
- **Historical replay impact:** mechanism can change over time (PoW→PoS transitions); attribute is temporal like any edge attribute — replay-safe under Bloc 1D rules.
- **Provenance impact:** none beyond existing edge provenance.
- **Adversarial test required:** T-1C-11 (new): mechanism attribute mandatory on SECURED_BY; Bitcoin≠Cosmos mechanism values; mechanism change over valid-time representable.
- **Target bloc/chapter:** Bloc 1C, Chapter 1C.2 (settlement/security edges).

## E-2 — USEFUL_BUT_DEFERABLE (with slot reservation)
- **Originating pilot:** Bitcoin
- **Ontology gap exposed:** role-tag registry has rollup/sidechain/appchain/DAG tags but no `STATE_CHANNEL` tag; Lightning-family L2s would be forced into `SIDECHAIN` (false) or left untagged.
- **Proposed amendment:** add architecture role tag `STATE_CHANNEL` to the Bloc 1B role-tag registry.
- **Generic or architecture-specific:** generic tag, currently one known family.
- **Changes Constitution?** No (§9.3 extension mechanism; registry addition). **Changes Book 1 only?** Yes (Bloc 1B registry).
- **Historical replay impact:** none (tag addition is additive).
- **Provenance impact:** none.
- **Adversarial test required:** T-1B-7 (new): a state-channel L2 (Lightning) carries `STATE_CHANNEL` + `PAYMENT_RAIL` roles without requiring `USES_VM`.
- **Why not REQUIRED:** no bloc exit gate fails without it today (Lightning appears in Books 3/5 content); but the tag costs one registry line, and deferring invites an ad-hoc tag later. **Adjudication: adopt now as a slot reservation — cost ≈ 0, but classified deferable-adopted.**
- **Target bloc/chapter:** Bloc 1B, Chapter 1B.6 (role-tag registry).

## E-5 — REQUIRED_BEFORE_BLOC_FREEZE
- **Originating pilot:** XRP Ledger (co-exercised by Solana, ICP)
- **Ontology gap exposed:** `DeploymentIdentity.address` admits only contract addresses and `NATIVE_MARKER`; XRPL issued assets anchor to *issuer accounts*, Solana to *programs/mints*, ICP to *canisters*. This is the single most consequential identity gap — without it, three of seven pilot architectures misidentify their native asset forms.
- **Proposed amendment:** extend the address field to a typed marker enum:
  ```text
  marker: CONTRACT(addr) | NATIVE | ISSUER_ACCOUNT(addr) | PROGRAM(program_id)
        | MINT_ACCOUNT(mint) | CANISTER(canister_id) | PACKAGE(pkg_id)
        | OTHER(family, defining string)     // Book 3B families extend
  ```
- **Generic or architecture-specific:** generic mechanism, family-populated values.
- **Changes Constitution?** No — Constitution §8.4 says deployments carry "address-or-native-marker" generically; the enum instantiates it. **Changes Book 1 only?** Yes (Bloc 1A schema).
- **Historical replay impact:** markers are immutable identity components; replay-safe. Marker *type* misassignment is a reclassification event (operator-reviewed) if discovered late.
- **Provenance impact:** none beyond deployment provenance.
- **Adversarial test required:** T-1A-12 (new): each marker type round-trips; a non-EVM chain (XRPL) issues assets with ISSUER_ACCOUNT markers and identity survives all Bloc 1A invariants.
- **Target bloc/chapter:** Bloc 1A, Chapter 1A.6 (deployment identity schema).

## E-7 — ALREADY_COVERED_BY_EXISTING_CONTRACT (with clarification)
- **Originating pilot:** Solana
- **Claimed gap:** `MEV_INFRASTRUCTURE` role tag needs family parameterization (Ethereum builder/relay vs Solana block-engine).
- **Adjudication:** the tag already exists (v0.1 Bloc 1B.6); the *parameterization* concern is satisfied by the primary/role model itself — family variation belongs in family slots (Bloc 1B.6 extension slots, which already list "Solana stake/fee markets") and Book 3B family models, not in the tag. Adding a family parameter to a role tag would duplicate the family-slot mechanism — ontology inflation. **Classification: ALREADY_COVERED**, with a definitional clarification added to the tag's definition string in v0.2 ("family-specific manifestations live in family slots, not tag parameters").
- **Constitution change:** no. **Book 1 change:** one definition-string clarification (v0.2).
- **Historical replay impact:** none. **Provenance impact:** none.
- **Adversarial test required:** covered by T-1B-6 (anti-EVM-bias).
- **Target:** Bloc 1B role-tag registry definition (clarification only).

## E-8 — REQUIRED_BEFORE_BLOC_FREEZE
- **Originating pilot:** Cosmos (generalized by ICP row E-11)
- **Ontology gap exposed:** `HE-BRIDGE-ROUTE` carries no channel/route attributes; IBC channels (channel id, state, version) and ICP chain-key routes (threshold mechanism) are the actual trust-carrying facts — a hyperedge without them under-delivers the very context pairwise flattening destroys (Constitution §11.1's whole point).
- **Proposed amendment:** hyperedge registry gains a generic `route_attributes` group: `{channel_id | route_spec, state, version, mechanism}` — typed per mechanism family (IBC channels, chain-key, lock-and-mint, light-client). The attribute *registry* is reserved in Book 1; *population* is Book 3B/4B.
- **Generic or architecture-specific:** generic group with family-typed values.
- **Changes Constitution?** No (§11.1 declares roles; attribute groups are dictionary detail). **Changes Book 1 only?** Yes (Bloc 1C hyperedge registry).
- **Historical replay impact:** channel state changes over time (open/closed) — attributes are temporal per record; replay-safe and *required* for replay fidelity (channel closure is a world-change event).
- **Provenance impact:** channel state evidence (E0/E1) attaches via claim_binding per existing rules.
- **Adversarial test required:** T-1C-12 (new): same asset over two channels = two hyperedges with distinct attributes; channel closure sets valid_to without touching other channels.
- **Target bloc/chapter:** Bloc 1C, Chapter 1C.7 (hyperedge rules).

## E-10 — REQUIRED_BEFORE_BLOC_FREEZE
- **Originating pilot:** ICP
- **Ontology gap exposed:** `RUNS_ON` range is `BLOCKCHAIN|LEDGER` only; ICP applications run on *subnets* (internally partitioned replication), and DAG shards/partitions generally need chain-scoped sub-objects. Without this, ICP's actual security topology (application availability = subnet health) is unrepresentable — the pilot's sharpest finding.
- **Proposed amendment:** add `chain_scope` attribute to RUNS_ON (and optionally VALIDATED_BY): `CHAIN | SUBNET(subnet_ref) | SHARD(shard_ref) | PARTITION(partition_ref)`; sub-objects are family-scoped nodes (BLOCKCHILD scope objects owned by Book 3B family models, referenced by object_id).
- **Generic or architecture-specific:** generic attribute; currently exercised by ICP only — but sharding futures make it generic.
- **Changes Constitution?** No — §10.1 requires domain/range per dictionary entry; this refines the range. **Changes Book 1 only?** Yes (Bloc 1C dictionary).
- **Historical replay impact:** subnets can be added/removed (ICP does this routinely via NNS) — chain_scope is temporal; replay-safe.
- **Provenance impact:** none beyond edge provenance.
- **Adversarial test required:** T-1C-13 (new): ICP application RUNS_ON subnet with subnet-level VALIDATED_BY; subnet removal event sets valid_to.
- **Target bloc/chapter:** Bloc 1C, Chapter 1C.6 (RUNS_ON entry) + Bloc 1B family slots (subnet object note).

## E-11 — ALREADY_COVERED_BY_EXISTING_CONTRACT (post-E-8)
- **Originating pilot:** ICP
- **Claimed gap:** HE-BRIDGE-ROUTE mechanism attribute (chain-key)
- **Adjudication:** E-11 is the generalization of E-8 (the pilot says so itself). Once E-8's `route_attributes.mechanism` exists, E-11 is subsumed — chain-key is a mechanism value, not a separate amendment. **Classification: ALREADY_COVERED_BY_EXISTING_CONTRACT (via E-8's adoption).** Mapping recorded; no independent change.
- **Constitution change:** no. **Book 1 change:** none beyond E-8.
- **Adversarial test required:** covered by E-8's T-1C-12 (include a chain-key route case).
- **Target:** Bloc 1C (via E-8).

## E-12 — USEFUL_BUT_DEFERABLE (slot reservation, with an information-gap flag)
- **Originating pilot:** DAG network
- **Ontology gap exposed:** no finality-device attribute registry exists; temporal doctrine's finality-anchoring (ADV-1D-J) needs family finality devices to anchor to.
- **Proposed amendment:** reserve a `finality_device` family-attribute slot in Bloc 1B's extension-slot registry (values LINEAR_DETERMINISTIC | PROBABILISTIC | DECLARATIVE_DAG | BFT_INSTANT | OPTIMISTIC | ZK_ROLLUP | OTHER(defining)); **registry and semantics reserved in Book 1, value-population in Book 3B** (the pilot's own scoping).
- **Generic or architecture-specific:** generic slot, family-populated.
- **Changes Constitution?** No. **Changes Book 1 only?** Yes (slot reservation in 1B.6).
- **Historical replay impact:** finality devices can change (upgrades); temporal attribute — replay-safe. ADV-1D-J explicitly requires this for finality-class claims.
- **Provenance impact:** none.
- **Adversarial test required:** T-1D-11 (new): DAG-network fact valid-time anchored to its declared finality device, not block appearance (extends ADV-1D-J).
- **Why not REQUIRED:** no exit gate fails without the slot today; but ADV-1D-J already references finality anchoring, so the *slot reservation* is the minimum honest contract. Population deferred by design (recorded INFORMATION GAP in stress-matrix errata).
- **Target bloc/chapter:** Bloc 1B extension-slot registry + Bloc 1D ADV-1D-J note.

## E-13 — REQUIRES_OPERATOR_DECISION (= R-1A-5)
- **Originating pilot:** Cosmos (USDC cross-cutting anchor)
- **Ontology gap exposed (dual-natured):** IBC vouchers fit neither `ISSUED_ON` canonical deployments nor `WRAPS` custodial representations. This is simultaneously (a) an **extension need** and (b) a genuine **contract defect** in v0.1: the `DeploymentIdentity.status` enum (`CANONICAL | BRIDGED_REPRESENTATIVE | WRAPPED | DEPRECATED`) has no class for channel-bound non-custodial representations, and no other object concept covers them either.
- **Proposed amendment:** **dependent on operator choice:**
  - *Option C (recommended in decision packet):* new `REALIZATION` object class + `REALIZES` edge (+ optional `RECEIVED_VIA` channel edge); registry 41→42 classes.
  - *Option A (acceptable fallback):* deployment-status enum + `CHANNEL_REPRESENTATIVE`; deployment semantics documented as stretched.
  - *Option B:* **REJECT-classified** — structurally violates Bloc 1D record-level temporal rules (channel closure would require attribute-level time) and loses multi-channel truth; adopting it would require a constitutional amendment to §12/Bloc 1D. Recorded here so the rejection rationale survives.
- **Generic or architecture-specific:** generic (any non-custodial channel-bound representation: IBC today, potential future layerZero-style omnichain denoms).
- **Changes Constitution?** No for A/C (§9.3 extension mechanism). Yes (de facto) for B.
- **Changes Book 1 only?** Yes — Blocs 1A/1B/1C per chosen option.
- **Historical replay impact:** A and C replay-safe (record-level); B not.
- **Provenance impact:** realizations/deployments carry claim_bindings per existing rules.
- **Adversarial test required:** T-1A-13 (new, post-decision): USDC across IBC channels — multiple channel-bound forms coexist; channel closure ends one without touching others; multi-hop intermediate forms representable; aggregation to canonical asset is a derived view only.
- **Target bloc/chapter:** Bloc 1A (schema), Bloc 1B (registry), Bloc 1C (edges) — **PENDING_OPERATOR_DECISION R-1A-5; do not freeze Bloc 1A until decided.**

---

# ADJUDICATION SUMMARY

| ID | Classification | Constitution change? | Book 1 change? | Target |
|---|---|---|---|---|
| E-1 | REQUIRED_BEFORE_BLOC_FREEZE | No | Yes | 1C.2 security edges |
| E-2 | USEFUL_BUT_DEFERABLE (adopted as slot reservation) | No | Yes | 1B.6 role tags |
| E-3 | ALREADY_COVERED_BY_EXISTING_CONTRACT | No | No | — |
| E-4 | ALREADY_COVERED_BY_EXISTING_CONTRACT | No | No | — |
| E-5 | REQUIRED_BEFORE_BLOC_FREEZE | No | Yes | 1A.6 deployment schema |
| E-6 | ALREADY_COVERED_BY_EXISTING_CONTRACT | No | Minor (test add) | 1A adversarial set |
| E-7 | ALREADY_COVERED_BY_EXISTING_CONTRACT | No | Clarification | 1B.6 definition |
| E-8 | REQUIRED_BEFORE_BLOC_FREEZE | No | Yes | 1C.7 hyperedges |
| E-9 | ALREADY_COVERED_BY_EXISTING_CONTRACT | No | No | — |
| E-10 | REQUIRED_BEFORE_BLOC_FREEZE | No | Yes | 1C.6 RUNS_ON |
| E-11 | ALREADY_COVERED_BY_EXISTING_CONTRACT (via E-8) | No | No (subsumed) | — |
| E-12 | USEFUL_BUT_DEFERABLE (slot reserved; population → Book 3B) | No | Yes | 1B.6 slots + 1D note |
| E-13 | REQUIRES_OPERATOR_DECISION (R-1A-5) | No (A/C) / de-facto yes (B) | Yes (pending) | 1A/1B/1C |

```text
REQUIRED_BEFORE_BLOC_FREEZE          = 4   (E-1, E-5, E-8, E-10)
USEFUL_BUT_DEFERABLE                 = 2   (E-2, E-12 — both adopted as slot
                                            reservations; cost ≈ 0)
ALREADY_COVERED_BY_EXISTING_CONTRACT = 5   (E-3, E-4, E-6, E-7, E-9, plus E-11
                                            subsumed — 6 identifiers, 5 substantive)
REJECT                               = 0 standalone (E-13 Option B rejected
                                            within R-1A-5 analysis)
REQUIRES_OPERATOR_DECISION           = 1   (E-13 / R-1A-5)
```

**Anti-inflation statement:** 6 of 13 identifiers required no ontology change at all; of the 9 real candidates, 2 were downgraded to zero-cost slot reservations and 1 deferred to operator choice. Only 4 amendments are genuinely blocking — all attribute/enum refinements within existing classes and edges, none adding standalone classes except the pending R-1A-5 Option C. Minimum sufficient ontology is preserved.

**Rule for bloc freezes:** Bloc 1A cannot freeze before R-1A-5 (E-13) is decided. Blocs 1B and 1C can freeze with E-1/E-8/E-10/E-2/E-12 folded; 1C freeze additionally absorbs R-1A-5's edge consequences once decided.

End of extension adjudication.
