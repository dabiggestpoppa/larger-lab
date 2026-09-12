# CRYPTO FIELD DEFINITIONS

**Branch:** `agent/crypto-quant-foundry`  
**Status:** Canonical conceptual vocabulary for terrain research  
**Purpose:** Translate qualitative market ideas into testable structure without overclaiming.

## 1. Observable

A measurable quantity directly represented in the available data at time t.

Examples: close price, rank, market cap, exchange volume, TVL, stablecoin supply, bridge flow, DEX volume, funding, OI, labeled-wallet balance.

An observable is not automatically an independent source of information.

## 2. Observation Layer

The complete set of available sensors and data surfaces through which the market is seen.

The observation layer is a projection of the real system, not the system itself.

## 3. Hidden / Unobserved Variable

A market-relevant quantity not directly available in the observation layer.

Examples may include private OTC inventory, undisclosed intent, incomplete wallet identity, private market-maker positioning, future policy decisions, or missing historical ecosystem state.

A hidden variable is a candidate explanation for residual structure, not a license to explain away failed hypotheses.

## 4. Latent State

An inferred underlying state that helps explain multiple observables more parsimoniously than treating them independently.

Example candidate: `ECOSYSTEM_LIQUIDITY_EXPANSION` inferred from stablecoin inflow, bridge inflow, TVL growth, DEX activity and breadth.

Latent state labels remain hypotheses until validated.

## 5. Redundancy

The degree to which two or more observables encode substantially overlapping information about the same underlying phenomenon.

Redundancy may be global or state-dependent.

## 6. Equivalence Class

A group of observables or transformations that are sufficiently substitutable for a defined research purpose.

Example: several broad-beta proxies may form an informational equivalence class if substituting one for another leaves the reconstructed field state materially unchanged.

Equivalence is always relative to a specified question and tolerance.

## 7. Primitive

A minimally reducible factor, constraint or state coordinate whose removal materially alters recurring field structure and which cannot be replaced by an equivalent observable without meaningful loss.

A primitive is empirical, not philosophical. It must earn primitive status through perturbation and compression tests.

## 8. Projection

A mapping from the full or latent system into a lower-dimensional observable view.

Examples:

- total-market return is a projection of the broader market state
- sector breadth is a projection of internal sector participation
- rank is a projection of relative market-cap position

## 9. Coordinate

A measurable or inferred dimension useful for locating a state within the field.

Coordinates can be redundant, local, global, continuous or categorical.

## 10. Vector / State Vector

An ordered collection of coordinates representing the market or subsystem at time t.

Example:

`X_t = [global_beta, breadth, rank_dispersion, stablecoin_flow, chain_flow, concentration]`

The usefulness of a state vector depends on whether its coordinates are non-redundant enough to preserve the structure of interest.

## 11. Subspace

A restricted region of the full state space in which certain variables or relationships dominate.

Example: a Solana ecosystem subspace may be more strongly governed by chain-specific liquidity and local breadth than by global BTC beta during some periods.

## 12. Locality

The property that a mechanism or relationship applies only to a specific region, scale, state, chain, sector, rank band or time regime.

A relationship can be valid locally without being universal.

## 13. Perturbation

A controlled alteration of the research representation used to test structural dependence.

Examples:

- remove BTC beta
- remove one cycle
- exclude one sector
- substitute a proxy
- suppress a flow variable
- truncate future data

Perturbation asks what changes when a coordinate or condition is changed or removed.

## 14. Ablation

A specific perturbation in which a component is removed entirely.

Ablation is useful for identifying necessary or redundant components.

## 15. Invariant

A property, relation, ordering or structural form that remains materially stable under a defined family of perturbations, transformations, scales or historical contexts.

“Invariant” must always specify what transformations it survives.

## 16. Boundary

A state-space region across which the qualitative behavior, admissible transitions or governing relationships change.

Examples may include a volatility threshold, rank-band transition boundary, liquidity saturation point or connectivity break.

A boundary may be sharp or probabilistic.

## 17. Neighborhood

A local region around a state, node or point in the field within which structure is sufficiently similar for a defined analysis.

Neighborhoods can be based on geometry, graph distance, economic similarity, rank proximity, sector membership or state-space distance.

## 18. Distance

A rule for quantifying separation between two states, assets, clusters or observations.

Distance need not be Euclidean.

Possible distances may be based on:

- returns
- rank trajectories
- sector/chain membership
- flow profiles
- graph connectivity
- state-transition behavior
- information divergence

The distance definition must match the market question.

## 19. Geometry

The structure induced by coordinates, distances, constraints and transformations in the market state space.

Geometry describes how states are arranged and related, not merely price-chart shapes.

## 20. Recursive Geometry

A materially similar structural pattern observed across multiple scales or nested subsystems.

Example candidate:

leader -> peer expansion -> breadth -> speculative perimeter

appearing within a sector, within a chain ecosystem and across the wider market.

Self-similarity must be tested, not assumed.

## 21. Graph

A representation consisting of nodes and edges.

Nodes may be assets, chains, sectors, wallets, venues or latent states.

Edges may encode capital flow, dependency, co-movement, lead-lag, ownership, liquidity routing, bridge relationships or transformation pathways.

## 22. Topology

The study of structural connectivity and organization that remains meaningful under continuous deformation or changing exact magnitudes.

In market terms, topology is useful when the important question is whether clusters remain connected, isolated, bridged, fragmented or structurally persistent rather than their exact numerical coordinates.

## 23. Connected Component

A subset of the graph in which nodes are mutually reachable through relevant edges.

May correspond to an ecosystem, liquidity island or strongly coupled market cluster.

## 24. Bridge / Articulation Node

A node whose presence materially connects otherwise weakly connected regions of the graph.

Examples may include a major bridge, stablecoin, exchange, L1 or protocol acting as a capital-routing bottleneck.

## 25. Liquidity Island

A cluster with strong internal economic/behavioral connectivity but relatively weak dependence on the broader global field over a defined interval.

This is an empirical classification, not a permanent project label.

## 26. State

A sufficiently coherent configuration of observables and latent coordinates that implies a distinct local set of likely behaviors or transitions.

State labels should be data-derived where possible.

## 27. Transition

A movement from one state to another.

Transitions can be abrupt, gradual, reversible, irreversible, path-dependent or state-conditioned.

## 28. Transition Kernel

A rule or empirical probability structure describing which next states are reachable from a current state and with what frequency/conditions.

## 29. Attractor

A state or region toward which trajectories repeatedly converge under a defined regime.

In market research, an attractor is descriptive unless a mechanism explains why convergence occurs.

## 30. Metastable State

A state that persists for a meaningful period but can transition when a constraint is breached or sufficient force accumulates.

## 31. Bifurcation

A qualitative change in the system’s admissible or dominant behavior following a change in a governing parameter or state variable.

Example candidate: liquidity crosses a threshold and sector behavior changes from concentration to broad propagation.

## 32. Hysteresis

Path dependence in which the state reached depends not only on current coordinates but also on the route taken to get there.

## 33. Plateau — Information

A point at which adding more observables or complexity yields negligible improvement in reconstruction, discrimination or explanatory power.

## 34. Plateau — Field

A point at which the market process itself stalls: propagation, rank migration, breadth expansion or contraction ceases despite prior momentum.

The trigger that releases or reverses this plateau is a primary mechanism question.

## 35. Flow

The movement of economically relevant quantity through the system.

Possible flow objects include capital, collateral, stablecoins, token supply, liquidity, leverage, users, attention or holdings.

Price movement alone is not automatically flow.

## 36. Propagation

A temporally ordered spread of state change or flow through connected parts of the field.

Propagation requires more evidence than contemporaneous correlation.

## 37. Mechanism

A defensible process explaining how one state or variable can transmit into another.

Mechanism evidence should include temporal ordering, conditioning, common-factor controls, stability and economic plausibility.

## 38. Correlation

Statistical association without implication of temporal direction or physical/economic cause.

## 39. Conditional Lead-Lag

A relationship in which changes in A systematically precede changes in B under specified states or conditions after accounting for important common drivers.

## 40. Cause

A strong claim reserved for cases where identification assumptions are explicit and defensible.

Predictive ordering, Granger causality or transfer entropy alone do not establish physical/economic causation.

## 41. Morphism

A structure-preserving transformation from one empirically defined object/state to another.

Market use: a recurring transformation such as

`capital reservoir -> infrastructure -> leader -> peers -> breadth -> speculative perimeter`

that may recur with different token names while preserving meaningful relational structure.

## 42. Composition

The chaining of transformations.

If `A -> B` and `B -> C` are supported, test whether the composed path `A -> C` behaves coherently and whether B is a necessary intermediary, optional route or redundant representation.

## 43. Lattice

A structured partially ordered family of states, sets, primitives or relationships in which inclusion, refinement, intersection or composition reveals hierarchy.

In this project, “lattice” is a research target: the compressed architecture remaining after redundant nodes merge and unsupported nodes dissolve.

## 44. Hierarchy

An empirically discovered ordering of explanatory levels or transformations.

Possible levels include global field, chain, sector, subsector, rank band, asset and wallet state, but the ordering must be discovered rather than imposed.

## 45. Reconstruction

The process of inferring a latent phenomenon or mechanism from one or more observable projections.

A good reconstruction explains multiple independent views with minimal unnecessary degrees of freedom and survives perturbation.

## 46. Observational Completeness

The degree to which the available observation layer captures the variables necessary to discriminate the states relevant to a given phenomenon.

Completeness is always relative to a question.

## 47. Residual

The portion of behavior left unexplained after the current model, controls and observable structure are accounted for.

Residuals can contain noise, hidden variables, regime differences, measurement error or missing mechanisms.

## 48. Information Gain

The incremental reduction in uncertainty obtained by adding a new observable, condition or representation after existing information is accounted for.

## 49. Redundancy Reduction

The process of collapsing variables, nodes or relationships that do not provide meaningful incremental structure for the question being studied.

## 50. Primitive Lattice

The eventual compressed representation of minimally redundant primitives and their empirically supported relations, states, boundaries and transformations.

This is an aspirational endpoint, not a predetermined mathematical object.

## 51. Node / Merge / Dissolve

Every research result should update the map as:

- **NEW NODE** — new non-redundant structure appears.
- **MERGE** — previously separate objects are shown to be equivalent/redundant.
- **DISSOLVE** — a pattern disappears under the correct control or correction.

## 52. Causal Evidence Ladder

Use the following ordered vocabulary:

- **L0 — DESCRIPTIVE_CO_MOVEMENT**
- **L1 — TEMPORAL_ORDERING**
- **L2 — CONDITIONAL_LEAD_LAG**
- **L3 — COMMON_FACTOR_ROBUST**
- **L4 — CROSS_REGIME_STABLE**
- **L5 — MECHANISM_SUPPORTED**
- **L6 — QUASI_CAUSAL_OR_CAUSAL** only when identification assumptions are defensible.

## 53. Formalization Trigger

Advanced math is introduced only after an empirical structure earns it.

A formalization trigger occurs when simpler descriptions repeatedly fail to capture a stable object that is visible in the data.

Examples:

- overlapping state membership -> set theory
- independent/redundant directions -> vector geometry
- connectivity/propagation -> graph theory
- persistent connectivity class -> topology
- recurrent states/transitions -> dynamical systems
- repeating structure-preserving transformations -> category theory
- scale-recurring structure -> recursive geometry
- incremental information/redundancy -> information theory

The phenomenon chooses the mathematics.
