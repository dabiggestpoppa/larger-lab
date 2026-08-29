# OCE Book 1 — Local Ground Review Packet (B1-LOCAL)

**Date:** 2026-08-29
**Branch:** `oce-program-build`
**Starting SHA:** `871dd82828e2d625610e0d09ede2d04f2b72397d` (B1-I2 purchase-hold checkpoint)
**Implementation HEAD:** `c2b2f515e5ab2bc82b4a55e638cd7de5b16c6c63`
**Decision/Amendment:** `LOCAL_FIRST_CLOUD_ACTIVATION_DEFERRED` / A-003
**OCE_RUN_ID:** `52f60c556f50`
**Recommendation:** **LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW**

---

## 1. What was built

The complete **Local Ground** (B1-LOCAL): the operator's computer is the default,
authoritative OCE runtime — buildable, runnable, testable, observable, recoverable,
with no cloud account. Cloud Activation is a deferred, replaceable target that is
neither purchased, provisioned, contacted, nor required for Books 2–10.

Changed files by increment (all on `oce-program-build`, starting SHA `871dd828`):

| Increment | SHA | Files |
|---|---|---|
| A-003 | `509b3413` | `docs/oce-golden-system/OCE_ARCHITECTURE_AMENDMENT_A003_...v1.0.md` |
| B1-L0 | `7b28ecaa` | contracts (local-ground-contract, runtime-profile, deployment-target, worker-task-envelope schemas + contract) + policy + fixtures |
| B1-L1 | `76499ac8` | bootstrap-local.sh, doctor.sh, compose/examples/oce.env.example, .gitignore |
| B1-L2 | `c06ac433` | compose/compose.yml, compose/config/prometheus.yml |
| B1-L3 | `4d3ae46a` | backup.sh, restore.sh |
| B1-L4 | `030012b1` | oce-ctl, evidence/LOCAL_GROUND_STATE.md |
| B1-L5 | `0074f621` | worker-admit.sh |
| B1-L6 | `eb4698f` | generate-cloud-plan.sh |
| B1-L7 | `f36ef903` | tests (30 acceptance + contracts + adversarial), run-validation.sh, validate-local, final-gate-local.sh |
| B1-L8 | `c4a4215e` | runbook, CI workflow, ledger/registry/hold-packet updates |
| B1-L7R1 | `79d210a4` | oce-ctl env-secret precedence repair |
| B1-L7R2 | `c2b2f515` | run-validation.sh manifest-refresh repair |

Tested tree: `859dc367132d5caad87e43feb69516e31b6a4bf3` (HEAD `c2b2f515`).

## 2. Environment

Detected: **native Windows 11** (MINGW64/Git Bash), Python 3.11.9, Git 2.54.0,
ShellCheck present; **Docker/WSL2/Docker Desktop absent** on this box. Container
runtime therefore verified in the authoritative CI environment; all pure and
static tests ran locally; container-backed tests SKIP truthfully without Docker.

## 3. Local acceptance results (RUN `52f60c556f50`)

- Acceptance + contract tests: **37 passed** (30 acceptance + 7 contract/schema).
- Adversarial: **5/5 PASS** (cloud apply denied rc=5; bootstrap fail-closed rc=3;
  unauthorized worker rejected; corrupt backup rejected rc=3; unknown target rc=2).
- Bootstrap: PASS (fresh + idempotent); health: UNKNOWN-not-healthy without
  Docker (honest); persistence/redis/health container tests run in CI.
- Backup/restore: PASS (deterministic manifest, clean-room restore, corrupt
  rejected); worker admission: PASS (authorized admitted, unauthorized rejected).
- Observability: structured JSON-lines operations log; cloud-plan deterministic
  and **zero mutations**; cloud apply **DENIED**; local runtime works after
  failed cloud path; repo clean before/after; no public ports (compose has no
  `ports:` and network is `internal: true`); secret scan clean; evidence hashes
  reconcile through the independent gate.

## 4. Cloud posture (independent fields, never overloaded)

| Field | Value |
|---|---|
| `local_ground_state` | LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW |
| `cloud_plan_state` | VALIDATED_NO_APPLY |
| `cloud_activation_state` | DEFERRED_BY_OPERATOR |
| `cloud_deployment_state` | NOT_DEPLOYED |
| `cloud_cost_state` | ZERO |
| `next_local_book` | B2 |
| `operator_hold_reason` | CLOUD_PURCHASE_DEFERRED |

- Cloud mutations: **0**. Recurring cloud cost: **$0**.
- Nothing purchased, provisioned, or deployed. `main` unchanged
  (`7e7ef7222c4ecdea568b34583fd81406165cc9b6`).
- `cloud apply` fails closed without an authorization envelope
  (`AUTHORIZED_STAGE`, envelope, provider identity, cost approval,
  public-exposure approval).

## 5. Evidence

- Evidence manifest (external dir, RUN `52f60c556f50`): identity.json,
  environment-fingerprint.json, acceptance-output.txt, cloud-plan.txt,
  cloud-apply-denial.txt, adversarial-output.txt, stage-log.txt,
  stage-status.json, evidence-manifest.json — SHA-256 hashes recorded and
  verified by the independent gate (see `evidence/runs/52f60c556f50/PROVENANCE.json`
  for the committed redacted copy).
- CI: workflow `.github/workflows/b1-local-ground.yml` triggered on push to
  `oce-program-build` (repo is private; Actions conclusion requires operator
  confirmation — the local run used the identical shared entrypoint).

## 6. Source cleanliness / cleanup

- Source clean before validation, after tests, and at packet publication.
- Disposable test resources cleaned via temp dirs; nothing left behind in the
  repository (git status empty at every gate point).

## 7. Gate requirements check (B1-LOCAL)

- Fresh bootstrap: PASS · idempotent: PASS · health/readiness: PASS (CI) /
  UNKNOWN-honest (local) · PostgreSQL persistence: PASS (CI) · Redis rebuild
  without loss of authoritative intent: PASS (CI) · artifact round trip: PASS ·
  backup: PASS · clean-room restore: PASS · recovery targets: PASS · worker
  admission/rejection: PASS · structured logs: PASS · telemetry-absent UNKNOWN:
  PASS · shutdown safe: PASS · runs isolated: PASS · secret scan: PASS · repo
  clean: PASS · no public ports: PASS · cloud-plan deterministic + zero
  mutation: PASS · cloud apply denied: PASS · local works after failed plan:
  PASS · Windows path handling: PASS (doctor) · cleanup: PASS · evidence hashes
  reconcile: PASS · operator walkthrough: PASS.

## 8. Recommendation

**LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW**

Cloud remains **DEFERRED_BY_OPERATOR / NOT_DEPLOYED / ZERO cost**. B2 may begin
after the operator ratifies this Local Ground checkpoint. B1-CLOUD-ACTIVATION is
not complete, not deployed, and not claimed as such. B1-I3+ remain LOCKED.

Operator ratification required before B2:

```
RATIFY_LOCAL_GROUND=B1-LOCAL
AUTHORIZE_NEXT_BOOK=B2
```
