# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Pre-Render Guard** — A demo showing how an AI agent acts as an invisible supervisor in a VFX pipeline, catching render-breaking errors the moment an artist saves a scene file, before expensive GPU hours are spent on the render farm.

Target audience: Film executives and VFX supervisors. All dashboards use executive-friendly language with real-world film analogies (not developer jargon).

## Setup

```bash
python3 setup_vfx_env.py  # Regenerates vfx_project_alpha/ with intentional bugs
python3 verify.py          # Validates the 3 fixes in shot_010
./pre_render_check.sh      # Audits all .usda files under shots/
```

### Agentic Mode

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key-here
python3 setup_vfx_env.py   # Regenerate the broken scene
python3 agent.py vfx_project_alpha/shots/shot_010/scene_v01.usda
```

The agent reads `rulebook.md`, uses Claude to reason about the scene, applies fixes
via tools, and runs `pre_render_check.sh` as a final deterministic backstop.

## File Map

### Core VFX Project
- `setup_vfx_env.py` — Generates `vfx_project_alpha/` with 3 deliberate bugs in the USD scene
- `vfx_project_alpha/` — Mock VFX project (shots, textures, assets, render_logs)
- `vfx_project_alpha/shots/shot_010/scene_v01.usda` — The USD scene file (has been fixed)

### Validation & Tooling
- `verify.py` — Checks scene_v01.usda for: texture=v01, visibility=inherited, focalLength=35
- `pre_render_check.sh` — Bash script to audit any .usda files for path integrity, focal length, visibility
- `CHANGELOG.md` — Documents the 3 fixes in a professional table

### Agentic System
- `agent.py` — Claude-powered agent with tool-use loop (read files, list dirs, apply fixes, run validation)
- `rulebook.md` — Natural language rules the agent interprets at runtime (edit rules without touching code)
- `requirements.txt` — Python dependencies (anthropic SDK)

### Executive Dashboards (both self-contained, base64 images embedded)
- `Usher_VFX.html` (1.5MB) — **Desktop dashboard** with:
  - 3 real VFX images (filmed / artist viewport / unusable render)
  - "The Domino Effect" cascade (bad path vs AI path)
  - Recoupment table (manual vs AI cost comparison)
  - Before/After code diff
  - Pre-Flight Corrections with film analogies
  - Base-Layer Intelligence (zero-config sanity checks)
- `mobile_demo.html` (1.5MB) — **Mobile-first dashboard** with:
  - 2-sentence executive value proposition at top
  - Vertical scrolling layout, large text
  - Same content restructured for phone demo
  - Recoupment grid (stacked cards instead of table)

### Image Assets
- `source_strip.png` — Original 3-panel screenshot
- `frame_1_footage.png` — Sliced: filmed plate with missing actor
- `frame_2_vfx.png` — Sliced: artist viewport with error overlays
- `frame_3_render.png` — Sliced: unusable comp output

## USD Validation Rules

When validating or fixing `.usda` scene files, enforce these rules:

1. **Asset references must resolve** — All `@...@` asset paths must point to files that exist on disk (resolve relative to the `.usda` file location)
2. **Camera focalLength must be positive** — A `focalLength` of 0 is physically invalid; use 35mm as the corrected default
3. **Mesh visibility should be "inherited"** — Meshes set to `"hidden"` won't render; default to `"inherited"` unless intentionally hidden

## The Three Fixes (Shot 010)

| Issue | Executive Name | Before | After |
|-------|---------------|--------|-------|
| Texture path mismatch | Warehouse Substitution | `iron_diffuse_v02.png` | `iron_diffuse_v01.png` |
| Zero focal length | Broken Lens | `focalLength = 0` | `focalLength = 35` |
| Hidden mesh | Invisible Asset | `visibility = "hidden"` | `visibility = "inherited"` |

## Narrative & Terminology

The project uses a consistent "Invisible Supervisor" narrative for executives:
- **The Domino Effect** — Shows how one undetected error cascades (bad data downstream, wasted farm hours, rework)
- **Post-Save Hook** — The AI fires silently when the artist saves, zero workflow disruption
- **Standard Technical Shield** — Three zero-config "Universal Sanity Checks":
  - Path Integrity (textures exist on server, no local paths)
  - Physical Bounds (no zero focal length, zero scale, etc.)
  - Contradiction Check (Ghost Objects: Hidden=True but Render=True)
- **Rulebook** — "The AI enforces the Director's project standards automatically on every save."
- Film analogies for each fix (actor locked in trailer, camera with no lens, wrong prop from storage)

## Design Decisions

- Dark theme throughout (--bg: #0b0d11)
- No external dependencies — all CSS internal, images base64-embedded
- System font stack only (no Google Fonts)
- Red/green badges for before/after status
- Blue highlight for AI-related elements
