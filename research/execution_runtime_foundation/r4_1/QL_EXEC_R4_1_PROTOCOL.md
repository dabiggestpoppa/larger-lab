# QL-EXEC-R4.1 — TB Generic Runtime Shadow Deployment Plan — Protocol

Checkpoint: QL-EXEC-R4.1-TB-GENERIC-RUNTIME-SHADOW-DEPLOYMENT-PLAN
Base: 750a14bf20bf0869f452d8df20138e58bbb091e5
Parent: QL-EXEC-R4-TB-FULL-NONREGRESSION-MIGRATION-HARNESS (PASS, 355/355)

## 1. Purpose

Design the SAFE operational plan for running the proven generic TB path
side-by-side with the existing active TB runtime in **SHADOW ONLY** mode.

This checkpoint is **PLAN ONLY**. Nothing is deployed, no code is changed,
no broker is contacted, no order is submitted.

## 2. Governing invariant

> The active proven TB stack remains PRIMARY OPERATIONAL AUTHORITY.
> The generic TB runtime is OBSERVER / SHADOW ONLY, with ZERO broker order
> authority enforced by construction (multiple independent barriers), not
> by configuration discipline alone.

## 3. Scope boundaries

IN scope (design only):

- shadow mode contract and enforcement layers
- read-only broker/session contract
- process + state isolation contract
- market-data sharing options (resolved decision)
- live parity / mismatch / telemetry schemas
- numeric tolerances (frozen pre-observation)
- resource budget
- restart / market-close / evidence-stop / rollback drills
- security + non-interference audits
- implementation sequence + test plan

OUT of scope (explicitly forbidden):

- any deployment, any code change, any scheduler change
- any broker connection, any broker order
- any write to active TB state/DB/log/PID/desired-state
- automatic failover / promotion of generic shadow

## 4. Decision summary

- shadow mode: first-class `SHADOW_OBSERVE_ONLY`
- execution gate: `can_submit_new_risk = false` at runtime authority
- broker write API: unavailable by construction (`ReadOnlyBrokerSession`)
- market-data path: **LEGACY_EXPORT_READ_ONLY_SNAPSHOT** (Option B)
- MT5 concurrent-read truth: **UNRESOLVED** (audit plan defined; no deployment
  until resolved)
- automatic failover / promotion: **impossible**
- active TB: **unmodified, unwritten**

## 5. Pass gate mapping

| Gate | Evidence |
|------|----------|
| shadow authority impossible by construction | ORDER_PREVENTION_LAYERS + READ_ONLY_BROKER_CONTRACT |
| generic process isolated from active TB | PROCESS_ISOLATION + STATE_DIRECTORY_CONTRACT |
| active TB sole operational authority | SHADOW_AUTHORITY_CONTRACT + NONINTERFERENCE |
| no automatic failover | SHADOW_AUTHORITY_CONTRACT (explicit) |
| concurrent MT5 read resolved/designed around | MT5_CONCURRENT_READ_AUDIT_PLAN + MARKET_DATA_SHARING_OPTIONS |
| live parity schema frozen | PARITY_SCHEMA |
| tolerances frozen before observation | NUMERIC_TOLERANCE |
| event-count stopping rule frozen | EVIDENCE_STOPPING_RULE |
| rollback trivial | ROLLBACK_PLAN |
| dashboard/watcher auxiliary | SUPERVISION classification (in R4) |
| no active TB modification | ACTIVE_TB_NONINTERFERENCE + SECURITY_AUDIT |
| no broker execution | READ_ONLY_BROKER_CONTRACT (order-check excluded from G1) |

## 6. Next checkpoint

QL-EXEC-R4.2-TB-GENERIC-RUNTIME-LIVE-SHADOW-CANARY (r4_2_authorized = false
until human review).
