# OCE Golden System
## Amendment A-003 — Local-First Architecture with Cloud Activation Deferred

**Document ID:** OCE-AMEND-A003
**Version:** 1.0
**Status:** RATIFIED BY OPERATOR DECISION
**Decision:** `AUTHORIZED_DECISION=LOCAL_FIRST_CLOUD_ACTIVATION_DEFERRED`
**Parent:** OCE Constitution 1.1; Amendment A-002; OCE Master Program Atlas 1.0
**Supersedes dependency references in:** OCE-FULL-PROGRAM-BUILD-ROADMAP §3 (B2 dependency on an actually provisioned cloud host)
**Authorized stage:** `AUTHORIZED_STAGE=B1-LOCAL-GROUND-CLOSURE`
**Source precedence:** Constitution > ratfied amendments (A-002, this A-003) > Atlas > Roadmap > Block plans > increment contracts > ledgers > existing implementation > commit messages. Where this amendment changes an older cloud dependency, **A-003 controls.**

---

## 0. Decision summary

The operator is **not purchasing cloud infrastructure now** (`PURCHASE_AUTHORIZATION=NONE`,
`CLOUD_PROVISIONING_AUTHORIZATION=NONE`, `CLOUD_DEPLOYMENT_AUTHORIZATION=NONE`,
`PUBLIC_EXPOSURE_AUTHORIZATION=NONE`). The complete OCE system must be **buildable,
runnable, testable, observable, recoverable, and useful on the operator's own computer.**
Cloud infrastructure is fully prepared as a later deployment target but is **not purchased,
provisioned, contacted, or required for Books 2–10.**

The existing B1-I2 cloud purchase hold remains truthful as historical evidence; it must not
block local OCE development.

## 1. Two independent readiness dimensions

Block 1 is split into two independent dimensions. A change in one does not imply a change in
the other:

| Dimension | State vocabulary | Typical values |
|---|---|---|
| **Local Ground** (active) | local readiness states | `BUILDING`, `VERIFYING`, `LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW`, `RATIFIED` |
| **Cloud Activation** (deferred) | cloud lifecycle states | `DEFERRED_BY_OPERATOR`, `PLANNED`, `VALIDATED_NO_APPLY`, `DEPLOYED` |

- **Local Ground** is the dependency supplied to B2. It must prove complete local runtime,
  local databases and transport, local artifacts, backup and restore, local observability,
  local workers, reproducible setup, deterministic validation, safe shutdown/restart, local
  recovery, and deployment portability.
- **Cloud Activation** contains provider-neutral contracts, Ansible, Compose cloud overlays,
  infrastructure variable schemas, deployment plans, dry-run validation, security policies,
  cost ceilings, rollback procedures, and evidence requirements. It must contain **no claim
  that a real host was purchased, reached, configured, or verified.**

While the operator has not activated cloud, cloud state remains exactly
`DEFERRED_BY_OPERATOR`. It is never reported as PASS, deployed, provisioned, or
production-ready.

## 2. Dependency correction

The roadmap's §3 made B2 depend on an actually provisioned B1 cloud host. **That dependency
is amended:** B2 may begin after the **Local Ground gate** demonstrates a stable, reproducible
audit environment. Actual cloud activation is **not required** for B2–B10 development.
Cloud-specific production promotion remains blocked until a later explicit operator
authorization.

## 3. Rules this amendment establishes

1. **Local operation is the default.** `OCE_RUNTIME_TARGET` defaults to `local`. Local must
   never depend on unset cloud variables.
2. **Cloud is a replaceable deployment target**, not a development dependency. No cloud
   account, public domain, certificate, public IP, or inbound internet port is required.
3. **Build readiness and deployment state are separated** and tracked in independent ledger
   fields (see §6).
4. **Local Ground** is the dependency consumed by B2.
5. **Cloud Activation** is deferred and provides no false equivalence between dry-run
   validation and real deployment. `cloud-plan` mutating nothing is not proof of deployment.
6. **Future activation requirements:** a signed authorization envelope supplying at least
   `AUTHORIZED_STAGE`, provider identity, product, cost ceilings, public-exposure approval,
   and deployment inputs. Without it, any `cloud apply` fails closed.
7. **Rollback to local operation:** the local runtime remains the control/rollback
   environment. Once s cloud deployment exists, the local runtime remains authoritative and
   able to drive recovery.
8. **Zero cloud cost** until the operator explicitly activates.
9. **Compatibility with A-002 (PO/Hermes boundary):** this amendment does not merge PO and
   Hermes, does not add a second Hermes, does not make Hermes a mandatory gateway, and does
   not make Telegram a canonical truth or a required dependency. Telecommunications loss must
   not stop local OCE operation.

## 4. Cloud-flip contract (validate / plan separation mandatory)

The activation interface supports exactly these phases; names may follow repo conventions but
the separation is mandatory:

1. `oce deployment validate --target cloud` — local static/dry-run validation; may run locally.
2. `oce deployment plan --target cloud` — produce a deterministic, non-mutating plan; may run
   locally.
3. Operator reviews plan, cost, exposure, and secrets, then supplies a signed authorization
   envelope.
4. `oce deployment apply --target cloud` — the only mutating operation; **fails closed**
   without explicit authorization.
5. health/security verification; evidence generation; operator promotion decision.

`validate` and `plan` may never mutate external state. `apply` fails closed when
authorization, provider identity, or cost approval is missing, and when cost exceeds an
approved ceiling. Public exposure requires a separate approval. No automatic fallback
purchase or deployment is allowed.

## 5. Local runtime profiles

| Profile | Purpose | Resources |
|---|---|---|
| `local` | Default, authoritative development runtime | local only |
| `local-test` | Disposable isolated test env with deterministic fixtures | local only |
| `local-recovery` | Prove backup restoration and clean rebuild | local only |
| `cloud-plan` | Validate cloud config/manifests/policies/Ansible with no provider contact | none external |
| `cloud` | Reserved for later activation; fails closed | none external |

Default is `local`. Master variable: `OCE_RUNTIME_TARGET` (values above).

## 6. Ledger model (independent fields)

```
local_ground_state      LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW
cloud_plan_state        VALIDATED_NO_APPLY
cloud_activation_state  DEFERRED_BY_OPERATOR
cloud_deployment_state  NOT_DEPLOYED
cloud_cost_state        ZERO
next_local_book         B2
operator_hold_reason    CLOUD_PURCHASE_DEFERRED
```

No single field is overloaded to imply both local readiness and cloud deployment.

## 7. Local data contract

- PostgreSQL is authoritative state.
- Redis is transient transport/cache only, never sole durable truth.
- Artifact storage is replaceable through a versioned storage adapter supporting deterministic
  paths, checksums, lineage, retention, backup, restore, corruption detection, and later
  migration to a cloud/object-storage target.
- No provider (netcup, Backblaze, Hetzner, etc.) is hardcoded into domain logic. Provider
  values live only in deployment adapters and configuration.

## 8. Local secrets

No credentials are committed. Provide placeholder `.env.example` config, documented secure
local injection, startup validation, redacted diagnostics, fail-closed missing-secret
behavior, secret scanning, and rotation instructions. Local dev secrets are separate from
future cloud/production secrets.

## 9. Falsification

This amendment is falsified by: making cloud a mandatory local dependency; reporting
`cloud_activation_state` other than `DEFERRED_BY_OPERATOR` while no activation occurred;
claiming real deployment from a dry-run plan; merging PO/Hermes; making Telegram mandatory;
or introducing any cloud cost without a separate operator activation.