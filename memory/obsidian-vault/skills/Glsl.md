# Glsl

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# GLSL Reference

## Uniforms

```
TouchDesigner          GLSL
─────────────────────────────
vec0name = 'uTime'  →  uniform float uTime;
vec0valuex = 1.0    →  uTime value
```

### Pass Time

```python
glsl_op.par.vec0name = 'uTime'
glsl_op.par.vec0valuex.mode = ParMode.EXPRESSION
glsl_op.par.vec0valuex.expr = 'absTime.seconds'
```

```glsl
uniform float uTime;
void main() { float t = uTime * 0.5; }
```

### Built-in Uniforms (TOP)

```glsl
// Output resolution (always available)
vec2 res = uTDOutputInfo.res.zw;

// Input texture (only when inputs connected)
vec2 inputRes = uTD2DInfos[0].res.zw;
vec4 color = texture(sTD2DInputs[0], vUV.st);

// UV coordinates
vUV.st  // 0-1 texture coords
```

**IMPORTANT:** `uTD2DInfos` requires input textures. For standalone shaders use `uTDOutputInfo`.

## Built-in Utility Functions

```glsl
// Noise
float TDPerlinNoise(vec2/vec3/vec4 v);
float TDSimplexNoise(vec2/vec3/vec4 v);

// Color conversion
vec3 TDHSVToRGB(vec3 c);
vec3 TDRGBToHSV(vec3 c);

// Matrix transforms
mat4 TDTranslate(float x, float y, float z);
mat3 TDRotateX/Y/Z(float radians);
mat3 TDRotateOnAxis(float radians, vec3 axis);
mat3 TDScale(float x, float y, float z);
mat3 TDRotateToVector(vec3 forward, vec3 up);
mat3 TDCreateRotMatrix(vec3 from, vec3 to);  // vectors must be normalized

// Resolution struct
struct TDTexInfo {
  vec4 res;   // (1/width, 1/height, width, height)
  vec4 depth;
};

// Output (always use this — handles sRGB correctly)
fragColor = TDOutputSwizzle(color);

// Instancing (MAT only)
int TDInstanceID();
```

## glslTOP

Docked DATs created automatically:
- `glsl1_pixel` — Pixel shader
- `glsl1_compute` — Compute shader
- `glsl1_info` — Compile info

### Pixel Shader Template

```glsl
out vec4 fragColor;
void main() {
    vec4 color = texture(sTD2DInputs[0], vUV.st);
    fragColor = TDOutputSwizzle(color);
}
```

### Compute Shader Template

```glsl
layout (local_size_x = 8, local_size_y = 8) in;
void main() {
    vec4 color = texelFetch(sTD2DInputs[0], ivec2(gl_GlobalInvocationID.xy), 0);
    TDImageStoreOutput(0, gl_GlobalInvocationID, color);
}
```

### Update Shader

```python
op('/project1/glsl1_pixel').text = shader_code
op('/project1/glsl1').cook(force=True)
# Check errors:
print(op('/project1/glsl1_info').text)
```

## glslMAT

Docked DATs:
- `glslmat1_vertex` — Vertex shader (param: `vdat`)
- `glslmat1_pixel` — Pixel shader (param: `pdat`)
- `glslmat1_info` — Compile info

Note: MAT uses `vdat`/`pdat`, TOP uses `vertexdat`/`pixeldat`.

### Vertex Shader Template

```glsl
uniform float uTime;
void main() {
    vec3 pos = TDPos();
    pos.z += sin(pos.x * 3.0 + uTime) * 0.2;
    vec4 worldSpacePos = TDDeform(pos);
    gl_Position = TDWorldToProj(worldSpacePos);
}
```

## Bayer 8x8 Dither Matrix

Reusable ordered dither function for retro/print aesthetics:

```glsl
float bayer8(vec2 pos) {
    int x = int(mod(pos.x, 8.0)), y = int(mod(pos.y, 8.0)), idx = x + y * 8;
    int b[64] = int[64](
        0,32,8,40,2,34,10,42,48,16,56,24,50,18,58,26,
        12,44,4,36,14,46,6,38,60,28,52,20,62,30,54,22,
        3,35,11,43,1,33,9,41,51,19,59,27,49,17,57,25,
        15,47,7,39,13,45,5,37,63,31,55,23,61,29,53,21
    );
    return float(b[idx]) / 64.0;
}
```

## glslPOP / glsladvancedPOP / glslcopyPOP

All use compute shaders. Docked DATs follow naming convention:
- `glsl1_compute` / `glsladv1_compute`
- `glslcopy1_ptCompute` / `glslcopy1_vertCompute` / `glslcopy1_primCompute`

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
