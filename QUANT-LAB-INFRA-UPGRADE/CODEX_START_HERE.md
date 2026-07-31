# Codex Start Here

Use this page when continuing QUANT LAB INFRA UPGRADE from Codex, another computer, or a fresh session.

## First Five Minutes

1. Pull the current `main` branch with a fast-forward-only update.
2. Read [AGENTS.md](AGENTS.md) and follow its mandatory read order.
3. Open [BUILD_STATUS.md](BUILD_STATUS.md); do not infer state from chat history.
4. Run `git status --short --branch` and preserve unrelated work.
5. Run the active part's existing tests before changing code.

## Current Continuation Prompt

```text
Continue QUANT LAB INFRA UPGRADE from its repository evidence.
Read the root OPERATOR_RULES.md and CLAUDE.md, then
QUANT-LAB-INFRA-UPGRADE/AGENTS.md, README.md, BUILD_STATUS.md,
the active phase README, active book, and exact implementation part.
State the active scope and authority boundary before editing.
Implement only the next admitted part, establish red before green,
run its declared tests, update BUILD_STATUS.md, and do not advance
the phase without the required independent gate.
```

## Current Next Work

The next planned slice is Phase 0, Book 1, Part 2:

- [Part 2 contract](implementation/phase-00/book-1/part-02-trading-dependencies-data.md)
- trading-engine and strategy census;
- dependency and runtime declaration inventory;
- bounded data-file metadata inventory;
- no operational classification and no broker actions.

Before implementing Part 2, verify Part 1 remains reproducible:

```bash
python3 -m tools.forge.validate_extension_docs --root .

python3 -m unittest discover -s tests/forge/phase_00 -p 'test_*.py'

python3 -m tools.forge.phase0_inventory \
  --root . \
  --output-dir artifacts/forge/phase-00/book-01-part-01
```

## Remote-Work Commit Discipline

Use explicit staging. Do not stage local PID files, credentials, caches, data, or unrelated workspace changes.

```bash
git status --short
git add <exact paths for the active part>
python3 -m tools.forge.validate_extension_docs --root .
git diff --cached --check -- '*.py' ':(top)README.md'
git diff --cached --stat
git commit -m "Phase 0 Book 1 Part N: <bounded outcome>"
git push origin main
```

A successful push publishes source; it does not change a build state to `verified` or `locked` by itself.
