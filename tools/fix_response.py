"""Fix OrchestrationResponse to include routing_hints."""
path = r"C:\Users\wifik\Desktop\projects\larger-lab\core\observer\primary_observer.py"
content = open(path).read()

old = '    context_summary: dict[str, Any] = field(default_factory=dict)\n    next_action: str = ""\n    error: str | None = None\n\n\nclass PrimaryObserver:'
new = '    context_summary: dict[str, Any] = field(default_factory=dict)\n    routing_hints: dict[str, Any] = field(default_factory=dict)\n    next_action: str = ""\n    error: str | None = None\n\n\nclass PrimaryObserver:'

if old in content:
    content = content.replace(old, new)
    print("Fixed OrchestrationResponse")
else:
    print("Pattern not found - trying alternative")
    # Try with different whitespace
    old2 = "    context_summary: dict[str, Any] = field(default_factory=dict)\n    next_action: str = \"\"\n    error: str | None = None"
    new2 = "    context_summary: dict[str, Any] = field(default_factory=dict)\n    routing_hints: dict[str, Any] = field(default_factory=dict)\n    next_action: str = \"\"\n    error: str | None = None"
    if old2 in content:
        content = content.replace(old2, new2)
        print("Fixed with alternative pattern")
    else:
        print("Neither pattern found")
        idx = content.find("context_summary")
        if idx >= 0:
            print(repr(content[idx:idx+200]))

open(path, "w").write(content)
print("Done")
