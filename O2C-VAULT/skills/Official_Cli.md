# Official Cli

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# comfy-cli Command Reference

Official CLI from [Comfy-Org/comfy-cli](https://github.com/Comfy-Org/comfy-cli).
Docs: https://docs.comfy.org/comfy-cli/getting-started

## Installation

Order of preference:

```bash
pipx install comfy-cli            # recommended (isolated env)
uvx --from comfy-cli comfy --help # zero-install via uv
pip install --user comfy-cli      # fallback
```

The skill's `comfyui_setup.sh` picks the best available method.

First run may prompt for analytics. Disable non-interactively:
```bash
comfy --skip-prompt tracking disable
```

## Global Options

| Option | Description |
|--------|-------------|
| `--workspace <path>` | Target a specific ComfyUI workspace |
| `--recent` | Use most recently used workspace |
| `--here` | Use current directory as workspace |
| `--skip-prompt` | No interactive prompts (use defaults) |
| `-v` / `--version` | Print version |

Workspace resolution priority:
1. `--workspace` (explicit path)
2. `--recent` (from config)
3. `--here` (cwd)
4. `comfy set-default` path
5. Most recently used
6. `~/comfy/ComfyUI` (Linux) or `~/Documents/comfy/ComfyUI` (macOS/Win)

## Lifecycle Commands

### `comfy install`

Download and install ComfyUI + ComfyUI-Manager.

```bash
comfy install                    # interactive GPU selection
comfy install --nvidia
comfy install --amd              # ROCm (Linux)
comfy install --m-series         # Apple Silicon (MPS)
comfy install --cpu              # CPU only (slow)
comfy install --fast-deps        # use uv for deps
comfy install --skip-manager     # skip ComfyUI-Manager
```

| Option | Description |
|--------|-------------|
| `--nvidia` / `--amd` / `--m-series` / `--cpu` | GPU type |
| `--cuda-version` | 11.8, 12.1, 12.4, 12.6, 12.8, 12.9, 13.0 |
| `--rocm-version` | 6.1, 6.2, 6.3, 7.0, 7.1 |
| `--fast-deps` | uv-based dependency resolution |
| `--skip-manager` | Don't install ComfyUI-Manager |
| `--skip-torch-or-directml` | Skip PyTorch install |
| `--version <ver>` | `0.2.0`, `latest`, `nightly` |
| `--commit <hash>` | Install specific commit |
| `--pr "#1234"` | Install from a PR |
| `--restore` | Restore deps for existing install |

### `comfy launch`

```bash
comfy launch                                   # foreground :8188
comfy launch --background                      # background daemon
comfy launch -- --listen 0.0.0.0               # LAN-accessible
comfy launch -- --port 8190                    # custom port
comfy launch -- --cpu                          # force CPU mode
comfy launch -- --lowvram                      # 6 GB cards
comfy launch --background -- --listen 0.0.0.0 --port 8190
```

Common extra args after `--`: `--listen`, `--port`, `--cpu`, `--lowvram`,
`--novram`, `--fp16-vae`, `--force-fp32`, `--disable-cuda-malloc`.

### `comfy stop`

```bash
comfy stop
```

### `comfy run`

Submit a raw workflow JSON to a running server. **Limited** — no parameter
injection, no structured output download. For agents, use
`scripts/run_workflow.py` instead.

```bash
comfy run --workflow workflow_api.json
comfy run --workflow workflow_api.json --host 10.0.0.5 --port 8188
comfy run --workflow workflow_api.json --timeout 300 --wait
```

### `comfy which`

```bash
comfy which          # show targeted workspace
comfy --recent which
```

### `comfy set-default`

```bash
comfy set-default /path/to/ComfyUI
comfy set-default /path/to/ComfyUI --launch-extras="--listen 0.0.0.0"
```

### `comfy update`

```bash
comfy update               # update ComfyUI core
comfy node update all      # update all custom nodes
```

---

## `comfy node` — Custom Node Management

All node operations use ComfyUI-Manager (`cm-cli`) under the hood.

```bash
comfy node show installed              # list installed
comfy node show enabled                # list enabled
comfy node show all                    # all available in registry
comfy node simple-show installed       # compact list

comfy node install comfyui-impact-pack
comfy node install <name> --uv-compile # ComfyUI-Manager v4.1+ unified resolver
comfy node uninstall <name>
comfy node update <name> | all
comfy node enable <name>
comfy node disable <name>
comfy node fix <name>                  # fix broken deps

comfy node install-deps --workflow=workflow.json
comfy node deps-in-workflow --workflow=w.json --output=deps.json

comfy node save-snapshot
comfy node restore-snapshot <file>

comfy node bisect start                # binary-search a culprit node
comfy node bisect good
comfy node bisect bad
comfy node bisect reset
```

### Dependency Resolution Options

| Flag | Description |
|------|-------------|
| `--fast-deps` | comfy-cli built-in uv resolver |
| `--uv-compile` | ComfyUI-Manager v4.1+ unified resolver (recommended) |
| `--no-deps` | Skip dep installation |

Make `uv-compile` default: `comfy manager uv-compile-default true`

---

## `comfy model` — Model Management

```bash
comfy model list
comfy model list --relative-path models/checkpoints

comfy model download --url <URL>
comfy model download --url <URL> --relative-path models/loras
comfy model download --url <URL> --filename custom_name.safetensors

comfy model remove                     # interactive
comfy model remove --relative-path models/checkpoints --model-names "model.safetensors"
```

| Option | Description |
|--------|-------------|
| `--url` | Download URL (CivitAI, HuggingFace, direct) |
| `--relative-path` | Subdirectory under workspace (e.g. `models/checkpoints`) |
| `--filename` | Custom save filename |
| `--set-civitai-api-token` | Persist CivitAI token |
| `--set-hf-api-token` | Persist HuggingFace token |
| `--downloader` | `httpx` (default) or `aria2` |

Standard model directories:
```
ComfyUI/models/
├── checkpoints/        # Full model files
├── loras/              # LoRA adapters
├── vae/                # VAE models
├── controlnet/         # ControlNet models
├── clip/               # CLIP / T5 text encoders
├── clip_vision/        # CLIP vision encoders
├── upscale_models/     # ESRGAN / SwinIR / etc.
├── embeddings/         # Textual inversion embeddings
├── unet/               # Standalone UNet weights
├── diffusion_models/   # Flux / SD3 / Wan diffusion models
├── animatediff_models/ # AnimateDiff motion modules
├── ipadapter/          # IPAdapter weights
└── style_models/       # Style adapters
```

---

## `comfy manager` — ComfyUI-Manager Settings

```bash
comfy manager disable               # disable Manager completely
comfy manager enable-gui            # enable new GUI
comfy manager disable-gui           # API-only
comfy manager enable-legacy-gui     # legacy GUI
comfy manager uv-compile-default true   # make --uv-compile the default
comfy manager clear                 # clear startup action
```

---

## `comfy pr-cache` — Frontend PR Cache

```bash
comfy pr-cache list
comfy pr-cache clean
comfy pr-cache clean 456
```

Cache expires after 7 days; max 10 builds.

---

## Configuration

| OS | Path |
|----|------|
| Linux | `~/.config/comfy-cli/config.ini` |
| macOS | `~/Library/Application Support/comfy-cli/config.ini` |
| Windows | `~/AppData/Local/comfy-cli/config.ini` |

Stores: default workspace, recent workspace, background server PID, API
tokens, manager GUI mode, launch extras.

## Discovery

Custom-node registry:
- https://registry.comfy.org/

Model browsers:
- https://huggingface.co/models
- https://civitai.com (NSFW; requires API token for many)
- https://comfyworkflows.com (community workflows)

LINKS:
[[Architecture]]
[[Agents]]
[[Claude]]
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
[[Quantization]]
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
[[Loader]]
