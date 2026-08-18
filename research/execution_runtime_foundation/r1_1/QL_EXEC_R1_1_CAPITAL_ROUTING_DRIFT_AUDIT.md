# QL-EXEC-R1.1 CAPITAL ROUTING DRIFT AUDIT

## Authority refresh
| Ref | SHA |
|---|---|
| Scale / heat science (sealed) | `40d237123ac2b709cc0ebce1d7f057bbfde25dab` |
| Scientific translation handoff seal (R1.1) | `2bbe52ea8798549ed9c03bd90684fd3a0d408a99` |
| capital-routing branch HEAD | `d51b9b4772f0bf2ee9a87deb830614e7494f25d1` |

## Drift
The branch moved past the R1 planning repair (`00bef1b5`) to the R1.1 truth
sync + handoff seal (`2bbe52ea`), then one test-only commit (`d51b9b47`)
that only fixes a cross-branch head check. No science change after the
scientific seal.

## Handoff seal boundary (recorded, read-only)
- A/B family classification, static 70/30 allocation, H1 admission, model
  heat, f semantics, pos_t, 1R: all upstream / sealed Capital Routing.
- Capital Translation Core is pure and MUST NOT recompute H1, model
  admission, gross model heat, or family allocation.
- `EconomicExposureTarget` contains NO broker fields.
- Account registry / BrokerSession / MT5 / secrets / reconciliation / fleet:
  owned by execution-runtime-foundation.

## Richer CapitalDecision
The seal defines `CAPITAL_DECISION_REFERENCE` with richer immutable audit
fields than the current generic `CapitalDecision` (requested_f_pct,
admitted_f_pct, status ACCEPT_FULL/REJECT_HEAT_CAP, model_heat_before,
model_heat_after, configuration_hash).

## Decision for R1.1
NOT a blocker. Do not modify `CapitalTranslationAdapter` in R1.1. Recorded for
future:
`R6_PORTFOLIO_INTEGRATION_CONTRACT_EXTENSION` — extend the generic
`CapitalDecision` to carry the sealed audit fields (generically, without
strategy-specific math) when portfolio integration lands.

## Boundary test
Generic runtime code contains no hardcoded A=0.70 / B=0.30 / 1R=24.494897 /
pos formula / USDJPY / H1-1.00. These remain in Capital Routing adapter
implementations later. Verified by test.
