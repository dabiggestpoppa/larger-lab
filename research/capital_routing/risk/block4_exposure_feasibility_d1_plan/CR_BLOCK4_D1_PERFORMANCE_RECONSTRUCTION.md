# CR-BLOCK4-D1 PERFORMANCE RECONSTRUCTION

## Rule (predefined)

- faithfully executed event: physical return derives from ACTUAL represented exposure
- blocked event: physical realized strategy return = 0 (research event still
  exists in the ideal book)
- partial / rounded diagnostic event: return scales with actual/target exposure
  ratio ONLY IF the source model is linear in exposure

## Linearity proof (already established)

Sealed gross account return = (N_t / E_t) x price_return_bps / 1e4 and
N_t/E_t = admitted_f x pos_t x 1e4 / RISK_UNIT_BPS, so account return is exactly
linear in N_t: scaling N by ratio r scales gross account return by r. Research-
modeled cost also scales with pos_t per event (R1 cost audit). Execution-level
net parity remains BROKER_DEPENDENT_UNRESOLVED.

## Two books, never merged

- SEALED IDEAL BOOK (frozen research data — never overwritten)
- PHYSICAL-CONSTRAINT BOOK (per scenario)

## Secondary performance metrics (never used to select constraints)

event count, frequency, WR, EV, PF, payoff, normalized return, DD, streaks,
family contribution, concentration, episode behavior.
