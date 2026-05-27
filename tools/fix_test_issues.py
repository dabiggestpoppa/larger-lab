"""Fix remaining test issues."""
path = r"C:\Users\wifik\Desktop\projects\larger-lab\tests\test_observer\test_o1_primary_observer.py"
content = open(path).read()

# Fix 1: Reset ContinuityMemory singleton between tests
old_continuity_setup = '''    def setup_method(self):
        from core.observer.continuity_memory import ContinuityMemory, WorkflowRecord
        self.memory = ContinuityMemory()
        self.WorkflowRecord = WorkflowRecord'''

new_continuity_setup = '''    def setup_method(self):
        from core.observer.continuity_memory import ContinuityMemory, WorkflowRecord
        # Reset singleton state for clean tests
        ContinuityMemory._instance = None
        self.memory = ContinuityMemory()
        self.WorkflowRecord = WorkflowRecord'''

content = content.replace(old_continuity_setup, new_continuity_setup)
print("Fixed: ContinuityMemory setup")

# Fix 2: Add routing_hints to OrchestrationResponse
old_response = '''@dataclass
class OrchestrationResponse:
    """Response from the Primary Observer."""
    request_id: str
    observer_id: str
    timestamp: str
    status: str  # "received", "analyzing", "routing", "spawning", "complete", "error"
    task_domain: str = ""
    complexity: str = ""
    message: str = ""
    context_summary: dict[str, Any] = field(default_factory=dict)
    next_action: str = ""
    error: str | None = None'''

new_response = '''@dataclass
class OrchestrationResponse:
    """Response from the Primary Observer."""
    request_id: str
    observer_id: str
    timestamp: str
    status: str  # "received", "analyzing", "routing", "spawning", "complete", "error"
    task_domain: str = ""
    complexity: str = ""
    message: str = ""
    context_summary: dict[str, Any] = field(default_factory=dict)
    routing_hints: dict[str, Any] = field(default_factory=dict)
    next_action: str = ""
    error: str | None = None'''

content = content.replace(old_response, new_response)
print("Fixed: OrchestrationResponse routing_hints")

open(path, "w").write(content)
print("Done")
