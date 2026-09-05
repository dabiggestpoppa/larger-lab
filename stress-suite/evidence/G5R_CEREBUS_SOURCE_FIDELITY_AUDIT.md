# G5R CEREBUS SOURCE FIDELITY AUDIT — S16 source binding + exact claim atoms

Scope: G5R-04 (source binding must be actually source-bound), G5R-05 (exact claim must be
exact), and the §26 manual source fidelity audit. **The manual file was NOT modified.**

## 1. Exact source path

`quant-lab/reports/CEREBUS_v4_Manual_EXTRACTED.txt` (repository text extract of the
CEREBUS FX v4 manual; internal labels: "Cerebus Cycle — Final Form",
"Constraint-System Framework | CEREBUS FX v4.0 | April 2026", PART 1 dated March 2026).

## 2. Actual source digest (recomputed from the file during the tests — never trusted from the fixture)

| Field | Value |
|---|---|
| Hash algorithm | SHA-256 (exactly 64 hex chars required; enforced by `validate_sha256_digest`) |
| Content digest | `72ba79d7064404b463dfcf7d937a3a4c03565f6bad12f0ffa4fb8f6d5f011233` |
| Content length | 366,841 bytes |
| `source_blob_sha` | identical to `content_digest` (whole-file binding) |

**Pre-G5R defect:** the fixture stored `72ba79d7064404b463dfcf7d937a3a4c` (32 hex chars)
while the audit called it SHA-256. A truncated digest cannot be a SHA-256 digest. The
fixture now stores the full recomputed digest, and `run_s16` recomputes from the actual
file: wrong length → `UNBOUND`/`ValueError` (fail closed); wrong content → `STALE_DIGEST`
(claim not source-bound; `test_stale_manual_digest_rejected`).

## 3. Exact bounded claim atoms (G5R-05)

**Pre-G5R defect:** `exact_claim_representation` was a synthesized composite sentence
combining the Target Metric table WITH the pre-session checklist / news filter / day-of-week
conditions — separate sections fused into one alleged "exact" quote.

**Replacement representation (DoctrineClaimAtom, one bounded fragment per locator):**

- **TARGET_METRIC atom** (locator `Target Metric table (PAGE 4-5)`) — bounded fragment of
  the actual table on PAGE 5 of the extract:
  - `Win Rate (Filtered) 85% – 90%`
  - `Daily Goal 1.0% – 1.5%`
  - `Max Daily Drawdown < 0.50%`
  - `Prop Firm Circuit Breaker: hard constraint boundary at 0.40% loss`
  The machine fragment is the JSON of the claim's `numeric_parameters`
  (`win_rate_band [0.85, 0.90]`, `daily_goal_band [0.010, 0.015]`, `max_daily_drawdown 0.005`,
  `circuit_breaker 0.004`, `p90_thresholds_by_window`, `session_window`, `tier_constraints`),
  digest-recorded per atom.
- **APPLICABILITY atoms** (separately bound, never merged into the target-metric quote):
  - pre-session conditions: Asian range measured `00:00 – 08:00 UTC`, pre-session checklist
    daily @ 1:45 AM EST, news filter (no high-impact within 4 hours), day-of-week sizing;
  - tier sizing: `<20 pips → TIER 1 100%`, `20–30 → TIER 2 75%`, `30–45 → TIER 3 50%`,
    `>45 → NO-GO 0%`;
  - P90 activation thresholds: M5 close in `2:00–11:00 AM EST` with per-window pips
    thresholds (2–4 AM ≥ 4.1; 4–6 AM ≥ 4.6; 6–8 AM ≥ 4.6; 8–10 AM ≥ 5.9; 10–11 AM ≥ 6.2).

Every atom carries `fragment_digest` (SHA-256 of the verbatim fragment), `source_path`,
`locator`, `claim_kind` and `manual_version`. Section boundaries are preserved; the G5
composite overreach is gone (`test_exact_claim_atoms_preserve_section_boundaries` asserts
`"Conditions:"` no longer appears inside the exact representation and that applicability
atoms exist separately).

## 4. Canonical PDF caveat (honest boundary — AMB-G5R-01)

No canonical CEREBUS v4 PDF exists in this repository, so **no byte-identity claim between
the extract and a canonical PDF is made**. What IS verified:

1. the extract's own PAGE-5 Target Metric table and PAGE-5/6 checklist/tier/P90 content
   were read directly from the file and match the claim atoms above (line-verified);
2. the whole-file SHA-256 binding is recomputed on every S16 run;
3. the file's bytes are unchanged across the run (`test_source_file_unchanged`) and across
   the whole G5R effort (digest above matches the pre-G5R file).

**If a canonical PDF is later introduced and materially conflicts with this extract, S16
must be re-blocked and re-audited.** Recorded as AMB-G5R-01 in the receipt.

## 5. Proof the source file is unchanged

- `test_source_file_unchanged`: reads bytes → recomputes binding → reads bytes again →
  byte-identical; digest equals `72ba79d7...11233`.
- `test_ratification_does_not_rewrite_source_file`: governed OPERATOR ratification leaves
  the manual bytes identical.
- Runner-level: `manual_modified=false`, `manual_claim_rewritten=false` on every S16 run.

## 6. Result

`S16 MANUAL SOURCE BINDING: PASS — SHA-256, recomputed from the actual file, 64 hex, full-file binding; claim atoms preserve section boundaries; source file unchanged.`
