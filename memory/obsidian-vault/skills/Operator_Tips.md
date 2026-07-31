# Operator Tips

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# Operator Tips

## Wireframe Rendering Pattern

Reusable setup for wireframe geometry on black background:

```python
# 1. Material
mat = root.create(wireframeMAT, 'wire_mat')
mat.par.colorr = 1.0; mat.par.colorg = 0.0; mat.par.colorb = 0.0
mat.par.linewidth = 3

# 2. Geometry COMP
geo = root.create(geometryCOMP, 'my_geo')
geo.par.rx.expr = 'absTime.seconds * 30'
geo.par.ry.expr = 'absTime.seconds * 45'
geo.par.material = mat.path  # NOTE: 'material' not 'mat'

# 3. Shape inside the geo
box = geo.create(boxSOP, 'cube')
box.par.sizex = 1.5; box.par.sizey = 1.5; box.par.sizez = 1.5

# 4. Camera
cam = root.create(cameraCOMP, 'cam1')
cam.par.tx = 0; cam.par.ty = 0; cam.par.tz = 4; cam.par.fov = 45

# 5. Render TOP
render = root.create(renderTOP, 'render1')
render.par.outputresolution = 'custom'
render.par.resolutionw = 1280; render.par.resolutionh = 720
render.par.bgcolorr = 0; render.par.bgcolorg = 0; render.par.bgcolorb = 0
render.par.camera = cam.path
render.par.geometry = geo.path

# 6. Output null
out = root.create(nullTOP, 'out1')
out.inputConnectors[0].connect(render.outputConnectors[0])
```

**Key rules:**
- Class names: `wireframeMAT` not `wireframeMat` (all-caps suffix)
- Geometry SOPs/POPs go INSIDE the geo comp
- Material: `geo.par.material` not `geo.par.mat`
- Render geometry: `render.par.geometry = geo.path` (string path)
- `wireframeMAT.par.wireframemode = 'topology'` for clean wireframe (vs `'tesselated'` for triangle edges)
- Alternative: Use `renderTOP.par.overridemat` instead of per-geo material

## Feedback TOP

### Basic Structure

```
input (initial state) ──┐
                        ├──→ feedback_top ──→ processing ──→ null_out
                        │                                        ↑
                        └── par.top = 'null_out' ────────────────┘
```

### Setup Pattern

```python
# 1. Processing chain
glsl = root.create(glslTOP, 'sim')
null_out = root.create(nullTOP, 'null_out')
glsl.outputConnectors[0].connect(null_out.inputConnectors[0])

# 2. Feedback referencing null_out
feedback = root.create(feedbackTOP, 'feedback')
feedback.par.top = 'null_out'

# 3. Black initial state
const_init = root.create(constantTOP, 'const_init')
const_init.par.colorr = 0; const_init.par.colorg = 0; const_init.par.colorb = 0

# 4. Wire: initial → feedback, feedback → processing
feedback.inputConnectors[0].connect(const_init)
glsl.inputConnectors[0].connect(feedback)

# 5. Reset to apply initial state
feedback.par.resetpulse.pulse()
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Not enough sources specified" | No input connected | Connect initial state TOP |
| Unexpected initial pattern | Wrong initial state | Use Constant TOP (black) |

### Tips

1. Use float format for simulations: `glsl.par.format = 'rgba32float'`
2. Reset after setup: `feedback.par.resetpulse.pulse()`
3. Match resolutions — feedback, processing, and initial state must match
4. Soft boundary prevents edge artifacts:
   ```glsl
   float edge = 3.0 * texel.x;
   float bx = smoothstep(0.0, edge, uv.x) * smoothstep(0.0, edge, 1.0 - uv.x);
   float by = smoothstep(0.0, edge, uv.y) * smoothstep(0.0, edge, 1.0 - uv.y);
   value *= bx * by;
   ```

### Use Cases
- **Wave Simulation** — R=height, G=velocity, black initial state
- **Cellular Automata** — white=alive, black=dead, random noise initial state
- **Trail / Motion Blur** — blend current frame with feedback, black initial

LINKS:
[[Architecture]]
[[Cg 8 Operator Coevolution]]
[[Claude]]
[[Operator Rules]]
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
