# ASE Generation-A AR_MAX Boundary Audit

Status: `CONTRACT_REPRODUCTION_REPAIR`

## Source audit

| Source | Executable wording | Interpretation |
|---|---|---|
| `quant-lab/reports/PART_1___Core_Manual.txt` | `> 45 pips` is NO-GO | strict greater-than |
| `quant-lab/reports/CEREBUS_v4_Manual_EXTRACTED.txt` | repeated `>45 pips` / `>45p NO-GO` | strict greater-than |
| `quant-lab/reports/P90_STRATEGY_GUIDE.md` | `Range > 45 pips` is NO-GO | strict greater-than |
| `quant-lab/strategies/CEREBUS_V5_LIVE_PERFECT_FORM.pine` | `ar_nogo_threshold = 55`; `ar_status` is NO-GO at `>= 55`; `get_tier` uses `>=30 and <45` for T3 and otherwise N/A | later P90 variant; not Generation-A tier contract |
| Generation-A regression fixture | `AR = 45p = NO-GO` | conflicting fixture, not executable source |

## Frozen conclusion

For this ASE-1.1 repair, the executable Generation-A source wins: **`AR > 45 pips` is NO-GO**. Therefore `AR == 45.0` remains eligible for the T3 calibration interval (`30 <= AR <= 45`), while `AR > 45` is retained in the master census with `AR_NO_GO_STATE=true` and excluded from calibration.

The supplied equality fixture is retained as an explicit unresolved historical discrepancy and is not silently relabeled as source parity. If a future authoritative Generation-A executable fixture proves `>=45`, that is a new contract clarification, not a parameter optimization.

## Operational boundary

- T1: `AR < 20`
- T2: `20 <= AR < 30`
- T3: `30 <= AR <= 45`
- NO-GO: `AR > 45`

No PnL or confirmation data was used.
