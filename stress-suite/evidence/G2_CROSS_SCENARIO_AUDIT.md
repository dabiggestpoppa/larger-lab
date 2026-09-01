# G2 X — Cross-Scenario Contract Audit

Every scenario was replayed under every OTHER scenario's frozen evaluation
contract (20 ordered pairs). The audit proves contracts participate in
decisions, are never mutated by foreign runs, and can only yield a PASS
verdict when behavior is identical to the own-contract run (no silent
inheritance of foreign semantics).

| scenario | under contract | behavior identical | foreign verdict |
|---|---|---|---|
| S01 | S02 | yes | PASS |
| S01 | S03 | no | FAIL |
| S01 | S04 | yes | PASS |
| S01 | S05 | no | FAIL |
| S02 | S01 | yes | PASS |
| S02 | S03 | yes | PASS |
| S02 | S04 | yes | PASS |
| S02 | S05 | no | FAIL |
| S03 | S01 | yes | PASS |
| S03 | S02 | no | FAIL |
| S03 | S04 | no | FAIL |
| S03 | S05 | yes | PASS |
| S04 | S01 | yes | PASS |
| S04 | S02 | no | FAIL |
| S04 | S03 | no | FAIL |
| S04 | S05 | no | FAIL |
| S05 | S01 | yes | PASS |
| S05 | S02 | yes | PASS |
| S05 | S03 | yes | PASS |
| S05 | S04 | yes | PASS |

**Interpretation:** a `yes` row means the foreign threshold happened to be
semantically equivalent for that scenario's gates (recorded as benign
equivalence); a `no` row means the foreign contract changed applied
behavior, and the verdict column reports the honest outcome against the
scenario's own expectations. No row shows `PASS` with different behavior.
