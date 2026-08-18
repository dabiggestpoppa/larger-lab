# CR-BLOCK4-D1.1A REPORT

**Checkpoint:** CR-RISK-BLOCK-IV-D1.1A-ARTIFACT-TRUTH-AND-QUANTILE-RECONCILIATION
**Base:** `2a44e824c269d62545fa44538b0df3cea3f51e60` · **Status:** PASS

## 1. Test-count truth

- dedicated suite collected: **62** (pytest
  --collect-only; AST count matches)
- dedicated passed / failed: 62 / 0
- combined checkpoint suites: **261** passed /
  0 failed (8 suites, 261 collected)
- prior claim 62 correct: True · prior
  claim 52 correct: False (52 was the
  brief's minimum-requirements list, not the collected suite)
- parent TEST_AUDIT/DECISION repaired to 62/62/0; runner now derives the
  count from source — `test_count_truth_reconciled = true`

## 2. Quantile reconciliation

- same source book: **True** (canonical hash
  `b64be26010171801104518db72df63abe01714079a5081fef18c42f990a2580a`)
- DESCRIPTIVE_DISTRIBUTION_QUANTILE (D1 plan): interpolated distribution estimate
- RANK_BIN_EDGE (D1.1): rank-fraction event value for binning
- `quantile_difference_explained = true` · `source_distribution_mismatch = false`

## 3. Hard nonregression

| check | result |
|---|---|
| grid counts | PASS [39, 178, 417, 655, 786, 817, 825, 826] |
| family distortion | PASS |
| episodes (12h) / max concurrency | 482 / 3 — PASS |
| performance rows | 8 — PASS |
| science counts | {'n_events': 890, 'n_accepted': 826, 'n_rejected': 64, 'accepted_A': 371, 'accepted_B': 455} — unchanged |

Parent D1.1 regeneration diff touched ONLY TEST_AUDIT + DECISION test-count
fields; all science artifacts byte-identical (see
CR_BLOCK4_D1_1A_ARTIFACT_CORRECTION_LOG.md).

## 4. Decision

`d1_1a_pass = True` · `d1_2_authorized = false` ·
`production_authorized = false` · `human_review_required = true`
