# OCE Golden System
## B5-I1 — Evidence Packet: CAND-001

**Document ID:** OCE-B5-I1-PACKET-CAND-001
**Version:** 1.0
**Status:** INTAKE_EVIDENCE — UNSCORED
**Candidate identifier:** CAND-001
**Working name (register-only):** Evidence Ledger Console
**Governing protocol:** `OCE_B5_I0_SELECTION_PROTOCOL_v1.0.md` (OPERATOR_RATIFIED — FROZEN)

---

## 1. Observable operator outcome

`AUTHORED_SPEC` — The operator asks "is the governance corpus internally truthful right now?" and gets a single local command that answers with a per-document PASS/FAIL table: every section cross-reference resolves, every status claim in ledgers matches the statuses in the documents they summarize, and every claimed artifact reference points at a real file. Failure output names the exact document, section, and broken claim. Success is judged by reading the table — no code reading required (protocol C1).

Basis: `REPO_ASSET` — the corpus this validates exists (`docs/oce-golden-system/`, 28 documents; `infrastructure/control-plane/B4-EVIDENCE-RECORD.md`, 24 sections) and the defect class is demonstrated: B5-I0 ratification repaired a nonexistent `L §11` citation and a false count heading; Book 4 evidence §17–§22 record four claim-falsification cycles.

## 2. Operator-testable acceptance scenarios

`AUTHORED_SPEC` — Each scenario is pass/fail judgeable by a human from the tool's output:

1. S-1 (healthy corpus): run the validator on the corpus as of the intake commit; output shows every document with `PASS` and a per-check count; exit code 0.
2. S-2 (broken reference): introduce a scratch copy of a matrix that cites a nonexistent section; output shows `FAIL` naming document, section, and the unresolved target; exit code 1; the canonical corpus is not modified.
3. S-3 (status drift): point the validator at a ledger whose increment status contradicts the referenced document's own status header; output shows `FAIL` with both observed values quoted verbatim.
4. S-4 (read-only guarantee): run against a read-only-mounted copy; the run succeeds and file hashes before/after are identical.

## 3. OCE lifecycle coverage matrix

`AUTHORED_SPEC` — How building and operating CAND-001 exercises OCE/PO contracts:

| OCE surface | Exercised by CAND-001 |
|---|---|
| Intent | Operator authorizes the validation run scope (which corpora, which checks) as a bounded intent statement. |
| Planning | Validation check-list compiled into a bounded, dependency-ordered plan with gates. |
| Grants | Each check class (filesystem read, git read) is a capability grant from the static grant inventory; denial envelope on out-of-scope paths. |
| Workers | Checks run as discrete jobs under the local worker pattern (job envelope, lease, result record). |
| Artifacts | Every run emits an artifact-referenced report (artifact-ref style digest). |
| Evidence | Reports are evidence-manifest-shaped: inputs, checks, observed values, dispositions. |
| Review | Operator approves/revises from the report packet without agent narrative. |
| Identity | Run identity bound to agent/worker identity contracts; reports carry the identity that produced them. |
| Packaging | Local install = Python entry point + corpus path convention; no cloud package. |
| Observability | Run health (checks executed, duration, failures) exposed in the report header. |
| Recovery | Interrupted runs resume from the canonical run state; partial reports never claimed complete. |

## 4. Deterministic-kernel boundary

`AUTHORED_SPEC` — Correctness-critical logic is deterministic code with tests:

- Deterministic core: corpus file discovery, markdown section-index parsing, cross-reference resolution, status consistency comparison, report rendering, exit-code policy. Fixed input → fixed output; same corpus + same check-set → byte-identical report.
- LLM-permitted surfaces: none required. The tool operates without any model in the loop. (An optional human-facing summary generator would be strictly post-kernel and never authoritative; default build omits it.)

## 5. Bounded input inventory

`AUTHORED_SPEC` grounded on `REPO_ASSET` paths:

| Input | Path/bounds | Schema class |
|---|---|---|
| Governance corpus | `docs/oce-golden-system/*.md` (28 files at intake) | Markdown with `##`/`###` section headers, `§` references, status header lines |
| Book 4 evidence set | `infrastructure/control-plane/B4-EVIDENCE-RECORD.md`, `B4-ACCEPTANCE-MATRIX.md`, `B4-*.md` | Markdown, large but bounded (fixed file list) |
| Ledger snapshot | The current `OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md` | Status table + decision history |
| Check-set definition | A versioned check manifest shipped with the app | Ordered list of check IDs + parameters |

No network inputs. No user-file scanning beyond the declared corpora. Unbounded data ingestion: none.

## 6. Canonical-state proposal

`AUTHORED_SPEC` — State = a run record: `{run_id, corpus_snapshot_digest, check_set_version, per_check_results[], disposition}` stored as one append-only JSON file per run under a local `runs/` directory, schema-validated before write. Replays: re-running the same check-set against the same corpus digest reproduces the same result set. No database; no hidden state.

## 7. Local-run topology

`AUTHORED_SPEC` — Single-process Python CLI on the operator's machine; reads the repository working tree; writes only to its own `runs/` output directory. No external service dependency, no network, no background daemons. Runs identically on any machine with Python ≥3.12 and a checkout.

## 8. Explainable-output example

`AUTHORED_SPEC` — Sample report fragment (format demonstration, not a measurement):

```
CAND-001 run r-0001  corpus=d41cd8…  checks=v1
  docs/oce-golden-system/OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md
    xref-resolution   PASS (41/41 refs resolve)
    status-parity     PASS (11/11 increment statuses match)
  infrastructure/control-plane/B4-EVIDENCE-RECORD.md
    xref-resolution   FAIL §11 → target section not found (offender: "…see §11")
  DISPOSITION: FAIL — 1 broken reference, 0 status drifts
```

Every PASS/FAIL carries the counted evidence and the exact offender text on failure.

## 9. Completion-window estimate and basis

`AUTHORED_SPEC` — Estimate: fits the B5-I2→B5-I5 increment ladder (product contract, failure/acceptance plan, deterministic kernel + first slice, complete build/review) — approximately 4–6 governed increments, each a single bounded agent session, plus one governed change cycle at B5-I7. Basis: the Block 5 plan's own increment granularity; comparable scope to the B5-I0 documentation increment (six authored documents, one session) per check-class, with kernel tests.

## 10. Recovery scenario

`AUTHORED_SPEC` — Injected failure: process killed after writing 3 of 5 per-check results. On restart, the run record's `COMPLETE=false` state is detected; the tool resumes from the last recorded check, re-runs the remaining checks, and rewrites the record atomically (write-temp-then-rename). The final report is never emitted for an incomplete run — no false success (plan B5.C2.S4).

## 11. Governed change-cycle scenario

`AUTHORED_SPEC` — Change request: "add a status-vocabulary check (statuses must be from the ratified vocabulary)." Applied as: new intent → plan line → capability grant unchanged (same read scope) → new check module + tests under the frozen check-set versioning → new check-set version `v2` → regression: all `v1` checks still pass on the intake corpus → report schema gains one field → prior run records remain valid and unedited.

## 12. Reuse inventory vs platform-extraction risk

`AUTHORED_SPEC` — Reuse: `infrastructure/control-plane/contracts/evidence-manifest.schema.json` and `artifact-ref.schema.json` shapes for report/record structure; schema_validator patterns; job-envelope concepts for check execution. Bespoke: corpus parsers and check logic (application-specific, expected). Platform-extraction risk: LOW — the app parses documents; it does not generalize the worker fabric or governance engine into an app-owned platform. No OCE service is forked into the app.

## 13. Governed-path mapping (C10 — all eleven paths)

`AUTHORED_SPEC` — identity: run/worker identity recorded per run (worker-identity/agent-identity contract shapes) · intent: operator-scoped validation intent · planning: check-set plan with gates · grants: read-scope capability grants + denial envelopes · workers: checks execute as leased jobs · artifacts: digest-referenced run records · evidence: manifest-shaped per-check results · review: operator PASS/FAIL packet, no narrative trust · packaging: single local entry point + versioned check-set · observability: run header health/duration/failures · recovery: resume-from-record with atomic rewrite.

## 14. D1–D14 evidence (positive evidence for every "does not require")

| D | Disqualifier | Evidence | Class |
|---|---|---|---|
| D1 | Capital/execution authority | Tool reads files and writes local reports; no payment, order, or execution surface exists in scope | AUTHORED_SPEC |
| D2 | Live trading/broker credentials | No broker API, no credential store, no network; scope is filesystem+git read-only | AUTHORED_SPEC |
| D3 | Irreversible external effects | Writes only to its own `runs/` dir; corpus is read-only by design (S-4 hash check) | AUTHORED_SPEC |
| D4 | Regulated submissions | Output consumed locally by the operator; no regulatory filing surface | AUTHORED_SPEC |
| D5 | Public write access | No publish/upload path; local CLI only | AUTHORED_SPEC |
| D6 | Sensitive mass data | Inputs are the governance corpus (already in-repo, non-personal); no PII harvesting | REPO_ASSET |
| D7 | Paid external hosting | Runs on the operator machine; `$0` services | AUTHORED_SPEC |
| D8 | Cloud-only operation | No cloud component; fully local (§7) | AUTHORED_SPEC |
| D9 | Vercel/Railway/SonarCloud/Kilo | None referenced in design or dependencies; local Python only | AUTHORED_SPEC |
| D10 | External hosting authority | Deployment authority = local machine; none external | AUTHORED_SPEC |
| D11 | Public SaaS | Not a service; no multi-tenancy | AUTHORED_SPEC |
| D12 | LLM as canonical state | Kernel is deterministic code (§4); canonical state is the schema-validated run record | AUTHORED_SPEC |
| D13 | Platform rewrite in disguise | Parses one corpus with one check-set; reuse inventory bounded (§12); no OCE service forked | AUTHORED_SPEC |
| D14 | Recurring cost > `$0` | No paid dependencies, hosting, or APIs | AUTHORED_SPEC |

No UNKNOWN answers. Evidence classes: static contract evidence only; no runtime measurements claimed.
