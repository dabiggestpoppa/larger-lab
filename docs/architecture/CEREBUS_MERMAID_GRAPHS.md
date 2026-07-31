# CEREBUS Neuro-Symbolic Scanner — Mermaid Graphs

> **Purpose:** All Mermaid diagrams for the CEREBUS build.
> **Last Updated:** 2026-06-10

---

## 1. Master 4-Step Architecture

```mermaid
graph TD
    subgraph "STEP 1: Data + Features"
        A[Raw OHLCV] --> B[CEREBUS Math Engine]
        B --> C[Micro Features]
        B --> D[Macro Features]
        C & D --> E[Labels]
        E --> F[(Parquet DB)]
    end

    subgraph "STEP 2: Models"
        F --> G[XGBoost 87% CV]
        F --> H[LSTM Patterns]
    end

    subgraph "STEP 3: RAG Oracle"
        I[PDFs + Manual] --> J[Smart Chunker]
        J --> K[(ChromaDB)]
        L[Market State] --> M[Query Engine]
        K --> M
    end

    subgraph "STEP 4: Guardian"
        N[M15 Candle] --> O[Features]
        O --> G
        G --> P{Alignment}
        P --> Q[RAG Query]
        Q --> R[Telegram Alert]
    end
```

---

## 2. Neuro-Symbolic Scanner Pipeline

```mermaid
flowchart LR
    A[Raw Data] --> B[Data Cleanup]
    B --> C[Feature Engineering<br/>48 features]
    C --> D[Label Generation<br/>Forward-looking]
    D --> E[Training Data<br/>5.3M samples]
    E --> F[XGBoost Training<br/>TimeSeriesSplit CV]
    F --> G[SHAP Analysis<br/>Physics Check]
    G --> H[Model Saved]
    H --> I[Guardian Pipeline<br/>Live Scanning]
    I --> J[Alignment Check]
    J --> K[RAG Oracle Query]
    K --> L[Alert Dispatch]
```

---

## 3. Markov Chain State Machine

```mermaid
stateDiagram-v2
    [*] --> RESET
    RESET --> AR_SET
    AR_SET --> P90_FIRED
    P90_FIRED --> T1_ACTIVE
    P90_FIRED --> T2_ACTIVE
    P90_FIRED --> T3_ACTIVE
    T1_ACTIVE --> TARGET_25
    T2_ACTIVE --> TARGET_25
    T3_ACTIVE --> TARGET_25
    TARGET_25 --> TARGET_50
    TARGET_50 --> REKEY
    REKEY --> REKEY_CONSOLID
    REKEY_CONSOLID --> REKEY_EXTENSION
    TARGET_25 --> STALL_ZONE
    STALL_ZONE --> DEEP_STATE
    DEEP_STATE --> REKEY
    [*] --> HARD_EXIT
```

---

## 4. Guardian Alert Flow

```mermaid
sequenceDiagram
    participant M as Market
    participant G as Guardian
    participant X as XGBoost
    participant R as RAG Oracle
    participant T as Telegram

    M->>G: Candle Close
    G->>G: Compute Features
    G->>X: Predict Regime
    X-->>G: CONFIRMED @ 92%
    alt Alignment Passes
        G->>R: Query Manual
        R-->>G: Manual Directive
        G->>T: Push Alert
    else Alignment Fails
        G->>G: Log & Wait
    end
```

---

## 5. RAG Oracle Architecture

```mermaid
flowchart TD
    A[55 PDFs] --> B[Smart Chunker]
    C[v4 Manual] --> B
    B --> D{Chunk Classifier}
    D -->|Temporal| E[Wednesday/12PM/MLR]
    D -->|Structural| F[132%/T3/Regime]
    D -->|Asset| G[EURUSD/OIL/BTC]
    E & F & G --> H[(ChromaDB Vector Store)]
    I[Market State] --> J[Query Builder]
    J --> K[Vector Query]
    H --> K
    K --> L[Top-5 Rules + Citations]
```

---

## 6. Feature Engineering Pipeline

```mermaid
flowchart LR
    A[OHLCV M15] --> B[Asian Range<br/>19:00-03:00 EST]
    A --> C[MLR<br/>07:00-15:00 UTC]
    A --> D[Session Detection]
    B --> E[K-Means Tiers<br/>T1/T2/T3/T4]
    C --> F[Fib Extensions<br/>-25/-50/-100/-168%]
    C --> G[132% Kill-Switch]
    D --> H[ILM State]
    E --> I[AU Deficit]
    F --> J[Distance Features]
    G --> K[Kill-Switch Proximity]
    H --> L[Regime Ratio]
    I & J & K & L --> M[44 Feature Vector]
```

---

## 7. Trade Orchestrator State Flow

```mermaid
flowchart TD
    A[Entry Eval] --> B{Regime?}
    B -->|CONFIRMED| C[Size 100%]
    B -->|CAUTION| D[Size 50%]
    B -->|FAILED| E[NO ENTRY]

    C --> F[Active Management]
    D --> F

    F --> G{State?}
    G -->|TARGET_25| H[Trail to BE]
    G -->|132% BREACH| I[EXIT + Rekey]
    G -->|168% STALL| J[Hedge 50%]
    G -->|12PM EST| K[HARD EXIT]
    G -->|FAILURE| L[2nd Acceptance]

    subgraph "Modifiers"
        M[Day-of-Week<br/>Tue/Wed strongest]
        N[Seasonal<br/>Q2/Q3 optimal]
        O[Session<br/>2-4AM cleanest]
    end
```

---

## 8. Data Flow (End-to-End)

```mermaid
flowchart TB
    subgraph Input
        I1[19 Asset CSVs]
        I2[Holy Grail Excel]
        I3[55 PDFs]
    end

    subgraph Processing
        P1[Cleanup]
        P2[Features]
        P3[Labels]
        P4[Training]
    end

    subgraph Storage
        S1[(training/)]
        S2[(models/)]
        S3[(rag_chroma/)]
    end

    subgraph Output
        O1[Telegram]
        O2[Discord]
        O3[API]
    end

    I1 --> P1 --> P2 --> P3
    I2 --> P2
    I3 --> S3
    P3 --> S1 --> P4 --> S2
    S2 --> O1
    S3 --> O1
    S2 --> O3
```

---

## 9. SHAP Feature Importance

```mermaid
bar title SHAP Mean Absolute Values (Top 10)
    x-axis: Features
    y-axis: Mean |SHAP|
    dist_to_132_pips: 0.149
    dist_to_mlr_low_pips: 0.071
    fib_sequence_state: 0.059
    dist_to_50_pips: 0.028
    dist_to_25_pips: 0.028
    dist_to_168_pips: 0.027
    dist_to_100_pips: 0.015
    hour_est: 0.013
    hours_since_mlr: 0.012
    day_of_week: 0.011
```

---

## 10. System File Structure

```mermaid
graph LR
    ROOT[quant-lab/ml/] --> P1[phase1_data/]
    ROOT --> P2[phase2_classifier/]
    ROOT --> P3[phase3_rag_oracle/]
    ROOT --> P4[phase4_guardian/]
    ROOT --> D[data/]
    ROOT --> T[tests/]

    P1 --> F1[full_feature_engine.py]
    P1 --> F2[label_generator_v2.py]
    P1 --> F3[dmr_features.py]
    P1 --> F4[macro/ - 18 patterns]

    P2 --> M1[regime_classifier.py]
    P2 --> M2[markov_chain_model.py]
    P2 --> M3[trade_orchestrator.py]

    P3 --> R1[chunker.py]
    P3 --> R2[vector_store.py]
    P3 --> R3[query_engine.py]

    P4 --> G1[guardian.py]

    D --> D1[training/ - 18 parquets]
    D --> D2[models/]
    D --> D3[shap/]
    D --> D4[rag_chroma/]

    T --> T1[test_rag_oracle.py - 22 tests]
```
