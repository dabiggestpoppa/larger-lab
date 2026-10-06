# B1-I1 Reality Inventory

**Date:** 2026-08-20
**Branch:** oce/block-1-i1-cloud-ground
**Commit:** (working branch)

---

## VERIFIED_PRESENT

| Item | Evidence | Location |
|------|----------|----------|
| Git repository on main | `git log --oneline -3` | Root |
| OCE Golden System docs | `docs/oce-golden-system/` | 6 files present |
| Block 1 planning dossier | `docs/oce-golden-system/OCE_BLOCK_01_CLOUD_GROUND_PLAN_v1.0.md` | 1011 lines |
| Block 1 agent master prompt | `docs/oce-golden-system/OCE_BLOCK_01_AGENT_MASTER_PROMPT_v1.0.md` | 583 lines |
| Existing OCE backend code | `oce/backend/` | Multiple Python files |
| Existing quant-lab | `quant-lab/` | Extensive codebase |
| .env with real API keys | `.env` | OPENAI, OANDA, etc. (redacted in output) |
| Python 3.11.9 installed | `python3 --version` | Windows Python |
| jsonschema available | `python3 -c "import jsonschema"` | Available |
| No Docker installed | `which docker` | NOT INSTALLED |
| No Ansible installed | `which ansible` | NOT INSTALLED |
| No jq installed | `which jq` | NOT INSTALLED |
| No shellcheck installed | `which shellcheck` | NOT INSTALLED |
| No gitleaks/trufflehog | `which gitleaks` | NOT INSTALLED |
| No existing cloud-ground infra | `find . -name "cloud-ground"` | None found |
| No existing Ansible config | `find . -name "ansible.cfg"` | None found |
| No CI/CD pipeline | `.github/workflows/` | Does not exist |
| .gitignore excludes .env, secrets | `.gitignore` | Present and configured |

## CLAIMED_NOT_VERIFIED

- OCE backend services are functional
- Any existing test infrastructure is complete
- pyproject.toml dependencies are current
- The existing quant-lab is production-ready

## MISSING (B1-I1 scope)

- Docker Engine and Compose
- Ansible and ansible-playbook
- jq for JSON processing
- shellcheck for shell script validation
- gitleaks for secret scanning
- yamllint for YAML validation
- Dedicated cloud server
- Tailscale account
- PostgreSQL running instance
- Redis running instance
- Object storage bucket
- Backup configuration

## CONTRADICTIONS

- None identified in B1-I1 scope

## HAZARDS

1. `.env` contains real API keys (OPENAI, OANDA, etc.)
   - Mitigation: .gitignore excludes .env; B1-I1 never reads or copies real credentials
   - Risk: Keys may have been committed historically
   - Action: Verify git history for leaked secrets during Block 2

2. No secret scanning tools installed
   - Mitigation: Manual grep-based scanning in validate-static
   - Risk: Pattern-based scanning may miss novel secret formats
   - Action: Install gitleaks during B1-I2

3. Windows environment may have path issues
   - Mitigation: POSIX syntax used throughout
   - Risk: Some bash commands may behave differently
   - Action: Test on actual Linux host during B1-I2

## DECISIONS_REQUIRED

1. None for B1-I1 — all decisions are pre-ratified in Block 1 dossier
2. Future: exact Tailscale auth key, backup target, provider credentials (B1-I0/B1-I2)

## RECOMMENDED_CANONICAL_PATH

- Infrastructure root: `infrastructure/cloud-ground/`
- This is the single canonical location for all Block 1 infrastructure code
- No parallel infrastructure stacks should be created
