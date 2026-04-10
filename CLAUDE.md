# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install all dependencies (including dev)
uv sync

# Run all tests
uv run pytest tests/ -v

# Run a single test
uv run pytest tests/test_server.py::test_daz_status_ok -v

# Run the MCP server (stdio transport, for use with Claude Desktop etc.)
uv run vangard-daz-mcp
```

## Available MCP Tools

This server exposes 84 tools to MCP clients:

### Documentation Tools

| Tool | Description |
|------|-------------|
| `daz_script_help` | Get DazScript documentation, examples, and best practices by topic |

**Topics available:** `overview`, `gotchas`, `camera`, `light`, `environment`, `scene`, `properties`, `content`, `coordinates`, `posing`, `morphs`, `hierarchy`, `interaction`, `batch`, `viewport`, `animation`, `rendering`

Documentation is loaded from `src/vangard_daz_mcp/dazscript_docs.json` and can be updated without code changes.

### Low-Level Tools (direct DazScript execution)

| Tool | Description |
|------|-------------|
| `daz_status` | Check DAZ Studio connectivity and DazScriptServer version |
| `daz_execute` | Execute inline DazScript code with optional args (enhanced docstring with critical gotchas) |
| `daz_execute_file` | Execute a `.dsa`/`.ds` script file from disk |

### High-Level Tools (structured operations)

| Tool | Description |
|------|-------------|
| `daz_scene_info` | Get scene snapshot (figures, cameras, lights, selection) |
| `daz_get_node` | Read all numeric properties of a node by label/name |
| `daz_set_property` | Set a numeric property (transform, morph, etc.) on a node |
| `daz_render` | Trigger render with current settings, optional output path |
| `daz_load_file` | Load a content file (`.duf`, `.daz`, `.obj`, etc.) into scene |

High-level tools use the **DazScriptServer script registry** (see Architecture section below) for efficiency.

### Morph Discovery Tools

| Tool | Description |
|------|-------------|
| `daz_list_morphs` | List all morphs (numeric properties) on a node with current values; can filter to show only active (non-zero) morphs |
| `daz_search_morphs` | Search morphs by name pattern (case-insensitive substring match); useful for finding morphs by category or body part |

**Morph discovery capabilities:**
- Enumerate all numeric properties (morphs) on a figure
- Filter by value (active vs all available morphs)
- Search by pattern (e.g., "smile", "head", "express", "muscle")
- Get morph metadata (label, internal name, value, property path)
- Performance-optimized for figures with 1000+ morphs

**Common use cases:**
- "List all active morphs on Genesis 9"
- "Find all smile-related facial expressions"
- "Show available body shape morphs"
- "What head morphs are currently applied?"

**Note:** Genesis figures typically have 500-1000+ morphs. Use `include_zero=False` to list only active morphs, or `daz_search_morphs` to filter by pattern.

### Scene Hierarchy Tools

| Tool | Description |
|------|-------------|
| `daz_get_node_hierarchy` | Get complete hierarchy tree for a node with all descendants (recursive with depth limit) |
| `daz_list_children` | List direct children of a node |
| `daz_get_parent` | Get parent node of a node |
| `daz_set_parent` | Set parent of a node (parenting operation with optional world-space transform maintenance) |

**Hierarchy manipulation capabilities:**
- Traverse parent-child relationships up and down
- Build complete skeleton/scene hierarchy maps
- Parent props to figure bones (attach weapons, clothing, etc.)
- Parent cameras/lights to moving nodes
- Reorganize scene structure programmatically
- Maintain world-space position during parenting

**Common use cases:**
- "Attach sword to right hand"
- "Show me the skeleton hierarchy of Genesis 9"
- "What bones are under the hip?"
- "Parent camera to character's head"
- "Find parent of lHand bone"

**Note:** Genesis skeletons have ~100+ bones. Use `max_depth` parameter in `daz_get_node_hierarchy` to limit recursion depth.

### Multi-Character Interaction Tools (advanced posing)

| Tool | Description |
|------|-------------|
| `daz_look_at_point` | Make character look at world-space point with configurable body involvement (eyes/head/neck/torso/full) |
| `daz_look_at_character` | Make one character look at another character's face with cascading body rotation |
| `daz_reach_toward` | Position arm to reach toward world-space point using pseudo-IK (calculates shoulder/elbow angles) |
| `daz_interactive_pose` | Coordinate two characters for interaction (hug, handshake, shoulder-arm, face-each-other) |

These tools handle complex world-space mathematics for multi-character scenes:
- Cascading look-at rotations from eyes through head/neck/torso/hip
- Pseudo-IK arm reaching with automatic elbow bend calculation
- Pre-configured interaction poses with proper character spacing
- Complementary pose coordination between two characters

**Use these helpers** for standard multi-character interactions instead of writing custom scripts. They handle the error-prone world-space coordinate transformations and provide natural-looking cascading body movements.

### Batch Operations Tools (performance optimization)

| Tool | Description |
|------|-------------|
| `daz_batch_set_properties` | Set multiple properties on one or more nodes with individual error handling |
| `daz_batch_transform` | Apply same transform properties to multiple nodes |
| `daz_batch_visibility` | Show or hide multiple nodes |
| `daz_batch_select` | Select multiple nodes (replace or add to current selection) |

**Performance benefits:**
- Single script call (all operations execute in one round-trip to DAZ Studio)
- No HTTP/network overhead between operations
- 5-10x faster than individual calls for typical batches
- Individual error handling without aborting the entire batch

**Common use cases:**
- **Facial expressions**: Apply 3-10 morphs at once (e.g., "surprised" = wide eyes + raised brows + open mouth)
- **Lighting presets**: Configure multiple light properties together (flux, shadow softness, color)
- **Scene management**: Show/hide groups of nodes (environment elements, props, cameras)
- **Group transformations**: Move, rotate, or scale multiple props together
- **Multi-node operations**: Any task that would require a loop of individual property sets

**Performance comparison:**
- Setting 10 morphs: ~2-3 seconds (individual) vs ~300-500ms (batch) = **5-6x faster**
- Configuring 5 lights: ~1-1.5 seconds (individual) vs ~200-300ms (batch) = **4-5x faster**
- Hiding 20 nodes: ~3-4 seconds (individual) vs ~400-600ms (batch) = **6-7x faster**

**Error handling:**
Each operation in a batch has individual error handling. Failed operations return error details without aborting the batch:
```json
{
  "results": [
    {"success": true, "node": "Genesis 9", "property": "X Translate", "value": 100},
    {"success": false, "node": "Missing", "error": "Node not found: Missing"}
  ],
  "successCount": 1,
  "failureCount": 1,
  "total": 2
}
```

**Use batch operations when:**
- Setting 3+ properties or affecting 3+ nodes
- Building complex scenes programmatically
- Applying presets or configurations
- Any operation where you'd call individual tools in a loop

**Use individual operations when:**
- Single property change
- Interactive/conditional logic between operations
- Need to check results between each operation

### Viewport and Camera Control Tools

| Tool | Description |
|------|-------------|
| `daz_set_active_camera` | Set which camera is active in the DAZ Studio viewport |
| `daz_orbit_camera_around` | Position camera orbiting around target at specified angle/distance |
| `daz_frame_camera_to_node` | Frame camera to show a node (auto-calculates distance from bounding box) |
| `daz_save_camera_preset` | Save camera position/rotation as JSON-serializable preset data |
| `daz_load_camera_preset` | Restore camera from saved preset data |

**Key capabilities:**
- **Active camera switching**: Change viewport view to show scene from specific camera
- **Spherical positioning**: Position camera using intuitive angle/distance parameters
- **Auto-framing**: Calculate optimal camera distance based on object bounding box
- **Preset management**: Save/load camera positions as reusable JSON data

**Common use cases:**
- **Multi-camera setup**: Create and position multiple cameras for different angles (front, side, top, 3/4 view)
- **Consistent framing**: Save camera positions for reuse across scenes (portrait preset, full body preset)
- **Turntable animation**: Position cameras at regular intervals around subject (0°, 45°, 90°, 135°, 180°, etc.)
- **Auto-framing**: Frame characters or props of varying sizes automatically
- **Camera presets library**: Build library of reusable camera angles (dramatic low, flattering portrait, bird's eye)

**Spherical coordinate system:**
- **Horizontal angle**: 0°=front(+Z), 90°=right(+X), 180°=back(-Z), -90°=left(-X)
- **Vertical angle**: positive=above horizon, negative=below horizon
- **Distance**: In centimeters from target

**Distance guidelines** (for 170cm tall character):
- Full body: 350-450cm
- Portrait (head/shoulders): 80-120cm
- Face close-up: 30-50cm
- Detail shots (eyes, hands): 15-25cm

**Flattering portrait angles:**
- Horizontal: 15-45° (slight angle avoids straight-on flatness)
- Vertical: 5-15° (slightly above eye level)

**Dramatic angles:**
- Low angle (powerful): horizontal 25-45°, vertical -20 to -30°
- High angle (vulnerable): horizontal 0-45°, vertical 40-60°

**Camera preset workflow:**
```python
# Save camera position after manual positioning
preset = daz_save_camera_preset("Camera 1")

# Save to file for reuse
import json
with open("portrait_preset.json", "w") as f:
    json.dump(preset, f)

# Later, in another scene
with open("portrait_preset.json") as f:
    preset = json.load(f)
daz_load_camera_preset("Camera 1", preset["preset"])

# Apply same preset to multiple cameras
for cam in ["Cam1", "Cam2", "Cam3"]:
    daz_load_camera_preset(cam, preset["preset"])
```

**Auto-framing workflow:**
```python
# Frame different body parts automatically
daz_frame_camera_to_node("Camera 1", "Genesis 9")        # Full body (auto distance)
daz_frame_camera_to_node("Camera 1", "head", distance=30)  # Face close-up
daz_frame_camera_to_node("Camera 1", "lHand", distance=20)  # Hand detail shot

# Frame varies-size props
daz_frame_camera_to_node("Camera 1", "Sword")    # Small prop
daz_frame_camera_to_node("Camera 1", "Car")      # Large prop
```

**Multi-camera turntable setup:**
```python
# Create 8 cameras at 45° intervals around character
angles = [0, 45, 90, 135, 180, 225, 270, 315]
for i, angle in enumerate(angles):
    cam_name = f"Cam_{angle}"

    # Create camera
    daz_execute(f'''
        var cam = new DzBasicCamera();
        Scene.addNode(cam);
        cam.setLabel("{cam_name}");
    ''')

    # Position camera
    daz_orbit_camera_around(cam_name, "Genesis 9", 200, angle, 15)

# Switch between cameras for preview/render
for angle in angles:
    daz_set_active_camera(f"Cam_{angle}")
    # render or preview
```

**Important notes:**
- All camera positioning tools automatically aim the camera at the target (uses `camera.aimAt()`)
- Genesis figures face +Z, so angle_horizontal=0 shows the front
- Camera presets are JSON-serializable and portable across scenes
- Auto-framing positions camera in front (+Z) at calculated or specified distance
- Viewport updates immediately when setting active camera

### Animation System Tools

| Tool | Description |
|------|-------------|
| `daz_set_keyframe` | Set a keyframe on a property at specified frame |
| `daz_get_keyframes` | Get all keyframes for a property |
| `daz_remove_keyframe` | Remove a keyframe at specified frame |
| `daz_clear_animation` | Remove all keyframes from a property |
| `daz_set_frame` | Set current animation frame |
| `daz_set_frame_range` | Set animation frame range (start and end) |
| `daz_get_animation_info` | Get animation timeline info (current frame, range, fps) |

**Animation capabilities:**
- **Keyframe-based animation**: Set property values at specific frames, DAZ interpolates between them
- **Any numeric property**: Animate transforms, morphs, lights, cameras, or any numeric property
- **Timeline control**: Set frame range, current frame, query fps and duration
- **Keyframe management**: Get, remove, clear keyframes programmatically
- **Animation export**: Render frame-by-frame to create image sequences

**Common use cases:**
- **Character animation**: Walk cycles, gestures, facial expressions (morph animation)
- **Camera animation**: Dolly, pan, zoom, cinematic shots
- **Product turntables**: 360° rotation animations for product visualization
- **Multi-character choreography**: Animate multiple characters with offset timing
- **Morph sequences**: Fade facial expressions, eye blinks, shape changes

**Basic animation workflow:**
```python
# 1. Set animation length (4 seconds = 120 frames at 30fps)
daz_set_frame_range(0, 119)

# 2. Set start keyframe
daz_set_keyframe("Genesis 9", "XTranslate", frame=0, value=0)

# 3. Set end keyframe (DAZ interpolates frames 1-118 automatically)
daz_set_keyframe("Genesis 9", "XTranslate", frame=119, value=100)

# 4. Render animation as image sequence
info = daz_get_animation_info()
for frame in range(info['startFrame'], info['endFrame'] + 1):
    daz_set_frame(frame)
    daz_render(output_path=f"frame_{frame:04d}.png")
```

**Keyframe management:**
```python
# Inspect keyframes
result = daz_get_keyframes("Genesis 9", "XTranslate")
for kf in result['keyframes']:
    print(f"Frame {kf['frame']}: {kf['value']}")

# Copy animation to another node
for kf in result['keyframes']:
    daz_set_keyframe("Genesis 8", "XTranslate", kf['frame'], kf['value'])

# Offset animation in time (shift by 30 frames)
keyframes = daz_get_keyframes("Genesis 9", "YRotate")
daz_clear_animation("Genesis 9", "YRotate")
for kf in keyframes['keyframes']:
    daz_set_keyframe("Genesis 9", "YRotate", kf['frame'] + 30, kf['value'])

# Clear all animations
daz_clear_animation("Genesis 9", "XTranslate")
```

**Animation patterns:**

*Simple translation (move 100cm over 1 second)*:
```python
daz_set_frame_range(0, 29)  # 30 frames at 30fps = 1 second
daz_set_keyframe("Genesis 9", "XTranslate", 0, 0)
daz_set_keyframe("Genesis 9", "XTranslate", 29, 100)
```

*Rotation animation (360° turntable)*:
```python
daz_set_frame_range(0, 119)  # 4 seconds
daz_set_keyframe("Genesis 9", "YRotate", 0, 0)
daz_set_keyframe("Genesis 9", "YRotate", 119, 360)
```

*Morph animation (fade in smile)*:
```python
daz_set_frame_range(0, 59)  # 2 seconds
daz_set_keyframe("Genesis 9", "PHMSmile", 0, 0)
daz_set_keyframe("Genesis 9", "PHMSmile", 59, 0.8)
```

*Camera animation (dolly in)*:
```python
daz_set_frame_range(0, 90)  # 3 seconds
daz_set_keyframe("Camera 1", "ZTranslate", 0, 300)
daz_set_keyframe("Camera 1", "ZTranslate", 90, 150)
```

*Multi-property animation (walk forward while waving)*:
```python
daz_set_frame_range(0, 90)

# Walk forward
daz_set_keyframe("Genesis 9", "ZTranslate", 0, 0)
daz_set_keyframe("Genesis 9", "ZTranslate", 90, 150)

# Wave arm (up-down-up)
daz_set_keyframe("Genesis 9/rShldrBend", "ZRotate", 0, 0)
daz_set_keyframe("Genesis 9/rShldrBend", "ZRotate", 30, 45)
daz_set_keyframe("Genesis 9/rShldrBend", "ZRotate", 60, 0)
daz_set_keyframe("Genesis 9/rShldrBend", "ZRotate", 90, 45)
```

**Frame calculations:**
- Frame range is **inclusive** (frames 0-29 = 30 frames, not 29)
- Duration in seconds = (end_frame - start_frame + 1) / fps
- Example: frames 0-119 at 30fps = (119 - 0 + 1) / 30 = 4.0 seconds
- Typical DAZ Studio FPS: 30

**Rendering tips:**
- Use zero-padded frame numbers: `f"frame_{frame:04d}.png"` (sorts correctly: frame_0001.png, frame_0002.png)
- Render to image sequence first, then convert to video using ffmpeg:
  ```bash
  ffmpeg -framerate 30 -i frame_%04d.png -c:v libx264 -pix_fmt yuv420p output.mp4
  ```

**Performance considerations:**
- Minimize keyframes (2-3 per motion, not one per frame)
- DAZ interpolates smoothly between keyframes
- Use `daz_clear_animation()` instead of removing keyframes individually

**Important notes:**
- Frames are 0-based integers (0, 1, 2, ...)
- Setting keyframe at existing frame updates the value
- DAZ Studio uses linear interpolation between keyframes
- Any numeric property can be animated (not just transforms)
- Use `daz_get_animation_info()` to check fps, frame range, and duration before rendering

### Advanced Rendering Control Tools

| Tool | Description |
|------|-------------|
| `daz_render_with_camera` | Render from specific camera without changing viewport |
| `daz_get_render_settings` | Get current render settings and configuration |
| `daz_batch_render_cameras` | Render from multiple cameras in sequence |
| `daz_render_animation` | Render animation frame range as image sequence |

**Rendering capabilities:**
- **Multi-camera rendering**: Render from specific cameras without disrupting viewport
- **Batch camera renders**: Render from multiple cameras in one operation
- **Animation export**: Render entire animations as frame-by-frame image sequences
- **Render configuration**: Query render settings (camera, output path, aspect ratio)
- **Automated workflows**: Single-call animation and multi-camera rendering

**Common use cases:**
- **Product photography**: Multi-angle renders (front, side, top, 3/4 views)
- **Character turntables**: 360° rotation with 8-16 camera positions
- **Animation export**: Export animations as PNG sequences for video conversion
- **Test renders**: Quick multi-angle test renders to evaluate composition
- **Multi-camera animation**: Render same animation from multiple camera angles

**Multi-camera rendering workflow:**
```python
# 1. Set up cameras at different angles
angles = [0, 45, 90, 135, 180, 225, 270, 315]
for angle in angles:
    cam_name = f"Cam_{angle}"
    daz_execute(f'var c = new DzBasicCamera(); Scene.addNode(c); c.setLabel("{cam_name}");')
    daz_orbit_camera_around(cam_name, "Genesis 9", 200, angle, 15)

# 2. Batch render all angles
cameras = [f"Cam_{angle}" for angle in angles]
daz_batch_render_cameras(cameras, "/renders/turntable", "angle")
# Generates: angle_Cam_0.png, angle_Cam_45.png, ..., angle_Cam_315.png
```

**Animation rendering workflow:**
```python
# 1. Create animation
daz_set_frame_range(0, 119)  # 4 seconds at 30fps
daz_set_keyframe("Genesis 9", "YRotate", 0, 0)
daz_set_keyframe("Genesis 9", "YRotate", 119, 360)

# 2. Render animation
daz_render_animation("/renders/animation", camera="Camera 1")
# Generates: frame_0000.png, frame_0001.png, ..., frame_0119.png

# 3. Convert to video (outside Python)
# ffmpeg -framerate 30 -i frame_%04d.png -c:v libx264 -pix_fmt yuv420p output.mp4
```

**Comparison: Manual vs Automated Animation Rendering**

*Manual approach (121 tool calls for 120 frames)*:
```python
info = daz_get_animation_info()  # 1 call
for frame in range(info['startFrame'], info['endFrame'] + 1):
    daz_set_frame(frame)  # 120 calls
    daz_render(output_path=f"frame_{frame:04d}.png")  # 120 calls
```

*Automated approach (1 tool call)*:
```python
daz_render_animation("/renders/animation")  # 1 call
```

Benefits:
- **Efficiency**: Single call instead of 121 calls (reduces HTTP overhead)
- **Reliability**: No loop interruption, auto frame restoration
- **Convenience**: Zero-padded filenames, auto frame range detection
- **Cleaner code**: One line instead of loop

**Product photography workflow:**
```python
# Set up standard product angles
angles = {
    "front": (0, 10),
    "front_left": (-45, 15),
    "front_right": (45, 15),
    "left": (-90, 10),
    "right": (90, 10),
    "top": (0, 75),
    "back": (180, 10)
}

# Create cameras
for name, (h_angle, v_angle) in angles.items():
    cam_name = f"Product_{name}"
    daz_execute(f'var c = new DzBasicCamera(); Scene.addNode(c); c.setLabel("{cam_name}");')
    daz_orbit_camera_around(cam_name, "Product", 250, h_angle, v_angle)

# Render all angles
camera_list = [f"Product_{name}" for name in angles.keys()]
daz_batch_render_cameras(camera_list, "/renders/product", "product")
```

**Video conversion (ffmpeg):**
```bash
# Standard quality (30fps)
ffmpeg -framerate 30 -i frame_%04d.png -c:v libx264 -pix_fmt yuv420p output.mp4

# High quality (slower encode)
ffmpeg -framerate 30 -i frame_%04d.png -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p hq_output.mp4

# 60fps (smooth)
ffmpeg -framerate 60 -i frame_%04d.png -c:v libx264 -pix_fmt yuv420p output_60fps.mp4

# Animated GIF (web preview)
ffmpeg -framerate 30 -i frame_%04d.png -vf "scale=640:-1" output.gif
```

**Important notes:**
- **Viewport camera unchanged**: `daz_render_with_camera()` doesn't change what user sees
- **Frame numbering**: Auto zero-padded to 4 digits (frame_0000.png, frame_0001.png)
- **Render time**: Rendering can take minutes per frame (increase `DAZ_TIMEOUT` for long renders)
- **Pixel dimensions**: Cannot be set reliably via DazScript - set in DAZ Studio UI
- **Timeline restoration**: `daz_render_animation()` restores current frame after completion
- **Camera restoration**: Batch and animation tools restore previous render camera

**Performance considerations:**
- Single frame: 30 seconds to 5+ minutes (depends on quality, scene complexity)
- 120-frame animation: 1-10 hours
- Multi-camera batch (8 cameras): 4-40 minutes
- Increase `DAZ_TIMEOUT` env var for long renders: `DAZ_TIMEOUT=300` (5 minutes) or more

### Phase 1 Tools

#### Spatial Query Tools

| Tool | Description |
|------|-------------|
| `daz_get_world_position` | Get world-space position, local position, rotation, and scale of a node |
| `daz_get_bounding_box` | Get bounding box (min/max corners, center, width/height/depth) of a node |
| `daz_calculate_distance` | Calculate distance and direction vector between two nodes (cm) |
| `daz_get_spatial_relationship` | Natural language spatial relationship between two nodes (direction, angle, overlap) |
| `daz_check_overlap` | Check if two nodes have overlapping bounding boxes with penetration depth |

**Common use cases:**
- "Where is the character's hand in world space?"
- "How far is the camera from Genesis 9?"
- "Is Bob in front of or behind Alice?"
- "Are these two characters interpenetrating?"

#### Property Introspection Tools

| Tool | Description |
|------|-------------|
| `daz_inspect_properties` | List all properties on a node; filter by type (numeric, transform, morph, bool, string, all) |
| `daz_get_property_metadata` | Get detailed metadata (min, max, default, type, path) for a single named property |
| `daz_validate_script` | Static analysis of DazScript for known anti-patterns (no DAZ Studio connection needed) |

**Common use cases:**
- "What properties can I set on this spotlight?"
- "What is the valid range for Flux on a light?"
- "Check this script for errors before running it"

**`daz_inspect_properties` filter types:** `all`, `numeric`, `transform`, `morph`, `bool`, `string`

#### Lighting Preset Tools

| Tool | Description |
|------|-------------|
| `daz_apply_lighting_preset` | Create a professional lighting setup in one command |
| `daz_validate_scene` | Validate scene for collisions, lighting, cameras, and figures; returns score |

**Lighting presets:**
- `three-point` — Key (front-right) + Fill (front-left) + Rim (back). General-purpose.
- `rembrandt` — Key (45° side, high) + dim Fill. Dramatic portrait lighting.
- `butterfly` — Key (directly front, high). Glamour/beauty lighting.
- `split` — Key (90° side). Half face lit, half in shadow. Moody.
- `loop` — Key (35° side) + Fill + Rim. Natural-looking portrait.

All presets:
- Position lights relative to the subject's actual bounding box
- Aim lights at the subject's face height
- Set environment mode to Scene Only (disables dome)
- Remove existing lights with the same names before recreating

**`daz_validate_scene` checks:**
- Bounding box collisions between figures (severity: high)
- No lights / single light source (severity: high/medium)
- No cameras in scene (severity: medium)
- No figures in scene (severity: low)
- Returns score 0-100 and per-category breakdown

### Phase 2 Tools

#### Emotional Direction

| Tool | Description |
|------|-------------|
| `daz_set_emotion` | Apply an emotional expression to a character (morphs + body language) |

**Supported emotions:** `happy`, `sad`, `angry`, `surprised`, `fearful`, `disgusted`, `neutral`, `excited`, `bored`, `confident`, `shy`, `loving`, `contemptuous`

**How it works:**
- Python side defines per-emotion morph candidate lists (multiple names tried in order — first match wins)
- Handles morph naming differences between Genesis 8 / Genesis 9 / other figures
- Scales all morph and bone rotation values by `intensity` (0.0–1.0, default 0.7)
- Reports non-found morphs in `not_found` list without raising errors

**Common use cases:**
- "Make Alice look happy" → `daz_set_emotion("Alice", "happy")`
- "Give Bob a subtle confident look" → `daz_set_emotion("Bob", "confident", intensity=0.4)`

#### Content Library Navigation

| Tool | Description |
|------|-------------|
| `daz_list_categories` | List subdirectories in content library under a parent path |
| `daz_browse_category` | List .duf files in a content library category path |
| `daz_get_content_info` | Read metadata from a .duf file without loading it |

**Content directory traversal:**
- `daz_list_categories` and `daz_browse_category` search all configured DAZ content directories
- Results are deduplicated by name across multiple library roots
- `daz_get_content_info` reads the .duf JSON directly in Python (no DAZ Studio connection needed)

**Common use cases:**
- "What Genesis 9 hair is available?" → `daz_list_categories("People/Genesis 9")` then `daz_browse_category("People/Genesis 9/Hair")`
- "What does this file require?" → `daz_get_content_info("/path/to/file.duf")`

#### Scene Composition / Cinematography

| Tool | Description |
|------|-------------|
| `daz_apply_composition_rule` | Position camera using a photography composition rule |
| `daz_frame_shot` | Frame camera to subject using a standard cinematic shot type |
| `daz_apply_camera_angle` | Apply a standard camera angle preset relative to a subject |

**`daz_apply_composition_rule` rules:**
- `rule-of-thirds` — Subject on right vertical third at eye level (default)
- `golden-ratio` — Subject at 1.618 golden section
- `center-frame` — Subject centered, symmetric
- `leading-lines` — Low angle with diagonal offset

**`daz_frame_shot` shot types:**
- `extreme-close-up` → 25 cm (eyes/mouth detail)
- `close-up` → 50 cm (face)
- `medium-close-up` → 90 cm (head and shoulders)
- `medium-shot` → 140 cm (waist up)
- `medium-full` → 200 cm (knees up)
- `full-shot` → 400 cm (whole body)
- `wide-shot` → 700 cm (body + environment)

**`daz_apply_camera_angle` angles:**
- `eye-level` — Neutral (default)
- `high-angle` — Above subject, looking down (vulnerable)
- `low-angle` — Below eye level, looking up (powerful)
- `dutch-angle` — Eye level + 15° Z-roll (unsettling)
- `overhead` — Directly above (bird's-eye)
- `worms-eye` — Ground level looking up
- `over-shoulder` — Behind and to one side

All composition tools maintain the camera's current horizontal distance from the subject and use `camera.aimAt()` to orient correctly.

#### Scene Checkpoint System

| Tool | Description |
|------|-------------|
| `daz_save_scene_state` | Save current transforms, morphs, and light properties as a named checkpoint |
| `daz_restore_scene_state` | Restore scene state from a named checkpoint |
| `daz_list_checkpoints` | List all saved checkpoints in the current session |

**What is captured:**
- All skeleton/figure: transform properties (XTranslate, YTranslate, ZTranslate, XRotate, YRotate, ZRotate, Scale) + all active (non-zero) morph values
- All cameras: transform properties
- All lights: transform properties + Flux, Shadow Softness, Spread Angle

**What is NOT captured:** Materials, geometry, HDR dome settings, parenting relationships

**Important:** Checkpoints are stored in MCP server process memory. They are lost if the server restarts.

```python
# Safe experimentation workflow
daz_save_scene_state("before_lighting_test")
daz_apply_lighting_preset("rembrandt", "Genesis 9")   # experiment...
# Don't like it?
daz_restore_scene_state("before_lighting_test")
```

#### Scene Layout & Proximity

| Tool | Description |
|------|-------------|
| `daz_get_scene_layout` | Full spatial map of all scene nodes with positions and bounding boxes |
| `daz_find_nearby_nodes` | Find all nodes within a radius of a target node |

**`daz_get_scene_layout` include_types filter:** `"figures"`, `"cameras"`, `"lights"`, `"props"`

**`daz_find_nearby_nodes` direction labels:** `front`, `front-right`, `right`, `back-right`, `back`, `back-left`, `left`, `front-left`

**Common use cases:**
- "Show me where everything is" → `daz_get_scene_layout()`
- "What props are near Alice?" → `daz_find_nearby_nodes("Alice", radius=200, include_types=["props"])`
- "How far is Bob from the chair?" → `daz_find_nearby_nodes("Chair", radius=500, include_types=["figures"])`

### Phase 4 Tools: Cinematic Director Workflow

#### Macro Recording System

| Tool | Description |
|------|-------------|
| `daz_start_recording` | Begin recording a macro (captures all subsequent high-level tool calls) |
| `daz_stop_recording` | Stop recording and save macro with name and description |
| `daz_replay_macro` | Replay a previously recorded macro |
| `daz_list_macros` | List all recorded macros with metadata |

**Macro capabilities:**
- Record sequences of high-level tool calls (scene setup, character posing, lighting, etc.)
- Save as reusable named macros
- Replay macros with optional variable substitution
- Session-based storage (lost on server restart)

**Common use cases:**
- "Record my character setup workflow for reuse"
- "Create a lighting macro for portraits"
- "Save this camera setup sequence"

#### Shot Sequences & Scene Generation

| Tool | Description |
|------|-------------|
| `daz_create_shot_sequence` | Create multi-shot sequences (establishing-medium-close, conversation, action, dramatic reveal) |
| `daz_animate_conversation` | Animate conversation between characters with alternating camera cuts |
| `daz_create_scene` | Generate complete scenes (two-character conversation, interview, action, group) with figures, cameras, lights |

**Shot sequence types:**
- `establishing-medium-close`: Wide → Medium → Closeup progression
- `conversation`: Over-shoulder singles + two-shot for dialogue
- `action`: Wide, tracking, hero angle sequence
- `dramatic-reveal`: High angle → medium → extreme closeup

**Scene generation capabilities:**
- Load Genesis 9 figures from content library
- Position characters with appropriate spacing
- Create multi-camera coverage
- Apply lighting presets
- Set up animations with keyframes

**Common use cases:**
- "Set up a conversation scene between two characters"
- "Create an interview setup"
- "Generate action scene with hero and villain"

#### Camera Movement & Animation (Phase 4.5)

| Tool | Description |
|------|-------------|
| `daz_animate_camera_movement` | Animate common camera movements (dolly, pan, tilt, crane, handheld shake) |
| `daz_create_camera_path` | Create smooth camera path through multiple waypoints |

**Camera movement types:**
- `dolly-in` / `dolly-out`: Move toward/away from subject
- `pan-left` / `pan-right`: Horizontal rotation
- `tilt-up` / `tilt-down`: Vertical rotation
- `crane-up` / `crane-down`: Vertical movement with tilt
- `handheld-shake`: Subtle random shake for realism

**Path types:**
- `straight`: Linear interpolation between waypoints
- `smooth`: Smooth curves (Catmull-Rom spline simulation)
- `arc`: Circular arc path

**Common use cases:**
- "Dolly in on character's face over 3 seconds"
- "Create sweeping pan across environment"
- "Animate camera following curved path"

#### Character Choreography (Phase 4.6)

| Tool | Description |
|------|-------------|
| `daz_create_character_path` | Animate character movement along a path with auto-rotation |
| `daz_arrange_characters` | Position multiple characters in formations (line, semicircle, triangle, circle) |
| `daz_choreograph_action` | Choreograph interactions (handshake, hug, fight, dance) |

**Character path types:**
- `straight`: Direct line between waypoints
- `curved`: Smooth curved path
- `zigzag`: Sharp direction changes
- `circular`: Circular movement

**Walking styles:**
- `casual`: Relaxed walking pace
- `hurried`: Fast, purposeful movement
- `sneak`: Slow, careful movement

**Formation types:**
- `line`: Horizontal or vertical line
- `semicircle`: Arc formation
- `triangle`: Three-point formation
- `conversation-circle`: Circle facing inward

**Choreographed actions:**
- `handshake`: Business/friendly handshake (60cm spacing)
- `hug`: Intimate embrace (30cm spacing)
- `fight`: Combat stance (100cm spacing)
- `dance`: Partner dance position (40cm spacing)

**Common use cases:**
- "Animate character walking from point A to point B"
- "Arrange 5 characters in semicircle formation"
- "Set up handshake between two business people"

#### Cinematic Coverage (Phase 4.7)

| Tool | Description |
|------|-------------|
| `daz_setup_shot_coverage` | Create multiple camera angles for professional coverage |
| `daz_create_camera_rig` | Set up multi-camera rig for bullet-time or simultaneous angles |

**Coverage types:**
- `standard`: Master (35mm), Medium (50mm), Closeup (85mm) — 3 cameras
- `interview`: Two-shot + singles at angles — 3 cameras
- `dramatic`: Master, Low Angle, High Angle, Profile — 4 cameras
- `action`: Wide, Medium, Tracking, Hero Low — 4 cameras

**Camera rig capabilities:**
- 2-8 cameras in circular formation
- All cameras parented to rig controller
- Rotate rig to orbit all cameras around subject
- Switch between cameras for instant angle changes
- Configurable radius, height variation, focal lengths

**Common use cases:**
- "Set up standard 3-camera coverage for dialogue"
- "Create 8-camera bullet-time rig"
- "Generate interview coverage with singles and two-shot"

#### Phase 4 Implementation Status

**Version:** 0.3.0

**Implemented tools:** 14 total
- Phase 4.0 (Original): 7 tools (macro system, shot sequences, conversation, scene generation)
- Phase 4.5: 2 tools (camera movement & animation)
- Phase 4.6: 3 tools (character choreography)
- Phase 4.7: 2 tools (cinematic coverage)

**Branch:** `phase4_tools_implementation`

**Remaining planned enhancements:**
- Lighting Animation (2 tools)
- Shot Planning (2 tools)
- Focus & DOF (2 tools)
- Visual Composition (2 tools)
- Multi-Scene Management (2 tools)
- Performance Timing (2 tools)

See `IMPLEMENTATION_PLAN.md` for full roadmap.

### Updating Documentation

The `daz_script_help` tool loads documentation from `src/vangard_daz_mcp/dazscript_docs.json`. To add or update topics:

1. Edit `dazscript_docs.json` with new topic entries
2. Each topic has a `title` and `content` field
3. Use markdown formatting in `content` for code examples
4. Restart the MCP server to reload documentation

No code changes required to update documentation.

## DazScript environment (verified against DAZ Studio 4.24.0.4)

### Globals

| Name | Type | Description |
|------|------|-------------|
| `Scene` | `DzScene` | The current scene |
| `App` | `DzApp` | The application object |
| `MainWindow` | — | Main window |

DAZ Studio version: `App.applicationVersion` / `App.versionString` / `App.longVersionString`.
The `/status` endpoint reports the **plugin** version, not the DAZ Studio version.

### Script format

Scripts must **not** use a bare top-level `return`. Wrap any script that returns a value in an IIFE:

```javascript
(function(){
    return { foo: 42 };
})()
```

`throw new Error("msg")` propagates as `success: false` with `error: "Line N: Error: msg"`.
`throw "string"` propagates as `error: "string"` (no line prefix).

### Scene queries

- `Scene.getNumNodes()` — total node count (production scenes easily exceed 3000 nodes)
- **Do not iterate all nodes.** Use the direct finders instead:
  - `Scene.findNodeByLabel(label)` — find by display label (preferred, labels are unique per scene)
  - `Scene.findNode(internalName)` — find by internal name (multiple nodes can share an internal name like `"Genesis9"`)
  - `Scene.findNodeByLabel(label)` → fallback `Scene.findNode(label)` covers both cases
- Skeleton/camera/light lists are the right way to enumerate actors: `Scene.getNumSkeletons()` / `getSkeleton(i)`, `getNumCameras()` / `getCamera(i)`, `getNumLights()` / `getLight(i)`

### Node properties

- `node.getNumProperties()` / `node.getProperty(i)` — iterate all properties
- `node.findProperty(internalName)` — direct lookup by internal name
- Property types: `DzFloatProperty`, `DzBoolProperty` (also inherits `DzNumericProperty`), `DzNumericNodeProperty`
- `prop.inherits("DzNumericProperty")` returns `true` for float and bool properties
- `prop.getValue()` / `prop.setValue(v)` — read/write numeric value

**Transform property names** (internal name → UI label):

| Internal name | UI label |
|---------------|----------|
| `XTranslate` | X Translate |
| `YTranslate` | Y Translate |
| `ZTranslate` | Z Translate |
| `XRotate` | X Rotate |
| `YRotate` | Y Rotate |
| `ZRotate` | Z Rotate |
| `Scale` | Scale |
| `XScale` | X Scale |
| `YScale` | Y Scale |
| `ZScale` | Z Scale |

`node.getLabel()` → UI display label. `node.getName()` → internal name (may be shared across instances).

### Render manager

```javascript
var renderMgr = App.getRenderMgr();
var opts = renderMgr.getRenderOptions();
opts.renderImgToId = 0;                  // 0 = render to file
opts.renderImgFilename = "C:/out.png";   // direct property assignment, no setter method
renderMgr.doRender();                    // trigger render (not .render())
```

Pixel dimensions cannot be set reliably via DazScript in this environment (`setImageSize` is not exposed).

### Content manager

```javascript
App.getContentMgr().openFile(filePath, mergeBoolean);
// true  → merge into current scene
// false → replace current scene
```

`DzFileInfo` constructor is **not** available in this scripting environment — do not attempt file-existence checks via it.

### Node creation

**Cameras** — use the direct constructor; do **not** use `DzNewCameraAction` or any other UI action:

```javascript
var cam = new DzBasicCamera();
Scene.addNode(cam);
cam.setLabel("My Camera");
```

Actions like `DzNewCameraAction` pop a modal dialog that blocks the script call and causes a timeout.

**Lights** — constructors work directly:

```javascript
var light = new DzSpotLight();
Scene.addNode(light);
```

### Aiming nodes

`node.aimAt(new DzVec3(x, y, z))` works on cameras and lights and immediately applies the correct rotation. Do not attempt to set `"Point At"` via `findProperty("Point At").setValue(...)` — that does not correctly link to a target node.

```javascript
light.aimAt(new DzVec3(0, 163, 0));   // point at Ethan's head
cam.aimAt(new DzVec3(0, 100, 0));     // point at torso
```

### Coordinate system and figure orientation

Genesis figures face **+Z** (positive Z is in front of the figure). Place cameras at positive Z to see the face; place rim/back lights at negative Z.

### Node element ID

`node.elementID` is a **property**, not a method. Use `node.elementID`, not `node.getElementID()`.

### Browsing the content library

Use `DzDir` and `DzContentMgr` to browse content — do not shell out to `find` or similar OS commands:

```javascript
var mgr = App.getContentMgr();
var path = mgr.getContentDirectoryPath(i);   // returns a plain string
var dir = new DzDir(path + "/People");
var files = dir.entryList(["*.duf"], DzDir.Files);
```

Content directory objects (from `mgr.getContentDirectory(i)`) expose a `.fullPath` property.

### Light properties

| UI Label | Internal name |
|---|---|
| Luminous Flux (Lumen) | `Flux` |
| Shadow Softness | `Shadow Softness` |
| Spread Angle | `Spread Angle` |
| Photometric Mode | `Photometric Mode` |

### Iray environment / lighting mode

The `DzEnvironmentNode` is always `Scene.getNode(1)`. Set `"Environment Mode"` to `3` for scene-lights-only rendering:

```javascript
var envNode = Scene.getNode(1); // DzEnvironmentNode
envNode.findProperty("Environment Mode").setValue(3); // 3 = Scene Only
```

## Architecture

**Version:** 0.3.0 (includes Phase 4: Cinematic Director Workflow tools)

This is a [FastMCP](https://github.com/jlowin/fastmcp) 3.x server that bridges Claude (or any MCP client) to DAZ Studio via the **DazScriptServer** HTTP plugin. DAZ Studio must be running locally with DazScriptServer active on port 18811.

### Request flow

```
MCP client → FastMCP tool → httpx.AsyncClient → DazScriptServer (HTTP) → DAZ Studio
```

### Key design points

- **Single file server**: all tools live in `src/vangard_daz_mcp/server.py`. The `mcp` FastMCP instance is the module-level singleton.
- **Shared HTTP client**: a single `httpx.AsyncClient` is created at startup via the `lifespan` async context manager and stored in the module-level `_http_client` global. FastMCP 3.x removed `server.state`; the global variable is the correct pattern.
- **Authentication**: API token loaded with priority: `DAZ_API_TOKEN` env var → `~/.daz3d/dazscriptserver_token.txt` file → empty string (no auth). Token is read once at startup and sent via `X-API-Token` header on all requests.
- **Script registry**: High-level tools register their DazScript implementations with DazScriptServer at startup via `POST /scripts/register`. Subsequent calls use `POST /scripts/:id/execute` (no script retransmission). On 404 (DAZ Studio restarted, registry cleared), the server auto-reregisters and retries.
- **`_execute()` helper**: low-level execution helper used by `daz_execute`. Sends `POST /execute` with inline script, handles HTTP errors and `success: false` → `ToolError`.
- **`_execute_by_id()` helper**: high-level execution helper used by all structured tools. Calls registered scripts by ID, auto-reregisters on 404, converts failures to `ToolError`.
- **DazScript constants**: embedded scripts are module-level string constants (`_SCENE_INFO_SCRIPT` etc.) and registered in `_REGISTRY` dict. This keeps script logic visible and editable without hunting through function bodies.
- **Configuration**: `DAZ_HOST`, `DAZ_PORT`, `DAZ_TIMEOUT`, `DAZ_API_TOKEN` environment variables are read at module import time. Changing them requires a server restart.

### DazScriptServer API surface

| Endpoint | Used by | Purpose |
|----------|---------|---------|
| `GET /status` | `daz_status` | Check connectivity and version |
| `POST /execute` with `script` | `daz_execute` | Execute inline DazScript |
| `POST /execute` with `scriptFile` | `daz_execute_file` | Execute script file from disk |
| `POST /scripts/register` | `_register_scripts()` (startup) | Register named scripts for later execution |
| `POST /scripts/:id/execute` | All high-level tools | Execute previously registered script by ID |

**Script registry workflow:**
1. At startup, `_register_scripts()` registers 65 named scripts:
   - **Basic operations:** `vangard-scene-info`, `vangard-get-node`, `vangard-set-property`, `vangard-render`, `vangard-load-file`
   - **Morph discovery:** `vangard-list-morphs`, `vangard-search-morphs`
   - **Scene hierarchy:** `vangard-get-node-hierarchy`, `vangard-list-children`, `vangard-get-parent`, `vangard-set-parent`
   - **Multi-character interaction:** `vangard-look-at-point`, `vangard-look-at-character`, `vangard-reach-toward`, `vangard-interactive-pose`
   - **Batch operations:** `vangard-batch-set-properties`, `vangard-batch-transform`, `vangard-batch-visibility`, `vangard-batch-select`
   - **Viewport/camera control:** `vangard-set-active-camera`, `vangard-orbit-camera-around`, `vangard-frame-camera-to-node`, `vangard-save-camera-preset`, `vangard-load-camera-preset`
   - **Animation system:** `vangard-set-keyframe`, `vangard-get-keyframes`, `vangard-remove-keyframe`, `vangard-clear-animation`, `vangard-set-frame`, `vangard-set-frame-range`, `vangard-get-animation-info`
   - **Advanced rendering:** `vangard-render-with-camera`, `vangard-get-render-settings`, `vangard-batch-render-cameras`, `vangard-render-animation`
   - **Phase 4: Cinematic Director (v0.3.0):**
     - Shot sequences: `vangard-create-shot-sequence`, `vangard-animate-conversation`, `vangard-create-scene`
     - Camera animation: `vangard-animate-camera-movement`, `vangard-create-camera-path`
     - Character choreography: `vangard-create-character-path`, `vangard-arrange-characters`, `vangard-choreograph-action`
     - Cinematic coverage: `vangard-setup-shot-coverage`, `vangard-create-camera-rig`
2. High-level tools call `POST /scripts/:id/execute` with just args (no script body)
3. On 404 (DAZ Studio restarted), `_execute_by_id()` calls `_register_scripts()` and retries

**Arguments:** Both `/execute` and `/scripts/:id/execute` accept an optional `args` JSON object accessible inside the script as the variable `args`.

### Testing

- Tests call the tool functions **directly** (e.g. `await daz_status()`) — `@mcp.tool()` returns the original function unchanged.
- `respx` mocks HTTP at the transport level; each test gets a fresh `httpx.AsyncClient` via the `http_client` autouse fixture which also sets `server_module._http_client`.
- `asyncio_mode = "auto"` (set in `pyproject.toml`) — no `@pytest.mark.asyncio` needed on individual tests.
- Async fixtures require `@pytest_asyncio.fixture`, not plain `@pytest.fixture`.
