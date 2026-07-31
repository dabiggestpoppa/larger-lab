# Phase 5, Book 1 — Discovery Contracts and Universe

> **Purpose:** Admit bounded discovery requests and construct survivorship-safe, point-in-time tradable universes  
> **Input:** Phase 3 data contracts and Phase 4 approved `DiscoveryRequest`  
> **Output:** `ScanRequest`, `UniverseSnapshot`, and `TradabilitySnapshot`  
> **Previous:** Phase 4 — Intelligence Forge  
> **Next:** [Book 2 — Deterministic Feature Fabric](book-2-deterministic-feature-fabric.md)

---

## 1. Success Statement

Given the same request, cutoff, policies, calendars, and data manifest, the system returns the same eligible instrument identities and the same exclusion reasons—including historically valid delisted securities.

---

## 2. Applicable Anchors

- **A1:** One Orchestration Spine
- **A2:** Evidence Before Narrative
- **A3:** Point-in-Time Data
- **A4:** Stable Identity Everywhere
- **A8:** Idempotent Event Handling
- **A10:** Observable and Reconstructable
- **F1:** Canonical schema and lineage
- **F3:** Passing data manifest required
- **F4:** Testable research only
- **F5:** Code scans broad markets

---

## 3. Universe Topology

```mermaid
flowchart LR
    D["DiscoveryRequest"] --> G["Admission gate"]
    G --> P["UniversePolicy"]
    P --> M["Membership snapshot"]
    M --> I["Identity resolution"]
    I --> T["Tradability gates"]
    T --> U["UniverseSnapshot"]
    T --> X["Exclusion ledger"]
```

---

## 4. Work Packages

### 4.1 Request admission

The adapter verifies schema, Intelligence Lock, thesis state, cutoff, expiration, requested asset classes, feature availability, universe policy, result bound, and prohibited fields.

It produces:

```yaml
scan_request_id: typed-id
discovery_request_ref: artifact-ref
research_thesis_ref: artifact-ref
as_of: RFC3339 UTC
universe_policy_ref: policy-id
data_policy_refs: []
required_feature_refs: []
scanner_refs: []
ranking_policy_ref: policy-id
maximum_result_count: integer
expires_at: timestamp
idempotency_key: string
```

### 4.2 Universe policy

The policy declares asset classes, venues, listing types, geographies, currencies, sectors, share classes, corporate-action handling, status rules, and effective-time semantics.

Free-form “all stocks” is invalid. Every population has a named policy and version.

### 4.3 Point-in-time membership

Membership uses effective intervals:

```text
listed_at <= as_of
AND (delisted_at is null OR as_of < delisted_at)
AND membership_start <= as_of
AND (membership_end is null OR as_of < membership_end)
```

Current index constituents cannot substitute for historical members.

### 4.4 Stable identity

Issuer, listing, instrument, venue, currency, and share class remain separate. Symbol changes, mergers, spin-offs, ADRs, duplicate listings, and corporate-action lineages resolve through Phase 3.

### 4.5 Tradability gates

Deterministic gates may include:

- active session/calendar state;
- valid price and corporate-action adjustment policy;
- minimum price;
- rolling median dollar volume;
- minimum observation count;
- spread or liquidity proxy;
- stale-price threshold;
- halt/suspension status;
- security-type eligibility;
- borrowability only when explicitly supplied for research.

Every gate stores input, threshold, result, and policy version.

### 4.6 Data completeness

Required fields missing at cutoff exclude the instrument with a reason. Optional fields remain null and flow to feature/ranking policies. A partial universe cannot silently masquerade as complete.

### 4.7 Universe snapshot

```yaml
universe_snapshot_id: content-id
scan_request_ref: artifact-ref
as_of: timestamp
policy_ref: policy-id
data_manifest_ref: artifact-ref
calendar_version: semver
included_instruments: []
exclusions: []
coverage_summary: {}
input_hashes: []
builder_version: semver
```

Rows are sorted by stable instrument ID before hashing.

### 4.8 External screeners

TradingView, OpenBB, or other screeners may serve as adapters or comparison sources. They are not the canonical universe unless their historical membership, timestamp, identity, licensing, and reproducibility meet Phase 3 and Book 1 contracts.

---

## 5. Target Layout

```text
discovery/
  contracts/
    scan_request.py
    admission.py
  universe/
    policy.py
    membership.py
    identity.py
    tradability.py
    exclusions.py
    snapshot.py
```

---

## 6. Deliverables

- Phase 4-to-5 admission adapter.
- Versioned universe-policy registry.
- Point-in-time membership builder.
- Stable instrument identity adapter.
- Liquidity/tradability gate registry.
- Immutable universe and exclusion snapshots.
- Coverage and survivorship audit reports.
- Historical fixtures covering corporate actions and listing changes.

---

## 7. Required Tests

### P5-REQ-001 — Valid Request Admission

A valid, locked, unexpired request produces one idempotent `ScanRequest`.

### P5-REQ-002 — Expired Request Rejection

An expired, rejected, or superseded thesis cannot begin or resume a scan.

### P5-REQ-003 — Prohibited Field Rejection

Entry, exit, target, size, strategy, portfolio, broker, and order fields fail schema validation.

### P5-REQ-004 — Scope Bound

The admitted request cannot broaden asset, geography, universe, feature, scanner, or result limits.

### P5-UNI-001 — Deterministic Universe

A fixed request and manifest produce identical ordered identities and snapshot hash.

### P5-UNI-002 — Delisted Inclusion

A historically listed but currently delisted security appears when valid at the historical cutoff.

### P5-UNI-003 — Future Listing Exclusion

An instrument listed after the cutoff is absent.

### P5-UNI-004 — Share-Class Separation

Multiple share classes remain distinct while retaining issuer lineage.

### P5-UNI-005 — Symbol Change

Historical symbols resolve to the correct stable instrument without rewriting identity.

### P5-UNI-006 — Index Membership Interval

Historical index scans use effective membership rather than current constituents.

### P5-PIT-001 — Survivorship Guard

A known survivor-only fixture fails and the complete historical fixture passes.

### P5-PIT-002 — Corporate Action Cutoff

Merger, split, spin-off, and delisting data become visible only at their admissible times.

### P5-PIT-003 — Calendar Pin

Session eligibility reproduces under the pinned exchange-calendar version.

### P5-TRD-001 — Tradability Edge Cases

Boundary values for price, dollar volume, observation count, stale price, and halt status resolve exactly.

### P5-TRD-002 — Exclusion Explanation

Every removed instrument records all failed gates and inputs.

### P5-TRD-003 — Required Missing Data

Missing required data excludes rather than zero-fills.

### P5-TRD-004 — Optional Missing Data

Missing optional data remains null without removing an otherwise eligible instrument.

### P5-IDN-001 — Ambiguous Symbol Rejection

An unresolved or ambiguous symbol cannot enter the universe.

### P5-IDN-002 — Venue Identity

The same ticker text on different venues resolves to distinct instrument IDs.

### P5-MAN-001 — Failed Manifest Block

A failed Phase 3 data manifest blocks universe publication.

---

## 8. Failure Modes

- Current constituents used historically.
- Current ticker treated as permanent identity.
- Missing values converted to zero.
- External screener results accepted without lineage.
- Liquidity computed with future observations.
- Hidden universe shrinkage after provider failure.
- Request scope expanded for convenience.

---

## 9. Exit Gate

Book 1 is complete only when request admission fails closed, historical universes reproduce, survivorship fixtures pass, every exclusion is explained, and a content-addressed universe snapshot is ready for feature computation.

---

## 10. Handoff

Book 2 receives only the admitted scan request, immutable universe snapshot, tradability decisions, cutoff, and passing Phase 3 manifest.
