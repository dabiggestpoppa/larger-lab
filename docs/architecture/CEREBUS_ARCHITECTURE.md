# CEREBUS Neuro-Symbolic Scanner — Architecture

> **Version:** v1.0 | **Date:** 2026-06-10 | **Status:** Wave 1-3 Complete
> **Source:** CEREBUS BUILD.txt + CEREBUS v4 Manual + ST_TIERS_AND_AU.pdf

---

## Table of Contents

1. [Master Architecture (4-Step Stack)](#master-architecture)
2. [Wave 1: Data + Features + Labels](#wave-1-data--features--labels)
3. [Wave 2: Model Training](#wave-2-model-training)
4. [Wave 3: RAG Oracle + Guardian](#wave-3-rag-oracle--guardian)
5. [Markov Chain State Machine](#markov-chain-state-machine)
6. [Trade Orchestrator](#trade-orchestrator)
7. [Data Flow Diagram](#data-flow-diagram)
8. [File Structure](#file-structure)

---

## Master Architecture

```mermaid
graph TD
    subgraph "STEP 1: Data + Features + Labels"
        A[Raw OHLCV M15/H1 Data] --> B[CEREBUS Math Engine]
        B --> C[Micro Features: AU, Tiers, Density, ILM]
        B --> D[Macro Features: MLR, Fib, 132%, Weekly]
        C & D --> E[Forward-Looking Labels]
        E --> F[(Master Parquet DB<br/>5.3M samples × 48 features)]
    end

    subgraph "STEP 2: Pattern & Regime Models"
        F --> G[XGBoost: Regime Classifier<br/>87% CV, 44 features]
        F --> H[LSTM: Temporal Sequence<br/>Pattern Recognition]
        G --> I[SHAP Physics Check<br/>dist_to_132_pips = #1 ✅]
    end

    subgraph "STEP 3: RAG Oracle"
        J[55 PDFs + v4 Manual] --> K[Smart Chunker<br/>Decision Nodes]
        K --> L[(ChromaDB Vector Store<br/>Semantic + Metadata Filter)]
        M[Live Market State] --> N[Query Engine]
        L --> N
        N --> O[Manual Rules + Citations]
    end

    subgraph "STEP 4: Guardian Alert Pipeline"
        P[M15 Candle Close] --> Q[Feature Computation]
        Q --> G
        G --> R{Alignment Check<br/>Confidence ≥ 85%<br/>Safe from Rekey<br/>Near Target}
        R -->|Pass| O
        O --> S[Rich Markdown Alert]
        S --> T[Telegram / Discord]
    end
```

---

## Wave 1: Data + Features + Labels

```mermaid
flowchart LR
    subgraph "Data Sources"
        D1[19 Asset CSVs<br/>M5 OHLCV]
        D2[Holy Grail Excel<br/>97 Sheets]
        D3[55 Predecessor PDFs<br/>1200 Pages]
    end

    subgraph "Feature Engineering"
        F1[Asian Range Extraction<br/>19:00-03:00 EST]
        F2[K-Means Tier Discovery<br/>T1/T2/T3/T4]
        F3[MLR Computation<br/>07:00-15:00 UTC]
        F4[Fib Targets<br/>-25/-50/-100/-168%]
        F5[132% Kill-Switch<br/>Structural Invalidation]
        F6[ILM State Detection<br/>Daily/IELM/WILM/Misaligned]
        F7[Regime Ratio<br/>9AM Checkpoint]
        F8[Weekly Targets<br/>Session Data]
    end

    subgraph "Labels"
        L1[label_25_delivery<br/>FAILED/CHOP/CONFIRMED]
        L2[label_50_delivery<br/>3-class]
        L3[rekey_triggered<br/>Binary]
        L4[regime_at_time<br/>4-class]
    end

    D1 --> F1 --> F2 --> F3 --> F4 --> F5 --> F6 --> F7 --> F8
    D2 --> F3
    D3 --> F5
    F1 --> L1
    F3 --> L2
    F5 --> L3
    F7 --> L4
```

---

## Wave 2: Model Training

```mermaid
flowchart TD
    A[5.3M Samples<br/>18 Assets × 44 Features] --> B[TimeSeriesSplit<br/>80/20 Train/Val]

    B --> C[XGBoost Classifier<br/>300 estimators, max_depth=6<br/>learning_rate=0.05]
    C --> D[5-Fold TimeSeriesSplit CV<br/>87.0% ± 1.7%]

    D --> E[SHAP Analysis<br/>KernelExplainer on 2000 samples]
    E --> F[Feature Importance<br/>dist_to_132_pips = #1 ✅]

    F --> G{Physics Check}
    G -->|PASS| H[Model Saved<br/>regime_classifier_full.pkl]
    G -->|FAIL| I[Retune Hyperparameters]

    subgraph "SHAP Rankings"
        H1[#1 dist_to_132_pips: 0.149]
        H2[#2 dist_to_mlr_low_pips: 0.071]
        H3[#3 fib_sequence_state: 0.059]
        H4[#4 dist_to_50_pips: 0.028]
        H5[#5 dist_to_25_pips: 0.028]
    end
    F --> H1 --> H2 --> H3 --> H4 --> H5
```

---

## Wave 3: RAG Oracle + Guardian

```mermaid
sequenceDiagram
    participant Market as Live Market (M15)
    participant Guardian as Guardian Engine
    participant Feat as Feature Engine
    participant ML as XGBoost/LSTM
    participant RAG as RAG Oracle
    participant User as Telegram/Discord

    Market->>Guardian: New Candle Close
    Guardian->>Feat: Calculate Micro/Macro States
    Feat-->>Guardian: Return Feature Vector
    Guardian->>ML: Pass Vector & 24-Candle Window
    ML-->>Guardian: Return Regime (CONFIRMED) + Confidence (92%)

    alt Alignment Check Passes
        Guardian->>RAG: Query Manual (Wed + CONFIRMED + -25% prox)
        RAG-->>Guardian: Return Rule (Tighten stops, 16:00 UTC exit)
        Guardian->>User: Push Rich Markdown Alert
    else Alignment Check Fails
        Guardian->>Guardian: Log State & Wait for next candle
    end
```

---

## Markov Chain State Machine

```mermaid
stateDiagram-v2
    [*] --> RESET: Monday 00:00 UTC
    RESET --> AR_SET: Asian Range Established (19:00-03:00 EST)

    AR_SET --> P90_FIRED: 95% of sessions
    AR_SET --> RESET: 5% NO-GO

    P90_FIRED --> T1_ACTIVE: 42% (<20p AR)
    P90_FIRED --> T2_ACTIVE: 38% (20-30p AR)
    P90_FIRED --> T3_ACTIVE: 15% (30-45p AR)
    P90_FIRED --> FAILURE: 5%

    T1_ACTIVE --> TARGET_25: 98.2%
    T1_ACTIVE --> STALL_ZONE: 34.2%
    T1_ACTIVE --> FAILURE: 1.8%

    T2_ACTIVE --> TARGET_25: 96.4%
    T2_ACTIVE --> STALL_ZONE: 35.4%
    T2_ACTIVE --> FAILURE: 3.6%

    T3_ACTIVE --> TARGET_25: 87.2%
    T3_ACTIVE --> STALL_ZONE: 38.2%
    T3_ACTIVE --> FAILURE: 12.8%

    TARGET_25 --> TARGET_50: 96.4%
    TARGET_25 --> STALL_ZONE: 34.2%
    TARGET_25 --> DEEP_STATE: 4.2%
    TARGET_25 --> HARD_EXIT: 3.8%

    TARGET_50 --> TARGET_100: 92.2%
    TARGET_50 --> REKEY: 71.5%
    TARGET_50 --> HARD_EXIT: 7.8%

    STALL_ZONE --> DEEP_STATE: 14.4%
    STALL_ZONE --> TARGET_50: 64.2%
    STALL_ZONE --> FAILURE: 21.4%

    DEEP_STATE --> REKEY: 95%
    DEEP_STATE --> FAILURE: 5%

    REKEY --> REKEY_CONSOLID: 85%
    REKEY --> REGIME_FLIP: 15%

    REKEY_CONSOLID --> REKEY_EXTENSION: 78%
    REKEY_CONSOLID --> FAILURE: 22%

    FAILURE --> HARD_EXIT: 45.2%
    FAILURE --> REGIME_FLIP: 54.8%

    REGIME_FLIP --> RESET: Next Monday
    HARD_EXIT --> RESET: Next Monday
    TARGET_100 --> HARD_EXIT: 12PM EST
    REKEY_EXTENSION --> HARD_EXIT: 12PM EST
```

---

## Trade Orchestrator

```mermaid
flowchart TD
    A[Trade Setup<br/>Symbol, Tier, AR, Regime, Session, Day, Quarter] --> B{Entry Evaluation}

    B -->|CONFIRMED + T1 + 2-4AM + Tue| C[Size: 100%<br/>Highest probability setup]
    B -->|CONFIRMED + T2 + 4-7AM| D[Size: 80%<br/>Good setup]
    B -->|CAUTION + Any| E[Size: 50%<br/>Reduced exposure]
    B -->|FAILED| F[NO ENTRY<br/>Stand down]

    C --> G[Active Trade Management]
    D --> G
    E --> G

    G --> H{State Transitions}
    H -->|TARGET_25 hit| I[Trail Stop to BE<br/>Evaluate -50% continuation]
    H -->|132% breached| J[EXIT Immediately<br/>Wait for 78.6% rekey retest]
    H -->|168% stall| K[Hedge 50%<br/>Evaluate DMR trigger]
    H -->|12PM EST| L[HARD EXIT<br/>All positions closed]
    H -->|Failure detected| M[Second Acceptance Edge<br/>69.8% WR]

    subgraph "Day-of-Week Rules"
        DW1[Tue/Wed: Play first violation<br/>75-85% real]
        DW2[Thursday: Wait for second<br/>First = coin flip]
        DW3[Friday: Mixed<br/>Tradeable but weaker]
    end

    subgraph "Seasonal Adjustments"
        S1[Q1+Q4: High risk<br/>63.7% of failures]
        S2[Q2+Q3: Optimal<br/>Best extensions]
    end
```

---

## Data Flow Diagram

```mermaid
flowchart LR
    subgraph "Input Layer"
        I1[(19 Asset CSVs<br/>M5 OHLCV)]
        I2[(Holy Grail Excel<br/>97 Sheets)]
        I3[(55 PDFs<br/>1200 Pages)]
    end

    subgraph "Processing Layer"
        P1[Data Cleanup<br/>1A]
        P2[Feature Engineering<br/>1B]
        P3[Pattern Recognition<br/>1C - PM]
        P4[Label Generation<br/>1D]
        P5[XGBoost Training<br/>2]
        P6[SHAP Analysis<br/>2]
        P7[RAG Indexing<br/>3]
    end

    subgraph "Storage Layer"
        S1[(training/<br/>18 parquet files)]
        S2[(models/<br/>regime_classifier_full.pkl)]
        S3[(rag_chroma/<br/>ChromaDB vectors)]
        S4[(shap/<br/>feature_importance_fixed.csv)]
    end

    subgraph "Output Layer"
        O1[Telegram Alerts]
        O2[Discord Webhooks]
        O3[API Endpoints]
    end

    I1 --> P1 --> P2 --> P4
    I2 --> P2
    I3 --> P7
    P2 --> P3
    P4 --> S1
    P5 --> S2
    P6 --> S4
    P7 --> S3

    S1 --> P5
    S2 --> O1
    S3 --> O1
    S4 --> O3
```

---

## File Structure

```mermaid
graph LR
    ROOT[quant-lab/ml/] --> W1[Wave 1: Data]
    ROOT --> W2[Wave 2: Models]
    ROOT --> W3[Wave 3: RAG]
    ROOT --> W4[Wave 4: Guardian]

    W1 --> W1A[phase1_data/]
    W1A --> W1A1[data_cleanup.py]
    W1A --> W1A2[full_feature_engine.py<br/>48 features/bar]
    W1A --> W1A3[label_generator_v2.py<br/>Forward-looking labels]
    W1A --> W1A4[dmr_features.py<br/>DMR/Stall-Harvest]
    W1A --> W1A5[macro/<br/>PM's 18 pattern detectors]

    W2 --> W2A[phase2_classifier/]
    W2A --> W2A1[regime_classifier.py<br/>XGBoost 87% CV]
    W2A --> W2A2[markov_chain_model.py<br/>17 states, HG priors]
    W2A --> W2A3[trade_orchestrator.py<br/>17 trade states]
    W2A --> W2A4[run_training_v2.py<br/>Full pipeline]

    W3 --> W3A[phase3_rag_oracle/]
    W3A --> W3A1[chunker.py<br/>Decision node chunking]
    W3A --> W3A2[vector_store.py<br/>ChromaDB + metadata filters]
    W3A --> W3A3[query_engine.py<br/>Market state → manual rules]
    W3A --> W3A4[rag_api.py<br/>FastAPI endpoints]

    W4 --> W4A[phase4_guardian/]
    W4A --> W4A1[guardian.py<br/>Live scanner + alerts]

    ROOT --> DATA[data/]
    DATA --> DATA1[training/<br/>18 asset parquets]
    DATA --> DATA2[models/<br/>regime_classifier_full.pkl]
    DATA --> DATA3[shap/<br/>feature_importance_fixed.csv]
    DATA --> DATA4[rag_chroma/<br/>ChromaDB vectors]

    ROOT --> TESTS[tests/]
    TESTS --> T1[test_rag_oracle.py<br/>22 tests, all passing]
```

---

## Key Metrics

| Component | Metric | Value |
|-----------|--------|-------|
| Training Data | Samples | 5.3M |
| Training Data | Features | 44 |
| Training Data | Assets | 18 |
| XGBoost | CV Accuracy | 87.0% ± 1.7% |
| XGBoost | Val Accuracy | 86.7% |
| SHAP | #1 Feature | dist_to_132_pips (0.149) |
| RAG | Chunks | 55 PDFs + manual |
| RAG | Tests | 22/22 passing |
| Markov | States | 17 |
| Orchestrator | Trade States | 17 |
