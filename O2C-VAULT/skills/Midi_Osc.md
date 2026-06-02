# Midi Osc

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# MIDI / OSC Reference

External controller input and output — MIDI hardware, TouchOSC mobile UIs, OSC routing across the network.

For audio-driven MIDI patterns (track triggers from spectrum analysis), see also `audio-reactive.md`.

---

## MIDI Input — Hardware Controllers

### Discovery

List connected MIDI devices first. Use a `midiinDAT` to enumerate:

```python
mdat = root.create(midiinDAT, 'mid_devices')
# Read available device names from the DAT after one cook
```

Or via Python directly:

```python
# In td_execute_python
import td
devices = [d for d in op.MIDI.devices]   # verify with td_get_docs('midi')
```

Verify the API with `td_get_docs(topic='midi')` since this varies between TD versions.

### MIDI In CHOP

Standard pattern:

```python
midi_in = root.create(midiinCHOP, 'midi_in')
midi_in.par.device = 0               # device index from discovery
midi_in.par.activechan = True
```

Output channels follow the convention `chCcN` and `chCnN`:
- `ch1c74` — channel 1, CC 74
- `ch1n60` — channel 1, note 60 (middle C) — value is velocity 0-127

**Map a CC to a parameter:**

```python
op('/project1/bloom1').par.threshold.mode = ParMode.EXPRESSION
op('/project1/bloom1').par.threshold.expr = "op('midi_in')['ch1c74'][0] / 127.0"
```

**Map a note as a trigger:**

Notes in `midiinCHOP` output velocity while held, 0 when released. Use a `triggerCHOP` to convert a held note into pulses:

```python
trig = root.create(triggerCHOP, 'note_trig')
trig.par.threshold = 1
trig.par.triggeron = 'increase'
trig.inputConnectors[0].connect(op('midi_in'))
# Filter to a single channel via a selectCHOP if desired
```

### MIDI Learn Pattern

Build a reusable learn pattern when you don't know the controller's CC layout in advance:

1. Drop a `midiinCHOP` and `selectCHOP` after it.
2. User wiggles the controller knob.
3. Use `td_read_chop` on the midiinCHOP to identify which channel is non-zero — that's the active CC.
4. Set the `selectCHOP.par.channames` to that channel name.
5. Save the mapping to a `tableDAT` so it persists across sessions.

---

## MIDI Output

```python
midi_out = root.create(midioutCHOP, 'midi_out')
midi_out.par.device = 0
midi_out.par.outputformat = 'continuous'    # 'continuous' | 'event'

# Drive an output: send out a CC mapped from any 0-1 source
src = root.create(constantCHOP, 'cc_src')
src.par.name0 = 'ch1c20'
src.par.value0 = 0.5
midi_out.inputConnectors[0].connect(src)
```

For note events specifically, use `event` mode and pulse the value with a `pulseCHOP` or `triggerCHOP`.

---

## OSC Input — Network Control

OSC is the more flexible cousin of MIDI. Used heavily for:
- TouchOSC / Lemur mobile control surfaces
- Show control systems (QLab, Watchout)
- Inter-application sync (Ableton via Max for Live, Resolume, etc.)

### OSC In CHOP

```python
osc_in = root.create(oscinCHOP, 'osc_in')
osc_in.par.port = 7000             # listen on UDP 7000
osc_in.par.localaddress = ''       # empty = all interfaces
osc_in.par.queued = False          # immediate vs. queued processing
```

Each incoming OSC address becomes a channel. `/scene/1/intensity` becomes a channel named `scene_1_intensity` (TD sanitizes slashes to underscores).

**Common gotcha:** TD only creates the channel after the FIRST message arrives at that address. Send a "hello" message from the controller during setup, or pre-declare channel names manually.

### OSC In DAT (for raw events)

Use a `oscinDAT` when you need full message access (multiple typed args, addresses with brackets/regex).

```python
osc_dat = root.create(oscinDAT, 'osc_events')
osc_dat.par.port = 7001
# Each row: timestamp, address, type tags, args...
```

Drive logic via a `datExecuteDAT` watching the `oscinDAT`:

```python
def onTableChange(dat):
    last = dat[dat.numRows - 1, 'message']
    parsed = last.val.split()
    addr = parsed[0]
    args = parsed[1:]
    if addr == '/scene/trigger':
        op('/project1/scene_switcher').par.index = int(args[0])
    return
```

---

## OSC Output — Sending to External Apps

```python
osc_out = root.create(oscoutCHOP, 'osc_out')
osc_out.par.netaddress = '127.0.0.1'    # destination IP
osc_out.par.port = 9000

# Channel names become OSC addresses
src = root.create(constantCHOP, 'send')
src.par.name0 = 'scene/intensity'        # → /scene/intensity
src.par.value0 = 0.7
osc_out.inputConnectors[0].connect(src)
```

**Channel-to-address mapping:** TD prepends `/` automatically. Use `/` in channel names to nest.

For one-shot string/typed messages, use `oscoutDAT` and call `.sendOSC(address, args)`:

```python
op('osc_out_dat').sendOSC('/scene/trigger', [1, 'fade'])
```

---

## TouchOSC / Mobile UI Pattern

Common setup for live VJ control from a phone/tablet:

1. **Configure TouchOSC layout** — assign each control an OSC address like `/vj/master`, `/vj/scene/1`, etc.
2. **Find your machine's LAN IP** — TouchOSC needs to point at it.
3. **TD listens** on `oscinCHOP.par.port = 8000` (or whichever).
4. **Map channels to params** via expressions:

```python
op('/project1/master_level').par.opacity.mode = ParMode.EXPRESSION
op('/project1/master_level').par.opacity.expr = "op('osc_in')['vj_master']"
```

5. **Send feedback** to the controller via `oscoutCHOP` — useful for syncing state across multiple devices.

---

## Network / Multi-Machine

OSC over LAN works out-of-the-box. For multi-TD-instance sync (e.g., projection cluster):

- One TD acts as **master**, broadcasts `/sync/...` over OSC
- Worker TDs run `oscinCHOP` listening on the same port
- Use UDP **broadcast address** (e.g., `192.168.1.255`) on the master's `oscoutCHOP.par.netaddress` to hit all peers

For reliability over WAN, use `webserverDAT` or `websocketDAT` with an external relay instead — UDP loss is invisible.

---

## Pitfalls

1. **MIDI device indexing** — device `0` is whichever device TD enumerated first. Reorder may shift it. Pin by name when possible.
2. **OSC channel names** — TD doesn't create a channel until the first message lands. New channels invalidate cooked dependents on first arrival, causing a one-frame stutter.
3. **OSC queued mode** — `par.queued = True` defers processing to a single per-frame batch. Lower latency but messages arriving same frame collapse to the last value. Off for triggers, on for continuous knobs.
4. **MIDI clock vs. transport** — `midiinCHOP` reports clock if available. Use `midisyncCHOP` (if your TD version exposes it) or compute BPM from clock pulses (24 per quarter note).
5. **Latency** — wired MIDI is ~1-3ms. WiFi OSC is 10-30ms with jitter. Use wired for tight beat-locked work.
6. **Port conflicts** — only one process can bind a UDP port on most OS. If `oscinCHOP` shows no traffic, check that another app (Max, Ableton, etc.) isn't already listening on that port.

---

## Quick Recipes

| Goal | Op chain |
|---|---|
| Knob → bloom intensity | `midiinCHOP` → expression on `bloom.par.threshold` |
| Note → scene change | `midiinCHOP` → `triggerCHOP` → `selectCHOP` → drive `switchTOP.par.index` |
| Phone slider → master fader | TouchOSC `/master` → `oscinCHOP` → expression on output `level.par.opacity` |
| TD → Resolume scene trigger | `oscoutCHOP` channel `composition/layers/1/clips/1/connect` → Resolume listening on 7000 |
| Multi-projector sync | Master TD `oscoutCHOP` broadcast → workers `oscinCHOP` |

LINKS:
[[Architecture]]
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
