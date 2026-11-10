# OCE Book 6 — B6-I2 Operator Ratification (templates and local harness)

Status: RATIFICATION RECORD FROZEN
Stage: B6-I2
Base: `4496d548078660efd7ad4f93e7fff461d34ea538` (B6-I1 merge)
Final governed head: `1be58fd92d04fc3040e11c074a4e602e31e4d979`
Product/governed implementation head: `18e7d6be134c9fab62685ff5254185a5c109d26d` (tree `eccdd93cf070143af71592c8739c0d1f7f35d7ec`)
Prior packet heads: B6-I0 `c5d7bfcc5ea99837985ba82a3c91fd1e76d85a81`; B6-I1 `96e3b81714321f4eea7abcb300ef471e93be0962`
Cost: `$0`; capital authority: `none`; G16: OPEN (owner B5I8-DF05)

## 1. What was accepted

The B6-I2 boundary — templates and the local harness under C1.S3 and C1.S4 — with the
proof-closure amendment applied. The stage exit gate is *fresh generated app starts locally*.
It is now proven by an executable start, not by file inspection: the generated app emits
`app/__main__.py`, prints `READY app`, accepts a `stop` line, prints `STOPPED` and exits 0 within a
15-second bound; a second run is identical; no socket, no network module, no cloud dependency.
Unresolved compatibility windows remain declared rather than claimed.

## 2. Proof-closure amendment

`OCE_BLOCK_06_I2_PROOF_CLOSURE_AMENDMENT_v1.0.json` (frozen at `e082609e9`) supersedes exactly two
frozen clauses, both disclosed:

- `IMPLEMENTATION_CONTRACT_v1.0.template.start`: in-process inspection → subprocess execution with
  readiness, timeout, orderly stop and exit 0.
- `ACCOUNTING_CORRECTION_v1.0.authoritative_mutation_population`: 13-row population → 12 governed
  mutations plus one POSIX environmental probe.

It also records the compatibility dispositions and the prior-stage preservation rule. No floor was
lowered: 30 nodes, 6 stage mutations, 12 B6-I0 governed mutations, 208 common nodes.

## 3. M13 final classification

M13 (symlink over a B6-I0 packet artifact) is a POSIX environmental probe, excluded from the
governed mutation population. In Linux CI it reported `observed_checks: []` and
`discriminated: false`: the validator aborted on `packet/canonical/...` before it could reach
`boundary/no_symlinked_artifacts`. Required precedence for any future validator is that a symlink
refusal precedes content, canonical and digest checks on the same artifact. The B6-I0 battery
therefore reports 13 physical rows, 12 governed discriminations and 13 restorations, and passes on
the frozen floor of 12. The POSIX symlink refusal itself is proven separately on the B6-I2 archive
surface (`test_symlink_escape_refused`) in Linux CI.

## 4. Local-start evidence

Node: `test_block_06_i2_templates.py::test_generated_app_starts_locally`.

- fresh empty destination; install refuses a dirty destination (`REFUSED_DIRTY_INPUT`);
- byte-identical double build; generated files written before any start;
- subprocess `python -E -s app/__main__.py` with `PYTHONPATH` removed;
- readiness `READY app`, shutdown `STOPPED`, exit 0, bounded 15-second timeout, kill-and-refuse on
  timeout (`REFUSED_START_TIMEOUT`);
- second run yields the same digest; no `.pyc` residue; entrypoint scanned for socket/urllib/http;
- tampered artifact refused (`REFUSED_INVALID_MANIFEST`), cloud claim refused (`REFUSED_CLOUD`).

## 5. Compatibility dispositions

- C1.S3 (templates): UNPROVEN_BUT_EXIT_GATE_ALLOWS, owner B6-I7. The exit gate proves a local
  start, not a published v1 support window.
- C1.S4 (local harness): UNPROVEN_BUT_EXIT_GATE_ALLOWS, owner B6-I7. The harness is exercised
  in-process for local/minimal profiles; a fresh-machine consumer window is not this gate.

Neither row is flipped to proven, and no consumer evidence is invented.

## 6. Prior-stage preservation

Both adapted prior-stage test files are restored byte-identical to `4496d548`; the I2 validator
asserts it mechanically. The B6-I0 and B6-I1 workflows now create a detached worktree at
`96e3b817` and rewind `origin/main` to `6783bf76` before running every prior-stage step there, so
the prior suites execute against their own history rather than the later head.

- B6-I0: 72/72 nodes, zero failures/errors/skips, validator PASS 136/136.
- B6-I1: 42/42 nodes, zero failures/errors/skips.
- B6-I0 battery: floor 12, 12 governed discriminated, 13 restored, pristine rerun green.
- B6-I1 battery: 6/6 discriminated and restored.

## 7. Resolver authority sets

- `i0`: empty authority; strict replay unchanged.
- `i1` (resolved at the prior merge): exact B6-I1 allowed paths plus the pinned B6-I0 amendment
  surfaces; no `oce/templates/` or `oce/harness/`.
- `i2`: `i1` law plus the B6-I2 registration prefixes and pinned I2 surfaces; the only production
  additions are `oce/templates/` and `oce/harness/`.
- No later-stage path is inherited; a branch rename cannot spoof identity; an I3 artifact is
  refused (`stage/later_stage_absent`); a missing registration is refused; controls 15/15.

## 8. Mutation and test totals

- B6-I2: 30 declared = 30 collected = 30 unique, 6/6 modules, 0 failures/errors/skips, rc 0.
- B6-I2 mutations: floor 6, 6/6 discriminated, 6/6 restored, pristine rerun green.
- B6-I2 validator: PASS 168/168. Manifest: 9 artifacts + 7 code files recomputed.
- B6-I0 validator at the B6-I2 head: PASS 136. B6-I1 validator: PASS 168.

## 9. Paired comparison

Base `4496d548` (tree `c6638bde`) → head `18e7d6be` (tree `eccdd93c`): PASS, 20 checks,
270 common nodes, 0 base-only, 270 common passes, 30 head-only green, 0 regressions, identical
dependency surface, cleanup before PASS (run `42809713955`).

## 10. Exact-head CI (head `1be58fd9`)

B6-I2 Validation `42809713938`; B6-I2 Paired `42809713955`; B6-I0 Validation `42809714005`;
B6-I1 Validation `42809713956`; B6-I0 Paired `42809713929`; B6-I1 Paired `42809714015`;
B5-I9 Gate `42809713932`; B5-I9 Paired `42809714016`; B5-I8 `42809714160`; B1-I1R `42809714019`.
All ten terminal SUCCESS on this head.

Failed runs remain visible: `42808974403` and `42808974599` (first replay attempt ran the validator
and battery outside the replay worktree) and the earlier `X1`–`X6` repairs. `X7F` is the repair.

## 11. Ladder

`f1fed54c8` P0 → `fc47388e3` → `47be5fbc3` → `4eb14659c` → `fa685ec1e` → `a980434b9` →
`ed7e5f885` → `5e5fac153` → `ec51b8633` → `9048d85b2` → `6b8d90ddb` → `25b5debd1` →
`696472da0` → `77f1c0f5b` → `09012f3a3` → `e082609e9` → `4417a7f26` → `edbd96c51` →
`cf0b7e8f0` → `16bbe2dcc` → `3ebc8b006` → `0060230f9` → `463aff225` → `18e7d6be1` →
`1be58fd92`. Append-only; no amend, squash, rebase or force.

## 12. Audit

SAME-AGENT — NOT ORGANIZATIONALLY INDEPENDENT.
SPEC 8/10, DESIGN 8/10, CORRECTNESS 8/10, QUALITY 8/10 → 8.0. The exit-gate repair and the M13
arithmetic correction each add one point over the prior 7.75; the replay tooling churn and the
still-unproven compatibility rows hold each dimension at 8.

## 13. Limitations

Same-agent authorship and audit; POSIX-only symlink proof (Windows skips two I0 nodes); C1.S3 and
C1.S4 remain unproven with named owners; G16 OPEN; prior-stage replay depends on the pinned heads
(`96e3b817`, `6783bf76`) and is exercised only in CI; merge-ref evidence identity differs from the
branch head by construction.

## 14. Locks

B6-I3 through B6-I9 remain LOCKED; Book 6 is not complete; no package publication, evaluation
system, cloud hosting, provider, broker, capital or execution authority was created. Merge
authority is granted only for PR #31.
