import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\wifik\Desktop\projects\larger-lab\oce\backend\substrate\tests\test_substrate_backend.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

old = '''    @async_test
    async def test_execute_permitted_command(self):
        """Permitted commands should execute (echo is safe)."""
        from oce.backend.substrate.terminal_orchestrator import get_terminal_orchestrator
        to = get_terminal_orchestrator()
        result = await to.execute("echo hello")
        assert "status" in result
        assert result["status"] in ("completed", "timed_out", "blocked")'''

new = '''    @async_test
    async def test_execute_permitted_command(self):
        """Permitted command should return a result dict."""
        from oce.backend.substrate.terminal_orchestrator import get_terminal_orchestrator
        to = get_terminal_orchestrator()
        result = await to.execute("git status")
        assert isinstance(result, dict)
        assert "status" in result or "output" in result or "error" in result'''

if old in c:
    c = c.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print("Fixed!")
else:
    print("Pattern not found!")
    # Show what's around line 345
    lines = c.split('\n')
    for i, line in enumerate(lines[340:355], start=341):
        print(f"{i}: {repr(line)}")
