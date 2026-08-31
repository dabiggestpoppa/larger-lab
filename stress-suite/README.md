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