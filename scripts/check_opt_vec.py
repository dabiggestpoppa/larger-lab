"""Check optimization_vector_eur.py for config values."""
import re, os

fpath = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\tests\optimization_vector_eur.py'
if os.path.exists(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Find ar_max values
    ar_vals = re.findall(r'ar_max["\':\s]+([\d.]+)', content)
    trigger_vals = re.findall(r'trigger["\':\s]+([\d.]+)', content)
    au_vals = re.findall(r'"au"["\':\s]+([\d.]+)', content)
    print('optimization_vector_eur.py:')
    print('  ar_max:', ar_vals[:10])
    print('  trigger:', trigger_vals[:10])
    print('  au:', au_vals[:10])
else:
    print('File not found')

# Also check git for the committed version
import subprocess
result = subprocess.run(
    ['git', 'show', '9982d4388:quant-lab/tests/optimization_vector_eur.py'],
    cwd=r'C:\Users\wifik\Desktop\projects\larger-lab',
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
if result.returncode == 0 and result.stdout:
    content = result.stdout
    ar_vals = re.findall(r'ar_max["\':\s]+([\d.]+)', content)
    trigger_vals = re.findall(r'trigger["\':\s]+([\d.]+)', content)
    au_vals = re.findall(r'"au"["\':\s]+([\d.]+)', content)
    print()
    print('GIT version (9982d4388):')
    print('  ar_max:', ar_vals[:10])
    print('  trigger:', trigger_vals[:10])
    print('  au:', au_vals[:10])
