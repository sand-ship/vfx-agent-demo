# Changelog

## [1.0.0] - 2026-02-21

### Shot 010 — `scene_v01.usda` Fixes

| # | Issue | Before | After | Rule |
|---|-------|--------|-------|------|
| 1 | Broken texture reference | `iron_diffuse_v02.png` (missing) | `iron_diffuse_v01.png` (exists) | Asset references must resolve to files on disk |
| 2 | Invalid camera focal length | `focalLength = 0` | `focalLength = 35` | Camera focalLength must be positive |
| 3 | Mesh not visible | `visibility = "hidden"` | `visibility = "inherited"` | Mesh visibility should default to inherited |

### Tooling Added

- `verify.py` — Validates `shot_010/scene_v01.usda` against expected values
- `pre_render_check.sh` — Audits all `.usda` files under `shots/` for common issues
