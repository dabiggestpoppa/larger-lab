# CR-BLOCK4-D1.2 TRUTH HIERARCHY

## Source precedence

| 1 | ACTUAL_OBSERVED |
| 2 | BROKER_DOCUMENTED |
| 3 | PROFILE_FROZEN |
| 4 | USER_SPECIFIED_SCENARIO |
| 5 | HYPOTHETICAL_DIAGNOSTIC |
| 6 | UNKNOWN |

## Rules

- Every physical field carries exactly one truth class.
- Classes never silently upgrade: USER_SPECIFIED_SCENARIO never becomes
  ACTUAL_OBSERVED without a real observation; FakeMT5 / TB demo specs never
  become actual broker truth.
- The user-supplied operating assumptions (prop ~25k USD, leverage floors
  1:50 / 1:100 / 1:500, OX up to 1:1000, smaller live balance with high
  leverage) are **USER_SPECIFIED_SCENARIO**, NOT ACTUAL_OBSERVED and NOT
  BROKER_DOCUMENTED.
- UNKNOWN is a first-class answer; missing critical quantity truth blocks the
  empirical lane.

## Cross-workstream heads (recorded read-only at checkpoint start)

| workstream | head | checkpoint |
|---|---|---|
| execution-runtime-foundation | `62e6d0402a780d171a8b81c2070567045e341be7` | QL-EXEC-R4.1-TB-GENERIC-RUNTIME-SHADOW-DEPLOYMENT-PLAN |
| tb-forward-engine | `b48fd35255b41865026a3cba333ae2a2a0d6a004` | TB-R6.1D-BOOT-FLOW-STACK: supervisor owns watcher + dashboard, full stack auto-starts at logon |
| main | `9f61288679eea56a298e08f718c314f2ca509bc5` | OCE Block 0: ratify constitutional control checkpoint |
