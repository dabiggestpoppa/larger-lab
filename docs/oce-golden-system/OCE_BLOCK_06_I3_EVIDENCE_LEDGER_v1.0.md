# B6-I3 evidence ledger (operator truth and authority)

Stage: `B6-I3` — C2.S1 capability view, C2.S2 approval inbox, C2.S3 evidence explorer.
Status: **EVIDENCE FROZEN — NOT RATIFIED, NOT MERGED.** Operator review required.

## Identity

| Item | Value |
|---|---|
| Base (B6-I2 merge) | `018b164f249bbf075334d5d03ad37e80dcbbede0` / tree `65c3713ad70e527a6a5657347c53f8663a2ccb20` |
| P0 freeze | `8726c2dd4c602c0788a7e0208047c7c1f873e5dd` |
| Implementation | `ac568c513bc3975e8f9740968fd32a7ac94578b6` / tree `8bbcc5c3b7d53264d698069d2f8677049c82bce2` |
| Paired pin | `2ac2ca0249cb09fdf55408bb405eea8fecec5b07` (docs only; pins base `018b164f` → product head `ac568c51`) |
| Proof-tooling repair | `1a7683f5ca180e7e2159672ffc6ee58b01e402b5` |
| Ledger freeze | `a817bac64b842ddb2273f50d6583cec779566723` |
| Ledger correction | `3ee76bc10879788c470d75d5fb2f5801c1fa98fe` |
| Ledger count restatement | `10ab7f667c6c1a0d4ffc6e410c86675370bca445` |
| Evidence hardening | `50075defd15f8d973bc8170760e39ef8a95409be` |
| Validation gate restatement | `655dcd4b5731b5deade521af679a2995c5f7842e` |
| CI tested merge ref | `14d97bcfd345bfcd8d79fbc3652de2101dfc6466` / tree `e5b6974a130e587b103a4d86577498628197e77c` |
| CI workflow run | `B6-I3 Validation` run `42919431261`, tested merge second parent `655dcd4b5731b5deade521af679a2995c5f7842e` |
| Artifact | `b6-i3-evidence-2d26cb2c67b6` |

## B6-I3 gates (workflow `B6-I3 Validation`, tested merge ref `14d97bcf`)

| Gate | Result |
|---|---|
| Conformance validator | PASS 136/136 (identity, packet, registry, failures, registration, manifest, boundary, text) |
| Node inventory vs registry | 28 collected, 28 unique, 4 modules, declared == defined |
| Executed nodes | 28 tests, 0 failures, 0 errors, 0 skipped, zero_problems true |
| Mutation battery | floor 6, 6 mutations, 6 discriminated, 6 restored, pristine green true |
| Stage-scope controls | 14/14 PASS (`i3_is_i2_plus_operator` = only `oce/operator/` added) |
| B6-I0 validator at later stage | PASS 136/136, resolved mode i3 |
| B6-I1 validator at later stage | PASS 168/168 |
| Frozen Book 5 gate | ok=true, 41/41 nodes |
| Adjacent Book 5 suites | 53 tests, 0 failures, 0 errors |
| Cleanup | tree clean true, tracked tree clean true, residue [] |

## Paired comparison (base `018b164f` → product head `ac568c51`)

- Status **PASS** on 20 checks; failed: [].
- Common population: 270 nodes (floor 208), base-only 0.
- Head-only (at product head `ac568c51`): 27/27 expected nodes.
- Common outcome: 270 pass, 0 fail, 0 skip, 0 error.
- Endpoints: base `018b164f249bbf075334d5d03ad37e80dcbbede0`, head `ac568c513bc3975e8f9740968fd32a7ac94578b6`.

## Notes on population

- The paired comparison's head endpoint is pinned to the product implementation head `ac568c51` (§3), which carries 27 B6-I3 focused nodes.
- The current governed head `655dcd4b` carries 28 focused nodes: the 27 product nodes plus the duplicate-node hostile control (`test_duplicate_node_refused`, B6I3-R28) added as proof-tooling hardening in `50075def`. That node is validated by the registry declared==defined==28 check, the local 28/28 run, and the validator's `registry/total`/`registry/unique` checks. It is intentionally outside the pinned paired population; proof-tooling behavior is validated separately per §3.

## Prior stages (unchanged, replayed at their own heads)

| Stage | Result |
|---|---|
| B6-I2 Validation (replay `9bf76df4`, main `4496d548`) | PASS 172 checks |
| B6-I0 Validation at later stage | PASS 136 |
| B6-I1 Validation at later stage | PASS 168 |

## Auditor parse

- Product contract, registry, 28 nodes (27 product + 1 hostile control), 6 mutations, 14 controls, paired population and prior-stage replay: **VERIFIED**.
- Repairs made before this freeze: X1 paired pin; X2 I1 later-stage authority admission and added-surface control; X6 duplicate-node refusal hardening + 28-node floor; X7 validation gate restatement to 28.
- No unresolved **DEFECT** or **AMBIGUOUS** finding remains. Nothing is ratified or merged.

## Holds

`B6-I4`–`B6-I9` LOCKED · Book 6 incomplete · G16 OPEN (B5I8-DF05) · cost `$0` · capital authority `none` · no publication, evaluation system, hosting, provider, broker or execution authority.
