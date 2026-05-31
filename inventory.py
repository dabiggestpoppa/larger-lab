import os, json
from pathlib import Path

lab = Path(r'C:\Users\wifik\Desktop\projects\larger-lab')

# Count all Python files by directory
dirs_to_check = [
    lab / 'srrs_opc',
    lab / 'core',
    lab / 'oce',
    lab / 'oce/backend',
    lab / 'quant-lab',
    lab / 'tools',
]

print("=" * 60)
print("SRRA-OPH + LAB MODULE INVENTORY")
print("=" * 60)

total = 0
for d in dirs_to_check:
    if not d.exists():
        continue
    py_files = list(d.rglob('*.py'))
    # Exclude __pycache__
    py_files = [f for f in py_files if '__pycache__' not in str(f)]
    count = len(py_files)
    total += count
    print(f"\n{d.name}/ ({count} Python files)")
    # Show subdirectories
    subdirs = set()
    for f in py_files:
        rel = f.relative_to(d)
        if len(rel.parts) > 1:
            subdirs.add(rel.parts[0])
    for sd in sorted(subdirs):
        sd_files = [f for f in py_files if str(f.relative_to(d)).startswith(sd + '/')]
        print(f"  {sd}/ ({len(sd_files)} files)")

print(f"\n{'='*60}")
print(f"TOTAL: {total} Python files across all directories")
print(f"{'='*60}")

# Specifically check core/ structure
print("\n\nCORE/ DETAILED BREAKDOWN:")
core = lab / 'core'
for item in sorted(core.iterdir()):
    if item.is_dir():
        py_count = len([f for f in item.rglob('*.py') if '__pycache__' not in str(f)])
        print(f"  {item.name}/: {py_count} Python files")

# Check if core is git-tracked
print("\n\nGIT STATUS FOR CORE/:")
import subprocess
result = subprocess.run(
    ['git', 'ls-files', 'core/'],
    cwd=str(lab), capture_output=True, text=True
)
tracked = result.stdout.strip().split('\n') if result.stdout.strip() else []
print(f"  Git-tracked files in core/: {len(tracked)}")

# Check srrs_opc API modules endpoint
print("\n\nSRRA API MODULES:")
api_main = lab / 'srrs_opc' / 'api' / 'main.py'
if api_main.exists():
    content = api_main.read_text()
    # Count router inclusions
    routers = [line.strip() for line in content.split('\n') if 'include_router' in line or 'APIRouter' in line]
    for r in routers[:20]:
        print(f"  {r[:80]}")
