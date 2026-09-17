# B1-I1 Build Learning Ledger

**Stage:** B1-I1
**Date:** 2026-08-20
**Agent:** OCE Build Agent (Buffy)

---

## Attempt Records

### B1-I1-ATTEMPT-001: Reality Inventory
- **Intent:** Establish present truth before generating files
- **Environment:** Windows, Python 3.11.9, Git on main branch
- **Action:** Inspected repository structure, tools, existing infrastructure patterns
- **Result:** No existing cloud-ground infrastructure; no Ansible/Docker installed; .env contains real API keys (OPENAI, OANDA, etc.)
- **Failure class:** None — inventory succeeded
- **Correction:** N/A
- **Evidence:** git status, find commands, tool checks
- **Confidence:** High
- **Disposition:** Retain normalized
- **Practice candidate:** "Reality inventory before generation prevents duplication"

### B1-I1-ATTEMPT-002: Branch Creation
- **Intent:** Create isolated working branch from main
- **Environment:** Git on main at commit 7e7ef722
- **Action:** git checkout -b oce/block-1-i1-cloud-ground main
- **Result:** Branch created successfully
- **Failure class:** None
- **Correction:** N/A
- **Evidence:** git branch output
- **Confidence:** High
- **Disposition:** Retain

### B1-I1-ATTEMPT-003: Ansible Role Generation
- **Intent:** Create 8 Ansible roles with meaningful tasks
- **Environment:** File system operations
- **Action:** Created roles: common, security, tailscale, docker, storage_layout, backup_client, monitoring_agent, host_manifest
- **Result:** All roles have tasks/main.yml, handlers/main.yml, and meta/main.yml
- **Failure class:** None
- **Correction:** N/A
- **Evidence:** File manifest
- **Confidence:** High
- **Disposition:** Retain normalized
- **Practice candidate:** "Ansible roles should have meaningful tasks, not empty scaffolds"

### B1-I1-ATTEMPT-004: Compose Foundation
- **Intent:** Create Docker Compose for PostgreSQL and Redis
- **Environment:** File system
- **Action:** Created compose.foundation.yml with health checks, resource limits, security options, no published ports
- **Result:** Syntactically valid YAML (pending parse test)
- **Failure class:** None
- **Correction:** N/A
- **Evidence:** compose.foundation.yml
- **Confidence:** High
- **Disposition:** Retain normalized

### B1-I1-ATTEMPT-005: JSON Schema Contracts
- **Intent:** Create 7 machine-readable contracts
- **Environment:** File system
- **Action:** Created worker-task-envelope, worker-capability-manifest, worker-admission-report, artifact-manifest, service-identity, cost-ledger, evidence-manifest
- **Result:** All schemas use Draft 2020-12 with stable IDs and version constraints
- **Failure class:** None
- **Correction:** N/A
- **Evidence:** contracts/*.schema.json
- **Confidence:** High
- **Disposition:** Retain normalized

### B1-I1-ATTEMPT-006: Static Validation Script
- **Intent:** Create deterministic validation that runs without provisioning
- **Environment:** Bash script
- **Action:** Created validate-static with 20 checks covering parsing, security, policy consistency, fail-closed behavior
- **Result:** Script created and chmod +x applied
- **Failure class:** None
- **Correction:** N/A
- **Evidence:** scripts/validate-static
- **Confidence:** High (pending actual execution)
- **Disposition:** Retain

---

## Failure Observations

### B1-I1-FAIL-001: Tool Availability
- **Context:** Docker, Ansible, jq, shellcheck not installed
- **Impact:** Some validation checks marked BLOCKED
- **Resolution:** BLOCKED results are honest — no false green from skipped tests
- **Learning:** "BLOCKED is a valid state; installing tools to pass checks would be scope creep"

### B1-I1-FAIL-002: Windows Environment
- **Context:** Running on Windows with Git Bash
- **Impact:** Some bash commands behave differently; path separators differ
- **Resolution:** Used POSIX syntax throughout; tested key commands
- **Learning:** "Cross-platform validation scripts need careful path handling"

---

## Practice Candidates

1. **Reality inventory before generation** — Always inspect what exists before creating new files
2. **BLOCKED is honest** — Tool unavailability produces BLOCKED, not false PASS
3. **Ansible roles need real tasks** — Empty task lists are scaffolds, not implementation
4. **Compose health checks ≠ readiness** — Both must be declared separately
5. **Policy files document intent** — Enforcement state must be explicitly declared
6. **No-empty-scaffold rule** — Every file must have substantive content, not just structure

---

## B1-I1 R3 Repair-Cycle Lessons (2026-08-26)

The R3A → R3H repair cycle closed the validation-truth gaps. Lessons promoted to practice:

1. **Expected identity cannot replace observed identity.** Evidence must record the observed git branch (e.g. `(detached)` inside a worktree) and any trusted CI ref separately, then compare through explicit identity rules. Substituting the contract branch into observed fields manufactures truth.
2. **Authoritative validation needs explicit phases.** Initial validation (source identity, config, security, schema, tools) must run before adversarial evidence exists; final validation additionally requires adversarial evidence, meta-test evidence, evidence consistency, RUN_ID consistency, and gate checks. A loose environment flag is not a phase contract — expose and validate an explicit CLI phase argument.
3. **Intermediate tests must never overwrite final evidence.** Engine `--only` runs inside the disposable adversarial worktree wrote `static-validation-results.json` with `(detached)` identity into the final evidence directory, failing the final EVIDENCE-CONSISTENCY check. Intermediate payloads go to a scratch directory, never the final evidence dir.
4. **Evidence paths must be deterministic before execution.** Callers (workflow/operator) must know the evidence directory before validation begins (explicit `--evidence-dir` / `OCE_EVIDENCE_DIR` / path-output file) so failed runs still upload truthful evidence. Never discover it by parsing the runner's last log line.
5. **Cleanup evidence must exist before the final gate.** `worktree-cleanup.json` (`removed`, `pruned`) is written immediately after worktree removal/prune; the gate treats a missing, malformed, false, or inconsistent cleanup artifact as fatal — not a warning.
6. **Manifests must be refreshed after mutable log output.** Appending stage-log lines after the engine wrote `evidence-manifest.json` made recorded SHA-256 hashes stale; the runner now refreshes the manifest after every stage-log append, before the gate, and once more after the gate result line.
7. **CI must preserve exact runner exit codes.** A fail-fast shell must capture the runner's real exit code (`rc=$?`), print the complete log, and exit with that exact status. No pipeline may hide or replace it.
8. **Commit messages are claims, not execution proof.** Only executed, verified evidence (totals, gate, manifest hashes, artifact identity) proves a checkpoint. Self-authored status fields and commit text are never treated as proof.
9. **Expiring CI artifacts require durable archival.** GitHub Actions artifacts expire (retention 30 days); the authoritative evidence ZIP is archived byte-identical in `evidence/archive/` with the expanded copy under `evidence/runs/<run_id>/` and a PROVENANCE record, before expiry.
10. **Pin the full toolchain, not just the headline package.** An unpinned transitive dependency (`ansible-compat` >=4.1.10 resolved to 26.6.0) changed cache behavior and dropped `.ansible/` into the checkout, failing the clean-source check. Pin every dependency that can affect validation behavior.

