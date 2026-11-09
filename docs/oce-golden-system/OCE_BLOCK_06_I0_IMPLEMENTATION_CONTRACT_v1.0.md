# OCE Golden System — Block 6 B6-I0 Implementation Contract — v1.0

**Document ID:** OCE-B6-I0-CONTRACT-MD-001
**Version:** 1.0
**Stage:** `AUTHORIZED_STAGE=B6-I0`
**Base:** `5e76dc12207bf1674ff7ccd94aed0f36b12dd3e6` (tree `34fef9633a2fe496ed2bef352858b3994b91b4e2`)
**P0 ratification:** `e2aa8ac71dc9f0de4287fbcaa8a17ff127d5356f`
**Machine copy:** `OCE_BLOCK_06_I0_IMPLEMENTATION_CONTRACT_v1.0.json`
**Status:** FROZEN — OPERATOR HOLD

## 1. What B6-I0 is

B6-I0 freezes extraction decisions, API principles, and the compatibility and conformance
baseline for Book 6. Its single mapped section is `C1.S5`. Its frozen output is a contract, and
its non-goal is explicit: **extraction of code** does not happen here.

The stage therefore decides between four possible modes and selects one:

| Mode | Selected |
| --- | --- |
| governed decision artifacts only | no — a baseline needs an executable check |
| decision artifacts plus executable conformance tooling | **yes** |
| experimental interfaces | no |
| narrowly bounded code extraction | no |

Consequence: B6-I0 writes canonical decision artifacts and an offline conformance validator.
It copies **zero** source files, exports **zero** symbols, creates no package, no dependency and
no interface. `exports_at_p0 = 0` remains historical truth and the observed B6-I0 state is tracked
separately.

## 2. Frozen inputs

| Input | Identity |
| --- | --- |
| P0 construction sequence, stage `B6-I0` | `OCE_BLOCK_06_P0_CONSTRUCTION_SEQUENCE_v1.0.json` |
| P0 requirement registry | 19 rows with `future_stage = B6-I0` |
| P0 candidate register | 27 rows, none extracted here |
| P0 API firewall | 30 rows, `public_stable 0` |
| P0 failure and threat registry | 6 B6-I0 failure classes, 7 B6-I0 threats |
| P0 compatibility plan | 25 rows, all `UNPROVEN` |
| P0 provenance plan | 15 obligations |
| B5-I9 amendment | `B5-I9-AMEND-001`, protected inventory 31 paths |

## 3. Requirement bindings

Nineteen P0 requirements bind to this stage: `B6-P0-SEC-05`, `B6-P0-NP-01…08`,
`B6-P0-CLS-01…03`, `B6-P0-G16-01…04`, `B6-P0-HOLD-01`, `B6-P0-HOLD-02`, `B6-P0-PKG-01`.
Each has exactly one test node in `OCE_BLOCK_06_I0_REQUIREMENT_TEST_REGISTRY_v1.0.json`. A binding
is not a result: the registry keeps `pass_claims = 0` and execution evidence lives in the ledger.

## 4. Allowed and prohibited surfaces

Allowed: this packet under `docs/oce-golden-system` with the `OCE_BLOCK_06_I0_` prefix, the three
B6-I0 tooling scripts, the six B6-I0 test modules, and one additive workflow. Prohibited: control
plane and console sources, `oce/`, packages/distribution trees, dependency manifests, the frozen
P0 packet, the B5-I9 amendment target, and the three frozen Book 5 workflows. The validator
enforces the boundary against `5e76dc12` and re-asserts that not one P0 byte changed.

## 5. Compatibility and conformance baseline

The baseline pins an API version `1.0.0-draft`, schema version `1.0.0`, semver package format and a
structural fingerprint over the canonical compatibility rows. All 25 rows stay `UNPROVEN`: a
declaration without a discriminating test may not become `PROVEN`, and no consumer exists yet.
Unknown and unsupported versions are refused explicitly; there is no silent "latest" resolution.
The conformance vocabulary is closed to `PASS`, `FAIL`, `UNPROVEN`, `REFUSED`, and missing
evidence defaults to `UNPROVEN`, never `PASS`.

## 6. Mutation floor

The P0 stage graph declares a floor of 0 because B6-I0 was planned as contract-only. This contract
raises the floor to **12** before any result is observed, and it may never be lowered afterwards.
Each mutation must name its target, be discriminated by a named check, and be restored
byte-exactly before the pristine rerun.

## 7. Exit gate and holds

Exit requires: contract frozen, all 72 nodes green, 12 mutations discriminated, the Linux symlink
proof executed (not skipped) in CI, the amended B5-I9 gate still 41/41, the P0 validator still
green at its own head, deterministic regeneration, independent manifest verification, and a clean
tree with no scratch residue.

`READY_FOR_OPERATOR_REVIEW` is the furthest claim this stage may make. Ratification, merge,
publication, B6-I1 and the evaluation system remain held: `B6_I0_MERGE_AUTHORIZED = false`,
`B6_I1_THROUGH_B6_I9_AUTHORIZED = false`, `PACKAGE_PUBLICATION_AUTHORIZED = false`,
`POST_BOOK_6_EVALUATION_SYSTEM_AUTHORIZED = false`, `G16 = OPEN (B5I8-DF05)`, cost `$0`,
`capital.authority = none`.
