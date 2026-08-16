# Model C — Disposition Archive (P7.5)

## Verdict

**ARCHIVED_CONDITIONAL_NOT_INCREMENTAL**

Model C (1σ crossing → |x|>2σ confirmation → trailing failure field
management) is **not promoted** and **not promotable** on the current sample.

## Evidence (P7, frozen)

| metric | development | confirmation |
|--------|-------------|--------------|
| N | 111 | 83 |
| continuation lift vs direct 2σ | +4.9pp | +3.1pp |
| incremental LR p-value | 0.0147 (q=0.044) | 0.19 |
| forward displacement vs direct 2σ | WORSE (dev −2.39, CI [−4.44, −0.12]) | — |
| sample gate (N≥200 HIGH) | below | below |

The development LR is nominally significant (p=0.0147, q=0.044 after
BH-FDR), which is why the label is CONDITIONAL rather than REDUNDANT. But:

1. the effect does **not** confirm in 2025 (p=0.19),
2. N=111 is below the preregistered HIGH coverage gate (N≥200),
3. the escalation logic's forward displacement is *worse* than simply
   entering at 2σ directly,
4. direction asymmetry is extreme (102 negative-side vs 9 positive-side
   events), so the marginal dev result rests almost entirely on one side.

## Why it must not disappear silently

P7's conclusion "no model survives" is the headline, but Model C is the
single conditional thread. This archive records it explicitly so a future
agent does not either (a) rediscover it as new, or (b) re-tune it on the same
sample to push it over a gate.

## Disposition

- Status: **ARCHIVED_CONDITIONAL_NOT_INCREMENTAL**
- Allowed future disposition: RESEARCH_ARCHIVE or
  REOPEN_ONLY_WITH_NEW_INDEPENDENT_DATASET
- **Reopen condition:** a new independent dataset (never the same sample),
  with a pre-registered hypothesis that addresses the direction asymmetry
  and the displacement deficit vs direct 2σ.
- Do NOT re-open on the current development/confirmation sample.

## Guardrail

The falsification registry (`MVE_P75_FALSIFICATION_REGISTRY.csv`) carries this
row permanently. Any future promotion of Model C requires: new independent
data + pre-registered hypothesis + full causality gate + human authorization.
