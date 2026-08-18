# PFT-B2 — Data Truth Seal — REPORT

- checkpoint: `PFT-B2-DATA-TRUTH-SEAL`
- branch: `agent/deepers-strategy-foundry`
- generated: 2026-08-18T18:23:14.663556+00:00

## Evidence

- all_signal_families_present: True
- direct_eurcad_present: True
- panel_built: True
- panel_has_development_partition: True
- ohlc_violation_quarantine: True
- fx_parity_run: True
- hash_manifest_complete: True
- split_frozen: True

### Coverage

| asset   |   total_canonical_slots |   valid_observed |   stale_carried |   expected_closed |   unexpected_missing |   bad |   stale_gt_2h |   usable_K1_K3 |
|:--------|------------------------:|-----------------:|----------------:|------------------:|---------------------:|------:|--------------:|---------------:|
| W       |                   29829 |            18767 |           11062 |              8496 |                 2566 |     0 |          9303 |          20170 |
| E       |                   29829 |            21204 |            8625 |              8496 |                  129 |     0 |          8258 |          20170 |
| C       |                   29829 |            21208 |            8621 |              7611 |                 1010 |     0 |          8254 |          20170 |
| I       |                   29829 |            19885 |            9944 |              9384 |                  640 |     0 |          8964 |          20170 |

### Cross-series identity

{
  "LCO_vs_OILUSD": {
    "common_bars": 18775,
    "return_corr": 0.90863,
    "exact_price_match_fraction": 0.0
  },
  "EURUSD_vendor_vs_PRO": {
    "common_bars": 223982,
    "return_corr": 0.999794,
    "exact_price_match_fraction": 0.98582
  },
  "USDCAD_fetched_vs_PRO": {
    "common_bars": 278480,
    "return_corr": 0.925101,
    "exact_price_match_fraction": 1.8e-05
  },
  "EURCAD_fetched_vs_PRO": {
    "common_bars": 278370,
    "return_corr": 0.922625,
    "exact_price_match_fraction": 0.120236
  }
}

### Triangular FX parity

{
  "n": 263234,
  "interval": "5min",
  "mean": 4.921232373232968e-07,
  "std": 0.0004540271581666118,
  "quantiles": {
    "0.0": -0.017076867223755475,
    "0.01": -0.0011055687932566762,
    "0.05": -0.0005951735202497016,
    "0.25": -0.00018754247708482538,
    "0.5": -6.558017748153899e-07,
    "0.75": 0.00018523916152751035,
    "0.95": 0.0006019327213818637,
    "0.99": 0.0011141252257927268,
    "1.0": 0.016517737341033057
  },
  "abs_residual_gt_1e_4": 185317,
  "abs_residual_gt_1e_3": 7147
}

## Derived status: **PASS**

## Gate

`human_review_required = true`
`next_checkpoint_authorized = false`
