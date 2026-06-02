# Webgl And 3D

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# WebGL and 3D

## WebGL Mode Setup

```javascript
function setup() {
  createCanvas(1920, 1080, WEBGL);
  // Origin is CENTER, not top-left
  // Y-axis points UP (opposite of 2D mode)
  // Z-axis points toward viewer
}
```

### Coordinate Conversion (WEBGL to P2D-like)

```javascript
function draw() {
  translate(-width/2, -height/2);  // shift origin to top-left
  // Now coordinates work like P2D
}
```

## 3D Primitives

```javascript
box(w, h, d);             // rectangular prism
sphere(radius, detailX, detailY);
cylinder(radius, height, detailX, detailY);
cone(radius, height, detailX, detailY);
torus(radius, tubeRadius, detailX, detailY);
plane(width, height);     // flat rectangle
ellipsoid(rx, ry, rz);    // stretched sphere
```

### 3D Transforms

```javascript
push();
  translate(x, y, z);
  rotateX(angleX);
  rotateY(angleY);
  rotateZ(angleZ);
  scale(s);
  box(100);
pop();
```

## Camera

### Default Camera

```javascript
camera(
  eyeX, eyeY, eyeZ,       // camera position
  centerX, centerY, centerZ, // look-at target
  upX, upY, upZ             // up direction
);

// Default: camera(0, 0, (height/2)/tan(PI/6), 0, 0, 0, 0, 1, 0)
```

### Orbit Control

```javascript
function draw() {
  orbitControl();  // mouse drag to rotate, scroll to zoom
  box(200);
}
```

### createCamera

```javascript
let cam;

function setup() {
  createCanvas(800, 800, WEBGL);
  cam = createCamera();
  cam.setPosition(300, -200, 500);
  cam.lookAt(0, 0, 0);
}

// Camera methods
cam.setPosition(x, y, z);
cam.lookAt(x, y, z);
cam.move(dx, dy, dz);      // relative to camera orientation
cam.pan(angle);              // horizontal rotation
cam.tilt(angle);             // vertical rotation
cam.roll(angle);             // z-axis rotation
cam.slerp(otherCam, t);     // smooth interpolation between cameras
```

### Perspective and Orthographic

```javascript
// Perspective (default)
perspective(fov, aspect, near, far);
// fov: field of view in radians (PI/3 default)
// aspect: width/height
// near/far: clipping planes

// Orthographic (no depth foreshortening)
ortho(-width/2, width/2, -height/2, height/2, 0, 2000);
```

## Lighting

```javascript
// Ambient (uniform, no direction)
ambientLight(50, 50, 50);     // dim fill light

// Directional (parallel rays, like sun)
directionalLight(255, 255, 255, 0, -1, 0);  // color + direction

// Point (radiates from position)
pointLight(255, 200, 150, 200, -300, 400);   // color + position

// Spot (cone from position toward target)
spotLight(255, 255, 255,       // color
          0, -300, 300,         // position
          0, 1, -1,             // direction
          PI / 4, 5);           // angle, concentration

// Image-based lighting
imageLight(myHDRI);

// No lights (flat shading)
noLights();

// Quick default lighting
lights();
```

### Three-Point Lighting Setup

```javascript
function setupLighting() {
  ambientLight(30, 30, 40);                    // dim blue fill

  // Key light (main, warm)
  directionalLight(255, 240, 220, -1, -1, -1);

  // Fill light (softer, cooler, opposite side)
  directionalLight(80, 100, 140, 1, -0.5, -1);

  // Rim light (behind subject, for edge definition)
  pointLight(200, 200, 255, 0, -200, -400);
}
```

## Materials

```javascript
// Normal material (debug — colors from surface normals)
normalMaterial();

// Ambient (responds only to ambientLight)
ambientMaterial(200, 100, 100);

// Emissive (self-lit, no shadows)
emissiveMaterial(255, 0, 100);

// Specular (shiny reflections)
specularMaterial(255);
shininess(50);                // 1-200 (higher = tighter highlight)
metalness(100);               // 0-200 (metallic reflection)

// Fill works too (no lighting response)
fill(255, 0, 0);
```

### Texture

```javascript
let img;
function preload() { img = loadImage('texture.jpg'); }

function draw() {
  texture(img);
  textureMode(NORMAL);  // UV coords 0-1
  // textureMode(IMAGE); // UV coords in pixels
  textureWrap(REPEAT);  // or CLAMP, MIRROR
  box(200);
}
```

## Custom Geometry

### buildGeometry

```javascript
let myShape;

function setup() {
  createCanvas(800, 800, WEBGL);
  myShape = buildGeometry(() => {
    for (let i = 0; i < 50; i++) {
      push();
      translate(random(-200, 200), random(-200, 200), random(-200, 200));
      sphere(10);
      pop();
    }
  });
}

function draw() {
  model(myShape);  // renders once-built geometry efficiently
}
```

### beginGeometry / endGeometry

```javascript
beginGeometry();
  // draw shapes here
  box(50);
  translate(100, 0, 0);
  sphere(30);
let geo = endGeometry();

model(geo);  // reuse
```

### Manual Geometry (p5.Geometry)

```javascript
let geo = new p5.Geometry(detailX, detailY, function() {
  for (let i = 0; i <= detailX; i++) {
    for (let j = 0; j <= detailY; j++) {
      let u = i / detailX;
      let v = j / detailY;
      let x = cos(u * TWO_PI) * (100 + 30 * cos(v * TWO_PI));
      let y = sin(u * TWO_PI) * (100 + 30 * cos(v * TWO_PI));
      let z = 30 * sin(v * TWO_PI);
      this.vertices.push(createVector(x, y, z));
      this.uvs.push(u, v);
    }
  }
  this.computeFaces();
  this.computeNormals();
});
```

## GLSL Shaders

### createShader (Vertex + Fragment)

```javascript
let myShader;

function setup() {
  createCanvas(800, 800, WEBGL);

  let vert = `
    precision mediump float;
    attribute vec3 aPosition;
    attribute vec2 aTexCoord;
    varying vec2 vTexCoord;
    uniform mat4 uModelViewMatrix;
    uniform mat4 uProjectionMatrix;
    void main() {
      vTexCoord = aTexCoord;
      vec4 pos = uProjectionMatrix * uModelViewMatrix * vec4(aPosition, 1.0);
      gl_Position = pos;
    }
  `;

  let frag = `
    precision mediump float;
    varying vec2 vTexCoord;
    uniform float uTime;
    uniform vec2 uResolution;

    void main() {
      vec2 uv = vTexCoord;
      vec3 col = 0.5 + 0.5 * cos(uTime + uv.xyx + vec3(0, 2, 4));
      gl_FragColor = vec4(col, 1.0);
    }
  `;

  myShader = createShader(vert, frag);
}

function draw() {
  shader(myShader);
  myShader.setUniform('uTime', millis() / 1000.0);
  myShader.setUniform('uResolution', [width, height]);
  rect(0, 0, width, height);
  resetShader();
}
```

### createFilterShader (Post-Processing)

Simpler — only needs a fragment shader. Automatically gets the canvas as a texture.

```javascript
let blurShader;

function setup() {
  createCanvas(800, 800, WEBGL);

  blurShader = createFilterShader(`
    precision mediump float;
    varying vec2 vTexCoord;
    uniform sampler2D tex0;
    uniform vec2 texelSize;

    void main() {
      vec4 sum = vec4(0.0);
      for (int x = -2; x <= 2; x++) {
        for (int y = -2; y <= 2; y++) {
          sum += texture2D(tex0, vTexCoord + vec2(float(x), float(y)) * texelSize);
        }
      }
      gl_FragColor = sum / 25.0;
    }
  `);
}

function draw() {
  // Draw scene normally
  background(0);
  fill(255, 0, 0);
  sphere(100);

  // Apply post-processing filter
  filter(blurShader);
}
```

### Common Shader Uniforms

```javascript
myShader.setUniform('uTime', millis() / 1000.0);
myShader.setUniform('uResolution', [width, height]);
myShader.setUniform('uMouse', [mouseX / width, mouseY / height]);
myShader.setUniform('uTexture', myGraphics);  // pass p5.Graphics as texture
myShader.setUniform('uValue', 0.5);           // float
myShader.setUniform('uColor', [1.0, 0.0, 0.5, 1.0]); // vec4
```

### Shader Recipes

**Chromatic Aberration:**
```glsl
vec4 r = texture2D(tex0, vTexCoord + vec2(0.005, 0.0));
vec4 g = texture2D(tex0, vTexCoord);
vec4 b = texture2D(tex0, vTexCoord - vec2(0.005, 0.0));
gl_FragColor = vec4(r.r, g.g, b.b, 1.0);
```

**Vignette:**
```glsl
float d = distance(vTexCoord, vec2(0.5));
float v = smoothstep(0.7, 0.4, d);
gl_FragColor = texture2D(tex0, vTexCoord) * v;
```

**Scanlines:**
```glsl
float scanline = sin(vTexCoord.y * uResolution.y * 3.14159) * 0.04;
vec4 col = texture2D(tex0, vTexCoord);
gl_FragColor = col - scanline;
```

## Framebuffers

```javascript
let fbo;

function setup() {
  createCanvas(800, 800, WEBGL);
  fbo = createFramebuffer();
}

function draw() {
  // Render to framebuffer
  fbo.begin();
  clear();
  rotateY(frameCount * 0.01);
  box(200);
  fbo.end();

  // Use framebuffer as texture
  texture(fbo.color);
  plane(width, height);
}
```

### Multi-Pass Rendering

```javascript
let sceneBuffer, blurBuffer;

function setup() {
  createCanvas(800, 800, WEBGL);
  sceneBuffer = createFramebuffer();
  blurBuffer = createFramebuffer();
}

function draw() {
  // Pass 1: render scene
  sceneBuffer.begin();
  clear();
  lights();
  rotateY(frameCount * 0.01);
  box(200);
  sceneBuffer.end();

  // Pass 2: blur
  blurBuffer.begin();
  shader(blurShader);
  blurShader.setUniform('uTexture', sceneBuffer.color);
  rect(0, 0, width, height);
  resetShader();
  blurBuffer.end();

  // Final: composite
  texture(blurBuffer.color);
  plane(width, height);
}
```

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
[[Webtoon]]
[[Winding Roadmap]]
[[Wise]]
[[Workflow]]
[[Workflow Format]]
[[Writing Guide]]
[[Wuxia]]
[[X.Ai]]
[[Zapier]]
