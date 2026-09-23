# CSIA Book 2 — Evidence Stress Matrix — v0.1

Status: PLANNING DRAFT — NOT RATIFIED
Companion to: Book 2 plan (Blocs 2A–2I), Source Authority Matrix v0.1
Purpose: walk fifteen real-world failure shapes through the full pipeline

```text
SOURCE → RAW EVIDENCE → CLAIM → CLAIM STATE → GRAPH EFFECT
```

and record which pipeline element each stress exercises and what it
teaches. Classification vocabulary:

```text
STRUCTURAL_FAILURE      pipeline as planned cannot handle this; design change needed
REQUIRED_EXTENSION      pipeline handles it only with a mechanism planned here
DEFERABLE_EXTENSION     handling can wait for later book/implementation scope
INFORMATION_GAP         doctrine exists but a parameter must be filled in later
OPERATOR_DECISION       resolution is policy only the operator can set
```

## Legend

VH = valid-time handling · OH = observation (transaction) time ·
GE = graph effect · PR = promotion requirement · CH = conflict handling ·
SP = staleness policy

---

### 1. Ethereum spec revised after an upgrade

- SOURCE: NATIVE_TECHNICAL (spec repo) — two document versions
- RAW EVIDENCE: capture E1 (pre-revision spec), E2 (post-revision spec); distinct evidence_ids, distinct content hashes
- CLAIM: "consensus parameter P = X" (from E1); successor claim "P = Y" (from E2)
- CLAIM STATE: first CORROBORATED → SUPERSEDED (by lineage, not deletion)
- VALID TIME: split at the upgrade activation boundary; P=X true before T, P=Y after T
- OBSERVATION TIME: E2 retrieval date
- GRAPH EFFECT: parameter attribute re-versioned; history queryable at both windows
- PROMOTION REQUIREMENT: spec tier carries specification truth; deployed-state evidence pins the activation boundary
- CONFLICT HANDLING: none once time-split (2F F-2 dissolves the conflict)
- STALE POLICY: supersession-oriented — neither spec version is "stale"
- Exercises: 2B survival-of-edits, 2F F-2 time-split, 2G historical rule
- Classification: REQUIRED_EXTENSION (valid-time splitting of doc supersession)

### 2. XRPL amendment active while old docs remain indexed

- SOURCE: RPC (amendment state) vs NATIVE_TECHNICAL (stale docs page)
- RAW EVIDENCE: E1 RPC amendment-flag capture; E2 old docs capture (still online)
- CLAIM: "amendment A is enabled" (E1) vs "feature requires amendment A" (E2)
- CLAIM STATE: both OBSERVED, structural claim CORROBORATED after boundary pin; docs claim gets a supersedence pointer
- VALID TIME: docs describe spec-intent (open-ended); RPC pins enablement instant
- OBSERVATION TIME: both recorded; docs page last-modified unreliable → retrieval time only
- GRAPH EFFECT: feature state = enabled-from-T; docs-derived relationship keeps its historical window
- PROMOTION REQUIREMENT: deployed state (RPC) is primary for enablement (authority matrix A-4)
- CONFLICT HANDLING: not a conflict after time-split; if docs assert falsity post-T, docs claim → CONTESTED then SUPERSEDED
- STALE POLICY: docs claim NOT stale — superseded; RPC claim SHORT re-observation
- Exercises: 2A scope, 2F, 2G
- Classification: REQUIRED_EXTENSION (indexed-but-superseded doc detection)

### 3. Cosmos governance proposal passes; execution occurs later

- SOURCE: GOVERNANCE (proposal/vote state) + RPC (param change observation)
- RAW EVIDENCE: E1 proposal PASSED capture; E2 execution-height RPC capture
- CLAIM: "proposal 123 passed" (E1); "param changed at height H" (E2) — TWO claims, never merged
- CLAIM STATE: first CORROBORATED (as a passed-proposal claim); second DECLARED until E2 arrives → OBSERVED
- VALID TIME: passed-at instant vs executed-at instant; gap is explicit
- OBSERVATION TIME: both captures
- GRAPH EFFECT: governance edge carries EXECUTION_PENDING phase (2F F-4); activation edge only after E2
- PROMOTION REQUIREMENT: nothing proves execution except execution (authority matrix)
- CONFLICT HANDLING: none — phase modeling prevents the false merge
- STALE POLICY: event-driven, no decay
- Exercises: 2C GOVERNANCE two-phase contract, 2F F-4, 2E P-2
- Classification: REQUIRED_EXTENSION (governance phase states)

### 4. Chainlink announces integration; deployment not verifiable

- SOURCE: NEWS (announcement) + RPC/EXPLORER (absence of deployment)
- RAW EVIDENCE: E1 announcement capture; E2 deployment-namespace capture showing no contract
- CLAIM: "integration was announced" (narrative) vs "integration is deployed" (structural)
- CLAIM STATE: narrative claim → CORROBORATED (narrative exists); structural claim stays DECLARED (2E P-3) — absence of evidence keeps it from OBSERVED (A-1: silence ≠ absence, but active capture showing nothing = evidence of nothing-yet)
- VALID TIME: narrative from announcement date; structural claim UNKNOWN open
- OBSERVATION TIME: both
- GRAPH EFFECT: NO integration edge; optionally an announced-integration flag with narrative-tier provenance
- PROMOTION REQUIREMENT: deployed state required (P-1/P-2)
- CONFLICT HANDLING: none — pipeline structurally prevents promotion
- STALE POLICY: narrative fast decay; structural claim no decay while DECLARED
- Exercises: 2E P-1/P-3, authority matrix
- Classification: INFORMATION_GAP (define the optional announced-but-not-deployed flag representation)

### 5. Bridge route closes

- SOURCE: RPC/EXPLORER (route state), STATUS_SYSTEM (incident)
- RAW EVIDENCE: E1 route-active capture (before), E2 route-reverted/empty capture (after), E3 status incident
- CLAIM: "route R active" → "route R closed at T"
- CLAIM STATE: first OBSERVED→STALE-eligible; closure claim OBSERVED→CORROBORATED (E2+E3)
- VALID TIME: closure instant from chain state; status page supports, never defines
- OBSERVATION TIME: E2/E3 captures
- GRAPH EFFECT: REMOVED_RELATIONSHIP as valid-time closure (2H H-2) — edge history preserved
- PROMOTION REQUIREMENT: deployed state primary; status page corroborates
- CONFLICT HANDLING: explorer lag vs RPC → 2F with lag awareness
- STALE POLICY: SHORT for route state
- Exercises: 2H H-2, 2G SHORT policy
- Classification: REQUIRED_EXTENSION (closure-event change class wiring)

### 6. USDC changes from bridged-only to native issuance

- SOURCE: NATIVE_TECHNICAL (issuer docs), RPC (contract/issuer state), REPOSITORY
- RAW EVIDENCE: E1 docs announcing native issuance; E2 chain-state showing new native mint path; E3 repo release
- CLAIM: "USDC on chain C is natively issued (not bridged)"
- CLAIM STATE: DECLARED (E1) → OBSERVED (E2) → CORROBORATED (E2+E3)
- VALID TIME: native-issuance start boundary; bridged-realization window closes at the same boundary
- OBSERVATION TIME: captures
- GRAPH EFFECT: realization identity transition — new realization with representation mechanism change; old realization CLOSED (never deleted; Book 1 closure doctrine)
- PROMOTION REQUIREMENT: deployed mechanics + docs
- CONFLICT HANDLING: docs precede deployment → time-split, not conflict
- STALE POLICY: MEDIUM; mechanism is stable once observed
- Exercises: Book 1 realization lifecycle consumed correctly by Book 2
- Classification: REQUIRED_EXTENSION (realization-mechanism transition change class)

### 7. Solana RPC providers disagree temporarily

- SOURCE: two RPC sources (distinct owners)
- RAW EVIDENCE: E1 provider-1 capture (state X at slot S), E2 provider-2 capture (state Y at slot S)
- CLAIM: two conflicting state claims at the same valid time
- CLAIM STATE: both OBSERVED → pair CONTESTED → resolution when providers converge (re-observation) → SUPERSEDED/REJECTED of the wrong line
- VALID TIME: identical slot, identical instant — time-split impossible
- OBSERVATION TIME: both captures within the disagreement window
- GRAPH EFFECT: NOTHING promoted while CONTESTED (P-6); prior state remains
- PROMOTION REQUIREMENT: convergence or operator adjudication
- CONFLICT HANDLING: F-3 (tie → CONTESTED), never average (F-5)
- STALE POLICY: SHORT; disagreement itself ages out via re-observation
- Exercises: 2F F-3/F-5, 2E
- Classification: REQUIRED_EXTENSION (transient-disagreement aging)

### 8. ICP docs rename a concept

- SOURCE: NATIVE_TECHNICAL (docs v1, docs v2)
- RAW EVIDENCE: E1 old term, E2 new term
- CLAIM: "concept K is called T1" → "concept K is called T2"
- CLAIM STATE: first SUPERSEDED by second (alias-window semantics, Book 1 §8.3 doctrine applied to terminology)
- VALID TIME: rename boundary (best-effort from release notes; else UNKNOWN bounded)
- OBSERVATION TIME: captures
- GRAPH EFFECT: terminology attribute re-versioned; NO new object minted — the concept persists
- PROMOTION REQUIREMENT: first-party docs sufficient (specification family)
- CONFLICT HANDLING: supersession, not conflict
- STALE POLICY: supersession-oriented
- Exercises: 2B edit-survival, 2A identity-stability doctrine analog for terms
- Classification: DEFERABLE_EXTENSION (terminology alias windows)

### 9. GitHub archived but social claims active development

- SOURCE: REPOSITORY (archived state) vs SOCIAL/NEWS (activity claims)
- RAW EVIDENCE: E1 repo archived capture; E2 social posts
- CLAIM: "repo archived at T" (structural, repository-tier); "team claims active development" (narrative)
- CLAIM STATE: both OBSERVED independently; no promotion conflict because families differ
- VALID TIME: archive instant; narrative window
- OBSERVATION TIME: captures
- GRAPH EFFECT: development-activity relationship decays (SP) or carries contested-development flag; repo state factual
- PROMOTION REQUIREMENT: narrative cannot promote structural activity (P-3)
- CONFLICT HANDLING: none — family separation is the resolution
- STALE POLICY: social fast decay
- Exercises: authority matrix family separation, 2E P-3
- Classification: INFORMATION_GAP (representation of "claimed-alive vs evidenced-alive")

### 10. Aggregator merges unrelated same-ticker assets

- SOURCE: AGGREGATOR vs REPOSITORY/RPC (ground truth for both real assets)
- RAW EVIDENCE: E1 aggregator page conflating assets; E2/E3 first-party data for each asset
- CLAIM: aggregator-fed claims (wrong supply, wrong description) vs correct structural claims
- CLAIM STATE: aggregator claims → CONTESTED → REJECTED; quarantined (2A S-4)
- VALID TIME: conflation window = aggregator page validity window
- OBSERVATION TIME: captures
- GRAPH EFFECT: none from aggregator line; correct identities untouched (Book 1 ticker-collision doctrine)
- PROMOTION REQUIREMENT: aggregator can never be sole authority (A-2/P-2)
- CONFLICT HANDLING: quarantine + rejection; correction claim against aggregator possible
- STALE POLICY: aggregator MEDIUM, but rejection is state-based not time-based
- Exercises: 2A S-4, 2E ADV-2E-2
- Classification: REQUIRED_EXTENSION (quarantine state for sources with conflation history)

### 11. Official website disappears

- SOURCE: NATIVE_TECHNICAL source goes dark
- RAW EVIDENCE: E1 historical captures (pre-death), E2 capture attempt failing (UNREACHABLE observation)
- CLAIM: whatever E1 backed stays; source-health claim "source S unreachable since T"
- CLAIM STATE: E1-backed claims unchanged in validity (evidence survived); source → UNREACHABLE/STALE
- VALID TIME: claims keep their original windows
- OBSERVATION TIME: failure capture
- GRAPH EFFECT: none retroactive; source-staleness may flag dependent claims for re-verification
- PROMOTION REQUIREMENT: existing promotions stand (evidence independence)
- CONFLICT HANDLING: n/a
- STALE POLICY: SOURCE_STALE kind (2G)
- Exercises: 2B survival-of-source-death, 2C failure states as evidence
- Classification: REQUIRED_EXTENSION (source-death re-verification cascade policy)

### 12. API changes schema silently

- SOURCE: REST_API source
- RAW EVIDENCE: E1 old-schema payload; E2 new-schema payload (raw-first, 2C A-2)
- CLAIM: parse of E1 vs parse of E2 — parser versions differ
- CLAIM STATE: pre-drift claims unchanged; new parses under new parser version produce derived evidence with lineage (2B E-3)
- VALID TIME: unchanged — drift is a transaction-time event
- OBSERVATION TIME: drift detected at E2 capture
- GRAPH EFFECT: none until re-parse completes; no gap fabrication
- PROMOTION REQUIREMENT: unchanged
- CONFLICT HANDLING: schema drift is an event, not a conflict
- STALE POLICY: evidence captured pre-drift remains valid for its claims
- Exercises: 2B E-3, 2C schema_drift_behavior
- Classification: REQUIRED_EXTENSION (drift-event detection contract)

### 13. Source corrects historical data

- SOURCE: EXPLORER/DATASET re-publishing corrected history
- RAW EVIDENCE: E1 original data; E2 correction notice + corrected data
- CLAIM: original claims → SUPERSEDED by corrected claims (lineage preserved)
- VALID TIME: corrected claims re-assert the SAME historical windows with corrected values; original remains queryable as "what source said then" (R7)
- OBSERVATION TIME: E2 capture
- GRAPH EFFECT: graph state updates via supersession, history intact
- PROMOTION REQUIREMENT: corrected data must meet the same tier as original
- CONFLICT HANDLING: self-correction = supersession path (2B withdrawal doctrine)
- STALE POLICY: n/a — event-driven
- Exercises: 2B withdrawal-vs-deletion, 2E supersession transitions
- Classification: REQUIRED_EXTENSION (source self-correction lineage)

### 14. Explorer/indexer lags chain state

- SOURCE: EXPLORER vs RPC, same block range
- RAW EVIDENCE: E1 explorer capture (stale view), E2 RPC capture (current)
- CLAIM: conflicting state claims at overlapping valid times
- CLAIM STATE: RPC claim OBSERVED; explorer claim OBSERVED; pair CONTESTED until lag resolves
- VALID TIME: same; lag is an observation-time phenomenon
- OBSERVATION TIME: both; delta measurement is the lag evidence
- GRAPH EFFECT: nothing promoted from the conflict; RPC-fed state stands per A-4 tier
- PROMOTION REQUIREMENT: RPC primary (A-4)
- CONFLICT HANDLING: F-1 tier resolution, not recency alone; phantom diffs (2H ADV-2H-1) never promote
- STALE POLICY: SHORT both, with explorer lag allowance
- Exercises: 2C ADV-2C-1, 2F, 2H
- Classification: INFORMATION_GAP (quantified lag allowance parameter per explorer)

### 15. Two authoritative sources disagree on activation time

- SOURCE: NATIVE_TECHNICAL (docs say T1) vs RPC (chain shows T2)
- RAW EVIDENCE: E1 docs capture; E2 chain activation-height capture
- CLAIM: "activated at T1" (specification family) vs "activated at T2" (deployed-state family)
- CLAIM STATE: deployed-state claim CORROBORATED; docs claim SUPERSEDED with correction pointer; docs-vs-chain discrepancy recorded as meta-claim (F-6)
- VALID TIME: activation instant = T2 (chain is primary for "what happened"); docs T1 recorded as the erroneous specification
- OBSERVATION TIME: captures
- GRAPH EFFECT: activation boundary pinned at T2; discrepancy preserved in history
- PROMOTION REQUIREMENT: deployed state outranks docs for "what IS" (A-1/F-1)
- CONFLICT HANDLING: tier resolution + meta-claim; never midpoint (F-5)
- STALE POLICY: docs supersession-oriented; chain state SHORT
- Exercises: 2F F-1/F-5/F-6 end-to-end
- Classification: OPERATOR_DECISION (whether systematic doc-vs-chain discrepancies trigger a source trust downgrade policy)

---

## Findings summary

```text
STRUCTURAL_FAILURE      0
REQUIRED_EXTENSION      9   (rows 1,2,3,5,6,7,10,11,12,13 — doc-supersession
                             splitting, governance phases, closure events,
                             realization transitions, transient disagreement,
                             quarantine, source-death cascade, drift events,
                             self-correction lineage)
DEFERABLE_EXTENSION     1   (row 8 — terminology alias windows)
INFORMATION_GAP         3   (rows 4,9,14 — announced-flag representation,
                             claimed-alive representation, lag parameters)
OPERATOR_DECISION       1   (row 15 — doc-vs-chain trust downgrade policy)
```

No STRUCTURAL_FAILURE: the planned pipeline resolves every stress without
design change. The REQUIRED_EXTENSIONs are already represented as bloc
invariants/adversarial cases in the plan; they are enumerated here for
ratification visibility.
