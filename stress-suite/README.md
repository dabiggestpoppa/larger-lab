# OCE Institutional Stress Suite

Deterministic adversarial harness that tests whether the proposed OCE
institutional architecture (LL-ARCH v1.1; A-004…A-010) can distinguish when to
**preserve, repair, question, transform, remain unresolved, and stop to ask the
operator** — before ratification.

This is a **test specification**, not self-validating truth. A failing scenario is
a successful research result. We never patch the architecture to make a test go
green.

## Scope (gates)

- **G0 — Planning / architecture ingestion** (`planning/`): authority hierarchy,
  dependency map, contradiction (CON) and ambiguity (AMB) registers. Exit
  `PASS_G0_PLANNING_INGESTION`.
- **G1 — Harness contracts** (`engine/`, `schemas/`, `fixtures/`, `tests/`):
  generic, deterministic, model-free machinery. No S01–S24 scenario logic lives
  in the engine. Exit `PASS_G1_HARNESS_CONTRACTS`.
- G2+ implement S01–S24 (future work; not authorized yet).

## Layout

```
stress-suite/
  planning/     G0 packets + receipts
  schemas/      JSON Schemas (control-plane style) for the canonical objects
  engine/       dataclass models + state machines (M4 lifecycle, M5 phase)
                + authority firewall + independence vector + replay
  fixtures/     generic fixture format + smoke fixtures
  tests/        pytest suite (local-first, deterministic)
  evidence/     gate receipts (machine + human readable)
```

## Design rules (G1)

1. **M4 / M5 / M1 are separate machines** — phase ≠ knowledge ≠ capability label.
2. **Authority is separate** from capability, evidence, phase, knowledge, profit.
   Workers may propose an authority change, never self-ratify one.
3. **No scalar transition authority** — evidence channels are a vector.
4. **Evaluation contracts freeze** — a window's success criteria cannot change mid-run.
5. **Negative knowledge is reopenable** unless operator-authorized permanent.
6. **Unresolved states need no classification** — never force nearest category.
7. **Independence is a vector**, not a count of agent processes.
8. **Provenance is never deleted** by a lifecycle transition.
9. Deterministic replay: same inputs + same contract versions ⇒ same output.
10. No production / cloud / capital mutation surface (test-guarded).

## Where each G8 rule lives

A rule is stated in exactly one layer; the other layers consume it. Data flows one
way — engine → scenarios → evidence — and never back.

| layer | owns |
| --- | --- |
| `engine/g8_*` | the rules themselves: comparison + equivalence classes, guarded properties, the gate decision, the contradiction register, and the test-baseline contract |
| `scenarios/g8_*` | running the surface and publishing: it renders the receipt, matrix and prose, and it derives the tested tree through its one owner (`scenarios/g8_tested_tree.py`). It keeps no copy of any engine rule |
| `tests/` | the adversarial controls; fixtures bind to the tree that owner derives, never to a scenario name or a call site's expectation |

The test-baseline path has one owner per step, so no two components can disagree
about which artifact is the baseline:

```
pytest --junitxml  -> evidence/G8_TEST_RESULTS.xml   declared once (engine/g8_test_evidence)
                   -> read_test_evidence()           admits only that path, inside the tree
                   -> TestEvidence                   the sole carrier of one baseline
                   -> check_baseline()               the sole publishability policy
                      |- emit()                      refuses to publish an unverified one
                      `- decide_gate()               records it and blocks on it
```

Consumers validate against the declaration rather than restating it: a second copy
of a path, command, digest rule or publishability check is a defect, not a
convenience.

The tested tree is DERIVED from Git — the newest commit that changed code or tests —
by that one owner, so the emitter, the harness (`conftest`) and the audit entry
point cannot disagree about it, and a package stays re-derivable from any later
evidence commit. A code commit after the archive is caught by
`test_the_committed_package_names_the_derived_code_tree`; that check is skipped only
in the artifact-producing run (`--junitxml`), which necessarily runs before the
archive it produces exists.

## Running

```bash
python -m pytest stress-suite/tests -q      # from the repo root
python -m pytest tests -q                   # from within stress-suite/
```

Cloud cost target $0; all scenarios are simulations.

## Carried-forward open items (from G0, remain OPEN)

- CON-02 A-009 PO posture vs A-010 Governor decision.
- CON-03 threshold preregistration vs opacity (visibility_policy preserved).
- AMB-01/03/05/06/07/08/11/12 (see `planning/G0_*`).