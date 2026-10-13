# OCE B5-I4 Construction Plan — v1.0

> **Book 5 increment:** B5-I4 (charter increment I-3, plan anchor `B5-I4`)
> **Derived from:** Block 5 plan §7 row `B5-I4` — *C3 deterministic kernel and first vertical slice*;
> charter §12 per-increment contract row I-3; B5-I3 construction plan §5 stage `I-3`.
> **Gate:** plan §7 — *Local real path passes*; charter §12 I-3 — *I-2 registry's S-1/G7 tests pass*.
> **Status:** planning only, frozen at P0 before any implementation result exists.
> **Scope contract:** `OCE_B5_I4_GAP_AND_SCOPE_CONTRACT_v1.0.md` (§1.1 records the explicit
> I-4 dual-anchor decision: I-4 remains fully deferred to B5-I5).

---

## 1. Objective and boundary

Build the deterministic console read path — a stdlib-only, loopback-only CLI status view over
the frozen B5-I2 contract pack's declared read surfaces — and prove it two-sidedly in
authoritative CI, discharging the five I-3-owned deferrals in the frozen B5-I3 registry
(G3 UI half, G7 UI half, S-1 console half, F-1 console half, F-5 console half).

**Stop rule (global):** if any rung discovers its work requires authority the charter has not
granted (new endpoint, schema change, control-plane modification, write path, non-loopback
bind, external provider, LLM-required kernel behavior, new job type), the rung stops and the
operator decides — scope never expands by drift (charter §12 stop conditions; Gate G17).

## 2. Grants (all rungs)

- **New grants: NONE.** The slice consumes the frozen B5-I2 contract pack and the existing
  loopback HTTP API only. No new governed operation, no new server endpoint, no schema change,
  no control-plane file modified.
- **Capital / broker / execution authority:** NONE (ledger §6; charter exit states).
- **External hosting / cloud / provider / telemetry:** NONE — loopback-only, local-first (A-003).
- **LLM:** never required; the kernel imports no model runtime (Gate G10), import-closure pinned by test.
- **Reuse law:** the console is a client; canonical state stays in the control plane; the B5-I2
  pack is consumed read-only, never duplicated or edited; the B5-I3 registry is referenced,
  never rewritten.

## 3. Budgets (all rungs)

- Recurring cost: **$0** (Gate G13). Increment ceiling: I-1/I-2 spent, I-3 executed here,
  I-4–I-8 remain (charter §12 ceiling accounting; Gate G17 — never more than 8).
- Changed-file ceiling: ≤14 paths, exactly 2 edited existing files (scope contract §6).
- Test budget: every landed node is whole-file selected by the authoritative workflow with a
  frozen floor, zero skips/failures/errors, zero duplicate node ids — a test CI does not
  select does not count as proven (B5-I3 R4 pattern).

## 4. Dependency graph

```
B5-I2 contract pack (frozen, OPERATOR_ACCEPTED) ──► B5-I3 registry + plan (frozen) ──► B5-I4 (I-3)
                                                                                          │
                                                                                          ├─► I-4 (S-2, F-3) → B5-I5
                                                                                          ├─► I-5 (G9, F-4) → B5-I5
                                                                                          └─► I-6 … → B5-I5/I6
```

Stage inputs are exactly: the B5-I2 pack, the five I-3 registry deferrals with their planned
nodes, and the charter §12 I-3 contract row. Nothing else may be pulled forward.

## 5. Rungs (staged commit discipline, mirror of B5-I2/B5-I3)

| Rung | Commit class | Content | Checks before commit |
|---|---|---|---|
| P0 | `B5-I4-P0: freeze authorized increment contract and acceptance` | This plan, the gap/scope contract, acceptance matrix, failure/recovery matrix; ledger B5-I4 row LOCKED → IN_PROGRESS | docs only; `git diff --check`; no code touched |
| R1 | `B5-I4-R1: deterministic console kernel and loopback-only transport` | `infrastructure/console/src/oce_console/{__init__.py,kernel.py,transport.py}` | ruff/compile on touched files; focused smoke (module imports, refusal paths) |
| R2 | `B5-I4-R2: CLI status view entry point` | `oce_console/{cli.py,__main__.py}` | compile; CLI `--help` + unreachable-stack fail-closed smoke |
| R3 | `B5-I4-R3: two-sided console-kernel proofs with negative controls` | `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py` (verbatim planned nodes + two-sided matrix + demonstrated negative controls), `OCE_B5_I4_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json`, one added CI selection step in `b1-i1r-validation.yml` | whole new suite green locally (zero skips); B5-I2/B5-I3 suites unchanged-green; `git diff --check`; workflow step mirrors the frozen B5-I3-R4 pattern exactly |
| Xn | only for demonstrated defects | append-only repair commits | re-run the failing proof plus adjacent suites |
| EVIDENCE | `B5-I4-EVIDENCE: record first vertical-slice evidence` (docs-only) | ledger §12 append with real SHAs/run ids; `OCE_B5_I4_VERTICAL_SLICE_DEMO_RECORD_v1.0.md` | implementation-head CI already green; evidence commit gets its own exact-head CI |

No amend, no rebase, no force-push, no committed-red false green; every pushed rung's SHA is
read back from Git after push, never predicted or pre-written into evidence.

## 6. Planned node inventory (frozen: the five I-3 deferrals, verbatim from B5-I3 plan §8)

| Owner | Planned node (must exist exactly) |
|---|---|
| I-3 | `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py::TestClientOnlyReads::test_no_direct_store_read` |
| I-3 | `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py::TestStatusAgreement::test_status_view_matches_api_verbatim` |
| I-3 | `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py::TestStatusView::test_s1_lists_match_api_verbatim` |
| I-3 | `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py::TestStackUnreachable::test_stack_unreachable_renders_fail_closed` |
| I-3 | `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py::TestNoStaleGreen::test_unverifiable_gap_never_renders_green` |

Additional nodes (same file, named by this plan, floor frozen at R3): loopback-only refusal of
hostile non-loopback base URLs (before any socket I/O); GET-only transport (no write verb
exists); contract-pack-route-only requests; malformed/missing-input refusal; denial rendered
verbatim without silent retry; determinism (byte-identical rerender); import-closure pin
(stdlib-only, no `oce_control` import); restart/statelessness (fresh process re-reads, no
cache); a real loopback vertical-slice test (uvicorn on `127.0.0.1` ephemeral port serving the
real FastAPI app) proving "local real path passes"; and demonstrated negative controls that
turn red under a genuinely weakened implementation (loopback guard removed, fail-closed
fallback replaced by stale-green, verbatim projection mutated) and green when restored.

## 7. CI selection plan (R3)

One added step in the existing `.github/workflows/b1-i1r-validation.yml`, mirroring the
B5-I2-X1 / B5-I3-R4 repair pattern *exactly*: no new workflow, no trigger change, no branch
protection change, no shared-runner change. Whole-file selection of
`test_b5_i4_console_kernel.py`; frozen floor = this file's node count; collection set == JUnit
set; zero duplicate full node ids; zero failures/errors/skips; every JUnit case inside the
B5-I4 module; orphan detection over `test_b5_i4_*.py`; tracked-tree-clean check; outputs into
the same evidence artifact bound to run id + tested checkout.

## 8. Evidence plan

- Rungs P0–R3: normal fast-forward pushes; SHA recorded from Git after each push.
- Implementation head: exact-head CI run id + parsed artifact (JUnit totals, registry proof
  JSON) recorded in the EVIDENCE commit and PR body — never badge-inferred.
- EVIDENCE (docs-only): ledger §12 append (real SHAs, run ids, totals, audit scores) + the
  vertical-slice demo record (charter I-3 evidence output). Evidence head gets its own
  exact-head CI; its run id goes in the PR body and final report only — never into another
  commit (self-reference failure class avoided per mission §11).
- This plan and its matrices freeze the requirements before any implementation result exists.

## 9. What this plan may not do

- May not authorize any later increment (fresh `AUTHORIZED_STAGE` per stage, operator only).
- May not weaken, skip or reorder charter gates (charter §13: strengthening only, by amendment).
- May not add requirements beyond the 28 registry ids (charter non-goal: no tests for
  unproposed features) or discharge any deferral other than the five owned by I-3.
- May not merge B5-I4 itself (draft PR, `NOT MERGE AUTHORIZED`), claim operator ratification,
  set `OPERATOR_ACCEPTED`, or unlock B5-I5+.
