# OCE Golden System
## B5-I8 — Amendment 001: CI Selection Surface — v1.0

**Document ID:** OCE-B5-I8-AMEND-001
**Version:** 1.0
**Status:** `OPERATOR_RATIFIED` under `AUTHORIZED_STAGE=B5-I8-RATIFICATION` (2026-11-06)
**Stage:** B5-I8 · **Contract:** `OCE_B5_I8_IMPLEMENTATION_CONTRACT_v1.0.md` · **Plan:** `OCE_B5_I8_CONSTRUCTION_PLAN_v1.0.md`

---

## 1. The clause this amendment supersedes

`OCE_B5_I8_CONSTRUCTION_PLAN_v1.0.md` §1, rung **R6**, "Allowed files" column:

> `.github/workflows/b1-i1r-validation.yml` (additive only) + evidence docs

and its evidence-output column:

> artifact `b1-i1r-evidence-<run_id>`

These are the only two sentences in the frozen B5-I8 packet that place the audit's
CI selection step *inside* the pre-existing authoritative workflow file and bind the
audit's artifact name to that workflow's artifact.

## 2. Why literal compliance is impossible without weakening ratified evidence

`OCE_B5_I7_EL09_X1_SUPERSEDING_MANIFEST_v1.0.json` contains a **whole-file**
immutable row for `.github/workflows/b1-i1r-validation.yml`. Adding the B5-I8
selection step changes that file's bytes, so
`test_b5_i7_evidence_laws.py::TestEL09` fails on the manifest hash and size.

Reproduced on the implementation head, not asserted:

```
$ python -m pytest infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py -q
=> 26 passed, 1 failed   (failure: manifest row hash/size mismatch for b1-i1r-validation.yml)
$ git checkout -- .github/workflows/b1-i1r-validation.yml
$ python -m pytest infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py -q
=> 27 passed
```

The historical manifest row is frozen and must not be edited (EL09 is the append-only
law of the ledger and its manifest). Editing it to accept new bytes would make any
workflow drift retroactively "verified", which is exactly the weakening EL09 exists
to prevent. Therefore the conflict is between two ratified invariants:

- plan R6: the selection step lives in `b1-i1r-validation.yml`;
- B5-I7 EL09: that file is byte-immutable.

One of them must be superseded explicitly. This amendment supersedes **only plan
R6's workflow placement**, because EL09 is an evidence-integrity invariant and R6 is
a placement instruction.

## 3. What this amendment authorizes

The B5-I8 selection surface is the **dedicated additive workflow**
`.github/workflows/b5-i8-audit-validation.yml`, which:

- triggers on `pull_request` targeting `main` — the same event class that produces
  the merge context the plan requires;
- runs on the same pull-request head/merge ref as `b1-i1r-validation.yml`, so both
  workflows observe one head and one merge context;
- requires `permissions: contents: read` and nothing else — no secrets, no hosting,
  no provider, no write scope, no additional authority;
- performs the frozen selection unchanged: the five exact files, floor 40,
  collection == execution, zero fail/error/skip, unique ids, node closure against the
  registry, orphan-file refusal, and fail-closed exit;
- emits its own artifact `b5-i8-evidence-<run_id>` while the untouched
  `b1-i1r-validation.yml` continues to emit `b1-i1r-evidence-<run_id>` on the same
  head. Both artifacts exist; neither replaces the other.

The artifact name is therefore also superseded: B5-I8's evidence lives in its own
artifact, and the plan §5 artifact schema is satisfied by the B1-I1R artifact that
still runs untouched on the same head, with the B5-I8 artifact adding the audit
proofs.

## 4. What this amendment does not change

- The 55 frozen requirements, their ids, kinds, owners and stage identity.
- The 40-node proof surface and its five files.
- The 18 failure classes and the 12-mutation floor.
- Floors: focused 40, adjacent 189.
- Trigger class, node floors, identity requirements (head, tree, merge ref, both
  parents, merge-tree equality), artifact retention, cleanup rules and authority
  boundaries.
- `G16`'s disposition and every limitation label.
- Any production, frontend, console or contract surface.

## 5. Ratification

Ratified by the operator's `AUTHORIZED_STAGE=B5-I8-RATIFICATION` authorization, which
explicitly permits "a narrow operator-ratified amendment for the CI-selection-surface
conflict if the source audit confirms it". The source audit confirmed it (§2, §6).

This amendment does not claim the original clause was satisfied. The original clause
is **superseded**, and both the clause and this supersession remain in history.

## 6. Reproduction record

| Check | Command | Observed |
|---|---|---|
| Pinned file untouched by B5-I8 | `git diff --name-only e999a4a3..HEAD -- .github/workflows/b1-i1r-validation.yml` | empty |
| EL09 green on the implemented head | `pytest .../test_b5_i7_evidence_laws.py -q` | 27 passed |
| Pinned file byte-identical to the manifest row | `TestEL09::test_manifest_rows_recomputed_hash_and_size` | pass |
| Dedicated workflow permissions | `grep -A1 '^permissions:' b5-i8-audit-validation.yml` | `contents: read` |
| Same event class | `on: pull_request: branches: [main]` in both workflows | identical |
| No secrets/hosting/provider | static scan of the dedicated workflow | none |

**Amendment commit:** recorded in `OCE_B5_I8_OPERATOR_RATIFICATION_v1.0.md` §7 and in
the ledger §20.11 after the commit exists. No SHA is predicted in this document.
