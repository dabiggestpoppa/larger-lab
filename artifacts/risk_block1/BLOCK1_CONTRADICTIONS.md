# BLOCK-I CONTRADICTIONS (seal-time reconciliation)

| contradiction | classification | resolution |
|---|---|---|
| R3_TIME_TO_PROFIT share_of_winners > 1.0 | RESOLVED_BY_LATER_REPAIR | R3.1 (commit 31fa1df1) split N_reached_all / winners / losers with own-population denominators; report/decision regenerated; unaffected artifacts byte-identical. |
| R3 report/decision Q12 ex-best-5% expectancy read NaN (wrong row selected) | RESOLVED_BY_LATER_REPAIR | fixed in R3 build (row selection on the non-null exclusion value); sealed artifacts use the corrected +0.20R. |
| R4 auto-zones collapsed (RM-S2/S3/S4 all = 5.0%) | NON-MATERIAL | mathematically valid under the auto-constraints; operationally unusable -> this seal REFRAMES profiles as non-overlapping bands from measured DD breakpoints (see BLOCK1_RM_PROFILE_LIBRARY.md). Frontier results unchanged. |
| R4 worst_cluster_pct returned 0.0 (max(-inf, ...) init bug) | RESOLVED_BY_LATER_REPAIR | fixed within R4 (min tracking); sealed ladder has worst-cluster = -6.0% at f=1%. |
| R4 worst_seq_pct semantics (absolute dip vs relative DD) | RESOLVED_BY_LATER_REPAIR | fixed within R4 to peak-to-trough relative DD; sequential max DD 10.0% at f=1% vs hourly 10.2%. |

No UNRESOLVED material contradictions. Seal proceeds.
