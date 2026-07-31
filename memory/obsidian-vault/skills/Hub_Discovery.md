# Hub Discovery

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# Hugging Face URL Workflows for llama.cpp

Use URL-only workflows first. Do not require `hf` or API clients just to find GGUF files, choose a quant, or build a `llama-server` command.

## Core URLs

```text
Search:
https://huggingface.co/models?apps=llama.cpp&sort=trending

Search with text:
https://huggingface.co/models?search=<term>&apps=llama.cpp&sort=trending

Search with size bounds:
https://huggingface.co/models?search=<term>&apps=llama.cpp&num_parameters=min:0,max:24B&sort=trending

Repo local-app view:
https://huggingface.co/<repo>?local-app=llama.cpp

Repo tree API:
https://huggingface.co/api/models/<repo>/tree/main?recursive=true

Repo file tree:
https://huggingface.co/<repo>/tree/main
```

## 1. Search for llama.cpp-compatible models

Start from the models page with `apps=llama.cpp`.

Use:

- `search=<term>` for model family names such as `Qwen`, `Gemma`, `Phi`, or `Mistral`
- `num_parameters=min:0,max:24B` or similar if the user has hardware limits
- `sort=trending` when the user wants popular repos right now

Do not start with random GGUF repos if the user has not chosen a model family yet. Search first, shortlist second.

Example: https://huggingface.co/models?search=Qwen&apps=llama.cpp&num_parameters=min:0,max:24B&sort=trending

## 2. Use the local-app page for the recommended quant

Open:

```text
https://huggingface.co/<repo>?local-app=llama.cpp
```

Extract, in order:

1. The exact `Use this model` snippet, if it is visible as text
2. The `Hardware compatibility` section from the fetched page text or HTML:
   - quant label
   - file size
   - bit-depth grouping
3. Any extra launch flags shown in the snippet, such as `--jinja`

Treat the HF local-app snippet as the source of truth when it is visible.

Do this by reading the URL itself, not by assuming the UI rendered in a browser. If the fetched page source does not expose `Hardware compatibility`, say that the section was not text-visible and fall back to the tree API plus generic guidance from `quantization.md`.

## 3. Confirm exact files from the tree API

Open:

```text
https://huggingface.co/api/models/<repo>/tree/main?recursive=true
```

Treat the JSON response as the source of truth for repo inventory.

Keep entries where:

- `type` is `file`
- `path` ends with `.gguf`

Use these fields:

- `path` for the filename and subdirectory
- `size` for the byte size
- optionally `lfs.size` to confirm the LFS payload size

Separate files into:

- quantized single-file checkpoints, for example `Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`
- projector weights, usually `mmproj-*.gguf`
- BF16 shard files, usually under `BF16/`
- everything else

Ignore unless the user asks:

- `README.md`
- imatrix or calibration blobs

Use `https://huggingface.co/<repo>/tree/main` only as a human fallback if the API endpoint fails or the user wants the web view.

## 4. Build the command

Preferred order:

1. Copy the exact HF snippet from the local-app page
2. If the page gives a clean quant label, use shorthand selection:

```bash
llama-server -hf <repo>:<QUANT>
```

3. If you need an exact file from the tree API, use the file-specific form:

```bash
llama-server --hf-repo <repo> --hf-file <filename.gguf>
```

4. For CLI usage instead of a server, use:

```bash
llama-cli -hf <repo>:<QUANT>
```

Use the exact-file form when the repo uses custom labels or nonstandard naming that could make `:<QUANT>` ambiguous.

## 5. Example: `unsloth/Qwen3.6-35B-A3B-GGUF`

Use these URLs:

```text
https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF?local-app=llama.cpp
https://huggingface.co/api/models/unsloth/Qwen3.6-35B-A3B-GGUF/tree/main?recursive=true
https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF/tree/main
```

On the local-app page, the hardware compatibility section can expose entries such as:

- `UD-IQ4_XS` - 17.7 GB
- `UD-Q4_K_S` - 20.9 GB
- `UD-Q4_K_M` - 22.1 GB
- `UD-Q5_K_M` - 26.5 GB
- `UD-Q6_K` - 29.3 GB
- `Q8_0` - 36.9 GB

On the tree API, you can confirm exact filenames such as:

- `Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`
- `Qwen3.6-35B-A3B-UD-Q5_K_M.gguf`
- `Qwen3.6-35B-A3B-UD-Q6_K.gguf`
- `Qwen3.6-35B-A3B-Q8_0.gguf`
- `mmproj-F16.gguf`

Good final output for this repo:

```text
Repo: unsloth/Qwen3.6-35B-A3B-GGUF
Recommended quant from HF: UD-Q4_K_M (22.1 GB)
llama-server: llama-server --hf-repo unsloth/Qwen3.6-35B-A3B-GGUF --hf-file Qwen3.6-35B-A3B-UD-Q4_K_M.gguf
Other GGUFs:
- Qwen3.6-35B-A3B-UD-Q5_K_M.gguf - 26.5 GB
- Qwen3.6-35B-A3B-UD-Q6_K.gguf - 29.3 GB
- Qwen3.6-35B-A3B-Q8_0.gguf - 36.9 GB
Projector:
- mmproj-F16.gguf - 899 MB
```

## Notes

- Repo-specific quant labels matter. Do not rewrite `UD-Q4_K_M` to `Q4_K_M` unless the page itself does.
- `mmproj` files are projector weights for multimodal models, not the main language model checkpoint.
- If the HF hardware compatibility panel is missing because the user has no hardware profile configured, or because the fetched page source did not expose it, still use the tree API plus generic quant guidance from `quantization.md`.
- If the repo already has GGUFs, do not jump straight to conversion workflows.

LINKS:
[[Architecture]]
[[Claude]]
[[Readme]]
[[User]]
[[Tradovate Api Discovery 20260531]]
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
