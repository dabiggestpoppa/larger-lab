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
                   -> verify_citation()               re-derives the citation from the bytes on disk
                      |- emit()                      refuses to publish an unverified baseline
                      `- decide_gate()               derives both checks itself, blocks on either
```

Consumers validate against the declaration rather than restating it: a second copy
of a path, command, digest rule or publishability check is a defect, not a
convenience.

**No verification input may be absent, empty or favourable by default**
(STRESS-G8ARCH4). The tree a package is archived for is required, with no default,
at every entry point: `check_baseline(tested_sha="")` and
`verify_citation(expected_tested_sha="")` refuse rather than skip their comparison
or fall back to the citation's own recorded tree — a check that verifies the
evidence against the evidence's self-report is the defect this gate exists to
forbid. An underivable tree is reported as an unverifiable tree, not as the absence
of a lag, and the gate derives its own citation check instead of accepting one,
because a check a caller can omit is a check that does not run. The reader accepts
no exit-status claim either: a JUnit document cannot show the producing process's
exit code, so the refusal that claim drove is driven by the counts measured from
the artifact, and the one honest partial case — a skipped test — is named in the
receipt and in the result prose rather than smoothed into a count.

The red evidence for every finding is a committed harness, not prose: two
harnesses (`scenarios/g8_pre_repair_red_transcript.py` for the first review,
`scenarios/g8_arch_red_transcript.py` for the passes after the closure matrix)
extract their named commits read-only, run the same probes against that code and
against the working tree, and archive the transcript they print. Each probe line
ends in `verdict=RED` or `verdict=GREEN`, and the closure matrix cites an id from
one of those annexes, so a row cannot cite evidence that no longer reproduces.
The canonicalization rule is a versioned NAME whose definition is data and whose
fingerprint is published, so the meaning behind a published label cannot move
while the label stays.

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