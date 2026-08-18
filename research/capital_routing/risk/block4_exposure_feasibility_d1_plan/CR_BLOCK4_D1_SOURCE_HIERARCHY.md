# CR-BLOCK4-D1 SOURCE HIERARCHY

Physical facts are consumed strictly in this order of authority. Never silently
replace a higher authority with a lower one, and never promote a lower class upward.

| rank | source | label |
|---|---|---|
| 1 | actual broker / account observed truth | ACTUAL_OBSERVED |
| 2 | broker/API documented instrument spec | BROKER_DOCUMENTED |
| 3 | execution-runtime-foundation normalized BrokerSession truth | (class per underlying source) |
| 4 | frozen operator execution profile | PROFILE_FROZEN |
| 5 | explicitly labeled hypothetical diagnostic contract | HYPOTHETICAL_DIAGNOSTIC |
| 6 | absent | UNKNOWN |

## Truth-class rules

- Every physical scenario carries exactly one truth class.
- Classes never silently upgrade: `HYPOTHETICAL_DIAGNOSTIC` -> `ACTUAL_OBSERVED`
  requires a real observation, not an assumption.
- `FakeMT5` demo fixtures (e.g. leverage=100 in `ox_demo`) are at best
  `HYPOTHETICAL_DIAGNOSTIC` and must NEVER be promoted to actual account leverage.
- UNKNOWN is a first-class answer; missing critical truth blocks the affected lane.

## Cross-workstream heads frozen at checkpoint start (git fetch)

| workstream | head | checkpoint |
|---|---|---|
| execution-runtime-foundation | `52e39b13f37812221cab7c283afc302623a61bc6` | QL-EXEC-R2.1-MT5-FILL-POLICY-AND-RESULT-TRUTH-REPAIR |
| tb-forward-engine | `b48fd35255b41865026a3cba333ae2a2a0d6a004` | TB-R6.1D-BOOT-FLOW-STACK: supervisor owns watcher + dashboard, full stack auto-starts at logon |
| main | `dfdca6acd829cda4c084cd3bd217ab606348b660` | (documentation commit) |

These are interface evidence only. Capital Routing does not modify or import these branches.
