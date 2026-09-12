# G3R — Cognitive Ecology Adversarial Hardening

## STATUS: `PASS_G3R_COGNITIVE_ECOLOGY_HARDENING`

- **Authorization:** G3R ONLY. G4 not begun.
- **Starting SHA:** `0f1ccaaa0f33b8b3317f764d393baa51ca51577a`
- **Artifacts head:** `546d23c4671bd5c4755a1dc027f94b8a02fce1e6` (all engine/scenario/test artifacts; the G3R evidence commit follows)
- **Externally verified branch head:** not yet pushed — `G3R_EVIDENCE_RECEIPT.json` `receipt_lineage` uses non-self-referential SHA semantics (G3-P0-C)
- **Tests:** 402/402 — 354 prior preserved (3 upgraded with documented rationale, none weakened) + **48 new adversarial regressions**

## Commits

| SHA | Subject |
| --- | --- |
| `113da0d5` | STRESS-G3R1: harden counter-attractor budget and method enforcement |
| `dba2829d` | STRESS-G3R2: generalize correlation-risk friction triggers (shared policy V2) |
| `37335c49` | STRESS-G3R3: consensus-strength facts, independent-design provenance, tri-state overlaps, provenance registry |
| `0aede9f9` | STRESS-G3R4: explicit capability contract and recommended-vs-executed topology semantics |
| `ed5f2702` | STRESS-G3R5: bind scenario reviewers to the governed provenance registry |
| `6e5c546d` | STRESS-G3RX: adversarial G3R regression suite + documented legacy upgrades |
| `546d23c4` | STRESS-G3R6: regenerate per-scenario receipts under the hardened pipeline |
| `<pending>` | STRESS-G3RR: archive G3R evidence package |

## Defects closed

- **G3R-01 — counter-attractor budget is REAL:** only findings consumed within the authorized budget affect `discriminating_contradiction_found`, `terminal_result`, `evidence_produced`, `cost_units`. A contradiction at finding #4 under budget 3 is ignored (`NO_CHANGE` stands); zero findings never fake budget consumption (`UNRESOLVED`).
- **G3R-02 — method contract enforced:** every consumed finding must carry a method in `spec.allowed_methods` or the canonical CounterAttractor contract; unknown/disallowed methods are recorded as `non_admissible_findings`, never affect the verdict, consume no budget.
- **G3R-03 — strong consensus means consensus:** `EcologyFacts` carries `dominant_vote_count` / `dominant_vote_ratio` / `distinct_conclusion_count` (vote-topology facts, never evidence strength). Counter-attractor strong-consensus requires ratio **strictly above 0.6**: 8/8 triggers, 3/2 (exactly 0.6) and 3/3 do not; reviewer count alone cannot trigger; duplicate correlated votes create no independent support.
- **G3R-04 — correlation without exposure:** the shared policy V2 fires friction on concentration of ANY shared axis (source/model/retrieval ≥ 0.6) OR exposure > 0 at HIGH/MEDIUM consequence. CASE A proves a blind monoculture (exposure=0) still triggers friction; disagreement alone never does.
- **G3R-05 — friction methods govern execution:** `FrictionResult.actions` records every executed action (method, reviewer, budget unit, exposure mode, result); only authorized methods execute; budgets bound actions; no trigger ⇒ zero actions.
- **G3R-06 — fresh vs independent design:** `independently_originated_design` is provenance-based and distinct from fresh context; the fresh-or-design topology constraint accepts either qualifying path; duplicated or UNKNOWN designs never count favorably.
- **G3R-07 — provenance registry-bound:** `ReviewerProvenanceRegistry` binds every profile; CLAIMED vs VERIFIED are separate; registered truth wins and conflicts are recorded; registered UNKNOWN never promotes a self-claim; a worker claiming blind while the registry records prior exposure is corrected.
- **G3R-08 — tri-state dependency:** pairwise overlap is `SAME` / `DIFFERENT` / `UNKNOWN`. UNKNOWN-vs-UNKNOWN is neither independent nor shared; only SAME counts as dependency, only DIFFERENT as separation; unknown axes cannot satisfy independence requirements.
- **G3R-09 — capability explicit:** `min_capability` / `minimum_all_required_roles_capability` require EVERY required reviewer to meet the tier (fail-closed — one HIGH + several BASIC fails an ADEQUATE contract); `minimum_any_reviewer_capability` is the explicit at-least-one semantic.
- **G3R-10 — recommended ≠ executed:** `ReviewTopologyDecision` carries `execution_status` (REVIEW_TOPOLOGY_RECOMMENDED | EXECUTED) and `evidence_obtained`; receipts record topology status and that no evidence was claimed from a recommendation (S07 stays `REQUIRES_INDEPENDENT_REVIEW`).

## Cross-case matrix (all PASS)

- CASE A: 10 reviewers, same source/model/retrieval, exposure=0, 10/10, HIGH → friction triggers, `SUPPORTED_BUT_CORRELATED`.
- CASE B: 6 independent reviewers 3/3 split, HIGH → not strong consensus; no counter-attractor.
- CASE C: budget 3, findings 1–3 clean, #4 contradicts → #4 cannot alter terminal state.
- CASE D: two independent experiment designs, no fresh context → fresh-or-design satisfied (contract permits).
- CASE E: reviewer claims three model lineages; registry says one → one verified lineage wins, conflicts recorded.

## Scenario results (ONE shared policy, V2)

- S06 `SUPPORTED_BUT_CORRELATED` · S07 `REQUIRES_INDEPENDENT_REVIEW` · S08 `SUPPORTED_BUT_CORRELATED` (friction information gain retained) · S09 `INDEPENDENTLY_SUPPORTED` (NO_CHANGE retained) — all `pass: true`, behavior fingerprints byte-reproducible.

## Preserved G3 successes

Axis separation, no effective-independent-agent scalar, pairwise matrix (now tri-state), raw vote preservation, S06–S09 outcomes, cost/resource accounting, rename invariance, sealing, zero model calls — all retained.

## Carried open

- Contradictions: CON-02, CON-03 · Ambiguities: AMB-03, AMB-08, AMB-11, AMB-13
- New contradictions: none · New ambiguities: none

## Mutations / cost

cloud=0 · production=0 · capital=0 · real authority changes=NONE · cost=$0 (local, deterministic, synthetic)

## Recommended next action

`AUTHORIZE_G4`
