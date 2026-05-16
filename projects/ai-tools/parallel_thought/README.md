# Parallel Thought Synthesis System

A system that queries multiple AI models in parallel via OpenRouter and synthesizes their responses using various strategies.

## Features

- **Parallel Model Querying**: Send the same prompt to multiple models simultaneously
- **Multiple Synthesis Strategies**:
  - `weighted_consensus` - Weighted merge of top responses
  - `contrarian_scoring` - Score against consensus for unique insights
  - `best_score` - Select the highest-scoring response
  - `vote` - Vote on common actions/steps
  - `contrast` - Show contrasts between different models
- **Response Caching**: Avoid re-querying the same prompts
- **Confidence Scoring**: Calculate confidence based on response quality
- **Hermes Agent Integration**: Use with agentic planning workflows

## Installation

```bash
cd parallel_thought
pip install -e .
```

## Usage

### CLI

```bash
# Query multiple models
parallel-thought query "Design a scalable microservices architecture"

# Generate a plan
parallel-thought plan "Build a web app that analyzes financial data"

# List available models
parallel-thought models
```

### Python API

```python
import asyncio
from parallel_thought import ParallelThoughtSynthesizer, SynthesisStrategy

async def main():
    synthesizer = ParallelThoughtSynthesizer()
    
    # Query models in parallel
    responses = await synthesizer.dispatch_thoughts(
        "Design a scalable microservices architecture"
    )
    
    # Synthesize results
    result = synthesizer.synthesize(
        responses=responses,
        agent_own_idea="Start with architecture diagram",
        strategy=SynthesisStrategy.WEIGHTED_CONSENSUS
    )
    
    print(result["synthesized"])

asyncio.run(main())
```

### With Hermes Agent

```python
import asyncio
from parallel_thought import ParallelThinkingAgent

async def main():
    agent = ParallelThinkingAgent()
    result = await agent.plan(
        goal="Build a web app that analyzes financial data",
        context="Using Python, FastAPI, and machine learning"
    )
    print(result.plan)

asyncio.run(main())
```

## Configuration

Set your OpenRouter API key:

```bash
export OPENROUTER_API_KEY="your-key-here"
```

Or create a file at `c:\Users\wifik\Downloads\open_router_key.txt` with your key.

## Models

Default models include:
- `mixtral-8x7b-instruct-v0.1` - Strong reasoning
- `llama3.1-405b-instruct` - Very strong but slower
- `llama3.1-8B-Instruct` - Fast, decent
- `mistral-7b-instruct-v0.2` - Good balance
- `gpt-4o-mini` - Fast, cheap, good
- `claude-3-5-sonnet` - Excellent reasoning

## License

MIT