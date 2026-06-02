# Quantization

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# Quantization Guide

## Contents
- Quantization methods comparison
- AWQ setup and usage
- GPTQ setup and usage
- FP8 quantization (H100)
- Model preparation
- Accuracy vs compression trade-offs

## Quantization methods comparison

| Method | Compression | Accuracy Loss | Speed | Best For |
|--------|-------------|---------------|-------|----------|
| **AWQ** | 4-bit (75%) | <1% | Fast | 70B models, production |
| **GPTQ** | 4-bit (75%) | 1-2% | Fast | Wide model support |
| **FP8** | 8-bit (50%) | <0.5% | Fastest | H100 GPUs only |
| **SqueezeLLM** | 3-4 bit (75-80%) | 2-3% | Medium | Extreme compression |

**Recommendation**:
- **Production**: Use AWQ for 70B models
- **H100 GPUs**: Use FP8 for best speed
- **Maximum compatibility**: Use GPTQ
- **Extreme compression**: Use SqueezeLLM

## AWQ setup and usage

**AWQ** (Activation-aware Weight Quantization) achieves best accuracy at 4-bit.

**Step 1: Find pre-quantized model**

Search HuggingFace for AWQ models:
```bash
# Example: TheBloke/Llama-2-70B-AWQ
# Example: TheBloke/Mixtral-8x7B-Instruct-v0.1-AWQ
```

**Step 2: Launch with AWQ**

```bash
vllm serve TheBloke/Llama-2-70B-AWQ \
  --quantization awq \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.95
```

**Memory savings**:
```
Llama 2 70B fp16: 140GB VRAM (4x A100 needed)
Llama 2 70B AWQ: 35GB VRAM (1x A100 40GB)
= 4x memory reduction
```

**Step 3: Verify performance**

Test that outputs are acceptable:
```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")

# Test complex reasoning
response = client.chat.completions.create(
    model="TheBloke/Llama-2-70B-AWQ",
    messages=[{"role": "user", "content": "Explain quantum entanglement"}]
)

print(response.choices[0].message.content)
# Verify quality matches your requirements
```

**Quantize your own model** (requires GPU with 80GB+ VRAM):

```python
from awq import AutoAWQForCausalLM
from transformers import AutoTokenizer

model_path = "meta-llama/Llama-2-70b-hf"
quant_path = "llama-2-70b-awq"

# Load model
model = AutoAWQForCausalLM.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)

# Quantize
quant_config = {"zero_point": True, "q_group_size": 128, "w_bit": 4}
model.quantize(tokenizer, quant_config=quant_config)

# Save
model.save_quantized(quant_path)
tokenizer.save_pretrained(quant_path)
```

## GPTQ setup and usage

**GPTQ** has widest model support and good compression.

**Step 1: Find GPTQ model**

```bash
# Example: TheBloke/Llama-2-13B-GPTQ
# Example: TheBloke/CodeLlama-34B-GPTQ
```

**Step 2: Launch with GPTQ**

```bash
vllm serve TheBloke/Llama-2-13B-GPTQ \
  --quantization gptq \
  --dtype float16
```

**GPTQ configuration options**:
```bash
# Specify GPTQ parameters if needed
vllm serve MODEL \
  --quantization gptq \
  --gptq-act-order \  # Activation ordering
  --dtype float16
```

**Quantize your own model**:

```python
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
from transformers import AutoTokenizer

model_name = "meta-llama/Llama-2-13b-hf"
quantized_name = "llama-2-13b-gptq"

# Load model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoGPTQForCausalLM.from_pretrained(model_name, quantize_config)

# Prepare calibration data
calib_data = [...]  # List of sample texts

# Quantize
quantize_config = BaseQuantizeConfig(
    bits=4,
    group_size=128,
    desc_act=True
)
model.quantize(calib_data)

# Save
model.save_quantized(quantized_name)
```

## FP8 quantization (H100)

**FP8** (8-bit floating point) offers best speed on H100 GPUs with minimal accuracy loss.

**Requirements**:
- H100 or H800 GPU
- CUDA 12.3+ (12.8 recommended)
- Hopper architecture support

**Step 1: Enable FP8**

```bash
vllm serve meta-llama/Llama-3-70B-Instruct \
  --quantization fp8 \
  --tensor-parallel-size 2
```

**Performance gains on H100**:
```
fp16: 180 tokens/sec
FP8: 320 tokens/sec
= 1.8x speedup
```

**Step 2: Verify accuracy**

FP8 typically has <0.5% accuracy degradation:
```python
# Run evaluation suite
# Compare FP8 vs FP16 on your tasks
# Verify acceptable accuracy
```

**Dynamic FP8 quantization** (no pre-quantized model needed):

```bash
# vLLM automatically quantizes at runtime
vllm serve MODEL --quantization fp8
# No model preparation required
```

## Model preparation

**Pre-quantized models (easiest)**:

1. Search HuggingFace: `[model name] AWQ` or `[model name] GPTQ`
2. Download or use directly: `TheBloke/[Model]-AWQ`
3. Launch with appropriate `--quantization` flag

**Quantize your own model**:

**AWQ**:
```bash
# Install AutoAWQ
pip install autoawq

# Run quantization script
python quantize_awq.py --model MODEL --output OUTPUT
```

**GPTQ**:
```bash
# Install AutoGPTQ
pip install auto-gptq

# Run quantization script
python quantize_gptq.py --model MODEL --output OUTPUT
```

**Calibration data**:
- Use 128-512 diverse examples from target domain
- Representative of production inputs
- Higher quality calibration = better accuracy

## Accuracy vs compression trade-offs

**Empirical results** (Llama 2 70B on MMLU benchmark):

| Quantization | Accuracy | Memory | Speed | Production-Ready |
|--------------|----------|--------|-------|------------------|
| FP16 (baseline) | 100% | 140GB | 1.0x | ✅ (if memory available) |
| FP8 | 99.5% | 70GB | 1.8x | ✅ (H100 only) |
| AWQ 4-bit | 99.0% | 35GB | 1.5x | ✅ (best for 70B) |
| GPTQ 4-bit | 98.5% | 35GB | 1.5x | ✅ (good compatibility) |
| SqueezeLLM 3-bit | 96.0% | 26GB | 1.3x | ⚠️ (check accuracy) |

**When to use each**:

**No quantization (FP16)**:
- Have sufficient GPU memory
- Need absolute best accuracy
- Model <13B parameters

**FP8**:
- Using H100/H800 GPUs
- Need best speed with minimal accuracy loss
- Production deployment

**AWQ 4-bit**:
- Need to fit 70B model in 40GB GPU
- Production deployment
- <1% accuracy loss acceptable

**GPTQ 4-bit**:
- Wide model support needed
- Not on H100 (use FP8 instead)
- 1-2% accuracy loss acceptable

**Testing strategy**:

1. **Baseline**: Measure FP16 accuracy on your evaluation set
2. **Quantize**: Create quantized version
3. **Evaluate**: Compare quantized vs baseline on same tasks
4. **Decide**: Accept if degradation < threshold (typically 1-2%)

**Example evaluation**:
```python
from evaluate import load_evaluation_suite

# Run on FP16 baseline
baseline_score = evaluate(model_fp16, eval_suite)

# Run on quantized
quant_score = evaluate(model_awq, eval_suite)

# Compare
degradation = (baseline_score - quant_score) / baseline_score * 100
print(f"Accuracy degradation: {degradation:.2f}%")

# Decision
if degradation < 1.0:
    print("✅ Quantization acceptable for production")
else:
    print("⚠️ Review accuracy loss")
```

LINKS:
[[Architecture]]
[[Claude]]
[[Testing]]
[[User]]
[[3D Scene]]
[[Action]]
[[Advanced Usage]]
[[Aged Academia]]
[[Airbnb]]
[[Airtable]]
[[Analysis Framework]]
[[Analysis Modules]]
[[Animation]]
[[Animations]]
[[Animation Design Thinking]]
[[Api Endpoints]]
[[Api Evaluation]]
[[Apple]]
[[Artifacts]]
[[Attribution]]
[[Audio Reactive]]
[[Autoreason Methodology]]
[[Auto Selection]]
[[Base Prompt]]
[[Benchmark Guide]]
[[Bento Grid]]
[[Binary Comparison]]
[[Block Types]]
[[Blueprint]]
[[Bmw]]
[[Bold Graphic]]
[[Bridge]]
[[Bug Report]]
[[Cal]]
[[Camera And 3D]]
[[Chalk]]
[[Chalkboard]]
[[Character Template]]
[[Checklists]]
[[Cinematic]]
[[Circular Flow]]
[[Citation Workflow]]
[[Ci Troubleshooting]]
[[Clay]]
[[Claymation]]
[[Clickhouse]]
[[Cohere]]
[[Coinbase]]
[[Colors]]
[[Color Systems]]
[[Comic Strip]]
[[Comparison Matrix]]
[[Composio]]
[[Composition]]
[[Concept Story]]
[[Configuration]]
[[Context Budget Discipline]]
[[Conventional Commits]]
[[Core Api]]
[[Corporate Memphis]]
[[Craft Handmade]]
[[Cursor]]
[[Custom Tasks]]
[[Cyberpunk Neon]]
[[Dark Mode]]
[[Dashboard]]
[[Dat Scripting]]
[[Decorations]]
[[Dense]]
[[Dense Modules]]
[[Description]]
[[Distributed Eval]]
[[Dogfood Report Template]]
[[Dramatic]]
[[Editing]]
[[Editorial]]
[[Effects]]
[[Elegant]]
[[Elevenlabs]]
[[Energetic]]
[[Equations]]
[[Examples]]
[[Experiment Patterns]]
[[Expo]]
[[Export Pipeline]]
[[External Data]]
[[Failures]]
[[Fantasy Animation]]
[[Feature Request]]
[[Figma]]
[[Flat]]
[[Flat Doodle]]
[[Formatting]]
[[Four Panel]]
[[Framer]]
[[Full Prompt Library]]
[[Funnel]]
[[Gates Taxonomy]]
[[Geometry Comp]]
[[Github Api Cheatsheet]]
[[Glsl]]
[[Gmail Search Syntax]]
[[Graphs And Data]]
[[Hand Drawn Edu]]
[[Hashicorp]]
[[Heuristics]]
[[Hierarchical Layers]]
[[Hub Discovery]]
[[Hub Spoke]]
[[Human Evaluation]]
[[Ibm]]
[[Iceberg]]
[[Ikea Manual]]
[[Ink Brush]]
[[Ink Notes]]
[[Inputs]]
[[Integrations]]
[[Interaction]]
[[Intercom]]
[[Intuition Machine]]
[[Isometric Map]]
[[Issue Taxonomy]]
[[Jailbreak Templates]]
[[Jigsaw]]
[[Kawaii]]
[[Knolling]]
[[Kraken]]
[[Layout Compositor]]
[[Lego Brick]]
[[Ligne Claire]]
[[Linear.App]]
[[Linear Progression]]
[[Lovable]]
[[Macaron]]
[[Manga]]
[[Mcp Tools]]
[[Message Composition]]
[[Methods Guide]]
[[Midi Osc]]
[[Minimal]]
[[Minimalist]]
[[Minimax]]
[[Mintlify]]
[[Miro]]
[[Mistral.Ai]]
[[Mixed]]
[[Mobjects]]
[[Modules]]
[[Mongodb]]
[[Mono Ink]]
[[Morandi Journal]]
[[Nature]]
[[Neon]]
[[Network Patterns]]
[[Neutral]]
[[Notion]]
[[Nvidia]]
[[Official Cli]]
[[Ohmsha]]
[[Ohmsha Guide]]
[[Ollama]]
[[Opencode.Ai]]
[[Operators]]
[[Operator Tips]]
[[Optimization]]
[[Optimizers]]
[[Origami]]
[[Output Formats]]
[[Palettes]]
[[Panel Ui]]
[[Paper Explainer]]
[[Paper Types]]
[[Partial Workflows]]
[[Particles]]
[[Patterns]]
[[Periodic Table]]
[[Pinterest]]
[[Pitfalls]]
[[Pixel Art]]
[[Playful]]
[[Pmb Codex Lane Prompt]]
[[Pop Laboratory]]
[[Port Notes]]
[[Postfx]]
[[Posthog]]
[[Pptxgenjs]]
[[Production Quality]]
[[Projection Mapping]]
[[Prompt Construction]]
[[Pr Body Bugfix]]
[[Pr Body Feature]]
[[Python Api]]
[[Raycast]]
[[Realistic]]
[[Refusal Detection]]
[[Rendering]]
[[Replicate]]
[[Replicator]]
[[Resend]]
[[Rest Api]]
[[Retro]]
[[Retro Pop Grid]]
[[Reviewer Guidelines]]
[[Review Output Template]]
[[Revolut]]
[[Romantic]]
[[Runwayml]]
[[Sanity]]
[[Scenes]]
[[Scene Planning]]
[[Scientific]]
[[Screen Print]]
[[Sentry]]
[[Server]]
[[Server Deployment]]
[[Shaders]]
[[Shapes And Geometry]]
[[Shoujo]]
[[Sketch]]
[[Sketch Notes]]
[[Skill]]
[[Sources]]
[[Spacex]]
[[Splash]]
[[Spotify]]
[[Standard]]
[[Starter]]
[[Storyboard Template]]
[[Storybook Watercolor]]
[[Story Mountain]]
[[Stripe]]
[[Structural Breakdown]]
[[Structured Content Template]]
[[Styles]]
[[Style Presets]]
[[Subway Map]]
[[Supabase]]
[[Superhuman]]
[[Sweeps]]
[[System]]
[[Technical Schematic]]
[[Template Integrity]]
[[Together.Ai]]
[[Tree Branching]]
[[Troubleshooting]]
[[Typography]]
[[Uber]]
[[Ui Wireframe]]
[[Updaters And Trackers]]
[[Usage]]
[[Vector Illustration]]
[[Venn Diagram]]
[[Vercel]]
[[Vintage]]
[[Visual Design]]
[[Visual Effects]]
[[Voltagent]]
[[Warm]]
[[Warp]]
[[Watercolor]]
[[Webflow]]
[[Webgl And 3D]]
[[Webtoon]]
[[Winding Roadmap]]
[[Wise]]
[[Workflow]]
[[Workflow Format]]
[[Writing Guide]]
[[Wuxia]]
[[X.Ai]]
[[Zapier]]
[[Memory]]
