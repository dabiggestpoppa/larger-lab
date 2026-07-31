# Postfx

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# Post-FX Reference

Bloom, CRT scanlines, chromatic aberration, and feedback glow patterns for live visual work.

---

## Bloom

### Built-in Bloom TOP

TD's `bloomTOP` is the fastest path — GPU-accelerated, no shader needed.

```python
bloom = root.create(bloomTOP, 'bloom1')
bloom.par.threshold = 0.6     # Luminance threshold (0-1)
bloom.par.size = 0.03         # Spread radius (0-1)
bloom.par.strength = 1.5      # Bloom intensity
bloom.par.blendmode = 'add'   # 'add' or 'screen'
```

**Audio reactive bloom:**
```python
bloom.par.strength.mode = ParMode.EXPRESSION
bloom.par.strength.expr = "op('audio_env')['envelope'][0] * 3.0 + 0.5"
```

### GLSL Bloom (More Control)

For multi-pass bloom with color tinting:

```glsl
// bloom_pixel.glsl — pass1: threshold + tint
out vec4 fragColor;
uniform float uThreshold;
uniform vec3 uBloomColor;

void main() {
    vec4 col = texture(sTD2DInputs[0], vUV.st);
    float luma = dot(col.rgb, vec3(0.299, 0.587, 0.114));
    float bloom = max(0.0, luma - uThreshold);
    fragColor = TDOutputSwizzle(vec4(col.rgb * bloom * uBloomColor, col.a));
}
```

Then blur with `blurTOP` (size ~0.02-0.05), composite back over source with `addTOP` or `compositeTOP` in Add mode.

---

## CRT / Scanlines

Pure GLSL — create a `glslTOP` and paste into its `_pixel` DAT.

```glsl
// crt_pixel.glsl
out vec4 fragColor;
uniform float uTime;
uniform float uScanlineIntensity;  // 0.0 - 1.0, default 0.4
uniform float uCurvature;          // 0.0 - 0.15, default 0.05
uniform float uVignette;           // 0.0 - 1.0, default 0.8

vec2 curveUV(vec2 uv, float amount) {
    uv = uv * 2.0 - 1.0;
    vec2 offset = abs(uv.yx) / vec2(6.0, 4.0);
    uv = uv + uv * offset * offset * amount;
    return uv * 0.5 + 0.5;
}

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 uv = vUV.st;

    // CRT barrel distortion
    uv = curveUV(uv, uCurvature * 10.0);

    // Kill pixels outside curved screen
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    vec4 col = texture(sTD2DInputs[0], uv);

    // Scanlines
    float scanline = sin(uv.y * res.y * 3.14159) * 0.5 + 0.5;
    col.rgb *= mix(1.0, scanline, uScanlineIntensity);

    // Horizontal noise flicker
    float flicker = TDSimplexNoise(vec2(uv.y * 100.0, uTime * 8.0)) * 0.03;
    col.rgb += flicker;

    // Vignette
    vec2 vig = uv * (1.0 - uv.yx);
    float v = pow(vig.x * vig.y * 15.0, uVignette);
    col.rgb *= v;

    fragColor = TDOutputSwizzle(col);
}
```

---

## Chromatic Aberration

Splits RGB channels and offsets them along screen axes.

```glsl
out vec4 fragColor;
uniform float uAmount;   // 0.001 - 0.02, default 0.006

void main() {
    vec2 uv = vUV.st;
    vec2 dir = uv - 0.5;

    float r = texture(sTD2DInputs[0], uv + dir * uAmount).r;
    float g = texture(sTD2DInputs[0], uv).g;
    float b = texture(sTD2DInputs[0], uv - dir * uAmount).b;
    float a = texture(sTD2DInputs[0], uv).a;

    fragColor = TDOutputSwizzle(vec4(r, g, b, a));
}
```

**Audio-reactive variant** — spike aberration on beats:
```glsl
uniform float uBeat;
void main() {
    vec2 uv = vUV.st;
    vec2 dir = uv - 0.5;
    float amount = uAmount + uBeat * 0.04;
    float r = texture(sTD2DInputs[0], uv + dir * amount * 1.2).r;
    float g = texture(sTD2DInputs[0], uv).g;
    float b = texture(sTD2DInputs[0], uv - dir * amount * 0.8).b;
    fragColor = TDOutputSwizzle(vec4(r, g, b, 1.0));
}
```

---

## Feedback Glow

Warm persistent trails for glow effects.

```glsl
out vec4 fragColor;
uniform float uDecay;     // 0.92 - 0.98 for slow trails
uniform vec3 uGlowColor;  // tint accumulated feedback

void main() {
    vec2 uv = vUV.st;
    vec4 prev = texture(sTD2DInputs[0], uv);  // feedback input
    vec4 curr = texture(sTD2DInputs[1], uv);  // current frame

    vec3 glow = prev.rgb * uDecay * uGlowColor;
    vec3 result = max(glow, curr.rgb);

    fragColor = TDOutputSwizzle(vec4(result, 1.0));
}
```

**Tips:**
- `uDecay = 0.95` → medium trail
- `uDecay = 0.98` → long comet tail
- Set `glslTOP` format to `rgba16float` for smooth gradients

---

## Full Post-FX Stack

Recommended order:

```
[scene / composite]
        ↓
   bloomTOP          ← luminance threshold bloom
        ↓
   glslTOP (chrom)   ← chromatic aberration
        ↓
   glslTOP (crt)     ← scanlines + barrel distortion + vignette
        ↓
   null_out          ← final output
```

**Performance note:** Each glslTOP is a full GPU pass. For 1920×1080 at 60fps this stack is comfortably real-time. For 4K, consider downsampling bloom input with `resolutionTOP` first.

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
