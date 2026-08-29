# OCE Checkpoint Registry

**Updated:** 2026-08-26

| Checkpoint | Status | Evidence commit | Implementation SHA | RUN_ID | Gate |
|---|---|---|---|---|---|
| B1-I1 | RATIFIED / CHECKPOINTED | `3ee31b2a6` | `50bf8fe4` | `e33a841c6eb2` | READY_FOR_OPERATOR_REVIEW |
| B1-I2 … B1-I9 | LOCKED (historical) | — | — | — | — |
| B1-LOCAL | LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW (RUN 52f60c556f50) | 793289c60fd3b02152bee2ec54ce32d2658e12b5 | c2b2f515 | 52f60c556f50 | LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW |
| B1-CLOUD-ACTIVATION | DEFERRED_BY_OPERATOR | — | — | — | — |

## B1-I1 Checkpoint Detail

- **Decision:** operator ratified the B1-I1 checkpoint on 2026-08-26 (`AUTHORIZED_STAGE=B1-I1-RATIFICATION-AND-B1-I0-PLANNING-ONLY`).
- **Evidence:** CI run [33010802229](https://github.com/dabiggestpoppa/larger-lab/actions/runs/33010802229), artifact `b1-i1r3h-evidence-e33a841c6eb2.zip` (ID 9622689584, SHA-256 `a87a4ab8…7684e`).
- **Totals:** regressions 48/48 · initial 31 PASS · adversarial 49/49 · final 35 PASS · independent gate READY_FOR_OPERATOR_REVIEW.
- **Verification:** manifest SHA-256 hashes verified after extraction; worktree cleanup `{removed: true, pruned: true}`; source clean before and after adversarial testing; one RUN_ID everywhere; version 3.6.0 consistent; cost $0; cloud mutations 0.
- **Held back:** B1-I2+ remain locked. Block 1 overall remains IN PROGRESS. Nothing purchased, provisioned, or deployed.
