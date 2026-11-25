# 01 — Directive, granted scope, and the exact ask

## 1. Reference lock, verified at start

| Reference | Value | Verified |
|---|---|---|
| Starting SHA | `13086755d22a539c6a4dcb20e782bce97fcde82d` | `git rev-parse HEAD` matched; worktree clean; 0 commits ahead |
| Production design R0 | `295acb5245ecc47d6f5c0a07f8ff631aa7217c15` | ancestor of the starting SHA; untouched |
| Consolidation candidate | `6de26be9…` | untouched, never checked out |
| Historical producer | `b76ba806…` | untouched |
| Independent security spec | `6e6ef219…` | untouched; not merged (permitted branch `…consumer-security-r1` left alone) |

No OCE, QCAE or unrelated project content is present on this branch.

## 2. What the directive granted

`AUTHORIZE_D1_ONLY` — exact-file authorization for two new Python files:

```
quant-lab/src/crypto_sensor_fabric/normalization/consumer/models.py
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_contracts.py
```

Plus, narrowly: the I05 audit amendment, the I10 audit amendment, the mechanical I11R2
inventory republication, and additive evidence under the Bloc 5 prefix.

Explicitly **not** authorized, and not created: `consumer/policy.py`,
`consumer/custody_authority.py`, `consumer/rebinding.py`, `consumer/__init__.py`,
`test_b5_p3_consumer_security.py`, any provider approval or manifest modification.

## 3. What the grant does not reach

`normalization/consumer/` is a **new subpackage directory**, and the I01 audit
(`test_b5_i01_scope_audit.py::test_only_authorized_subpackages_exist`) freezes the set of
subpackages under `normalization/` to six names. `consumer` is not one of them. Adding it
fails that audit, which is outside the two amendments granted.

§2 of the directive is explicit that historical exceptions are preserved **without
expansion**, and §0 is explicit that an unauthorized path is disclosed rather than created
silently. Extending I01's allowlist is exactly the expansion §2 forbids, so it was not done.

### `__init__.py`: not required, and this is measured

The directive asked that an `__init__.py` need be *demonstrated*, not assumed. It is not
needed: with no `__init__.py` present, `consumer/` resolves as an implicit namespace package
inside the regular `normalization` package, and both the implementation and its 32 tests
imported and ran (`32 passed`). One inventory unit is therefore avoided, and the ask in §4
does **not** include that file.

## 4. The ask, exactly

A third amendment is required. Precisely:

1. **I01** — one named entry in `allowed` at `test_b5_i01_scope_audit.py:89`:
   `"consumer"`. No prefix is widened; the audit already grows this set by one named package
   at a time (the I09P2A precedent is recorded in its own comment).
2. **I05** — one exact-file entry, `src/crypto_sensor_fabric/normalization/consumer/models.py`,
   admitted by the `rung1_exact_paths` predicate prepared in `03_PREPARED_AMENDMENT_NOT_APPLIED.md`.
3. **I10** — the same exact-file entry, and the same predicate.
4. **I11R2** — the mechanical republish, `python_files_scanned` **1,102 → 1,104**.

Still not requested, and still not authorized by granting the above: Rung 2 verification
logic, custody authority, rebinding, provider trust, the sibling security suite, or any
manifest change.

## 5. Commit ladder on this branch

| Commit | Message | Status |
|---|---|---|
| A1 | `B5-P3-R1-AUTH: disclose exact-file D1 authorization` | **published** — this directory |
| A2 | `B5-P3-R1-BUILD: implement production consumer data contracts` | **not created** — blocked as described |

The A1 commit introduces this packet; its identity is the branch head recorded in the final
report. There is no A2, and none is implied.
