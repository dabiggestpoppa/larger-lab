# LOWER-FIELD-6 — PRD DEFINITION HARMONIZATION

Agent-1 (MECH-8/10) and Agent-2 (LF5) report different PRICE_UP/RANK_DOWN
(PRD) population sizes. This document reconciles them explicitly before any
further health-state synthesis. No merged claims are made before resolution.

## 1. Universe comparison

| Axis | LEGACY_AGENT1 (MECH-8/10) | LEGACY_AGENT2 (LF5) |
|------|---------------------------|---------------------|
| Event universe | MECH-8 health events: ISOLATED_DOWNSIDE_EXTREME z>=2, ns==1, bands 1-2000 | ISOLATED downside z1>=2, bands 26-2000 (peer EVENT_BANDS) |
| n_total | 1023 | 2462 |
| Isolation filter | ns==1 (same band/date/sign) | participation==ISOLATED (same cluster_n==1 rule) |
| Shock threshold | z>=2 | z1>=2 (same) |
| Price anchor | fwd{h}/sigma_t0 >= 0.5 (0.5σ) at horizon | recover1s{h}: fwd/sigma >= sqrt(h) (1σ·√h) |
| Rank velocity rule | fwd rank vel > 0 (RANK_RECOVERY) | fwd_rank_vel_{h}d > 0 (canonical: <= 0 = RANK_DOWN, LF5 convention) |
| Horizon | cross_state at t0 (7D price rule) | per-horizon 3/7/14/30D |

## 2. Exact counts

| Group | n | p |
|-------|---|---|
| AGENT-1 PRD (PRICE_RECOVERY_RANK_DECAY, 7D) | 282 | 0.276 |
| AGENT-1 PRR (PRICE_RECOVERY_RANK_RECOVERY) | 339 | 0.331 |
| AGENT-1 PDD (PRICE_DECAY_RANK_DECAY) | 293 | 0.286 |
| AGENT-1 PDR (PRICE_DECAY_RANK_RECOVERY) | 109 | 0.107 |
| AGENT-2 PRD (recover1s7 & rv<0, 7D) | 48 | 0.019 |
| HARMONIZED_CANONICAL (Agent-2 universe, 1σ rule, 7D) | 59 | 0.024 |
| HARMONIZED 0.5σ variant (Agent-1 threshold on A2 universe) | 213 | 0.087 |

## 3. Why the sizes differ

1. **Universe**: Agent-1 counts on the MECH-8 health event set (n=1023,
   all bands incl. top 1-25 and mid-band truncation from LF2 cache); Agent-2
   counts on the LF5 PIT-substrate isolated events restricted to bands
   26-2000 (n=2462). The LF2 cache band truncation excludes deep
   lower-field ranks that the PIT substrate now includes.
2. **Price rule**: Agent-1 uses a 0.5σ threshold; Agent-2 uses 1σ·√h. On the
   same universe the 0.5σ variant captures 213 vs 59
   events — the 1σ rule is stricter by construction.
3. **Horizon**: Agent-1's cross_state is a t0 (7D-lag) classification;
   Agent-2 reports per-horizon states.

## 4. Canonical definition adopted for LF6

- Universe: LF5 PIT-substrate ISOLATED downside z1>=2, bands 26-2000
- Price up: recover1s7 (signed_fwd7 >= sigma_t0·√7)
- Rank down: fwd_rank_vel_7d <= 0 (LF5 convention; strict < 0 gives 48)
- Canonical PRD n = 59 at 7D (0.5σ variant: 213)

Legacy Agent-1 claims are preserved as LEGACY_AGENT1 and NOT merged into the
canonical until a shared universe re-run exists.

## 5. Resolution

DEFINITION_DRIVEN_DIFFERENCE, RESOLVED_BY_DOCUMENTATION + canonical
universe. Further price×rank matrix work in LF6 uses the canonical
definition above.
