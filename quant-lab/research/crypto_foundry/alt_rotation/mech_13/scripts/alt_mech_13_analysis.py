from _m13base import *
from _m13base import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _entropy, _subperiod_split
from _m13p2 import *
from _m13p3 import *
from _m13p4 import *
from _m13p5 import *
from _m13p6 import *
from _m13p7 import *
from _m13p8 import *
from _m13p9 import *


def main():
    dfw = _cache_step("dfw", load_dfw)
    ev = _cache_step("ev", load_ev)
    health = _cache_step("health", load_health)
    band = _cache_step("bandpanel", load_band_panel)
    loners = _cache_step("loners", load_loners)
    consensus = _cache_step("lf6_consensus", load_lf6_consensus)
    peer_paths = _cache_step("lf6_peer_paths", load_lf6_peer_paths)
    print(f"[data13] dfw {dfw.shape} ev {ev.shape} health {health.shape} "
          f"band {band.shape} loners {loners.shape} "
          f"consensus {consensus.shape} peer_paths {peer_paths.shape}",
          flush=True)

    life = _cache_step("ws1", lambda: ws1_lifecycle_deep_map(dfw))
    mass, law = _cache_step("ws2", lambda: ws2_mass_migration(dfw))
    init = _cache_step("ws3", lambda: ws3_initiation_geometry(dfw))
    iaud = _cache_step("ws4", lambda: ws4_initiation_primitive_audit(dfw,
                                                                    init))
    ed = _cache_step("ws5", lambda: ws5_entropy_deep_map(dfw))
    eprim = _cache_step("ws6", lambda: ws6_entropy_primitive(dfw))
    eprop = _cache_step("ws7", lambda: ws7_entropy_propagation(band))
    spt = _cache_step("ws8", lambda: ws8_spatial_temporal_matrix(dfw, band))
    wsub = _cache_step("ws9", lambda: ws9_waterfall_subtypes(band, dfw))
    asurf = _cache_step("ws10", lambda: ws10_activation_surfaces(band, dfw))
    presp = _cache_step("ws11", lambda: ws11_patch_response_curves(dfw, band))
    rhet = _cache_step("ws12", lambda: ws12_response_heterogeneity(dfw,
                                                                  presp))
    meta = _cache_step("ws13", lambda: ws13_metastability_recheck(dfw))
    asg = _cache_step("ws14", lambda: ws14_abs_sigma_shock_geometry(ev))
    mat = _cache_step("ws15", lambda: ws15_shock_materiality(ev))
    dirl = _cache_step("ws16", lambda: ws16_directional_atlas(dfw))
    up = _cache_step("ws17u", lambda: ws17_upside_geometry(dfw))
    dn = _cache_step("ws17d", lambda: ws17_downside_geometry(dfw))
    dgain = _cache_step("ws18", lambda: ws18_directional_information_gain(dfw))
    conv = _cache_step("ws19", lambda: ws19_local_conversion_paths(dfw))

    results = {
        "lifecycle": life, "mass": mass, "mass_law": law,
        "initiation": init, "init_audit": iaud,
        "entropy_deep": ed, "entropy_primitive": eprim,
        "entropy_prop": eprop, "spat_temp": spt,
        "waterfall_subtypes": wsub, "activation_surfaces": asurf,
        "patch_resp": presp, "resp_het": rhet,
        "meta_recheck": meta, "abs_sigma": asg, "materiality": mat,
        "directional": dirl, "upside": up, "downside": dn,
        "dir_gain": dgain, "conv_paths": conv, "nodes": None,
    }
    fmap = ws20_field_map(results)
    results["field_map"] = fmap
    nodes = ws20_nodes(results)
    results["nodes"] = nodes
    ws20_nulls(results)
    vd = write_verdicts(results)
    write_summary(results)
    write_decision(results)
    print(f"[done13] MECH-13 pipeline complete. verdict={vd['verdict']}",
          flush=True)


if __name__ == "__main__":
    main()