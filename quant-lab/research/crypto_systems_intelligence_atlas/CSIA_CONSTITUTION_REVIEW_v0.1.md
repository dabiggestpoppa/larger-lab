# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## Constitutional Review v0.1

**Document ID:** CSIA-REVIEW-001
**Version:** 0.1
**Status:** REVIEW COMPLETE — AWAITING OPERATOR ADJUDICATION
**Reviewed artifacts:**
- `CRYPTO_SYSTEMS_INTELLIGENCE_ATLAS_IACER_PLAN.md`
- `CSIA_CONSTITUTION_v0.1.md`
- `CSIA_MASTER_BOOK_BLOC_CHAPTER_ROADMAP_v0.1.md`
**Companion outputs:** `CSIA_CONSTITUTION_v0.2.md` (revised draft, NOT ratified)
**Date:** 2026-09-23
**Rule honored:** Nothing in v0.1 was silently rewritten. Every change below is traceable to an issue ID.

---

## 0. How to read this review

Each issue carries:

- **Issue ID** — stable identifier, referenced by the v0.2 revision notes.
- **Clause** — the document and section affected.
- **Severity** — `CRITICAL` (blocks ratification / guarantees drift), `MAJOR` (causes ambiguity that will later become drift), `MINOR` (quality/completeness gap).
- **Problem** — what is wrong or missing.
- **Why it matters** — the concrete failure mode if left unfixed.
- **Proposed correction** — the exact change adopted in v0.2.
- **Constitutional impact** — which clauses/articles change, and whether amendment-class or editorial.

Severity totals: **7 CRITICAL / 13 MAJOR / 10 MINOR = 30 issues.**

---

# PART I — CONTRADICTIONS AND AUTHORITY GAPS

## Issue CR-01
- **Clause:** Constitution §39 vs Roadmap "FIRST IMPLEMENTATION ARC"; Roadmap CURRENT STATE
- **Severity:** CRITICAL
- **Problem:** Constitution §39 sets `NEXT = REVIEW CONSTITUTION + MASTER ROADMAP` and declares `BOOK_PLANNING_AUTHORITY = TRUE`, but the Roadmap's own CURRENT STATE says `NEXT = OPERATOR CONSTITUTION REVIEW / THEN = BOOK 0 RATIFICATION + DETAILED BOOK 1 PLAN`. Two documents each claim to define the next authorized step, and they disagree on whether Book 0 planning precedes or follows constitution review. Neither document defines who resolves the disagreement.
- **Why it matters:** The exact failure the constitution exists to prevent — ambiguity about what is authorized — exists inside its own artifacts. Later agents will pick whichever "NEXT" they find first. This is canonical drift at the governance layer, before a single node exists.
- **Proposed correction:** v0.2 defines a single **Program Ledger** concept (the progress document, `CSIA_PLANNING_PROGRESS.md`) as the *only* place where the current authorized next step is recorded. "NEXT" statements inside other documents are declared non-authoritative pointers.
- **Constitutional impact:** New clause (Governance §G). Editorial in v0.1 terms; structural in effect.

## Issue CR-02
- **Clause:** Constitution §5.3 (Explicitly absent authority) vs §5.2 (Research authority)
- **Severity:** CRITICAL
- **Problem:** §5.3 forbids "publish investment recommendations" but nowhere defines what an *investment recommendation* is, versus a research summary, a state vector, a confirmation state, or a Context Bridge output. §5.2 permits "generate hypotheses" and "produce research summaries." The boundary is asserted, not defined.
- **Why it matters:** Every Book 6/8/9 output (fundamental states, confirmation states, investor panel) will sit adjacent to this line. Without a definition, the first surface that reads like advice triggers either silent violation or paralyzed over-conservatism. This is the most likely clause in the entire constitution to be violated accidentally.
- **Proposed correction:** v0.2 adds a **Descriptive/Prescriptive boundary definition**: outputs may describe evidence, states, and relationships (descriptive); outputs may not rank, score, recommend, target, or advise (prescriptive). Includes concrete examples of forbidden phrasings and permitted phrasings.
- **Constitutional impact:** Amendment-class addition to §5.

## Issue CR-03
- **Clause:** Constitution §34 (Planning and implementation gates)
- **Severity:** CRITICAL
- **Problem:** The gate sequence ends at "IMPLEMENTATION → VERIFICATION → RATIFICATION" but never states **who ratifies an implemented bloc and against what evidence**. "OPERATOR AUTHORIZATION" appears once, before implementation, and then vanishes. There is no defined artifact for bloc exit evidence, no ratification record, and no rule for what happens when an exit gate is judged failed.
- **Why it matters:** Blocs will complete ("files exist" — explicitly warned against in §33) with no formal mechanism to stop them from being treated as canonical. The constitution's §33 warning is aspirational because no enforcement artifact exists.
- **Proposed correction:** v0.2 adds a **Bloc Ratification Record** doctrine: every bloc exit requires (a) named exit-gate evidence, (b) operator review decision (`RATIFIED / RETURNED / BLOCKED`), (c) a signed record entry. Unratified bloc output is non-canonical by construction, not by warning.
- **Constitutional impact:** Amendment-class addition to §34 and §35.

## Issue CR-04
- **Clause:** Constitution §4.3 (Capital Field) vs IACER §C2 / §R3
- **Severity:** CRITICAL
- **Problem:** The IACER says Capital Field is a *queued, separately planned* program whose pieces (DEX/CEX mechanics, onchain flow, bridges, lending) overlap CSIA's Book 5 scope. The Constitution §4.3 declares Capital Field "a future major subsystem / lens **inside** CSIA." These two statements have different consequences: if Capital Field is a separate program, CSIA Book 5 must not duplicate it; if it is a subsystem, Book 5 *is* it. Neither document resolves the scheduling conflict, and both declare the other non-authoritative in overlapping domains.
- **Why it matters:** "No component silently gains authority over another" (IACER R3) is currently violated by the planning documents themselves. Book 5 and a future Capital Field program will collide — duplicated evidence pipelines, conflicting capital-routing semantics, or a hostile absorption of one by the other.
- **Proposed correction:** v0.2 defines Capital Field as **CSIA-internal in mission, but subject to a separate reconciliation gate**: Book 5 planning must begin with an operator decision on whether existing Capital Field planning artifacts are absorbed, referenced, or superseded. No Book 5 population before that gate.
- **Constitutional impact:** Amendment to §4.3.

## Issue CR-05
- **Clause:** Constitution §7 (Claim states) — missing state transition rules
- **Severity:** CRITICAL
- **Problem:** Nine claim states are enumerated (`OBSERVED, DECLARED, INFERRED, CORROBORATED, CONTESTED, UNRESOLVED, STALE, REJECTED, SUPERSEDED`) with three prose rules, but there is **no legal state machine**: which transitions are allowed, what evidence moves a claim between states, whether states are per-claim or per-edge, and what happens to dependent claims when a claim is REJECTED or SUPERSEDED.
- **Why it matters:** Claim states are the epistemic load-bearing wall of the entire system. Without transition legality, every downstream consumer (Book 2 promotion, Book 6 states, Book 8 bridge) will implement its own ad-hoc transitions, and `INFERRED` will silently leak into `OBSERVED` — the exact failure §7 forbids.
- **Proposed correction:** v0.2 defines the claim state machine: legal transitions, evidence requirements per transition, propagation rules for dependent claims, and the rule that state is a property of the *claim-evidence pair*, not the node.
- **Constitutional impact:** Amendment-class expansion of §7.

## Issue CR-06
- **Clause:** Constitution §8 (Identity doctrine)
- **Severity:** CRITICAL
- **Problem:** §8 requires canonical identity independent of ticker but does not define: the ID namespace scheme, who mints IDs, whether IDs are mutable on rebrand, how contract addresses across many chains are represented (per-chain? per-deployment?), how a multi-chain token maps to many contract identities, or what happens when two canonical IDs must merge (discovered duplicate) or split (discovered conflation). "A rebrand must preserve historical identity" is stated, but the mechanism — identity permanence — is undefined.
- **Why it matters:** Book 1 Bloc 1A is entirely dependent on this doctrine, and the doctrine is one paragraph. Identity is the one layer that is nearly impossible to repair later: retrofitting ID scheme changes after hundreds of nodes exist is a full-graph migration.
- **Proposed correction:** v0.2 expands identity doctrine to cover: namespaced ID scheme (`csia:<type>:<slug>`), minting rules, identity permanence (IDs never change meaning), merge/split operations as explicit versioned events, and deployment-scoped contract identity.
- **Constitutional impact:** Amendment-class expansion of §8.

## Issue CR-07
- **Clause:** Constitution §11 (Hypergraph doctrine) vs §10 (Relationship ontology)
- **Severity:** CRITICAL
- **Problem:** §11 permits hyperedges but gives no rules for: when a hyperedge is *required* vs optional, whether hyperedges participate in the same temporal/provenance doctrine as pairwise edges, whether Book 1's "relationship ontology" governs hyperedge types, or how a consumer (downstream books, the Context Bridge) is supposed to traverse them. The sole example is one USDC sentence.
- **Why it matters:** Hyperedges are the mechanism that prevents flattening multi-party facts — one of the constitution's own stated purposes. Without rules, implementers will default to pairwise flattening because it is easier, and the constitution will have permitted its own erosion.
- **Proposed correction:** v0.2 adds hyperedge typing (hyperedges have declared roles per participant), subject hyperedges to identical temporal/provenance doctrine, requires Book 1 Bloc 1C to enumerate initial hyperedge classes, and defines the rule "multi-party facts must not be losslessly decomposable into pairs" as the trigger for hyperedge use.
- **Constitutional impact:** Amendment-class expansion of §11.

---

## Issue MA-01
- **Clause:** Constitution §6 (Epistemic hierarchy) vs §13 (Provenance doctrine)
- **Severity:** MAJOR
- **Problem:** §6 ranks evidence tiers E0–E4; §13 requires provenance on every promoted fact. Neither says **what tier is required for which promotion**: can an E4 narrative source alone ever promote a relationship to `DECLARED`? Can E3 corroborate an E0? Is one E0 source sufficient, or are two independent sources required for `OBSERVED`?
- **Why it matters:** The source hierarchy is currently a sorting rule, not a promotion rule. Book 2 (evidence promotion) cannot be planned without it, and without it the hierarchy will be reinterpreted per-implementation.
- **Proposed correction:** v0.2 adds a **tier-to-claim-state matrix**: minimum tier and independence requirements for `OBSERVED`, `DECLARED`, `CORROBORATED`, and `INFERRED`.
- **Constitutional impact:** Amendment expansion of §6.

## Issue MA-02
- **Clause:** Constitution §12 (Temporal doctrine)
- **Severity:** MAJOR
- **Problem:** Six timestamps are required but undefined in semantics: Does `valid_from` mean "true in the world from" or "we first believed from"? What is the rule when `source_published_at` and `observed_at` diverge widely (late-discovered historical facts)? Is `superseded_at` a claim-level or edge-level event? What distinguishes `valid_to` (fact ended) from `superseded_at` (replaced by better evidence)? How are timezone/precision differences across chains handled?
- **Why it matters:** Temporal semantics chosen implicitly in Book 1 propagate to historical replay (Book 7), time alignment (Book 8), and every "what changed" answer. Getting bitemporal semantics wrong at this layer invalidates all downstream history.
- **Proposed correction:** v0.2 defines a **bitemporal model explicitly**: valid time (world truth) vs transaction time (system knowledge) as separate axes; each of the six timestamps assigned to a precise axis and definition; late-discovery rule (a fact may have valid_from in the past with observed_at now, without rewriting history).
- **Constitutional impact:** Amendment-class expansion of §12.

## Issue MA-03
- **Clause:** Constitution §9 (Core ontology) vs IACER §A2
- **Severity:** MAJOR
- **Problem:** The IACER's object-type list (38 types incl. L2, L3, SIDECHAIN, DATA_AVAILABILITY_NETWORK, MESSAGING_LAYER, INTEROPERABILITY_PROTOCOL, INDEXER, MARKET_INFRASTRUCTURE) and the Constitution §9 node list (35 types, different set — no L2/L3, but WALLET, VM, STANDARD, SOURCE, METRIC) disagree. The IACER list mixes *architecture* classes (ROLLUP, L2) with *function* classes (DEX, ORACLE); §9 partially resolves this but inconsistently (e.g., ROLLUP remains, while L2 disappears; WALLET appears as a node class but is arguably an ENTITY role).
- **Why it matters:** The two documents were supposed to be nested (roadmap depends on constitution). Two different initial ontologies means Book 1 Bloc 1B has no constitutional anchor. Also, single-inheritance classification ("is a ROLLUP") vs multi-role tagging (§A5 "role is multi-dimensional") are both implied but never reconciled.
- **Proposed correction:** v0.2 defines the node class model: a **primary class** (what the object structurally is) plus **role tags** (what it functionally does), reconciles the IACER and §9 lists into one canonical initial set, and delegates the full enumeration to Book 1 Bloc 1B under constitutional extension rules.
- **Constitutional impact:** Amendment-class rewrite of §9.

## Issue MA-04
- **Clause:** Constitution §10 (Relationship ontology)
- **Severity:** MAJOR
- **Problem:** 30 edge types are listed with zero definitions. Several are ambiguous or overlapping: `DEPENDS_ON` vs `INTEGRATES_WITH` vs `BUILT_WITH` vs `USES_STANDARD`; `SECURED_BY` vs `SECURES` vs `VALIDATED_BY`; `ISSUED_ON` vs `NATIVE_TO`; `WRAPS` vs `ISSUED_ON`. No directionality conventions, no cardinality rules, no inverse-edge rules, no invalid-relationship rules (§32 mentions "invalid relationships" tests, but nothing defines validity).
- **Why it matters:** Edge semantics are the ontology. Undefined edges will be populated opportunistically ("INTEGRATES_WITH" as a junk drawer — §10 itself warns against this, but provides no alternative mechanism). Post-hoc edge disambiguation is a full re-tagging of the graph.
- **Proposed correction:** v0.2 requires every edge type to carry a definition, direction convention, domain/range constraints, and inverse; delegates the full edge dictionary to Book 1 Bloc 1C; adds constitutional invalid-relationship rules (e.g., TOKEN `-RUNS_ON->` CHAIN is invalid; edges must connect type-compatible classes).
- **Constitutional impact:** Amendment-class expansion of §10.

## Issue MA-05
- **Clause:** Constitution §3 Axiom 3 vs §20/§21 (Narrative doctrine, ladder)
- **Severity:** MAJOR
- **Problem:** Axiom 3 says narrative is "a first-class research object, but not a substitute for structural evidence," and §21 makes the narrative→action ladder "constitutional." But there is no rule for how narrative objects **link** to evidence objects: can a narrative cite an E0 evidence record? Can a structural event be *caused* by a narrative? The ladder distinguishes claim→action, but the constitution never says narrative evidence can *never* be promoted to a structural claim even with corroboration, or whether corroboration upgrades it.
- **Why it matters:** This is the narrative/evidence confusion risk named in the program's own charter. Book 7 planning inherits the ambiguity directly.
- **Proposed correction:** v0.2 adds: narrative objects may reference evidence but a structural claim's promotion tier is determined only by structural evidence classes (E0–E2); narrative corroboration may raise narrative *state*, never claim *state*.
- **Constitutional impact:** Amendment expansion of §20–21.

## Issue MA-06
- **Clause:** Constitution §4.2 (Crypto Sensor boundary) and §24 (Context Bridge)
- **Severity:** MAJOR
- **Problem:** The Sensor boundary is defined by a list of owned domains ("price, funding, OI...") — enumeration-based, not rule-based. New mechanical domains (e.g., a Sensor expansion into perp-greeks or options flow, or CSIA-adjacent stablecoin flow data) have no assignment rule. §24 says the bridge "does not merge raw source authority" but does not say which side owns *shared* objects (e.g., stablecoin supply: capital-plumbing concept in CSIA, market-relevant volume in Sensor).
- **Why it matters:** Boundary disputes surface exactly at the richest seams (stablecoins, bridge flows, perp collateral). Without an assignment rule, authority bleeds precisely where both systems are most active.
- **Proposed correction:** v0.2 adds a **boundary assignment rule**: any domain where both systems need data is owned by one side by explicit assignment; CSIA owns *what a thing is* (structural), Sensor owns *what the market is doing to it* (mechanical); disputed domains default to CSIA research-only until operator assignment.
- **Constitutional impact:** Amendment expansion of §4.2 and §24.

## Issue MA-07
- **Clause:** Constitution §14/§15 (Inclusion/Exclusion) vs §27 (Discovery)
- **Severity:** MAJOR
- **Problem:** §14 says "no single threshold is permanently constitutional" and delegates thresholds to "later versioned research policy" — which is not scheduled in any Book/Bloc. §27 says candidates "do not enter canonical state automatically" but there is no defined candidate-queue contract (states, promotion criteria, rejection criteria, aging). The two doctrines reference a missing document.
- **Why it matters:** Inclusion is the first operator decision that scales: every Book 3+ artifact depends on a defensible inclusion rule. Leaving it undefined invites scope-by-vibes — the top-50-by-marketcap bias the IACER explicitly rejects.
- **Proposed correction:** v0.2 assigns the inclusion-threshold policy a home (Book 3 Bloc 3C for chains; Book 4 census for protocols) and defines the candidate-queue state machine (`DISCOVERED → EVALUATING → ACCEPTED / QUARANTINED / REJECTED`).
- **Constitutional impact:** Amendment expansion of §14/§15/§27.

## Issue MA-08
- **Clause:** Constitution §16 (Chain dossier doctrine)
- **Severity:** MAJOR
- **Problem:** The 30-item dossier list (consensus, fees, staking, RWA, wallets...) is implicitly list-shaped and EVM-lean (e.g., "smart-contract model," "RPC/indexing," "contract deployment" do not exist natively on XRP Ledger or Bitcoin; Bitcoin has mining pools, XRPL has issued-asset trustlines, ICP has canisters/subnets — none of which have dossier slots). "Not every chain must have every category" acknowledges but does not solve: there is no *native slot extension* mechanism.
- **Why it matters:** This is the architecture-family bias the program explicitly forbids (Axiom 1). A list-shaped dossier forces native concepts into EVM-shaped categories or drops them — the exact "everything-is-EVM taxonomy" failure §R4 of the IACER forbids.
- **Proposed correction:** v0.2 converts the dossier from a fixed checklist into **core slots + family extension slots**: Book 3 architecture-family models define native sections per family; the constitution requires only that identity, security, execution, interoperability, capital, and temporal-change sections exist for every chain.
- **Constitutional impact:** Amendment-class rewrite of §16.

## Issue MA-09
- **Clause:** Constitution §19 (Capital-plumbing doctrine)
- **Severity:** MAJOR
- **Problem:** §19 says "possible capital route does not equal realized flow" — good — but provides no representation distinction between *capability* (route exists), *capacity* (liquidity size), and *realized flow* (movement observed). All three will live in Book 5 and the ontology has no node/edge vocabulary to distinguish them.
- **Why it matters:** Conflating capability and flow is the most common fundamental-analysis error; the constitution names the error but does not prevent it structurally.
- **Proposed correction:** v0.2 requires the ontology to distinguish capability edges from flow events (flow = temporally bounded event objects, not edges), and requires Book 5 to honor the distinction.
- **Constitutional impact:** Amendment expansion of §19, with Book 1 Bloc 1C/1D implications.

## Issue MA-10
- **Clause:** Constitution §23 (Fundamental state vectors) vs §25 (Causality)
- **Severity:** MAJOR
- **Problem:** §23 allows `NARRATIVE_CONFIRMATION_STATE` and §24 Context Bridge confirmation combinations. §25 forbids causality language without mechanism. Nothing defines the *language* of confirmation states — whether "confirmed" is a causal assertion, a temporal-adjacency observation, or a descriptive co-occurrence.
- **Why it matters:** "Confirmation" is implicitly causal to any reader. If state vectors use causal-sounding names with correlational semantics, the system will routinely overclaim — violating its own §25 in every output surface.
- **Proposed correction:** v0.2 defines confirmation language: `CONFIRMED_*` states are defined as *evidence-of-response observed*, never as causal claims; causal language reserved to event-study outputs with explicit methodology.
- **Constitutional impact:** Amendment expansion of §23/§24/§25.

## Issue MA-11
- **Clause:** Constitution §33 (Status language) vs §34 (Gates)
- **Severity:** MAJOR
- **Problem:** §33 lists program states including `FROZEN_FOR_REVIEW`, `RATIFIED`, `GATED_COMPLETE` but no rules for transitions between them, no definition of `GATED_COMPLETE` vs `RATIFIED`, and no per-object granularity (do states apply to programs, books, blocs, chapters, or claims?).
- **Why it matters:** Status vocabulary is what operators and future agents read to know what is trustworthy. Ambiguity here degrades every governance interaction.
- **Proposed correction:** v0.2 assigns status scope explicitly (program/book/bloc levels) and defines transition legality, aligned with the CR-03 ratification record.
- **Constitutional impact:** Amendment expansion of §33.

## Issue MA-12
- **Clause:** Constitution §30 (Security) and §31 (Cost)
- **Severity:** MAJOR
- **Problem:** Both doctrines are rules for *implementation*, but no Book/Bloc owns compliance verification for them (Book 2 covers acquisition mechanics but not security/cost compliance gates).
- **Why it matters:** Unowned doctrines decay. First paid API or credential appears inside an unreviewed adapter.
- **Proposed correction:** v0.2 assigns security/cost compliance evidence as required Book 2 exit-gate items.
- **Constitutional impact:** Amendment expansion; no behavior change until Book 2.

## Issue MA-13
- **Clause:** Roadmap BOOK 1 Bloc 1D vs Constitution §12
- **Severity:** MAJOR
- **Problem:** Bloc 1D includes "Historical replay" and "Stale-edge handling" as build chapters, but Book 1 is planned *before* Book 2 (evidence substrate). A replay and staleness contract cannot be finalized without the evidence/timestamps from Book 2. The dependency order diagram shows Book 2 and Book 3 after Book 1, but 1D's exit gate implies temporal machinery that needs evidence-tier inputs.
- **Why it matters:** Either 1D over-builds (duplicating Book 2 scope) or under-builds (replay contract invalidated later). Both are drift.
- **Proposed correction:** v0.2 (roadmap-level note recorded in review): Bloc 1D defines the *temporal schema and semantics* in Book 1; *replay execution machinery* is deferred to Book 7D with 1D exit gate requiring schema + adversarial cases only. Recorded as a roadmap amendment note pending operator ratification.
- **Constitutional impact:** Roadmap scoping clarification; no clause change.

---

## Issue MI-01
- **Clause:** Constitution §2.1 mission list
- **Severity:** MINOR
- **Problem:** Mission enumerates domains but omits: mining/validator economies as first-class systems,MEV/sequencer infrastructure, privacy pools/compliance layer, and **entities** (companies/foundations/DAOs) as mission-level objects despite ENTITY appearing in §9.
- **Why it matters:** Entity-level intelligence (funding rounds, treasury, employment) is investor-critical and currently implicit.
- **Proposed correction:** v0.2 adds entity/operator economy to mission enumeration.
- **Constitutional impact:** Editorial.

## Issue MI-02
- **Clause:** Constitution §6 Tier E2
- **Severity:** MINOR
- **Problem:** "High-quality technical analysis" listed under independent evidence — ambiguous term, reads like TA charts.
- **Why it matters:** Minor vocabulary risk.
- **Proposed correction:** Reworded to "independent technical security analysis."
- **Constitutional impact:** Editorial.

## Issue MI-03
- **Clause:** Constitution §7
- **Severity:** MINOR
- **Problem:** No `DISPUTED` vs `CONTESTED` distinction needed — but `STALE` is a claim state while staleness is also a graph-edge property (Bloc 1D.5). Double life will confuse.
- **Proposed correction:** v0.2: `STALE` defined as derived state (computed from temporal policy), not an asserted claim state.
- **Constitutional impact:** Editorial but load-bearing for 1D.

## Issue MI-04
- **Clause:** Constitution §9
- **Severity:** MINOR
- **Problem:** `SOURCE` and `METRIC` as node classes mix research-process objects into the domain ontology.
- **Proposed correction:** v0.2 moves SOURCE to the evidence layer (Book 2 concern), keeps METRIC as a Book 6 concern; the Book 1 domain ontology excludes both.
- **Constitutional impact:** Amendment to §9 (scope cleanup).

## Issue MI-05
- **Clause:** Constitution §17
- **Severity:** MINOR
- **Problem:** Protocol dossier lacks failure-mode taxonomy (technical risk vs economic risk vs governance risk).
- **Proposed correction:** v0.2 adds risk-classification requirement.
- **Constitutional impact:** Editorial.

## Issue MI-06
- **Clause:** Constitution §26
- **Severity:** MINOR
- **Problem:** "Confidence bands" permitted but no requirement they carry methodology references.
- **Proposed correction:** v0.2 requires every confidence representation to carry an inspectable methodology ID.
- **Constitutional impact:** Editorial.

## Issue MI-07
- **Clause:** Constitution §28
- **Severity:** MINOR
- **Problem:** Change-detection list omits: entity changes (acquisitions covered, but leadership/team, legal entity changes not), and token supply-schedule changes.
- **Proposed correction:** v0.2 adds both.
- **Constitutional impact:** Editorial.

## Issue MI-08
- **Clause:** Constitution §32 (Testing doctrine)
- **Severity:** MINOR
- **Problem:** No test class for **ontology regressions** (a change that reclassifies or merges existing nodes) — distinct from adversarial tests.
- **Proposed correction:** v0.2 adds regression-test class for identity/ontology changes.
- **Constitutional impact:** Editorial.

## Issue MI-09
- **Clause:** IACER §A2 / Roadmap Book 3
- **Severity:** MINOR
- **Problem:** Architecture-family list omits: TON (actor/Infinite Sharding), Hedera (hashgraph aBFT + mirror nodes), Cardano (eUTXO), Algorand (pure PoS + instant finality), Kadena/Chainweb (braided PoW), Privacy systems (Zcash/Monero shielded architectures).
- **Why it matters:** Coverage lists steer later census work; omissions become blind spots.
- **Proposed correction:** v0.2 adds these families to the Book 3 expected-family list (as candidates, not commitments).
- **Constitutional impact:** Roadmap-level only.

## Issue MI-10
- **Clause:** Roadmap Book 1 Bloc 1B
- **Severity:** MINOR
- **Problem:** No chapter for **deprecation/legacy classes** (dead chains, frozen protocols) — §15 exclusion touches it but the ontology needs resolved states for dead objects, not exclusion.
- **Proposed correction:** v0.2's Book 1 plan adds lifecycle states to Bloc 1B scope.
- **Constitutional impact:** Editorial.

---

# PART II — SYSTEMATIC GAPS (cross-cutting)

## SG-A: Missing chain types (feeds Issue MA-03, MI-09)
Constitution/IACER family lists omit: **permissioned/enterprise ledgers** (IACER §A3 mentions them "where materially relevant" but no node class or doctrine exists), **privacy-preserving architectures** (shielded-pool semantics are structurally different — address model, proof systems), **hybrid UTXO/account models** (Cardano eUTXO), **rollup-ecosystem-of-ecosystems** (L3s, validiums, optimistic vs ZK rollup subclass semantics), and **braided/multi-block architectures** (Chainweb). Book 1 Bloc 1B extension mechanism must anticipate these.

## SG-B: Missing protocol/infrastructure classes
Node lists omit: **sequencer** (centralized/shared/decentralized — a systemic single point), **prover/attestation infrastructure** (ZK provers, EigenLayer AVSs), **intent/solver networks**, **key-management infrastructure** (MPC networks, wallet providers as infrastructure not just WALLET nodes), **insurance/security protocols**, **mesh of MEV infrastructure** (relays, builders, searchers as *classes* not instances). These belong in Bloc 1B extension or initial classes.

## SG-C: Missing capital-plumbing concepts
§19 covers most, but omits: **on/off-ramp topology** (fiat rails as research objects), **treasury/endowment wallets as capital nodes** (protocol-owned liquidity), **liquid-restaking derivatives chains** (e.g., restaked collateral re-entering DeFi — the second-order collateral graph), **cross-domain MEV capture**, **perp funding as a capital transfer mechanism**, and **bridged-asset depeg risk paths**. Book 5 must plan for these; constitution should name them.

## SG-D: Missing operator governance
§5.1 lists operator authorities but no **operator decision log** doctrine exists — where decisions are recorded, referenced, and how they bind later planning. The program's own governance (this review, Book 0 packet, ratifications) needs a canonical record location. v0.2 adds §5.4: Operator Decision Log as constitutional record.

## SG-E: Overlap with Crypto Sensor (feeds MA-06)
Enumerated overlap seams: stablecoin flows (Sensor volume vs CSIA structure), perp collateral state (Sensor liquidations vs CSIA collateral topology), bridge flows (Sensor flow data vs CSIA bridge semantics), venue listings (Sensor venue mechanics vs CSIA MARKET class). Each needs explicit ownership assignment at Context Bridge planning (Book 8) — flagged now so Book 1 does not accidentally define Sensor-owned semantics.

## SG-F: Overlap with Capital Field (feeds CR-04)
Direct scope collision: Book 5 Blocs 5A–5F enumerate DEX, lending, staking, RWA — exactly the Capital Field queue items named in IACER §C2. Resolution gate required before Book 5 planning (not before Book 1 — Book 1 is safe).

## SG-G: Drift vectors ahead
Three specific drift risks visible now: (1) **comparison-layer creep** — normalization ("comparison layer" in Axiom 1) expanding until native models atrophy; (2) **ticker-first modeling** — because users search by ticker, entity/token/chain distinctions eroding in operator surfaces; (3) **snapshot-itis** — operator surfaces (Book 9) pulling toward current-state-only views, eroding temporal doctrine. v0.2 anti-drift tests (§37) extended with these three.

---

# PART III — VERDICT

```text
IACER                = SOUND as mission charter. No critical defects.
CONSTITUTION v0.1    = NOT RATIFIABLE. 7 critical issues (CR-01..CR-07).
                       All are definitional/authority gaps, not direction errors.
ROADMAP v0.1         = SOUND structure. 1 scoping defect (MA-13), coverage gaps (MI-09).
DIRECTION VERDICT    = The architectural direction is correct. The constitutional
                       precision is not yet sufficient to bind implementation.
RECOMMENDATION       = Ratify Constitution v0.2 after operator review of the 7
                       critical corrections; then Book 0 packet; then Book 1.
```

End of constitutional review.
