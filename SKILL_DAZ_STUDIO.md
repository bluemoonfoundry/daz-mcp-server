# DAZ Studio Workflow — Institutional Knowledge

Read this before any DAZ Studio session involving cameras, lighting, posing, or rendering.

## MCP Surface

Normal sessions use the compact MCP profile. Its five tools form one workflow:

1. `daz_inspect_scene` before choosing a recipe.
2. `daz_materialize_recipe` for repeatable scene work, or `daz_submit_job` for
   a general file-backed DazScript job.
3. `daz_observe_job` for live progress and the terminal result.
4. `daz_fetch_artifact` for an image or file declared in the job manifest.

Use a unique JSONL report file for each submission. Keep long work file-backed;
inline scripts do not preserve the recipe filename or its relative includes.
Static DazScript reference material lives at `daz://help/{topic}`.

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

**Bone rotations follow the same inverted convention.**
- Head "Twist" (YRotate): positive turns the head left, negative turns right
- Eye "Side-Side" (YRotate): positive looks left, negative looks right
- When computing angles to aim bones at a target, negate the expected sign.

**Genesis 9 figures face the +Z axis by default** (with Y rotation = 0).
- "In front of" a character = positive Z
- Camera placed at positive Z with no Y offset is looking directly at the character's face

---

## Camera Placement

**Never use `daz_orbit_camera_around` for portrait work.**
- It aims at the node's *root position* (feet/origin), not face level
- Always place cameras manually using explicit world-space XYZ coordinates

**Always calculate true 3D distance for focal distance.**
- Focal distance = √(ΔX² + ΔY² + ΔZ²) from camera to face
- Do not use Z distance alone — the offset in X and Y matters significantly at portrait distances
- Head bone world position is the most reliable face target; use `daz_get_world_position("Head")`

**Portrait camera workflow (proven):**
1. Get head world position with `daz_get_world_position("Head")`
2. Calculate camera position manually: X = -sin(angle) × distance, Z = cos(angle) × distance, Y = head Y + small offset
3. Create camera with `daz_create_camera` at those coordinates
4. Set Y rotation to *negative* of the horizontal angle to face the subject
5. Calculate true 3D distance for focal distance and set explicitly via `daz_set_property("Focal Distance", ...)`

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

## `daz_look_at_point` Limitations

- The tool *does* rotate eyes and head bones, but applies rotations in the wrong direction due to the inverted convention
- **Always verify in the viewport after calling it** and manually correct bone rotations if needed
- For reliable gaze direction: manually set Head Twist and Eye Side-Side values, accounting for the inverted sign

---

## Rendering

**`daz_render_with_camera_async` fails in this DAZ Studio version.**
- Error: `Property 'getViewportMgr' of object DzApp is not a function`
- Use `daz_render_async` with the `camera` parameter instead

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

---

## Scene File

- Current project scene: `X:/Development/Study/A Woman in Saigon.duf`
- Renders output to: `X:/Development/Study/renders/`
