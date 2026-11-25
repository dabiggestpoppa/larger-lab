# SENSOR-B5-P3-RUNG1-BUILD-R1 — implementation attempt, and the authorization it hit

**Directive:** `SENSOR-B5-P3-PRODUCTION-CONSUMER-RUNG1-BUILD-R1` · `OPERATOR_DIRECTIVE: AUTHORIZE_D1_ONLY`
**Base:** `13086755d22a539c6a4dcb20e782bce97fcde82d` (authorization packet R0)
**Branch:** `agent/crypto-sensor-fabric-p3-consumer-rung1-build-r1`
**Disposition:** **`RUNG1_BLOCKED_ON_SCOPE_AUTHORIZATION_I01`**

## What happened

Rung 1 was implemented in full — the five data contracts and 32 contract tests — and it
executed green (`32 passed`). It could not be committed, because the granted amendment
scope covers **two** frozen audits and the authorized file path contradicts a **third**:

`test_b5_i01_scope_audit.py::test_only_authorized_subpackages_exist` asserts

```
assert present <= allowed          # allowed = {identity, terms, time, common, sensors, authority}
E   AssertionError: unauthorized subpackages: ['consumer']
```

Its `present` set is `{entry.name for entry in PACKAGE.iterdir() if entry.is_dir()}`, so the
directory `normalization/consumer/` is a subpackage to that audit whether or not it contains
`__init__.py`. D-1 grants exact-file entries in the **I05** and **I10** audits. The I01 audit
is not among them, and §2 of the directive requires historical exceptions to be preserved
without expansion. There is no order of operations that both ships `consumer/models.py` and
leaves I01 green: the path the directive authorizes is the path I01 refuses.

So the implementation was verified, measured, and **withdrawn**, and this packet reports the
blocking condition instead of shipping a branch that fails its own frozen governance.

**A2 was not created.** `A1` is the commit that publishes this directory.

## Why this is not a second planning package

The code exists in this round's record with its hashes, its test results and its A1.1–A1.5
conformance evidence; only the commit was withheld. Given a third amendment, the same content
commits and passes. `01_OPERATOR_DIRECTIVE_AND_GRANTED_SCOPE.md` §4 states the ask exactly.

## Correction to the R0 authorization packet

The R0 blocker matrix asserted that I05 and I10 were the only frozen audits refusing the
paths, and that I09 did not block. Both remain true — and both were re-measured here — but the
matrix never examined **I01**'s subpackage allowlist. That was an omission in R0, not in this
checkpoint, and it is the single reason this checkpoint cannot complete. The corrected matrix
is `02_GOVERNANCE_BLOCKER_MATRIX.md`.

## Packet

| File | Contents |
|---|---|
| `01_OPERATOR_DIRECTIVE_AND_GRANTED_SCOPE.md` | the directive, the exact grant, what was and was not authorized, the ask |
| `02_GOVERNANCE_BLOCKER_MATRIX.md` | every audit measured against the authorized paths, with the exact refusals |
| `03_PREPARED_AMENDMENT_NOT_APPLIED.md` | the amendment as written and as tested, held back deliberately |
| `04_IMPLEMENTATION_RESULT_AND_WITHDRAWAL.md` | what was built, what it proved, and the proof of clean withdrawal |
| `rung1_build_r1.json` | the same facts machine-readable |

## Hard stop

No Rung 2 implementation, no custody authorization, no provider certification, no trust
promotion, no production merge, no program-gate advancement, no self-ratification. The empty
approval manifest and `INTEGRATION_REQUIRED` are untouched; the tracked-Python inventory
remains **1,102**; the canonical universe is **4,733** at digest `1036049742…`, unchanged from
the anchor.
