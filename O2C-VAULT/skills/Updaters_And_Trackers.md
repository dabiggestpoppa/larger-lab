# Updaters And Trackers

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# Updaters and Value Trackers

## The problem updaters solve

Normal animations are discrete: `self.play()` goes from state A to state B. But what if you need continuous relationships — a label that always hovers above a moving dot, or a line that always connects two points?

Without updaters, you'd manually reposition every dependent object before every `self.play()`. Five animations that move a dot means five manual repositioning calls for the label. Miss one and it freezes in the wrong spot.

Updaters let you declare a relationship ONCE. Manim calls the updater function EVERY FRAME (15-60 fps depending on quality) to enforce that relationship, no matter what else is happening.

## ValueTracker: an invisible steering wheel

A ValueTracker is an invisible Mobject that holds a single float. It never appears on screen. It exists so you can ANIMATE it while other objects REACT to its value.

Think of it as a slider: drag the slider from 0 to 5, and every object wired to it responds in real time.

```python
tracker = ValueTracker(0)        # invisible, stores 0.0
tracker.get_value()              # read: 0.0
tracker.set_value(5)             # write: jump to 5.0 instantly
tracker.animate.set_value(5)     # animate: smoothly interpolate to 5.0
```

### The three-step pattern

Every ValueTracker usage follows this:

1. **Create the tracker** (the invisible slider)
2. **Create visible objects that READ the tracker** via updaters
3. **Animate the tracker** — all dependents update automatically

```python
# Step 1: Create tracker
x_tracker = ValueTracker(1)

# Step 2: Create dependent objects
dot = always_redraw(lambda: Dot(axes.c2p(x_tracker.get_value(), 0), color=YELLOW))
v_line = always_redraw(lambda: axes.get_vertical_line(
    axes.c2p(x_tracker.get_value(), func(x_tracker.get_value())), color=BLUE
))
label = always_redraw(lambda: DecimalNumber(x_tracker.get_value(), font_size=24)
    .next_to(dot, UP))

self.add(dot, v_line, label)

# Step 3: Animate the tracker — everything follows
self.play(x_tracker.animate.set_value(5), run_time=3)
```

## Types of updaters

### Lambda updater (most common)

Runs a function every frame, passing the mobject itself:

```python
# Label always stays above the dot
label.add_updater(lambda m: m.next_to(dot, UP, buff=0.2))

# Line always connects two points
line.add_updater(lambda m: m.put_start_and_end_on(
    point_a.get_center(), point_b.get_center()
))
```

### Time-based updater (with dt)

The second argument `dt` is the time since the last frame (~0.017s at 60fps):

```python
# Continuous rotation
square.add_updater(lambda m, dt: m.rotate(0.5 * dt))

# Continuous rightward drift
dot.add_updater(lambda m, dt: m.shift(RIGHT * 0.3 * dt))

# Oscillation
dot.add_updater(lambda m, dt: m.move_to(
    axes.c2p(m.get_center()[0], np.sin(self.time))
))
```

Use `dt` updaters for physics simulations, continuous motion, and time-dependent effects.

### always_redraw: full rebuild every frame

Creates a new mobject from scratch each frame. More expensive than `add_updater` but handles cases where the mobject's structure changes (not just position/color):

```python
# Brace that follows a resizing square
brace = always_redraw(Brace, square, UP)

# Area under curve that updates as function changes
area = always_redraw(lambda: axes.get_area(
    graph, x_range=[0, x_tracker.get_value()], color=BLUE, opacity=0.3
))

# Label that reconstructs its text
counter = always_redraw(lambda: Text(
    f"n = {int(x_tracker.get_value())}", font_size=24, font="Menlo"
).to_corner(UR))
```

**When to use which:**
- `add_updater` — position, color, opacity changes (cheap, preferred)
- `always_redraw` — when the shape/structure itself changes (expensive, use sparingly)

## DecimalNumber: showing live values

```python
# Counter that tracks a ValueTracker
tracker = ValueTracker(0)
number = DecimalNumber(0, font_size=48, num_decimal_places=1, color=PRIMARY)
number.add_updater(lambda m: m.set_value(tracker.get_value()))
number.add_updater(lambda m: m.next_to(dot, RIGHT, buff=0.3))

self.add(number)
self.play(tracker.animate.set_value(100), run_time=3)
```

### Variable: the labeled version

```python
var = Variable(0, Text("x", font_size=24, font="Menlo"), num_decimal_places=2)
self.add(var)
self.play(var.tracker.animate.set_value(PI), run_time=2)
# Displays: x = 3.14
```

## Removing updaters

```python
# Remove all updaters
mobject.clear_updaters()

# Suspend temporarily (during an animation that would fight the updater)
mobject.suspend_updating()
self.play(mobject.animate.shift(RIGHT))
mobject.resume_updating()

# Remove specific updater (if you stored a reference)
def my_updater(m):
    m.next_to(dot, UP)
label.add_updater(my_updater)
# ... later ...
label.remove_updater(my_updater)
```

## Animation-based updaters

### UpdateFromFunc / UpdateFromAlphaFunc

These are ANIMATIONS (passed to `self.play`), not persistent updaters:

```python
# Call a function on each frame of the animation
self.play(UpdateFromFunc(mobject, lambda m: m.next_to(moving_target, UP)), run_time=3)

# With alpha (0 to 1) — useful for custom interpolation
self.play(UpdateFromAlphaFunc(circle, lambda m, a: m.set_fill(opacity=a)), run_time=2)
```

### turn_animation_into_updater

Convert a one-shot animation into a continuous updater:

```python
from manim import turn_animation_into_updater

# This would normally play once — now it loops forever
turn_animation_into_updater(Rotating(gear, rate=PI/4))
self.add(gear)
self.wait(5)  # gear rotates for 5 seconds
```

## Practical patterns

### Pattern 1: Dot tracing a function

```python
tracker = ValueTracker(0)
graph = axes.plot(np.sin, x_range=[0, 2*PI], color=PRIMARY)
dot = always_redraw(lambda: Dot(
    axes.c2p(tracker.get_value(), np.sin(tracker.get_value())),
    color=YELLOW
))
tangent = always_redraw(lambda: axes.get_secant_slope_group(
    x=tracker.get_value(), graph=graph, dx=0.01,
    secant_line_color=HIGHLIGHT, secant_line_length=3
))

self.add(graph, dot, tangent)
self.play(tracker.animate.set_value(2*PI), run_time=6, rate_func=linear)
```

### Pattern 2: Live area under curve

```python
tracker = ValueTracker(0.5)
area = always_redraw(lambda: axes.get_area(
    graph, x_range=[0, tracker.get_value()],
    color=PRIMARY, opacity=0.3
))
area_label = always_redraw(lambda: DecimalNumber(
    # Numerical integration
    sum(func(x) * 0.01 for x in np.arange(0, tracker.get_value(), 0.01)),
    font_size=24
).next_to(axes, RIGHT))

self.add(area, area_label)
self.play(tracker.animate.set_value(4), run_time=5)
```

### Pattern 3: Connected diagram

```python
# Nodes that can be moved, with edges that auto-follow
node_a = Dot(LEFT * 2, color=PRIMARY)
node_b = Dot(RIGHT * 2, color=SECONDARY)
edge = Line().add_updater(lambda m: m.put_start_and_end_on(
    node_a.get_center(), node_b.get_center()
))
label = Text("edge", font_size=18, font="Menlo").add_updater(
    lambda m: m.move_to(edge.get_center() + UP * 0.3)
)

self.add(node_a, node_b, edge, label)
self.play(node_a.animate.shift(UP * 2), run_time=2)
self.play(node_b.animate.shift(DOWN + RIGHT), run_time=2)
# Edge and label follow automatically
```

### Pattern 4: Parameter exploration

```python
# Explore how a parameter changes a curve
a_tracker = ValueTracker(1)
curve = always_redraw(lambda: axes.plot(
    lambda x: a_tracker.get_value() * np.sin(x),
    x_range=[0, 2*PI], color=PRIMARY
))
param_label = always_redraw(lambda: Text(
    f"a = {a_tracker.get_value():.1f}", font_size=24, font="Menlo"
).to_corner(UR))

self.add(curve, param_label)
self.play(a_tracker.animate.set_value(3), run_time=3)
self.play(a_tracker.animate.set_value(0.5), run_time=2)
self.play(a_tracker.animate.set_value(1), run_time=1)
```

## Common mistakes

1. **Updater fights animation:** If a mobject has an updater that sets its position, and you try to animate it elsewhere, the updater wins every frame. Suspend updating first.

2. **always_redraw for simple moves:** If you only need to reposition, use `add_updater`. `always_redraw` reconstructs the entire mobject every frame — expensive and unnecessary for position tracking.

3. **Forgetting to add to scene:** Updaters only run on mobjects that are in the scene. `always_redraw` creates the mobject but you still need `self.add()`.

4. **Updater creates new mobjects without cleanup:** If your updater creates Text objects every frame, they accumulate. Use `always_redraw` (which handles cleanup) or update properties in-place.

LINKS:
[[Architecture]]
[[04 Data And Storage]]
[[Claude]]
[[Errors And Solutions]]
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
