# S22 — G6 scenario result

- outcome: **PASS_G6_SCENARIO** (expected `AUTHORITY_AND_TRUTH_SEPARATED_BOTH_DIRECTIONS`) — PASS
- behavior fingerprint: `684ce67d5d190d57f984ccc65e97edb7`
- forbidden transitions declared: ['GRADE_IMPROVED_BY_DESIRE', 'GRADE_FROZEN_BY_DESIRE', 'DIRECTIVE_AUTHORIZED_UNGROUNDED', 'GOVERNOR_AUTHORIZED_WITHOUT_MANDATE']
- forbidden shortcuts attempted & refused: ['DIRECTIVE_REFUSED', 'GRADE_CHANGE_REFUSED']
- sealed: expected_accessed=False · hidden_ground_truth_accessed=False
- authority changes: NONE · model calls: 0 · cloud/production/capital mutations: 0/0/0

## Phase trace

- `01` PERMISSION_RECORDED
- `02` DIRECTIVE_AUTHORIZED
- `03` DIRECTIVE_REFUSED
- `04` MANDATE_RECORDED
- `05` DIRECTIVE_AUTHORIZED
- `06` GRADE_CHANGE_REFUSED
- `07` GRADE_CHANGED
- `08` DIRECTIVE_AUTHORIZED
