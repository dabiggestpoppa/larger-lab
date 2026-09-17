# ALPHA-2R Engine Audit

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

## Funding (REPAIRED: Hyperliquid hourly)

Test funding observations (for toy audit only):
- 16:00 UTC: rate = +0.001 (positive → LONG PAYS → -10 bps)
- 17:00 UTC: rate = -0.0005 (negative → SHORT PAYS → +5 bps)
- 19:00 UTC: rate = +0.0008 (positive → LONG PAYS → -8 bps)

- Funding obs 1: rate=+0.001, LONG pays = -10.0000 bps
- Funding obs 2: rate=-0.0005, SHORT pays = 5.0000 bps
- Funding obs 3: rate=+0.0008, LONG pays = -8.0000 bps
- Total funding: -10.0000 + 5.0000 + -8.0000 = -13.0000 bps

## Net Calculation

- Net return: 50.0000 - 2.5000 - 2.5000 + (-13.0000) = 32.0000 bps
- Gross R: 0.5000
- Net R: 0.3200

## Engine Verification

ENGINE INTEGRITY: PASS — arithmetic matches manual calculation.

## Stress Cost

- Stress cost (2x): 10.0 bps
- Stress net: 27.0000 bps

## Funding Sign Convention

- Source: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding
- Retrieved: 2026-08-24
- Convention: LONG PAYS when funding > 0
- Implementation: funding_pnl = -rate * 10000 (for LONG)
- Frequency: HOURLY (actual Hyperliquid observations)
