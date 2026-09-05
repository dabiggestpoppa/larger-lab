# ================================================================ 41 old node reconnection
def old_node_reconnection():
    rows = []
    def add(node, prior_role, connection, changed):
        rows.append(dict(old_node=node, prior_role=prior_role,
                         mech20_connection=connection[:200], placement_changed=changed))
    # old promoted/local nodes, re-examined for NEW explanatory connections only
    add("POTENTIAL_REALIZATION", "ADAPTIVE_LAW",
        "M20 17-20: realization = constraint network with equifinality; THRESHOLD x TRANSFER 2x2 repaired; MI-based complementarity replaces M19 inconsistent SUBSTITUTABLE language", "yes")
    add("EQUIFINALITY", "ADAPTIVE_LAW",
        "M20 20: initiation equifinality (MECH-14) now mirrored downstream: realization shows multiple constraint patterns (realization equifinality)", "yes")
    add("BRANCH_CLOSURE", "ADAPTIVE_LAW",
        "M20 17: route deformation / exit pressure remain weakly coupled to gain; branch closure is a downstream expression of transfer+threshold, not an independent law", "yes")
    add("RANK_RECRUITMENT", "ADAPTIVE_LAW",
        "M20 08: not a differentiator in matched sat-with/without-delivery; remains rank7 coordinate, not a response-law node", "no")
    add("PHYSICAL_VS_SIGMA", "RESEARCH_ONLY",
        "M20 25-27: threshold inversion materiality audit reframes 'deep early activation' as composition-artifact-prone; physical/sigma question absorbed into materiality gate", "yes")
    add("STATE_TOPOLOGY", "STRUCTURAL_CORE",
        "Frozen; M20 uses states only as conditioning strata (08 matching, 14 2x2, 29 hysteresis) - no structural change", "no")
    add("SPATIAL_ACTIVATION", "STRUCTURAL_CORE",
        "M20 30-31: spatial character (broad vs rank-local) of forcing families reuses patch activation correlations - consistent with frozen topology", "no")
    add("SATURATION_LAW", "ADAPTIVE_LAW",
        "M20 03-07: gain + ceiling confirmed as the 2-coordinate saturation description; slope x ceiling surface defines response environments; saturation meaning is response-dependent", "yes")
    add("THRESHOLD_BAND", "ADAPTIVE_LAW",
        "M20 14-16: threshold position is the strongest single realization coordinate; complements transfer", "no")
    add("BIRTH_GEOMETRY", "ADAPTIVE_LAW",
        "M20 21-24: failure = load-vs-resolution mismatch; recovery path mapped (which variable normalizes first)", "yes")
    add("2022_STRUCTURAL_SCAR", "RESEARCH_ONLY",
        "M20 34-39: era hypotheses + changepoint agreement + surface-vs-law generalization tested; verdict finalizes 2022 interpretation", "yes")
    out = pd.DataFrame(rows)
    W("41_OLD_NODE_RECONNECTION.csv")(out)


# ================================================================ 42 promote park dissolve
def promote_park_dissolve():
    rows = []
    def add(obj, os_role, action, note):
        rows.append(dict(object=obj, os_role=os_role, action=action, note=note[:200]))
    add("RESPONSE_LAW_GAIN_CEILING", "ADAPTIVE_LAW", "FREEZE",
        "gain+ceiling = 2-coordinate response description (anti-coupled r=-0.85, together explain 96% of node motion); unclamped fit only; see 02")
    add("RESPONSE_GAIN_STATE", "ADAPTIVE_LAW", "PROMOTE",
        "CONTINUOUS_GAIN_COORDINATE: autocorr 0.99 (lag1)/0.66 (lag30), near-absorbing tercile states; era-adaptive; see 04")
    add("CEILING_ROLE", "ADAPTIVE_LAW", "LOCAL",
        "regime-local scaling (H4): ceiling varies by era (0.67 pre -> 0.93 2022 -> 1.01 2025-26), anti-coupled with gain, NOT enabler/absorber; see 05")
    add("SLOPE_X_CEILING_SURFACE", "ADAPTIVE_LAW", "PROMOTE",
        "distinct environments: HI_GAIN_LO_CEIL delivers 0.40 vs LO_GAIN_HI_CEIL 0.31; see 06")
    add("SATURATION_WITHOUT_DELIVERY", "LOCAL_PHYSICS", "PROMOTE",
        "matched (state/gain/ceiling/demand/sat): impaired transfer (-0.08,p<0.05) + lower concentration-release (-0.66) + higher volatility forcing (+0.38), NOT exit structure; see 08")
    add("SATURATION_FAILURE_TRANSITIONS", "LOCAL_PHYSICS", "PARK",
        "sterile saturation resolves fast (decays 1-3d; state change 82% @14d; realization 51% @30d); no new mechanism beyond 08; see 09")
    add("SATURATION_TO_DELIVERY", "LOCAL_PHYSICS", "LOCAL",
        "first-changed variable: threshold 31% / forcing 30% / exit-pressure 27%; transfer rarely first (3%); see 10")
    add("CAPACITY_ROLE", "ADAPTIVE_LAW", "LOCAL",
        "ABSORPTIVE_CAPACITY: delivery falls monotonically with capacity in every load band (HIGH_LOAD Q1 0.81 -> Q4 0.45); state-structural attribute; see 11-12")
    add("THRESHOLD_X_TRANSFER", "ADAPTIVE_LAW", "PROMOTE",
        "2x2 repaired: THR_HI_TE_HI 0.79 vs THR_LO_TE_LO 0.12; MI + interaction logit classify SUBSTITUTES with conditional complementarity at high transfer; see 14-15")
    add("REALIZATION_CORE", "ADAPTIVE_LAW", "PROMOTE",
        "single-coordinate core = TRANSFER (heldout AUC 0.83); threshold 0.72, capacity 0.69, gain 0.54; extra coords add nothing; see 16")
    add("REALIZATION_NETWORK", "ADAPTIVE_LAW", "PROMOTE",
        "descriptive graph: THRESHOLD~FORCING 0.92, CAPACITY suppresses THRESHOLD/TRANSFER (-0.46/-0.50), EXIT_PRESSURE~ROUTE_DEFORM 0.43; see 17-18")
    add("REALIZATION_MINIMAL_SETS", "ADAPTIVE_LAW", "PROMOTE",
        "DELIVERY: TRANSFER alone 0.73, +THRESHOLD 0.79, +GAIN 0.88; STALL: CAPACITY+NON_SATURATED 0.80; see 19")
    add("REALIZATION_EQUIFINALITY", "ADAPTIVE_LAW", "PROMOTE",
        "MULTIPLE_REALIZATION_PATHS: 62 distinct met-patterns, top <11%; realization equifinality mirrors M14 initiation equifinality; see 20")
    add("BIRTH_LOAD_RESOLUTION_MISMATCH", "ADAPTIVE_LAW", "PROMOTE",
        "at INITIATION aborted births: routes OPENING (+0.33) while load rises (+0.15) vs viable routes PRUNING (-0.80) with load falling; resolution_d 1.65; see 22")
    add("BIRTH_RECOVERY_PATH", "ADAPTIVE_LAW", "LOCAL",
        "first restoration: routes prune 38% / demand cools 35% / threshold normalizes 22%; transfer rarely first; see 24")
    add("THRESHOLD_INVERSION", "RESEARCH_ONLY", "DEMOTE",
        "materiality audit: activation gaps 0.001-0.03 (5.7% of patch sigma) during thr50 'inversions' -> COMPOSITION_ARTIFACT; mechanism analysis demoted (25-27)")
    add("DEEP_HYSTERESIS", "LOCAL_PHYSICS", "PARK",
        "final reconciliation: STATE_DOMINANT (state spread 0.040 > depth spread 0.009); 6C_2 strongest (0.12-0.16); depth gradient only inside 6C_0; no global object; see 28-29")
    add("FORCING_FUNCTIONAL_MAP", "ADAPTIVE_LAW", "PROMOTE",
        "functional dimensions without scalar collapse: VOLATILITY/STABLECOIN/RANK_RECRUITMENT = persistent background fields; PARTICIPATION/CONC_RELEASE/PHYSICAL = impulses; response fns: MOVE_CEILING/MOVE_SLOPE/MOVE_ONSET; see 30-32")
    add("FORCING_INTERACTIONS_DEEP", "ADAPTIVE_LAW", "LOCAL",
        "supported pairs alter threshold most (PARTICIPATIONxVOLATILITY -0.46, PARTICIPATIONxBTC -0.29); route pressure/transfer/gain mostly additive; see 33")
    add("2022_RESPONSE_GAIN_ERA", "RESEARCH_ONLY", "PROMOTE",
        "H3_MULTIPLE_REGIME_MODULATIONS: 21 monthly gain-regime transitions, 5 LOW runs, 7 HIGH runs; no single era break agreed (SEG finds 2021-12/2022-12/2024-12 collapses); see 34-38")
    add("SURFACE_VS_LAW_CLOCKS", "ADAPTIVE_LAW", "LOCAL",
        "PARTIAL_GENERALIZATION: surface precedes law in first 2 post-2022 excursions only; later excursions law decays at least as fast; 2022-anchored clock, see 39")
    add("RESPONSELAW_STATE", "ADAPTIVE_LAW", "PROPOSAL",
        "OS runtime object proposal (gain/ceiling/baseline_version/deviation/changepoint/recovery_status); see 40_RESPONSE_LAW_STATE_PROPOSAL.md")
    W("42_PROMOTE_PARK_DISSOLVE.csv")(pd.DataFrame(rows))


# ================================================================ 43 null and failed
def null_failed():
    rows = []
    for f in sorted(OUT.glob("*.csv")):
        try:
            d = pd.read_csv(f)
        except Exception:
            continue
        na = int(d.isna().sum().sum()); total = int(d.size)
        flags = []
        for val in ("DATA_LIMITED", "NO_EVENT_BLOCK_FOUND", "NULL", "DATA_BLOCKED",
                    "NO_STABLE", "ARTIFACT", "WEAK", "DEMOTED", "COMPOSITION_ARTIFACT",
                    "NO_CONVERSIONS", "NO_SUPPORTED_INTERACTIONS", "NONE", "DATA_BLOCKED(panel-aggregate)"):
            for c in d.columns:
                nv = int((d[c].astype(str) == val).sum())
                if nv:
                    flags.append(f"{val}:{nv}")
        rows.append(dict(file=f.name, n_rows=len(d), n_cells=total, null_cells=na,
                         null_frac=round(na / max(total, 1), 3),
                         failed_flags=";".join(sorted(set(flags))[:8])))
    W("43_NULL_AND_FAILED_RESULTS.csv")(pd.DataFrame(rows))


# ================================================================ RUNNER
if __name__ == "__main__":
    response_law_decomposition()
    saturation_response_coords()
    response_gain_state()
    ceiling_role()
    slope_ceiling_surface()
    saturation_position_by_response()
    saturation_failure_matched()
    saturation_failure_transitions()
    saturation_to_delivery()
    capacity_interpretation()
    capacity_response_law()
    threshold_transfer_2x2()
    threshold_transfer_interaction()
    realization_core()
    realization_relations()
    realization_constraint_network()
    realization_minimal_sets()
    realization_equifinality()
    birth_failure_deep()
    load_resolution_mismatch()
    birth_failure_surface()
    birth_recovery_path()
    threshold_inversion_materiality()
    threshold_inversion_post_audit()
    threshold_inversion_function()
    hysteresis_reconciliation()
    hysteresis_survival_map()
    forcing_functional_dimensions()
    forcing_functional_map()
    forcing_temporal_scales()
    forcing_interaction_deep()
    era_hypotheses()
    response_gain_changepoints()
    pre_transition_post_law()
    new_baseline_vs_scar()
    reexcursion_anatomy()
    surface_vs_law_generalization()
    old_node_reconnection()
    promote_park_dissolve()
    null_failed()
    print("MECH-20 BUILD COMPLETE")
