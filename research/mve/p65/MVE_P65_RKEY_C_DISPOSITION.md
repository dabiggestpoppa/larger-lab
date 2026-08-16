# MVE P6.5 — RKEY-C DISPOSITION

**Decision: ARCHIVE_INSUFFICIENT_N**

RKEY-C produced N=20 development events (12 confirmation) at B=1.0 and N=3 at
B=2.0 — far below the pre-registered P6 coverage gate (N >= 200 for HIGH,
N >= 30 for LOW; N < 30 is INSUFFICIENT_N).

No parameter rescue was attempted, and none is permitted here. RKEY-C is a
real-time pivot-family rekey variant (sealed causal status
CAUSAL_REALTIME). Its observational count is structurally low on the frozen
H1 field because its trigger (crossing the most-recent pivot boundary after
a state change) is rare.

Two options were considered:

1. **ARCHIVE_INSUFFICIENT_N** (chosen): RKEY-C is archived with its
   INSUFFICIENT_N label. It receives no predictive credit and is not a P7
   input. Re-opening it requires a separately authorized research question,
   NOT re-tuning inside this checkpoint.
2. DEFERRED_UNTIL_LARGER_DATASET: rejected here because the canonical
   dataset is frozen and no larger dataset is authorized. Deferral would
   merely postpone the same N constraint.

The pivot-family observational robustness check (N=205 dev episodes at
relaxed pivot height 0.1%, continuation 83.9%) is recorded in
MVE_P6_EVIDENCE_STATUS_MATRIX.csv as HYPOTHESIS_ONLY — it was never a
candidate for promotion and changes nothing about this disposition.

RKEY-C remains **not promoted to P7**.
