# VFX Pre-Render Rulebook

This file defines the validation rules enforced by the AI Pre-Render Guard agent.
Rules are read at runtime and interpreted by the agent — edit this file to change
what the agent checks without touching any code.

---

## Universal Sanity Checks (always enforced)

### 1. Asset Path Integrity
- Every asset reference (`@...@` in USD) must resolve to a file that exists on disk.
- Paths are resolved relative to the `.usda` file's directory.
- If a referenced file is missing, check for similar filenames in the same directory
  (e.g. version mismatch like `v02` vs `v01`) and suggest the closest match.

### 2. Camera Physical Validity
- `focalLength` must be greater than 0. A value of 0 is physically impossible (no lens).
- Typical range: 12mm (ultra-wide) to 300mm (telephoto). Default correction: 45mm.
- `focusDistance` must be positive if present.

### 3. Mesh Visibility
- Meshes with `visibility = "hidden"` will not render. This is almost always an error
  unless the prim is explicitly documented as an internal helper.
- Default correction: set to `"inherited"` so the mesh respects its parent's visibility.

### 4. Transform Validity
- No negative scale values on transforms (causes inside-out geometry).
- No zero scale values (collapses geometry to nothing).

### 5. Render Settings
- Render resolution must be > 0 in both width and height if present.
- Frame range `endFrame` must be >= `startFrame`.

---

## Project-Specific Rules

### Texture Versioning
- Texture file versions should match the shot version where possible.
- If the scene is `scene_v01.usda`, prefer `*_v01.png` textures unless overridden.

### Subdivision Limits
- Subdivision level (`subdivisionScheme` iterations) should not exceed 3 for any mesh.
- Higher values cause exponential geometry growth and farm memory issues.

---

## Fix Policy

When the agent identifies an issue:
1. **Explain** the problem in plain language (suitable for a VFX supervisor).
2. **Propose** a specific fix with the exact old and new values.
3. **Apply** the fix only after reasoning about it.
4. **Verify** by re-reading the file and confirming the fix took effect.
5. **Run** the deterministic validation script as a final backstop.
