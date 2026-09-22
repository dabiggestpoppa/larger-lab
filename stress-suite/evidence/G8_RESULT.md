# G8 — Cross-Scenario Contradiction Audit Result

**GATE STATUS:** `PASS_G8_CROSS_SCENARIO_COHERENCE`

- starting SHA `661878e7df4c5b8f7bcb2479ceebabd79d8c28b3`
- tested SHA `2cf1bb4b6bc39b2a372851a02ec50d96758a8788`
- evidence commit `STRESS-G8RR` (this package; not self-hashed)
- contract `G8-EQUIVALENCE-CONTRACT-001` v1.2.0 `525b18bcea68d23584097c8b740d2d23`
- authoritative test command `cd stress-suite && PYTHONIOENCODING=utf-8 python -m pytest tests -q` -> **passed 1024**, and this count is not the artifact's: an ordinary run of this command executes the lag check that the artifact-producing run has to skip, so it passes 1023 (measured below) + 1 (the skipped case) = 1024 of 1024 collected
- artifact-producing command `cd stress-suite && PYTHONIOENCODING=utf-8 python -m pytest tests -q --junitxml=evidence/G8_TEST_RESULTS.xml` -> **collected 1024 / passed 1023 / skipped 1 / failed 0** (artifact `pytest` `23f97af88ff31c0e`, python `3.11.9`). These are the counts this package rests on, and they belong to the command that produced the artifact
- skipped in the artifact-producing run 'stress-suite.tests.test_g8_contradiction::test_the_committed_package_names_the_derived_code_tree', and named here rather than smoothed over: artifact-producing run: the archive for this tree cannot exist yet, so a lag is expected here and is checked by every ordinary run (and by test_the_lag_rule_detects_a_lagging_tree_...)
- test provenance (revision R3, finding R-G8-07): the baseline is read from the JUnit artifact the authoritative command produced, never from a self-reported integer. The receipt records the artifact digest, the suite identity, the tested tree, the command and the environment; a missing, malformed, stale or failing artifact refuses emission. No exit status is published, because a JUnit document cannot show the producing process's exit code -- a claim where an observation is impossible is not evidence, and the refusal it drove is driven by the counts MEASURED from the artifact instead (STRESS-G8ARCH4).

## What was asked

Not whether each scenario works, but whether EQUIVALENT institutional facts produce CONSISTENT phase, authority, evidence, lifecycle, recovery and terminal-state behaviour across S01-S24 and the G1-G7 implementation, and whether materially different facts are ever treated as equivalent.

## What was done

One observation per scenario was derived by RUNNING that scenario through its OWN canonical runner (G2 phase machine, G3 ecology, G4 memory, G5 domain, G6 governance), with every evaluator handed a decision-grade projection whose sealed fields are asserted empty first. Those observations were then compared inside the contract's families: **65 comparisons over 35 observations**, **21/21** of them declared mandated relationships.

Verdicts: `{"CONSISTENT": 1, "MATERIAL_DISCRIMINATOR": 58, "NOT_COMPARABLE": 6}`.

## Gate decision

Exit `PASS_G8_CROSS_SCENARIO_COHERENCE` with reasons `[]`.

- blocking contradictions: **0**
- guarded-property violations: **0**
- high-severity evidence gaps: **0**
- low-severity gaps recorded only: **0**
- gate-claim findings blocking: **0**; recorded but not blocking: **1**; superseded: **1**
- mandated pairs not compared: **0**

## Recorded findings, none of them architectural

| receipt | finding | classification | severity | blocks |
|---|---|---|---|---|
| G4_EVIDENCE_RECEIPT.json | TESTED_SHA_FULL_FORM_UNRESOLVABLE | RECEIPT_OR_CLAIM_DEFECT | MEDIUM | no |
| G6_EVIDENCE_RECEIPT.json | AUTHORITY_ACCOUNTING_VOCABULARY | SUPERSEDED_BY_LATER_ARTIFACT | MEDIUM | no |

No finding blocks the gate. The one recorded identifier defect (G4) resolves through the receipt's own declared abbreviation to a unique commit whose subject matches verbatim, which the declared `blocks_gate_policy` classifies as MEDIUM and non-blocking; the G6 vocabulary finding is corrected by a later recorded artifact. G8 does not claim the historical evidence package is flawless. It claims that no equivalent governed facts produced incompatible institutional behaviour, that every divergence it observed is explained by a materially different derived discriminator, and that the defects it did find are recorded with their exact referents.

## Repairs made to G8's own equipment

Two defects in the audit itself were found by running it, and each is recorded as a declared contract revision rather than applied silently:

- **R1** — widened the F4/F5 derivations (reopen-target class; claim-scope ladder derived from each pack's declared claim_type). Both gaps were caused by a declared outcome-relevant field being DERIVED AS A CONSTANT, which is a defect of the audit's own equipment.
- **R2** — split the tested-surface key vocabulary from the terminal-head key vocabulary, added abbreviation resolution and the declared blocks_gate policy.
- no verdict rule, token vocabulary, order invariant or outcome permissiveness rank was relaxed; the changes add derivations and reclassify findings.

The pre-revision verdict was `BLOCKED_G8_MISSING_EVIDENCE` with reasons `["3 gate-claim defect(s)", "2 evidence gap(s) where equivalence could not be established"]`. Those entries are preserved verbatim in `G8_COUNTEREXAMPLE_REGISTER.json`, together with the refuted false positive and the post-revision comparison for each reclassified pair. A reviewer can therefore see exactly what changed and judge whether the revision was justified.

## Claim defects recorded, not rewritten

A claim published by this line of work that the evidence later FALSIFIED is recorded here. Commit messages already pushed are not rewritten to make an earlier claim read better: the register entry is the durable record, and the corrected statement stands in the field it belongs to.

| claim | classification | severity | status | disposition |
|---|---|---|---|---|
| commit 950e6efb (STRESS-G8ARCH2-R): 'the same package regenerates byte-identically from here' | RECEIPT_OR_CLAIM_DEFECT | INFO | FALSIFIED_THEN_SUPERSEDED | superseded by the corrected `reproducibility` field, added at 4d80828f; the commit message was NOT rewritten because it is already pushed, and this register entry is the durable record |

## What this PASS does not mean

It does not mean the audit is unbounded. Of 69 declared verified fields, 36 actually varied inside their family in this run; the rest are constant or identically UNKNOWN and are listed as limitations (`AMB-G8-01`, `AMB-G8-02`). It does not mean S13 proves the proposed continuation-equivalence contract, which is an unratified future document. It does not resolve `CON-02`, `CON-03` or `AMB-08`. It does not claim independent external verification.

## Boundary

A-004..A-010 untouched. No amendment ratified. No scenario expectation changed, no existing test weakened. Model calls 0, network calls 0, cloud mutations 0, production mutations 0, capital mutations 0, external authority mutations 0. The MF-B0..B4 worktree was not touched.

## Next

`PASS_G8_CROSS_SCENARIO_COHERENCE` -> next eligible gate: **G9 — NOT AUTHORIZED**; G9 requires a new explicit authorization after operator review of this evidence.
