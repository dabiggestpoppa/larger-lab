# CR-BLOCK4-D1 IMPLEMENTATION SEQUENCE

## Preregistered future checkpoint sequence

| id | name | purpose | gate |
|---|---|---|---|
| D1.1 | BROKER-INDEPENDENT-NOTIONAL-FEASIBILITY-SURFACE | sealed target multiples vs preregistered notional grid; no broker/lot/margin | needs only frozen distribution |
| D1.2 | INSTRUMENT-SPEC-AND-QUANTITY-REPRESENTABILITY | economic target -> raw quantity -> representable quantity | actual instrument spec truth frozen |
| D1.3 | MARGIN-CONTRACT-FEASIBILITY | margin/buying-power representability | actual margin semantics; else BLOCKED_PENDING_MARGIN_TRUTH |
| D1.4 | CONCURRENT-ACCOUNT-RESOURCE-REPLAY | causal overlap resource replay | D1.2/D1.3 contracts |
| D1.5 | PHYSICAL-BOOK-DISTORTION-SEAL | ideal vs physical book comparison | no constraint optimization |
| D1.6 | BROKER-QUANTITY-TRANSLATION-CONTRACT | deterministic broker-native quantity handoff | science approval of physical contract |

Then broker-native quantity requirements hand to execution-runtime-foundation.
Revision of this sequence requires explicit architectural justification.

Each later checkpoint requires its own authorization; nothing is automatic.
