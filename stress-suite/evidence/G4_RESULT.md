# G4 — MEMORY, NEGATIVE KNOWLEDGE, EPISTEMIC METABOLISM & EPOCH RECONSTRUCTION

**STATUS:** `PASS_G4_MEMORY_AND_EPOCHS`

**STARTING SHA:** `27ae2a5aee7e02bba62b352c6e9bf8d6eb2c07bf`
**ARTIFACTS HEAD:** `490e078d1e2e6f1c31e88944de9cf2dcd99a4609`
**EXTERNALLY VERIFIED BRANCH HEAD:** not yet — G4 authorized no push; the receipt records `externally_verified_branch_head: null` (non-self-referential SHA semantics).

**COMMITS (7):**
1. `f67c2627` STRESS-G4P0 — replication identity/provenance, conflict ledger, exact operator permanence, sealed epochs
2. `2788b964` STRESS-G4A — activation tiers, memory index, metabolism pipeline
3. `2f5bb0f6` STRESS-G4B — versioned machine-readable reopen conditions + evaluator + suppression decisions
4. `d71174d9` STRESS-G4C — one shared G4 memory/reactivation policy (S10–S13)
5. `c3a958df` STRESS-G4D — sealed epoch reconstruction bundle + PROVISIONAL reconstruction contract
6. `df038fdb` STRESS-S10–S13 — scenario packs + deterministic runner + byte-reproducible receipts
7. `490e078d` STRESS-G4X — adversarial cross-scenario/metamorphic regression suite (66 tests)

**TESTS:** **524 / 524** — 458 prior preserved + **66 new G4 regressions** (no prior test weakened; the one documented legacy upgrade is the `make_permanent` signature in `test_negative_knowledge.py`, which now binds the ACTUAL AuthorityState level instead of trusting a payload string).

## Scenario results (all under the ONE shared `G4_MEMORY_AND_REACTIVATION_POLICY` V1)

| Scenario | Outcome | Behavior fingerprint |
|---|---|---|
| S10 dormant knowledge returns | `REOPEN_CANDIDATE` (DORMANT → REACTIVATED → CANDIDATE; direct DORMANT→ACTIVE forbidden) | `ea9ff74b…` |
| S11 negative knowledge dogma | `STOP_SUPPRESSION` (evidence-backed blocker reopen; record retained) | `4f78dba1…` |
| S12 institutional hyperthymesia | `BOUNDED_CONTEXT` (55,012 objects; 12 active; recall 1.0; stale intrusion 0) | `cdde25d0…` |
| S13 runtime replacement | `RECONSTRUCTED` (sealed epoch rebuilt from canonical artifacts; runtime rename stable) | `a69a8c80…` |

## Status by discipline

- **G4-P0:** PASS — raw replication counts cannot mint paths; secondary-surface conflicts survive in a `ProvenanceConflictLedger`; permanence requires exact OPERATOR authority (fake/worker payloads rejected); sealed epochs are deeply immutable with alias-proof successors.
- **M4 vs memory-tier separation:** PASS — `KnowledgeActivationState` keeps lifecycle state, memory tier, retrieval relevance and canonical truth separate (ACTIVE + ARCHIVAL_STORE is legal).
- **Reopen contract:** PASS — versioned `ReopenCondition` with a small fail-closed operator vocabulary; `ReopenEvaluator` decides eligibility only, never promotion.
- **Negative-knowledge authority:** PASS — ordinary agents cannot create permanence; operator-permanent records stay `OPERATOR_REVIEW_REQUIRED` (revocation ambiguity preserved, not resolved).
- **Epoch immutability:** PASS — BUILDING→SEALED snapshots, frozen fingerprints, nested mutation impossible, successors never rewrite predecessors.
- **Runtime-neutral reconstruction:** PASS — replacement-runtime rename leaves the semantic fingerprint unchanged; missing surfaces fail closed (no guessed defaults); AMB-12 = `EMPIRICALLY_TESTED_PROVISIONAL_CONTRACT`, subject to ratification.
- **Sealing:** PASS — expected outcomes and hidden ground truth never reach the decision path; scenario rename leaves behavior fingerprints unchanged.

**NEW CONTRADICTIONS:** none · **NEW AMBIGUITIES:** operator-permanence revocation semantics unspecified (kept explicit).

**CARRIED:** CON-02, CON-03, AMB-03, AMB-08, AMB-11, AMB-13, AMB-12 (provisional).

**MUTATIONS:** cloud=0 · production=0 · capital=0 · authority=NONE · **MODEL CALLS:** 0 · **COST:** $0 (local, deterministic, synthetic).

**RECOMMENDED NEXT ACTION:** `AUTHORIZE_G5`. G5 not begun; S14–S24 not implemented.
