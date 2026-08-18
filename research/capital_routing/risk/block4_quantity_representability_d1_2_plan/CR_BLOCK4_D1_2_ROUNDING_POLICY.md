# CR-BLOCK4-D1.2 ROUNDING POLICY

## Frozen defaults

| item | value |
|---|---|
| primary | **ROUND_DOWN_TOWARD_ZERO** — never exceeds the approved target |
| comparator | NEAREST_STEP (diagnostic only) |
| upward rounding default | **False** |
| below volume_min | **MIN_QUANTITY_BLOCKED** (no auto round-up) |
| above volume_max | **MAX_QUANTITY_BLOCKED** (no clip) |
| multi-ticket split | **False** unless broker truth says the max is per ticket AND a later execution contract explicitly authorizes it |
| clipping | **False** |

## Volume-step rule (within min/max)

    faithful_quantity = floor_toward_zero(raw_quantity / volume_step) * volume_step

Then recompute represented_notional, exposure_ratio, relative_exposure_error.

## Rationale

- Rounding DOWN can only under-represent, never over-represent, the approved
  scientific target.
- Rounding UP creates MORE exposure than science requested — prohibited as a
  default; studied only in ALTERED_BOOK_ROUND_UP diagnostics.
