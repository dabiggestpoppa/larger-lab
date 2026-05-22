# Full SRRA-OPH Topology — Phases 1-10

> Source: CODEMAP.md (line 125)
> Phase: 6-9 Resources | Updated: Phase 10 Complete

```mermaid
graph TD
    subgraph "Local Observers"
        O1[Observer A]
        O2[Observer B]
        O3[Observer C]
    end

    subgraph "Active Collars (Phase 3)"
        AC1[Active Collar Field]
        AC2[Active Collar Field]
        AC3[Active Collar Field]
    end

    subgraph "Reconstruction (Phase 2+5)"
        TF[Trajectory Fields]
        CC[Continuity Collars]
        RP[Repair-First Continuity]
    end

    subgraph "Capability Fields (Phase 4)"
        CF1[Claude]
        CF2[VSCode]
        CF3[Memory DB]
        CF4[OpenClaw]
    end

    subgraph "Governance (Phase 9)"
        MSR[MSR Optimizer]
        MCR[MCR Optimizer]
        ES[Entropy Scheduler]
    end

    subgraph "Recursive Compute (Phase 10)"
        RCG[RecursiveComputeGraph]
        PRS[PositionalReferenceSystem]
        RPE[ResonancePropagationEngine]
        DCT[DynamicConstraintTopology]
        ACE[AttractorComputeEngine]
    end

    O1 --> AC1
    O2 --> AC1
    O2 --> AC2
    O3 --> AC2

    AC1 --> TF
    AC2 --> CC
    AC3 --> RP

    CF1 --> AC1
    CF2 --> AC2
    CF3 --> AC3
    CF4 --> AC1

    TF --> MSR
    CC --> MCR
    RP --> ES

    MSR --> RCG
    MCR --> PRS
    ES --> RPE
    RCG --> DCT
    PRS --> RPE
    RPE --> ACE
    DCT --> ACE
    ACE --> RCG
```

## Phase 10: Recursive Field Computation ✅ COMPLETE

| Module | File | Tests | Purpose |
|--------|------|-------|---------|
| RecursiveComputeGraph | `oce/backend/phase10/rcg.py` | 6 | Recursive compute graph + stabilization |
| PositionalReferenceSystem | `oce/backend/phase10/prs.py` | 5 | Positional reference system |
| ResonancePropagationEngine | `oce/backend/phase10/rpe.py` | 4 | Resonance propagation engine |
| DynamicConstraintTopology | `oce/backend/phase10/dct.py` | 4 | Dynamic constraint topology |
| AttractorComputeEngine | `oce/backend/phase10/ace.py` | 4 | Attractor compute engine |
| **Total** | | **23 tests** | |
