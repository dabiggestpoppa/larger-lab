"""Fix repair patterns in task_intent_analyzer.py"""
path = r"C:\Users\wifik\Desktop\projects\larger-lab\core\observer\task_intent_analyzer.py"
content = open(path).read()

# Add 'fix' back to repair patterns
old = '    "repair": [\n        r"\\b(repair|recover|restore|heal|stabilize)\\b",'
new = '    "repair": [\n        r"\\b(repair|fix|recover|restore|heal|stabilize)\\b",'

if old in content:
    content = content.replace(old, new)
    print("Added 'fix' to repair patterns")
else:
    print("Pattern not found!")
    # Debug: show what's around "repair"
    idx = content.find('"repair"')
    if idx >= 0:
        print(repr(content[idx:idx+200]))

open(path, "w").write(content)
print("Done")
