# ALPHA-2 Engine Integrity Test

## Toy Trade Parameters

- Asset: BTC
- Strategy: ALPHA1_S001 (FAM_A, perp long)
- Entry: 2026-02-01T12:00:00+00:00
- Entry price: $100,000.00 (next bar open)
- Exit: 2026-02-01T20:00:00+00:00 (8h time exit)
- Exit price: $100,500.00
- Direction: LONG

## Manual Calculation

- Gross return: (100500.0 - 100000.0) / 100000.0 × 10000 = 50.0000 bps
- Transaction cost: 5.0 bps roundtrip (2.5 entry + 2.5 exit)
- Funding (1 settlement): rate=0.001, LONG receives = +10.0000 bps
- Net return: 50.0000 - 2.5000 - 2.5000 + 10.0000 = 55.0000 bps
- Gross R: 0.5000
- Net R: 0.5500

## Engine Verification

ENGINE INTEGRITY: PASS — arithmetic matches manual calculation.

## Stress Cost Calculation

- Stress cost (2x): 10.0 bps
- Stress net bps: 50.0000 - 10.0000 + 10.0000 = 50.0000
- Stress net R: 0.5000
- PF decay: 0.0% (if gross_R > 0)

## Cost Model Verification

- Perp roundtrip: 5.0 bps ✓
- Spot roundtrip: 7.5 bps ✓
- Hedge roundtrip: 12.5 bps ✓
- Stress multiplier: 2.0x ✓
- Perp stress: 10.0 bps ✓
- Spot stress: 15.0 bps ✓
- Hedge stress: 25.0 bps ✓

## Funding Accounting Verification

- Settlements: [0, 8, 16] UTC ✓
- Entry on settlement: NOT accrued ✓
- Exit on settlement: IS accrued ✓
- Long receives when funding > 0 ✓
