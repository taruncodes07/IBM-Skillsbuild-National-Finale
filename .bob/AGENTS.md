# VIDYUT-TRACE — Bob Agent Configuration

## Project Overview
This is **VIDYUT-TRACE**, a grid-theft detection cockpit built with React + React Three Fiber (R3F). The frontend is a single-screen, zero-clutter 4-zone cockpit:
- **Zone A** (top): `CockpitTopBar` — command bar with preset stepper & replay controls
- **Zone B** (left): `LeftHierarchyPanel` — network hierarchy tree + energy balance waterfall
- **Zone C** (center): `Scene.tsx` (R3F Canvas) + floating HUD overlays + `PiPDroneHUD`
- **Zone D** (right): `RightPipelinePanel` — multi-worker trace, hypotheses ledger, human gate
- **Zone E** (bottom drawer): `EvaluationDrawer` — IBM Bob evidence log, baseline comparison, finance

## Skills Available
The `.agents/skills/` directory contains Three.js and R3F skills. Use them when working on 3D scene code:

| Skill | When to use |
|---|---|
| `threejs-r3f` | React Three Fiber Canvas, hooks, Drei helpers, Suspense |
| `threejs-scene` | Camera framing, coordinate transforms, renderer lifecycle |
| `threejs-lighting` | Lights, shadows, environment maps, mood |
| `threejs-html` | R3F `<Html>` overlays, responsive layout integration |
| `threejs-interaction` | OrbitControls, picking, pointer events |
| `threejs-animation` | useFrame motion, flight paths, damping |
| `threejs-performance` | Frame budget, instancing, draw-call reduction |
| `threejs-materials` | PBR materials, emissive, transparency |
| `threejs-geometry` | BufferGeometry, procedural meshes |
| `threejs-accessibility` | Keyboard navigation, reduced-motion, ARIA |
| `threejs-shaders` | GLSL uniforms, custom materials |
| `threejs-postprocessing` | Bloom, antialiasing, depth effects |

## Stack
- React 18 + TypeScript
- React Three Fiber (`@react-three/fiber`) + Drei (`@react-three/drei`)
- Three.js r163+
- Vite (build tool)
- Lucide React (icons)
- Python FastAPI backend (`backend/`)

## Code Style
- Components are tightly minified/dense — preserve the existing style when making small edits
- All styles are in `frontend/style.css` (single flat CSS file, no CSS modules)
- No test framework for frontend; Python pytest covers backend acceptance tests
- Keep every change minimal and targeted; do not refactor unrelated code

## Key Files
- `frontend/App.tsx` — root layout, all state, main orchestrator
- `frontend/Scene.tsx` — R3F scene: buildings, poles, wires, drone, flight logic
- `frontend/style.css` — all CSS (cockpit-app, zone classes, cards, HUD, drawer)
- `frontend/CockpitTopBar.tsx` — Zone A top bar
- `frontend/LeftHierarchyPanel.tsx` — Zone B left panel
- `frontend/RightPipelinePanel.tsx` — Zone D right panel
- `frontend/PiPDroneHUD.tsx` — drone HUD overlay inside Zone C
- `frontend/EvaluationDrawer.tsx` — Zone E bottom drawer
