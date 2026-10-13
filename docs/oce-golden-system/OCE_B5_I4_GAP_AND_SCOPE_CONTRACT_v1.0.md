# OCE B5-I4 Gap and Scope Contract — v1.0

**Document ID:** OCE-B5-I4-GAP-SCOPE-001
**Version:** 1.0
**Status:** FROZEN — P0 scope artifact (requirements frozen before any implementation result exists)
**Authorized stage:** `AUTHORIZED_STAGE=B5-I4`
**Base (merged main):** `9df3bf4f00a47230b42c22ce10a2d81d1591c885` (merge of PR #13; parents `674e0e78…` + `424c27d0…`)
**Branch:** `oce-book-5-i4` (fresh worktree `larger-lab-book5-i4`, created from the exact base above)
**Governing charter:** `OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md` (`OPERATOR_RATIFIED — FROZEN`, 2026-10-07)
**Governing plan:** `OCE_BLOCK_05_REFERENCE_APPLICATION_FACTORY_PLAN_v1.0.md` section 7
**Predecessor:** B5-I3 `OPERATOR_ACCEPTED` with permanent governance exception (ledger §11.11; erratum `OCE_B5_I3_POST_MERGE_GOVERNANCE_ERRATUM_v1.0.md`)

---

## 1. Stage identity derived from frozen authorities (in order)

| Authority | Provision |
|---|---|
| Block 5 plan §7 | `B5-I4 \| C3 deterministic kernel and first vertical slice \| Local real path passes` |
| Ledger §1 B5-I4 row (pre-authorization) | `B5-I4 \| C3 deterministic kernel and first vertical slice \| LOCKED \| Requires B5-I3 complete` |
| Charter §12 increment map | `I-3 → B5-I4` — "deterministic console kernel + first vertical slice (status view, S-1)"; `I-4 → B5-I4/B5-I5` — "submission and representative-job timeline (S-2)" (dual anchor) |
| Charter §12 per-increment contract, I-3 row | Purpose: build the deterministic read path. Exact scope: "CLI status view over contract-validated reads (S-1); fail-closed `STACK_UNREACHABLE`". Executable gate: "I-2 registry's S-1/G7 tests pass". Evidence output: "first vertical-slice demo record". Non-goals: "no writes, no drills, no web view". Stop condition: "any direct store read: stop — client-only, contract-mediated (Gate G3)" |
| B5-I3 construction plan §5 (merged, frozen) | Stage `I-3 — deterministic read path (plan anchor B5-I4)` owns registry entries G3 (UI half), G7 (UI half), S-1 (console half), F-1 (console half), F-5 (console half); five planned nodes verbatim in `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py` (§8 planned-node inventory) |

**Official stage title:** *C3 deterministic kernel and first vertical slice — deterministic console read path (charter increment I-3)*.

### 1.1 The I-4 dual anchor — explicit scope decision (not drift)

Charter §12 maps increment I-4 to **B5-I4/B5-I5** (a dual anchor), and the B5-I3 construction plan lists I-4's planned tests under the same dual anchor. A dual anchor means I-4 *may* be split across the two increments; it does not require any I-4 work inside B5-I4. Three authorities pin B5-I4's own identity to the *first* vertical slice, singular: plan §7 ("first vertical slice"), ledger §1 (same wording), and charter §12's I-3 row (the only increment mapped exclusively to B5-I4). Therefore:

- **B5-I4 implements charter increment I-3 exactly.**
- **I-4 (governed submission + dual-clock timeline, S-2/F-3 console halves) remains deferred in full** and may be executed at B5-I5, whose dual anchor admits it. Registry entries S-2 and F-3 keep their existing `deferred` bindings with owner `I-4`; nothing about them changes in this increment.
- This is the minimum mandated scope; implementing more would exceed "first vertical slice" and violate the charter §12 ceiling law (Gate G17). Implementing less would leave the I-3 mapped planned nodes unbuilt. The scope is **uniquely decidable: I-3 only**. No `BLOCKED_B5_I4_SCOPE_AMBIGUOUS` condition exists.

## 2. Gap statement

B5-I2 froze the console→control-plane interface contracts (12 surfaces bound to existing governed operations); B5-I3 made acceptance executable (28-entry requirement-test registry, 17 G + 4 S + 7 F, with five entries deferred to owner `I-3` carrying planned nodes in `test_b5_i4_console_kernel.py`). What does **not** exist yet:

1. **No console kernel code exists anywhere** — no CLI, no client, no status view. `git ls-files` at base contains zero `b5_i4` artifacts; `src/oce_control/` contains only the control plane itself.
2. The five I-3-owned registry deferrals (G3, G7, S-1, F-1, F-5) have planned nodes that do not collect — the registry closure is complete only as *mapping*, not as *execution*, for those ids.
3. The charter §11 gates that depend on a console surface (G3 read half, G7) have contract-level proofs (B5-I2) but no vertical-slice execution over the live API.
4. The plan §7 B5-I4 gate "Local real path passes" has never been exercised: no client has ever consumed the loopback API end to end as the operator would.

## 3. Exact scope (what B5-I4 delivers)

One new, stdlib-only client package plus its proofs — nothing else:

1. **Console kernel package** `infrastructure/console/src/oce_console/`:
   - `kernel.py` — deterministic status-view projection: loads the frozen B5-I2 contract pack read-only, enumerates the declared read surfaces, projects each governed `APIResponse` verbatim into a fixed-order status document, and renders it deterministically (identical inputs produce byte-identical output). Any unreachable or unverifiable section is rendered as an explicit gap or `STACK_UNREACHABLE` — never green, never cached, never fabricated.
   - `transport.py` — loopback-only HTTP client (stdlib `urllib`): refuses any non-loopback base URL fail-closed **before any socket I/O**; issues **GET only** on routes declared in the contract pack; maps connection failure to the fail-closed `STACK_UNREACHABLE` state; carries operator-supplied `X-OCE-Grant`/`X-OCE-Actor` headers, never mints them.
   - `cli.py` + `__main__.py` — `python -m oce_console status`: the mandatory first-release CLI interface (charter §8.1), rendering the status view; nonzero exit with `STACK_UNREACHABLE` when the local stack is unreachable.
2. **Two-sided proofs** `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py` — containing, verbatim, the five frozen planned nodes:
   - `TestClientOnlyReads::test_no_direct_store_read` (G3)
   - `TestStatusAgreement::test_status_view_matches_api_verbatim` (G7)
   - `TestStatusView::test_s1_lists_match_api_verbatim` (S-1)
   - `TestStackUnreachable::test_stack_unreachable_renders_fail_closed` (F-1)
   - `TestNoStaleGreen::test_unverifiable_gap_never_renders_green` (F-5)
   plus the additional two-sided/negative-control nodes required by the mission (§7 of the authorization), including one **real loopback vertical-slice test** (uvicorn on `127.0.0.1` ephemeral port serving the real FastAPI app over the real ControlPlaneAPI) that is the executable form of the plan §7 gate "Local real path passes".
3. **Registry execution addendum** `docs/oce-golden-system/OCE_B5_I4_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json` — binds the five I-3 deferrals to their executed nodes, referencing (never modifying) the frozen B5-I3 registry. The B5-I3 registry JSON, its suite, and every historical entry remain byte-identical.
4. **Authoritative CI selection** — one added step in the existing `.github/workflows/b1-i1r-validation.yml` mirroring the established B5-I2-X1 / B5-I3-R4 pattern: whole-file selection, frozen node floor, zero skips/failures/errors, zero duplicate node ids, orphan detection over `test_b5_i4_*.py`, outputs into the same evidence artifact.
5. **First vertical-slice demo record** `docs/oce-golden-system/OCE_B5_I4_VERTICAL_SLICE_DEMO_RECORD_v1.0.md` — the charter I-3 evidence output, recording the executed local real path (EVIDENCE rung).

## 4. Authority and boundary law (frozen)

| Boundary | Frozen value |
|---|---|
| Authority owner | The existing control plane (`ControlPlaneAPI`, `AuthorityEngine`, stores, scheduler, health) remains the sole authority. The console is a client with zero authority of its own (charter §5 rules 1–9) |
| Canonical state | Stays entirely outside the console. The console holds no durable state of any kind; it is a stateless projection of live governed reads; a fresh process re-reads authoritative state (Gate G6 by construction) |
| Deterministic kernel | `oce_console` is stdlib-only (`json`, `urllib`, `pathlib`, `argparse`, `socket`, `typing`); imports no LLM/model runtime (Gate G10), no third-party package, and **not even `oce_control`** — the client speaks only the HTTP contract. Its import closure is pinned by test |
| Client-only law (Gate G3 stop condition) | Any direct store read would stop the increment. The kernel never imports `job_store`, `worker_leases`, `pg_store`, `events`, or any store module; it reads the contract pack JSON (data) and requests only declared read routes. Proven by AST import-closure test + behavioral proof |
| Local-only topology | Base URL must be loopback (`127.0.0.1`, `::1`, `localhost`); anything else is refused fail-closed before any request (charter §6). No Vercel/Railway/external hosting, no provider, no telemetry, no cloud mutation, no capital/broker/execution path; recurring cost `$0`; `capital.authority = none` |
| Read-only slice | Transport issues GET only. No submit/cancel/retry, no drills, no session-record writes, no web view, no `oce/frontend` modification (I-4/I-5/I-6/I-7 remain unauthorized; `B5_I5_THROUGH_B5_I9 = LOCKED`) |
| No server-side change | No file under `infrastructure/control-plane/src/` or `contracts/` is touched; the frozen B5-I2 pack blob stays SHA-identical; no new server endpoint; no schema change. (The B5-I3 suite's `TestStageBoundaries`/`TestB5I2Compatibility` enforce this and must stay green unchanged) |
| UI question resolved | The "no UI before I-3" constraint merely *removed a prohibition*; what I-3 affirmatively authorizes is exactly the CLI status-view slice (charter §8.1: CLI/TUI is the mandatory first-release interface). The optional web view remains I-7, operator-directed only. No frontend/UI work beyond the CLI text surface is authorized |

## 5. Explicit non-goals (never in this increment)

- No job submission, cancel, or retry (charter I-3 non-goal "no writes"; I-4 territory).
- No dual-clock timeline, no session records, no drill playbooks, no recovery enactment (I-4/I-5/I-6).
- No web view, no TUI framework, no browser automation, no `oce/frontend` change (I-7 optional; operator-directed only).
- No new governed operation, no `jobs.list` endpoint: the governed API exposes no list-jobs read surface, so the status view renders the jobs dimension exactly as far as governed reads allow (system totals + schedules + per-job inspect on explicit request), leaving any finer job listing an **explicit gap** — never guessed, never worked around (charter §9 Progress observation; stop-condition law).
- No second state machine, no duplicate registry, no second API authority, no second evidence store; the B5-I3 registry is referenced, never rewritten.
- No provider, no hosting, no deployment configuration, no recurring cost.

## 6. Changed-file ceiling (frozen)

At most **14 paths**: 10–11 NEW (`OCE_B5_I4_GAP_AND_SCOPE_CONTRACT_v1.0.md`, `OCE_B5_I4_CONSTRUCTION_PLAN_v1.0.md`, `OCE_B5_I4_ACCEPTANCE_MATRIX_v1.0.md`, `OCE_B5_I4_FAILURE_AND_RECOVERY_MATRIX_v1.0.md`, `OCE_B5_I4_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json`, `OCE_B5_I4_VERTICAL_SLICE_DEMO_RECORD_v1.0.md`, `oce_console/__init__.py`, `oce_console/kernel.py`, `oce_console/transport.py`, `oce_console/cli.py`, `oce_console/__main__.py`, `test_b5_i4_console_kernel.py`) and exactly **2 EDITED** existing files: the Book 5 ledger (B5-I4 row at P0; evidence append at EVIDENCE) and `.github/workflows/b1-i1r-validation.yml` (one added selection step, R3). Any further file requires a recorded stop and operator decision.

## 7. Stop conditions (global and stage-specific)

- Charter I-3 stop condition verbatim: **any direct store read — stop, client-only, contract-mediated (Gate G3).**
- Any discovery that the slice requires a new server endpoint, a schema change, a control-plane modification, a write path, a non-loopback bind, an external provider, an LLM in the kernel path, or any authority the charter has not granted: stop, record, operator decides — scope never expands by drift (charter §12; Gate G17).
- Any frozen B5-I2/B5-I3 instrument found drifting (pack blob SHA, registry blob, suite floors): stop and record before any repair.

## 8. Downstream boundary

This contract freezes scope only. It is not a ratification, grants no authority beyond §3, does not authorize merge, and does not unlock B5-I5+ (`B5_I5_THROUGH_B5_I9 = LOCKED`). No acceptance, operator ratification, or self-acceptance may be claimed at any point in this stage.

---

**FROZEN under `AUTHORIZED_STAGE=B5-I4`.** Cloud mutations 0; broker mutations 0; capital mutations 0; execution mutations 0; recurring cost `$0`; `capital.authority = none`.
