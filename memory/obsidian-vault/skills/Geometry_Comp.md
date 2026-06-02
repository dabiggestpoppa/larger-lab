# Geometry Comp

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# Geometry COMP Reference

## Creating Geometry COMPs

```python
geo = root.create(geometryCOMP, 'geo1')
# Remove default torus
for c in list(geo.children):
    if c.valid: c.destroy()
# Build your shape inside
```

## Correct Pattern (shapes inside geo)

```python
# Create shape INSIDE the geo COMP
box = geo.create(boxSOP, 'cube')
box.par.sizex = 1.5; box.par.sizey = 1.5; box.par.sizez = 1.5

# For POP-based geometry (TD 099), POPs must be inside:
sph = geo.create(spherePOP, 'shape')
out1 = geo.create(outPOP, 'out1')
out1.inputConnectors[0].connect(sph.outputConnectors[0])
```

## DO NOT: Common Mistakes

```python
# BAD: Don't create geometry at parent level and wire into COMP
box = root.create(boxPOP, 'box1')  # ← outside geo, won't render

# BAD: Don't reference parent operators from inside COMP
choptopop1.par.chop = '../null1'  # ← hidden dependency, breaks on move
```

## Instancing

```python
geo.par.instancing = True
geo.par.instanceop = 'sopto1'    # relative path to CHOP/SOP with instance data
geo.par.instancetx = 'tx'
geo.par.instancety = 'ty'
geo.par.instancetz = 'tz'
```

### Instance Attribute Names by OP Type

| OP Type | Attribute Names |
|---------|-----------------|
| CHOP | Channel names: `tx`, `ty`, `tz` |
| SOP/POP | `P(0)`, `P(1)`, `P(2)` for position |
| DAT | Column header names from first row |
| TOP | `r`, `g`, `b`, `a` |

### Mixed Data Sources

```python
geo.par.instanceop = 'pos_chop'       # Position from CHOP
geo.par.instancetx = 'tx'
geo.par.instancecolorop = 'color_top' # Color from TOP
geo.par.instancecolorr = 'r'
```

## Rendering Setup

```python
# Camera
cam = root.create(cameraCOMP, 'cam1')
cam.par.tx = 0; cam.par.ty = 0; cam.par.tz = 4

# Render TOP
render = root.create(renderTOP, 'render1')
render.par.outputresolution = 'custom'
render.par.resolutionw = 1280; render.par.resolutionh = 720
render.par.camera = cam.path
render.par.geometry = geo.path  # accepts path string
```

## POPs vs SOPs for Rendering

In TD 099, `geometryCOMP` renders **POPs** but NOT SOPs. A `boxSOP` inside a geometry COMP is invisible — no errors.

```python
# WRONG — SOPs don't render (invisible, no errors)
box = geo.create(boxSOP, 'cube')       # ✗ invisible

# CORRECT — POPs render
box = geo.create(boxPOP, 'cube')       # ✓ visible
```

| SOP | POP | Notes |
|-----|-----|-------|
| `boxSOP` | `boxPOP` | `sizex/y/z`, `surftype` |
| `sphereSOP` | `spherePOP` | `radx/y/z`, `freq`, `type` (geodesic/grid/sharedpoles/tetrahedron) |
| `torusSOP` | `torusPOP` | TD auto-creates in new geo COMPs |
| `circleSOP` | `circlePOP` | |
| `gridSOP` | `gridPOP` | |
| `tubeSOP` | `tubePOP` | |

New geometry COMPs auto-create: `in1` (inPOP), `out1` (outPOP), `torus1` (torusPOP). Always clean before building.

## Morphing Between Shapes (switchPOP)

```python
sw = geo.create(switchPOP, 'shape_switch')
sw.par.index.expr = 'int(absTime.seconds / 3) % 4'
sw.inputConnectors[0].connect(tetra.outputConnectors[0])  # shape 0
sw.inputConnectors[1].connect(box.outputConnectors[0])    # shape 1
sw.inputConnectors[2].connect(octa.outputConnectors[0])   # shape 2
sw.inputConnectors[3].connect(sphere.outputConnectors[0]) # shape 3

out = geo.create(outPOP, 'out1')
out.inputConnectors[0].connect(sw.outputConnectors[0])
```

`spherePOP.par.type` options: `geodesic`, `grid`, `sharedpoles`, `tetrahedron`. Use `tetrahedron` for platonic solid polyhedra.

## Misc

- `connect()` replaces existing connections — no need to disconnect first
- `project.name` returns the TOE filename, `project.folder` returns the directory

LINKS:
[[Architecture]]
[[Claude]]
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
[[Shared]]
