# FORMALISM READINESS — MECH-4

## Currently EARNED (from MECH-3 + this checkpoint)

- **Descriptive dynamical systems / metastable-state language**: concentration and
  mixed form a 2-state basin; concentration is a persistent/reflexive pivot state.
  MECH-4 adds a **duration-structured escape hazard**: P(escape within 7D) falls
  monotonically with concentration-episode age (0.83 at age 1 → 0.29 at age 15-30).
- **Semi-Markov / duration-conditioned process** EARNED (narrow form): escape
  likelihood depends on episode age (rho = −0.78 on the age-binned escape rate),
  though destination does NOT depend on age (χ² p = 0.71). The clock that matters
  for *when* you leave is age; the clock does not change *where* you go.
- **Bifurcation-style boundary language** (strong form, EARNED-with-caveat): the
  G3 predicted-probability projection shows a sharp outcome-rate discontinuity —
  0.16 in bin 4 → 0.76 in bin 5 (jump 0.60) — i.e. a small change in the joint
  coordinate region maps to a large change in propagation probability (WS 39).
  Caveat: this is on the logit's own projection; a full multi-dimensional boundary
  scan is not performed, so strong form is declared EARNED but flagged PARTIAL
  until the boundary surface is mapped.
- **Empirical hysteresis**: entry-route↔exit-route association (descriptive,
  MECH-3). MECH-4 shows this is **descriptive**: path memory does NOT add held-out
  predictive information for the *route* after current state (HYSTERESIS_DESCRIPTIVE).

## NOT EARNED (do not formalize yet)

- **Category-theory composition** across scales: MECH-3 already marked
  CATEGORY_STYLE_FORMALIZATION = NO; MECH-4's second-order routing is mostly
  concentration↔mixed oscillation, not a composed reservoir→infra→leader→breadth→…
  pathway with stable morphisms.
- **Full HMM / latent-state machinery**: the duration-conditioned observable-state
  model is sufficient; no stable-structured residuals requiring a hidden layer were
  demonstrated (WS D runs on explicit states).
- **Deterministic causal state-machine**: route selection remains poorly
  reconstructable (WS C / WS 20 route gap); a deterministic transition law is not
  justified.

## Inference / decision update from MECH-4

| Structure | Readiness |
|---|---|
| Descriptive dynamical systems | EARNED (carry forward) |
| Duration-dependent (semi-Markov) escape hazard | **NEW: EARNED** |
| Bifurcation-style boundary | **NEW: EARNED (with multi-dim caveat)** |
| Empirical hysteresis (descriptive) | EARNED, descriptive only |
| Category-style / HMM / causal law | NOT EARNED |

## The phenomenon chooses the mathematics

MECH-4's additions are all natural consequences of the observed pivot-release
structure: age-structured escape, a sharp route-selection boundary, and hysteresis
that is descriptive (not predictive). These are the minimal formalisms the data
already support; heavier machinery is deferred until simple models demonstrably
leave material structure unexplained.