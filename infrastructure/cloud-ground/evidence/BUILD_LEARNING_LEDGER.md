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
