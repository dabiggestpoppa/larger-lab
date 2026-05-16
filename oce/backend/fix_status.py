"""Fix status key references in srrs_adapter.py"""
import os

target = os.path.join(os.path.dirname(__file__), 'srrs_adapter.py')
f = open(target, 'r')
content = f.read()
f.close()

# Fix 1: observer status state key
old = '"state": patch_status.get("state", "active"),'
new = '"state": "active" if patch_status.get("is_stable", False) else "repairing",'
content = content.replace(old, new)

# Fix 2: health check state key
old = '"state": status.get("state", "unknown"),'
new = '"state": "active" if status.get("is_stable", False) else "repairing",'
content = content.replace(old, new)

# Fix 3: health check healthy key
old = '"healthy": status.get("state") == "active",'
new = '"healthy": status.get("is_stable", False),'
content = content.replace(old, new)

f = open(target, 'w')
f.write(content)
f.close()
print('Fixed status keys in srrs_adapter.py')
