# BLOC 05 / SENSOR-B5-I11 READINESS ASSESSMENT (READ-ONLY)

Checkpoint assessed: SENSOR-B5-I11 - liquidation normalizer
Frozen authority: bloc_05/04 section 3 (MECHANICAL_LIQUIDATION), bloc_05/03 sections 2,
11-13, 17, 20, 22, bloc_05/06 sections 5-6 and 17-21, bloc_05/07 F14-F17 and F24
Status: READINESS ONLY. No I11 module, test, fixture or evidence exists. I11 is NOT authorized.

## 1. What the frozen contract already fixes

Section 3 opens with the mandate that liquidation semantics are especially easy to corrupt.
Four things must stay separate and must never be collapsed:

    position_side_liquidated
    execution_side
    aggressor_side                (optional)
    maker_taker_liquidation_role  (optional)

position_side_liquidated is LONG / SHORT / UNKNOWN. A long liquidation "generally requires
sell execution", but the frozen text explicitly forbids encoding that as the only
representation: both fields must survive where the provider supports both.

## 2. Canonical fields (04 section 3.3)

    liquidation_event_id         optional
    position_side_liquidated     required
    execution_side               required
    maker_taker_role             optional
    quantity_native              required
    quantity_native_unit         required
    quantity_base                optional
    liquidation_quote_notional   optional
    liquidation_usd              optional
    price_native                 optional
    price_reference              optional
    count                        optional
    aggregation_scope            required

aggregation_scope vocabulary: TRADE_LEVEL, EVENT_LEVEL, INTERVAL_AGGREGATE,
PROVIDER_MULTI_EVENT_AGGREGATE, UNKNOWN.

## 3. Distinctions I11 must preserve

1. Liquidation event vs provider aggregate: an INTERVAL_AGGREGATE row is not an event;
   count and scope must be explicit rather than implied.
2. Forced-order event vs liquidation claim: a provider's long_liq_usd / short_liq_usd is a
   position-side aggregate, not market-wide liquidation truth and not aggressor flow
   (04 section 3.4 makes this distinction mandatory).
3. Position side vs execution side: never derived from one another when the provider does
   not state both.
4. Maker/taker liquidation role (Deribit-style MAKER_LIQUIDATED / TAKER_LIQUIDATED /
   BOTH_LIQUIDATED) is richer than long/short volume and must remain available.
5. Native quantity vs contract units vs USD notional: three separate derived slots, each
   independently blockable.
6. price_native vs price_reference: the second is a PIT observation, not the trade price.

## 4. Dependencies already satisfied upstream

| Need | Provider | Status |
|---|---|---|
| USD-conversion refusal discipline | B5-I08 conversion.py | ACCEPTED |
| PIT terms, multiplier, linear/inverse geometry | B5-I04B terms/conversion | ACCEPTED |
| Methodology + semantic registry | B5-I09a | ACCEPTED (I09b deferred) |
| Side-evidence pattern, provisional mapping | B5-I10 sensors/ | IMPLEMENTATION_PASS_PENDING (see I10R1 hold) |
| Identity, time, revision, coverage, lineage envelope | B5-I01/I02/I04A | ACCEPTED |

I11 must reuse these by import, never by copy or fork.

## 5. Implementable now with deterministic offline fixtures

- position_side_liquidated / execution_side separation, including the consistent
  LONG+SELL and SHORT+BUY cases and the contradictory case (refuse or quarantine).
- aggregation_scope vocabulary enforcement; INTERVAL_AGGREGATE requiring count.
- Zero-interval rule (04 section 3.5): a zero liquidation interval is permitted only when
  the provider reports completed intervals and coverage is verified. No missing interval
  becomes zero.
- Native quantity and unit preservation, with blockable quantity_base.
- liquidation_usd blocked on B5_I08_UNITS_V1 with the citation preserved and no stablecoin
  parity shortcut; liquidation_quote_notional limited to genuine quote-asset values.
- maker_taker_role enum retention for Deribit-style rows.
- UNKNOWN position side never upgraded from price movement or from execution side.

## 6. Requires provider evidence before it can be certified

- Which provider endpoint publishes liquidations and whether it is event or interval scope
  (Binance USD-M forceOrder is event-level; other venues differ).
- Direction/side semantics per provider (position side vs order side naming).
- Whether a provider's liquidation figure is market-wide or venue-wide.
- Interval completeness guarantees for aggregate series.
- Presence of Deribit maker/taker role fields.

Until that evidence exists, I11 can implement Layer 1 behaviour only and must keep
canonical semantic confidence at AMBIGUOUS, exactly as I10 did.

## 7. Proposed frozen-clause-to-test matrix (not written, not authorized)

| Case family | Frozen clause | Shape |
|---|---|---|
| I11-SIDE | 04 3.1 | position/execution separation, contradiction refusal |
| I11-SCOPE | 04 3.3 | aggregation_scope + count coherence |
| I11-AGGREGATE | 04 3.4 | long/short aggregate maps to position side, never aggressor |
| I11-ROLE | 04 3.2 | maker/taker/both role retention |
| I11-ZERO | 04 3.5 | zero interval only with verified coverage |
| I11-USD | 04 3.3 + I08 | liquidation_usd blocked, citation preserved |
| I11-PIT | 03 11-13 | reference price required for inverse/base derivation |
| I11-IDENTITY | 03 17 | event id, sequence, event vs aggregate identity |
| I11-LINEAGE | 05 11-12 | REST/archive distinct, no I17 collapse |
| I11-INTERFACE | 06 17-21 | no I12+ intrusion, gates unchanged |

## 8. Boundary for the next implementation

I11 owns: normalization/sensors/liquidations.py (or the frozen equivalent), its fixtures,
its tests, its evidence artifact name per bloc_05/06 section 17, and one ledger entry.

I11 does not own: USD methodology registration (I09), duplicate collapse (I17), OI / funding
/ book / positioning normalizers (I12-I15), lineage identity issuance (I16), golden replay (I22).

## 9. Non-claims

This assessment implements nothing, tests nothing new and promotes nothing. All eight
program gates remain NOT_YET_EARNED. next_checkpoint_authorized = FALSE.
