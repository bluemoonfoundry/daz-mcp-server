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

This server exposes 39 tools to MCP clients:

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

**Version:** 0.1.0 (early release, functional and tested)

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
1. At startup, `_register_scripts()` registers 35 named scripts:
   - **Basic operations:** `vangard-scene-info`, `vangard-get-node`, `vangard-set-property`, `vangard-render`, `vangard-load-file`
   - **Morph discovery:** `vangard-list-morphs`, `vangard-search-morphs`
   - **Scene hierarchy:** `vangard-get-node-hierarchy`, `vangard-list-children`, `vangard-get-parent`, `vangard-set-parent`
   - **Multi-character interaction:** `vangard-look-at-point`, `vangard-look-at-character`, `vangard-reach-toward`, `vangard-interactive-pose`
   - **Batch operations:** `vangard-batch-set-properties`, `vangard-batch-transform`, `vangard-batch-visibility`, `vangard-batch-select`
   - **Viewport/camera control:** `vangard-set-active-camera`, `vangard-orbit-camera-around`, `vangard-frame-camera-to-node`, `vangard-save-camera-preset`, `vangard-load-camera-preset`
   - **Animation system:** `vangard-set-keyframe`, `vangard-get-keyframes`, `vangard-remove-keyframe`, `vangard-clear-animation`, `vangard-set-frame`, `vangard-set-frame-range`, `vangard-get-animation-info`
   - **Advanced rendering:** `vangard-render-with-camera`, `vangard-get-render-settings`, `vangard-batch-render-cameras`, `vangard-render-animation`
2. High-level tools call `POST /scripts/:id/execute` with just args (no script body)
3. On 404 (DAZ Studio restarted), `_execute_by_id()` calls `_register_scripts()` and retries

**Arguments:** Both `/execute` and `/scripts/:id/execute` accept an optional `args` JSON object accessible inside the script as the variable `args`.

### Testing

- Tests call the tool functions **directly** (e.g. `await daz_status()`) — `@mcp.tool()` returns the original function unchanged.
- `respx` mocks HTTP at the transport level; each test gets a fresh `httpx.AsyncClient` via the `http_client` autouse fixture which also sets `server_module._http_client`.
- `asyncio_mode = "auto"` (set in `pyproject.toml`) — no `@pytest.mark.asyncio` needed on individual tests.
- Async fixtures require `@pytest_asyncio.fixture`, not plain `@pytest.fixture`.
