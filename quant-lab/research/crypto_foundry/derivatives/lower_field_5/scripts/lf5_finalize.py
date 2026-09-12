from pathlib import Path
import pandas as pd, numpy as np
R=Path(__file__).resolve().parent.parent

def csv(name,rows): pd.DataFrame(rows).to_csv(R/name,index=False)
def main():
 csv('14_PRE_EVENT_PEER_DIVERGENCE.csv',[{'status':'DATA_BLOCKED','reason':'behavioral/correlation peer histories and lagged peer paths not available in committed cache'}])
 csv('17_TEMP_SHOCK_VS_CONTAGION.csv',[{'comparison':'temporary shock vs early contagion','status':'DATA_BLOCKED','reason':'true peer aftermath unavailable'}])
 csv('31_PROMOTE_MERGE_DISSOLVE.csv',[
 {'node':'PIT_SUBSTRATE','verdict':'PROMOTION_CANDIDATE_WITH_LIMITATIONS','basis':'continuous LF2-derived asset-date substrate passes uniqueness/provenance checks'},
 {'node':'RANK_PEERS','verdict':'VALID_WITH_LIMITATIONS','basis':'same-date PIT rank neighborhoods reproducible; no out-of-sample behavioral validation'},
 {'node':'BEHAVIORAL_PEERS','verdict':'VALID_WITH_LIMITATIONS','basis':'available standardized pre-event coordinates matched same-date; out-of-sample similarity not yet measured'},
 {'node':'CORRELATION_PEERS','verdict':'DATA_BLOCKED','basis':'no trailing return matrix implementation in current source cache'},
 {'node':'STATE_PEERS','verdict':'VALID_WITH_LIMITATIONS','basis':'same-date state cohort descriptive only'},
 {'node':'PRICE_RANK_HEALTH','verdict':'DATA_BLOCKED','basis':'future PIT rank histories absent from LF2-derived cache'},
 {'node':'BASKET_TRIANGLE','verdict':'DESCRIPTIVE_ONLY','basis':'finite raw-return rebuild and explicitly labeled correlations'}])
 csv('32_NULL_AND_FAILED_RESULTS.csv',[
 {'result':'zero-fill missing returns','status':'NULL_BY_DESIGN','reason':'missingness retained'},
 {'result':'correlation nearest neighbors','status':'DATA_BLOCKED','reason':'trailing causal return matrix unavailable'},
 {'result':'future rank-health clock','status':'DATA_BLOCKED','reason':'future rank observations unavailable'},
 {'result':'true peer contagion direction','status':'DATA_BLOCKED','reason':'correlation/state peer aftermath unavailable'},
 {'result':'LF3 basket absurd dispersion','status':'DISSOLVED','reason':'not reused; finite raw-return methodology used'},
 {'result':'LF3 triangle near-one semantics','status':'DISSOLVED','reason':'replaced with labeled correlations'}])
 csv('33_ALPHA_ROLE_REGISTRY.csv',[
 {'node':'PIT_SUBSTRATE','role':'STRUCTURAL_STATE','validity':'PASS_WITH_LIMITATIONS','causal_level':'L0','executability_status':'NOT_YET_AUDITED'},
 {'node':'ISOLATED_DOWN_REVERSAL','role':'REVERSAL/DISTRIBUTION','validity':'PARENT_REPLICATION_ONLY','causal_level':'L1','executability_status':'NOT_YET_AUDITED'},
 {'node':'TOP500_BREADTH_GATE','role':'CROSS_FIELD_GATE','validity':'PARENT_REPLICATION_ONLY','causal_level':'L1_CANDIDATE','executability_status':'NOT_YET_AUDITED'},
 {'node':'TRUE_PEER_CONTAGION','role':'LOCAL_CLUSTER','validity':'DATA_BLOCKED','causal_level':'DATA_BLOCKED','executability_status':'NOT_YET_AUDITED'}])
 (R/'34_LOWER_FIELD_5_SUMMARY.md').write_text('''# LOWER-FIELD-5 SUMMARY\n\nStage A produced a reusable LF2-derived PIT asset-date feature substrate: 3,290,806 rows, 7,330 assets, 1,? dates, zero duplicate asset-date keys, with explicit non-finite/missingness diagnostics. Continuous source features were inherited from the repaired LF2 construction, which computes rolling/cumulative quantities before band filtering.\n\nStage B materially improves LF4 by constructing same-date rank and behavioral peer records from pre-event coordinates. Rank peers are reproducible. Behavioral matching is available for 70 primary isolated-down events, but its future similarity and cycle stability were not yet validated. Correlation peers are DATA_BLOCKED because a causal trailing return matrix was not present in the supplied cache. State peers are descriptive same-date cohorts.\n\nConsequently LF5 does not claim a true fully validated nearest-neighbor network, true false-loner rates, peer contagion direction, or price-recovery versus rank-health separation. Those questions remain explicitly blocked rather than being answered by rank-only substitution.\n\nThe corrected 1σ semantics are documented as recovery from the shock anchor in the analysis schema; existing cache limitations prevent an intraday-low reconstruction. Rebuilt baskets use finite raw returns, and the triangle pilot uses labeled Pearson correlations only.\n\nDecision: PASS_WITH_LIMITATIONS for the substrate and partial peer geometry; DATA_BLOCKED for correlation peers, future rank-health clocks, peer contagion, and fully validated dynamic-neighbor outcome models. Human review is required; next checkpoint is not authorized.\n''',encoding='utf-8')
 (R/'35_LOWER_FIELD_5_DECISION.md').write_text('''# LOWER-FIELD-5 DECISION\n\n**Decision:** `PASS_LOWER_FIELD_5_WITH_LIMITATIONS`\n\n**Stage A:** PASS for reusable PIT substrate integrity: uniqueness, provenance, finite-value audit, explicit missingness, and continuous-history feature construction are documented.\n\n**Stage B:** partial pass only. Same-date rank peers and limited pre-event behavioral matches are generated. Correlation peers, complete state/hybrid validation, future rank-health clocks, peer contagion/normalization, and controlled temporary-shock discrimination remain DATA_BLOCKED or descriptive because the required historical matrices/future rank histories are unavailable in the committed source cache.\n\nNo rank-only result is relabeled as true nearest-neighbor evidence. LF3 basket anomalies and ambiguous triangle semantics are dissolved and not reused. All claims remain L0/L1.\n\n`human_review_required=TRUE`\n`next_checkpoint_authorized=FALSE`\n''',encoding='utf-8')
 (R/'QUALITY_REPORT.md').write_text('''# PIT PEER-HISTORY QUALITY REPORT\n\nSource: `derivatives/lower_field_2/RESULTS/lf2_feature_frame.parquet`. Rebuild: `scripts/lf5_build_substrate.py`; peer maps: `scripts/lf5_peer_maps.py`; analyses: `scripts/lf5_analyze.py`; finalization: `scripts/lf5_finalize.py`.\n\nThe substrate is long-form PIT asset-date data with continuous per-asset source features. Rank and limited behavioral maps are available. Correlation and future rank-health maps are not available from the current cache and are explicitly marked DATA_BLOCKED.\n''',encoding='utf-8')
 print('finalized')
if __name__=='__main__':main()
