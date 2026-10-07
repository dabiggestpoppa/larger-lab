# OCE Golden System
## B5-I1 — Evidence Packet: CAND-002

**Document ID:** OCE-B5-I1-PACKET-CAND-002
**Version:** 1.0
**Status:** INTAKE_EVIDENCE — UNSCORED
**Candidate identifier:** CAND-002
**Working name (register-only):** Test-Claim Reconciler
**Governing protocol:** `OCE_B5_I0_SELECTION_PROTOCOL_v1.0.md` (OPERATOR_RATIFIED — FROZEN)

---

## 1. Observable operator outcome

`AUTHORED_SPEC` — The operator asks "do the test counts claimed in our governance documents match reality?" and runs one local command that executes the declared Python test suites, records a canonical run manifest (collected/passed/failed/skipped per suite), and prints a reconciliation table: every claimed count found in the corpus vs the measured count, with `MATCH`/`DRIFT`/`CLAIM_NOT_FOUND` dispositions. Success is judgeable from the table (protocol C1).

Basis: `REPO_ASSET` — three real suites exist (`srrs_opc/tests/` 9 files; `infrastructure/control-plane/tests/` ~24 files; `oce/backend/tests/` ~20 files) and governance documents carry count claims (e.g., AGENTS.md phase table, B5-I0 artifacts, Book 4 evidence sections). Claim drift is a demonstrated failure mode in this program's history.

## 2. Operator-testable acceptance scenarios

`AUTHORED_SPEC` —

1. S-1 (clean reconciliation): run all three suites; manifest records exact pytest counts; reconciliation table lists every corpus count claim with `MATCH` or an explicit, quoted `DRIFT (claimed 39, measured 41)` line; no silent omissions.
2. S-2 (failing suite): a deliberately broken scratch test causes measured `1 failed`; the manifest records it, disposition shows `DRIFT`, exit code reflects failure, and the report states the failing test's node id verbatim.
3. S-3 (claim without measurement): a document claims a suite the manifest did not run (excluded by scope); row shows `CLAIM_NOT_FOUND — not in run scope`, never inferred as passing.
4. S-4 (determinism): two consecutive runs on an unchanged tree produce identical manifests (modulo timestamps, which are recorded per-run, not compared).

## 3. OCE lifecycle coverage matrix

`AUTHORED_SPEC` —

| OCE surface | Exercised by CAND-002 |
|---|---|
| Intent | Operator declares run scope (which suites, which claim sources) as bounded intent. |
| Planning | Execution plan: suite order, dependency setup (test deps), timeout budgets. |
| Grants | Process-execution grant per suite path; denial envelope for out-of-scope paths. |
| Workers | Each suite executes as a job with lease/heartbeat and structured result record. |
| Artifacts | Manifest + raw pytest output stored as digest-referenced artifacts. |
| Evidence | Reconciliation table is manifest-shaped: claim source, claimed value, measured value, disposition. |
| Review | Operator sees MATCH/DRIFT table; no agent narrative required. |
| Identity | Run bound to worker identity; manifest records producer identity. |
| Packaging | Local CLI + suite manifest file; no cloud packaging. |
| Observability | Per-suite duration, collected/pass/fail counts, environment versions in header. |
| Recovery | Interrupted run resumes per-suite; incomplete manifests are marked partial and never reconciled as complete. |

## 4. Deterministic-kernel boundary

`AUTHORED_SPEC` — Deterministic core: suite manifest parsing, pytest result parsing (`-p no:cacheprovider --json`-style structured output or exit/tap parsing), claim extraction from corpus via fixed patterns (e.g., `(\d+) tests? (passing|green|pass)`), reconciliation comparison, table rendering. Fixed tree + fixed suite set → fixed manifest content (timestamps excepted). LLM-permitted surfaces: none required; claim extraction is pattern-based, not model-based, to keep the kernel deterministic.

## 5. Bounded input inventory

`AUTHORED_SPEC` grounded on `REPO_ASSET`:

| Input | Path/bounds |
|---|---|
| Suite definitions | Fixed list: `srrs_opc/tests/`, `infrastructure/control-plane/tests/`, `oce/backend/tests/` (paths and per-suite env/dep notes recorded) |
| Claim corpus | `docs/oce-golden-system/*.md`, `AGENTS.md`, `infrastructure/control-plane/B4-*.md` (fixed file list at intake) |
| Test execution | Local pytest over the existing checkout; no network (dependency install handled by existing repo requirements, executed only if the operator's environment already provides them) |

Unbounded ingestion: none. Suite set is closed; adding a suite is a governed change (§11).

## 6. Canonical-state proposal

`AUTHORED_SPEC` — State = run manifest: `{run_id, tree_head_sha, suite_results[{suite, exit_code, collected, passed, failed, skipped, duration_s, raw_output_ref}], complete}` as an append-only JSON file per run; reconciliation results reference manifest + claim locations. No database; replayable from stored raw output refs.

## 7. Local-run topology

`AUTHORED_SPEC` — Local Python CLI; executes pytest as subprocesses against the local checkout; writes only `runs/` output. No external services. Control-plane suites that require compose services (B2/B3 compose tests) are marked `requires_local_compose` in the suite manifest and run only when the operator's flag includes them; default scope is the compose-free set, recorded explicitly either way.

## 8. Explainable-output example

`AUTHORED_SPEC` — Format demonstration (not a measurement):

```
CAND-002 run r-0001  head=f8988347…  suites=3
  srrs_opc/tests            exit 0  collected 39  passed 39  failed 0  42.1s
  oce/backend/tests         exit 0  collected 214 passed 214 failed 0  88.0s
  control-plane/tests       exit 0  collected 197 passed 197 failed 0  121.3s
  claims:
    AGENTS.md:24 "39 tests passing"                vs srrs_opc 39   MATCH
    B5-I0 matrix G-row "39 tests" (if present)     vs srrs_opc 39   MATCH
  DISPOSITION: ALL_MATCH (claims checked: 2; unmatched claims: 0)
```

Every row quotes the claim text and the measured number.

## 9. Completion-window estimate and basis

`AUTHORED_SPEC` — Fits the B5-I2→B5-I5 ladder; approximately 4–6 governed increments. Basis: kernel is thin (parse, run, compare) but carries the highest test-execution burden of the candidate set (suite runtime); estimate accounts for failure-injection and determinism tests from plan B5.C3.S3.

## 10. Recovery scenario

`AUTHORED_SPEC` — Injected failure: worker killed during the second suite. Manifest records suite 1 complete, suite 2 `interrupted`. Restart resumes at suite 2 (suite results are idempotent per tree SHA); partial manifests display `PARTIAL` and are excluded from reconciliation dispositions until complete.

## 11. Governed change-cycle scenario

`AUTHORED_SPEC` — Change: "add the local-ground suite to scope." Applied as governed change: intent → plan → grant extension (one additional process-execution scope) → suite manifest `v2` entry → regression (previous suites' manifests unchanged in format) → reconciliation table gains the new suite; prior run records remain valid and unedited.

## 12. Reuse inventory vs platform-extraction risk

`AUTHORED_SPEC` — Reuse: job-envelope/lease patterns and evidence-manifest shapes from `oce_control` contracts; pytest is an existing repo-standard dependency. Bespoke: claim-extraction patterns and reconciliation logic. Platform-extraction risk: LOW — it orchestrates test processes; it does not re-implement the worker fabric or scheduler. It consumes the existing test layout rather than restructuring it.

## 13. Governed-path mapping (C10 — all eleven paths)

`AUTHORED_SPEC` — identity: per-run producer identity · intent: scoped run declaration · planning: suite execution plan with budgets · grants: per-suite process-execution grants · workers: suites as leased jobs · artifacts: manifest + raw output digests · evidence: claim-vs-measured rows · review: MATCH/DRIFT table · packaging: local CLI + versioned suite manifest · observability: per-suite counts/durations header · recovery: per-suite resume, partial-run discipline.

## 14. D1–D14 evidence (positive evidence for every "does not require")

| D | Disqualifier | Evidence | Class |
|---|---|---|---|
| D1 | Capital/execution authority | Executes local tests; no capital/execution surface | AUTHORED_SPEC |
| D2 | Live trading/broker credentials | No broker APIs or credentials in scope; suites are repo tests | AUTHORED_SPEC |
| D3 | Irreversible external effects | Writes only `runs/`; pytest runs against local checkout; no external mutation | AUTHORED_SPEC |
| D4 | Regulated submissions | Local report only | AUTHORED_SPEC |
| D5 | Public write access | No publish path | AUTHORED_SPEC |
| D6 | Sensitive mass data | Inputs are repo tests/docs; no personal data | REPO_ASSET |
| D7 | Paid external hosting | Local execution only; `$0` | AUTHORED_SPEC |
| D8 | Cloud-only operation | Fully local (§7) | AUTHORED_SPEC |
| D9 | Vercel/Railway/SonarCloud/Kilo | Not referenced; pytest+stdlib | AUTHORED_SPEC |
| D10 | External hosting authority | None; local machine only | AUTHORED_SPEC |
| D11 | Public SaaS | Not a service | AUTHORED_SPEC |
| D12 | LLM as canonical state | Deterministic kernel (§4); state = JSON manifest | AUTHORED_SPEC |
| D13 | Platform rewrite in disguise | Thin runner over existing suites; no orchestration platform re-built (§12) | AUTHORED_SPEC |
| D14 | Recurring cost > `$0` | No paid services or APIs | AUTHORED_SPEC |

No UNKNOWN answers. Static contract evidence only; no runtime measurements claimed.
