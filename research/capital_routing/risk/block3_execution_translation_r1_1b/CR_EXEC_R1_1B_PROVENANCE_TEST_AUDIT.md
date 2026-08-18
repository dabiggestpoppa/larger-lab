# R1.1B provenance test audit (immutable commit-SHA semantics)

## Semantics
IMMUTABLE_COMMIT_SHA — branch tips are mutable and are NEVER frozen; historical provenance locks commit objects only

## A. Frozen commit objects exist
- execution-runtime-foundation `9e11db928ad3c330fcde06d075e20a6e5b349d89` — exists: True
- tb-forward-engine `d12005988ce61170d9bc5478089baa5ce54cc2a9` — exists: True
- **frozen_commits_exist = True**

## B. Commit identity (subject matches expected checkpoint)
- exec foundation subject: `QL-EXEC-R1-GENERIC-CONTRACTS-AND-ACCOUNT-REGISTRY` — matches `QL-EXEC-R1-GENERIC-CONTRACTS-AND-ACCOUNT-REGISTRY`: True
- tb subject: `TB-R6.1B-FIX-WORKER-STATE-LATCH: ONLINE_MARKET_CLOSED no longer sticks after market recovery` — matches `TB-R6.1B-FIX-WORKER-STATE-LATCH`: True
- **identity_matches = True**

## C. Manifest <-> decision SHA agreement
- **manifest_decision_sha_agreement = True**
- Historical R1.1 SOURCE_SHA_MANIFEST carried science-input hashes only (no authority-SHA fields); the authority SHAs were frozen in the R1.1 DECISION + CROSS_WORKSTREAM_AUTHORITY.md. R1.1B closes the gap: its manifest carries the frozen SHAs.

## D. No cross-branch write by R1.1 (ancestry + changed-file truth)
- R1.1 commit `seal_2bbe52ea` (2bbe52ea): exists=True, on_capital_routing=True, ancestor_of_exec_foundation_frozen=False, ancestor_of_tb_frozen=False
- R1.1 commit `test_child_d51b9b47` (d51b9b47): exists=True, on_capital_routing=True, ancestor_of_exec_foundation_frozen=False, ancestor_of_tb_frozen=False
- `scripts/run_exec_translation_planning_r1_1.py` — in exec-foundation frozen tree: False; in tb frozen tree: False
- `research/capital_routing/risk/block3_execution_translation_r1_1/CR_EXEC_R1_1_DECISION.json` — in exec-foundation frozen tree: False; in tb frozen tree: False
- `research/capital_routing/risk/block3_execution_translation_r1_1/CR_EXEC_R1_1_SOURCE_SHA_MANIFEST.json` — in exec-foundation frozen tree: False; in tb frozen tree: False
- **foreign_branch_write_detected = False**

## E. Current branch heads (informational diagnostics ONLY)
- execution-runtime-foundation: `9e11db928ad3c330fcde06d075e20a6e5b349d89`
- tb-forward-engine: `d12005988ce61170d9bc5478089baa5ce54cc2a9`
- INFORMATIONAL ONLY — recorded at audit time; movement of these tips is NOT a provenance test failure

## Verdict
- current_branch_tip_equality_required = False
- network_required = False · git_fetch_used = False
- **provenance_test_pass = True**
