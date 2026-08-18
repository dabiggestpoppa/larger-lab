# CR-BLOCK4-D1.2 QUANTITY PIPELINE (PLAN)

    EconomicTarget
      -> account-currency notional (D0.1 target, equity-normalized x equity)
      -> instrument/native exposure (contract semantics)
      -> raw broker quantity
      -> quantity feasibility gate (min / max / step)
      -> faithful rounded quantity (ROUND_DOWN_TOWARD_ZERO)
      -> represented notional
      -> exposure error (exposure ratio, relative / signed error)

## Rules

1. The pipeline is implemented ONLY in D1.2B after physical truth is sealed.
2. No generic FX contract is assumed: contract_size = 100000, volume_min =
   0.01, volume_step = 0.01, volume_max = 100 may appear only inside a labeled
   HYPOTHETICAL_DIAGNOSTIC_PROFILE.
3. Long/short symmetry is CHECKED against the instrument contract, never
   assumed; if asymmetric, side-specific conversion is preserved.
4. Causality: instrument spec known at/before event simulation, account equity
   snapshot known at decision time, causal FX conversion at translation time.
   No end-of-period price conversion.

## Currency conversion (USDJPY / USD account)

Research EconomicTarget notional (account currency) must map to native
instrument quantity using broker contract semantics.  The plan specifies the
required causal conversion price(s): entry-side price for notional->units, and
contract-side semantics for USDJPY (base USD / quote JPY) with a USD account —
conversion is NOT assumed trivial.  CURRENCY_CONVERSION_UNRESOLVED while the
causal conversion source is unknown.
