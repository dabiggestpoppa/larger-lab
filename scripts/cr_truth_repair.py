import json, subprocess, sys, os, datetime, re
from pathlib import Path
C = Path(__file__).resolve().parents[1]
# Files
book2 = C / 'evidence' / 'book_2_nautilus_evidence.json'
book3 = C / 'artifacts' / 'book_3_classification.json'
appr = C / 'artifacts' / 'independent_approval.json'
external = C / 'evidence' / 'external_claims_register.json'
repo_fp = C / 'evidence' / 'repository_fingerprint.json'
test_exec = C / 'evidence' / 'test_execution.json'
impl_inv = C / 'evidence' / 'implementation_inventory.json'
phase_status = C / 'evidence' / 'phase_status.json'
report_md = C / 'artifacts' / 'audits' / 'cr_truth_repair_report.md'
gate_json = C / 'artifacts' / 'audits' / 'cr_truth_repair_gate.json'
# Ensure audits dir
(C / 'artifacts' / 'audits').mkdir(parents=True, exist_ok=True)
# Load originals if present
orig = {}
for p,label in [(book2,'book_2'),(book3,'book_3'),(appr,'approval')]:
    if p.exists():
        try:
            orig[label] = json.loads(p.read_text(encoding='utf-8'))
        except Exception as e:
            orig[label] = {'_raw': p.read_text(encoding='utf-8')}
    else:
        orig[label] = None
# Create external claims register with originals
external_content = {
    'created_at': datetime.datetime.utcnow().isoformat()+'Z',
    'source': 'migrated_unverified_external_claims',
    'items': {}
}
for k,v in orig.items():
    if v is not None:
        external_content['items'][k] = {'verified': False, 'original': v}
external.write_text(json.dumps(external_content, indent=2), encoding='utf-8')
# Overwrite book_2 to mark unverified
if book2.exists():
    new_book2 = {'note':'migrated_to_external_claims_register','verified': False}
    book2.write_text(json.dumps(new_book2, indent=2), encoding='utf-8')
# Update classification to mark external/unverified
if book3.exists():
    try:
        c = json.loads(book3.read_text(encoding='utf-8'))
    except:
        c = {}
    c.update({
        'classification': 'EXTERNAL_UNVERIFIED',
        'evidence_based': False,
        'research_status': 'UNVERIFIED',
        'deployment_status': 'NOT_DEPLOYED',
        'validation_status': 'UNVERIFIED',
        'notes': 'Original classification inherited from external projects; marked unverified by truth-repair.'
    })
    book3.write_text(json.dumps(c, indent=2), encoding='utf-8')
# Update approval artifact to mark unverified if missing provenance
if appr.exists():
    try:
        a = json.loads(appr.read_text(encoding='utf-8'))
    except:
        a = {}
    # Minimal provenance check
    reviewer = a.get('approved_by')
    if not reviewer or reviewer in ('OC2','Auto','System'):
        a.update({'verified': False, 'verification_note': 'No independent reviewer identity/provenance found; marked unverified by truth-repair.'})
    else:
        a.update({'verified': False, 'verification_note': 'Approved but still requires reviewer provenance (id,commit,timestamp). Marked unverified until provided.'})
    appr.write_text(json.dumps(a, indent=2), encoding='utf-8')
# Create repository fingerprint
sha = subprocess.run(['git','rev-parse','HEAD'], cwd=C, capture_output=True, text=True)
branch = subprocess.run(['git','rev-parse','--abbrev-ref','HEAD'], cwd=C, capture_output=True, text=True)
repo_info = {
    'repository': 'dabiggestpoppa/larger-lab',
    'path': str(C),
    'commit_sha': sha.stdout.strip() if sha.returncode==0 else None,
    'branch': branch.stdout.strip() if branch.returncode==0 else None,
    'python_version': sys.version,
    'generated_at': datetime.datetime.utcnow().isoformat()+'Z'
}
repo_fp.write_text(json.dumps(repo_info, indent=2), encoding='utf-8')
# Run pytest and capture output
start = datetime.datetime.utcnow()
proc = subprocess.run([sys.executable,'-m','pytest','-q','tests/'], cwd=C, capture_output=True, text=True)
end = datetime.datetime.utcnow()
raw_out = proc.stdout + '\n' + proc.stderr
# Try to find counts
passed = failed = skipped = 0
m2 = re.search(r'(?:(\d+) passed)?(?:,?\s*(\d+) failed)?(?:,?\s*(\d+) skipped)?', raw_out)
if m2:
    g = m2.groups()
    try:
        passed = int(g[0]) if g[0] else 0
    except:
        passed = 0
    try:
        failed = int(g[1]) if g[1] else 0
    except:
        failed = 0
    try:
        skipped = int(g[2]) if g[2] else 0
    except:
        skipped = 0
# Create test_execution.json
test_exec_data = {
    'command': 'pytest -q tests/',
    'returncode': proc.returncode,
    'start': start.isoformat()+'Z',
    'end': end.isoformat()+'Z',
    'duration_seconds': (end-start).total_seconds(),
    'counts': {
        'passed': passed,
        'failed': failed,
        'skipped': skipped,
        'errors': 0
    },
    'raw_output': raw_out,
    'commit_sha': repo_info['commit_sha']
}
Path(test_exec).write_text(json.dumps(test_exec_data, indent=2), encoding='utf-8')
# Implementation inventory (simple)
impl = {'phases_implemented': ['phase_1_data_discovery'], 'modules': ['SymbolAliases','ProviderRegistry','SchemaDetector','BasicChecks','DataDiscoverer']}
Path(impl_inv).write_text(json.dumps(impl, indent=2), encoding='utf-8')
# Phase status
phase = {
    'phase_0': 'implemented_repaired',
    'phase_1': 'implemented_pending_independent_validation',
    'phase_2': 'not_implemented',
    'phase_3': 'not_implemented'
}
Path(phase_status).write_text(json.dumps(phase, indent=2), encoding='utf-8')
# Generate markdown report
report = f"""# CR Truth Repair Report

Generated: {datetime.datetime.utcnow().isoformat()}Z
Repository SHA: {repo_info['commit_sha']}
Branch: {repo_info['branch']}

Summary:
- Extracted external claims from existing artifacts and moved originals into `evidence/external_claims_register.json`.
- Marked classification and approval artifacts as unverified.
- Ran unit tests in `tests/` and recorded results in `evidence/test_execution.json`.

Test counts: passed={test_exec_data['counts']['passed']} failed={test_exec_data['counts']['failed']} skipped={test_exec_data['counts']['skipped']}

Next steps:
1. Provide independent reviewer provenance for any approvals to re-validate Phase 1.
2. Implement Phase 2 after independent validation.

"""
Path(report_md).write_text(report, encoding='utf-8')
# Gate json
gate = {'gate_id':'CR-P0-TRUTH-REPAIR-01','decision':'partial_repair','phase_1_accepted': False,'notes':'Phase 1 implemented but pending independent validation; external claims moved/marked unverified.'}
Path(gate_json).write_text(json.dumps(gate, indent=2), encoding='utf-8')
# Update docs/BUILD_STATUS.md
build_status = C.parent / 'docs' / 'BUILD_STATUS.md'
build_status.parent.mkdir(parents=True, exist_ok=True)
build_status.write_text('# BUILD STATUS\n\nCR Truth Repair performed: Phase 1 implemented/pending validation. See capital-routing/artifacts/audits/cr_truth_repair_report.md\n', encoding='utf-8')
# Git add and commit
subprocess.run(['git','add','evidence','artifacts','docs/BUILD_STATUS.md'], cwd=C)
subprocess.run(['git','commit','-m','CR-P0-TRUTH-REPAIR-01: remove unsupported evidence and reconcile actual state'], cwd=C)
# Print summary
print(json.dumps({'commit': subprocess.run(['git','rev-parse','HEAD'], cwd=C, capture_output=True, text=True).stdout.strip(), 'test_counts': test_exec_data['counts']}))
