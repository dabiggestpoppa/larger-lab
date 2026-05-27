"""Fix ContinuityMemory test to delete persistence file."""
path = r"C:\Users\wifik\Desktop\projects\larger-lab\tests\test_observer\test_o1_primary_observer.py"
content = open(path).read()

old = '''    def setup_method(self):
        from core.observer.continuity_memory import ContinuityMemory, WorkflowRecord
        # Reset singleton state for clean tests
        ContinuityMemory.reset_instance()
        self.memory = ContinuityMemory()
        self.WorkflowRecord = WorkflowRecord'''

new = '''    def setup_method(self):
        from core.observer.continuity_memory import ContinuityMemory, WorkflowRecord
        from pathlib import Path
        # Delete persistence file for clean tests
        mem_file = Path("data/observer/memory/continuity_memory.json")
        if mem_file.exists():
            mem_file.unlink()
        # Reset singleton state for clean tests
        ContinuityMemory.reset_instance()
        self.memory = ContinuityMemory()
        self.WorkflowRecord = WorkflowRecord'''

content = content.replace(old, new)
open(path, "w").write(content)
print("Fixed ContinuityMemory test setup")
