# OCE Golden System — B5-I9 Implementation Evidence Record — v1.0

**Document ID:** OCE-B5-I9-EVIDENCE-001
**Version:** 1.0
**Status:** `B5-I9 IMPLEMENTATION = IMPLEMENTED — PENDING OPERATOR REVIEW`
**Stage:** `AUTHORIZED_STAGE=B5-I9-IMPLEMENTATION`
**Base:** `e81bef4335de5e222fb6647c602080a129dea543` (merged `origin/main`, PR #24)
**Cost:** `$0` · **Cloud/provider mutations:** 0 · **`capital.authority = none`** · Freebuff untouched

---

## 1. Reality lock (verified before editing)

`origin/main` = `e81bef4335de5e222fb6647c602080a129dea543`; PR #24 `MERGED` at
`2026-11-07T15:51:42Z` with parents `833f7d1b9f2dfec2986fb9516d0abde06bf23dae` and
`455a8ff00a86107ac55295cb32ffbf8a330fa0c2`, merge tree
`5fe7d38cb81ae0fdce7fdd4fe73117095fb76c0d` equal to the ratification-head tree;
`oce-book-5-i9` retained at `455a8ff0…`; P0 `f6b5448fd2fc0785209327e0f31b6ce199bacdb5`;
repair `368c2a09dd175e9c998394a4e1577fe5e170ddb5`; ratification `455a8ff0…`; all reachable
from `origin/main`; the implementation worktree was clean with no unpublished commits; no
B5-I9 test, source or workflow artifact existed; no Book 6 branch, folder, test, source or
evidence artifact existed; G16 `OPEN`; cost `$0`; `capital.authority = none`. No divergence
was found, so the stage proceeded.

## 2. Contract re-derived, not assumed

The merged P0 packet was re-read in full (contract, boundary, registry, acceptance matrix,
failure matrix, construction plan, ratification record, ledger) and the counts were
recomputed independently and matched: **51 requirements** — stage_identity 6, extraction 10,
no_platform_law 9, packaging 9, book6_handoff 8, g16 4, boundary 5; bindings test 41, static
4, attestation 4, deferred 2; states MAPPED 41, PLANNED 8, DEFERRED_WITH_OWNER 2, BLOCKED 0,
PASS 0; **27 candidates** in nine classes; **25 failure classes** (floor 22); **10 mutations**
(floor 10); NP-1…NP-8 plus NP-9; `G16 OPEN (B5I8-DF05)`; Book 6 input-ready `true` only in
the narrow upstream-evidence sense, never authorized. Two residual defects were found in the
frozen packet and repaired forward (§5, D3).

## 3. What this stage implemented

| Surface | Path | Content |
|---|---|---|
| Gate library | `infrastructure/control-plane/scripts/b5_i9_gate.py` | census, packet construction, manifest, determinism, ten named invariants |
| Generator | `infrastructure/control-plane/scripts/b5_i9_factory_gate.py` | `--emit`, `--check`, `--json`; repository-relative, offline, stdlib-only |
| Mutation battery | `infrastructure/control-plane/scripts/b5_i9_mutation_battery.py` | the 10 frozen mutations on copies, byte-exact restoration, pristine rerun |
| Validator | `infrastructure/control-plane/scripts/b5_i9_p0_validate.py` | stage-aware; every P0 check retained, packet/selection/battery/reproduction added |
| Proof surface | `infrastructure/control-plane/tests/test_b5_i9_*.py` | exactly the 41 frozen nodes across the five planned files |
| Packet | `infrastructure/control-plane/evidence/b5-i9/` | 11 artifacts: gate packet, census, learning closure, handoff contract, input readiness, provenance, operator hold, reproduction, G16 limitation, validation, manifest |
| Selection | `.github/workflows/b5-i9-factory-gate-validation.yml` | 13 steps, pinned actions, `contents: read`, evidence artifact |

The gate executes against the frozen candidate population, produces the learning closure and
the proposed Book 6 extraction contract, proves deterministic packaging, provenance, refusal
behaviour and boundary closure, and demonstrates that nothing authority-bearing, private,
platform-internal or prohibited is consumable. It extracts nothing: `files_copied: []`,
`public_surface_paths: []`, `contains_extracted_source: false`.

## 4. Exact-head CI identity (implementation head)

Implementation head `fe836cd7f9b2c55d58113a57f049b3ff7e970396`, tree
`2d9d5bd30d84a65fa9a41ec74ecfc67be6f4ca86`. Pull-request merge ref
`7c9dd23b287ff03065d8ad1782f3ba071240ab8c` with first parent
`e81bef4335de5e222fb6647c602080a129dea543` and second parent `fe836cd7…`; merge-ref tree
`2d9d5bd3…` equals the tested tree, so tree identity and second-parent identity are both
proven. Event `pull_request`.

| Workflow | Run | Suite | Job | Artifact | Size | Expires |
|---|---|---|---|---|---|---|
| B5-I9 Factory Gate Validation | `42407861257` | `114890872032` | `128509359450` | `b5-i9-evidence-8229bf9fe58b` (`13587244611`) | 11 656 B | 2026-12-07T19:48:33Z |
| B5-I8 Audit Validation | `42407861328` | `114890872199` | — | `b5-i8-evidence-de9e15381a4d` (`13588520640`) | 7 404 B | 2026-12-07T19:49:04Z |
| B1-I1R Validation | `42407861362` | — | — | — | — | — |

### 4.1 Artifact content (downloaded and parsed, not inferred from a badge)

- B5-I9 totals: `tests 41`, `failures 0`, `errors 0`, `skipped 0`, `rc 0`,
  `collected_equals_executed true`, `zero_problems true`.
- Adjacent frozen Book 5 suites in the same run: `tests 53`, `failures 0`, `errors 0`,
  `skipped 0`.
- Mutations: `verdict PASS`, `mutations_total 10`, `discriminated 10`, `applied 10`,
  `restored_byte_exact true`, `pristine_green true`, `packet_deterministic true`.
- Validator inside CI: `status PASS`, `mandatory_checks 169`, `candidate_inspections 96`,
  `failures 0`, `packet_digest c6e8057766b0c1debb3c38d94ae764a6fdd1b5c202876b2ebd9bc98dc8a29f04`.
- Cleanup: `cleanup_ok true`, `tracked_tree_clean true`, `scratch_residue []`,
  `status_porcelain ""`.
- Identity: `tested_sha` = merge ref, `tested_tree` = merge tree, `tree_identity_proven true`.
- B5-I8 proof: `collected 40`, `executed 40`, `passed 40`, `tested_tree 2d9d5bd3…`,
  `pr_head_sha fe836cd7…`.
- B1-I1R on this head: `success`.

## 5. Local exact-tree verification (before the evidence commit)

| Check | Result |
|---|---|
| P0 validator | PASS — 169 mandatory checks, 96 candidate inspections, 0 failures, self-check stable |
| B5-I9 nodes | 41 collected / 41 executed / 41 passed, 0 fail, 0 error, 0 skip, 0 xfail |
| Frozen mutations | 10/10 discriminated, 10 applied, byte-exact restoration, pristine rerun green |
| Classification arithmetic | 27 rows: 7 / 5 / 4 / 3 / 2 / 3 / 1 / 1 / 1 |
| No-platform laws | NP-1…NP-8 green as structural proofs over the proposed contract |
| Packet determinism | byte-identical across two isolated directories; `--check` clean |
| Manifest | 11 rows recomputed from LF-normalised bytes; hashes and sizes equal |
| Size rule | every artifact ≤ 262 144 B; an oversized synthetic artifact is refused |
| Frozen B5-I3 laws | 51/51 green — the production tree is byte-identical to its base |
| Adjacent B5-I7/I8 suites | 53 passed |
| Secret scan | clean; no token pattern in packet, library or scripts |
| Compilation | all changed Python files compile |
| YAML | workflow parses; 13 steps |
| `git diff --check` | clean |
| Cleanup | clean tree, no scratch residue |

## 6. Defects found and repaired forward

No defect was manufactured: each row is a real failure observed in a run.

| # | Defect | Repair |
|---|---|---|
| D1 | a bytes literal carried a literal em dash (SyntaxError) and the learning closure cited a rung that did not exist | `B5-I9-X1` |
| D2 | the ledger node asserted `endswith()` on a token that a closing fence follows | `B5-I9-X2` |
| D3 | two P0 observable strings said 26 where the table, arithmetic and total say 27 | `B5-I9-R5` (records only; ids, bindings and states unchanged) |
| D4 | the frozen style rule required CRLF bytes, unsatisfiable in a Linux checkout whose blobs are LF | `B5-I9-X3`, `B5-I9-X5`, `B5-I9-X6` |
| D5 | a frozen B5-I3 law forbids adding any module under `src/oce_control/`, which three proofs caught | `B5-I9-X3` relocated the library to `scripts/` |
| D6 | the stdlib-only check classified the repository's own gate module as external | `B5-I9-X4` |
| D7 | an attempted validator repair silently matched nothing, leaving CI red on a stale rule | `B5-I9-X5` |
| D8 | that repair wrote a real carriage return into the helper and broke the validator; the broken rung was pushed and preserved | `B5-I9-X6` rebuilt it from byte values |
| D9 | the adjacent governed-change drill needs the control-plane runtime | `B5-I9-X7` installs the repository's hash-locked CI set |

The failed rungs and the red CI runs remain in history; none were rewritten.

## 7. Learning closure

Ten observations are recorded in `learning-closure.json`, each with its consequence,
correction and disposition: the validator's stage-scoped boundary checks (L01); the
`book6-`/`b6-` filename rule false-positives on the frozen planned surface (L02, L07); the
frozen 41-node inventory forbids adding mutation discriminators as nodes (L03); the 26/27
observable defect (L04); the packet-side environment-path obligation (L05); the class-count
guard (L06); the validator's node-versus-mutation comparison defect (L08); CRLF as a checkout
artefact rather than a law (L09); and the production-tree law forcing the library out of
`src/` (L10). No observation is discarded.

## 8. Audit and honest limitations

`SAME-AGENT — NOT ORGANIZATIONALLY INDEPENDENT`.

| Dimension | Score | Basis |
|---|---|---|
| SPEC | 8.4 | every frozen count and identifier reproduced; two P0 text defects found |
| DESIGN | 8.2 | one canonical source, named invariants, stage-aware validator; battery resolves discriminators indirectly because the node inventory is frozen |
| CORRECTNESS | 8.1 | everything claimed was executed and artifact-parsed; nine repairable defects surfaced, one of them a pushed syntax error |
| QUALITY | 8.1 | deterministic, offline, stdlib-only, bounded; churn across nine repair rungs is visible |

Total = (8.4 + 8.2 + 8.1 + 8.1) / 4 = **8.2 / 10**.

Limitations carried, not hidden:

- **G16 remains OPEN** under `B5I8-DF05`; an independent operator must repeat the usability
  measurement. Same-agent evidence never becomes independent evidence.
- **B5-I9 implementation does not authorize Book 6.** `BOOK_6_AUTHORIZED = false`,
  `BOOK_6_STARTED = false`; no Book 6 artifact exists.
- **No reusable software extraction has occurred.** Nothing was copied, re-exported,
  packaged, published or deployed.
- **The post-Book-6 rigorous evaluation system has not begun**
  (`POST_BOOK_6_EVALUATION = UNSTARTED`).
- **B5-I9 is not complete.** `B5-I9 COMPLETE = false`, `BOOK_5 GOVERNANCE COMPLETE = false`;
  completion is operator-only.
- Four static and four attestation requirements remain non-machine-checkable; the census
  classifications remain judgements with stated reasons.
- CI artifacts expire after 30 days; the identities above are the durable record.

## 9. Locks and accounting

```
B5-I9 IMPLEMENTATION          = IMPLEMENTED — PENDING OPERATOR REVIEW
B5-I9 COMPLETE                = false
BOOK_5 GOVERNANCE COMPLETE    = false
BOOK_6 INPUT_READY            = true (upstream evidence only)
BOOK_6 CONTRACT_RATIFIED      = true
BOOK_6_AUTHORIZED             = false
BOOK_6_STARTED                = false
POST_BOOK_6_EVALUATION        = UNSTARTED
G16                           = OPEN (B5I8-DF05)
MERGE_AUTHORIZED              = false
RATIFICATION_AUTHORIZED       = false
CAPITAL_AUTHORITY             = none
RECURRING_COST                = $0
WEB_VIEW                      = ABSENT
```

This commit is documentation and evidence only. It changes no test, source, workflow or
packet byte.
