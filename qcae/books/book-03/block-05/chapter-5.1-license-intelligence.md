# Chapter 5.1 — License Intelligence

## Mission

Determine what legal/licensing evidence exists for every source, artifact, dependency, dataset, model, test fixture, and extracted component QCAE proposes to acquire.

QCAE performs evidence collection and policy classification. It does not impersonate legal counsel.

## 5.1.1 License Evidence Sources

Inspect, where applicable:

- repository license files;
- package metadata;
- source-file headers;
- NOTICE/COPYING files;
- dependency manifests/lockfiles;
- dataset/model terms;
- documentation terms;
- submodule/vendor directories;
- generated artifacts;
- upstream project links.

## 5.1.2 License Identity

Record normalized license identifiers when confidently supported, while preserving original text/reference and revision.

Unknown/custom/ambiguous terms remain `UNKNOWN_OR_CUSTOM`, never guessed into a familiar license.

## 5.1.3 Scope

License evidence is component-scoped. A repository-level license does not automatically prove that every vendored file, dataset, model, asset, or submodule has identical terms.

## 5.1.4 Provenance

For each relevant asset capture:

```text
asset identity
source revision/artifact digest
license claim
license evidence path/reference
copyright/notice obligations
redistribution/modification conditions
unknowns
```

## 5.1.5 Extraction Implications

MEU extraction must carry licensing provenance for included source and tests. Removing framework code does not erase obligations attached to extracted code.

## 5.1.6 Reimplementation Distinction

QCAE must distinguish:

- copying/modifying implementation;
- clean reimplementation from normative specification;
- reimplementation informed by paper;
- behavioral compatibility testing.

These have different provenance/legal considerations and must not be collapsed.

## 5.1.7 Dataset/Model Terms

Code license and data/model license may differ. Quant/research assets require separate term tracking.

## 5.1.8 Uncertainty

Ambiguous ownership, missing terms, conflicting metadata, or unclear redistribution conditions are hard uncertainty signals and may block acquisition pending review.

## Invariants

1. License is asset-scoped, not blindly repository-scoped.
2. Unknown terms remain unknown.
3. License evidence is revision/provenance linked.
4. Extracted components retain obligations.
5. Code/data/model/test licensing can differ.
6. QCAE classifies evidence; final legal authority remains outside model inference.

## Exit Criteria

Every acquisition path has a license evidence package sufficient for compatibility policy or human/legal escalation.
