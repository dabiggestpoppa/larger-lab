# OCE Golden System
## B5-I1 — Candidate Intake Register

**Document ID:** OCE-B5-I1-INTAKE-001
**Version:** 1.0
**Status:** INTAKE_RECORDED — AWAITING_INDEPENDENT_REVIEW
**Authorized stage:** `AUTHORIZED_STAGE=B5-I1-EVALUATION`
**Governing authorities:** `OCE_B5_I0_SELECTION_PROTOCOL_v1.0.md` (OPERATOR_RATIFIED — FROZEN); `OCE_B5_I0_RISK_CEILING_AND_DISQUALIFIER_REGISTER_v1.0.md`; `OCE_B5_I0_EVALUATION_AND_INDEPENDENT_REVIEW_PROCEDURE_v1.0.md`; `OCE_B5_I0_CANDIDATE_SCORECARD_TEMPLATE_v1.0.md`; `OCE_BLOCK_05_REFERENCE_APPLICATION_FACTORY_PLAN_v1.0.md`
**Branch:** `oce-book-5-i1` (created from exact merged `main` `f89883471dbc93d481b43d73757c716afc817441`)
**Build authorization:** None. Intake and evidence only; no application code at this stage.

---

## 1. Census method

A read-only audit of the repository at `f89883471…` was performed to ground candidates in actual assets and demonstrated operator needs:

- Governance corpus: `docs/oce-golden-system/` (28 governing documents, including the Book 4 evidence record sections 17–24, which document repeated claim-falsification and truth-audit cycles).
- Governed runtime: `infrastructure/control-plane/` (`src/oce_control/` — 36 modules covering job store, scheduler, worker fabric, authority, boundaries, clocks, evidence, recovery, state machines; `contracts/` — 12 schema/contract files including agent-identity, capability-grant, job-envelope, evidence-manifest, denial-envelope; ~24 test files; `compose/compose.yml`).
- OCE services: `oce/backend/` (22 modules: event fabric, governance engine, metrics collector, tracing, self-healing, observer runtime; ~20 test files).
- Research core: `srrs_opc/` (33+ modules; `srrs_opc/tests/` — 9 test files).
- Operator audit assets: `tv_vm_audit/` (15 files: 5 CSV activity exports, IOC JSON, baseline/diff/verdict documents).
- Operator tooling: `tools/` (50+ local tools including progress-sync, phase-gate, workflow engines).
- Existing product surface: `oce/frontend/` (Next.js; internally owned; untouched by B5).
- Infrastructure grounds: `infrastructure/local-ground/` and `infrastructure/cloud-ground/` (compose, policy, runbooks, tests).

Demonstrated operator needs observed in the corpus (not invented): evidence-truth auditing (Book 4 evidence §17–§22 record four claim falsifications), claimed-vs-actual test reconciliation, secret/hygiene scans, line-ending discipline, branch/merge governance verification (reality locks), progress-ledger maintenance, and local recovery drills.

## 2. Candidate register (identifiers → working names)

| Identifier | Working name (register-only) | One-line summary | Evidence packet |
|---|---|---|---|
| CAND-001 | Evidence Ledger Console | Validates and renders the OCE governance evidence corpus (ledgers, evidence records, matrices) into an operator-readable truth dashboard | `OCE_B5_I1_CAND-001_EVIDENCE_PACKET_v1.0.md` |
| CAND-002 | Test-Claim Reconciler | Runs local test suites, records a canonical run manifest, and reconciles claimed test counts in governance documents against measured results | `OCE_B5_I1_CAND-002_EVIDENCE_PACKET_v1.0.md` |
| CAND-003 | Repo Integrity & Governance-State Auditor | Automates reality locks: secret scan, `git diff --check`, line-ending census, frozen-branch and merge-parent verification | `OCE_B5_I1_CAND-003_EVIDENCE_PACKET_v1.0.md` |
| CAND-004 | Local Job Console | Operator surface over the local control plane: list jobs/workers/health, submit representative jobs, run recovery drills, inspect event/evidence timelines | `OCE_B5_I1_CAND-004_EVIDENCE_PACKET_v1.0.md` |
| CAND-005 | Audit-Artifact QA Workbench | Schema-validates and cross-checks `tv_vm_audit`-style security-audit artifact sets (CSV/IOC/baseline/diff) and produces signed evidence summaries | `OCE_B5_I1_CAND-005_EVIDENCE_PACKET_v1.0.md` |

No sixth candidate was admitted: remaining census ideas were variations of the above (e.g., a documentation link-checker is a strict subset of CAND-001) and were not padded in.

## 3. Evidence-requirement parity

All five candidates received the identical evidence requirement set (protocol §7.2 + operator B5-I1 authorization §4):

| # | Required packet component | CAND-001 | CAND-002 | CAND-003 | CAND-004 | CAND-005 |
|---|---|---|---|---|---|---|
| 1 | Observable operator outcome | §1 | §1 | §1 | §1 | §1 |
| 2 | Operator-testable scenarios | §2 | §2 | §2 | §2 | §2 |
| 3 | OCE lifecycle coverage matrix | §3 | §3 | §3 | §3 | §3 |
| 4 | Deterministic-kernel boundary | §4 | §4 | §4 | §4 | §4 |
| 5 | Bounded input inventory | §5 | §5 | §5 | §5 | §5 |
| 6 | Canonical-state proposal | §6 | §6 | §6 | §6 | §6 |
| 7 | Local-run topology | §7 | §7 | §7 | §7 | §7 |
| 8 | Explainable-output example | §8 | §8 | §8 | §8 | §8 |
| 9 | Completion-window estimate + basis | §9 | §9 | §9 | §9 | §9 |
| 10 | Recovery scenario | §10 | §10 | §10 | §10 | §10 |
| 11 | Governed change-cycle scenario | §11 | §11 | §11 | §11 | §11 |
| 12 | Reuse inventory vs platform-extraction risk | §12 | §12 | §12 | §12 | §12 |
| 13 | Governed-path mapping (11 paths) | §13 | §13 | §13 | §13 | §13 |
| 14 | D1–D14 evidence (no UNKNOWN) | §14 | §14 | §14 | §14 | §14 |

## 4. Evidence classification discipline

Every packet item is labeled with one of:

- `REPO_ASSET` — an existing repository path/content cited as evidence (verifiable at the intake commit).
- `AUTHORED_SPEC` — a written proposal produced at intake (scenario, schema draft, estimate). Static contract evidence only; it becomes executable/contract evidence at B5-I2+.
- `NOT_YET_MEASURED` — a runtime property that cannot be truthfully claimed before the application exists. These are stated as such and are never represented as observations.

No runtime measurements exist for any candidate at intake; no packet claims any.

## 5. Screening posture (pre-review)

The disqualifier screen (scorecard §2) is executed by the reviewers at scoring time from packet §14 evidence. At intake:

- No D1–D14 trigger is known for any candidate; each packet §14 carries positive evidence for every "does not require" answer (deny-by-default satisfied).
- No `UNKNOWN` remains in any packet.
- No candidate has been scored, ranked, favored, or eliminated by this register or by any packet.

## 6. Boundary statements

- Sensor Fabric distinction: candidates operate on governance corpora, test suites, git state, the local control plane, and `tv_vm_audit` security artifacts. None edits, executes, or advances `quant-lab/research/crypto_foundry/sensor_fabric/bloc_05/` material. CAND-005 carries an explicit distinction statement in its packet.
- `oce/frontend`, Book 4 evidence records, workflows, and configuration are untouched by intake.
- Candidates are quant-adjacent at most (CAND-005 processes audit CSVs of a trading-VM security exercise); none performs trading, order placement, credential handling, or any capital authority function.

## 7. Accounting

Documentation only. Cloud mutations 0; broker mutations 0; capital mutations 0; execution mutations 0; recurring cost `$0`; `capital.authority = none`. No candidate scored, favored, or selected by this register.
