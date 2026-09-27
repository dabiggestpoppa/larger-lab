# G3R2 — Provenance Closure / Unknown-Semantics Hardening

**STATUS: `PASS_G3R2_PROVENANCE_AND_UNKNOWN_CLOSURE`**

| item | value |
|---|---|
| STARTING SHA | `e787fef30b3cc5864694d3c184e091a0180ce7c4` |
| ARTIFACTS HEAD | `52848620dc64b7ec48556a69e8a6a9bb245a0c37` |
| EXTERNALLY VERIFIED BRANCH HEAD | reported after push (receipt is non-self-referential) |
| TESTS | **456 / 456** (402 prior preserved + 54 new adversarial regressions) |

Governing principle enforced: **UNKNOWN IS NOT INDEPENDENT. UNVERIFIED IS NOT
VERIFIED. A PLANNED REVIEWER IS NOT EVIDENCE. A SELF-CLAIM IS NOT ITS OWN
PROVENANCE AUTHORITY.**

## Commits (8)

1. `74dd311e` STRESS-G3R2A — fail-close missing provenance, explicit fixture authority, prevalence/unknown-coverage facts, unique epistemic paths
2. `18890689` STRESS-G3R2E — validate friction/counter method vocabularies and stop on first discriminating contradiction
3. `70eed99f` STRESS-G3R2G — bind topology capability provenance and unique-path accounting
4. `75d6c38f` STRESS-G3R2B — bind topology/friction secondary reviewer surfaces to the scenario provenance authority
5. `79a3be6b` STRESS-G3R2C — shared policy V3 — single-source prevalence correlation + explicit synthetic fixture authority in scenario contracts
6. `9b2b32cb` STRESS-G3R2F — export provenance-mode and epistemic-path surfaces
7. `b2d3ca0d` STRESS-G3R2X — adversarial provenance/unknown-semantics regression suite + documented legacy upgrades
8. `52848620` STRESS-G3R2R — regenerate per-scenario receipts under the hardened provenance pipeline

## Defect closures

| defect | status | evidence |
|---|---|---|
| G3R2-01 missing registry fails closed | PASS | `bind()` forces every independence axis to UNKNOWN; 7 regressions incl. blind/design claims |
| G3R2-02 no silent self-registration | PASS | `provenance_mode` explicit; default `GOVERNED_REGISTRY` fails closed; synthetic fixture authority explicit |
| G3R2-03 secondary surfaces bound | PASS | topology/friction reviewers bound through the same authority; fake BLIND/diversity/design fail |
| G3R2-04 source-overlap prevalence | PASS | `max_single_source_lineage_prevalence` = 1.0 for partial-bundle shared source; friction triggers (CASE G) |
| G3R2-05 UNKNOWN exposure not FALSE | PASS | true/false/unknown counts + known ratios; strict independence requires known coverage |
| G3R2-06 tri-state into facts | PASS | `known_coverage_by_axis` / `unknown_count_by_axis`; 2-known+8-unknown ≠ 10-known |
| G3R2-07 method vocabulary fail-closed | PASS | unknown counter/friction methods rejected at construction |
| G3R2-08 early contradiction stop | PASS | budget_used = actions actually executed; later findings never consumed |
| G3R2-09 unique epistemic paths | PASS | fresh+design path counts ONCE; duplicated ids once; UNKNOWN provenance not qualifying |
| G3R2-10 capability provenance | PASS | UNVERIFIED fails positive min-capability; registered/synthetic explicit (CASE K) |

## Scenario outcomes (ONE shared policy V3)

| scenario | disposition | fingerprint |
|---|---|---|
| S06 | `SUPPORTED_BUT_CORRELATED` (pass) | `ec879b1fe30196cc1b68a079e4a878ef` |
| S07 | `REQUIRES_INDEPENDENT_REVIEW` (pass) | `0e44a11fba9c977ed3a0997cfa7c4742` |
| S08 | `SUPPORTED_BUT_CORRELATED` (pass, friction gain retained) | `662edcf34c0e41e160f39b39e3998d5c` |
| S09 | `INDEPENDENTLY_SUPPORTED` (pass, counter-attractor NO_CHANGE) | `d8e76f5dbdcd8b4f44e217b243b55c51` |

All four run under `provenance_mode=AUTHORITATIVE_SYNTHETIC_FIXTURE` (explicit in
each scenario contract; the harness owns the deterministic synthetic provenance;
`agent_claims_trusted=false`, `model_calls=0`). The default mode remains
`GOVERNED_REGISTRY`, which fails closed.

## Legacy upgrades (documented, none weakened)

- `test_missing_registry_entry_does_not_promote_claims`: old assertion allowed
  claimed OR UNKNOWN; replacement requires UNKNOWN on every independence axis
  (G3R2-01).
- `_topology` helper: declares `AUTHORITATIVE_SYNTHETIC_CAPABILITY` explicitly;
  the UNVERIFIED gate is proven by new regressions (G3R2-10).
- policy-version assertion V2 -> V3 (semantic change in the shared policy).

## Cross-cases F–K

- **F** self-registered swarm: 10 claimed lineages, no registry, governed mode → independence NOT established.
- **G** partial source monoculture: 10 × [COMMON + unique_i] → prevalence 1.0, correlation visible.
- **H** UNKNOWN exposure with diverse sources/models → strict unexposed requirement NOT satisfied.
- **I** budget 5, contradiction on action 2 → stops at 2.
- **J** one path fresh AND design → one unique epistemic path.
- **K** fake topology (self-claimed HIGH capability, registry UNKNOWN) → verified HIGH-consequence routing unsatisfied.

## Carried open

CON-02 · CON-03 · AMB-03 · AMB-08 · AMB-11 · AMB-13 (all OPEN). No new
contradictions or ambiguities. No effective-independence scalar was minted
(AMB-03 remains open; the pairwise vector and coverage facts are preserved).

## Mutations / cost

cloud=0 · production=0 · capital=0 · authority=NONE · A-009/A-010 untouched ·
model calls=0 · **cost=$0** (local, deterministic, synthetic reviewers).

## Recommended next action

**AUTHORIZE_G4**. Stopping here — G4 not begun. S10–S13 not implemented.
