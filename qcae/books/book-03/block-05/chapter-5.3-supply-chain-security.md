# Chapter 5.3 — Supply Chain Security

## Mission

Treat every external source/artifact and its dependency chain as untrusted until QCAE has bounded what can execute, what can change, and what upstream identities produced it.

## 5.3.1 Threat Surface

Inspect risk from:

- compromised maintainer/account;
- dependency confusion/typosquatting;
- malicious install/build scripts;
- mutable tags/branches;
- unpinned dependencies;
- artifact/source mismatch;
- vendored binaries;
- download-at-build/runtime behavior;
- code generation;
- compromised transitive dependency;
- abandoned packages;
- unexpected network execution.

## 5.3.2 Immutable Inputs

Proving should prefer immutable source revisions and artifact digests. Floating dependencies are recorded as reproducibility/security defects unless unavoidable and explicitly controlled.

## 5.3.3 Source vs Artifact

Where distributed artifacts are used, QCAE distinguishes reviewed source from executed artifact. If equivalence cannot be established, artifact risk remains.

## 5.3.4 Dependency Inventory

Generate capability-scoped inventory including versions, source locators, hashes where available, and execution/build roles.

## 5.3.5 Install-Time Execution

Install/build hooks receive special scrutiny because they execute before normal runtime controls may apply.

## 5.3.6 Binary/Native Components

Opaque binaries and native extensions increase trust burden. They may require stronger isolation, provenance, signature/hash verification, or rejection under policy.

## 5.3.7 Vulnerability Intelligence

Known vulnerability signals can influence gating, but absence of known CVEs is not proof of safety.

## 5.3.8 Upstream Identity Drift

Ownership transfer, package takeover, signing-key change, dependency replacement, or release-process changes should later trigger differential revalidation.

## 5.3.9 Supply Chain Record

```text
component identity
revision/version/digest
source-artifact mapping
dependencies
install/build execution
network/download behavior
native/binary surface
known vulnerability signals
provenance uncertainty
required isolation
```

## Invariants

1. Unknown external code is zero-trust.
2. Immutable identities are preferred for proof.
3. Source review does not automatically validate published artifacts.
4. Transitive dependencies are part of the trust surface.
5. Install/build behavior is security-sensitive.
6. No-known-vulnerability is not proof of safety.
7. Upstream identity/process drift triggers revalidation.

## Exit Criteria

The Proving Lab receives an immutable, inventoried candidate and knows which supply-chain risks must be contained or tested before execution.
