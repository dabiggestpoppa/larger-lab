"""One-time fix for progress-sync.py REPO_MEMORY path."""
content = open('tools/progress-sync.py', 'r', encoding='utf-8').read()
old = 'REPO_MEMORY = Path(__file__).parent.parent.parent / "memories" / "repo" / "workspace-state.md"'
new = 'REPO_MEMORY = WORKSPACE_ROOT / "progress" / "workspace-state.md"'
if old in content:
    content = content.replace(old, new)
    open('tools/progress-sync.py', 'w', encoding='utf-8').write(content)
    print('FIXED: REPO_MEMORY path corrected')
else:
    print('NOT FOUND - checking actual content:')
    for i, line in enumerate(content.splitlines(), 1):
        if 'REPO_MEMORY' in line:
            print(f'  Line {i}: {repr(line)}')
