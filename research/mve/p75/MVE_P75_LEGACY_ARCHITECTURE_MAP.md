# MVE Legacy Architecture Map (P7.5)

## Status

The sequential research architecture

```
coordinates → acceptance → rekey → model signal
```

is **LEGACY_RESEARCH_ARCHITECTURE**. It is deprecated.

Each layer was implemented causally and tested (P4, P6, P7). Each failed to
earn independent predictive credit after controlling for the underlying
coordinate/sigma field. Presenting them as sequential layers of a working
architecture is no longer scientifically justified.

## The false hierarchy

| legacy layer | tested at | verdict | role today |
|--------------|-----------|---------|-----------|
| coordinates | R0.5 (sealed) | CAUSAL_STATE_PRIMITIVE | SURVIVES |
| acceptance | P4 | REDUNDANT (explained by coordinate distance) | PRUNED_PREDICTIVE |
| rekey | P6 | REDUNDANT / INSUFFICIENT_N | PRUNED_PREDICTIVE (RKEY-A/B), ARCHIVED (RKEY-C) |
| model signal | P7 | A/B REDUNDANT; C CONDITIONAL_NOT_INCREMENTAL | REJECTED / ARCHIVED |

## The surviving canonical architecture

```
PRICE
→ STRUCTURAL ANCHOR (causal trailing extremes)
→ CAUSAL VOLATILITY NORMALIZATION
→ MORPHIC COORDINATE
→ SIGMA STATE
→ STATE TRANSITION / SURVIVAL DESCRIPTION
```

Implemented by `src/mve/core_state.py` (deterministic, parity-verified against
the sealed P7 pipeline).

## Roles that remain legal

- **acceptance**: DESCRIPTIVE_ONLY. It may appear as a descriptive label in
  research notes, never as a predictive feature in executable science.
- **rekey A/B**: STATE_MAINTENANCE_ONLY *if* mechanically required for
  coordinate construction. P6.5 verified the executed field (trailing-extreme
  anchors) does **not** consume rekey. So even the maintenance role is unused
  in the current core.
- **rekey C**: ARCHIVED_INSUFFICIENT_N. Not a P7/P8 input.
- **Models A/B/C**: no predictive role. C is archived
  (CONDITIONAL_NOT_INCREMENTAL) with a reopen condition of a new independent
  dataset only.

## What may NOT happen

- acceptance/rekey/models may NOT re-enter as alpha features without a
  separate future research authorization (P8+ gate, human review).
- `generate_all_signals` remains BLOCKED_AGGREGATE (Model E included).
- Model D / Model E remain BLOCKED_LOGIC_SPEC.
