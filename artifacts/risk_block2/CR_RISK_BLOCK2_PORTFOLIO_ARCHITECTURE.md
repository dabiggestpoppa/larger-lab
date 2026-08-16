# CR-RISK-BLOCK-II — Portfolio Architecture (frozen)

**Task:** CR-RISK-BLOCK-II-INTERMEDIATE-SEAL

## Default architecture
The evidence supports the SIMPLE static structure, not a cascade of
dynamic sizing rules:

```
ALPHA
 -> FAMILY QUALITY (A / B; R5)
 -> STATIC FAMILY ALLOCATION (50/50 | 70/30 | 100/0 A references; R5)
 -> SIMPLE SIMULTANEOUS-HEAT LIMIT (H1 gross cap; R6)
 -> PORTFOLIO
```

NOT:

```
ALPHA -> dozens of dynamic sizing rules
```

## Why this holds
- R5: 50/50 allocation cuts solo max DD roughly in half (10.3%/11.1% ->
  5.2%) at comparable total f=1% with no allocation selected as best.
- R6: portfolio DD is NOT mainly an overlap problem (84.7% of in-drawdown
  hourly loss is single-position); the 3-position state is rare (20h of
  4,735 in-market hours) and a single static 1.0x gross cap removes its
  resampled tail contribution at A-heavy allocations.
- R6: more complex controls (H2 same-direction, H4 episode budget) do not
  add incremental value over the simple gross cap; H5 is optional-only.
- Edge degradation dominates risk outcome: at 50% retained edge every
  policy is fragile regardless of heat control. No exposure rule creates
  expectancy.

## Supported design region (NOT a production pick)
- Allocation references: 50/50, 70/30, 100/0 A (0/100 B diagnostic).
- Heat: H0 diagnostic; simple H1 gross cap (1.0x-3.0x research multiples);
  H2/H3 secondary references.
- Base total-f research band: 0.25%-2.00% (frozen R6 F_GRID; 3.00% outer
  stress only).

## Locked flags
best_allocation_selected = false · best_heat_policy_selected = false ·
best_size_selected = false · dd_adaptive/kelly/hybrid/deployment/mt5 = false.
