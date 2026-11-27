# 01 - The verified candidate, frozen

No production change is authorized or required for this closeout. The candidate
is re-measured here so the acceptance record names exactly one implementation.

## Identity

| Field | Value |
| --- | --- |
| Candidate | `66200f3cb18ee5cea1483d986e64502f388eeb77` |
| Subject | `B5-P3-R6: close selected-revision cutoff and typed-refusal leakage` |
| Parent | `21fd7e473a534c38b237729f9474c46bb94267ee` |
| Tree | `e7f058bb2e315365b19c3933c16745c895e7bb5b` |
| Branch | `agent/crypto-sensor-fabric-p3-production-master-r1` |
| Local = remote at the publication head | true (`96f4cd28e` both sides, 0 ahead / 0 behind) |
| Production source changed since the candidate | **none** |

`git diff 66200f3cb..96f4cd28e -- quant-lab/src quant-lab/tests quant-lab/config`
is empty: the canonical publication commit is evidence only. The only untracked
path in the worktree is the historical `canonical_runs/p3-r6-final/` bundle,
which is evidence for `868dd3fc9` and is not part of the candidate.

The consumer module that carries the repairs is byte-identical at the candidate
and at the publication head:

```
git rev-parse 66200f3cb:quant-lab/src/crypto_sensor_fabric/normalization/consumer/policy.py
git rev-parse 96f4cd28e:quant-lab/src/crypto_sensor_fabric/normalization/consumer/policy.py
-> 8456aae69bcb577dff5a13550c3d50764e2c9825   (both)
```

## Governance invariants, re-measured

| Invariant | Value at this closeout | Moved by this mission |
| --- | --- | --- |
| Approval manifest git blob | `7be15e8e56c87a4acea533a7b2382c1f5d5ad2f9` | no |
| Approval manifest SHA-256 | `3d707c59fbf1fe96f28b2080811a0da189d2ad5c2859c97faa01a367c7042654` | no |
| Manifest `artifacts` | `{}` (empty) | no |
| Manifest `revoked_approval_ids` | `[]` | no |
| Manifest `authority_id` | `B5_I09P2A_EMPTY_TRUST_ROOT_V1` | no |
| `sensors/verification.py :: INTEGRATION_STATE` | `"INTEGRATION_REQUIRED"` | no |
| Provider approvals | none | no |
| Custody-source authorization | `OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1` unresolved, unimplemented | no |
| Replay binding | `REPLAY_EVIDENCE_RECORD_BINDING_V1` named, guarded (`REPLAY_RECORD_BINDING_ESTABLISHED = False`), **not** implemented | no |
| Trust promotion / gate advancement / Bloc 6 | untouched | no |
| Merge to production | not performed | no |

An empty manifest is the mechanical statement that no trust was promoted: with
no approved artifact and no source-authorization record, the consumer can
compose no `AUTHORIZED` basis, which is the intended state.

## Inventory

| Measure | Value |
| --- | --- |
| Tracked Python files (repository) | 1,111 |
| `quant-lab/src/` | 157 |
| `quant-lab/tests/` | 249 |

## What was not done, deliberately

- **No canonical regression was run.** The mission forbids it and it is not
  needed: no source or test byte changed after the anchored green run.
- **No production, test, schema or manifest edit.** Not one line.
- **No replay or custody contract implementation**, and no architecture
  reopened. The two contracts stay deferred with their requirements already
  written down.
- **No new evidence claim.** This package cites the published bundle; it does
  not re-derive the canonical result and does not restate it as a new execution.

## Why the freeze is trustworthy

The freeze is not an assertion of intent; each row above is a git object or a
hash that an auditor can recompute:

```bash
git -C <worktree> rev-parse 66200f3cb^{tree}
git -C <worktree> rev-parse 66200f3cb:quant-lab/src/crypto_sensor_fabric/normalization/consumer/policy.py
git -C <worktree> rev-parse 96f4cd28e:quant-lab/src/crypto_sensor_fabric/normalization/consumer/policy.py
git -C <worktree> cat-file -p HEAD:quant-lab/config/crypto_sensor_fabric/provider_semantics/approval_manifest.json | sha256sum
git -C <worktree> diff --stat 66200f3cb..96f4cd28e -- quant-lab/src quant-lab/tests quant-lab/config
```
