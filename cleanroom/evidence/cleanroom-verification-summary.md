# Cleanroom Verification Summary

Repository: `https://github.com/dabiggestpoppa/larger-lab.git`  
Branch: `agent/repo-cleanroom`  
Observed at (UTC): `2026-08-30T15:06:26Z`  
Observed branch SHA: `79886c12ae3aa1bf0e375944936304c33bf71a39`  
Tested subject commit: `79886c12ae3aa1bf0e375944936304c33bf71a39`  
Evidence commit: `None`  
Overall status: **PASS** (exit code 0)

| Status | Count |
|---|---|
| PASS | 18 |
| FAIL | 0 |
| BLOCKED | 0 |
| SKIPPED | 2 |
| NOT_RUN | 4 |

## Checks

| Check | Status | Detail |
|---|---|---|
| repo_identity | PASS | {"expected": "https://github.com/dabiggestpoppa/larger-lab.git", "observed": "https://github.com/dabiggestpoppa/larger-lab"} |
| cleanroom_branch | PASS | {"expected": "agent/repo-cleanroom", "observed": "agent/repo-cleanroom"} |
| tested_subject | PASS | {"expected_subject": "79886c12ae3aa1bf0e375944936304c33bf71a39", "observed_head": "79886c12ae3aa1bf0e375944936304c33bf71a39"} |
| clean_worktree | PASS | {"dirty_entries": [], "dirty_count": 0, "rc": 0} |
| main_unchanged | PASS | {"expected": "7e7ef7222c4ecdea568b34583fd81406165cc9b6", "observed": "7e7ef7222c4ecdea568b34583fd81406165cc9b6", "resolved_ref": "refs/remotes/origin/main", "note": "reported without altering main if  |
| protected_branches | PASS | {"results": {"oce": {"expected": "d3df9eb45aeddd8a3dd40ced24a7f2e1d2f0ff41", "remote": "d3df9eb45aeddd8a3dd40ced24a7f2e1d2f0ff41", "status": "EXACT"}, "oce-program-build": {"expected": "ac0e239386aa10 |
| restored_branches | PASS | {"results": {"archive/cerebus-local-extra": {"expected": "133364c9cb1cd2127b48421babc14a8d57e1d99a", "remote": "133364c9cb1cd2127b48421babc14a8d57e1d99a", "status": "EXACT"}, "archive/content-oc2": {" |
| archive_tags | PASS | {"results": {"archive-branch/cerebus-local-extra": {"annotated_remote": true, "annotated_local": true, "expected_target": "133364c9cb1cd2127b48421babc14a8d57e1d99a", "remote_target": "133364c9cb1cd212 |
| manifest_consistency | PASS | {"problems": []} |
| restored_files | PASS | {"files_checked": 50, "failures": [], "results": {"quant-lab/backtests/debug_jan3.py": {"path": "quant-lab/backtests/debug_jan3.py", "git_blob": "e521dfc537642fcda876da732006cd5ce1338114", "blob_match |
| trash_inventory | SKIPPED | {"reason": "local-only operator-machine state; not present in CI clone"} |
| lfs_status | PASS | {"cache_dir": "/home/runner/work/larger-lab/larger-lab/.git/lfs/objects", "cache_size_bytes": 0, "min_cache_size_bytes": 1000000000, "cache_size_note": "LFS cache directory is local-only state; not as |
| stash_inventory | SKIPPED | {"reason": "local-only operator-machine state; not present in CI clone"} |
| gitleaks_secret_scan | PASS | {"binary": "/usr/local/bin/gitleaks", "exit_code": 0, "findings": 0, "finding_list": [], "reason": "no leaks found in cleanroom commits", "note": "full-history repo scan is documented in the report; t |
| regex_secret_scan | PASS | {"files_scanned": 75, "hits": [], "hit_count": 0, "note": "non-authoritative; gitleaks is the authoritative scan"} |
| json_parse | PASS | {"files_parsed": 8, "failures": []} |
| yaml_parse | PASS | {"files_parsed": 2, "failures": []} |
| python_compile | PASS | {"files_compiled": 11, "failures": []} |
| doc_links | PASS | {"links_checked": 0, "broken": [], "broken_count": 0} |
| git_object_integrity | PASS | {"exit_code": 0, "output_tail": ""} |
| not_run:protected_suites_oce_b1_i1r | NOT_RUN | {"reason": "intentionally NOT run on cleanroom branch; integrity verified by unchanged refs"} |
| not_run:protected_suites_grant | NOT_RUN | {"reason": "intentionally NOT run; worktree untouched"} |
| not_run:protected_suites_crypto | NOT_RUN | {"reason": "intentionally NOT run; branches verified by unchanged refs"} |
| not_run:protected_suites_tb | NOT_RUN | {"reason": "intentionally NOT run; branch verified by unchanged refs"} |

## Branches advanced after observation
- `agent/crypto-sensor-fabric-build`
- `oce-program-build`

**Clean: no mandatory FAIL or BLOCKED checks.**
