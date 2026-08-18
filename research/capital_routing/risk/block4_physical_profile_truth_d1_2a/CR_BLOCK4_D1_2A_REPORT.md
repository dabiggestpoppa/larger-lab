# CR-BLOCK4-D1.2A REPORT

**Checkpoint:** CR-RISK-BLOCK-IV-D1.2A-PHYSICAL-PROFILE-TRUTH-INGEST-AND-SEAL
**Base:** `aaf3e0548ec9bff85b38b7f8a853a7becffce4c3` · **Status:** PARTIAL_PASS_WAITING_PHYSICAL_TRUTH

## Truth ingestion summary

- truth sources found: True (inventory of
  10 sources)
- actual observed sources found: False
- broker documented sources found: False
- user scenario sources found: True (4)

## Instrument / account truth

All executable quantity fields are UNKNOWN (no actual/documented evidence):
broker_symbol, product_type, contract_size, volume min/step/max, account
currency, base/quote/margin currency, trade_calc_mode, hedging/netting,
quantity conversion rule.  research_symbol = USDJPY is PROFILE_FROZEN from the
sealed science.

## Profile registry

- profiles total: 5 (4 scenario + 1 actual placeholder)
- profiles quantity complete: 0
- profiles margin complete: 0
- every scenario profile: PARTIAL_PROFILE (equity + leverage only)

## Nonregression

- science counts: {'n_events': 890, 'n_accepted': 826, 'n_rejected': 64, 'accepted_A': 371, 'accepted_B': 455} — unchanged
- canonical book hash: `b64be26010171801104518db72df63abe01714079a5081fef18c42f990a2580a`
- fidelity tolerance 1% unchanged · rounding policy ROUND_DOWN_TOWARD_ZERO unchanged
- quantity surface executed: False
- margin study executed: False
- broker client / MT5 import / broker contact / order attempt: all FALSE
- secrets committed: False

## Decision

`d1_2a_pass = True` · `d1_2b_ready = False`
· `d1_2b_authorized = false` · `d1_3_authorized = false` ·
`production_authorized = false` · `human_review_required = true`

Next: CR-RISK-BLOCK-IV-D1.2A1-PHYSICAL-TRUTH-COLLECTION
