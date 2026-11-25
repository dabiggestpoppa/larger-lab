# 04 - Governance, reconciliation and invariants

## G16 - I08 scope admission, confirmed prospective

Recorded in R5, re-checked here mechanically: the amendment is **+15 / -3** in
`test_b5_i08_scope_audit.py`. One live admission predicate gained `/consumer/`;
the rest is a disclosure comment that names the directive and states that every
previously admitted path is still admitted while `identity/`, `terms/`, `time/`
and the top-level modules remain refused by name. No sealed evidence, record or
artifact was rewritten. Exact-file constraint lives in I05/I10
`P3_MASTER_EXACT_PATHS`, so the amendment is not a directory-wide permission
slip. Disposition: prospective amendment, disclosed, admitted by name.

## G17 - consumer admission in the I06 audit and producer (pre-existing red)

Not previously known, found by this mission while executing the governance set.

Defect: the I06 replay-safety audit and the I06 producer allowlists admitted
`normalization/{common,sensors,authority}` and never admitted `consumer/`, and
their pinned source hashes predated the R5 tree. The consumer package could not
have been evaluated by the I06 audit at all - the audit would have refused it
as an unadmitted change rather than reviewing it.

Repair, disclosed and prospective: the audit and producer now admit the
consumer package by exact file set (`P3_CONSUMER_EXACT_PATHS`,
`P3_DISCLOSED_SRC_EXACT_PATHS`), pin the disclosed per-file digests
(`P3_DISCLOSED_SHA256`, `P3_DISCLOSED_EVIDENCE_SHA256`) and name the admitted
delta in row detail. The pattern is the one these files already use for the
other admitted packages; the change is additive and nothing historical was
re-pinned to a new value.

Republished mechanically by their own producers (never hand-edited):

| Artifact | SHA-256 |
| --- | --- |
| `bloc_05_time_validation.json` | `5f308aa689c26cd574169a1cc0b24b4da4663493f3026af0a5fb8181767b2237` |
| `bloc_05_semantic_validation.json` | `9347afccb7ef3d8272e80e9a945eaf6c6787fedde04d99b708798f1e5253bb70` |
| `bloc_05_replay_safety_validation.json` | `7c1fbd24a86f5654e81bdcdfb5bd1924bf85268c9fc8454771c64718cadba3ac` |
| `BLOC_05_I06_SCOPE_AUDIT.json` | `8f076bd5450bf2427ce12628daae0f5945e55220c2c471f5c1e0f4ac4bcab1cc` |

Producer results at the verified candidate: I05 86 rows / 86 pass; I06 14/14
rows plus 8/8 scope rows, exit 0, identical across two consecutive runs
(idempotent); I09 35 pass / 0 fail with `--check` exit 0 and artifact
`9347afcc...bb70`; I11R2 binding audit green.

## Invariants that must hold after this mission

| Invariant | Value |
| --- | --- |
| Approval manifest artifacts | `{}` (empty) |
| Approval manifest revoked ids | `[]` |
| Approval manifest authority | `B5_I09P2A_EMPTY_TRUST_ROOT_V1` |
| Approval manifest SHA-256 | `3d707c59fbf1fe96f28b2080811a0da189d2ad5c2859c97faa01a367c7042654` |
| `sensors/verification.py :: INTEGRATION_STATE` | `"INTEGRATION_REQUIRED"` |
| Provider approvals added | none |
| Custody-source authorization | `OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1` unresolved, not implemented |
| Trust promotion / gate / Bloc 6 | untouched |
| Merge to production | not performed |

The manifest hash is unchanged from the starting SHA, which is the mechanical
statement of "no trust was promoted by this mission". The empty manifest is
also what H03's guard is now written against, so the hardening cannot be
satisfied by quietly approving an artifact.

## Tracked inventory

1,111 tracked Python files: 157 under `quant-lab/src/`, 249 under
`quant-lab/tests/`. This matches the I11R2 pin from R5 and is unchanged by the
repairs, which edited existing modules only.

## Independent reconciliation

The mission anticipates an independent Agent 2 pass over the same candidate.
This package records the primary verification only; no independent
reconciliation has been received, and none is claimed here. The bundle is
independently re-checkable with `canonical_runner.py verify --require-anchor`
as shown in the README, which recomputes counts from the raw result stream
rather than trusting the summary.
