# SRRA-OPH Resource Reference

> Consolidated from 3 agent analyses. Organized by category with SRRA alignment rationale.

## Graph Computation & Topology

| Resource | Relevance | SRRA Phase |
|----------|-----------|------------|
| GraphBLAS | Sparse matrix topology computation | 3, 7, 9 |
| Gelly (Flink) | Dynamic graph analytics | 3, 6 |
| Pregel | Vertex-centric computation | 7 |
| GraphScope | Large-scale graph analytics | 7 |
| NetworkX | Prototyping topology algorithms | 6, 9 |
| igraph | Entropy-aware topology metrics | 6, 9 |
| Gephi | Topology visualization | 6 |
| GraphStorm | GNN-based graph ML | 6, 7 |
| DGL | Graph neural networks | 1, 7 |
| PyG | Flexible message passing | 1, 7 |
| JGraphT | Formal graph analysis | 6 |
| graph-tool | High-performance graph algorithms | 6, 9 |
| Deep Graph Library | GPU-accelerated GNNs | 7 |

## Event Sourcing & Causal Systems

| Resource | Relevance | SRRA Phase |
|----------|-----------|------------|
| EventStoreDB | Native event store | 2, 5 |
| Axon Framework | CQRS/ES | 2, 5 |
| Eventuate | Distributed event sourcing | 2, 5 |
| Apache Flink | Exactly-once stream processing | 5, 9 |
| Materialize | Streaming SQL materialized views | 2 |
| Apache Kafka | Distributed log | 2, 5 |
| Apache Pulsar | Multi-tenancy, tiered storage | 4, 9 |
| Chronicle Queue | Ultra-low-latency persistence | 2 |
| LMDB | Fast local persistence | 1, 2 |
| Badger | LSM-tree with versioning | 2, 5 |
| Redpanda | Kafka-compatible streaming | 5 |

## Active Inference & Probabilistic

| Resource | Relevance | SRRA Phase |
|----------|-----------|------------|
| Pyro | Deep probabilistic programming | 2, 5, 9 |
| NumPyro | JAX-based scalable inference | 2, 6, 9 |
| TensorFlow Probability | Hamiltonian Monte Carlo | 2, 5 |
| Edward2 | Composable distributions | 2 |
| PyMDP | Active inference implementation | 1, 8 |
| RxInfer.jl | Message-passing inference | 1, 2, 6 |
| ActiveInferenceInstitute | Active inference ecosystem | 1, 8 |
| Bean Machine | Declarative probabilistic models | 2 |

## Distributed Systems & Synchronization

| Resource | Relevance | SRRA Phase |
|----------|-----------|------------|
| FoundationDB | Bounded synchronization | 3, 9 |
| CRDTs (Yjs, Automerge) | Conflict-free eventual consistency | 3, 9 |
| DeltaCRDT | Efficient delta propagation | 2, 3 |
| Orleans | Virtual actor model | 1, 3 |
| Raft (etcd) | Consensus for recovery | 3, 9 |
| Dynamo | Eventual consistency model | 3 |
| NATS | Lightweight messaging | 3, 4 |
| Apache Mesos | Resource isolation | 4, 9 |
| Kubernetes | Container orchestration | 4, 8 |
| Nomad | Flexible workload orchestration | 4 |
| Linkerd | Service mesh observability | 3, 6 |
| Envoy | L7 proxy with dynamic routing | 3, 9 |
| Consul | Service discovery | 3, 7 |
| Dapr | Distributed application runtime | 4, 9 |

## Cognitive Architectures

| Resource | Relevance | SRRA Phase |
|----------|-----------|------------|
| Numenta HTM | Hierarchical temporal memory | 2, 5 |
| SOAR | Cognitive architecture | 1, 8 |
| ACT-R | Cognitive architecture | 2 |
| LIDA | Cognitive modeling | 2, 5 |
| OpenCog | Hypergraph reasoning | 6, 7 |
| MicroPsi | Psi-theory cognition | 1, 5 |
| Spaun | Large-scale brain model | 7 |
| Capsule Networks | Dynamic routing | 7 |
| Liquid State Machines | Reservoir computing | 2, 5 |
| BindsNET | Spiking neural networks | 1, 7 |
| Brian2 | SNN simulator | 1, 7 |
| Norse | PyTorch-based SNNs | 1, 9 |

## Formal Verification

| Resource | Relevance | SRRA Phase |
|----------|-----------|------------|
| TLA+ | Formal specification | 3, 6, 9 |
| PlusCal | Algorithmic specification | 3, 6 |
| Alloy | Relational model finding | 6, 9 |
| P | Async event-driven verification | 3, 6 |
| TLAPS | TLA+ proof system | 6, 9 |
| Coq | Proof assistant | 6, 9 |
| Isabelle/HOL | Higher-order logic | 2, 5 |
| Stateright | Model checker for distributed systems | 3, 9 |
| Ivy | Distributed protocol verification | 3 |

## Observability

| Resource | Relevance | SRRA Phase |
|----------|-----------|------------|
| OpenTelemetry | Standard instrumentation | 6, 9 |
| Prometheus | Metrics collection | 6, 9 |
| Grafana | Visualization | 6 |
| Jaeger | Distributed tracing | 5, 6 |
| Tempo | Trace storage | 5 |
| Loki | Log aggregation | 2 |
| Phlare | Continuous profiling | 9 |
| Vector | Telemetry pipeline | 9 |
| eBPF (Cilium) | Kernel-level observability | 4, 9 |
| Kiali | Service mesh visualization | 3, 6 |

## Mathematical Frameworks

| Framework | Relevance | SRRA Phase |
|-----------|-----------|------------|
| Spectral Graph Theory | Coherence metrics via Laplacian eigenvalues | 3, 6, 9 |
| Percolation Theory | Topology collapse modeling | 3 |
| Renormalization Group | Multi-scale cognitive fields | 7 |
| Catastrophe Theory | Continuity drift detection | 5 |
| Sheaf Theory | Local-to-global consistency | 6, 7 |
| Category Theory | Compositional systems | 4 |
| Information Geometry | Entropy optimization | 2, 9 |
| Topological Data Analysis | Topology introspection | 6, 7 |
| Algebraic Topology | Distributed computing limits | 6, 7 |
| Bayesian Nonparametrics | Adaptive complexity models | 2, 7 |
| Rate-Distortion Theory | Bounded memory compression | 2, 9 |
| Free Energy Principle | Active inference foundation | 1, 8, 9 |

## Key Research Papers

| Paper | Relevance | SRRA Phase |
|-------|-----------|------------|
| Friston (2010) "Free Energy Principle" | Active inference foundation | 1, 8, 9 |
| Hawkins & George (2006) "HTM" | Memory as reconstruction | 2, 5 |
| Lamport (1978) "Time, Clocks" | Vector clocks, causal ordering | 2, 3, 5 |
| Dijkstra (1974) "Self-stabilizing Systems" | Local repair loops | 1 |
| Fischer, Lynch, Paterson (1985) "Impossibility of Consensus" | Avoid universal sync | 3, 9 |
| Shannon (1948) "Mathematical Theory of Communication" | Entropy formalization | 9 |
| Cover & Thomas (2012) "Information Theory" | Mutual information metrics | 6, 9 |
| Pearl (2009) "Causality" | Causal memory | 2, 5, 6 |
| Carlsson (2009) "Topology and Data" | Persistent homology | 6, 7 |
| Herlihy et al. "Distributed Computing Through Algebraic Topology" | Topology determines computability | 6, 7 |
| Robinson "Sheaves: A Topological Theory of Distributed Consistency" | Local-to-global consistency | 6, 7 |
| Amari "Information Geometry" | Entropy optimization | 2, 9 |
| Friston "The Free Energy Principle: A Unified Brain Theory?" | Unified cognition theory | 1, 8 |
| Hoel (2017) "Causal Emergence" | Macro-level causal models | 6, 7 |
| Shapiro et al. "Conflict-free Replicated Data Types" | Local-first sync | 3 |
| Ongaro & Ousterhout "In Search of an Understandable Consensus Algorithm" | Raft consensus | 3 |
| Milner "Communicating and Mobile Systems: The π-calculus" | Mobile processes | 3 |
| Alvaro et al. "Dedalus: Datalog in Time and Space" | Disorderly programming | 3 |
| Eliasmith & Anderson "Neural Engineering" | Neural representation | 1 |
| Friston "Active Inference: A Process Theory of Epistemic Value" | Active inference | 1, 8 |
| Bertsekas & Tsitsiklis "Parallel and Distributed Computation" | Sync cost models | 3, 9 |
