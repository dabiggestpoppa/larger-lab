"""Compare OLD vs NEW engine - extract key logic differences"""
import re

# Read both files as text (ignoring encoding issues)
def read_file_safe(path):
    for enc in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
        try:
            with open(path, 'r', encoding=enc) as f:
                return f.read()
        except:
            continue
    return ''

old = read_file_safe(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py.bak')
new = read_file_safe(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py')

# Extract the process_bar method from both
def extract_method(text, method_name):
    # Find method definition
    pattern = r'def ' + method_name + r'\([^)]*\).*?(?=\n    def |\nclass |\Z)'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(0)
    return ''

# Extract key methods
methods = ['process_bar', 'initialize_session', '_check_kill_switch', '_reset_state_keep_loop']

print("=== METHOD-BY-METHOD COMPARISON ===\n")

for method in methods:
    old_m = extract_method(old, method)
    new_m = extract_method(new, method)
    
    if old_m and new_m:
        # Compare line by line, ignoring whitespace and comments
        old_lines = [l.strip() for l in old_m.split('\n') if l.strip() and not l.strip().startswith('#')]
        new_lines = [l.strip() for l in new_m.split('\n') if l.strip() and not l.strip().startswith('#')]
        
        old_set = set(old_lines)
        new_set = set(new_lines)
        
        only_old = old_set - new_set
        only_new = new_set - old_set
        
        if only_old or only_new:
            print("\n--- %s ---" % method)
            if only_old:
                print("  REMOVED from old:")
                for line in sorted(only_old)[:10]:
                    print("    - %s" % line[:100])
            if only_new:
                print("  ADDED in new:")
                for line in sorted(only_new)[:10]:
                    print("    + %s" % line[:100])
    elif old_m and not new_m:
        print("\n--- %s ---" % method)
        print("  REMOVED entirely in new engine")
    elif not old_m and new_m:
        print("\n--- %s ---" % method)
        print("  NEW method in new engine")

# Also compare the classify functions
print("\n\n=== CLASSIFY FUNCTIONS ===\n")

# Find all classify-related functions
for text, label in [(old, 'OLD'), (new, 'NEW')]:
    funcs = re.findall(r'def (classify_\w+)\([^)]*\)', text)
    print("%s engine classify functions: %s" % (label, funcs))

# Extract classify_tier (old) vs classify_tier_by_ar + classify_tier_by_impulse (new)
print("\n=== TIER CLASSIFICATION LOGIC ===\n")

# Old classify_tier
old_classify = extract_method(old, 'classify_tier')
if old_classify:
    print("OLD classify_tier:")
    # Find the key logic
    for line in old_classify.split('\n'):
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and not stripped.startswith('"""'):
            print("  %s" % stripped[:120])

print()

# New classify_tier_by_ar
new_ar = extract_method(new, 'classify_tier_by_ar')
if new_ar:
    print("NEW classify_tier_by_ar:")
    for line in new_ar.split('\n'):
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and not stripped.startswith('"""'):
            print("  %s" % stripped[:120])

print()

# New classify_tier_by_impulse
new_impulse = extract_method(new, 'classify_tier_by_impulse')
if new_impulse:
    print("NEW classify_tier_by_impulse:")
    for line in new_impulse.split('\n'):
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and not stripped.startswith('"""'):
            print("  %s" % stripped[:120])
