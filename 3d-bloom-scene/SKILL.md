---
name: "3d-bloom-scene"
description: "Scaffold a Three.js scene with bloom post-processing, atmospheric lighting, and fog. Use when the user asks for a Three.js scene, bloom or glow effects, or an atmospheric 3D hero visual."
---
Set up a Three.js scene with UnrealBloomPass post-processing, atmospheric lighting, and fog. This creates a cinematic, glowing aesthetic ideal for data visualizations and 3D UIs.

## What to generate

Ask the user which framework context they're using:
- **Standalone Three.js** — generate a plain `init()` function
- **react-three-fiber** — generate a `<PostProcessing>` component using `@react-three/postprocessing`
- **react-force-graph-3d** — generate a `useEffect` hook that taps into the ForceGraph3D ref

Then generate the following setup adapted to their framework:

### 1. EffectComposer Pipeline

```typescript
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";

// Tone mapping — ACESFilmic gives natural HDR rolloff
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.1; // >1 brightens, <1 darkens

// Composer chain: render scene → bloom → output correction
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(
  new THREE.Vector2(width, height),
  0.9,   // strength — how intense the glow is (0.5-1.5 typical)
  0.4,   // radius — how far glow spreads (0.1-1.0)
  0.85   // threshold — minimum brightness to bloom (0-1, lower = more glow)
);
composer.addPass(bloom);
composer.addPass(new OutputPass()); // Required for correct color output
```

### 2. Atmospheric Fog

```typescript
// Exponential fog — objects fade into background at distance
scene.fog = new THREE.FogExp2(0x060612, 0.0015);
// Color should match your scene background
// Density 0.001-0.003 for subtle depth, higher for dramatic falloff
```

### 3. Dual-Light Rig (Cool + Warm)

```typescript
// Ambient base — tinted slightly cool for depth
const ambient = new THREE.AmbientLight(0x8888cc, 0.7);
scene.add(ambient);

// Primary light — cool accent (upper-right, brighter)
const p1 = new THREE.PointLight(0x4fc3f7, 1.0, 900);
p1.position.set(250, 250, 250);
scene.add(p1);

// Secondary light — warm accent (lower-left, subtler)
const p2 = new THREE.PointLight(0xe07c4f, 0.6, 900);
p2.position.set(-250, -150, -250);
scene.add(p2);
```

### 4. Materials That Work With Bloom

For objects to glow, they need emissive properties:

```typescript
const mat = new THREE.MeshStandardMaterial({
  color: nodeColor,
  metalness: 0.15,     // Low metalness for soft look
  roughness: 0.25,     // Slightly glossy
  transparent: true,
  opacity: 0.85,
  emissive: nodeColor,
  emissiveIntensity: 0.3, // Controls bloom brightness per object
  // Increase to 0.5-0.8 for highlighted/selected objects
});
```

### 5. Cleanup Pattern

```typescript
// Return cleanup function to prevent light/fog accumulation on remount
return () => {
  scene.remove(ambient);
  scene.remove(p1);
  scene.remove(p2);
  scene.fog = null;
  composer.dispose();
};
```

## Important notes
- The `OutputPass` at the end of the composer chain is required — without it, colors shift incorrectly after bloom
- For react-force-graph-3d, set `postProcessingComposer` on the ref: `fgRef.current.postProcessingComposer = () => composer`
- Bloom threshold controls what glows: lower = more objects bloom, higher = only bright emissive objects
- Light colors should complement each other (cool primary + warm secondary creates visual depth)
- Fog color should match scene background for seamless fade

$ARGUMENTS
