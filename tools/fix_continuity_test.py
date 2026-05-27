"""Fix ContinuityMemory test to properly reset singleton."""
path = r"C:\Users\wifik\Desktop\projects\larger-lab\tests\test_observer\test_o1_primary_observer.py"
content = open(path).read()

old = '''    def setup_method(self):
        from core.observer.continuity_memory import ContinuityMemory, WorkflowRecord
        # Reset singleton state for clean tests
        ContinuityMemory._instance = None
        self.memory = ContinuityMemory()
        self.WorkflowRecord = WorkflowRecord'''

new = '''    def setup_method(self):
        from core.observer.continuity_memory import ContinuityMemory, WorkflowRecord
        # Reset singleton state for clean tests
        ContinuityMemory.reset_instance()
        self.memory = ContinuityMemory()
        self.WorkflowRecord = WorkflowRecord'''

content = content.replace(old, new)
print("Fixed ContinuityMemory test setup")

open(path, "w").write(content)
print("Done")
