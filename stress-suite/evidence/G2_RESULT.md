# G2 — Core Phase-Control Scenarios (S01–S05)

**Gate:** G2 | **Status:** `PASS_G2_CORE_PHASE_CONTROL` | **Tests:** 225/225 | **Cost:** $0

## What G2 built

The G1 harness could validate phase **topology** but deliberately not decide
*why* a transition should occur. G2 adds:

1. **G2-P0 identity binding** — governed phase/lifecycle/authority actions are
   attributed to `event.actor`; a payload `authority_level` claim must exactly
   match `AuthorityState` (or be omitted and derived); unknown actors fail
   closed; RATIFY binds `ratifier == event.actor`; `seed_level` rejects unknown
   authority levels; risk classes outside the canonical capability-grant
   vocabulary fail closed.
2. **G2-A generic evidence adjudicator** — a `PROVISIONAL_SCENARIO_TEST_POLICY`
   of declarative predicates (`all_of` / `any_of` / persistence / prior-history /
   dependency-centrality rigour / patch pressure / affected surface) evaluated
   against the **frozen** `PhaseEvaluationContract`. Grade-less gates inherit
   contract thresholds, so the frozen contract genuinely participates. No
   scenario-ID branches; no scalar score; fail-closed grades.
3. **Sealed expectations** — `expected_phase_trace.json` and any hidden ground
   truth are stripped from the decision-grade projection; metamorphic tests
   prove flipping them changes nothing in any run.
4. **Scenario runner** — proposals are applied exclusively through the governed
   executor (authority binding + forbidden rules + topology prefilter), the
   evaluation contract is frozen and fingerprinted before the first decision,
   and per-transition evidence refs are recorded.

## Scenario outcomes (all derived from observable evidence)

| scenario | terminal | evidence-derived path | verdict |
|---|---|---|---|
| S01 old theory dies slowly | `NEW_STABLE` | STABLE → WATCH → STABLE → WATCH → ESCALATION_REVIEW → TRANSFORMATION_CANDIDATE → TRANSFORMATION_WINDOW → RECONSOLIDATION → NEW_STABLE | PASS |
| S01_WEAK sensitivity | `STABLE` | STABLE → WATCH → STABLE → WATCH → STABLE — same CORE centrality, weak contradiction ⇒ **no transformation** | PASS |
| S02 false revolution | `STABLE` | STABLE → WATCH → ESCALATION_REVIEW → (defect holds) → NO_CHANGE → STABLE — novelty opened review, leakage/survivorship reversed it | PASS |
| S03 patch maze | `TRANSFORMATION_CANDIDATE` | … two local repair cycles … → WATCH → ESCALATION_REVIEW → TRANSFORMATION_CANDIDATE — only the SAME causal signature aggregated; SIG_X never did | PASS |
| S04 leaf failure | `STABLE` | STABLE → WATCH → ESCALATION_REVIEW → HOMEOSTATIC_REPAIR → STABLE — one adapter fault stayed local | PASS |
| S05 two non-dominated models | `STABLE` (+ plural knowledge) | … → RECONSOLIDATION → PLURAL_MODEL_STATE → STABLE — nothing averaged, no forced winner | PASS |

## What the scenarios prove

- **S01**: CORE centrality raises review rigour (an extra independent-confirmation
  gate) but never grants immunity; a single weak period cannot transform; two
  separate evidence lineages + persistence eventually can; the old mechanism is
  SUPERSEDED with lineage retained, never deleted.
- **S02**: novelty alone cannot vote for transformation; a data-quality defect
  (timestamp leakage / survivorship bias) parks escalation via pass-1 holds; the
  failed claim becomes DEMOTED knowledge with an explicit reopen condition; the
  leaked dataset and the original anomaly are never erased.
- **S03 vs S04**: the same generic harness infers *repeated shared causal
  signature ⇒ scope escalation* from a *single leaf fault ⇒ local repair* —
  from evidence fields, not scenario IDs.
- **S05**: no forced consensus; PLURAL_MODEL_STATE is reachable; institutional
  phase returns to STABLE while M4 keeps both models ACTIVE (explicit M4/M5
  separation). S01 resolves to NEW_STABLE; S05 preserves multiplicity — outcomes
  differ on evidence shape, not scenario name.

## Sealing and determinism

- Expected traces are applied only post-hoc; two runs with a deliberately wrong
  expected trace produce byte-identical fingerprints.
- All runs are deterministic and model-free; receipts on disk reproduce exactly.
- G2X audit: all 20 cross-contract pairs have distinct fingerprints; foreign
  contracts stay frozen and byte-stable; a foreign-contract run can only PASS
  when its behavior is identical to the own-contract run (no silent
  inheritance).

## Tensions recorded (not resolved)

- **CON-02 / CON-03** carried from G0 (PO posture vs Governor decision;
  preregistration vs threshold opacity).
- **AMB-03 / AMB-08 / AMB-11** carried from G1R (independence aggregation,
  reversible low-scope transformation boundary, automated causal-signature
  discovery).
- **AMB-13 (new)** — M5 outcome semantics are expressible only with
  history-shaped gates (`prior`); the A-010 channel vocabulary has no dedicated
  "replacement validated" channel. Represented, not resolved.

## Mutations

cloud=0, production=0, capital=0, authority changes=NONE, architecture
amendments=NONE. A-004 … A-010 were not modified.