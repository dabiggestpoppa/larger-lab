# QL-EXEC-R2 MT5 FILL POLICY AUDIT

## Generic FillPolicy
FILL_OR_KILL / IMMEDIATE_OR_CANCEL / RETURN_OR_PARTIAL / BROKER_DEFAULT /
UNKNOWN. No MT5 enum integers in the generic contract.

## Adapter mapping (TB-observed broker quirk)
| Generic | `type_filling` code (this broker) |
|---|---|
| FILL_OR_KILL | 1 |
| IMMEDIATE_OR_CANCEL | 2 |
| RETURN_OR_PARTIAL | 0 |

Standard MT5 enum constants are FOK=0/IOC=1/RETURN=2; the validated TB path
observed a PERMUTED acceptance (FOK=1/IOC=2/RETURN=0) via order_check probing.
This is a BROKER-SPECIFIC observation, kept injectable (`fill_policy_codes`),
never a universal default.

## DECLARED vs ACTUAL
`symbol_info.filling_mode` bits are DECLARED capability. TB showed the broker
declared IOC bits but only accepted FOK for market deals. R2 represents both:
- `SymbolInfo.declared_fill_policies` (declared bitfield)
- `probe_fill_policies()` (actual, via order_check: FOK -> IOC -> RETURN)

## Selection policy
- Explicit `fill_policy` on OrderIntent maps directly (unsupported => fail).
- `BROKER_DEFAULT`/`UNKNOWN` resolves via probe, then first declared policy,
  then RETURN fallback.

## Discovery bit mapping (TB-observed)
1 -> FOK, 2 -> IOC, 4 -> RETURN.
