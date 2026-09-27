# G5 — CEREBUS DOCTRINE AUDIT (S16)

## Manual source (read-only, authoritative)
- Source artifact: `CEREBUS_v4_Manual_EXTRACTED.txt` (repo-extracted CEREBUS v4 material). SHA-256 fingerprint recorded at read time; manual file untouched (`manual_modified=false` in the run receipt).
- Claim fixture: `CEREBUS_V4_P90_TARGET_METRICS` — exact machine-representable claim with its numeric thresholds (P90 target metrics), captured unparaphrased in `DoctrineClaimRecord`:
  - claim_id, doctrine=CEREBUS, manual version, source path/document, locator, source fingerprint, exact claim representation, numeric parameters, structural conditions, authority_class=CEREBUS_MANUAL, current_status.
- No material conflict observed between the repo-extract and itself; no fabrication from memory — the fitted numbers come from the extracted text.

## Separation of objects
- `DoctrineClaimRecord` (what the doctrine IS) and `ReproductionRecord` (what the evidence SAYS) are distinct objects; a contradiction is a relation between two preserved objects, never a rewrite of either.
- Frozen-before-result rule: each reproduction protocol (dataset lineage, implementation version, exact conditions, PIT status, sample size, metrics, protocol fingerprint) is frozen before result evaluation.

## Results
- Clean, repeated contradiction under governed conditions → `DoctrineContradictionRecord` + `CONTRADICTION_OPEN`. Manual remains canonical; no silent rewrite; generic quant convention cannot override CEREBUS (tested).
- Flawed reproduction (explicit timing-leak / boundary deviation) → `REPRODUCTION_REJECTED`; manual preserved.
- `AmendmentProposal`: original claim + contradicting evidence + scope + explanations + reproduction confidence + AffectedSurface + dependent strategies + requested amendment + rollback implications + **operator requirement**. Only governed doctrine-amendment authority may ratify; operator preference alone cannot fabricate a contradiction (tested).

## Authority vs evidence
Manual authority determines what current CEREBUS doctrine IS; evidence determines whether that doctrine is empirically challenged. Authority cannot fabricate evidence; evidence cannot silently change authority.

## Status
**PASS** — doctrine preserved, contradiction explicit, amendment path gated on governed authority.