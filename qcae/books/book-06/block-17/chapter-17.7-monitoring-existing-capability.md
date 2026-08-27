# Chapter 17.7 — Monitoring Existing Capability

## Mission

Define how operators register, inspect, and tune ongoing monitoring for acquired capabilities without turning monitoring into automatic upgrading.

## Monitoring Registration

A monitored capability should identify:

```text
capability/integration ID
reviewed source/package/service revision
watch sources
material-change triggers
security/license triggers
revalidation policy
review cadence if required
owner
```

## Operator Views

Operators should be able to see:

- current reviewed revision;
- latest upstream revision;
- pending change findings;
- evidence freshness;
- open revalidation jobs;
- vulnerabilities/license changes;
- supersession candidates;
- current authorization/health state.

## Action Options

```text
ACKNOWLEDGE
REVALIDATE
DEFER_WITH_REASON
PIN_CURRENT
INVESTIGATE_ALTERNATIVE
RETIRE
```

## No Auto-Upgrade

Monitoring may discover and test newer versions, but protected integration changes require their normal acquisition/authority path.

## Invariants

1. Every monitored capability is anchored to its reviewed revision.
2. Change detection does not equal update approval.
3. Security/legal changes receive elevated priority.
4. Deferred review is reasoned and durable.
5. Operators can see evidence freshness and revalidation state.

## Exit Criteria

Operators can maintain capabilities over time without either ignoring drift or surrendering update control to automation.
