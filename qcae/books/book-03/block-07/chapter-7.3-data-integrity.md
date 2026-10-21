# Chapter 7.3 — Data Integrity

## Mission

Prove that the dataset and transformations used for financial validation represent the intended market information without hidden leakage, survivorship distortion, timestamp errors, or silent cleaning choices.

## 7.3.1 Data Provenance

Capture:

```text
provider/source
instrument/universe
raw coverage
frequency
timezone/timestamp convention
adjustment method
corporate actions where applicable
roll method where applicable
missing-data policy
revision/version/hash
license/use restrictions
```

## 7.3.2 Time Integrity

Validate:

- UTC/local conversions;
- DST transitions;
- session boundaries;
- bar labels/open-close semantics;
- publication/release time;
- revised data;
- ordering/duplicates.

## 7.3.3 Leakage Checks

Explicitly test for:

- look-ahead;
- future extrema;
- centered transforms;
- future-filled missing data;
- full-sample normalization/clustering where inappropriate;
- target leakage;
- post-event universe selection.

## 7.3.4 Survivorship/Universe

Equity/index/universe research must distinguish historical membership/availability from today's surviving set when relevant.

## 7.3.5 Data Cleaning

Cleaning rules are part of the strategy experiment. Outlier removal, interpolation, bad-tick filtering, session removal, and winsorization are recorded and tested for sensitivity.

## 7.3.6 Cross-Source Validation

For material results, compare key samples/features against an independent source when feasible, especially around suspicious outliers or event windows.

## 7.3.7 CEREBUS Session Semantics

CEREBUS-defined windows and structural measurements must use the exact intended timezone/session convention from the authoritative manual/configuration. Ambiguous session mapping blocks final validation until resolved.

## Invariants

1. Data is versioned/provenance-linked.
2. Timestamp semantics are explicit.
3. Leakage checks are mandatory.
4. Cleaning is an experimental choice, not invisible preprocessing.
5. Universe construction is point-in-time when required.
6. CEREBUS windows preserve authoritative session semantics.
7. Data-license constraints survive into reproducibility packages.

## Exit Criteria

QCAE can state why the dataset is fit—or not fit—for the exact signal and period being tested.
