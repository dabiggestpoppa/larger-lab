# OBB-02 — OpenBB Foundation

> **Program:** GLX FORGE OpenBB Operational Integration  
> **Status:** planned  
> **Required predecessor:** OBB-01 locked  
> **Authority effect:** Read-only market and research data only  
> **Capital authority:** None  
> **Broker authority:** None  
> **Phase anchor:** A real provider response is not usable until it is normalized, lineaged, quality-checked, and exposed through an approved FORGE seam.

## Why This Phase Exists

The existing FORGE data package contains provider and gateway abstractions, but they are not yet connected to OpenBB. The existing dashboard has workflow controls, but it does not yet display real market or research data through OpenBB Workspace.

OBB-02 turns those abstractions into a real, bounded data and analyst-workspace foundation.

## Phase Objective

At lock, the system can:

1. Run a controlled OpenBB integration service.
2. Detect and report its available data capabilities.
3. Query one real approved dataset through OpenBB.
4. Normalize the response into FORGE contracts.
5. Preserve provider, request and retrieval lineage.
6. Store or catalog the normalized result appropriately.
7. Expose the result through an OpenBB Workspace widget.
8. Display explicit unavailable, stale, partial and error states.
9. Do all of the above without enabling research agents, backtests, paper trading, brokerage, or execution.

## Phase Topology

~~~mermaid
flowchart TD
    A["OpenBB Data Platform"] --> B["FORGE OpenBB Adapter"]
    B --> C["FORGE Data Gateway"]
    C --> D["Canonical Data Contract"]
    D --> E["Data Catalog / Artifact Store"]
    D --> F["Workspace Backend"]
    F --> G["OpenBB Workspace Widget"]
~~~

## Phase Scope

Included:

- Package and runtime design for OpenBB.
- OpenBB availability and capability health reporting.
- One approved read-only provider path.
- Symbol and timestamp normalization.
- Data provenance and quality fields.
- Provider fallback policy.
- Workspace custom backend.
- Initial widget configuration and app layout.
- Local-first container/service topology.
- Health, readiness and failure-state contracts.

Excluded:

- News or macro interpretation agents.
- Deep research agents.
- Whole-market stock ranking logic.
- Strategy generation.
- Nautilus backtesting.
- Paper or shadow trading.
- Broker connections.
- Portfolio capital allocation.
- Live execution.
- Unbounded data crawling.
- Silent paid-provider fallback.

## Book Sequence

| Book | Name | Primary output | Cannot begin until |
|---|---|---|---|
| 1 | Runtime and Adapter Boundary | Controlled OpenBB integration runtime | OBB-01 lock |
| 2 | Canonical Data and Provenance | Real normalized data path with lineage | Book 1 |
| 3 | Workspace Backend and Widgets | First GLX research app in OpenBB Workspace | Book 2 |
| 4 | Local Runtime, Health and Readiness | Reproducible local service topology | Book 3 |

---

# Book 1 — OpenBB Runtime and Adapter Boundary

> **Purpose:** Introduce OpenBB as an isolated, configurable runtime behind a FORGE-owned adapter interface.  
> **Output:** Dependency policy, settings model, health contract, capability model, adapter skeleton and provider-registration policy.

## Design Rule

Only approved adapter paths may import OpenBB SDK packages.

~~~mermaid
flowchart LR
    A["FORGE Consumers"] --> B["MarketDataGateway Interface"]
    B --> C["OpenBBAdapter"]
    C --> D["OpenBB SDK / API"]
    D --> E["Configured Providers"]
~~~

The rest of FORGE must depend on the interface, not the OpenBB SDK.

## Required Interface Family

~~~text
MarketDataGateway
  - health()
  - capabilities()
  - historical_prices()
  - company_profile()
  - fundamentals()
  - macro_series()
  - economic_calendar()
  - company_news()
  - universe()

OpenBBAdapter
  - translates FORGE request into OpenBB call
  - normalizes provider response
  - returns data plus lineage
  - classifies availability and errors

ProviderRegistry
  - approved providers
  - credential requirement
  - data domains
  - rate limits
  - fallback order
  - allowed environments
~~~

## Capability Contract

Each capability must report:

| Field | Meaning |
|---|---|
| capability_id | Stable machine identifier |
| data_domain | Prices, fundamentals, macro, news, universe, calendar |
| status | available, unavailable, degraded, blocked, unknown |
| provider | Provider selected or attempted |
| credential_state | not_required, configured, missing, invalid, unknown |
| freshness | Real-time, delayed, end-of-day, historical, unknown |
| environment | local, test, production-like |
| limitation | Rate, coverage, entitlement, unsupported field |
| checked_at | Time of health evaluation |

## Required Deliverables

~~~text
integrations/openbb/
├── README.md
├── settings.py
├── adapter.py
├── capabilities.py
├── health.py
├── provider_registry.py
├── errors.py
└── tests/
    ├── test_settings.py
    ├── test_capabilities.py
    ├── test_adapter_boundary.py
    └── test_provider_registry.py
~~~

Exact final paths may adapt to the repository conventions, but the adapter boundary must remain explicit.

## Required Tests

- The application starts with no provider key and reports unavailable rather than crashing.
- A configured capability reports provider and freshness.
- Unsupported calls return typed errors.
- An unapproved provider cannot be selected.
- OpenBB imports outside the approved adapter path fail architecture validation.
- Credential values never appear in logs, artifacts or dashboard payloads.
- Capability checks are bounded and do not launch broad data scans.

## Failure Injections

- Missing provider credential.
- Invalid provider credential.
- OpenBB package unavailable.
- OpenBB provider endpoint timeout.
- Rate limit response.
- Unsupported asset/data combination.
- OpenBB response with an unexpected field shape.

## Non-Goals

- Do not connect every OpenBB provider.
- Do not add broad paid data plans.
- Do not embed provider credentials in repository files.
- Do not let downstream modules make raw SDK calls.
- Do not treat OpenBB as canonical historical storage.

## Book 1 Exit Gate

A local adapter process can truthfully state what it can and cannot access, and all access passes through the adapter boundary.

---

# Book 2 — Canonical Data, Quality and Provenance

> **Purpose:** Turn one real OpenBB response into a reproducible FORGE data artifact with explicit lineage and quality.  
> **Output:** Normalization rules, request/response manifests, data-quality checks, point-in-time policy and catalog contract.

## Core Data Flow

~~~mermaid
flowchart TD
    A["FORGE Data Request"] --> B["OpenBB Adapter"]
    B --> C["Provider Response"]
    C --> D["Normalization"]
    D --> E["Quality Validation"]
    E --> F["Lineage Manifest"]
    F --> G["Cataloged FORGE Artifact"]
    G --> H["Workspace Widget or Future Consumer"]
~~~

## First Supported Slice

The initial slice must be narrow. Recommended first implementation:

| Dataset | Initial use | Why first |
|---|---|---|
| Equity historical prices | Charts and basic scanner inputs | Clear schema and direct validation |
| Company profile | Candidate context | Small, explainable payload |
| Macro series or economic calendar | Macro workspace proof | Supports later intelligence phase |

Implement one dataset fully before expanding to others.

## Required Data Artifact Fields

~~~text
data_artifact_id
schema_version
dataset_type
instrument_id or series_id
provider
provider_endpoint
provider_request_parameters
retrieved_at
observed_at
coverage_start
coverage_end
frequency
timezone
normalization_version
quality_status
quality_flags
cache_status
source_hash
lineage_id
~~~

## Quality Rules

- Timestamp timezone must be explicit.
- Instrument mapping must be explicit.
- Missing fields remain missing.
- Numeric values must retain units and currency.
- Corporate-action treatment must be declared.
- Frequency conversion must be declared.
- Duplicate observations must be classified, not silently overwritten.
- Historical data selection must be reproducible from manifest fields.

## Point-in-Time Rule

OpenBB is used for provider access. It does not automatically make data safe for historical testing.

~~~mermaid
flowchart TD
    A["Current Provider Response"] --> B{"Historical experiment?"}
    B -->|"No"| C["Operational / research artifact"]
    B -->|"Yes"| D["Versioned historical catalog required"]
    D --> E["Point-in-time manifest"]
    E --> F["Nautilus may consume later in OBB-04"]
~~~

A live response cannot silently enter a historical validation run.

## Required Tests

- Real provider response normalizes into a canonical FORGE contract.
- Provider, endpoint and retrieval time appear in the artifact.
- Symbol aliases resolve deterministically.
- Timezone normalization is deterministic.
- A missing field becomes a quality flag.
- Duplicate timestamps trigger declared behavior.
- Cached and fresh data are distinguishable.
- Current operational data cannot satisfy a historical-data request.
- Provider fallback is recorded, not hidden.

## Failure Injections

- Provider returns no rows.
- Provider returns wrong timezone.
- Provider returns a symbol mapping mismatch.
- Provider returns duplicate timestamps.
- Provider returns data later than an experiment cutoff.
- Provider changes a required field name.
- Cache contains stale data.

## Non-Goals

- Do not build the full historical lake here.
- Do not execute a backtest.
- Do not calculate strategy performance.
- Do not allow a data-quality warning to be silently ignored.
- Do not use inferred timezones.

## Book 2 Exit Gate

One real response survives normalization, quality checks and lineage capture, and is reproducibly accessible through a FORGE artifact.

---

# Book 3 — OpenBB Workspace Backend and Initial Widgets

> **Purpose:** Expose verified FORGE data through an OpenBB Workspace application without rebuilding a financial dashboard from scratch.  
> **Output:** Custom backend, widgets configuration, app layout, parameter contract and widget-quality tests.

## Workspace Role

~~~mermaid
flowchart TD
    A["OpenBB Workspace"] --> B["GLX Research App"]
    B --> C["FORGE Custom Backend"]
    C --> D["FORGE Data Gateway"]
    D --> E["OpenBB Adapter"]
    E --> F["Approved Data Providers"]
~~~

Workspace displays results. It does not own workflow authority.

## First GLX Workspace App

Name: **GLX Research Foundation**

Initial widgets:

| Widget | Data source | Purpose |
|---|---|---|
| Market Data Health | OBB-02 capability contract | What data is available right now |
| Equity Price Explorer | Canonical historical-price artifact | Inspect price history and parameters |
| Company Context Card | Profile artifact | Quick company facts with provenance |
| Macro Series Explorer | Macro artifact | Display one verified macro series |
| Data Lineage Panel | Artifact manifests | Show provider, timestamp, parameters and quality |
| Provider Status Board | Capability service | Surface unavailable/degraded providers |

## Widget Contract Rules

Every widget must declare:

- Stable widget ID.
- Category.
- Backend endpoint.
- Parameter schema.
- Data schema.
- Supported visualization type.
- Required capability.
- Empty-state behavior.
- Error-state behavior.
- Provenance display behavior.
- Allowed refresh policy.

## Required Deliverables

~~~text
integrations/openbb/workspace/
├── widgets.json
├── apps.json
├── README.md
├── examples/
│   └── GLX_RESEARCH_FOUNDATION.md
└── tests/
    ├── test_widgets_schema.py
    ├── test_apps_schema.py
    ├── test_widget_endpoints.py
    └── test_widget_states.py
~~~

## Required Tests

- Every widget configuration references a real endpoint.
- Every endpoint response matches declared fields.
- Required parameters validate.
- Empty data renders an explicit empty state.
- Missing provider capability renders unavailable.
- Error payloads do not leak credentials.
- Provenance fields are visible to the user.
- A Workspace refresh does not trigger duplicate workflow activity.

## Failure Injections

- Widget endpoint returns malformed JSON.
- Required widget parameter is missing.
- Provider becomes unavailable after app load.
- Artifact is stale.
- Widget references a deleted capability.
- Large response exceeds declared display limit.

## Non-Goals

- No research agents yet.
- No stock ranking logic yet.
- No dashboard execution controls.
- No broker or account widgets.
- No custom HTML trading terminal.

## Book 3 Exit Gate

The GLX Research Foundation app displays at least one real, lineaged artifact with clear capability, empty and failure states.

---

# Book 4 — Local Runtime, Health and Readiness

> **Purpose:** Define a reproducible local-first topology for OCE, FORGE and OpenBB integration services and prove that the system fails safely.  
> **Output:** Local runtime profile, environment templates, health/readiness contract, service topology and recovery runbook.

## Target Topology

~~~mermaid
flowchart TD
    subgraph LocalCore["Persistent Local Core"]
        O["OCE"]
        F["FORGE API"]
        DB["PostgreSQL"]
        R["Redis"]
    end

    subgraph Integration["OpenBB Integration"]
        A["OpenBB Adapter"]
        W["Workspace Backend"]
    end

    subgraph External["External"]
        P["Approved Providers"]
        U["OpenBB Workspace"]
    end

    U --> W
    W --> F
    F --> A
    A --> P
    F --> O
    O --> DB
    O --> R
~~~

## Required Runtime States

| State | Meaning |
|---|---|
| not_configured | Service or required provider is not configured |
| starting | Process is beginning initialization |
| ready | Health and required dependencies pass |
| degraded | Noncritical capability unavailable |
| blocked | Required dependency unavailable |
| failed | Service cannot fulfill declared contract |
| paused | Administrative or safety pause |
| stopping | Graceful shutdown in progress |

## Readiness Rules

A service is not ready merely because its process exists.

Readiness must check:

- Process responsiveness.
- Required configuration validity.
- Database/queue availability where relevant.
- Adapter import readiness.
- Capability status.
- Ability to produce a bounded health response.
- No credential exposure.
- Version and configuration fingerprint.

## Required Deliverables

~~~text
deploy/
├── compose.openbb-foundation.yml
├── env.example
├── service-topology.md
├── health-contract.md
├── readiness-checklist.md
└── recovery-runbook.md
~~~

The exact container tool may be Docker Compose or Podman Compose, but the service contract must remain tool-neutral.

## Required Tests

- Services report not_configured without keys.
- Service reports degraded if optional provider is absent.
- Service reports blocked if a required dependency is unavailable.
- Health endpoint contains no secrets.
- Configuration mismatch is visible.
- Restart preserves only allowed persistent state.
- Widget backend reports unavailable while adapter is down.
- Service recovery restores readiness without duplicating requests.

## Failure Injections

- Stop adapter while Workspace backend is live.
- Stop database while FORGE API is live.
- Provide malformed environment setting.
- Introduce port conflict.
- Restart a service while a request is in flight.
- Simulate a provider timeout during health evaluation.

## Non-Goals

- No cloud production deployment.
- No autoscaling.
- No live brokerage runtime.
- No persistent unbounded worker fleet.
- No automatic repair that changes execution permissions.

## Book 4 Exit Gate

A fresh local environment starts predictably, reports truthful readiness, visibly degrades when dependencies fail, and recovers without duplicating work or hiding failures.

---

# OBB-02 Lock Gate

OBB-02 locks only when all books are independently verified and the following integration proof exists:

~~~mermaid
sequenceDiagram
    participant P as Approved Provider
    participant O as OpenBB Adapter
    participant F as FORGE Gateway
    participant W as Workspace Backend
    participant U as OpenBB Workspace

    P->>O: Real read-only response
    O->>F: Normalized data plus lineage
    F->>W: Canonical artifact
    W->>U: Widget payload and provenance
~~~

## Required Gate Evidence

- Approved adapter boundary.
- Capability report from the real runtime.
- At least one real normalized artifact.
- Data-quality and provenance report.
- Workspace widget screenshot or reproducible render evidence.
- Empty, unavailable and degraded state evidence.
- Local runtime health/readiness results.
- Independent review record.
- Proof that no execution or capital authority was introduced.

## Handoff to OBB-03

Once locked, OBB-03 may use the verified Workspace context and data artifacts to build:

> Macro/news intelligence, theme mapping, market scanning, candidate ranking and deep-research agents that can propose—but never self-approve—StrategySpecs.
