# Book V — Block 13 Freeze Review

**Result:** READY TO FREEZE

## Chain

```text
13.1 Local Runtime
→ 13.2 Local Policy Engine
→ 13.3 Local Evidence Store
→ 13.4 Local Secrets Boundary
→ 13.5 Local Sandbox Manager
→ 13.6 Local Job Queue
→ 13.7 Standalone CLI/API
→ 13.8 Graceful OCE Absence
```

## Frozen Invariants

1. Standalone QCAE is a real operating mode, not mocked OCE.
2. Local-first control plane is the default.
3. Runtime services start simple and split only when evidence justifies it.
4. Authority is mediated by a provider contract and policy-as-data.
5. Evidence/memory is structured, persistent, append-oriented, and hashable where practical.
6. Secret access is mediated and least-privileged.
7. Sandboxes are profile-driven, disposable, and backend-abstracted.
8. Long-running work is queue/state based, crash-safe, and idempotent.
9. CLI/API expose domain objects rather than worker/provider internals.
10. OCE absence does not block core QCAE work.
11. OCE failure never expands local authority.
12. Historical standalone evidence remains intact after future federation.
13. Core domain modules do not directly depend on OCE implementation packages.

## Block 14 Handoff

Block 14 must define the exact governance seam: authority provider, evidence submission, identities, policy migration, registry federation, event model, and anti-pollution rules that allow OCE to govern QCAE without absorbing its core domain logic.

**Block 13 status: FROZEN v0.1.**
