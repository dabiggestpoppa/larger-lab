# OCE Golden System — B5-I9 Failure Matrix and Recovery Plan — v1.0

**Document ID:** OCE-B5-I9-FAILURE-001
**Version:** 1.0
**Status:** `B5-I9 P0 = DRAFT FOR OPERATOR REVIEW`
**Base:** `833f7d1b9f2dfec2986fb9516d0abde06bf23dae`

---

## 1. Method

A failure class is admitted only if it (a) has a trigger that can occur in this stage's
scope, (b) has a containment that a future test can observe, and (c) can be made to fail on
purpose by a named mutation. Classes without a discriminator are not listed.

**Scope honesty:** B5-I9 produces documents and one read-only validator. Its failure modes
are therefore **classification, provenance and claim-inflation** failures, plus
**premature-work** failures (a Book 6 or implementation artifact appearing). It has no
runtime failure mode, and none is claimed.

---

## 2. Failure classes (22)

| # | Class | Trigger | Expected containment | Proof (requirement) | Evidence output | Recovery |
|---|---|---|---|---|---|---|
| F01 | Private API leakage | A `PRIVATE_API`/`PLATFORM_INTERNAL` path appears in a public-surface list | Classification rejected by name; stage blocked | `B5I9-EX-03` | named path + class | Reclassify; no exception granted |
| F02 | Authority-bearing extraction | An item that decides admission/refusal/recovery is classified `EXTRACTABLE_*` | Refused; authority scan names the decision | `B5I9-EX-02` | item + decision symbol | Reclassify to `AUTHORITY_BEARING` |
| F03 | Hidden canonical-state copy | A candidate proposes a consumer-side store as canonical | Refused by charter §5 law 5 / Constitution §7.8 | `B5I9-NP-03` | path + law citation | Remove; keep single owner |
| F04 | Missing refusal law | An extractable item has no refusal path recorded | Item downgraded to `REFERENCE_ONLY` | `B5I9-EX-04` | missing field | Supply law or downgrade |
| F05 | Missing recovery law | An extractable item has no recovery/cleanup statement | Downgraded | `B5I9-EX-05` | missing field | Supply law or downgrade |
| F06 | Missing provenance | A packet artifact lacks source/tree/version identity | Validator fails | `B5I9-PK-01` | artifact + field | Add identity; no default |
| F07 | Unpinned dependency | The validator or packet depends on an unpinned third-party package | Refused; stdlib-only assertion | `B5I9-PK-07` | import name | Replace with stdlib |
| F08 | Environment-specific path or duplicated configuration truth | An absolute, host-specific or drive-qualified path appears | Refused | `B5I9-NP-06` | offending string | Repository-relative path only |
| F09 | Nondeterministic packet | Two generations differ in ordering, whitespace or newline | Refused by byte comparison | `B5I9-PK-03` | first differing offset | Sort keys, normalize LF |
| F10 | Manifest mismatch | A recorded hash or size differs from recomputation | Refused | `B5I9-PK-02` | path + recorded/observed | Regenerate; never retype |
| F11 | Stale source SHA | Packet names a commit that is not the validated head | Refused | `B5I9-SI-02` | recorded/observed | Rebind to validated head |
| F12 | Incomplete artifact set | A contract §4.2 artifact is missing | Refused | `B5I9-SI-03` | missing artifact | Add artifact |
| F13 | Oversized/unbounded artifact | An artifact exceeds the declared size rule | Refused | `B5I9-PK-06` | size | Split; no silent truncation |
| F14 | External network dependency | A network call or URL fetch appears in the validator | Refused | `B5I9-PK-09` | symbol | Remove |
| F15 | Non-loopback exposure | A host/ingress/provider binding appears in any packet claim | Refused | `B5I9-NP-07` | host string | Remove |
| F16 | Secret/credential leakage | A token-like value or credential field appears | Refused | `B5I9-PK-05` | pattern class (never the value) | Remove and rotate if real |
| F17 | Incomplete cleanup | Scratch paths or worktrees remain after the run | Refused | `B5I9-BD-05` | path | Remove |
| F18 | Non-reproducible rebuild | Second run differs from the first | Refused by digest comparison | `B5I9-PK-04` | digest pair | Fix generator |
| F19 | Evidence substitution | A claim cites an artifact that does not contain the cited fact | Refused | `B5I9-SI-04` | claim + citation | Correct the claim |
| F20 | False Book 6 readiness | `BOOK_6_AUTHORIZED`/`STARTED` true without authorization | Refused | `B5I9-HO-02` | state triple | Reset; operator decision |
| F21 | Premature Book 6 artifact | A Book 6 folder, branch, test or evidence file exists | Refused | `B5I9-HO-03` | path | Remove; record the attempt |
| F22 | G16 falsely closed | G16 reported closed or independence claimed | Refused | `B5I9-GA-01` | status string | Restore `OPEN` + `B5I8-DF05` |
| F23 | Provider/cloud assumption | A cloud, hosting or telemetry assumption appears | Refused | `B5I9-NP-09` | claim | Remove |
| F24 | Live execution authority | A broker/capital/execution surface is introduced | Refused | `B5I9-BD-02` | symbol | Remove; `capital.authority = none` |
| F25 | Premature B5-I9 implementation artifact | A B5-I9 test, source or workflow file exists at P0 | Refused; stage blocked | `B5I9-SI-05` | path | Remove; record the attempt |

25 classes are enumerated; the matrix floor is **22**, so the set exceeds its floor and no
class is padded. Every class is bound to exactly one planned node named above.

---

## 3. Mutation plan (10 mutations, floor 10)

Each mutation is applied to a **copy** of the packet or its inputs, must be discriminated
by a named proof, and must be restored byte-exactly. Cosmetic mutations (whitespace-only in
a region no proof reads, comments, renaming a variable the proof never inspects) are
rejected as non-discriminating.

| ID | Target | Change | Expected discriminator | Restoration |
|---|---|---|---|---|
| `M01` | Classification table copy | Move `job_store.py` from `PLATFORM_INTERNAL` to `EXTRACTABLE_PATTERN` | `test_private_interfaces_never_promoted` fails | Byte-exact original restored |
| `M02` | Classification table copy | Move admission path to `EXTRACTABLE_PATTERN` | `test_authority_bearing_items_are_never_extractable` fails | Restored |
| `M03` | Registry copy | Duplicate one requirement id | `test_requirement_ids_unique` fails | Restored |
| `M04` | Registry copy | Set one requirement `state = PASS` | `test_zero_pass_claims` fails | Restored |
| `M05` | Registry copy | Remove a binding from one requirement | `test_every_requirement_has_one_binding` fails | Restored |
| `M06` | Registry copy | Point a test-bound requirement at a nonexistent node | `test_every_test_requirement_maps_to_a_planned_node` fails | Restored |
| `M07` | Packet artifact copy | Replace `base_sha` with a stale commit | `test_base_sha_is_the_merged_main` fails | Restored |
| `M08` | Packet artifact copy | Insert a drive-qualified path | `test_no_environment_specific_paths` fails | Restored |
| `M09` | Locks block copy | Set `BOOK_6_AUTHORIZED = true` | `test_book6_states_remain_false` fails | Restored |
| `M10` | Locks block copy | Change `G16 = OPEN` to `CLOSED` | `test_g16_remains_open_with_owner` fails | Restored |

Each mutation is accompanied by: the mutated digest, the failing node's message, the
restored digest equal to the original, and a final pristine rerun of the whole planned
surface. A mutation that does not fail its named node is reported as a **non-discriminating
mutation**, which blocks the stage rather than being quietly dropped.

## 4. Recovery and cleanup behaviour

No mutation touches the repository: mutations operate on copies under a scratch directory
outside the tracked tree. Cleanup removes the scratch directory and asserts its absence.
If a run is interrupted, the tracked tree must be clean and every artifact byte-identical
to its committed form; the run then restarts from the committed state rather than resuming
mid-mutation.

## 5. What this plan does not claim

It does not claim that any of these proofs exist. At P0 the nodes are **named plans**; the
mutations are **planned**, not executed. Executing them requires the operator to authorize
B5-I9 implementation.
