# Validation Room — Governance

> **Purpose:** The quality gate between "built" and "validated." Nothing leaves without passing.
> **Lead:** AS (Assistant Manager)
> **Rule:** No expansion without PASS from validation gate. Fix before convert.

## What Gets Validated
1. **Quant Strategies** — Cost model validation (real spread + commission + slippage)
2. **Content Quality** — Review before publishing
3. **Tool Integration** — Testing before deployment
4. **API Connectivity** — Verification before production use
5. **Code Quality** — Review before merge

## Validation Process
1. Any room submits work for validation
2. AS reviews against criteria
3. PASS / FAIL decision
4. If FAIL: specific feedback sent back to originating room
5. If PASS: work moves to SW Dev Room for deployment

## Validation Criteria for Quant Strategies
- PF > 1.5 after real costs
- MaxDD < 5%
- WR > 50%
- At least 100 trades in backtest
- No single trade > 20% of total PnL

## Validation Criteria for Content
- Original (not duplicated)
- Platform-appropriate format
- Hashtags assigned
- Caption ready
- Image/generation prompt ready

## Validation Criteria for Tools
- Installs without errors
- API connectivity confirmed
- Documentation reviewed
- Integration path defined

---
*Created: 2026-05-18 per Software CEO recommendation*
