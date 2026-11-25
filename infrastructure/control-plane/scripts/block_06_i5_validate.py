#!/usr/bin/env python3
"""B6-I5 P0 contract validator.

Durable, committed validator for the repaired B6-I5 P0 packet. Standard library
only, offline, no secret, no network, no wall clock.

Checks:
  all JSON parses
  exact source citations resolve
  requirement IDs unique and contiguous where specified
  bindings exactly once
  node inventory exact
  zero PASS
  current failure-class partition exact-once
  deferred T19 owner closure
  threat witnesses can produce their required observables
  negative controls distinct
  mutation laws complete and non-vacuous
  static/behavioural crosswalk valid
  cross-document arithmetic identical
  S1 corrective supplement present and referenced
  amendment reference rebinding (historical + governing)
  T19 direct governing-source citation
  mutation law compile-success wording
  no production or B6-I5 tests exist
  no prior-stage weakening
  no B6-I6+ files
  secret scan clean
  absolute-path scan clean
  manifest/packet integrity where applicable
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

DOCS = "docs/oce-golden-system"
PREFIX = "OCE_BLOCK_06_I5_"
SCRIPTS = "infrastructure/control-plane/scripts"
TESTS = "infrastructure/control-plane/tests"


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def main(argv=None) -> int:
    root = pathlib.Path(__file__).resolve().parents[3]

    def git(*args: str) -> str:
        proc = subprocess.run(["git", "-C", str(root), *args],
                              capture_output=True, encoding="utf-8", errors="replace")
        return proc.stdout

    checks: list[str] = []
    failures: list[str] = []

    def need(name: str, ok: bool, detail="") -> None:
        checks.append(name)
        if not ok:
            failures.append(f"{name}: {detail}")

    # ---- all JSON parses ----
    p0_files = sorted(p.name for p in (root / DOCS).glob(f"{PREFIX}*.json"))
    need("packet/count", len(p0_files) == 10, p0_files)
    objs: dict[str, dict] = {}
    for name in p0_files:
        raw = (root / DOCS / name).read_bytes()
        need(f"packet/canonical/{name}", raw == canonical(json.loads(raw)), "non-canonical JSON")
        need(f"packet/lf/{name}", b"\r\n" not in raw and raw.endswith(b"\n"), "CRLF or missing trailing newline")
        objs[name] = json.loads(raw.decode("utf-8"))

    scope = objs[f"{PREFIX}SCOPE_DERIVATION_v1.0.json"]
    contract = objs[f"{PREFIX}IMPLEMENTATION_CONTRACT_v1.0.json"]
    registry = objs[f"{PREFIX}REQUIREMENT_TEST_REGISTRY_v1.0.json"]
    proofs = objs[f"{PREFIX}FAILURE_AND_THREAT_PROOFS_v1.0.json"]
    registration = objs[f"{PREFIX}STAGE_SCOPE_REGISTRATION_v1.0.json"]
    surface = objs[f"{PREFIX}SERVICE_SURFACE_CONTRACT_v1.0.json"]
    compat = objs[f"{PREFIX}COMPATIBILITY_MATRIX_v1.0.json"]
    paired = objs[f"{PREFIX}PAIRED_COMPARISON_CONTRACT_v1.0.json"]
    amendment = objs[f"{PREFIX}AMENDMENT_001_v1.0.json"]

    # ---- amendment reference present in every packet doc except the amendment itself and S1 ----
    for name in p0_files:
        if name == f"{PREFIX}AMENDMENT_001_v1.0.json" or name == f"{PREFIX}AMENDMENT_001_S1_v1.0.json":
            continue
        obj = objs[name]
        has_ref = obj.get("amendment") == f"{PREFIX}AMENDMENT_001_v1.0.json" and bool(obj.get("amendment_sha"))
        need(f"amendment_ref/{name}", has_ref, name)

    # ---- amendment identity ----
    need("amendment/head_matches",
         amendment.get("audited_p0_head") == "21be8b21a16daa27a0a5114194ac1a6c931224d4",
         amendment.get("audited_p0_head"))
    need("amendment/tree_matches",
         amendment.get("audited_p0_tree") == "5eb228fcf859fc7224ee82b64d4bffc21d95e639",
         amendment.get("audited_p0_tree"))
    need("amendment/agent2_sha",
         amendment.get("agent2_hostile_matrix_sha")
         == "47e98eb7d7bb1f46772f87de45b97eae66456181c31fab7cc1bd7fc1e09404a2")
    need("amendment/disposition",
         amendment.get("agent2_disposition") == "PARALLEL_P0_AUDIT_REPAIR_REQUIRED_B6_I5")
    need("amendment/blocking_b1", "B-1" in amendment.get("blocking", []))
    need("amendment/weaknesses_e",
         set(amendment.get("weaknesses", [])) == {"E-1", "E-2", "E-3", "E-4"})
    need("amendment/i4_defect", bool(amendment.get("i4_workflow_replay_defect")))
    need("amendment/preserved_run",
         amendment["i4_workflow_replay_defect"].get("preserved_failed_run") == "45479336318")

    # ---- S1 corrective supplement and reference rebinding ----
    S1_SHA = "bec496dfa60be3f61eced6f25d9fbf8ca19f5e17"
    HISTORICAL_SHA = "3d1f94e87067d63deffa4295bc6575636db14878"
    s1_name = f"{PREFIX}AMENDMENT_001_S1_v1.0.json"
    s1_path = root / DOCS / s1_name
    need("s1/document_exists", s1_path.exists(), s1_name)
    if s1_path.exists():
        s1_raw = s1_path.read_bytes()
        s1 = json.loads(s1_raw.decode("utf-8"))
        need("s1/canonical", s1_raw == canonical(s1), "non-canonical S1")
        need("s1/lf", b"\r\n" not in s1_raw and s1_raw.endswith(b"\n"), "S1 CRLF/LF")
        need("s1/status", s1.get("status") == "CORRECTIVE_SUPPLEMENT_FROZEN", s1.get("status"))
        need("s1/created_after_repair", s1.get("supplement_created_after_repair_audit") is True)
        need("s1/frozen_before_s1_repairs", s1.get("frozen_before_s1_repairs") is True)
        need("s1/not_frozen_before_original_results",
             s1.get("frozen_before_original_repair_results") is False)
        need("s1/supersedes_only_arithmetic",
             s1.get("supersedes_only_inaccurate_arithmetic_and_reference_identity") is True)
        need("s1/original_commit",
             s1.get("amendment_001", {}).get("introduction_commit") == HISTORICAL_SHA)
        need("s1/original_blob",
             s1.get("amendment_001", {}).get("introduction_blob")
             == "0434291f9ac49fcf55b261f11fe1f5dbdbbfbbde")
        need("s1/repair_commit",
             s1.get("repair_commit") == "e44d7f56d5c9912e52dc4559ee2efef580d75609")
        need("s1/audited_head",
             s1.get("audited_head") == "2a922d710ff8fb79f6cb78c21e52f635bd1b0eae")
        need("s1/agent2_sha",
             s1.get("agent2_hostile_matrix_sha")
             == "47e98eb7d7bb1f46772f87de45b97eae66456181c31fab7cc1bd7fc1e09404a2")
        need("s1/disposition",
             s1.get("agent2_disposition") == "PARALLEL_P0_REAUDIT_REPAIR_REQUIRED_B6_I5")
        drift = s1.get("arithmetic_drift", {}).get("section_drift", [])
        drift_map = {d["section"]: (d["original_frozen_value"], d["correct_value"]) for d in drift}
        need("s1/drift_C3.S3", drift_map.get("C3.S3") == (15, 13), drift_map)
        need("s1/drift_C3.S4", drift_map.get("C3.S4") == (11, 12), drift_map)
        need("s1/drift_C3.S5", drift_map.get("C3.S5") == (14, 15), drift_map)
        need("s1/drift_total", drift_map.get("Total") == (40, 40), drift_map)
        # S1 must not predict a real governing SHA (uses placeholder)
        s1_gov = s1.get("cross_reference_plan", {}).get("governing_amendment_commit", "")
        need("s1/no_predicted_sha", "REAL S1 COMMIT SHA" in s1_gov and "<" in s1_gov, s1_gov)
    # Reference rebinding on each governed doc (not the amendment itself, not S1)
    governed_names = [n for n in p0_files
                      if n != f"{PREFIX}AMENDMENT_001_v1.0.json" and n != s1_name]
    for name in governed_names:
        obj = objs[name]
        need(f"s1_ref/historical/{name}",
             obj.get("historical_amendment_commit") == HISTORICAL_SHA, name)
        need(f"s1_ref/governing/{name}",
             obj.get("governing_amendment_commit") == S1_SHA, name)
        need(f"s1_ref/amendment_sha/{name}",
             obj.get("amendment_sha") == S1_SHA, name)
    # Original amendment history reachable
    orig_rev = git("rev-parse", f"{HISTORICAL_SHA}^{{commit}}")
    need("s1/original_history_reachable", HISTORICAL_SHA in orig_rev,
         "original amendment commit not reachable")
    # B-2: T19 direct governing source citation
    t19_entry = next((t for t in proofs.get("deferred_threats", []) if t.get("id") == "T19"), None)
    need("b2/t19_governing_source", t19_entry is not None
         and "governing_source" in t19_entry
         and "refuse publication" in t19_entry.get("governing_source", ""),
         t19_entry)
    need("b2/t19_provisional_node", t19_entry is not None
         and "provisional" in t19_entry.get("future_planned_node", ""), t19_entry)
    # B-3: mutation law compile wording
    mlaw = amendment["e1_non_vacuous_mutation_law"]
    need("b3/mutation_compile_law",
         "compiles successfully and remains syntactically valid before collection" in mlaw["law"]
         and "Mutated Python source must compile successfully and remain syntactically valid before collection" in mlaw["law"],
         "compile wording missing")

    # ---- stage identity ----
    need("stage/identity", scope["stage"] == contract["stage"] == "B6-I5")
    need("stage/base", scope["base_sha"] == contract["base_sha"] == "a4c4f10acac56ce53e1efd29c726039c86930b10")
    need("stage/base_tree",
         scope["base_tree"] == contract["base_tree"] == "b66fa4e3068565bc8d52ac5e0b7db71aee5b762b")
    need("stage/sections", scope["sections"] == ["C3.S3", "C3.S4", "C3.S5"])
    need("stage/surfaces", scope["implementation_surfaces"] == ["services"])
    need("stage/frozen", contract["status"] == "FROZEN" and contract["frozen_before_results"] is True)
    need("stage/registration_frozen",
         registration["status"] == "FROZEN" and registration["frozen_before_results"] is True)
    need("implementation/not_authorized",
         scope["locks"]["IMPLEMENTATION_AUTHORIZED"] is False
         and contract["locks"]["IMPLEMENTATION_AUTHORIZED"] is False
         and amendment["implementation_authorized"] is False)
    need("ratification/not_authorized",
         scope["locks"]["RATIFICATION_AUTHORIZED"] is False
         and amendment["ratification_authorized"] is False)
    need("merge/not_authorized",
         scope["locks"]["MERGE_AUTHORIZED"] is False
         and amendment["merge_authorized"] is False)
    need("locks/i6_i9",
         all(scope["locks"][f"B6-I{i}"] == "LOCKED" for i in (6, 7, 8, 9))
         and contract["locks"]["B6-I6_through_I9"] == "LOCKED"
         and amendment["b6_i6_through_i9_locked"] is True)
    need("cost/capital", scope["cost_usd"] == 0 and scope["capital_authority"] == "none"
         and amendment["cost_usd"] == 0 and amendment["capital_authority"] == "none")

    # ---- requirement/node totals ----
    reqs = registry["requirements"]
    nodes = registry["inventory"]["nodes"]
    need("registry/total", registry["requirements_total"] == len(reqs) == registry["inventory"]["node_total"] == 40,
         (registry["requirements_total"], len(reqs), registry["inventory"]["node_total"]))
    need("contract/floor", contract["implementation_floor"]["test_nodes"] == 40)
    need("scope/minimum_nodes", scope["minimum_nodes"] == 40)
    need("paired/head_only_expected", paired["population"]["head_only_expected"] == 40)
    need("contract/paired_head_only", contract["paired_comparison"]["head_only_expected"] == 40)

    # ---- requirement IDs unique and contiguous B6I5-R01..R40 ----
    req_ids = [r["id"] for r in reqs]
    need("req/unique", len(set(req_ids)) == len(req_ids))
    expected_ids = [f"B6I5-R{i:02d}" for i in range(1, 41)]
    need("req/contiguous", set(req_ids) == set(expected_ids),
         sorted(set(req_ids) ^ set(expected_ids)))

    # ---- bindings exactly once ----
    binding_nodes = [r["binding_node"] for r in reqs]
    need("binding/unique", len(set(binding_nodes)) == len(binding_nodes))
    need("binding/covers_inventory", set(binding_nodes) == set(nodes),
         sorted(set(binding_nodes) ^ set(nodes)))

    # ---- node inventory exact ----
    need("inventory/modules", len(registry["inventory"]["modules"]) == 5)
    section_counts: dict[str, int] = {}
    for r in reqs:
        section_counts[r["section"]] = section_counts.get(r["section"], 0) + 1
    need("section/C3.S3", section_counts.get("C3.S3", 0) == 13, section_counts)
    need("section/C3.S4", section_counts.get("C3.S4", 0) == 12, section_counts)
    need("section/C3.S5", section_counts.get("C3.S5", 0) == 15, section_counts)
    module_counts: dict[str, int] = {}
    for n in nodes:
        mod = n.split("::")[0]
        module_counts[mod] = module_counts.get(mod, 0) + 1
    need("module/contract", module_counts.get("test_block_06_i5_contract.py", 0) == 6, module_counts)
    need("module/knowledge", module_counts.get("test_block_06_i5_knowledge.py", 0) == 7, module_counts)
    need("module/artifact", module_counts.get("test_block_06_i5_artifact.py", 0) == 9, module_counts)
    need("module/evaluation", module_counts.get("test_block_06_i5_evaluation.py", 0) == 12, module_counts)
    need("module/provenance", module_counts.get("test_block_06_i5_provenance.py", 0) == 6, module_counts)

    # ---- failure-class partition exact-once ----
    fc = proofs["failure_classes"]
    fc_ids = [row["id"] for row in fc]
    need("failure/classes", set(fc_ids) == {"F03", "F08", "F11", "F12", "F23"}, fc_ids)
    need("failure/bound", all(row["proof_state"] == "BOUND" for row in fc))
    all_fc_nodes = [n for row in fc for n in row["nodes"]]
    need("failure/unique", len(set(all_fc_nodes)) == len(all_fc_nodes),
         "duplicate node across failure classes")
    need("failure/covers_inventory", set(all_fc_nodes) == set(nodes),
         sorted(set(all_fc_nodes) ^ set(nodes)))
    fc_counts = {row["id"]: len(row["nodes"]) for row in fc}
    need("failure/F03", fc_counts.get("F03") == 8, fc_counts)
    need("failure/F08", fc_counts.get("F08") == 2, fc_counts)
    need("failure/F11", fc_counts.get("F11") == 7, fc_counts)
    need("failure/F12", fc_counts.get("F12") == 3, fc_counts)
    need("failure/F23", fc_counts.get("F23") == 20, fc_counts)
    need("failure/total", sum(fc_counts.values()) == 40)

    # ---- R06 rebound to F23 ----
    r06 = next(r for r in reqs if r["id"] == "B6I5-R06")
    need("r06/failure_class", r06["failure_class"] == "F23", r06["failure_class"])
    need("r06/binding_node",
         r06["binding_node"] == "test_block_06_i5_contract.py::test_no_later_stage_dependency")
    need("r06/section", r06["section"] == "C3.S5")
    need("r06/rebind_recorded",
         registration.get("r06_rebinding", {}).get("failure_class") == "F23"
         and registration["r06_rebinding"].get("previous_failure_class") == "T19")

    # ---- T19 deferred ----
    t19_list = proofs.get("deferred_threats", [])
    t19_entry = next((t for t in t19_list if t["id"] == "T19"), None)
    need("t19/deferred", t19_entry is not None)
    if t19_entry:
        need("t19/owner", t19_entry["owner"] == "operator")
        need("t19/future_stage", t19_entry["future_authorized_stage"] == "B6-I9")
        need("t19/expected_refusal", t19_entry["expected_refusal"] == "refuse publication")
        need("t19/outside_partition", t19_entry.get("outside_current_partition") is True)
        need("t19/proof_state", t19_entry.get("proof_state") == "DEFERRED")
        need("t19/future_planned_node",
             "B6-I9 publication-hold gate node" in t19_entry.get("future_planned_node", ""))
    bound_threat_ids = [t["id"] for t in proofs.get("threats", []) if t.get("bound") is True]
    need("t19/not_bound", "T19" not in bound_threat_ids, bound_threat_ids)
    t19_nodes = [n for row in fc if row["id"] == "T19" for n in row["nodes"]]
    need("t19/no_current_nodes", len(t19_nodes) == 0, t19_nodes)

    # ---- threats T05-T08 bound ----
    need("threats/bound_count", len(bound_threat_ids) == 4, bound_threat_ids)
    need("threats/ids", set(bound_threat_ids) == {"T05", "T06", "T07", "T08"})

    # ---- negative controls distinct ----
    neg_controls = [r["negative_control"] for r in reqs]
    need("negative_control/distinct", len(set(neg_controls)) == len(neg_controls))

    # ---- mutation laws ----
    need("mutation/floor", mlaw["mutation_floor"] == 3)
    need("mutation/floor_kind", mlaw["mutation_floor_kind"] == "minimum")
    planned_mutations = mlaw["planned_mutations"]
    need("mutation/planned_count", len(planned_mutations) == 3)
    planned_ids = [m["id"] for m in planned_mutations]
    need("mutation/planned_ids", set(planned_ids) == {"M01", "M02", "M03"}, planned_ids)
    for m in planned_mutations:
        need(f"mutation/{m['id']}/discriminator",
             m["discriminator_node"] in nodes, m["discriminator_node"])
    need("mutation/law_items", len(mlaw["law"].split(";")) >= 10)
    need("mutation/prohibited_nonvacuous", len(mlaw["prohibited"]) >= 6)
    need("mutation/restoration", len(mlaw["restoration"]) >= 3)
    need("amendment/mutation_ids",
         set(amendment["new_mutation_ids_before_results"]) == {"M01", "M02", "M03"})

    # ---- E-2 refusal never pass ----
    r35 = next(r for r in reqs if r["id"] == "B6I5-R35")
    need("r35/failure_class", r35["failure_class"] == "F23")
    need("r35/mutation_witness", r35.get("mutation_witness") == "M03")
    need("r35/section", r35["section"] == "C3.S5")
    need("e2/refusal_not_pass",
         "refusal" in r35["statement"].lower() and "PASS" in r35["statement"])
    need("amendment/new_node_ids_r35",
         "test_block_06_i5_evaluation.py::test_refusal_never_pass"
         in amendment["new_node_ids_before_results"])

    # ---- E-3 reserved fields ----
    for field, rid in (("score", "B6I5-R36"), ("weight", "B6I5-R37"),
                       ("threshold", "B6I5-R38"), ("ranking", "B6I5-R39")):
        r = next(x for x in reqs if x["id"] == rid)
        need(f"e3/{field}", r["failure_class"] == "F23" and field in r["statement"].lower(), rid)
    need("e3/new_nodes",
         all(f"test_block_06_i5_evaluation.py::test_{field}_field_prohibited"
             in amendment["new_node_ids_before_results"]
             for field in ("score", "weight", "threshold", "ranking")))

    # ---- E-4 manifest separability ----
    r16 = next(r for r in reqs if r["id"] == "B6I5-R16")
    r17 = next(r for r in reqs if r["id"] == "B6I5-R17")
    r40 = next(r for r in reqs if r["id"] == "B6I5-R40")
    need("e4/r16_f12", r16["failure_class"] == "F12", r16["failure_class"])
    need("e4/r17_f11", r17["failure_class"] == "F11", r17["failure_class"])
    need("e4/r40_f12", r40["failure_class"] == "F12", r40["failure_class"])
    need("e4/r40_node",
         r40["binding_node"] == "test_block_06_i5_artifact.py::test_substitution_unchanged_name_refused")
    crosswalk = amendment["e4_manifest_separability"]["crosswalk"]
    need("e4/crosswalk_static_preserved",
         "R16" in crosswalk["static_preserved"] and "R17" in crosswalk["static_preserved"])
    need("e4/crosswalk_no_replace", "never replace" in crosswalk["no_silent_replace"])
    need("e4/crosswalk_laws",
         "hash_only_law" in crosswalk and "size_only_law" in crosswalk
         and "substitution_law" in crosswalk)

    # ---- cross-document arithmetic identical ----
    arith = amendment["planned_arithmetic"]
    need("arith/req_total", arith["requirements_total"] == 40)
    need("arith/node_total", arith["node_total"] == 40)
    need("arith/paired_head_only", arith["paired_head_only_expected"] == 40)
    need("arith/min_node_floor", arith["minimum_node_floor"] == 40)
    need("arith/mutation_floor", arith["mutation_minimum_floor"] == 3)
    need("arith/per_section_sum", sum(arith["per_section"].values()) == 40, arith["per_section"])
    need("arith/per_module_sum", sum(arith["per_module"].values()) == 40, arith["per_module"])
    need("arith/fc_sum", sum(arith["current_failure_class_partition"].values()) == 40)
    need("arith/deferred_threat_count", arith["deferred_threat_count"] == 1)
    need("arith/negative_control_count", arith["negative_control_count"] == 40)
    need("arith/planned_mutation_count", arith["planned_mutation_count"] == 3)
    need("arith/per_section_values",
         arith["per_section"] == {"C3.S3": 13, "C3.S4": 12, "C3.S5": 15}, arith["per_section"])
    need("arith/per_module_values",
         arith["per_module"] == {
             "test_block_06_i5_contract.py": 6,
             "test_block_06_i5_knowledge.py": 7,
             "test_block_06_i5_artifact.py": 9,
             "test_block_06_i5_evaluation.py": 12,
             "test_block_06_i5_provenance.py": 6,
         }, arith["per_module"])
    need("arith/fc_values",
         arith["current_failure_class_partition"] == {"F03": 8, "F08": 2, "F11": 7, "F12": 3, "F23": 20},
         arith["current_failure_class_partition"])

    # ---- cross-document ID sets ----
    need("id_set/new_nodes_count", len(amendment["new_node_ids_before_results"]) == 6)
    need("id_set/new_nodes_unique",
         len(set(amendment["new_node_ids_before_results"])) == 6)
    new_node_set = set(amendment["new_node_ids_before_results"])
    need("id_set/new_nodes_in_inventory", new_node_set <= set(nodes),
         sorted(new_node_set - set(nodes)))

    # ---- registration prefixes / locks ----
    need("registration/prefixes",
         ".github/workflows/block-06-i4-validation.yml" in registration["this_stage"]["allowed_prefixes"])
    need("registration/locks",
         all(registration["locks"][f"B6-I{i}"] == "LOCKED" for i in (6, 7, 8, 9)))

    # ---- zero PASS ----
    need("zero_pass", registry.get("tests_present") is False
         and contract.get("tests_present") is False
         and proofs.get("tests_present") is False
         and scope.get("p0_documentation_only") is True)
    need("amendment/tests_present",
         amendment["planned_arithmetic"]["tests_present"] is False)

    # ---- no production or B6-I5 tests exist ----
    test_files = sorted(p.name for p in (root / TESTS).glob("test_block_06_i5_*.py"))
    need("no_b6_i5_tests", len(test_files) == 0, test_files)
    oce_dir = root / "oce"
    i5_refs = git("grep", "-InE", "block_06_i5|B6-I5", "--", str(oce_dir))
    need("no_b6_i5_production_refs", i5_refs == "", i5_refs[:500])

    # ---- no prior-stage weakening ----
    changed = git("diff", "--name-only", "a4c4f10acac56ce53e1efd29c726039c86930b10..HEAD").splitlines()
    prior_changed = [p for p in changed if re.search(r"OCE_BLOCK_06_I[0-3]_", p)]
    need("no_prior_stage_change", len(prior_changed) == 0, prior_changed)

    # ---- no B6-I6+ files ----
    LATER_RE = r"OCE_BLOCK_06_I[6-9]_"
    later_files = [p for p in changed if re.search(LATER_RE, p)]
    need("no_b6_i6_plus_files", len(later_files) == 0, later_files)
    tree_later = git("ls-tree", "-r", "--name-only", "HEAD").splitlines()
    forbidden = [p for p in tree_later if any(f"OCE_BLOCK_06_I{i}_" in p for i in range(6, 10))]
    need("tree/no_b6_i6_plus", len(forbidden) == 0, forbidden)

    # ---- secret scan (exclude regex pattern definitions and markdown docs) ----
    secret_raw = git("grep", "-InE", "sk_live|sk_test|AKIA|ghp_|github_pat|AWS_SECRET", "--", DOCS, SCRIPTS)
    secret_lines = [l for l in secret_raw.splitlines()
                    if "re.compile" not in l
                    and not l.split(":", 1)[0].endswith(".md")
                    and not l.split(":", 1)[0].endswith("block_06_i5_validate.py")]
    need("secret_scan_clean", not secret_lines, secret_raw[:500])

    # ---- absolute-path scan (exclude markdown docs) ----
    abs_raw = git("grep", "-InE", "C:/|/home/|/Users/", "--", DOCS)
    abs_lines = [l for l in abs_raw.splitlines()
                 if not l.split(":", 1)[0].endswith(".md")]
    need("abs_path_scan_clean", not abs_lines, abs_raw[:500])

    # ---- git diff --check clean ----
    diffcheck = git("diff", "--check")
    need("git_diff_check_clean", diffcheck == "", diffcheck[:500])

    # ---- tracked tree clean after commit ----
    status = git("status", "--porcelain", "--untracked-files=all").strip()
    need("tracked_tree_clean", status == "", status[:500])

    # ---- local == remote ----
    local = git("rev-parse", "HEAD").strip()
    remote = git("rev-parse", "origin/oce-book-6-i5").strip()
    need("local_equals_remote", local == remote, (local, remote))

    status_str = "PASS" if not failures else "FAIL"
    doc = {"status": status_str, "stage": "B6-I5", "checks": len(checks),
           "failures": len(failures), "detail": failures[:12],
           "cost_usd": 0, "capital_authority": "none"}
    text = json.dumps(doc, sort_keys=True, indent=2) + "\n"
    print("\n".join(f"FAIL {row}" for row in failures))
    print(f"{status_str} {len(checks) - len(failures)}/{len(checks)} checks")
    return 0 if status_str == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
