# Chapter 5.6 — Data Exfiltration Controls

## Mission

Prevent candidate code or external services from transmitting Quant Lab data, source, evidence, prompts, credentials, market datasets, or derived proprietary information beyond approved boundaries.

## 5.6.1 Data Classes

```text
public
internal
confidential source
private research
market/vendor licensed data
credentials/secrets
production telemetry
OCE identity/policy data
```

## 5.6.2 Egress Default

No network egress for unknown code unless the proof plan requires and policy authorizes it.

## 5.6.3 Destination Allowlisting

When network is required, constrain destination, protocol, purpose, and data class. "Internet access" is not an acceptable generic privilege for proving.

## 5.6.4 External Comprehension Services

DeepWiki or any future hosted comprehension provider cannot receive private source merely because it improves analysis. Source egress requires explicit policy authority; local analysis is fallback.

## 5.6.5 Telemetry

Libraries may contain analytics/crash reporting/update checks. Identify and disable/contain them where possible. Unexpected telemetry attempts become evidence.

## 5.6.6 DNS/Indirect Egress

Policy should treat indirect network channels and subprocess-launched clients as egress too; network controls must apply at the sandbox boundary, not only application configuration.

## 5.6.7 Output Inspection

Evidence export from sandbox should be limited to declared outputs/logs/artifacts. Large/unexpected outputs can require quarantine/review.

## 5.6.8 Licensed Market Data

Quant proving must respect dataset redistribution/use restrictions. A candidate must not upload vendor data to remote services unless explicitly permitted.

## 5.6.9 Egress Manifest

```text
run_id
data classes available
allowed destinations
allowed protocols
purpose
observed connections
blocked attempts
exported artifacts
```

## Invariants

1. Unknown code has no arbitrary egress.
2. Data classification governs allowed movement.
3. Hosted analysis never implies permission to upload private source.
4. Telemetry/update behavior counts as egress.
5. Controls operate at sandbox boundary.
6. Licensed market data remains license-governed during proving.
7. Unexpected egress is evidence.

## Exit Criteria

QCAE can prove capabilities without turning evaluation into an uncontrolled data-export channel.
