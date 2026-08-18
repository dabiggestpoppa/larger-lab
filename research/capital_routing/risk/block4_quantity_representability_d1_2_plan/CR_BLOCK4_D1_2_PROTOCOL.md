# CR-BLOCK4-D1.2 PROTOCOL — Instrument Spec + Quantity Representability Plan

**Checkpoint:** CR-RISK-BLOCK-IV-D1.2-INSTRUMENT-SPEC-AND-QUANTITY-REPRESENTABILITY-PLAN
**Base:** `73f760ce09e7109b23732fb7ff2ec8ad455a563e` (D1.1A)
**Status:** PLAN + PREREGISTRATION (no empirical quantity study, no broker, no orders)

## 1. Question (Lane B)

> Given a frozen account/product contract, can each sealed EconomicTarget be
> represented by broker-native quantity WITHOUT materially altering exposure?

The question is NOT "can we make some order fit" — it is "can the INTENDED
EXPOSURE be represented faithfully?".  EconomicTarget != broker quantity.

## 2. Frozen science (verified)

| fact | value |
|---|---|
| events | 890 |
| ACCEPT_FULL | 826 (A 371 / B 455) |
| REJECT_HEAT_CAP | 64 |
| canonical book hash | `b64be26010171801104518db72df63abe01714079a5081fef18c42f990a2580a` |
| D1.1 grid | [39, 178, 417, 655, 786, 817, 825, 826] (PASS) |
| 1R | 24.49489742783178 bps — NOT a hard stop |

## 3. Non-goals

- no broker quantity execution, no MT5 connection, no live broker queries, no orders
- no production-lot rounding, no clipping, no multi-ticket evasion
- no H1 / pos / f_total / family-weight / strategy-science change
- no margin / buying-power / leverage feasibility (Lane C -> D1.3)
- no performance-based broker/profile selection

## 4. Truth hierarchy

1. ACTUAL_OBSERVED 2. BROKER_DOCUMENTED 3. PROFILE_FROZEN
4. USER_SPECIFIED_SCENARIO 5. HYPOTHETICAL_DIAGNOSTIC 6. UNKNOWN

Lower truth classes never silently upgrade.

## 5. Empirical execution gate

D1.2 empirical quantity study is **BLOCKED** until minimum required quantity
fields are frozen (contract size, volume min/step/max, broker symbol, product
type, account currency, causal conversion source).

## 6. Artifacts

26 preregistration files in this directory; `CR_BLOCK4_D1_2_DECISION.json` is
the checkpoint decision. Nothing here is an empirical feasibility result.
