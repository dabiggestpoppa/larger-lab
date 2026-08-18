# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Source-Truth Audit

Traces the FULL lineage of the sealed 890-event A/B book from raw market data
to Capital Routing, citing the frozen files that are the source of truth.

## Lineage

    RAW MARKET DATA
      -> capital-routing/data/raw/mt5_pro            (MT5 historical export;
         provider/broker of record, data only -- see ingestion/mt5_adapter.py)
      -> data/USDJPY_M5.parquet                      (canonical USDJPY M5 panel,
         sha256-frozen in Phase 8; prices used by the execution grid)
    ALPHA EVENT (Phase 5 routing events -> Phase 6 outcomes -> Phase 7
      validated families; family classifier in phase_7_families.py)
      -> SEALED EVENT LEDGER
         artifacts/phase_07_5/P7_5_TRADES.csv        (890 events, A 432 /
            B 458; the sealed P0 book, all splits)
      -> FAMILY -> CAPITAL ROUTING
         Block I R1 risk ledger
         artifacts/risk_block1/R1_EVENT_RISK_LEDGER.csv (adds entry/exit
            prices, risk_unit_bps, r_multiple, mfe_r/mae_r, rv, costs)
         Block II/III scale: phase_r6_common.py (H1 admission),
            capital_scale_frontier.py / capital_scale_seal.py (static scale)

## Sealed event fields (P7_5_TRADES.csv, verified)
event_id, event_start, family, dir, pos, entry_ts, exit_ts, pnl_bps,
gross_pnl_bps, cost_pnl_bps, split, hold_h.

| field | value range / semantics |
|---|---|
| event_id | e.g. EUR_ORIGIN_202307101100 (deterministic, unique) |
| family | A (432) / B (458) |
| dir | +1 (A long) / -1 (B short) |
| pos | 0.1104 .. 18.19 -- vol-normalized research sizing unit (pos = TARGET_VOL/rv), NOT the executed notional |
| entry_ts / exit_ts | entry = event_start + family delay (A 2h, B 1h); exit = entry + 6h |
| pnl_bps | NET PnL in bps (direction + vol-normalized position + cost) |
| gross_pnl_bps | same without modeled cost |
| cost_pnl_bps | modeled all-in cost (spread+commission + signed swap) |
| split | inner_sel 461 / inner_val 149 / RELATIONSHIP_CONFIRMED_OOS 280 |

## Instrument truth
- RESEARCH SYMBOL: USDJPY (only instrument in the sealed universe).
- Broker symbol / venue / tick specs / margin: **MISSING_EXECUTION_TRANSLATION_FIELD** -- recorded, not
  fabricated.  Research identity and broker identity are separate fields.

## Missing execution-translation fields (recorded, NOT fabricated)
broker_symbol, venue/exchange, tick_size, tick_value, minimum_quantity,
quantity_step, maximum_quantity, fractional_support, shortability/borrow,
margin_requirement, buying_power_semantics, trading_hours_definition,
order_types_supported, account_currency, account_equity_source.

## Input hashes (frozen sources consumed by this planning audit)
- P7_5_TRADES.csv:        ad19e08f16aeb65c17305041182c591401d28c32b418287f45d76a678ddfcd07
- R1_EVENT_RISK_LEDGER.csv: 6c98b0d218c66f3f5893733f26c51490138e658046487e3ea108c5feeee2d26f
