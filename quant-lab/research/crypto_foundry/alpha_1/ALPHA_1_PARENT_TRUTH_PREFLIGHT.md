# CRYPTO-ALPHA-1 — PARENT TRUTH PREFLIGHT

## Parent checkpoint

- **Checkpoint:** CRYPTO-MECH-2-STATE-AND-DISLOCATION-TAXONOMY
- **Commit:** 1e0265c684ef457f6ead0e6bc84d4eb2147eaa11
- **Decision:** PASS_STATE_TAXONOMY
- **Parent decision verified:** YES (MECH_2_DECISION.json reads PASS_STATE_TAXONOMY)

## Required parent artifacts — all present

| Artifact | Present | Notes |
|---|---|---|
| MECH_2_DECISION.json | ✅ | PASS_STATE_TAXONOMY, n_promoted=25, n_falsified=55 |
| MECH_2_STATE_REGISTRY.csv | ✅ | 107 states |
| MECH_2_PROMOTION_REGISTRY.csv | ✅ | 25 PROMOTE_TO_ALPHA, 55 FALSIFIED, 22 SPARSE, 4 RESEARCH_ONLY, 1 REDUNDANT |
| MECH_2_STATE_DEFINITIONS.json | ✅ | hash=171673b82a724964... |
| MECH_2_EXTENSION_MANIFEST.json | ✅ | 3 files, matching sha256 |
| MECH_2_REPORT.md | ✅ | |

## Clerical inconsistency repair #1 — Base WETH/USDC 30d count

- **Report claim:** "Base WETH/USDC 150,978 swaps"
- **MECH_2_EXTENSION_MANIFEST.json:** 150,195 records
- **Actual dataset (base_weth_usdc_swap_30d.json):** 150,195 records
- **Root cause:** 150,978 was the raw eth_getLogs count in the collection log; the decoded record count is 150,195. The report used the raw count by mistake.
- **CANONICAL:** **150,195 decoded swap records**
- **Action:** This preflight document records the correction. The manifest and dataset agree; the report figure was a transcription error from the collection log. No data file is modified.

## Clerical inconsistency repair #2 — State ledger count

- **DECISION.json evidence.state_ledger_rows:** 6,802
- **Actual MECH_2_STATE_LEDGER.csv rows:** 6,802 (6,801 data rows + 1 header)
- **Report language:** "~6,803" used in summary narrative
- **Root cause:** Approximate language in narrative prose; the CSV and decision JSON agree at 6,802.
- **CANONICAL:** **6,802 labeled hourly rows**
- **Action:** This preflight records the exact figure. The "~6,803" in report prose was an approx; no data file is modified. The decision JSON's 6,802 is authoritative.

## State definitions integrity

- MECH_2_STATE_DEFINITIONS.json hash: `171673b82a724964`
- Thresholds frozen BEFORE MECH-2 transition/path results were inspected (per preregistration)
- No threshold modification occurred during ALPHA-1 parent verification

## Other parent checks

- MECH-1 parent (9c02b1dd) → MECH-2 (1e0265c6) chain intact
- DATA-1 freeze hashes verified at MECH-2 checkpoint
- All 137 tests pass (53 DATA-1 + 30 MECH-1 + 54 MECH-2)
- No MECH-2 artifacts modified during preflight

## Preflight verdict

**PARENT TRUTH RECONCILED.** Two clerical inconsistencies (Base 30d count, ledger approx) are recorded and corrected in this document. No scientific evidence is contradicted. State definitions hash matches. All promoted statuses are intact. ALPHA-1 may proceed.