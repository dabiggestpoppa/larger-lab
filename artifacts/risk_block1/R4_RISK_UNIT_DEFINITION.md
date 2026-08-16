# R4.1 — Risk-Unit Definition

**1R = TARGET_VOL x sqrt(HOLD) = 24.4949 bps** is the sealed strategy's
normalized expected-move unit — it is **NOT a hard stop-loss R**.

## The critical mapping

    trade_return_R x risk_fraction  ->  account equity PnL

Historical trades lose far more than -1R:

- Family A worst: **-3.66R**
- Family B worst: **-3.31R**

Therefore "risk 1%" does **NOT** mean "maximum 1% loss". A -3R trade at
f = 1% costs approximately **-3%** of the account:

    equity_after = equity_before x (1 + f x r_R)
    f = 0.01, r_R = -3.0  ->  equity_after = 0.97 x equity_before

## Compounding conventions (both multiplicative, no additive approximation)

1. **Hourly (overlap-exact)** — used for the pooled A+B historical book: the
   ledger's per-trade hourly net-PnL increments (cost charged at entry) are
   summed across all concurrently open positions each hour, then
   `E_{h+1} = E_h x (1 + f x r_h)`. Real overlap (max 3 concurrent) is
   preserved exactly. Sum of hourly increments == sum of sealed net PnLs
   (asserted in code).
2. **Sequential (per-trade reference)** — `E_{t+1} = E_t x (1 + f x r_R_t)`
   over the chronological trade sequence (the brief's formula), used for
   A-only / B-only and as a comparison column.

## What this means for the frontier

- During 2-position overlap the account is exposed to up to **2 x f** per hour;
  during 3-position overlap up to **3 x f** (gross; opposing positions are NOT
  treated as riskless — see R4_ACCOUNT_HEAT_MAP.csv).
- Max historical concurrent positions: **3** (gross R exposure 3R at entry).
- Worst historical portfolio adverse excursion: see R4_ACCOUNT_HEAT_MAP.csv
  (portfolio CAE in R and its account impact at each f).
