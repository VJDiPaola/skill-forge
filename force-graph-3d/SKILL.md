---
name: "force-graph-3d"
description: "Scaffold an interactive 3D network graph using react-force-graph-3d. Use when the user asks for a 3D network graph, force-directed layout, or interactive node-link visualization."
---
Scaffold a fully customized react-force-graph-3d component with cached node objects, shared geometries/materials, imperative highlight updates, and graph algorithm utilities. This creates an interactive, performant 3D network graph.

## What to ask the user

1. What are your **node types**? (e.g., person, restaurant, group — each gets a color)
2. What are your **edge/relationship types**? (e.g., founded, worked_at, trained_under — each gets a color and dash style)
3. What node metadata fields do you need? (e.g., role, cuisine, neighborhood, year)
4. Do you want path finding between nodes?
5. Do you want hover dimming (non-neighbors fade out)?

## Files to generate

### 1. `types/graph.ts` — Type definitions

```typescript
export type NodeType = "person" | "restaurant" | "group"; // customize per user
export type EdgeType = "founded" | "worked_at" | "trained_under"; // customize per user

export interface GraphNode {
  id: string;
  label: string;
  type: NodeType;
  // Add user's metadata fields here
  // Force-graph position fields (auto-populated):
  x?: number; y?: number; z?: number;
  fx?: number | null; fy?: number | null; fz?: number | null;
  vx?: number; vy?: number; vz?: number;
}

export interface GraphEdge {
  source: string | GraphNode; // react-force-graph resolves string IDs to objects
  target: string | GraphNode;
  type: EdgeType;
  label?: string;
  years?: string;
}
```

### 2. `utils/graphHelpers.ts` — Shared utilities

Include all of these utilities:

**ID normalization helper** (critical for react-force-graph-3d):
```typescript
// react-force-graph-3d mutates edges: source/target start as strings
// but become object references after first render
function resolveId(ref: string | GraphNode): string {
  return typeof ref === "string" ? ref : ref.id;
}
```

**Degree map** — count connections per node in O(E):
```typescript
export function buildDegreeMap(edges: GraphEdge[]): Map<string, number> {
  const map = new Map<string, number>();
  for (const e of edges) {
    const s = resolveId(e.source), t = resolveId(e.target);
    map.set(s, (map.get(s) ?? 0) + 1);
    map.set(t, (map.get(t) ?? 0) + 1);
  }
  return map;
}
```

**Adjacency list** — for path finding:
```typescript
export function buildAdjacency(edges: GraphEdge[]): Map<string, Set<string>> {
  const adj = new Map<string, Set<string>>();
  for (const e of edges) {
    const s = resolveId(e.source), t = resolveId(e.target);
    if (!adj.has(s)) adj.set(s, new Set());
    if (!adj.has(t)) adj.set(t, new Set());
    adj.get(s)!.add(t);
    adj.get(t)!.add(s);
  }
  return adj;
}
```

**BFS shortest path**:
```typescript
export function bfsShortestPath(
  adj: Map<string, Set<string>>, start: string, end: string
): string[] | null {
  if (start === end) return [start];
  const visited = new Set<string>([start]);
  const queue: string[][] = [[start]];
  while (queue.length > 0) {
    const path = queue.shift()!;
    const current = path[path.length - 1];
    for (const neighbor of adj.get(current) ?? []) {
      if (visited.has(neighbor)) continue;
      const newPath = [...path, neighbor];
      if (neighbor === end) return newPath;
      visited.add(neighbor);
      queue.push(newPath);
    }
  }
  return null;
}
```

**Neighbor set** — for hover dimming:
```typescript
export function getNeighborSet(nodeId: string, edges: GraphEdge[]): Set<string> {
  const neighbors = new Set<string>([nodeId]);
  for (const e of edges) {
    const s = resolveId(e.source), t = resolveId(e.target);
    if (s === nodeId) neighbors.add(t);
    if (t === nodeId) neighbors.add(s);
  }
  return neighbors;
}
```

**Node radius from degree**:
```typescript
export function nodeRadiusFromDegree(degree: number): number {
  return Math.max(6, Math.min(22, 4 + degree * 1.5));
}
```

**Geometry/material caching with radius quantization**:
```typescript
const RADIUS_BUCKETS = [6, 8, 10, 13, 16, 22];

function quantizeRadius(r: number): number {
  for (const b of RADIUS_BUCKETS) {
    if (r <= b) return b;
  }
  return RADIUS_BUCKETS[RADIUS_BUCKETS.length - 1];
}

const geometryCache = new Map<number, THREE.SphereGeometry>();
export function getSharedGeometry(radius: number): THREE.SphereGeometry {
  const q = quantizeRadius(radius);
  if (!geometryCache.has(q)) {
    geometryCache.set(q, new THREE.SphereGeometry(q * 0.5, 24, 24));
  }
  return geometryCache.get(q)!;
}

const materialCache = new Map<string, THREE.MeshStandardMaterial>();
export function getSharedMaterial(type: NodeType, highlighted: boolean): THREE.MeshStandardMaterial {
  const key = `${type}-${highlighted}`;
  if (!materialCache.has(key)) {
    const color = new THREE.Color(NODE_COLORS[type]);
    materialCache.set(key, new THREE.MeshStandardMaterial({
      color, metalness: 0.15, roughness: 0.25,
      transparent: true, opacity: 0.85,
      emissive: color, emissiveIntensity: highlighted ? 0.7 : 0.3,
    }));
  }
  return materialCache.get(key)!;
}

const ringGeoCache = new Map<number, THREE.RingGeometry>();
export function getSharedRingGeometry(radius: number): THREE.RingGeometry {
  const q = quantizeRadius(radius);
  if (!ringGeoCache.has(q)) {
    ringGeoCache.set(q, new THREE.RingGeometry(q * 0.65, q * 0.75, 48));
  }
  return ringGeoCache.get(q)!;
}
```

### 3. `components/Graph.tsx` — Main visualization component

Key patterns to include:

**Node object caching** — create Three.js groups once, update imperatively:
```typescript
const nodeObjCache = useRef<Map<string, THREE.Group>>(new Map());

const nodeThreeObject = useCallback((node: any) => {
  const cached = nodeObjCache.current.get(node.id);
  if (cached) return cached;

  const group = new THREE.Group();

  // Sphere mesh — use shared geometry, clone shared material
  const geo = getSharedGeometry(r);
  const mat = getSharedMaterial(node.type, false);
  const sphere = new THREE.Mesh(geo, mat.clone());
  sphere.name = "sphere";
  group.add(sphere);

  // SpriteText label below node
  const label = new SpriteText(node.label, 2.5, "#cccccc");
  label.position.set(0, -(r * 0.5 + 5), 0);
  label.name = "label";
  group.add(label);

  nodeObjCache.current.set(node.id, group);
  return group;
}, [degreeMap]);
```

**Imperative highlight updates** — never recreate objects for state changes:
```typescript
useEffect(() => {
  for (const [id, group] of nodeObjCache.current) {
    const sphere = group.getObjectByName("sphere") as THREE.Mesh;
    const mat = sphere.material as THREE.MeshStandardMaterial;

    const isHighlighted = selectedNode?.id === id || pathHighlight.has(id);
    const isDimmed = hoverNeighbors !== null && !hoverNeighbors.has(id);

    // Update material properties — no object recreation
    mat.emissiveIntensity = isHighlighted ? 0.7 : 0.3;
    mat.opacity = isDimmed ? 0.12 : 0.85;

    // Add/remove ring highlight
    const existingRing = group.getObjectByName("ring");
    if (isHighlighted && !existingRing) {
      const ring = new THREE.Mesh(
        getSharedRingGeometry(r),
        new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide, transparent: true, opacity: 0.55 })
      );
      ring.name = "ring";
      group.add(ring);
    } else if (!isHighlighted && existingRing) {
      group.remove(existingRing);
    }
  }
}, [selectedNode, searchHighlight, hoveredNode, hoverNeighbors, pathHighlight]);
```

**Camera fly-to** on node click/search:
```typescript
const distance = 180;
const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
fgRef.current.cameraPosition(
  { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
  { x: node.x, y: node.y, z: node.z },
  1200 // ms animation duration
);
```

**Link styling** with hover/path awareness:
```typescript
const linkColor = useCallback((link: any) => {
  if (hoverNeighbors) {
    const s = resolveId(link.source), t = resolveId(link.target);
    if (!hoverNeighbors.has(s) || !hoverNeighbors.has(t)) return "rgba(255,255,255,0.03)";
  }
  if (pathHighlight.size > 0) {
    const s = resolveId(link.source), t = resolveId(link.target);
    if (pathHighlight.has(s) && pathHighlight.has(t)) return "#ffffff";
  }
  return EDGE_STYLES[link.type]?.stroke ?? "#444";
}, [hoverNeighbors, pathHighlight]);
```

**ForceGraph3D props**:
```typescript
<ForceGraph3D
  ref={fgRef}
  graphData={graphData}
  nodeThreeObject={nodeThreeObject}
  nodeThreeObjectExtend={false}
  linkColor={linkColor}
  linkWidth={linkWidth}
  linkOpacity={0.45}
  linkCurvature={0.2}           // Curves parallel edges apart
  linkCurveRotation={0.5}
  linkDirectionalParticles={2}  // Flowing particles along edges
  linkDirectionalParticleWidth={0.5}
  linkDirectionalParticleSpeed={0.004}
  onNodeClick={handleNodeClick}
  onNodeHover={handleNodeHover}
  backgroundColor="rgba(0,0,0,0)"
  showNavInfo={false}
  d3AlphaDecay={0.02}          // Slower = more organic settling
  d3VelocityDecay={0.3}        // Friction
/>
```

## Dependencies to install

```
npm install react-force-graph-3d three three-spritetext
npm install -D @types/three
```

## Critical implementation notes

- **Always clone shared materials** before adding to mesh: `mat.clone()`. Shared materials are templates; clones allow per-node property mutation.
- **Source/target normalization**: react-force-graph-3d mutates edge objects — `source`/`target` start as string IDs but become object references after the first simulation tick. Always use the `resolveId()` helper.
- **Node object caching is essential for performance**: The `nodeThreeObject` callback fires on every graph data change. Without caching, you'd recreate all Three.js objects every time filters change.
- **Imperative updates, not recreation**: When selection/hover state changes, update material properties on cached objects. Never put `selectedNode` in `nodeThreeObject`'s dependency array — that would recreate all objects on every click.
- **graphData must spread nodes**: `nodes.map(n => ({...n}))` because react-force-graph-3d mutates node objects with x/y/z position data.

$ARGUMENTS
