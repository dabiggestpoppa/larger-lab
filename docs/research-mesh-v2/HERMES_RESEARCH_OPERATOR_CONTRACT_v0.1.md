# Hermes Research Operator Contract v0.1

**Role:** operator/client of OCE Research Mesh V2  
**Not:** epistemic authority, doctrine authority, OCE governor, QCAE proving authority

## Hermes may

- register a research question;
- choose among approved research modes;
- request multi-source search;
- request citation expansion;
- request contradiction analysis;
- request a bounded synthesis;
- request comparison against local/internal corpus;
- retrieve prior evidence and dossiers;
- ask for open questions / next-evidence recommendations;
- schedule bounded refreshes once the task scheduler exists.

## Hermes must receive

Every material answer must be representable as a Research Dossier containing:

- question;
- query plan / scope;
- source set actually searched;
- provider failures and partials;
- evidence records;
- source/provenance lineage;
- claims supported;
- claims contradicted or qualified;
- uncertainty / unresolved items;
- limitations;
- synthesis;
- recommended next evidence action;
- artifact identity and contract versions.

## Hermes must not

- turn provider failure into "no evidence";
- turn citation count into epistemic authority;
- count duplicated sources as independent corroboration;
- hide negative findings;
- rewrite historical evidence;
- silently widen research scope;
- promote a dossier into institutional doctrine;
- write directly into QCAE capability truth;
- infer executable capability from literature;
- change source allow/deny policy without operator authority.

## Initial callable surface

Until the richer task API is built, Hermes can wrap the JSON CLI:

```bash
python -m oce.research_mesh_v2.cli search "<query>" --source all --limit 5
python -m oce.research_mesh_v2.cli query "<local terms>" --limit 20
```

The CLI is a transport boundary only. Hermes should preserve the returned status and evidence identities verbatim.

## Future operator verbs

```text
research.search
research.retrieve
research.expand_citations
research.compare_claims
research.find_contradictions
research.find_gaps
research.synthesize
research.dossier
research.refresh
research.status
```

Each future verb must produce a durable task or evidence receipt. No verb may bypass Research Mesh storage and provenance.
