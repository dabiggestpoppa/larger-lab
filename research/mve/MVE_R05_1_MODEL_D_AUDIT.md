# MVE R0.5.1 — MODEL D LOGIC AUDIT (AUDIT-ONLY)

> Checkpoint: MVE-R0.5.1-SCIENTIFIC-STUB-CAUSAL-REPAIR · 2026-08-15

## Component

`SignalGenerator.generate_multi_timeframe_morphic_alignment_signals`
(Model D: MULTI-TIMEFRAME MORPHIC ALIGNMENT).

## The three candidate regimes (as written)

```python
if (d1_coord > 0 and h1_coord > n_h1 and d1_coord < 0):   # condition 1
    signals.iloc[i] = 1
elif (d1_coord > 0 and h1_coord > 0 and d1_coord > 0):    # condition 2
    signals.iloc[i] = 1
elif (d1_coord > 0 and h1_coord < 0):                     # condition 3
    signals.iloc[i] = 1
```

## Docstring intent

| # | Docstring regime | Code condition |
|---|---|---|
| 1 | candidate pullback-long: M_M > 0, M_W > +1, M_D < 0 | `d1 > 0 and h1 > n_h1 and d1 < 0` → **impossible** (d1 > 0 ∧ d1 < 0) |
| 2 | full alignment: M_M > 0, M_W > 0, M_D > 0 | `d1 > 0 and h1 > 0 and d1 > 0` → equivalent to d1 > 0 ∧ h1 > 0 (redundant d1) |
| 3 | lower-timeframe opposition inside higher-timeframe positive state | `d1 > 0 and h1 < 0` → **opposite sign** of the docstring (docstring: higher-timeframe positive h1 > 0, opposition d1 < 0) |

## Contradiction classification

| Condition | Classification | Rationale |
|---|---|---|
| #1 | SCIENTIFIC_INTENT_AMBIGUOUS | `d1 > 0` is likely a typo, but the correct expression is not derivable: the docstring names three timeframes (M_M, M_W, M_D) while the function receives only two (h1, d1); the M_M ↔ h1/d1 mapping is unspecified |
| #2 | MECHANICAL_TYPO_CLEAR (redundancy only) | `d1 > 0` repeated; semantically equivalent to d1 > 0 ∧ h1 > 0 — no repair needed, no behavior change |
| #3 | SCIENTIFIC_INTENT_AMBIGUOUS | sign inversion vs docstring, but which timeframe is "higher" (h1 or d1) is ambiguous |

## Verdict

**Model D = BLOCKED_LOGIC_SPEC.** The contradictions are NOT repaired (the
correct logical expression cannot be established unambiguously from the
specification). Per the R0.5.1 pass gate, Model D may remain BLOCKED because
it is excluded/fail-closed from future scientific execution.

## Changes actually made (robustness only, not logic)

- NaN guard on the `int()` conversions (`int(NaN)` crash on warm-up
  coordinates) — mechanical robustness repair, no condition changed.
- The three conditions above are byte-for-byte unchanged.

## Behavioral note

Because condition 2 fires whenever d1 > 0 (given h1 > 0 is implied by nothing
— condition 2 needs h1 > 0 AND d1 > 0; condition 3 needs d1 > 0 AND h1 < 0),
the emitted output is 1 for every bar with d1 > 0. This is a consequence of
the ambiguous conditions and is exactly why the component is BLOCKED, not
treated as scientific output.
