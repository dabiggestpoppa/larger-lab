# G8 — contract amendment chronology

A verdict rule set that was chosen after seeing the outcome is not a gate, it is a summary. This artifact records what is PROVABLE about when the G8 verdict rules were fixed, in three declared stages, and refuses to summarise itself as stronger than its weakest element.

| artifact | stage | claims_pre_run_freeze | introducing_commit |
|---|---|---|---|
| G8-EQUIVALENCE-CONTRACT v1.0.0 (superseded) | RETROSPECTIVE_RECONSTRUCTION | False | - |
| G8-EQUIVALENCE-CONTRACT v1.1.0 @ f5482e3e (STRESS-G8P0) | POST_FINDING_AMENDMENT | False | f5482e3e (STRESS-G8P0) |
| G8-EQUIVALENCE-CONTRACT v1.2.0 (revision R3) | PRE_RUN_FROZEN_ARTIFACT | True | STRESS-G8R1 (the repaired audit-contract commit) |

Overall classification: **RETROSPECTIVE_RECONSTRUCTION**.

Gate blocking policy source: G8-EQUIVALENCE-CONTRACT v1.2.0 (revision R3) — committed by STRESS-G8R1, i.e. a PRE-RUN FROZEN ARTIFACT relative to the STRESS-G8RR evidence commit that archives the repaired result. The gate's blocking status is therefore derived from a policy that predates the repaired run, NOT from any rule authored after seeing the repaired outcome.

## Git evidence

`git log --all -- stress-suite/evidence/G8_EQUIVALENCE_CONTRACT.json` returns exactly one commit, f5482e3e (STRESS-G8P0), and that commit's blob already carries version 1.1.0 WITH the R1/R2 revisions. Git therefore does NOT establish that the v1.0.0 verdict rules were frozen before the first comparison ran. The earlier wording 'preserved verbatim' / 'frozen before any comparison ran' was NOT supportable and has been removed rather than softened.

## Retraction

The pre-repair contract declared `status: FROZEN_AT_STRESS-G8P0` and a `freeze_note` stating it was *authored BEFORE any cross-scenario comparison runs*. Git shows exactly one commit ever touching that file and that blob already carries the revisions motivated by the first run's own findings, so the freeze claim is **not supportable** and is recorded here as retracted rather than softened. The unsupported phrases ('preserved verbatim', 'frozen before any comparison ran') are removed from the contract of record.

## Forward rule

future gates must commit the pre-run contract BEFORE executing the audit; this gate records the chronology defect instead of rewriting it away

Gate exit for this run: `PASS_G8_CROSS_SCENARIO_COHERENCE`.
