# DAZ Studio Workflow — Institutional Knowledge

Read this before any DAZ Studio session involving cameras, lighting, posing, or rendering.

## MCP Surface

Normal sessions use the compact MCP profile. It has ten tools.

To build a scene declaratively, use the five scene recipe tools: describe the
scene as JSON (schema: `daz://recipe/schema`), then `daz_recipe_validate`,
`daz_recipe_plan`, `daz_recipe_apply`, `daz_recipe_render`, and
`daz_recipe_observe` at any time. Re-applying an edited recipe changes only what
changed and never silently overwrites hand edits. See `daz://guide/recipe`.

For anything a recipe cannot express, the five job tools form one workflow:

1. `daz_inspect_scene` before choosing a script.
2. `daz_run_script_job` for repeatable scene work, or `daz_submit_job` for
   a general file-backed DazScript job.
3. `daz_observe_job` for live progress and the terminal result.
4. `daz_fetch_artifact` for an image or file declared in the job manifest.

Use a unique JSONL report file for each submission. Keep long work file-backed;
inline scripts do not preserve the script filename or its relative includes.
Static DazScript reference material lives at `daz://help/{topic}`.

In the `desktop` profile (`DAZ_MCP_PROFILE=desktop`, for clients such as
Claude Desktop that cannot write files on the DAZ Studio machine) the same ten
tools are there, plus direct scripting. Use `daz_execute` for a short script
whose result you want back, `daz_submit_script` to queue a long inline script
as a job (observe it with `daz_observe_job`), and `daz_write_script` to have
DAZ Studio save a `.dsa` file whose returned path you then pass to
`daz_run_script_job`. Never pass `daz_run_script_job` a path from your own
sandbox: the file must exist on the DAZ Studio machine.

The detailed tools named later in this document require the expert profile.
Set `DAZ_MCP_PROFILE=expert` in the MCP server environment and restart the MCP
client when doing low-level development or one-off scene surgery. The expert
profile changes visibility only; it uses the same implementations as compact.

---

## Coordinate System & Rotation Conventions

**Camera Y rotation is inverted from what you'd expect.**
- Negative Y rotation → camera points right (+X direction)
- Positive Y rotation → camera points left (-X direction)
- Example: to face a subject offset to -X (camera's right), use a *negative* Y rotation value.

**Bone rotations are in the figure's own frame.**
- Head "Twist" (YRotate): positive turns the head to the figure's left (+X), negative to its right
- Eye "Side-Side" (YRotate): positive looks to the figure's left, negative to its right
- For a figure at rest facing +Z, `atan2(dx, dz)` toward the target is the YRotate to set (no sign flip)

**Genesis 9 figures face the +Z axis by default** (with Y rotation = 0).
- "In front of" a character = positive Z
- Camera placed at positive Z with no Y offset is looking directly at the character's face

---

## Camera Placement

**Don't use `daz_orbit_camera_around` for portrait work.**
- It aims at the node's *root position* (feet/origin), not face level

**Portrait camera workflow:**
1. Create a camera with `daz_create_camera` and set its lens (focal length) first
2. `daz_frame_shot(camera, figure, "close-up")` (or another size) places and aims it at the right height for that size, fitted to the lens
3. `daz_apply_camera_angle` / `daz_apply_composition_rule` adjust the angle or composition
4. `daz_set_focus_point(camera, target_label=figure, f_stop=...)` focuses on the eyes using the true 3D distance

If you place a camera by hand, focal distance is the full 3D distance from camera to the eyes
(√(ΔX² + ΔY² + ΔZ²)), not the Z offset alone; the head bone's world position
(`daz_get_world_position("Head")`) is a good face target.

---

## Bone Rotation Limits (Genesis 9)

| Bone | Property | Min | Max |
|------|----------|-----|-----|
| Head | Twist (YRotate) | -22° | +22° |
| Head | Bend (XRotate) | -30° | +25° |
| Head | Side-Side (ZRotate) | -20° | +20° |
| Left/Right Eye | Side-Side (YRotate) | -30° | +40° |
| Left/Right Eye | Up-Down (XRotate) | -30° | +30° |

**When aiming a character's gaze at a camera offset to one side:**
- The head must carry most of the horizontal rotation (up to ±22°)
- Eyes fill in the remainder (but remember the inverted sign)
- If the total required angle exceeds ~42° (22° head + 20° eye), the pose will look strained

---

## `daz_look_at_point` Limits

- Rotations are absolute (a look-at is a state, not a delta) and computed from the figure at rest; on a figure that is itself rotated or posed, check the result in the viewport
- Bone limits clamp the result: a target more than ~22° to the side leaves the head at its limit, so use `mode="neck"`, `"torso"` or `"full"` to spread the turn

---

## Rendering

**Render from a specific camera** with `daz_render_async(camera=...)` or `daz_render_with_camera_async`
(the same render path with the camera pinned); the active viewport camera is not changed.

**DOF is sensitive at short camera distances.**
- At ~90cm subject distance, even small focal distance errors throw the face out of focus
- Prefer f/8 or higher for portrait work unless the camera is pulled back to 150cm+
- Always disable DOF first, verify framing with a sharp render, then re-enable DOF

---

## Lighting

**`daz_apply_lighting_preset` flux values are high for portrait work.**
- Default three-point preset: Key=2000, Fill=800, Rim=1200
- Soft portrait studio levels: Key=1200, Fill=500, Rim=600
- Shadow Softness clamps to 1.0 internally — that's the maximum (fully soft), which is correct for portraits
- Always set environment to Scene Only mode (mode 3) when using a custom lighting rig
