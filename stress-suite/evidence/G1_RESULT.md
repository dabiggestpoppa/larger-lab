# G1 — Harness Contracts — Result

**Status:** `PASS_G1_HARNESS_CONTRACTS`
**Branch:** `agent/oce-institutional-stress-suite-build`
**Starting SHA:** `df2abf8334e8cdbdf6a390b2c5c647f8060eae73`
**Ending SHA (code):** `5fc4d97717a819c5d18407f1764c8263fb7bea0e`
**Tests:** 77 / 77 passing (0 failures), local-first, $0 cost.

## What was built

A generic, deterministic, model-free harness under `stress-suite/`:

- **M5 Governor phase machine** (`engine/phase.py`): A-010 §3 graph + Book §5
  holding/terminal outcomes as a provisional edge table; vector-preserving
  `PhaseDecisionRecord`; no scalar transition authority.
- **M4 knowledge lifecycle engine** (`engine/lifecycle.py`): A-009 §9 states as a
  `PROVISIONAL_TEST_CONTRACT` edge table; provenance never deleted; replaceable
  without rewriting traces; no auto-promotion on reopen.
- **M5/M4/M1 separation** (tests): phase, knowledge, and capability-truth-label
  machines are independent.
- **Authority firewall** (`engine/authority.py`): capability ≠ authority,
  operator preference ≠ evidence, confidence ≠ confirmation, research ≠ execution
  authority, window ≠ capital; a worker may propose but never self-ratify an
  authority change.
- **Forbidden-transition validator** (`engine/forbidden.py`): 10 named negative
  invariants (G1 §10) with tests.
- **Independence vector** (`engine/independence.py`): 10 overlap dimensions;
  raw reviewers vs distinct lineages kept separate; summary explicitly
  NON-AUTHORITATIVE; allocation origin observable (G0 Q3).
- **PhaseEvaluationContract** (`engine/evalcontract.py`): versioned,
  freeze-once, `visibility_policy` preserved (CON-03 measurable, not resolved).
- **Deterministic replay** (`engine/replay.py`): same inputs + same contract
  versions ⇒ same fingerprint; strict seq ordering; illegal events recorded, not
  applied; no model/wall-clock dependence.
- **EpochManifest** round-trip (`engine/epoch.py`); **Object contracts** for the
  full G1 object set; **generic fixture loader** with sealed ground truth;
  three smoke fixtures (legal, illegal, reactivation).
- **JSON Schemas** (`schemas/`) following the control-plane conventions.

## Pass criteria check

1. Generic harness, no scenario-specific logic in the engine — ✅ (smoke fixtures carry all scenario data; engine has no S01–S24 branches/names).
2. M4 and M5 explicitly separate — ✅ (separate engines + separation tests).
3. Phase transitions machine-checkable — ✅ (edge table + validator).
4. Forbidden transitions machine-checkable — ✅ (10 rules + negative tests).
5. Evidence provenance survives transitions — ✅.
6. Independence as a vector, not agent count — ✅.
7. Authority cannot rise from capability/evidence alone — ✅.
8. Negative knowledge preserves reopen semantics — ✅.
9. Unresolved patterns exist without forced classification — ✅ (no `closest_category`/channel-required fields).
10. Evaluation contracts freeze correctly — ✅.
11. Deterministic replay succeeds — ✅ (6 replay tests).
12. EpochManifest round-trips — ✅.
13. Tests run locally — ✅.
14. cloud mutations = 0 — ✅.
15. production mutations = 0 — ✅.
16. capital mutations = 0 — ✅.
17. authority changes = NONE — ✅.
18. Open G0 tensions remain visible, not declared solved — ✅ (CON-02/03, AMB-01/03/05/06/07/08/11/12 carried forward in README + receipt).

## Stop conditions

No G1 stop condition triggered. No existing canonical control-plane contract
conflicted with required semantics; the engine references them by convention and
did not modify any B2/B3 artifact. Deterministic replay required no production
dependency. No A-009/A-010 text was amended.

## Recommended next action

`AUTHORIZE_G2` — implement S01–S05 (core phase control) against this harness.

*A failing architectural test remains valuable evidence; we preserved the harness
to make illegal shortcuts and ambiguous transitions fail closed before any
scenario runs.*