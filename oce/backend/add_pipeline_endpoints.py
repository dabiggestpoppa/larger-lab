"""Add pipeline endpoints to main.py - run once."""
import os

target = os.path.join(os.path.dirname(__file__), 'main.py')
f = open(target, 'r')
content = f.read()
f.close()

# 1. Add import for pipeline manager
old_import = "from srrs_adapter import get_adapter, SRRSAdapter"
new_import = "from srrs_adapter import get_adapter, SRRSAdapter\nfrom dspy_pipelines import OCEPipelineManager"
content = content.replace(old_import, new_import)

# 2. Find the websocket endpoint and add pipeline endpoints before it
ws_marker = '@app.websocket("/ws/events")'

pipeline_code = '''
# Pipeline manager
pipeline_manager = OCEPipelineManager()


@app.get("/pipelines/status")
async def get_pipeline_status():
    """Get status of all DSPy pipelines."""
    return pipeline_manager.get_status()


@app.post("/pipelines/contract/generate")
async def generate_contract(request: dict):
    """Generate optimized prediction contract parameters."""
    result = pipeline_manager.generate_contract(
        mutation_type=request.get("mutation_type", "unknown"),
        target=request.get("target", "unknown"),
        historical_accuracy=request.get("historical_accuracy", 0.5),
        coherence_metrics=request.get("coherence_metrics"),
    )
    return result


@app.post("/pipelines/event/route")
async def route_event(request: dict):
    """Route an event through optimal path."""
    result = pipeline_manager.route_event(
        event_type=request.get("event_type", "unknown"),
        observer_state=request.get("observer_state", {}),
        entropy_level=request.get("entropy_level", 0.0),
    )
    return result


@app.post("/pipelines/evolution/plan")
async def plan_evolution(request: dict):
    """Plan adaptive evolution."""
    result = pipeline_manager.plan_evolution(
        current_metrics=request.get("current_metrics", {}),
        budget=request.get("entropy_budget_remaining", 500.0),
        targets=request.get("coherence_targets", {}),
    )
    return result

'''

content = content.replace(ws_marker, pipeline_code + ws_marker)

f = open(target, 'w')
f.write(content)
f.close()
print('Added pipeline endpoints to main.py')
