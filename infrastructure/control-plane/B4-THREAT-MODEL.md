# Book 4 — Canonical Threat Model and Trust Boundary (B4-CXR7U1)

> **One canonical statement of what the OCE Book 4 local-first runtime is and
> is not.** Every security claim in source documentation, the configuration
> input inventory, the lifecycle authority matrix, the adversarial matrix,
> tests, and evidence must be consistent with this boundary. Any later
> feature that depends on a security property MUST state its position against
> *this* document first (B4-CXR7U1).

## 1. The trusted computing base (operator disposition, B4-CXR7U)

Book 4's operator accepted the CXR7 blocker finding as technically correct:
within the current local-first / private-first Book 4 runtime there is **no
enforceable parent/child issuance boundary between same-principal processes**.

> **THE OCE SUPERVISOR, API, WORKER, MIGRATION, AND OUTBOUND-WORKER
> PROCESSES RUNNING AS THE SAME APPROVED LOCAL OS PRINCIPAL FORM ONE
> TRUSTED COMPUTING BASE.**
>
> They are **not mutually hostile security principals.**

Therefore `OCE_ACTIVATION_ENVELOPE` is:

```
AUTHENTICATED PARENT-LAUNCH HANDOFF
WITH ROLE/AUDIENCE CONSISTENCY CHECKING
```

It verifies that a child process was launched by a legitimate parent
activation (shared-secret MAC + role/audience consistency + canonical
re-derivation). It is **not** a security boundary against arbitrary code
already executing as the approved OCE operating-system account.

**The correct statement is:**

```
SAME-PRINCIPAL ARBITRARY CODE EXECUTION IS FULL LOCAL OCE COMPROMISE.
```

Such an attacker could already read the worker token, the PostgreSQL
credential, the runtime store, source modules, process state, and the
activation-handoff key — verification material and issuance material are
the same key under one OS principal.

### What we therefore DO NOT claim

- a compromised same-account child cannot read the HMAC key;
- a compromised child cannot create another MAC;
- 0600 file permissions isolate same-user OCE processes;
- symmetric verification material cannot provide issuance material;
- Book 4 implements mutually distrustful process roles;
- RLIMIT/resource bounding provides network, filesystem, identity, syscall,
  or hostile-code isolation;
- a boolean network policy check is OS network enforcement.

## 2. In-scope (the realistic adversarial model)

The Book 4 runtime defends against **adversarial values supplied to
legitimate OCE processes**, not against hostile code running as the OCE
account:

- adversarial values in the environment, CLI, config files, URLs, DSNs,
  paths, and payloads;
- forged handoff data without approved-store access (no valid MAC);
- malformed, stale, expired, replayed, or wrong-audience handoffs;
- unauthorized secret initialization or rotation (e.g. an ambient
  `POSTGRES_PASSWORD` that never self-legitimates);
- unauthorized migration, configuration override, or destination changes;
- corrupt persisted security state (replay ledgers, secret stores) — must
  fail closed, never behave like empty state;
- partial writes, concurrency, crash recovery, and replay races (single-use
  means at most one concurrent consumer);
- job parameters treated as untrusted data (never source code, executables,
  module paths, shell fragments, or environment/fs authority);
- direct child entrypoint invocation without the required parent handoff
  (ambient-only input cannot create a valid MAC without store access);
- divergence between a request/correlation ID and the durable decision it
  claims (audit idempotency is exact).

## 3. Out-of-scope (explicitly NOT defended against)

- arbitrary code execution as the approved OCE OS account;
- malicious trusted OCE source code;
- a compromised trusted OCE component;
- an attacker able to read or modify `.runtime` (the approved store is
  inside the TCB);
- administrator/root/SYSTEM compromise;
- kernel or host compromise;
- repository/runtime code replacement;
- same-user debugger/process-memory access;
- mutually hostile same-principal subprocess isolation.

These out-of-scope threats require a **real OS trust boundary** (separate
OS principal, restricted token, per-role container UID, or equivalent) —
a scope expansion Book 4 explicitly does **not** authorize (hard boundary,
CXR7U section 12).

## 4. Truthful defense-in-depth still in force

Within the single TCB, Book 4 still enforces defense-in-depth:

1. **Authenticated activation**: a child may start only with a MAC-verified,
   role/audience-consistent, non-stale, single-use handoff; ambient JSON is
   never authority.
2. **API-level least privilege (B4-CXR7U2)**: verified child contexts expose
   NO parent issuance API (`build_envelope` / `child_environment`). This is
   *API-level least privilege and defense in depth* — it is NOT OS
   isolation, and arbitrary same-user Python can still import internal
   modules or read the runtime key.
3. **Hard code-execution lock (B4-CXR7U3)**: only fixed repository-owned
   allowlisted programs execute; unknown job types fail closed; job
   parameters are data, never code/executable/import-path/shell.
4. **Fail-closed persisted security state (B4-CXR7U4)**: corrupt/unreadable
   replay state blocks use AND mutation; exactly one concurrent consumer
   can use a single-use handoff nonce.
5. **Exact durable audit (B4-CXR7U5)**: a request ID reconciles only the
   exact same canonical durable decision through the real PostgreSQL sink.
6. **Complete-or-nothing initialization (B4-CXR7U6)**: `configure` either
   commits a complete governed state or leaves the previous state intact.
7. **Truthful isolation reporting (B4-CXR7U3)**: resource bounding, network
   policy, and OS enforcement are reported literally — never overstated.

## 5. Execution trust and the hard lock

```
GENERATED, DOWNLOADED, THIRD-PARTY, PLUGIN, STRATEGY, USER-SUPPLIED,
OR MODEL-PRODUCED CODE MAY NOT EXECUTE UNTIL A REAL OS ISOLATION
INCREMENT IS SEPARATELY AUTHORIZED AND PROVEN.
```

Current execution trust: **repository-owned allowlisted programs only**,
selected by `program_for(job_type)` inside `representative_jobs.py`.
No firewall, network namespace, VM, restricted account, or container-per-role
conversion is built in this increment.

## 6. Network truth

```
network authorization:  denied by Book 4 policy
OS network enforcement: not implemented
current execution trust: repository-owned allowlisted programs only
```

OS-level network denial is NOT implemented; the policy boolean merely
forbids granting network to jobs. This is reported literally everywhere.

## 7. Pronunciation

- `ActivationHandoff` — the authenticated launch handoff carrier (alias of
  `ActivationEnvelope`).
- `VerifiedChildContext` — the child-consumer type (no issuance API).
- `ParentActivationContext` — the parent issuer type (may issue handoffs).
- Resource bounding (POSIX rlimits / Windows watchdog) is reported as
  **resource limits available** (`resource_limits_available`), never "full
  isolation".

## 8. Consistency rule

Any document or test that claims a security property MUST resolve against
this boundary first. In particular:

- never describe 0600 same-user readability as process-role isolation;
- never describe a MAC as preventing a same-account actor from MACing;
- never describe `resource_limits_available` as filesystem/network/identity
  isolation;
- never claim zero state mutation for `recover()` without accounting for its
  classified stale-PID cleanup.