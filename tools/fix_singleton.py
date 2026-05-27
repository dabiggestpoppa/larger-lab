"""Fix singleton reset in ContinuityMemory."""
path = r"C:\Users\wifik\Desktop\projects\larger-lab\core\observer\continuity_memory.py"
content = open(path).read()

# Add a reset method to ContinuityMemory
old_class = """class ContinuityMemory:
    \"\"\"
    Persistent operational continuity memory.
    
    Stores workflow outcomes, routing patterns, and operational goals
    to enable continuity across sessions and restarts.
    \"\"\"

    def __init__(self):
        self._lock = threading.RLock()
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self._record = self._load()"""

new_class = """class ContinuityMemory:
    \"\"\"
    Persistent operational continuity memory.
    
    Stores workflow outcomes, routing patterns, and operational goals
    to enable continuity across sessions and restarts.
    \"\"\"

    _instance: ContinuityMemory | None = None

    def __init__(self):
        self._lock = threading.RLock()
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self._record = self._load()

    @classmethod
    def reset_instance(cls) -> None:
        \"\"\"Reset the singleton instance (for testing).\"\"\"
        cls._instance = None"""

content = content.replace(old_class, new_class)
print("Added reset_instance to ContinuityMemory")

open(path, "w").write(content)
print("Done")
