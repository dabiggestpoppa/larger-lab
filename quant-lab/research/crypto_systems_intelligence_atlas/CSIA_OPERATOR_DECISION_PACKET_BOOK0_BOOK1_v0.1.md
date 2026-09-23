# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## OPERATOR DECISION PACKET — BOOK 0 + BOOK 1 (D1–D6 + R-1A-5)

**Document ID:** CSIA-OPDEC-001
**Version:** 0.1
**Status:** AWAITING OPERATOR DECISIONS — NO DECISION IS MADE HERE
**Purpose:** Present each reserved operator decision with exact question, options, consequences, reversibility, and a recommended default with rationale. The operator decides; nothing in this packet binds.
**Decision authority:** Operator only (Constitution v0.2 §5.1, §5.4 — itself unratified until D1)
**Planning branch:** `agent/crypto-systems-intelligence-atlas-plan`

---

# PART I — BOOK 0 DECISIONS (D1–D6)

## D1 — Ratify Constitution v0.2

- **Exact question:** Is `CSIA_CONSTITUTION_v0.2.md` ratified as the governing constitutional doctrine of CSIA (with or without per-correction objections to CR-01..CR-07)?
- **Why it exists:** Constitution v0.1 failed constitutional review (7 critical issues). v0.2 resolves them, but per Constitution §0 "silence does not equal ratification" and §5.1 ratification is operator-reserved.
- **Options:**
  1. RATIFY v0.2 as written;
  2. RATIFY with named objections (list which CR corrections are rejected — each becomes a v0.3 item);
  3. RETURN for revision (specify defects).
- **Architectural consequences:**
  - Option 1: all downstream planning binds to v0.2's epistemic hierarchy, claim-state machine, identity doctrine, bitemporal model, Program Ledger concept, and Bloc Ratification Records.
  - Option 2: rejected corrections reopen those specific authority/epistemic seams; affected Books (1, 2, 5, 8) replan around the objection.
  - Option 3: program remains in DRAFT governance state; Book 1 cannot be ratified (its contract anchors to v0.2).
- **Downstream consequences:** every Book 1 bloc exit gate requires a ratified Constitution anchor. No bloc can be sealed under an unratified constitution.
- **Reversibility:** Yes via constitutional amendment (§36) — but ratification-then-amend is costlier than objecting now.
- **Recommended DEFAULT:** **Option 1 — ratify as written.**
- **Why the default matches IACER + Constitution:** Every CR-01..CR-07 correction closes a defect the IACER itself forbids (e.g., R3's "no component silently gains authority" was violated by the planning docs themselves; IACER's "NEXT STAGE" list demands exactly the clauses v0.2 adds). The corrections tighten, never loosen, authority boundaries.
- **Another option requires constitutional amendment?** No — this IS the ratification act. Option 2/3 keep the constitution in draft.
- **Clause/artifact affected:** Entire `CSIA_CONSTITUTION_v0.2.md`; status blocks of every downstream artifact.

## D2 — Accept the claim-state machine (§7.1) as fixed

- **Exact question:** Is the claim state machine (states, legal/illegal transitions, dependent-claim propagation, STALE-as-derived) accepted as fixed doctrine, or proposed for amendment?
- **Why it exists:** Review issue CR-05 — v0.1 listed states with no transition legality, making accidental `INFERRED→OBSERVED` leaks inevitable.
- **Options:** 1. ACCEPT as fixed; 2. AMEND (specify transition changes).
- **Architectural consequences:** Option 1 makes claim states property of claim-evidence pairs with a closed transition set — the epistemic spine for Books 2 (promotion), 6 (state vectors), 8 (bridge). Option 2 changes the promotion spine before any evidence exists — the cheapest possible time to do it, but it must precede Book 2 planning.
- **Downstream consequences:** Book 2 Bloc 2D promotion state machine is derived directly from this; Book 6 state vectors inherit legality.
- **Reversibility:** Amendable later (§36), but transitions become load-bearing in Book 2; later changes require evidence-migration rules.
- **Recommended DEFAULT:** **Option 1 — accept.** The transition set is conservative (every strengthening transition requires strictly stronger evidence; E4 can never strengthen structural claims), matching Axiom 3 and the §6.1 matrix.
- **Another option requires constitutional amendment?** Option 2 is itself a constitutional amendment.
- **Clause/artifact affected:** Constitution §7.1; Book 2 Bloc 2D; Book 6 Bloc 6C.

## D3 — Accept the tier-to-claim-state promotion matrix (§6.1)

- **Exact question:** Is the evidence-tier → claim-state promotion matrix accepted as fixed doctrine?
- **Why it exists:** Review issue MA-01 — v0.1 ranked tiers but never said what tier promotes what claim, leaving promotion per-implementation.
- **Options:** 1. ACCEPT; 2. AMEND (e.g., require two independent E0 sources even for deterministic facts; relax DECLARED to allow E2-only).
- **Architectural consequences:** Option 1 sets the evidence bar for the entire system — most notably "E4-only evidence may never produce OBSERVED or CORROBORATED." Option 2 either raises acquisition cost (more independence) or loosens epistemic security.
- **Downstream consequences:** Book 2 evidence thresholds; Book 3/4 promotion of chain/protocol facts; Book 7 event evidence.
- **Reversibility:** Amendable; matrix is data-like (a table), so amendment is cheap pre-population, expensive post-population.
- **Recommended DEFAULT:** **Option 1 — accept.** The matrix operationalizes IACER §C4's source hierarchy and Axiom 3 exactly; its single-E0 allowance for deterministic facts (e.g., contract deployment) matches how native technical truth works.
- **Another option requires constitutional amendment?** Option 2 is itself a constitutional amendment.
- **Clause/artifact affected:** Constitution §6.1; Book 2 Bloc 2D.

## D4 — Confirm the descriptive/prescriptive boundary (§5.3a)

- **Exact question:** Is the §5.3a boundary wording (no ranking/score/target/timing/advice; prescriptive intent smuggled through naming is a violation) confirmed?
- **Why it exists:** Review issue CR-02 — §5.3 forbade "investment recommendations" without defining them; the most likely accidental violation in the whole program.
- **Options:** 1. CONFIRM wording; 2. TIGHTEN (add more forbidden constructs); 3. LOOSEN (specify which descriptive outputs are permitted that v0.2 forbids — not recommended).
- **Architectural consequences:** This clause shapes every operator surface (Book 9), every state vector name (Book 6), and every Context Bridge label (Book 8). Confirming now prevents prescriptive vocabulary from crystallizing anywhere.
- **Downstream consequences:** naming conventions for CONFIRMED_* states; panel copy; export formats.
- **Reversibility:** Amendable; but vocabulary crystallizes early in surfaces, so earliest confirmation is cheapest.
- **Recommended DEFAULT:** **Option 1 — confirm.** The wording implements IACER R4 ("not a token recommender / not an automated investment ranking") and Axiom 8 with testable examples.
- **Another option requires constitutional amendment?** Options 2/3 are themselves amendments.
- **Clause/artifact affected:** Constitution §5.3a; Book 6 §23.1 naming; Book 8/9 surfaces.

## D5 — Confirm anti-drift cadence (per-book + per-phase audits)

- **Exact question:** Is the anti-drift audit cadence confirmed — the 13 standing questions answered in a recorded audit entry at every book ratification and program-phase boundary?
- **Why it exists:** Constitution §37 lists drift questions but specifies no enforcement cadence; unowned doctrine decays.
- **Options:** 1. CONFIRM cadence as proposed; 2. LIGHTER (phase boundaries only); 3. HEAVIER (per-bloc).
- **Architectural consequences:** Option 1 places 1 audit per book (~10 total) plus phase boundaries. Option 3 would add ~20 more audits for marginal benefit. Option 2 risks a whole book drifting between audits.
- **Downstream consequences:** operator time budget; Book 9 Bloc 9E owns audit tooling.
- **Reversibility:** Fully reversible (cadence is procedural).
- **Recommended DEFAULT:** **Option 1 — confirm.** Book boundaries are where drift actually compounds (a book's outputs become the next book's inputs); phase boundaries alone would let intra-book drift run for months.
- **Another option requires constitutional amendment?** No — cadence is procedural policy, not constitutional text (though §37 anchors it).
- **Clause/artifact affected:** Constitution §37; Book 0 Bloc 0C.4; Book 9E.

## D6 — Confirm Program Ledger as sole next-step authority (§G)

- **Exact question:** Is `CSIA_PLANNING_PROGRESS.md` confirmed, upon this ratification, as the sole authoritative record of the current authorized next step — with all "NEXT" pointers in other documents demoted to non-authoritative?
- **Why it exists:** Review issue CR-01 — Constitution §39 and Roadmap CURRENT STATE disagreed on the next step, with no resolution rule.
- **Options:** 1. CONFIRM ledger as sole authority (takes effect at D1 ratification); 2. REJECT (each document keeps its own NEXT, conflicts resolved ad hoc — recreates CR-01); 3. CONFIRM with a different ledger location/name.
- **Architectural consequences:** Option 1 creates a single governance chokepoint: any agent or future session reads one file to know what is authorized. This is the anti-drift mechanism for program-level state.
- **Downstream consequences:** every future planning session must update the ledger to change authorization; the Operator Decision Log references it.
- **Reversibility:** Amendable (§36); ledger location can move with a recorded decision.
- **Recommended DEFAULT:** **Option 1 — confirm.** This directly implements CR-01's correction; the bootstrap problem (ledger claiming authority from an unratified constitution) is resolved exactly by this decision sequence — the ledger is PROPOSED authority until this D6 is recorded.
- **Another option requires constitutional amendment?** Option 2/3 amend §G.
- **Clause/artifact affected:** Constitution §G; `CSIA_PLANNING_PROGRESS.md` header.

---

# PART II — BOOK 1 DECISION

## R-1A-5 — IBC voucher representation (from stress matrix E-13)

**Origin:** Cross-cutting USDC anchor, Cosmos row: an IBC voucher (e.g., `ibc/…` denom for USDC on Osmosis) is neither a custodial wrap (`WRAPS`) nor a canonical deployment (`ISSUED_ON` status CANONICAL). It is a channel-bound, non-custodial representation whose existence and denomination depend on an IBC channel.

**The exact question:** How does the Book 1 identity model represent IBC vouchers (and channel-bound representations generally)?

### OPTION A — Deployment-like object per voucher/channel realization
Each voucher realization is its own deployment-like object: `USDC@cosmos-hub:ibc/27394FB…` with status `CHANNEL_REPRESENTATIVE`, carrying channel ID, counterparty chain, and denom trace.

- **Stress results:**
  - *Channel-specific denom traces:* native fit — the denom trace IS the identity marker. Strong.
  - *Same asset over multiple channels:* each channel produces a distinct denom and thus a distinct deployment — representable without collision. Strong.
  - *Channel closure/migration:* deployment gets valid_to; new channel → new deployment; MIGRATED edges. Representable. Strong.
  - *Multi-hop IBC:* multi-hop paths create intermediate denoms on intermediate chains — each hop's denom is a deployment on its chain. Representable, but hop chain becomes explicit. Strong.
  - *Canonical economic identity:* preserved — canonical token object (csia:token:usdc) remains one; deployments multiply. Strong.
  - *Local chain representation:* the voucher is queryable as a first-class local asset (apps reference the denom directly). Strong.
  - *Historical replay:* deployments are bitemporal records — replay clean. Strong.
  - *Capital-flow analysis:* flows reference concrete denoms (what actually moves) — best flow grounding of the three options. Strong.
- **Costs:** object proliferation — a heavily routed asset can have hundreds of channel-denom deployments; dedup/discovery load; risk of "deployment" concept stretching to cover things that are not deployments.

### OPTION B — Canonical asset + WRAPS/REPRESENTS edge with denom-trace/channel/mechanism attributes
One deployment per chain per canonical asset (not per channel); channel-bound nature expressed as edge attributes (`mechanism: IBC`, `denom_trace`, `channel_ids[]`).

- **Stress results:**
  - *Channel-specific denom traces:* the trace must live as an attribute list on a single deployment — a chain can hold **multiple concurrent denoms for the same asset via different channels**; a single attribute value cannot represent that set losslessly. **Weak — information loss or unbounded attribute lists.**
  - *Same asset over multiple channels:* collapses onto one deployment with channel list; channel-level distinctions (fees, state, trust) lost. **Weak.**
  - *Channel closure:* one channel closes while another stays open — the deployment must remain valid while one attribute entry dies. Valid-time semantics become per-attribute, violating the record-level temporal model (Bloc 1D rules apply to records, not attribute entries). **Weak — temporal integrity strain.**
  - *Multi-hop:* intermediate denoms are distinct assets locally; Option B hides them inside attributes. **Weak.**
  - *Canonical identity:* clean. Strong.
  - *Local representation:* local apps see denoms, not the collapsed deployment — query mismatch. **Weak.**
  - *Replay:* attribute-level history is exactly what Bloc 1D's record-level supersession forbids. **Weak.**
  - *Capital flow:* flows by channel are second-class. **Weak.**
- **Costs:** simplicity of object count; but it breaks record-level bitemporality and loses channel-level truth.

### OPTION C — Hybrid: canonical economic identity separate from chain-local realization identity
Two layers: the canonical token object (economic identity, `csia:token:usdc`) is separate from **realization objects** (`csia:realization:usdc@osmosis:ibc/<hash>`) — a new lightweight object class for chain-local representational forms, with typed edges (`REALIZES`) to the canonical asset, carrying channel/mechanism attributes on the realization.

- **Stress results:**
  - *Denom traces:* realization identity = denom. Strong.
  - *Multiple channels:* distinct realizations. Strong.
  - *Closure/migration:* per-realization valid_to. Strong.
  - *Multi-hop:* each hop is a realization, linked REALIZES→canonical, and optionally RECEIVED_VIA→channel. Strong.
  - *Canonical identity:* explicitly preserved and unburdened. Strong.
  - *Local representation:* realizations are first-class local assets. Strong.
  - *Replay:* bitemporal per realization. Strong.
  - *Capital flow:* flows bind to realizations; aggregation to canonical is a derived view (exactly per Constitution §11.1 derived-view doctrine). Strong.
- **Costs:** a new primary concept (`REALIZATION`) — largest ontology change of the three; requires Bloc 1A/1B/1C amendments (new object class + edge type); slightly more complex queries for "all forms of USDC on chain X" (answered by realization objects, though).
- **Key difference vs Option A:** A overloads `DeploymentIdentity` (which so far means *issuance forms*: native, contract, issuer-account, program, canister). C says channel-bound representations are a *different kind of thing* than issuances and deserve their own class, keeping the deployment semantics pure.

### Consequence comparison summary

| Criterion | A (deployment-like) | B (attributes) | C (realization class) |
|---|---|---|---|
| Denom-trace fidelity | Strong | Weak (lossy) | Strong |
| Multi-channel | Strong | Weak | Strong |
| Channel closure temporal integrity | Strong | Weak (attribute-level time) | Strong |
| Multi-hop | Strong | Weak | Strong |
| Canonical economic identity | Strong | Strong | Strong (explicit) |
| Local-chain queryability | Strong | Weak | Strong |
| Historical replay | Strong | Weak | Strong |
| Capital-flow grounding | Strong | Weak | Strong |
| Ontology cost | Medium (stretches "deployment") | Low | High (new class + edge) |
| Bitemporal-model consistency | Strong | **Violates Bloc 1D record-level rules** | Strong |

### Reversibility
- Option B is effectively **irreversible without data loss** once populated (attribute-level history cannot be reconstructed into record-level). Options A and C are interconvertible with a mechanical migration (A's channel deployments ↔ C's realizations share the same identity key), so choosing A now does not preclude C later, and vice versa.

### Recommendation (not a decision)
- **Recommended DEFAULT: Option C (hybrid)** — it is the only option that is strong on every stress criterion, and the "deployment purity" argument matters: Bloc 1A's deployment model is about *how an asset comes to exist on a chain* (native issuance, contract, issuer account, program, canister), while IBC vouchers are *how an existing asset travels*. Conflating them would recreate the junk-drawer problem the relationship ontology guards against (IR-7 analog for identity).
- **Fallback if the operator wants minimal ontology change: Option A** — acceptable, interconvertible with C, and strictly better than B.
- **Option B should be rejected**: it is the only option that structurally violates the bitemporal contract (Bloc 1D R-rules) and loses channel-level truth.
- **If Option C is chosen:** Bloc 1A adds `REALIZATION` object class + `REALIZES` edge + `RECEIVED_VIA` (optional channel edge); Bloc 1B adds the class to the registry (42 classes); Bloc 1C adds edge dictionary entries. No constitutional amendment required — all within §9.3 extension mechanism (registry change, not doctrine change).
- **If Option A is chosen:** Bloc 1A extends the deployment-status enum with `CHANNEL_REPRESENTATIVE` and documents the stretched semantics. No constitutional amendment required.
- **If Option B were chosen:** would require a constitutional amendment to Bloc 1D's record-level temporal rules (or a documented exception) — strongest reason against.

**Clause/artifact affected:** Book 1 Bloc 1A.6 (DeploymentIdentity / new class), Bloc 1B.6 (class registry), Bloc 1C.6 (edge dictionary); stress matrix E-13; no direct Constitution change unless Option B.

---

# OPERATOR DECISION RECORD LINE

When the operator decides, record per Constitution §5.4:

```text
DECISION LOG ENTRY {
  decision_id:    D1 | D2 | D3 | D4 | D5 | D6 | R-1A-5
  question_ref:   this packet, section above
  chosen_option:  <option number/letter>
  conditions:     <any> 
  decided_by:     OPERATOR
  decided_at:     <timestamp>
  binding_effect: <per section above>
}
```

No decision in this packet has been made. All seven remain open.

End of operator decision packet.
