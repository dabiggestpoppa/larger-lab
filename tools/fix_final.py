"""Fix ContinuityMemory reset to delete file and clear singleton."""
path = r"C:\Users\wifik\Desktop\projects\larger-lab\core\observer\continuity_memory.py"
content = open(path).read()

old = """    @classmethod
    def reset_instance(cls) -> None:
        \"\"\"Reset the singleton instance (for testing).\"\"\"
        if cls._instance is not None:
            cls._instance._record = cls._instance._load()
        cls._instance = None"""

new = """    @classmethod
    def reset_instance(cls) -> None:
        \"\"\"Reset the singleton instance (for testing).\"\"\"
        # Delete persistence file
        try:
            if MEMORY_FILE.exists():
                MEMORY_FILE.unlink()
        except Exception:
            pass
        cls._instance = None"""

content = content.replace(old, new)
open(path, "w").write(content)
print("Fixed reset_instance to delete file")

# Also update the test to just use reset_instance
path2 = r"C:\Users\wifik\Desktop\projects\larger-lab\tests\test_observer\test_o1_primary_observer.py"
content2 = open(path2).read()

old2 = '''    def setup_method(self):
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

new2 = '''    def setup_method(self):
        from core.observer.continuity_memory import ContinuityMemory, WorkflowRecord
        # Reset singleton state for clean tests (deletes persistence file)
        ContinuityMemory.reset_instance()
        self.memory = ContinuityMemory()
        self.WorkflowRecord = WorkflowRecord'''

content2 = content2.replace(old2, new2)
open(path2, "w").write(content2)
print("Simplified test setup")
