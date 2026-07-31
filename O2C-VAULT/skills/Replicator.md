# Replicator

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# Replicator COMP Reference

The `replicatorCOMP` clones a template operator N times, driven by a table of data. The fundamental TD pattern for data-driven networks: button grids, scene rosters, dynamic UI, parameter panels per-channel.

For visual instancing (per-pixel/per-render copies), see `geometry-comp.md`. Replicator builds NETWORK NODES; instancing builds RENDER COPIES. Different layer.

---

## Concept

```
[Template OP]                  [Data tableDAT]
       │                              │
       └─────→ replicatorCOMP ←───────┘
                     │
                     ▼
        [N clones], one per data row
        Each clone gets per-row params
```

Edit the template once → all clones inherit. Edit the table → clones add/remove dynamically. Push parameter overrides per-row.

---

## Minimal Setup

```python
# 1. Make a template (the thing to clone)
template = root.create(buttonCOMP, 'btn_template')
template.par.w = 80; template.par.h = 80
template.par.text = 'X'
template.par.bgcolorr = 0.2

# 2. Make a data table (one row per clone)
data = root.create(tableDAT, 'scene_data')
data.appendRow(['name', 'color_r', 'color_g', 'color_b'])
data.appendRow(['Sunset', 1.0, 0.4, 0.0])
data.appendRow(['Midnight', 0.0, 0.1, 0.4])
data.appendRow(['Storm', 0.3, 0.3, 0.5])
data.appendRow(['Forest', 0.0, 0.5, 0.2])

# 3. Replicator — points at template + data
rep = root.create(replicatorCOMP, 'scene_buttons')
rep.par.template = template.path
rep.par.opfromdat = data.path
rep.par.namefromdatname = 'name'        # use 'name' column for clone names
rep.par.incrementalnumbering = False
```

After cooking, the replicator creates 4 child COMPs named `Sunset`, `Midnight`, `Storm`, `Forest` (one per non-header row), each cloned from `btn_template`.

---

## Per-Row Parameter Overrides

The replicator's docked `replicator1_callbacks` DAT lets you customize each clone:

```python
def onReplicate(comp, allOps, newOps, template, master):
    """Called once per replicate cycle. newOps is the list of just-created clones."""
    data = op('scene_data')
    for i, clone in enumerate(newOps):
        row = i + 1                 # +1 to skip header
        clone.par.text = data[row, 'name'].val
        clone.par.bgcolorr = float(data[row, 'color_r'].val)
        clone.par.bgcolorg = float(data[row, 'color_g'].val)
        clone.par.bgcolorb = float(data[row, 'color_b'].val)
    return
```

Or use parameter expressions referencing `digits` (the per-clone index, available as a built-in expression token inside the cloned subtree):

```python
# Inside the template, set a param expression like:
# par.value0.expr = "op('../scene_data')[me.digits + 1, 'value']"
```

`me.digits` resolves to the row index of the current clone. This is the cleanest way for static reference patterns — no callback needed.

---

## Layout: Buttons in a Grid

Drop the replicator inside a `containerCOMP` with auto-layout:

```python
panel = root.create(containerCOMP, 'scene_panel')
panel.par.w = 400; panel.par.h = 100
panel.par.align = 'lefttoright'

# Move the replicator inside
rep.parent = panel.path           # or create rep as a child of panel directly
```

Each clone is a child of the replicator (which itself is a child of the panel). The panel auto-arranges everything.

For a 2D grid, set `par.align = 'fillresize'` on the container and override `par.x` / `par.y` per clone in the callback based on row/col index.

---

## Updating Without Rebuilding

When the data table changes, the replicator regenerates the clones. By default it destroys and recreates everything. To preserve state, set:

```python
rep.par.recreatemissing = True       # only add/remove changed rows
rep.par.recreateallonchange = False
```

This pattern is essential for live-edit scenarios (designer adjusts table, network keeps running).

For incremental data ingestion (e.g., from a `webDAT` polling an API), have a `datExecuteDAT` watch the response, parse, write to the data table, and the replicator self-updates.

---

## Common Patterns

### Scene Roster (Data → Buttons + Logic)

```python
# Data per scene: name, file path, audio track, BPM
scene_data.appendRow(['name', 'file', 'audio', 'bpm'])
scene_data.appendRow(['Intro', '/scenes/intro.tox', '/audio/intro.wav', 110])
scene_data.appendRow(['Main', '/scenes/main.tox', '/audio/main.wav', 128])

# Replicator clones a buttonCOMP per scene
# Each button's onClick callback loads the corresponding tox + cues audio
```

### Dynamic Parameter Panel

For a list of audio bands, generate a fader strip per band:

```python
# Data: band names (sub, low, mid, hi-mid, high, air)
# Template: containerCOMP with label + sliderCOMP
# Replicator clones N strips
# Each slider's value is read at /audio_eq/{band_name}/fader
```

### Procedural Visual Network

Build a multi-channel visual network from a config file:

```python
# Data: which TOPs to chain, per "scene"
# Template: a baseCOMP with placeholder children
# Replicator builds one baseCOMP per scene; each scene contains a custom chain
# Switch between scenes via switchTOP.par.index driven by panel
```

### Per-Channel CHOP Display

Visualize each channel of a multi-channel CHOP separately:

```python
# Data table: one row per channel (auto-extracted via choptodatDAT)
# Template: a small chopVis COMP showing one channel
# Replicator generates N visualizers stacked vertically
```

---

## Replicator vs. Pure Python Loop

| Approach | When to use |
|---|---|
| **replicatorCOMP** | The set of clones changes (add/remove rows live). Visual editor expectations. Pattern is reusable across projects. |
| **Python loop** (in `td_execute_python`) | One-shot generation. Static set. Simpler logic, no template overhead. Faster to write. |

If you'll only ever build the network once, prefer a Python loop with `td_execute_python`. The replicator earns its weight when data is live.

---

## Pitfalls

1. **Header row** — `tableDAT` rows are 0-indexed. If you have a header, your first data row is index 1. Off-by-one bugs are common in callbacks.
2. **`namefromdatname` column missing** — replicator silently uses `digits` (numeric suffix) names. Buttons end up named `1`, `2`, `3` instead of meaningful names. Set `par.namefromdatname` explicitly.
3. **Template lives in network** — the template OP is itself a real network node. Don't connect things downstream of it directly; connect to the clones (or use a `nullCOMP` between).
4. **Recreate-on-change wipes state** — toggles, slider positions, and uncached data inside clones are lost on each regeneration. Use `recreatemissing` to preserve.
5. **`onReplicate` doesn't fire on edit** — only fires when the clone set changes. Editing a value WITHIN an existing row doesn't re-trigger. Use `parameterExecuteDAT` or expressions for per-cell live updates.
6. **Custom params on clones** — pages added in the template propagate. Pages added in `onReplicate` don't survive the next regeneration. Always add custom pages on the template, not the clone.
7. **Cooking storms** — adding many rows fast triggers many clone events. Bundle adds via Python and call `data.cook(force=True)` once at the end.
8. **`me.digits` outside replicator children** — `me.digits` only resolves inside an op that's a descendant of the replicator. Don't reference it in unrelated networks.
9. **Cross-clone references** — referencing a sibling clone via relative path works from inside a clone (`op('../OtherClone/x')`), but breaks if names change. Prefer absolute paths via the data table.

---

## Quick Recipes

| Goal | Setup |
|---|---|
| 8-button scene picker | `tableDAT` (8 rows) + `buttonCOMP` template + `replicatorCOMP` |
| Per-band EQ strip panel | `tableDAT` (band names) + container template (label + slider) + replicator |
| Data-driven visual scenes | `tableDAT` (scene config) + `baseCOMP` template (visual chain) + replicator |
| Live-updating clone set | Same as above + `par.recreatemissing = True` |
| Per-row colored UI | Data table with color cols, `onReplicate` callback sets per-clone colors |
| List from API response | `webDAT` → `datExecuteDAT` parses JSON → writes to data table → replicator updates |

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
