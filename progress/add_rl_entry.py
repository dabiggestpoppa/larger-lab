"""Add OCE integration entry to rl-progress.md."""
import os

target = os.path.join(os.path.dirname(__file__), 'rl-progress.md')
f = open(target, 'r')
content = f.read()
f.close()

new_entry = """
####  OWL [RL] 2026-05-16 — OCE Integration: Adapter Fix + DSPy Pipelines + 27 Tests
- **Adapter Fix:** Fixed `srrs_adapter.py` — corrected constructor calls (no-arg for patches), fixed status key lookups ("is_stable" not "state"), fixed event ID uniqueness (counter), fixed validate_contract signature
- **DSPy Pipelines:** Created `dspy_pipelines.py` with 3 pipelines:
  - ContractGenerationPipeline: Heuristic + DSPy-optimized contract parameter generation
  - EventRoutingPipeline: Optimal event routing through overlap topology
  - EvolutionPlanningPipeline: Adaptive topology mutation planning with budget constraints
- **Pipeline Endpoints:** Added 4 new FastAPI endpoints: `/pipelines/status`, `/pipelines/contract/generate`, `/pipelines/event/route`, `/pipelines/evolution/plan`
- **Tests:** Created `oce/tests/test_oce_adapter.py` — 27 tests covering initialization, observer status, health checks, entropy economics, attractor state, memory access, event emission, prediction contracts, and full integration workflows
- **Results:** All 27 OCE tests passing + all 56 existing SRRA-OPH tests still passing (83 total)
- **Graceful Degradation:** All DSPy pipelines work without DSPy installed (heuristic fallback)
- **Files modified/created:**
  - `oce/backend/srrs_adapter.py` (fixed)
  - `oce/backend/dspy_pipelines.py` (new)
  - `oce/backend/main.py` (added pipeline endpoints)
  - `oce/tests/test_oce_adapter.py` (new, 27 tests)
  - `oce/tests/conftest.py` (new)

"""

# Insert after the first header separator
content = content.replace('---\n', '---\n' + new_entry, 1)

f = open(target, 'w')
f.write(content)
f.close()
print('Updated rl-progress.md')
