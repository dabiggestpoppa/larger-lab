# PFT — NEXT PLAN (after B0)

## Gate state

    human_review_required      = true
    next_checkpoint_authorized = false (until operator approves B0 seal)

## Next checkpoint: PFT-B1-SPECIFICATION-SEAL

Scope (authorized by the current build prompt):

1. Convert PFT specifications into deterministic machine-readable truth:
   - A1 v2.2 RAW machine spec (assets, time semantics, windows, constants,
     schedules, state rules, fail-closed behavior, execution precedence).
   - A0-GENESIS lineage registration.
   - Q0-TRANSMISSION lineage registration (independent; no borrowing from A1).
2. Complete the formula registry: all 19 A1 formula ids map to
   implementation targets, tests, and expected failure behavior.
3. Complete the parameter register: every constant used by the machine
   spec must be registered and classified; RAW must reference only
   AUTHOR_CONSTANT / RESEARCH_CONSTANT.
4. Freeze RAW/TWIN namespace isolation.
5. Tests: spec schema validation, constant freeze, formula completeness,
   fail-closed state enumeration.

B1 PASS gate and artifact list are defined in the build prompt sections
16-17. Commit message: `PFT-B1: seal A0 A1 Q0 specifications`.

## Standing prohibitions (unchanged)

- No economic testing capability invoked.
- No optimization.
- Confirmation/holdout untouched.
- No branch creation outside the authorized PFT branch.
