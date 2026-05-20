## Description

<!-- Provide a clear and concise description of the changes. -->

## Type of Change

<!-- Mark the relevant option with an [x] -->

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to change)
- [ ] 📝 Documentation update
- [ ] 🔧 Tooling / infrastructure change
- [ ] 🧪 Test addition or improvement
- [ ] 🏗️ Architecture change

## Related Issue

<!-- Link to the related issue(s) -->
Closes #

## Changes Made

<!-- List the key changes made in this PR -->

1.
2.
3.

## Testing

<!-- Describe how you tested these changes -->

- [ ] All existing tests pass (`python -m pytest srrs_opc/tests/ -v`)
- [ ] All existing tests pass (`python -m pytest oce/backend/tests/ -v`)
- [ ] New tests added for new functionality
- [ ] Tested manually (describe below)

**Test output:**
```
Paste relevant test output here
```

## Architecture Impact

<!-- Does this change affect the system architecture? -->

- [ ] No architecture impact
- [ ] Requires arch-commit review

If architecture impact, run:
```powershell
python tools/arch-commit.py --agent <TAG> --file "<path>" --change "<description>"
```

## Checklist

<!-- Mark completed items with [x] -->

- [ ] Code follows the project's coding standards (`docs/CODE_QUALITY.md`)
- [ ] Self-reviewed the code
- [ ] Added/updated docstrings for public functions
- [ ] Updated relevant documentation (`docs/`)
- [ ] Added/updated tests for new functionality
- [ ] All tests pass locally
- [ ] No new warnings introduced
- [ ] Progress file updated (`progress/<agent>-progress.md`)
- [ ] Changes are backward compatible (or breaking change is documented)

## Screenshots / Logs

<!-- If applicable, add screenshots or log output to help explain the change. -->

## Additional Notes

<!-- Any additional information that reviewers should know. -->
