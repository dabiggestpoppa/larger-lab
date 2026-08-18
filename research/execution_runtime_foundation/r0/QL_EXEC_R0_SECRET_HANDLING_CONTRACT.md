# QL_EXEC_R0_SECRET_HANDLING_CONTRACT

---

## 1. Hard rule

Broker passwords, API secrets, account tokens, and private keys are NEVER stored in committed configuration, the AccountRegistry, or any git-tracked artifact.

The registry stores **secret references**, not credentials.

---

## 2. Reference kinds

- environment-variable key (resolved at process start, never logged);
- OS keyring reference (Windows Credential Manager / DPAPI-backed keyring);
- encrypted secret-store identifier (future secret manager);
- never a literal value.

---

## 3. Residency

- A credential lives only in the OS secret store or the environment of the running process.
- It is loaded at runtime by the `BrokerSession` credential resolver, and only into the specific runtime process bound to that account (one process per directly controlled account).
- It is never written to logs, heartbeats, dashboards, ledgers, or error trails.

---

## 4. Masking

Login/account identifiers are masked in all observability output (TB's `_mask_login` already does this). Only the resolver sees the full value.

---

## 5. Audit obligations

- `quant-lab/mt5/symmetry_trap_executor_fixed.py` and `quant-lab/mt5/production_runtime.py` contain demo login/password/server constants that must be audited before any R1 migration touches those paths. They are legacy, not part of the TB R6.1 runtime, and are left untouched in R0.
- Any future R1 config hash must cover secret references but never their resolved values.

---

## 6. Enforcement tests (future)

- Committed config contains no key matching `password|secret|token|api_key|private_key`.
- A mock resolver can inject a credential without any file access.
- A failed resolve fails closed (EXECUTION BLOCKED / AUTH_FAILED), never a fallback to a default credential.
