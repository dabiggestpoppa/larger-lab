# CG-1 MERMAID VISUAL SPECIFICATIONS (MAD 2026-05-28)

## Master Operational Flow
```mermaid
flowchart TB
    TASK[Incoming Task] --> DOMAIN[Domain Detection]
    DOMAIN --> DOCTRINE[Micro-Doctrine Activation]
    DOCTRINE --> OBJECTIVE[Objective Hierarchy]
    OBJECTIVE --> CONSTRAINT[Constraint Awareness]
    CONSTRAINT --> TOPOLOGY[Micro-Topology Synthesis]
    TOPOLOGY --> VALIDATE[Pre-Execution Validation]
    VALIDATE --> PLAN[Execution Planning]
    PLAN --> EXEC[Execution]
```

## Component 1: Domain Activation Flow
```mermaid
flowchart LR
    TASK[Task] --> DETECT[Domain Detection]
    DETECT --> TRADING[Trading Overlay]
    DETECT --> CODING[Coding Overlay]
    DETECT --> DEPLOY[Deployment Overlay]
    DETECT --> REPAIR[Repair Overlay]
    DETECT --> ORCH[Orchestration Overlay]
```

## Component 2: Micro-Doctrine Injection
```mermaid
flowchart TD
    DOMAIN[Active Domain] --> DOCTRINE[Doctrine Registry]
    DOCTRINE --> LAWS[Operational Laws]
    LAWS --> PRIORITY[Priority Hierarchy]
    PRIORITY --> CONSTRAINTS[Constraint Activation]
    CONSTRAINTS --> GOVERNANCE[Governed Planning]
```

## Component 3: Pre-Execution Validation Loop
```mermaid
flowchart TB
    ACTION[Proposed Action] --> RISK[Risk Analysis]
    RISK --> DEPENDENCY[Dependency Check]
    DEPENDENCY --> STRUCTURE[Structure Check]
    STRUCTURE --> VALIDATION[Validation Check]
    VALIDATION --> APPROVE[Approved]
    VALIDATION --> BLOCK[Blocked]
```

## Component 4: Micro-Topology Thinking
```mermaid
flowchart TD
    OBJECTIVE[Objective] --> CONSTRAINTS[Constraints]
    CONSTRAINTS --> RISKS[Risks]
    RISKS --> DEPENDENCIES[Dependencies]
    DEPENDENCIES --> VALIDATION[Validation]
    VALIDATION --> EXECUTION[Execution]
```

## Component 5: Execution Gating
```mermaid
flowchart LR
    PROPOSE[Proposed Execution] --> GOVERNANCE[Governance Gate]
    GOVERNANCE --> VALIDATE[Validation Gate]
    VALIDATE --> APPROVE[Execution Approved]
    VALIDATE --> REJECT[Execution Rejected]
```

## Component 6: Priority Hierarchy Engine
```mermaid
flowchart TD
    CONTINUITY[Continuity] --> SAFETY[Safety]
    SAFETY --> STABILITY[Operational Stability]
    STABILITY --> OBJECTIVE[Objective Achievement]
    OBJECTIVE --> EXECUTION[Execution]
```

## Trading Domain Example
```mermaid
flowchart TB
    STRATEGY[Trading Strategy] --> RISK[Risk Controls]
    RISK --> SLTP[SL / TP]
    SLTP --> DRAWDOWN[Drawdown Limits]
    DRAWDOWN --> VALIDATE[Validation]
    VALIDATE --> DEPLOY[Deployment]
```

## Failure Detection Flow
```mermaid
flowchart TD
    EXECUTION[Execution Plan] --> MISSING[Missing Structure Detection]
    MISSING --> RISK[Risk Gap]
    MISSING --> VALIDATION_GAP[Validation Gap]
    MISSING --> CONSTRAINT[Constraint Violation]
    RISK --> BLOCK[Execution Block]
    VALIDATION_GAP --> BLOCK
    CONSTRAINT --> BLOCK
```

## OC2 Governed Execution Model (Sequence)
```mermaid
sequenceDiagram
    participant USER as Operator
    participant OC2
    participant DOMAIN as Domain Layer
    participant DOC as Doctrine
    participant TOPO as Topology
    participant VAL as Validation
    participant EXEC as Execution

    USER->>OC2: Task
    OC2->>DOMAIN: Detect Domain
    DOMAIN->>DOC: Load Doctrine
    DOC->>TOPO: Generate Micro-Topology
    TOPO->>VAL: Validate Structure
    VAL->>EXEC: Approve Execution
    EXEC-->>USER: Governed Output
```

---
_CG-1 Visual Specs | 2026-05-28 | For reference. Internal思维 tool, not for constant rendering._
