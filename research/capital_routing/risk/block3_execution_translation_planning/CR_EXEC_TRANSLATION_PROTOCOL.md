# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Protocol

**Repo:** dabiggestpoppa/larger-lab
**Branch:** capital-routing
**Authoritative base:** 40d237123ac2b709cc0ebce1d7f057bbfde25dab (CR-RISK-BLOCK-III-SCALE-SEAL-R1-FAIL-CLOSED-GATE)
**Type:** PLANNING / CONTRACT DESIGN -- no orders, no broker, no live capability.

## Mission
Design, unambiguously, the canonical chain that converts a sealed Capital
Routing A/B event into a broker-executable quantity WITHOUT changing the
sealed science:

    ALPHA EVENT -> identity -> family A/B -> family weight -> f_total ->
    requested_f -> H1 causal admission -> admitted_f -> account equity
    reference -> normalized 1R dollar budget -> instrument-native move unit
    -> target economic notional -> raw quantity -> broker quantity rounding
    -> actual notional -> actual realized R sensitivity -> post-rounding
    admitted_f equivalent -> margin / buying-power check -> execution-health
    check -> ORDER INTENT -> future execution layer.

Every arrow must carry input / units / formula / known-time / failure state /
rounding semantics / audit field.  This protocol freezes the rules BEFORE the
contracts are written.

## Frozen science (NOT negotiable here)
- Sealed A/B book: 890 events (A 432 / B 458),
  hold_h always [6], dir in [-1.0, 1.0].
- 1R = TARGET_VOL x sqrt(hold) = 24.4949 bps (TARGET_VOL = 10.0 bps/h,
  hold = 6.0h). 1R is an EXPECTED-MOVE unit, NOT a hard stop.
- Families: A = EUR accumulation -> JPY weakness -> LONG USDJPY (delay 2h,
  hold 6h); B = EUR liquidation -> JPY strength -> SHORT USDJPY (delay 1h,
  hold 6h).
- Block III sealed architecture: static family allocation A1_70_30
  (A event = 0.70 equity per 1R, B event = 0.30),
  f_total = 1.00%, H1-1.00-REJ gross heat cap (1.00 f-unit,
  REJECT treatment, causal admission, exit <= new-entry expires).
- No best cell; no Kelly; no DD adaptation; no production sizing; no
  deployment; no MT5.

## Pass gate (14 questions -- all must be answerable)
1. What exactly does 1R mean?                   2. How is pnl_bps constructed?
3. What dollar sensitivity does admitted_f represent?
4. How does that sensitivity become notional?   5. How does notional become
   broker quantity?                             6. How does rounding affect
   realized f?                                  7. Margin vs buying power vs
   risk heat kept separate?                     8. H1 preserved after
   translation?                                 9. Atomic reservation of
   simultaneous events?                         10. Partial fills?
11. Restart reconstruction?                     12. Foreign positions?
13. 890-event research admission reproduced exactly?
14. Which existing broker/execution path is safe to reuse?

If any remains unknown: status = BLOCKED_PLANNING with the exact fact.

## No-go (this checkpoint)
Order placement, production capital, MT5 / broker authorization, account
selection, alpha/family/allocation/heat/f_total/1R changes, entry/exit
changes, Kelly, DD-adaptive sizing, new risk optimization, final execution
engine.  Default authority: DENY.

## Expected decision truth
planning_pass (per gate), implementation_authorized = FALSE, broker / MT5 /
deployment authorization = FALSE, human_review_required = TRUE.
Next recommended checkpoint: CR-RISK-BLOCK-IV-EXECUTION-TRANSLATION-ENGINE-D0.
