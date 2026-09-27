# G7 Sensitivity Matrix

| Case | Dimension | Perturbation | Expected RELATION | Verdict |
|---|
|---|---|---|---|---|
| G7-EQ-01 | EVIDENCE QUALITY | WEAK -> STRONG | MONOTONE_NON_WEAKENING: stronger evidence must not weaken empirical support | PASS |
| G7-EQ-02 | EVIDENCE QUALITY | WEAK (1 lineage) x50 | INVARIANT: correlated copies never manufacture distinct source lineages | PASS |
| G7-IN-01 | INDEPENDENCE | LOW -> HIGH | MONOTONE_NON_WEAKENING: more genuine independence must not reduce observed distinctness | PASS |
| G7-IN-02 | INDEPENDENCE | UNKNOWN | UNKNOWN NEVER FAVORABLE: unknown provenance counts as zero distinct lineages, never favorable | PASS |
| G7-PE-01 | PERSISTENCE | ONE_SHOT -> REPEATED | ONE_SHOT != CHRONIC: one-shot anomaly must not escalate; repeated credible contradiction may | PASS |
| G7-PE-02 | PERSISTENCE | REPEATED -> CHRONIC | INVARIANT: raw extra repetition without new quality does not deepen transformation | PASS |
| G7-RV-01 | REVERSIBILITY | HIGH -> LOW | LOWER REVERSIBILITY NEVER EASIER: actual irreversibility must hold even under a safe grant | PASS |
| G7-RV-02 | REVERSIBILITY | LOW (grant says safe) | INVARIANT: grant reversibility metadata never reverses an actually-irreversible action | PASS |
| G7-CE-01 | DEPENDENCY CENTRALITY | LEAF -> CORE | RIGOR RAISED: higher centrality raises the bar; MEDIUM contradiction no longer opens review at core | PASS |
| G7-CE-02 | DEPENDENCY CENTRALITY | CORE + STRONG | NO PERMANENT IMMUNITY: strong persistent contradiction opens review even at core | PASS |
| G7-OA-01 | OPERATOR AVAILABILITY | AVAILABLE -> UNAVAILABLE | AVAILABILITY CHANGES ACTION AUTHORITY ONLY: empirical evidence state is invariant | PASS |
| G7-ES-01 | ENVIRONMENT SHIFT | NONE -> CONFIRMED | PROVENANCE INVARIANT, EVIDENCE NEVER BYPASSED: shift may change interpretation but never erases provenance or routes by raw keywords | PASS |
