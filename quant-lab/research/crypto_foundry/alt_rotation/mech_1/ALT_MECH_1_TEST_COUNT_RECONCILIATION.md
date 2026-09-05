# ALT_MECH_1 TEST-COUNT RECONCILIATION

## Discrepancy

| Source | Claim |
|---|---|
| Parent commit message (`2c36afd0`) | "All tests pass (69/69: 50 DATA-1 + 19 DATA-1.1)" |
| Parent decision (`ALT_DATA_1_1_DECISION.json`) | `"test_results": "91/91 passing (DATA-0 + DATA-0.1 + DATA-1 tests)"` |

## Resolution (verified empirically via pytest collection in this worktree, base `2c36afd0`)

| Suite | File | Tests collected |
|---|---|---|
| DATA-0 | `data_0/tests/test_alt_data_0.py` | 21 |
| DATA-0.1 | `data_0/tests/test_alt_data_0_1.py` | 20 |
| DATA-1 | `data_1/tests/test_alt_data_1.py` | 50 |
| DATA-1.1 | `data_1_1/tests/test_alt_data_1_1.py` | 19 |
| **Total (full stack)** | | **110** |

### Canonical accounting

- **69/69** = DATA-1 (50) + DATA-1.1 (19) — the suites exercised by the DATA-1/DATA-1.1
  truth-seal itself; the commit message counted only the suites relevant to that seal.
- **91/91** = DATA-0 (21) + DATA-0.1 (20) + DATA-1 (50) — cumulative through DATA-1;
  the decision JSON was written before the DATA-1.1 suite existed and its wording
  ("DATA-0 + DATA-0.1 + DATA-1") confirms the intended scope.
- **110** = full canonical stack including DATA-1.1.

Both parent claims are correct within their stated scopes; neither is wrong.
Canonical cumulative test count for the lineage is **110**, plus the MECH-1 suite
authored at this checkpoint (`mech_1/tests/test_alt_mech_1.py`).

No scientific result is altered by this reconciliation (documentation only).
