"""Fix ContinuityMemory reset to clear in-memory data."""
path = r"C:\Users\wifik\Desktop\projects\larger-lab\core\observer\continuity_memory.py"
content = open(path).read()

old = """    @classmethod
    def reset_instance(cls) -> None:
        \"\"\"Reset the singleton instance (for testing).\"\"\"
        cls._instance = None"""

new = """    @classmethod
    def reset_instance(cls) -> None:
        \"\"\"Reset the singleton instance (for testing).\"\"\"
        if cls._instance is not None:
            cls._instance._record = cls._instance._load()
        cls._instance = None"""

content = open(path).read()
content = content.replace(old, new)
open(path, "w").write(content)
print("Fixed reset_instance")
