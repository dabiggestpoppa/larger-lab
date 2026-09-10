# S22 — G6 scenario result

- outcome: **PASS_G6_SCENARIO** (expected `AUTHORITY_AND_TRUTH_SEPARATED_BOTH_DIRECTIONS`) — PASS
- behavior fingerprint: `aea9f752cabfb8af910ad05ef261909c`
- forbidden transitions declared: ['GRADE_IMPROVED_BY_DESIRE', 'GRADE_FROZEN_BY_DESIRE', 'DIRECTIVE_AUTHORIZED_UNGROUNDED', 'GOVERNOR_AUTHORIZED_WITHOUT_MANDATE', 'DIRECTIVE_AUTHORIZED_FROM_CLAIMED_LEVEL', 'GRADE_CHANGED_BY_UNRELATED_EVIDENCE']
- forbidden shortcuts attempted & refused: ['DIRECTIVE_REFUSED', 'GRADE_CHANGE_REFUSED']
- sealed: expected_accessed=False · hidden_ground_truth_accessed=False
- authority accounting: external mutations 0 · production 0 · scenario-internal events 3 (simulated only) · model calls: 0 · cloud/production/capital mutations: 0/0/0

## Phase trace

- `01` PERMISSION_RECORDED
- `02` GOVERNED_GRANT_ISSUED
- `03` DIRECTIVE_AUTHORIZED
- `04` DIRECTIVE_REFUSED
- `05` DIRECTIVE_REFUSED
- `06` MANDATE_RECORDED
- `07` DIRECTIVE_AUTHORIZED
- `08` GRADE_CHANGE_REFUSED
- `09` GRADE_CHANGED
- `10` DIRECTIVE_AUTHORIZED
