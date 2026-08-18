# CR-BLOCK4-D1.2 REPORT

**Checkpoint:** CR-RISK-BLOCK-IV-D1.2-INSTRUMENT-SPEC-AND-QUANTITY-REPRESENTABILITY-PLAN
**Base:** `73f760ce09e7109b23732fb7ff2ec8ad455a563e` · **Status:** PASS (preregistration)

## Frozen science (verified)

- events 890 · ACCEPT_FULL 826
  (A 371 / B 455) ·
  REJECT_HEAT_CAP 64
- canonical book hash `b64be26010171801104518db72df63abe01714079a5081fef18c42f990a2580a` · D1.1 grid [39, 178, 417, 655, 786, 817, 825, 826] (PASS)
- D1.1A PASS verified: PASS

## Scenario profile registry (USER_SPECIFIED_SCENARIO — no broker truth)

| profile | equity | leverage | truth class | instrument spec |
|---|---|---|---|---|
| PROP_25K_L50_SCENARIO | 25000.0 | 1:50 | USER_SPECIFIED_SCENARIO | UNKNOWN_UNTIL_FROZEN |
| PROP_25K_L100_SCENARIO | 25000.0 | 1:100 | USER_SPECIFIED_SCENARIO | UNKNOWN_UNTIL_FROZEN |
| PROP_25K_L500_SCENARIO | 25000.0 | 1:500 | USER_SPECIFIED_SCENARIO | UNKNOWN_UNTIL_FROZEN |
| OX_SMALL_L1000_SCENARIO | UNRESOLVED | up to 1:1000 | USER_SPECIFIED_SCENARIO | UNKNOWN_UNTIL_FROZEN |

## Lane B vs Lane C

Lane B quantity representability is planned; Lane C margin/buying-power is
EXCLUDED (deferred to D1.3).  An event can be QUANTITY_REPRESENTABLE and
later MARGIN_BLOCKED.

## Rounding / fidelity (frozen defaults)

Primary ROUND_DOWN_TOWARD_ZERO · upward default False ·
min MIN_QUANTITY_BLOCKED · max MAX_QUANTITY_BLOCKED · clipping
False · comparator NEAREST_STEP · immaterial tolerance
1% / distorted 5%
(preregistered; never chosen from performance).

## Missing truth

18 unresolved fields, all UNKNOWN, all blocking
for empirical D1.2.  Empirical quantity study is BLOCKED until quantity
fields are frozen (D1.2A).

## Decision

`d1_2_plan_pass = True` ·
`d1_2_empirical_authorized = false` · `d1_3_authorized = false` ·
`production_authorized = false` · `human_review_required = true`

Next: CR-RISK-BLOCK-IV-D1.2A-PHYSICAL-PROFILE-TRUTH-INGEST-AND-SEAL (then CR-RISK-BLOCK-IV-D1.2B-QUANTITY-REPRESENTABILITY-SURFACE).
