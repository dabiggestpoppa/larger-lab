# MECH-19 DECISION

**Primary verdict: `PASS_MECH19_RESPONSE_GEOMETRY`**
**Co-earned milestone: `PASS_MECH19_STRUCTURAL_SCAR`**
**Global law freeze: PARTIAL** (deferred; see below)
`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`

## What MECH-19 hardened
1. **Saturation response geometry** — 1–2 response coordinates, slope-dominant (slope 70% of node motion,
   +ceiling ≈96%); held-out curve reconstruction confirms a shared normalized shape; UNIVERSALISH survives.
   This is the flagship result and directly earns PASS_MECH19_RESPONSE_GEOMETRY.
2. **Saturation-without-delivery mechanism** — located as a coordination failure: field reads active while
   forcing<threshold and transfer is impaired; exit concentration is NOT the cause (p1 equal). Strong, new, local.
3. **Parallel-constraint realization** — no loose hierarchy; realization = THRESHOLD ∧ TRANSFER (substitutable),
   capacity inversely associated, 2–3 constraint coordinates. This formalizes potential→realization as geometry.
4. **Forcing atlas round-2** — distinct primitive profiles (burstiness/persistence/rank/sat-node), mostly additive
   interactions, route-specific loads/suppressions per family.
5. **Birth-abort mechanism** — demand arriving into an OPEN (many-exit, high-entropy) route set with low dominant-share
   instability; load-outpaces-commitment at INITIATION. Clean and new.
6. **2022 structural scar confirmed post-repair** — the unclamped fit preserves the slope collapse (0.091 during vs
   1.54 pre; 0.40 post); the ceiling clamp was a minor artifact (+0.07), NOT the driver. Surface recovery preceded law
   recovery; residue is REPEATED re-excursions, not a single continuous scar. This earns PASS_MECH19_STRUCTURAL_SCAR.

## What MECH-19 found NOT stable / weak (do not over-promote)
- **ROUTE_COMMITMENT has no durable band** — dominant-route allocation is always revisable within 60 days; treat as
  LOCAL/weak, not a sticky state.
- **CONCENTRATION_PHASES** — continuous but flat; exits near-inevitable → no separate phase structure.
- **THRESHOLD_INVERSION_SPECIES** — chronic deep-patch early-activation inversions, but too few/too chronic to separate species.
- **Deep-rank hysteresis is state-local and decays with depth** (strongest 6C_1/6C_2; raw gap 0.17→0.11 into depth);
  not global.

## Global law freeze status
**PARTIAL, deferred.** The adaptive-law machinery is mapped and internally consistent, but the GLOBAL law is not a
single frozen object. The OS must carry, alongside the frozen topology:
- a state-local hysteresis coordinate,
- a parallel-constraint realization core (THRESHOLD ∧ TRANSFER),
- a response-slope REGIME condition (post-2022 slope stays ~0.40 vs pre-2021 1.54, with recurrent re-excursions),
- separate SURFACE_END / LAW_END recovery clocks.

## Recommended Field Model v1 wording
- Topology: FREEZE (unchanged).
- Law layer: adaptive, parallel-constraint, state-local hysteresis, slope-regime condition.
- 2022: carried as a re-entrant STRUCTURAL_SCAR on the response slope (RESEARCH_ONLY), not a named permanent regime.
- Do NOT use route-commitment, a single forcing scalar, a global memory kernel, or a universal state-age clock as objects.

## Proposed verdict line (single)
> **PASS_MECH19_RESPONSE_GEOMETRY** — response law compressed to ~2 slope-dominant coordinates with a confirmed
> universalish shape; saturation-without-delivery and birth-abort mechanisms located; potential→realization is a
> parallel constraint system; 2022 structural scar confirmed under the unclamped repair. Global adaptive-law freeze
> deferred to PASS-partial pending the slope-regime treatment by the human review.

## Governance
Stopped after MECH-19. No commit, no push, no PR. No files outside `mech_19/` were created or modified.
Awaiting human review.