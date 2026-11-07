# OCE Golden System — B5-I9 Implementation Operator Ratification — v1.0

**Document ID:** OCE-B5-I9-IMPLEMENTATION-RATIFICATION-001
**Version:** 1.0
**Status:** `B5-I9 IMPLEMENTATION = OPERATOR_ACCEPTED — RATIFIED`
**Stage:** `AUTHORIZED_STAGE=B5-I9-RATIFICATION`
**Base:** `e81bef4335de5e222fb6647c602080a129dea543` (merged `origin/main`, PR #24)
**Implementation head:** `fe836cd7f9b2c55d58113a57f049b3ff7e970396`
**Evidence head:** `56e3c861b00bb347d0feb7a5a2b3a24b173bb91f`
**Cost:** `$0` · **Cloud/provider mutations:** 0 · **`capital.authority = none`** · Freebuff untouched

---

## 0. Status block

```
B5-I9 P0                      = OPERATOR_ACCEPTED — PLANNING FROZEN
B5-I9 IMPLEMENTATION          = OPERATOR_ACCEPTED — RATIFIED
B5-I9 COMPLETE                = true
BOOK_5 GOVERNANCE COMPLETE    = true
BOOK_6 INPUT_READY            = true (upstream evidence + ratified contract)
BOOK_6 CONTRACT_RATIFIED      = true
BOOK_6_AUTHORIZED             = false
BOOK_6_STARTED                = false
POST_BOOK_6_EVALUATION        = UNSTARTED
G16                           = OPEN (B5I8-DF05)
MERGE_AUTHORIZED              = true (PR #25 only)
REUSABLE_EXTRACTION           = NOT STARTED
WEB_VIEW                      = ABSENT
```

This record ratifies **evidence and a contract**. It authorizes no extraction, no package, no
deployment, no G16 closure, no Book 6 work and no post-Book-6 evaluation work.

---

## 1. Reality lock (re-verified from Git objects)

`origin/main` = `e81bef4335de5e222fb6647c602080a129dea543`, tree
`5fe7d38cb81ae0fdce7fdd4fe73117095fb76c0d`, commit parents
`833f7d1b9f2dfec2986fb9516d0abde06bf23dae` and
`455a8ff00a86107ac55295cb32ffbf8a330fa0c2`. PR #24 `MERGED` at `2026-11-07T15:51:42Z` with
merge commit equal to that main SHA. Frozen P0 branch `oce-book-5-i9` remains at
`455a8ff0…`. P0 `f6b5448fd2fc0785209327e0f31b6ce199bacdb5`, repair
`368c2a09dd175e9c998394a4e1577fe5e170ddb5` and ratification `455a8ff0…` are reachable from
`origin/main`. Implementation branch `oce-book-5-i9-build` local equals remote at
`56e3c861b00bb347d0feb7a5a2b3a24b173bb91f`, ahead/behind `0/0`, tracked tree clean, untracked
and ignored entries enumerated (ignored: build caches only, no evidence). `fe836cd7…` is a
direct ancestor of `56e3c861…`; the branch is not yet in `main`. PR #25 `OPEN`, draft,
unmerged, `MERGEABLE/CLEAN`, base `main`, head equal to the live branch. `origin/main` has not
advanced. No Book 6 branch, folder, test, source, package or evaluation artifact exists
(repository-wide filename scan: 0 matches on the branch diff; the workspace has none). G16
`OPEN` under `B5I8-DF05`; cost `$0`; `capital.authority = none`; Freebuff untouched.

No material divergence. The stage proceeded.

---

## 2. Complete ladder, reconstructed from Git

Fourteen first-parent commits, zero merges inside the branch, every subject unique, no
amend/squash/rebase/reset/force-push evidence (each commit's parent is the previous rung):

| # | Commit | Subject | Changed | CI at that rung |
|---|---|---|---|---|
| 1 | `c6cb15111a56f66b8675afec131e24c32465536f` | R1 generator + schema | 1 file, +900 | red (X1) |
| 2 | `f9672157afcca3daefb3941282a91b6256faf393` | R2 classify + boundary laws | 12 files, +1329 | red (X1, X3) |
| 3 | `03539ec90ddc138ef57635b1fa4f42d8b16361c0` | R3 no-platform proofs | 1 file, +103 | red (X3) |
| 4 | `2e4696838f04888895290e84b4cbd777cd7559ff` | R4 packaging + reproducibility | 2 files, +186 | red (X3) |
| 5 | `485ea1b0c8070e33b1e63294032603fc8588616e` | R5 Book 6 handoff + hold | 4 files, +291/−9 | red (X3, X4) |
| 6 | `93f7f89fcd7bb24fdb2d81a9a8346b48954c1558` | R6 CI selection + mutation + cleanup | 4 files, +608/−17 | red (X5, X6, X7) |
| 7 | `6d72729264b5898fb4da44960c34cfe7f43e185e` | X1 bytes literal + stale reference | 5 files, +7/−7 | red (X3) |
| 8 | `a927816439015691bd72e4acbb92bf33ad9e3b4f` | X2 ledger tail assertion | 1 file, +2/−1 | red (X3) |
| 9 | `afcbbc56d480a0c933e4bba333e19c8a388fc1c7` | X3 relocate library, portable newline rule | 13 files, +75/−24 (R096) | red (X4) |
| 10 | `65e691cac571b35d5de090e9d250e0cff5e63c8f` | X4 stdlib-only allowlist | 1 file, +2/−1 | red (X5) |
| 11 | `074fa4ec11afc7ec53629c1ed77312a1bc5a433e` | X5 portable newline rule in validator | 1 file, +16/−2 | red (X6) |
| 12 | `7b8cf11f7fbd59b89489f2c721356ae7906ace1d` | X6 rebuild newline helper from bytes | 1 file, +5/−7 | green |
| 13 | `fe836cd7f9b2c55d58113a57f049b3ff7e970396` | X7 pinned CI dependency set | 1 file, +5/−2 | green (implementation head) |
| 14 | `56e3c861b00bb347d0feb7a5a2b3a24b173bb91f` | EVIDENCE record | 1 docs file, +185 | green (evidence head) |

**Reconciliation of the implementation report's arithmetic.** The report said "six rungs
pushed" and then referred to X1–X7 plus two textual repairs; that was imprecise. The true
ladder is **six feature rungs (R1–R6), seven repair rungs (X1–X7) and one evidence rung** —
fourteen commits. **Nine defects** were demonstrated, not eleven: D1 non-ASCII bytes literal
(X1); D2 stale learning reference (X1); D3 ledger tail assertion (X2); D4 production-tree law
violation (X3); D5 non-portable CRLF rule (X3, completed by X5 after X5 itself silently
matched nothing); D6 stdlib-only false positive (X4); D7 the pushed syntax error in X5
(repaired by X6); D8 pinned adjacent-suite dependency (X7); D9 the two P0 observables that
said 26 where 27 is authoritative (R5). The report's "18 files" was likewise wrong: the
branch changes **25 paths** (§4). These corrections are recorded here rather than by editing
the earlier text, which stays in history unchanged.

---

## 3. Source-to-claim audit

Recomputed from the committed registry, not from the report: 51 requirements — stage_identity
6 · extraction 10 · no_platform_law 9 · packaging 9 · book6_handoff 8 · g16 4 · boundary 5;
bindings test 41 · static 4 · attestation 4 · deferred 2; states MAPPED 41 · PLANNED 8 ·
DEFERRED_WITH_OWNER 2 · BLOCKED 0 · PASS 0; 25 failure classes; 10 mutation laws; 41 planned
nodes across five files (9/7/9/8/7); 27 candidates; NP-1…NP-8. G16 `OPEN`.

The three state layers are kept distinct and are not contradictory: the **historical P0
registry state** remains `PASS 0` because those are planning states; **implementation
evidence** is recorded in the committed packet and CI artifacts; **ratification** is recorded
in this document and in the registry's new `implementation_ratification` block. A planning
`PASS` is never manufactured by implementing.

The two 26/27 defects are traceable to `B5I9-EX-01` and `B5I9-EX-09` observables, corrected in
`485ea1b0c8`. A repository-wide scan of the registry and the six deliverables finds no
remaining stale `26` claim where 27 is authoritative.

---

## 4. Changed-file boundary (25 paths)

| Class | Paths |
|---|---|
| Workflow (1) | `.github/workflows/b5-i9-factory-gate-validation.yml` |
| Tests (5) | `tests/test_b5_i9_stage_identity_and_scope.py`, `_extraction_classification`, `_no_platform_extraction`, `_packet_packaging_and_provenance`, `_book6_handoff` |
| Tooling (4) | `scripts/b5_i9_gate.py`, `scripts/b5_i9_factory_gate.py`, `scripts/b5_i9_mutation_battery.py`, `scripts/b5_i9_p0_validate.py` (modified) |
| Packet (11 files) | ten governed artifacts + `manifest.json` under `evidence/b5-i9/` |
| Documents (4) | implementation contract (modified), registry (modified), ledger (appended), implementation evidence record (new) |

Zero changes in `infrastructure/control-plane/src/`, `oce/frontend`, provider integrations,
Book 4, frozen B5-I0–I8 implementation or evidence, Sensor Fabric, broker/capital/execution
surfaces, external hosting, Book 6 surfaces or post-Book-6 evaluation work. The production
tree is byte-identical to base, so the frozen B5-I3 stage laws stay green.

**Relocation audit.** No B5-I9 module remains under `src/oce_control/` (X3 moved it; the
diff shows the file only at `scripts/`). The library is test/evidence tooling: it imports only
the standard library, exposes `Repo`, census, packet construction, named invariants and
`emit`/`diff_packet`, and no production module imports it (`grep b5_i9 src/` = 0 hits). Its
location matches the repository convention that committed gate/validator tooling lives in
`infrastructure/control-plane/scripts/`, and the dedicated workflow invokes exactly those
committed entry points.

---

## 5. Factory-gate semantics

The gate consumes the frozen candidate population from the committed census and refuses:
unknown classification, duplicate id, missing candidate, ungoverned addition, category-count
drift, authority-bearing extraction, private-API promotion, platform-internal extraction, the
prohibited candidate, unresolved dependency, operator-hold removal, Book 6 execution claim,
missing evidence, and UNKNOWN-as-success. Each of the 27 candidates carries id, source
location, classification, source-backed reason, authority effect, public/private status,
dependencies, limitation or prohibition, proposed Book 6 disposition and evidence references.
Distribution: 7 · 5 · 4 · 3 · 2 · 3 · 1 · 1 · 1. The proposed contract names future surfaces and
their prohibitions; it contains no extracted implementation (`files_copied: []`,
`public_surface_paths: []`).

---

## 6. Determinism, packaging, provenance

Two emissions from clean isolated inputs are byte-identical (file inventory, normalised bytes,
SHA-256, sizes, parsed structure); `--check` is clean. The canonical digest recomputed from the
six deliverables was `c6e8057766b0c1debb3c38d94ae764a6fdd1b5c202876b2ebd9bc98dc8a29f04` at the
implementation and evidence heads; ratification changes two deliverables, so the packet was
re-emitted deterministically and the digest is now
`4d290f088c197f638581a18f50bd4473abe3141042ecc55e420d13d0d86a2583`. The gate packet is the
implementation-stage artifact and keeps its implementation-stage status and false
completion flags; the ratified state lives in §0, the registry's
`implementation_ratification` block and this record. An
independent verifier (not the generator) re-hashed the packet: **10 declared artifacts, 10
manifest rows, 11 files** (ten artifacts plus `manifest.json`), zero hash or size mismatches —
the earlier phrase "11 artifacts" was imprecise and is corrected here. No timestamp, hostname,
username, absolute path, temporary path or environment value appears; no network or secret
access; generator and battery use the standard library only; the workflow installs the
repository's hash-locked set. Oversized-artifact refusal and scratch cleanup are exercised.

---

## 7. Tests, failure classes, mutations, regression

- B5-I9: **41 collected / 41 executed / 41 passed**, 0 failed, 0 errors, 0 skipped, 0 xfail,
  unique node ids, inventory equal to the registry, no orphans.
- 25 failure classes all bound and exercised; 10/10 mutations applied, each discriminated by a
  named invariant, each target restored byte-exact, pristine rerun green. Three discriminators
  are resolved through named invariants rather than through extra nodes because the 41-node
  inventory is frozen; each maps to the law it proves and none reddens via collection failure.
- Adjacent frozen suites: 53 nodes green (I7 evidence laws and governed change, I8 evidence
  laws, independent audit, adversarial); B5-I8 e2e 4 green; B5-I2–I5 135 green; B5-I6 9 green.
- Full-project regression is the B1-I1R workflow on the pull-request merge ref, green at both
  the implementation and evidence heads; it is the governed population for the base-versus-head
  comparison, and the branch adds no production code that could alter an existing node.

---

## 8. Exact-head CI identities (parsed, not inferred)

| Head | Workflow | Run | Suite | Job | Artifact | Size |
|---|---|---|---|---|---|---|
| `fe836cd7…` (tree `2d9d5bd3…`, merge ref `7c9dd23b…`, parents `e81bef43…`+`fe836cd7…`) | B5-I9 Factory Gate | `42407861257` | `114890872032` | `128509359450` | `b5-i9-evidence-8229bf9fe58b` (`13587244611`) | 11 656 B |
| same | B5-I8 Audit | `42407861328` | `114890872199` | — | `b5-i8-evidence-de9e15381a4d` (`13588520640`) | 7 404 B |
| same | B1-I1R | `42407861362` | — | — | — | — |
| `56e3c861…` (tree `37da5fdc…`, merge ref `1cf2a0c3…`, parents `e81bef43…`+`56e3c861…`) | B5-I9 Factory Gate | `42408473420` | `114892424766` | `128511226681` | `b5-i9-evidence-e180451760d0` (`13588711513`) | 11 660 B |
| same | B5-I8 Audit | `42408473424` | `114892424771` | — | `b5-i8-evidence-4f74da66ce88` (`13588133560`) | 7 405 B |
| same | B1-I1R | `42408473447` | — | — | — | — |

Both heads: terminal success; artifacts downloaded and parsed — 41/0/0/0 with
`zero_problems true`, adjacent 53/0/0/0, mutations `PASS` 10/10, validator `PASS` 169 checks /
96 candidate inspections / 0 failures, cleanup `cleanup_ok true` with an empty porcelain, B5-I8
40/40 at the stated tested tree, and merge-ref tree equal to the tested tree on both heads.
This ratification head's own CI is recorded append-only in PR #25 once it exists; no SHA or
identity is predicted here.

---

## 9. Defects found during ratification

| # | Defect | Evidence | Repair |
|---|---|---|---|
| D10 | registry `implementation.library` still named the pre-relocation path `src/oce_control/b5_i9_gate.py`, which does not exist | file absent; the shipped library is `scripts/b5_i9_gate.py` | corrected in this rung |
| D11 | ledger §23.1 repeated the stale library path, said "eight observations" where ten are recorded, and the implementation handoff said "18 files"/"11 artifacts" | ledger §23.1, §23.3; PR body | corrected append-only in ledger §24 and here (§2, §6) |

No frozen evidence, test, workflow or production file was altered to satisfy any probe.

---

## 10. Audit

`SAME-AGENT — NOT ORGANIZATIONALLY INDEPENDENT`

SPEC **8.4** · DESIGN **8.2** · CORRECTNESS **8.0** · QUALITY **8.1** →
(8.4 + 8.2 + 8.0 + 8.1) / 4 = **8.2 / 10**.

Correctness is unchanged in aggregate but its components moved: the behaviour is verified
end-to-end at three heads, while a dead path inside the machine-readable registry and three
narrative imprecisions were found only by this audit. Deductions remain for nine demonstrated
defects, seven repair rungs including a pushed syntax error, indirect mutation witnesses forced
by the frozen node inventory, same-agent review and G16 still open. No score was raised for
green CI.

---

## 11. Book 5 closure, derived from authority

`OCE_B5_I9_EXTRACTION_AND_PACKAGING_BOUNDARY_v1.0.md` defines *Book 5 governance complete* as
"the operator has ratified the factory gate (B5-I9 exit)", citing the Block 5 plan §7 gate
*Operator-only completion*, with this stage's ratification record as the evidence. The Block 5
plan exit gate — one narrow application specified, built, locally operated,
deployment-packaged, recovered, changed and independently verified — was satisfied by
B5-I1–I8, each `OPERATOR_ACCEPTED` and merged. The operator has now (a) reviewed the
implementation, (b) ratified the extraction scope and the correction decisions, and (c)
recorded the Book 6 handoff as **withheld**, which is the withheld branch of the contract's
exit gate. Therefore `B5-I9 COMPLETE = true` and `BOOK_5 GOVERNANCE COMPLETE = true`, while
G16 remains `OPEN` under `B5I8-DF05` as a disclosed limitation with an independent owner; it is
not a Book 5 governance blocker under the ratified definition.

Book 6 remains unauthorized: the Block 6 plan requires a fresh `AUTHORIZED_STAGE=B6-I0`. Book 5
closure grants Book 6 nothing.

---

## 12. What did not begin

No reusable software extraction (no file copied, re-exported, relabelled, packaged, published
or deployed); no Book 6 branch, folder, test, source, evidence or evaluation framework; no
post-Book-6 evaluation system; no web view; no G16 closure; no cloud, provider, telemetry,
credential, secret or recurring cost; no capital, broker or execution authority; Freebuff
untouched. `MERGE_AUTHORIZED = true` applies to **PR #25 only**, after its exact-head CI
passes, and is a merge authority, not a ratification of Book 6.
