# G3R Counter-Attractor Audit

Scope: the bounded adversarial check can no longer be influenced by evidence it never authorized, and "strong consensus" means actual vote concentration.

## 1. Budget is real (G3R-01)

`run_counter_attractor()` walks findings in order and consumes at most `spec.budget` ADMISSIBLE findings:

- `contradiction_after_budget_is_ignored`: budget 3, findings 1–3 clean, #4 contradicts → terminal stays `NO_CHANGE`, `discriminating_contradiction_found=False`, `E4` absent from `evidence_produced`.
- `contradiction_within_budget_is_honored`: a contradiction in finding #2 of 2 consumed → `CHALLENGE_SUPPORTED`.
- `evidence_produced_contains_only_consumed_findings`: only consumed evidence ids appear.
- `cost_equals_consumed_authorized_methods`: `cost_units == budget_used * cost_per_method`.
- `zero_findings_does_not_fake_budget_consumption`: 0 findings → `budget_used=0`, `cost_units=0`, `UNRESOLVED` (no authorized action completed; budget exhaustion is never faked).

## 2. Method contract enforced (G3R-02)

Every consumed finding must carry a `method` in `spec.allowed_methods` (empty ⇒ canonical `COUNTER_ATTRACTOR_METHODS`):

- An unauthorized method carrying a contradiction cannot support a challenge (recorded `non_admissible_findings`, `UNRESOLVED`).
- An authorized method CAN support a challenge.
- An unknown method is preserved in `non_admissible_findings` but consumes no budget and never affects the verdict; `method_budget_and_finding_count_are_consistent` proves consumed ≤ budget and evidence count == consumed count.

## 3. Strong consensus is actual concentration (G3R-03)

New `EcologyFacts` fields are vote-topology facts, explicitly NOT evidence strength:

- `dominant_vote_count`, `dominant_vote_ratio`, `distinct_conclusion_count`.
- The shared policy gate is `dominant_vote_ratio > 0.6` (strict): 8/8 (1.0) triggers; 3/2 (exactly 0.6) does NOT; 3/3 (0.5) does NOT; reviewer count alone (8 reviewers, 4/4) does NOT.
- `CounterAttractorSpec.min_dominant_vote_ratio_for_trigger` mirrors the strict gate at the contract layer (defense in depth).
- Duplicate correlated votes (S06 monoculture, ratio 1.0) still fail `independent_confirmation_satisfied`, so the strong-consensus route never fires for them.

## 4. Honest termination preserved

- S09 still closes `NO_CHANGE` (3/3 clean authorized findings at budget 3), no dissent manufactured, no confidence penalty, no loop.
- `CHALLENGE_SUPPORTED` remains reachable when a consumed authorized finding contradicts — the machinery is not hardcoded to NO_CHANGE.
