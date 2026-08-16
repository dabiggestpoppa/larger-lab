# TB-P6.5 — COST-GATE SEAL REPAIR

**Base:** master `31e7ad5e` (TB-P6-ENTRY-ANATOMY-SEAL).
**Scope:** repair a candidate-classification bug only. No gates were changed; the
pre-registered gates from `TB_P6_PROTOCOL.md` are applied identically.
**Artifacts:** `TB_P6_5_REVISED_CANDIDATES.json` (full corrected candidate set) and
`TB_P6_5_DECISION.json` (summary). `P6_CANDIDATE_ENTRY_RULES.json`,
`TB_P6_DECISION.json` and `TB_P6_ENTRY_ANATOMY_REPORT.md` were regenerated with the
fix.

## Root cause

`write_cost_stress()` computes `break_even_mult` as the modeled-cost multiplier at which
EV crosses zero, interpolated over the tested grid {1.0, 1.25, 1.5, 2.0, 2.5, 3.0}. When
EV stays **positive at the maximum tested 3.0x level**, the function returns `NaN`
(break-even lies beyond the tested range). `build_candidates()` then evaluated the
pre-registered cost gate as `break_even_mult >= 1.5` — and `NaN >= 1.5` is `False` in
Python. Every z ≥ 3.0 cell (which is exactly where cost robustness is *best*) therefore
had its cost gate recorded as `false` and its break-even shown as `NaN`.

This is an **artifact-encoding bug**, not a research failure: the underlying EV data
(`P6_COST_STRESS.csv`) always showed EV > 0 at 3.0x for those cells.

## Fix (no gate change)

In `build_candidates()`:

- `break_even_mult == NaN` is now read truthfully as **break-even ≥ 3.0x** (EV positive
  at the maximum tested multiplier) and recorded as `break_even_bound = ">=3.0"` plus
  `cost_survives_3x = true`.
- The pre-registered gate "break-even cost multiplier ≥ 1.5x" then evaluates **PASS**
  (`>= 3.0 >= 1.5`). No extrapolation of an exact break-even beyond the tested range.
- Candidate records now carry `break_even_bound` and `cost_survives_3x` in addition to
  the numeric `break_even_mult` (which remains `NaN` when uncapped).

## Verification (specific cells required by the task)

| Model | z=3.00 | z=3.25 | z=3.50 |
|---|---|---|---|
| TB-B | cost gate PASS, BE ≥ 3.0x | PASS, BE ≥ 3.0x | PASS, BE ≥ 3.0x |
| TB-C-2.5% | PASS, BE ≥ 3.0x | PASS, BE ≥ 3.0x | PASS, BE ≥ 3.0x |
| TB-C-5% | PASS, BE ≥ 3.0x | PASS, BE ≥ 3.0x | PASS, BE ≥ 3.0x |
| TB-C-7.5% | PASS, BE ≥ 3.0x | PASS, BE ≥ 3.0x | PASS, BE ≥ 3.0x |
| TB-C-10% | PASS, BE 2.98x (numeric) | PASS, BE ≥ 3.0x | PASS, BE ≥ 3.0x |

All 15 cells now pass the cost gate (verified by assertion against the regenerated
candidate file).

## Changed grades (4, all upgrades)

| Candidate | Old | New | Reason |
|---|---|---|---|
| TB-B @ z=3.00 | B | **A** | cost gate was the only failing gate; BE ≥ 3.0x |
| TB-C-2.5% @ z=3.00 | B | **A** | same |
| TB-C-5% @ z=3.00 | B | **A** | same |
| TB-C-7.5% @ z=3.00 | B | **A** | same |

Grade distribution: A 1 → **5**, B 14 → **10**, C 10 (unchanged), D 25 (unchanged).

## Unchanged grades

All 25 D cells (z = 1.50–2.75), all 10 C cells (z = 3.75/4.00), and TB-C-10% @ z=3.00
(already A). No candidate was downgraded; no gate threshold moved.

## Did the scientific conclusions change?

**No.** The P6 conclusions — a stable entry plateau at z ≈ 2.75–3.50, z=3.00 the
coverage/quality compromise, basis reversion dominant, cost robustness rising with
threshold — are unaffected. The repair *strengthens* the existing conclusion: the z=3.00
candidates (the recommended operating region) are STRONG (grade A) across **all five**
neutral models, not merely most. `p7_convergence_optimization_cleared` remains `true`.

**No STOP required** — conclusions did not materially change; proceeding to P7.
