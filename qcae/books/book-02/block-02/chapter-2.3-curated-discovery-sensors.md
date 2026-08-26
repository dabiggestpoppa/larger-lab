# Chapter 2.3 — Curated Discovery Sensors

## Mission

Curated lists, newsletters, awesome-lists, GitHubDaily-style collections, OSINT arsenals, expert bookmarks, and community registries are **discovery sensors**. They provide compressed human attention and useful taxonomy, but they are neither capability proof nor authority.

## 2.3.1 Sensor Role

Curated sources are valuable because they can reveal candidates QCAE would miss through literal search:

- niche terminology;
- emerging projects;
- domain-specific tools;
- alternative ecosystems;
- abandoned-but-useful prior art;
- category structures that improve query expansion.

## 2.3.2 Sensor vs Registry

QCAE should distinguish:

### Sensor
A stream/list that generates candidate leads.

### Registry prior art
A structured classification that can improve QCAE's own ontology/search taxonomy.

### Capability source
A linked project that independently enters normal candidate evaluation.

A single curated project may play all three roles, but those roles remain separate.

## 2.3.3 GitHubDaily Role

GitHubDaily is treated as a curated candidate generator and novelty sensor. Its inclusion of a repository increases discovery probability, not trust level.

QCAE should ingest where practical:

```text
source collection
category/tags
description
linked repository/resource
observed date
curation context
```

The linked repository then receives a canonical candidate identity and normal evidence process.

## 2.3.4 awesome-osint-arsenal Role

A broad OSINT arsenal is particularly useful for:

- capability-category discovery;
- registry/schema prior art;
- identifying specialized intelligence sources;
- learning alternate vocabulary;
- finding selective capabilities useful to research workflows.

QCAE should not import an entire arsenal as architecture merely because its taxonomy is broad.

## 2.3.5 Trust Firewall

Curation means someone found the item noteworthy. It does not establish:

- source integrity;
- license compatibility;
- maintenance quality;
- security;
- reproducibility;
- contract coverage.

Curator reputation may influence discovery priority only.

## 2.3.6 Multi-Sensor Corroboration

Appearing in multiple independent curated sources can increase investigation priority because it suggests ecosystem relevance. It still does not count as independent technical proof of capability.

## 2.3.7 Sensor Provenance

Preserve:

```text
sensor_id
sensor_revision/date
category path
curator-provided description
linked target
first_seen
last_seen
discovery plan/query that consumed it
```

This enables later evaluation of which sensors actually produce useful candidates.

## 2.3.8 Sensor Performance

QCAE should eventually measure sensors by:

- novel candidate yield;
- accepted capability yield;
- duplicate rate;
- false-positive rate;
- time-to-discovery advantage;
- domain coverage;
- maintenance/freshness.

This turns curated-source selection into an evidence-driven process.

## 2.3.9 Taxonomy Harvesting

Curated categories can expand QCAE vocabulary, but imported taxonomy terms should remain aliases/hypotheses until reconciled with the Capability Model.

External taxonomy must not overwrite canonical capability identity.

## 2.3.10 Poisoning/Manipulation Awareness

Public curated lists can contain promoted, compromised, misleading, or low-quality projects. Sensor ingestion must remain zero-trust and cannot bypass later security/proving gates.

## 2.3.11 Staleness

Curated sources can become stale even when their repositories remain online. QCAE should record observed source revision and avoid interpreting continued list presence as current maintenance evidence.

## 2.3.12 Sensor Adapter Contract

A generic adapter should emit normalized leads:

```text
sensor_id
lead_locator
lead_kind
category
raw_description
tags
observed_at
source_revision
confidence_as_discovery_lead
```

It should not emit `VERIFIED_CAPABILITY`.

## 2.3.13 Invariants

1. Curated sources generate leads, not truth.
2. Taxonomies are prior art, not canonical ontology.
3. Linked projects enter normal candidate evaluation.
4. Multi-list appearance does not equal technical corroboration.
5. Sensor effectiveness should eventually be measured.
6. Sensor provenance and revision are retained.
7. Public curation never bypasses zero-trust rules.

## Exit Criteria

QCAE can ingest GitHubDaily, awesome-style catalogs, and future curated sources through one conceptual sensor interface while preserving their useful human curation without allowing curation to become authority.
