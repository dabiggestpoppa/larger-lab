# QCAE Amendment A-002 — Explicit External Discovery Egress Authority

**Document ID:** QCAE-AMEND-A002  \n**Version:** 1.0 (DRAFT — FOR OPERATOR REVIEW; NOT RATIFIED)  \n**Status:** PROPOSED — awaits operator approval before implementation  \n**Canon affected:** QCAE v0.1 Books I–VI remain COMPLETE / FROZEN; this amendment adds an enforceable egress contract without rewriting frozen canon  \n**Primary seams:** Block 2 (Discovery Plan / budget / tier), Block 15 (Discovery port / adapter outcomes), P2 governance shim (authority/policy), P3-T02 GitHub discovery adapter  \n**Build authorization:** INTERFACE/PLANNING ONLY; no autonomous egress authority; implementation blocked on operator ratification

---

## 1. Decision

QCAE discovery may reach out to an external provider (GitHub repository/code search) only under an **explicit, bounded external-egress authorization** that binds the entire executable query envelope. A general `MAY_DISCOVER` grant for a contract does **not** by itself authorize external calls, and the frozen P2 policy model must not be permitted to silently widen an internal discovery allowance into unrestricted GitHub egress.

Every external egress decision must bind, at minimum:

- **Provider/resource** — the external provider and resource class being called (e.g. `github` / `repository code`).
- **Contract ID and version** — the capability contract under which the discovery runs.
- **DiscoveryPlan ID** — the plan that authorized the query envelope.
- **Query identity or canonical query digest** — the exact planned query (family, atom, concrete query).
- **Atom and source class** — the atom targeted and the source class used.
- **Effective tier and source-call envelope** — `min(query.max_tier, plan.cost_tier_ceiling, allocation.max_tier)` and the declared source-call/result/query budgets.
- **Decision identity, policy version, expiry** — the authority decision id, the policy version it was decided under, and any expiry/revocation semantics.

Stale, mismatched, or revoked authorization **fails closed**, and every denial produces **zero transport calls**.

---

## 2. Problem the amendment addresses

P3-T02-R1 repaired the GitHub discovery adapter so that it performs its own pre-flight egress gates (C01–C07): baseline established, baseline/plan/version/atom/hypothesis identity binding, explicit `may_discover` GRANT through the authority boundary, effective-tier computation, budget checks, typed provider-outcome truth, two-surface aggregation, duration-based retry, and non-durable fingerprint classification.

That repair is sound **within the adapter**, but it exposes a frozen-model gap (reported as C02 blocker in P3-T02-R1):

- `qcae/governance/standalone/policy.py` `LocalPolicyEngine.evaluate()` rule-matches only `action` / `principal` / `resource` / `classification`.
- `PolicyRequest.scope` and `PolicyRequest.budget_ref` are **carried but never rule-matched** (verified: an identical broad `may_discover` ALLOW matches a request with `scope="github-external-search"` and `budget_ref="plan-001"` and one with both empty, returning the same rule ref).
- `qcae/governance/standalone/authority.py` `LocalAuthorityProvider` maps that engine result to `AuthorityDecision` and forwards `scope`/`budget_ref` into the `AuthorityRequest.context` for auditability only — the adapter records them, but no authority-layer enforcement binds the intended external egress scope.

Consequence: a broad internal `MAY_DISCOVER` ALLOW for contract `CAP` cannot distinguish:

1. internal capability discovery (registry lookup, `INTERNAL_REGISTRY_CODE`) — no egress;
2. external GitHub repository search — egress, metadata surface;
3. external GitHub code search — egress, deeper source surface;
4. one contract/plan from another — bound at the adapter but **not** at the authority layer;
5. one bounded query envelope (atom/source-class/tier/budget) from another — carried as context, not matched by policy.

A generic wildcard `MAY_DISCOVER` ALLOW can therefore accidentally substitute for a specific external-egress grant. A-002 closes this gap.

---

## 3. Freeze preservation

This amendment does not rewrite QCAE Books I–VI or Blocks 0–18. It adds an explicit external-egress contract and a provider-neutral authority port; frozen canon remains authoritative unless an amendment explicitly supersedes a named clause.

In particular:

- P2 remains **frozen**: no P2 grant is widened, no P2 file is modified, and no existing `MAY_DISCOVER` rule is reinterpreted as authorizing external egress.
- Canon 2.1 (Discovery Plan), 2.2 (discovery execution), 2.6 (internal baseline), and Book V 13.2/15.3 remain unchanged.
- The adapter-level C01–C07 repairs in P3-T02-R1 are **preserved as-is**; A-002 adds the authority-layer enforcement they currently cannot receive from the frozen model.

---

## 4. Enforceable external-egress contract

### 4.1 Required bindings

An external-egress authorization is valid only if every field below is present and matches the executable query envelope the adapter is about to run:

| Binding | Source | Enforced by |
|---|---|---|
| Provider | `github` (fixed for this adapter) | Authority port + adapter gate |
| Resource | `repository` and/or `code` surface | Authority port + adapter gate |
| Contract ID | `DiscoveryPlan.contract_id` | Authority port + adapter gate |
| Contract version | `DiscoveryPlan.contract_version` | Authority port + adapter gate |
| DiscoveryPlan ID | `DiscoveryPlan.discovery_plan_id` | Authority port + adapter gate |
| Query identity / digest | `DiscoveryQuery.query_id` (and/or `sha256` digest) | Authority port + adapter gate |
| Atom | `DiscoveryQuery.atom_id` | Authority port + adapter gate |
| Source class | `DiscoveryQuery.source_class` | Authority port + adapter gate |
| Effective tier | `min(query.max_tier, plan.cost_tier_ceiling, allocation.max_tier)` | Authority port + adapter gate |
| Source-call envelope | `DiscoveryBudget.max_source_calls`, `max_queries`, `max_results_inspected` | Authority port + adapter gate |
| Decision identity | `AuthorityDecision.decision_id`, `request_ref == request.request_id` | Adapter C01 gate |
| Policy version | `DiscoveryPlan.policy_version` / policy set version | Authority port |
| Expiry / revocation | decision `expires_at` or revocation check | Authority port |

### 4.2 Fail-closed laws

1. **No authorization, no egress:** absence of a wiring provider, a missing/denied/more-evidence decision, a structural validation failure, or an authority-provider exception produces zero transport calls (P3-T02-R1 C01/C05).
2. **Mismatch fails closed:** `decision.request_ref != request.request_id`, `decision.action != MAY_DISCOVER`, or `decision.outcome != GRANT` → zero transport calls.
3. **Stale/revoked fails closed:** an expired or revoked authorization is treated as DENY; the adapter must not cache a GRANT across revocation.
4. **Generic wildcard cannot substitute:** a rule matching `action="*"`, `resource="*"`, `scope=""`, or empty `budget_ref` must **not** satisfy an external-egress request; the egress action/scope must match explicitly.
5. **Every denial produces zero transport calls:** a denial is never reported as a completed empty search (`NO_RESULTS`); it is `NOT_CONFIGURED`/`AUTH_FAILURE`/`UNSUPPORTED_QUERY` as appropriate.

### 4.3 What is deliberately out of scope (not implemented by A-002)

- Live GitHub network transport (P3-T03+ integration decision).
- Wall-clock or dollar-cost metering (see Gate 5: these budget dimensions exist on `DiscoveryPlan` but are not measured by the adapter; unsupported metering fails closed by not claiming enforcement).
- Research Mesh delegation seam (`LOCAL_FALLBACK_RESEARCH`, A-001 §5/§13) — separate concern.

---

## 5. Design comparison: Option A vs Option B

### Option A — Distinct external-egress policy action + exact rule-matching

Add a new policy action (e.g. `MAY_DISCOVER_EXTERNAL`) and extend `LocalPolicyEngine` rule-matching to include `scope` and/or `budget_ref` (exact or prefix-star), so a rule must explicitly name the external egress scope and budget to GRANT.

**Canon sections affected:** Book V 13.2 (policy rule vocabulary), `PolicyRule.action`/`scope`/`budget_ref` matching, P2 governance shim interface contract.

**New/altered interfaces:** `PolicyRule` gains effective matching on `scope`/`budget_ref`; `PolicyAction` gains a distinct external-egress action; `AuthorityRequest`/`AuthorityDecision` unchanged (already carry context).

**Migration/compatibility:** Additive — existing `MAY_DISCOVER` rules continue to govern internal discovery unchanged. External egress requires a new explicit rule. No existing P2 grant is widened because the new action is distinct and not matched by `action="*"` unless explicitly opted in.

**Risk of widening existing P2 grants:** Low — the new action is opt-in; wildcard `action="*"` rules would need explicit review to cover the external-egress action, and scope/budget_ref matching prevents a broad contract rule from implicitly covering egress.

**Logging/provenance:** The matched rule id and policy version are recorded on the `PolicyDecision`/`AuthorityDecision`; scope and budget_ref already flow into `AuthorityRequest.context` for audit.

**Adversarial tests:** broad `MAY_DISCOVER` ALLOW must not grant `MAY_DISCOVER_EXTERNAL` for GitHub scope; empty scope/budget_ref must not match an explicit egress rule; mismatched contract/version/atom/plan must fail closed; zero transport calls on every denial.

**Implementation complexity:** Small — extends the existing first-match-wins engine with two additional matchers and one new action value.

### Option B — Provider-neutral `ExternalEgressAuthority` port binding the full envelope

Add a new port `ExternalEgressAuthority` whose `authorize_external_egress(envelope)` decision must bind the entire executable query envelope (provider, resource, contract id/version, plan id, query identity/digest, atom, source class, effective tier, source-call envelope, decision id, policy version, expiry). The adapter calls this port **in addition to** (or instead of) the generic `may_discover` decision, and proceeds only on an explicit GRANT.

**Canon sections affected:** Book V 15.3 (adapter port contract), a new port module, P3 adapter wiring.

**New/altered interfaces:** New `ExternalEgressAuthority` port + envelope record; adapter constructor gains the port dependency; `AdapterOutcome` unchanged.

**Migration/compatibility:** Additive port; existing `AuthorityProvider`/`MAY_DISCOVER` path untouched. Requires wiring the new port into the adapter and governance layer.

**Risk of widening existing P2 grants:** Low — existing P2 grants are not consulted by the new port; the risk is a permissive default implementation of the port, which the contract forbids (fail closed, explicit grant required).

**Logging/provenance:** The full envelope is the decision input, so provenance is intrinsic; decision id/policy version/expiry are explicit fields.

**Adversarial tests:** port returns DENY/REQUEST_MORE_EVIDENCE/exception → zero transport calls; mismatched envelope field → DENY; expired/revoked → DENY; wildcard envelope cannot substitute.

**Implementation complexity:** Medium — new port, envelope type, adapter wiring, and a governance implementation; two authority boundaries to maintain instead of one.

### Recommendation

**Option A (smallest enforceable option).** It adds a distinct external-egress action plus exact `scope`/`budget_ref` rule-matching to the existing frozen P2 engine, preserving all P2 grants unchanged, requiring no new port, and keeping a single authority boundary. It satisfies every contract property in §4 with the least surface area. Option B is reserved for P12/OCE migration if a provider-neutral, multi-provider egress boundary is later required.

---

## 6. Canon sections affected

- Book V §13.2 — policy rule matching vocabulary (add external-egress action, scope/budget_ref matching).
- Book V §15.3 — discovery adapter port contract (egress gate precondition).
- Block 2 (canon 2.1/2.2) — DiscoveryPlan budget, tier ceiling, source allocation, query identity.
- Block 15 — AdapterOutcome typed statuses (AUTH_FAILURE/RATE_LIMITED/PROVIDER_FAILURE/NOT_CONFIGURED/UNSUPPORTED_QUERY/NO_RESULTS/PARTIAL_RESULTS/OK).
- P2 governance shim (`qcae/governance/standalone/policy.py`, `authority.py`) — extended rule-matching, no behavior change to existing grants.
- P3-T02 GitHub discovery adapter (`qcae/discovery/github/adapter.py`) — unchanged; already fail-closes on the authority decision it receives.

---

## 7. Migration and compatibility implications

- **No P2 grant is widened:** existing `MAY_DISCOVER` ALLOW rules govern internal discovery only; external egress requires the new explicit action/scope rule.
- **Additive only:** no existing field is removed or repurposed; `scope`/`budget_ref` move from "carried but unmatched" to "rule-matched."
- **Adapter unchanged:** P3-T02-R1 C01–C07 behavior is preserved; the adapter's existing C01 binding gates (`request_ref`, `action`, `outcome`, structural validation, fail-closed on exception) already implement §4.2.
- **Operator action required:** deploy versioned policy rules naming the external-egress action and the intended GitHub scope/budget_ref; without such a rule, all external egress fails closed (current `NOT_CONFIGURED` behavior preserved).

---

## 8. Logging and provenance implications

- `AuthorityRequest.context` already records `provider`, `query_id`, `atom_id`, `family_id`, `cost_tier_ceiling`, `scope`, `budget_ref`, `classification`, `risk_class` (P3-T02-R1).
- Option A adds the matched external-egress rule id and policy version to `PolicyDecision.rule_ref`/`policy_version`, carried through to `AuthorityDecision`.
- Every denial is logged as `NOT_CONFIGURED`/`AUTH_FAILURE` with a message naming the failed gate and "zero transport calls"; no lead, revision, or raw artifact ref is emitted on denial.

---

## 9. Adversarial tests (qualification, not ratification)

1. Broad `MAY_DISCOVER` ALLOW (`action="*"`, `resource="*"`, `scope=""`, `budget_ref=""`) does NOT authorize GitHub external egress; engine returns DENY/NO_MATCH for an explicit egress scope.
2. Same broad rule matches internal discovery only; an identical request with `scope="github-external-search"`, `budget_ref="plan-001"` must not inherit the grant.
3. `decision.request_ref != request.request_id` → zero transport calls (C01).
4. `decision.action != MAY_DISCOVER` → zero transport calls (C01).
5. `decision.outcome == DENY` / `REQUEST_MORE_EVIDENCE` → zero transport calls (C01/C05).
6. Authority provider raises → zero transport calls, fail closed (C01).
7. Baseline/plan contract or version mismatch → zero transport calls (C03).
8. Atom outside `baseline.external_target_atoms` → zero transport calls (C03).
9. Effective tier below code-search threshold → no code transport call (C04).
10. `max_queries`/`max_source_calls`/`max_results_inspected` exhausted → zero further calls (C04).
11. 401 → AUTH_FAILURE, `retry_after_seconds` None; 403 with `X-RateLimit-Remaining: 0` → RATE_LIMITED with duration-based retry; 403 without → AUTH_FAILURE; 429 → RATE_LIMITED (C06).
12. Invalid pagination cursor refused, zero transport calls (C06).
13. Missing/malformed `items` → PROVIDER_FAILURE, never NO_RESULTS (C06).
14. Repository failure is terminal: no code-search continuation, no retained leads (C05).
15. Per-surface lead completeness matches surface coverage; no `github:unknown` fabrication; raw SHA refs classified as non-durable fingerprints (C07).
16. Expired/revoked authorization → zero transport calls.

---

## 10. Relationship to P3-T02-R1 and P3-T03

- P3-T02-R1 is **preserved as the inspectable code baseline** (commit `e1005f51d`, local + remote `agent/qcae-p3-t02-github-discovery`). Its C02 blocker is the authority-model gap this amendment closes; R1's adapter repairs do not pretend the frozen model enforces egress scope.
- A-002 is **not implemented** and **not ratified** by this document. Implementation awaits operator approval.
- P3-T03 (live GitHub transport, Research Mesh delegation seam, worker integration) remains paused; no egress authority is granted by this draft.

---

## 11. Open questions for operator

1. Confirm Option A is the desired design (vs Option B).
2. Confirm the external-egress action name and scope/budget_ref matching semantics (exact vs prefix-star).
3. Confirm whether expiry/revocation is enforced via `expires_at` on the decision or a separate revocation check.
4. Confirm A-002 may proceed to implementation only after this operator ratification; P3-T03 remains paused regardless.

---

*End of A-002 draft. Do not implement, ratify, merge, or begin P3-T03 on the basis of this document alone.*
