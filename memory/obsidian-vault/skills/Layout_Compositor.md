# Layout Compositor

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# Layout Compositor Reference

Patterns for building modular multi-panel grids — useful for HUD interfaces, data dashboards, and multi-source visual composites.

## Layout Approaches

| Approach | Best For | Notes |
|----------|----------|-------|
| `layoutTOP` | Fixed grid, quick setup | GPU, simple tiling |
| Container COMP + `overTOP` | Full control, mixed-size panels | More setup, very flexible |
| GLSL compositor | Procedural / BSP-style | Most powerful, more complex |

---

## layoutTOP

Built-in grid compositor — fastest path for uniform tile grids.

```python
layout = root.create(layoutTOP, 'layout1')
layout.par.resolutionw = 1920
layout.par.resolutionh = 1080
layout.par.cols = 3
layout.par.rows = 2
layout.par.gap = 4
```

Connect inputs (up to cols×rows):
```python
layout.inputConnectors[0].connect(op('panel_radar'))
layout.inputConnectors[1].connect(op('panel_wave'))
layout.inputConnectors[2].connect(op('panel_data'))
```

**Variable-width columns:** Not directly supported. Use overTOP approach for non-uniform grids.

---

## Container COMP Grid

Build each element as its own `containerCOMP`. Compose with `overTOP`:

```python
def create_panel(root, name, width, height, x=0, y=0):
    panel = root.create(containerCOMP, name)
    panel.par.w = width
    panel.par.h = height
    panel.viewer = True
    return panel

# Composite with overTOP chain
over1 = root.create(overTOP, 'over1')
over1.inputConnectors[0].connect(panel_radar)
over1.inputConnectors[1].connect(panel_wave)
over1.par.topx2 = 0
over1.par.topy2 = 512
```

**Tip:** Use a `resolutionTOP` before each `overTOP` input if panels are different sizes.

---

## Panel Dividers (GLSL)

```glsl
out vec4 fragColor;
uniform vec2 uGridDivisions;   // e.g. vec2(3, 2) for 3 cols, 2 rows
uniform float uLineWidth;      // pixels
uniform vec4 uLineColor;       // e.g. vec4(0.0, 1.0, 0.8, 0.6) for cyan

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 uv = vUV.st;
    vec4 bg = texture(sTD2DInputs[0], uv);

    float lineW = uLineWidth / res.x;
    float lineH = uLineWidth / res.y;

    float vDiv = 0.0;
    for (float i = 1.0; i < uGridDivisions.x; i++) {
        float x = i / uGridDivisions.x;
        vDiv = max(vDiv, step(abs(uv.x - x), lineW));
    }

    float hDiv = 0.0;
    for (float i = 1.0; i < uGridDivisions.y; i++) {
        float y = i / uGridDivisions.y;
        hDiv = max(hDiv, step(abs(uv.y - y), lineH));
    }

    float line = max(vDiv, hDiv);
    vec4 result = mix(bg, uLineColor, line * uLineColor.a);
    fragColor = TDOutputSwizzle(result);
}
```

---

## Element Library Pattern

Each visual element lives in its own `baseCOMP` as a reusable `.tox`:

### Standard Interface
```
inputs:
  - in_audio   (CHOP)  — audio envelope / beat data
  - in_data    (CHOP)  — optional data stream
  - in_control (CHOP)  — intensity, color, speed params

outputs:
  - out_top    (TOP)   — rendered element
```

### Network Structure
```
/project1/
  audio_bus/          ← all audio analysis (see audio-reactive.md)
  elements/
    elem_radar/       ← baseCOMP with out_top
    elem_wave/
    elem_data/
  compositor/
    layout1           ← layoutTOP or overTOP chain
    dividers1         ← GLSL divider lines
    postfx/           ← bloom → chrom → CRT stack (see postfx.md)
      null_out        ← final output
  output/
    windowCOMP        ← full-screen output
```

**Key principle:** Elements don't know about each other. The compositor assembles them. Audio bus is referenced by all elements but lives separately.

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
