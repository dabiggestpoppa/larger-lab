# Oransim - Causal Marketing Simulation Engine

Predict campaign ROI before spending. Agent-based causal simulation with counterfactual reasoning.

**Use Oransim when:**
- Planning a marketing campaign and want to predict ROI before spending
- Need to compare creative x KOL x budget combinations
- Mid-campaign: want to simulate "what if I swap KOLs / reallocate budget?"
- Post-mortem: want to know "what if we'd chosen a different platform?"
- Building a content lab / agency and need data-driven campaign strategy

**Requires:** Python 3.10+, `oransim` package, `LLM_MODE=mock` works without API key

## Quick Start

```bash
# 1. Navigate to oransim
cd oransim

# 2. Run in mock mode (no API key needed)
$env:LLM_MODE="mock"; python -m uvicorn oransim.api:app --port 8001

# 3. Open frontend
python -m http.server 8090 --directory frontend

# 4. Open http://localhost:8090 -> click "Predict"
```

## API Usage

```bash
# Health check
curl http://localhost:8001/api/health

# Inspect the 64-node causal graph
curl http://localhost:8001/api/graph/inspect

# Run a prediction
curl -X POST http://localhost:8001/api/predict \
  -H "Content-Type: application/json" \
  -d '{"creative": "...", "budget": 50000, "platform": "xhs"}'
```

## Three Core Workflows

### 1. Pre-launch ROI Ranking
Simulate all creative x KOL x budget combinations in 60 seconds. Get P35/P65 confidence bands. Pick top 3 to actually test.

### 2. Mid-campaign Intervention
`do(kol=swap_A_for_B, day=3)` counterfactual rollout in 30 seconds. Shows 14-day path diff with the intervention applied.

### 3. Post-mortem Counterfactual
Load actuals + `do(platform_alloc={xhs: 1.0})`. Get counterfactual ROI curve over the same agent population.

## Architecture

- **World Model** - LightGBM quantile baseline (default) or CausalTransformer (opt-in)
- **Agent Layer** - IPF-scalable agent population with LLM soul personas
- **Causal Engine** - 64-node causal graph + `do()` counterfactuals (Pearl 3-step)
- **Diffusion** - 14-day intervention-aware Hawkes process rollout
- **Frontend** - Browser UI at http://localhost:8090

## Configuration (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MODE` | `mock` | `mock` (free, deterministic) or `api` (real LLM) |
| `LLM_PROVIDER` | `openai` | `openai`, `anthropic`, `gemini`, `qwen` |
| `LLM_API_KEY` | - | API key for real LLM mode |
| `LLM_MODEL` | `gpt-5.4` | Model to use |
| `SOUL_POOL_N` | 100 | Number of LLM personas |
| `POP_SIZE` | 100000 | Agent population size |
| `PORT` | 8001 | Backend port |

## Data Sources (Enterprise)

The OSS ships with a 21k-note demo corpus. Enterprise Edition provides:
- 4.3M+ 小红书 notes (daily refresh)
- 2.1M+ creators across 15 verticals
- 100,000+ surveyed consumer panel

Contact: cto@orannai.com | Live panel: https://datacenter.oran.cn/

## Links

- **GitHub:** https://github.com/OranAi-Ltd/oransim
- **Website:** https://oran.cn/oransim
- **License:** Apache-2.0
