# vangard-daz-mcp

**Version 0.3.0** | MCP Server for DAZ Studio

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that exposes DAZ Studio operations to Claude and other MCP clients. Built on [FastMCP](https://github.com/jlowin/fastmcp) and wraps the [DazScriptServer](https://github.com/bluemoonfoundry/daz-script-server) HTTP plugin.

---

## What Is This?

This MCP server allows Claude (via Claude Desktop or other MCP clients) to control DAZ Studio directly:
- Query scene information (figures, cameras, lights, spatial positions)
- Read and modify node properties (transforms, morphs)
- Discover and apply morphs, including searching by name pattern
- Traverse and manipulate scene hierarchies (parent/child, skeleton)
- Apply emotional expressions to characters
- Coordinate multi-character interactions (look-at, reach-toward, hug, handshake)
- Execute batch operations (set multiple properties in one call, 5-10x faster)
- Control cameras and viewport (orbit, frame, presets)
- Create keyframe animations and export as image sequences
- Trigger synchronous or asynchronous renders with cancellation support
- Apply professional lighting presets and cinematography composition rules
- Browse and query the DAZ content library
- Save and restore named scene checkpoints
- **Generate complete scenes from natural language descriptions**
- **Create multi-camera shot sequences (orbit, push-in, shot-reverse-shot)**
- **Choreograph animated conversations with dialogue beats**
- **Record and replay operation macros for workflow automation**
- Execute arbitrary DazScript code
- Access comprehensive DazScript documentation and examples

The server acts as a bridge: **MCP Client** ↔ **vangard-daz-mcp** ↔ **DazScriptServer plugin** ↔ **DAZ Studio**

---

## Prerequisites

Before using this server, you need:

1. **DAZ Studio 4.5+** installed and running
2. **DazScriptServer plugin** installed, configured, and active
   - Download from: https://github.com/bluemoonfoundry/daz-script-server
   - Plugin must be running on port 18811 (default)
   - Authentication must be configured (API token)
3. **Python 3.11+** for running the MCP server
4. **uv** package manager (recommended) or pip

---

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/bluemoonfoundry/vangard-daz-mcp.git
cd vangard-daz-mcp

# Install dependencies
uv sync

# Run the server
uv run vangard-daz-mcp
```

### Using pip

```bash
# Install from source
pip install .

# Run the server
vangard-daz-mcp
```

---

## Configuration

### Environment Variables

Configure the server via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DAZ_HOST` | `localhost` | DazScriptServer hostname |
| `DAZ_PORT` | `18811` | DazScriptServer port |
| `DAZ_TIMEOUT` | `30.0` | Request timeout in seconds (increase for long renders) |
| `DAZ_API_TOKEN` | *(from file)* | API token for authentication |

### Authentication

The server automatically reads the API token from `~/.daz3d/dazscriptserver_token.txt` (the file created by DazScriptServer).

**Override with environment variable:**
```bash
export DAZ_API_TOKEN="your-token-here"
```

**Important:** DazScriptServer must have authentication enabled (default). The MCP server cannot connect without a valid token.

---

## Claude Desktop Configuration

Add this to your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "daz-studio": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/vangard-daz-mcp",
        "run",
        "vangard-daz-mcp"
      ],
      "env": {
        "DAZ_TIMEOUT": "60.0"
      }
    }
  }
}
```

**Note:** Replace `/absolute/path/to/vangard-daz-mcp` with the actual path on your system.

After saving the config, restart Claude Desktop. The DAZ Studio tools will appear in Claude's tool palette.

---

## Available Tools

### 📚 Documentation Tools

#### `daz_script_help`
Get DazScript documentation, examples, and best practices.

**Arguments:**
- `topic` (string, default `"overview"`): Documentation topic to retrieve

**Available Topics:**
- `overview` - DazScript environment basics
- `gotchas` - Critical mistakes that cause timeouts or errors
- `camera` - Camera creation, positioning, and aiming
- `light` - Light creation, types, and three-point lighting
- `environment` - Iray environment settings and lighting modes
- `scene` - Scene management (new, save, load, selection)
- `properties` - Node properties, transforms, and morphs
- `content` - Browsing and loading content from library
- `coordinates` - Coordinate system and positioning reference
- `posing` - Figure posing, bone hierarchy, morphs vs poses, rotation gotchas
- `morphs` - Morph discovery, searching, value ranges, and management
- `hierarchy` - Scene hierarchy, parent-child relationships, parenting operations
- `interaction` - Multi-character interaction, look-at mechanics, world-space posing
- `batch` - Batch operations patterns and performance optimization
- `viewport` - Viewport and camera control, spherical positioning, presets
- `animation` - Keyframe animation, timeline control, image sequence export
- `rendering` - Rendering workflows, multi-camera, batch render, animation export

**Returns:** Formatted documentation with examples

**Use when:** Before writing custom DazScript code to learn correct patterns and avoid common mistakes.

**Example:**
```
daz_script_help("camera")  # Get camera documentation
daz_script_help("gotchas") # Learn critical gotchas
```

---

### 🔍 Inspection Tools

#### `daz_status`
Check DAZ Studio connectivity and version.

**Returns:**
```json
{
  "running": true,
  "version": "1.3.0"
}
```

**Use when:** Verifying DAZ Studio is running and the connection works.

---

#### `daz_scene_info`
Get a snapshot of the current scene.

**Returns:**
```json
{
  "sceneFile": "/path/to/scene.duf",
  "selectedNode": "Genesis 9",
  "figures": [
    {"name": "Genesis9", "label": "Genesis 9", "type": "DzFigure"}
  ],
  "cameras": [
    {"name": "Camera", "label": "Camera 1"}
  ],
  "lights": [
    {"name": "DistantLight", "label": "Distant Light", "type": "DzDistantLight"}
  ],
  "totalNodes": 3247
}
```

**Use when:** You need an overview of what's in the scene (characters, cameras, lights).

**Note:** Does not enumerate all nodes (scenes can have 1000+ nodes). Use `daz_execute` for fine-grained queries.

---

#### `daz_get_node`
Read all numeric properties of a node by its label or internal name.

**Arguments:**
- `node_label` (string): Display label or internal name (e.g., "Genesis 9")

**Returns:**
```json
{
  "name": "Genesis9",
  "label": "Genesis 9",
  "type": "DzFigure",
  "properties": {
    "X Translate": 0.0,
    "Y Translate": 0.0,
    "Z Translate": 0.0,
    "X Rotate": 0.0,
    "Y Rotate": 0.0,
    "Z Rotate": 0.0,
    "Scale": 100.0,
    "Head Size": 0.5
  }
}
```

**Use when:** You need to read transforms, morphs, or other numeric properties on a node.

---

### 🔬 Morph Discovery Tools

#### `daz_list_morphs`
List all morphs (numeric properties) on a node with their current values.

**Arguments:**
- `node_label` (string): Node display label or internal name
- `include_zero` (bool, default `False`): Include morphs with zero values

**Returns:**
```json
{
  "morphs": [
    {"label": "Height", "name": "Height", "value": 1.05, "path": "Morphs/Body"},
    {"label": "Head Size", "name": "HeadSize", "value": 0.9, "path": "Morphs/Head"}
  ],
  "count": 2,
  "nodeLabel": "Genesis 9"
}
```

**Use when:**
- Discovering what morphs are available on a figure
- Checking which morphs are currently active
- Building morph selection UIs
- Exploring character customization options

**Example:**
```
# List only active morphs (non-zero values)
daz_list_morphs("Genesis 9", include_zero=False)

# List ALL available morphs (warning: may return 500-1000+ morphs)
daz_list_morphs("Genesis 9", include_zero=True)
```

**Note:** Genesis figures can have 1000+ morphs. Use `include_zero=False` to see only active morphs, or use `daz_search_morphs` to filter by pattern.

---

#### `daz_search_morphs`
Search for morphs matching a name pattern.

**Arguments:**
- `node_label` (string): Node display label or internal name
- `pattern` (string): Substring to search for (case-insensitive)
- `include_zero` (bool, default `False`): Include morphs with zero values

**Returns:**
```json
{
  "morphs": [
    {"label": "Smile", "name": "Smile", "value": 0.0, "path": "Morphs/Expressions"},
    {"label": "Smile Open", "name": "SmileOpen", "value": 0.0, "path": "Morphs/Expressions"}
  ],
  "count": 2,
  "pattern": "smile",
  "nodeLabel": "Genesis 9"
}
```

**Use when:**
- Finding specific morphs (e.g., all smile morphs, head morphs)
- Discovering morphs by category or body part
- Building filtered morph lists

**Example:**
```
# Find all smile-related morphs
daz_search_morphs("Genesis 9", "smile", include_zero=True)

# Find active head morphs only
daz_search_morphs("Genesis 9", "head", include_zero=False)

# Find all facial expression morphs
daz_search_morphs("Genesis 9", "express", include_zero=True)
```

**Common search patterns:**
- `"smile"`, `"frown"`, `"express"` - Facial expressions
- `"head"`, `"face"`, `"nose"` - Facial features
- `"arm"`, `"leg"`, `"body"` - Body parts
- `"muscle"`, `"tone"`, `"fit"` - Body definition
- `"height"`, `"scale"` - Size adjustments

---

### 🌳 Scene Hierarchy Tools

#### `daz_get_node_hierarchy`
Get complete hierarchy tree for a node with all descendants.

**Arguments:**
- `node_label` (string): Root node display label or internal name
- `max_depth` (int, default `10`): Maximum recursion depth (0 = unlimited)

**Returns:**
```json
{
  "node": "Genesis 9",
  "hierarchy": {
    "label": "Genesis 9",
    "name": "Genesis9",
    "type": "DzFigure",
    "children": [
      {
        "label": "hip",
        "name": "hip",
        "type": "DzBone",
        "children": [...]
      }
    ]
  },
  "totalDescendants": 127
}
```

**Use when:**
- Understanding skeleton structure
- Exploring bone relationships
- Mapping complex scene hierarchies
- Finding all descendants of a node

**Example:**
```
# Get skeleton hierarchy with depth limit
daz_get_node_hierarchy("Genesis 9", max_depth=3)

# Get full hierarchy (warning: Genesis 9 has 100+ bones)
daz_get_node_hierarchy("Genesis 9", max_depth=0)
```

---

#### `daz_list_children`
List direct children of a node.

**Arguments:**
- `node_label` (string): Parent node display label or internal name

**Returns:**
```json
{
  "node": "hip",
  "children": [
    {"label": "pelvis", "name": "pelvis", "type": "DzBone"},
    {"label": "lThighBend", "name": "lThighBend", "type": "DzBone"},
    {"label": "rThighBend", "name": "rThighBend", "type": "DzBone"}
  ],
  "count": 3
}
```

**Use when:**
- Exploring hierarchy one level at a time
- Checking if a node has children
- Building custom tree structures

**Example:**
```
# List children of Genesis 9 root
daz_list_children("Genesis 9")

# Check if node has children
result = daz_list_children("Camera 1")
if result["count"] == 0:
    print("No children")
```

---

#### `daz_get_parent`
Get parent node of a node.

**Arguments:**
- `node_label` (string): Child node display label or internal name

**Returns:**
```json
{
  "node": "lHand",
  "parent": {
    "label": "lForearmBend",
    "name": "lForearmBend",
    "type": "DzBone"
  }
}
```

Returns `null` for parent if node is a root (no parent).

**Use when:**
- Traversing hierarchy upward
- Finding what contains a node
- Checking if node is a root

**Example:**
```
# Get parent of a bone
result = daz_get_parent("lHand")
print(f"Parent: {result['parent']['label']}")

# Check if node is root
result = daz_get_parent("Genesis 9")
if result["parent"] is None:
    print("This is a root node")
```

---

#### `daz_set_parent`
Set parent of a node (parenting operation).

**Arguments:**
- `node_label` (string): Node to parent
- `parent_label` (string): New parent node
- `maintain_world_transform` (bool, default `True`): If true, adjust local transform to keep same world position

**Returns:**
```json
{
  "success": true,
  "node": "Sword",
  "newParent": "rHand",
  "previousParent": null
}
```

**Use when:**
- Attaching props to figures (e.g., weapon to hand)
- Parenting cameras to nodes
- Reorganizing scene hierarchy
- Attaching clothing to bones

**Example:**
```
# Attach sword to right hand (maintains position)
daz_set_parent("Sword", "rHand", maintain_world_transform=True)

# Parent camera to figure (follows figure)
daz_set_parent("Camera 1", "Genesis 9", maintain_world_transform=True)

# Attach bracelet to forearm
daz_set_parent("Bracelet", "lForearmBend", maintain_world_transform=True)
```

**Note:** When `maintain_world_transform=True`, the node's world position stays the same, but local transform values (X/Y/Z Translate, Rotate) change to account for the new parent's transform.

---

### ⚡ Batch Operations

Batch operations allow you to modify multiple nodes or properties in a single call, significantly improving performance. Each operation has individual error handling, so failures don't abort the entire batch.

**Performance benefits:**
- Single script call (all operations execute in one round-trip)
- No HTTP/network overhead between operations
- 5-10x faster than individual calls for typical batches
- Individual error handling without aborting the batch

**Common use cases:**
- Applying facial expressions (multiple morphs at once)
- Configuring lighting setups (multiple light properties)
- Moving/rotating groups of props together
- Showing/hiding groups of nodes for scene management
- Resetting multiple cameras or lights to default values

#### `daz_batch_set_properties`
Set multiple properties on one or more nodes in a single call.

**Arguments:**
- `operations` (array): List of operation objects, each containing:
  - `nodeLabel` (string): Display label of the node
  - `propertyName` (string): Property label or internal name
  - `value` (float): New value for the property

**Returns:**
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

**Use when:** Setting 3+ properties, applying facial expressions, configuring scene presets.

**Example:**
```
# Apply "surprised" facial expression
daz_batch_set_properties([
    {"nodeLabel": "Genesis 9", "propertyName": "PHMEyesWide", "value": 0.8},
    {"nodeLabel": "Genesis 9", "propertyName": "PHMBrowsUp", "value": 0.7},
    {"nodeLabel": "Genesis 9", "propertyName": "PHMMouthOpen", "value": 0.4}
])

# Configure lighting setup
daz_batch_set_properties([
    {"nodeLabel": "Key Light", "propertyName": "Flux", "value": 2000},
    {"nodeLabel": "Fill Light", "propertyName": "Flux", "value": 800},
    {"nodeLabel": "Rim Light", "propertyName": "Flux", "value": 2500}
])
```

**Performance:** Setting 10 morphs via batch is ~5-10x faster than 10 individual `daz_set_property` calls.

---

#### `daz_batch_transform`
Apply the same transform properties to multiple nodes.

**Arguments:**
- `node_labels` (array): List of node display labels to transform
- `transforms` (object): Dictionary of property names to values (e.g., `{"XTranslate": 50, "YRotate": 45}`)

**Returns:**
```json
{
  "results": [
    {"success": true, "node": "Prop1", "applied": ["X Translate", "Y Rotate"]},
    {"success": false, "node": "Missing", "error": "Node not found: Missing"}
  ],
  "successCount": 1,
  "failureCount": 1,
  "total": 2
}
```

**Use when:** Moving, rotating, or scaling multiple objects by the same amount.

**Example:**
```
# Move multiple props to the right
daz_batch_transform(
    ["Chair", "Table", "Lamp"],
    {"XTranslate": 100}
)

# Rotate and scale multiple objects
daz_batch_transform(
    ["Prop1", "Prop2", "Prop3"],
    {"YRotate": 45, "Scale": 1.2}
)

# Reset rotation for all cameras
daz_batch_transform(
    ["Camera 1", "Camera 2", "Camera 3"],
    {"XRotate": 0, "YRotate": 0, "ZRotate": 0}
)
```

**Note:** Only properties that exist on each node are applied. Missing properties are silently skipped.

---

#### `daz_batch_visibility`
Show or hide multiple nodes in the viewport and renders.

**Arguments:**
- `node_labels` (array): List of node display labels to modify
- `visible` (bool, default `True`): True to show nodes, False to hide them

**Returns:**
```json
{
  "results": [
    {"success": true, "node": "Ground", "visible": false},
    {"success": true, "node": "Sky Dome", "visible": false}
  ],
  "successCount": 2,
  "failureCount": 0,
  "total": 2
}
```

**Use when:** Scene management, testing configurations, optimizing render times.

**Example:**
```
# Hide all cameras
daz_batch_visibility(["Camera 1", "Camera 2", "Camera 3"], visible=False)

# Hide environment elements for character close-up
daz_batch_visibility(["Ground", "Sky Dome", "Background"], visible=False)

# Show all weapons
daz_batch_visibility(["Sword", "Shield", "Helmet"], visible=True)
```

**Note:** Hidden nodes remain in the scene but are not visible in viewport or renders.

---

#### `daz_batch_select`
Select multiple nodes in the DAZ Studio scene.

**Arguments:**
- `node_labels` (array): List of node display labels to select
- `add_to_selection` (bool, default `False`): If True, add to current selection; if False, replace current selection

**Returns:**
```json
{
  "selected": ["Genesis 9", "Genesis 8 Female"],
  "count": 2,
  "total": 2
}
```

**Use when:** Selecting groups of nodes for inspection or operations.

**Example:**
```
# Select multiple characters
daz_batch_select(["Genesis 9", "Genesis 8 Female"])

# Add props to current selection
daz_batch_select(["Sword", "Shield"], add_to_selection=True)

# Select all lights
daz_batch_select(["Spot Light 1", "Distant Light 1", "Point Light 1"])
```

**Note:** Nodes that don't exist are silently skipped. Returns count of successful selections.

---

### 📷 Viewport and Camera Control

Viewport control tools enable programmatic camera positioning, framing, and preset management for automated scene photography and consistent camera angles.

**Key capabilities:**
- Switch active viewport camera
- Position camera using spherical coordinates (orbit around target)
- Auto-frame camera to show objects (calculates bounding box)
- Save/load camera positions as presets (JSON-serializable)
- Reusable camera angles across scenes

#### `daz_set_active_camera`
Set which camera is active in the DAZ Studio viewport.

**Arguments:**
- `camera_label` (string): Display label of the camera to activate

**Returns:**
```json
{
  "success": true,
  "camera": "Camera 1",
  "previousCamera": "Perspective View"
}
```

**Use when:** Switching between predefined camera angles, previewing from multiple viewpoints.

**Example:**
```
# Switch to specific camera
daz_set_active_camera("Camera 1")

# Switch back to default
daz_set_active_camera("Perspective View")
```

---

#### `daz_orbit_camera_around`
Position camera orbiting around a target node at specified angle and distance.

**Arguments:**
- `camera_label` (string): Camera to position
- `target_label` (string): Target node to orbit around
- `distance` (float, default `200.0`): Distance from target in cm
- `angle_horizontal` (float, default `45.0`): Horizontal angle in degrees (0=front/+Z, 90=right/+X)
- `angle_vertical` (float, default `15.0`): Vertical angle in degrees (positive=above)

**Returns:**
```json
{
  "success": true,
  "camera": "Camera 1",
  "target": "Genesis 9",
  "position": {"x": 141.4, "y": 151.8, "z": 141.4},
  "targetPosition": {"x": 0, "y": 100, "z": 0}
}
```

**Use when:** Character photography, product shots, turntable animations, establishing camera angles.

**Example:**
```
# Front 3/4 view (classic portrait angle)
daz_orbit_camera_around("Camera 1", "Genesis 9",
                        distance=200, angle_horizontal=45, angle_vertical=15)

# Side view from left
daz_orbit_camera_around("Camera 1", "Genesis 9",
                        distance=150, angle_horizontal=-90, angle_vertical=0)

# Bird's eye view
daz_orbit_camera_around("Camera 1", "Genesis 9",
                        distance=300, angle_horizontal=0, angle_vertical=60)

# Dramatic low angle
daz_orbit_camera_around("Camera 1", "Genesis 9",
                        distance=180, angle_horizontal=25, angle_vertical=-20)
```

**Angle reference:**
- Horizontal: 0°=front(+Z), 90°=right(+X), 180°=back(-Z), -90°=left(-X)
- Vertical: positive=above horizon, negative=below

**Distance guidelines** (170cm tall figure):
- Full body: 350-450cm
- Portrait: 80-120cm
- Face close-up: 30-50cm

---

#### `daz_frame_camera_to_node`
Frame camera to show a node by positioning at calculated distance.

**Arguments:**
- `camera_label` (string): Camera to position
- `node_label` (string): Node to frame
- `distance` (float, optional): Distance from node center in cm. If not specified, auto-calculated as 2.5x largest bounding box dimension.

**Returns:**
```json
{
  "success": true,
  "camera": "Camera 1",
  "node": "Genesis 9",
  "position": {"x": 0, "y": 100, "z": 450},
  "nodeCenter": {"x": 0, "y": 100, "z": 0},
  "nodeSize": {"x": 50, "y": 170, "z": 40}
}
```

**Use when:** Auto-framing objects of varying sizes, consistent framing across scenes.

**Example:**
```
# Frame character (auto distance)
daz_frame_camera_to_node("Camera 1", "Genesis 9")

# Frame prop with specific distance
daz_frame_camera_to_node("Camera 1", "Sword", distance=50)

# Close-up on head
daz_frame_camera_to_node("Camera 1", "head", distance=30)
```

**Note:** Camera is positioned in front (+Z) and aimed at node's bounding box center. Auto-calculated distance is 2.5x the largest dimension.

---

#### `daz_save_camera_preset`
Save camera position and rotation as preset data.

**Arguments:**
- `camera_label` (string): Camera to save

**Returns:**
```json
{
  "preset": {
    "label": "Camera 1",
    "transforms": {
      "XTranslate": 0, "YTranslate": 100, "ZTranslate": 300,
      "XRotate": -10, "YRotate": 0, "ZRotate": 0,
      "XScale": 1.0, "YScale": 1.0, "ZScale": 1.0
    }
  }
}
```

**Use when:** Saving reusable camera angles, sharing camera positions across projects.

**Example:**
```python
# Save camera position
preset = daz_save_camera_preset("Camera 1")

# Store to file
import json
with open("portrait_camera.json", "w") as f:
    json.dump(preset, f)
```

**Note:** Preset data is JSON-serializable and can be applied to any camera.

---

#### `daz_load_camera_preset`
Restore camera position and rotation from preset data.

**Arguments:**
- `camera_label` (string): Camera to modify
- `preset` (dict): Preset dictionary from `daz_save_camera_preset()` (must contain `transforms` key)

**Returns:**
```json
{
  "success": true,
  "camera": "Camera 1",
  "applied": ["XTranslate", "YTranslate", "ZTranslate", "XRotate", "YRotate", "ZRotate"]
}
```

**Use when:** Restoring saved camera positions, applying same angle to multiple cameras.

**Example:**
```python
# Load preset from file
import json
with open("portrait_camera.json") as f:
    preset = json.load(f)

# Apply to camera
daz_load_camera_preset("Camera 1", preset["preset"])

# Apply same preset to multiple cameras
for cam in ["Camera 1", "Camera 2", "Camera 3"]:
    daz_load_camera_preset(cam, preset["preset"])
```

**Note:** Preset can be applied to any camera, not just the original. Useful for synchronizing multiple cameras.

---

### 🎬 Animation System

Animation tools enable keyframe-based property animation. Set keyframes at specific frames, and DAZ Studio interpolates smoothly between them. Supports animating any numeric property (transforms, morphs, lights, cameras).

**Key capabilities:**
- Set/get/remove keyframes on properties
- Timeline control (current frame, frame range)
- Export animations as image sequences
- Copy and offset animations between properties
- Inspect keyframe data programmatically

**Common use cases:**
- Character animation (walk cycles, gestures, facial expressions)
- Camera animation (dolly, pan, zoom)
- Product turntables (360° rotation)
- Morph animations (smile fade, eye blink)
- Multi-character choreography

#### `daz_set_keyframe`
Set a keyframe on a property at specified frame.

**Arguments:**
- `node_label` (string): Node display label
- `property_name` (string): Property label or internal name
- `frame` (int): Frame number (0-based)
- `value` (float): Value at this frame

**Returns:**
```json
{
  "success": true,
  "node": "Genesis 9",
  "property": "X Translate",
  "frame": 0,
  "value": 0.0
}
```

**Use when:** Creating animations, defining key poses.

**Example:**
```
# Animate movement (0 to 100cm over 30 frames)
daz_set_keyframe("Genesis 9", "XTranslate", frame=0, value=0)
daz_set_keyframe("Genesis 9", "XTranslate", frame=30, value=100)

# Animate rotation (0 to 90 degrees)
daz_set_keyframe("Genesis 9", "YRotate", frame=0, value=0)
daz_set_keyframe("Genesis 9", "YRotate", frame=60, value=90)

# Animate morph (fade in smile)
daz_set_keyframe("Genesis 9", "PHMSmile", frame=0, value=0)
daz_set_keyframe("Genesis 9", "PHMSmile", frame=15, value=0.8)
```

**Note:** DAZ Studio interpolates between keyframes automatically. Setting keyframe at existing frame updates the value.

---

#### `daz_get_keyframes`
Get all keyframes for a property.

**Arguments:**
- `node_label` (string): Node display label
- `property_name` (string): Property label or internal name

**Returns:**
```json
{
  "keyframes": [
    {"frame": 0, "value": 0.0},
    {"frame": 30, "value": 100.0}
  ],
  "count": 2
}
```

**Use when:** Inspecting animations, copying keyframes, checking if property is animated.

**Example:**
```python
# Get keyframes
result = daz_get_keyframes("Genesis 9", "XTranslate")
for kf in result['keyframes']:
    print(f"Frame {kf['frame']}: {kf['value']}")

# Copy keyframes to another node
for kf in result['keyframes']:
    daz_set_keyframe("Genesis 8", "XTranslate", kf['frame'], kf['value'])
```

---

#### `daz_remove_keyframe`
Remove a keyframe at specified frame.

**Arguments:**
- `node_label` (string): Node display label
- `property_name` (string): Property label or internal name
- `frame` (int): Frame number

**Returns:**
```json
{
  "success": true,
  "node": "Genesis 9",
  "property": "X Translate",
  "frame": 15,
  "removed": true
}
```

**Use when:** Removing specific keyframes, editing animation timing.

**Example:**
```
# Remove keyframe
daz_remove_keyframe("Genesis 9", "XTranslate", frame=15)
```

**Note:** Returns `removed: false` if no keyframe exists at that frame (not an error).

---

#### `daz_clear_animation`
Remove all keyframes from a property.

**Arguments:**
- `node_label` (string): Node display label
- `property_name` (string): Property label or internal name

**Returns:**
```json
{
  "success": true,
  "node": "Genesis 9",
  "property": "X Translate",
  "removed": 5
}
```

**Use when:** Clearing animations, resetting properties to static state.

**Example:**
```python
# Clear animation
result = daz_clear_animation("Genesis 9", "XTranslate")
print(f"Removed {result['removed']} keyframes")

# Clear all transform animations
for prop in ["XTranslate", "YTranslate", "ZTranslate", "XRotate", "YRotate", "ZRotate"]:
    daz_clear_animation("Genesis 9", prop)
```

**Note:** More efficient than removing keyframes individually.

---

#### `daz_set_frame`
Set current animation frame.

**Arguments:**
- `frame` (int): Frame number to move to

**Returns:**
```json
{
  "success": true,
  "frame": 30,
  "previousFrame": 0
}
```

**Use when:** Previewing animation, rendering specific frames.

**Example:**
```python
# Jump to frame 30
daz_set_frame(30)

# Render all frames
info = daz_get_animation_info()
for frame in range(info['startFrame'], info['endFrame'] + 1):
    daz_set_frame(frame)
    daz_render(output_path=f"frame_{frame:04d}.png")
```

**Note:** Scene updates to show animated state at the frame.

---

#### `daz_set_frame_range`
Set animation frame range (start and end).

**Arguments:**
- `start_frame` (int): First frame (typically 0)
- `end_frame` (int): Last frame

**Returns:**
```json
{
  "success": true,
  "startFrame": 0,
  "endFrame": 119,
  "previousStart": 0,
  "previousEnd": 30
}
```

**Use when:** Defining animation length before creating keyframes.

**Example:**
```
# 4-second animation (120 frames at 30fps)
daz_set_frame_range(0, 119)

# 10-second animation
daz_set_frame_range(0, 299)
```

**Note:** Frame range is inclusive (frames 0-119 = 120 frames). Duration = (end - start + 1) / fps.

---

#### `daz_get_animation_info`
Get animation timeline info (current frame, range, fps).

**Returns:**
```json
{
  "currentFrame": 0,
  "startFrame": 0,
  "endFrame": 119,
  "fps": 30.0,
  "totalFrames": 120,
  "durationSeconds": 4.0
}
```

**Use when:** Checking timeline state before rendering, calculating duration.

**Example:**
```python
# Get timeline info
info = daz_get_animation_info()
print(f"Animation: {info['durationSeconds']} seconds ({info['totalFrames']} frames)")

# Render entire animation
for frame in range(info['startFrame'], info['endFrame'] + 1):
    daz_set_frame(frame)
    daz_render(output_path=f"frame_{frame:04d}.png")
```

**Note:** FPS is typically 30 in DAZ Studio.

---

### 🎥 Advanced Rendering Control

Advanced rendering tools provide programmatic control for multi-camera rendering, animation export, and batch rendering operations.

**Key capabilities:**
- Render from specific camera without changing viewport
- Batch render from multiple cameras
- Export animations as image sequences
- Query render settings
- Automated rendering workflows

**Common use cases:**
- Multi-angle product shots (front, side, top, perspective)
- Character turntables (8-16 camera angles)
- Animation export (frame-by-frame image sequences)
- Test renders from multiple angles
- Multi-camera animation rendering

#### `daz_render_with_camera`
Render from specific camera without changing active viewport camera.

**Arguments:**
- `camera_label` (string): Camera to render from
- `output_path` (string, optional): Output file path (if not specified, renders to viewport)

**Returns:**
```json
{
  "success": true,
  "camera": "Camera 1",
  "outputPath": "/path/to/render.png"
}
```

**Use when:** Multi-camera batch renders, testing camera angles without disrupting viewport.

**Example:**
```python
# Render from specific camera
daz_render_with_camera("Camera 1", output_path="/renders/cam1.png")

# Render from multiple cameras
for cam in ["Front", "Side", "Top"]:
    daz_render_with_camera(cam, output_path=f"/renders/{cam}.png")
```

**Note:** Viewport camera remains unchanged. Previous render camera is restored automatically.

---

#### `daz_get_render_settings`
Get current render settings and configuration.

**Returns:**
```json
{
  "renderToFile": true,
  "outputPath": "/path/to/output.png",
  "currentCamera": "Camera 1",
  "aspectRatio": 1.777,
  "aspectWidth": 16,
  "aspectHeight": 9
}
```

**Use when:** Verifying render configuration before batch operations, debugging render issues.

**Example:**
```python
# Check render settings
settings = daz_get_render_settings()
print(f"Render camera: {settings['currentCamera']}")
print(f"Aspect: {settings['aspectWidth']}x{settings['aspectHeight']}")

# Verify configuration
if not settings['renderToFile']:
    print("Warning: Render configured for viewport, not file")
```

---

#### `daz_batch_render_cameras`
Render from multiple cameras in sequence.

**Arguments:**
- `cameras` (list[string]): List of camera labels
- `output_dir` (string): Output directory
- `base_filename` (string, default `"render"`): Base filename (camera name is appended)

**Returns:**
```json
{
  "success": true,
  "rendered": [
    {"camera": "Front", "outputPath": "/renders/product_Front.png"},
    {"camera": "Side", "outputPath": "/renders/product_Side.png"}
  ],
  "total": 2
}
```

**Use when:** Product photography, turntable renders, multi-angle test renders.

**Example:**
```python
# Render from multiple cameras
daz_batch_render_cameras(
    cameras=["Front", "Side", "Top", "Perspective"],
    output_dir="/renders",
    base_filename="product"
)
# Generates: product_Front.png, product_Side.png, product_Top.png, product_Perspective.png

# Turntable (8 cameras around character)
cameras = [f"Cam_{angle}" for angle in [0, 45, 90, 135, 180, 225, 270, 315]]
daz_batch_render_cameras(cameras, "/renders/turntable", "angle")
```

**Note:** Camera names in filenames have non-alphanumeric chars replaced with underscores. Previous render camera is restored after batch.

---

#### `daz_render_animation`
Render animation frame range as image sequence.

**Arguments:**
- `output_dir` (string): Output directory
- `start_frame` (int, optional): First frame (default: animation range start)
- `end_frame` (int, optional): Last frame (default: animation range end)
- `filename_pattern` (string, default `"frame"`): Filename pattern (frame number appended)
- `camera` (string, optional): Camera to render from (default: current render camera)

**Returns:**
```json
{
  "success": true,
  "rendered": [
    {"frame": 0, "outputPath": "/animation/frame_0000.png"},
    {"frame": 1, "outputPath": "/animation/frame_0001.png"}
  ],
  "total": 120,
  "frames": {"start": 0, "end": 119}
}
```

**Use when:** Exporting animations, creating video sequences.

**Example:**
```python
# Render entire animation (uses animation range)
daz_render_animation(output_dir="/animation")
# Generates: frame_0000.png, frame_0001.png, ..., frame_0119.png

# Render specific frame range
daz_render_animation(
    output_dir="/animation/clip",
    start_frame=30,
    end_frame=60,
    filename_pattern="clip"
)

# Render animation from specific camera
daz_render_animation(
    output_dir="/animation",
    camera="Camera 1"
)

# Convert to video (using ffmpeg)
# ffmpeg -framerate 30 -i frame_%04d.png -c:v libx264 -pix_fmt yuv420p output.mp4
```

**Note:** Frame numbers zero-padded to 4 digits (0000-9999). Timeline position and render camera restored after completion.

---

### 📐 Spatial Query Tools

These tools let you query the world-space position, size, and relationships of scene nodes.

#### `daz_get_world_position`
Get world-space position, local position, rotation, and scale of a node.

**Arguments:**
- `node_label` (string): Node display label or internal name

**Returns:**
```json
{
  "node": "Genesis 9",
  "worldPosition": {"x": 0, "y": 0, "z": 0},
  "localPosition": {"x": 0, "y": 0, "z": 0},
  "rotation": {"x": 0, "y": 0, "z": 0},
  "scale": {"x": 1, "y": 1, "z": 1}
}
```

**Use when:** Finding exact world coordinates of a character or prop before placing another object relative to it.

---

#### `daz_get_bounding_box`
Get bounding box (min/max corners, center, dimensions) of a node.

**Arguments:**
- `node_label` (string): Node display label or internal name

**Returns:**
```json
{
  "node": "Genesis 9",
  "min": {"x": -30, "y": 0, "z": -15},
  "max": {"x": 30, "y": 170, "z": 15},
  "center": {"x": 0, "y": 85, "z": 0},
  "width": 60, "height": 170, "depth": 30
}
```

**Use when:** Auto-framing cameras, checking object sizes, placing objects on surfaces.

---

#### `daz_calculate_distance`
Calculate distance and direction vector between two nodes.

**Arguments:**
- `from_label` (string): Source node
- `to_label` (string): Target node

**Returns:**
```json
{
  "from": "Alice",
  "to": "Bob",
  "distance": 120.5,
  "direction": {"x": 0.707, "y": 0, "z": 0.707}
}
```

**Use when:** Checking if two characters are within interaction range, positioning props relative to figures.

---

#### `daz_get_spatial_relationship`
Natural-language spatial relationship between two nodes.

**Arguments:**
- `from_label` (string): Reference node
- `to_label` (string): Target node

**Returns:**
```json
{
  "from": "Camera 1",
  "to": "Genesis 9",
  "distance": 300.0,
  "direction": "in front of",
  "angle": 5.2,
  "overlap": false
}
```

**Use when:** Describing scene layout in natural language, verifying camera placement.

---

#### `daz_check_overlap`
Check if two nodes have overlapping bounding boxes.

**Arguments:**
- `node1_label` (string): First node
- `node2_label` (string): Second node

**Returns:**
```json
{
  "overlapping": true,
  "penetrationDepth": {"x": 2.1, "y": 0, "z": 0}
}
```

**Use when:** Detecting interpenetration between characters, validating poses before rendering.

---

### 🔬 Property Introspection Tools

#### `daz_inspect_properties`
List all properties on a node, optionally filtered by type.

**Arguments:**
- `node_label` (string): Node display label or internal name
- `filter_type` (string, default `"all"`): One of `"all"`, `"numeric"`, `"transform"`, `"morph"`, `"bool"`, `"string"`

**Returns:**
```json
{
  "node": "Spot Light 1",
  "properties": [
    {"label": "Flux", "name": "Flux", "type": "numeric", "value": 1500},
    {"label": "Shadow Softness", "name": "Shadow Softness", "type": "numeric", "value": 0.5}
  ],
  "count": 2
}
```

**Use when:** Discovering what properties are settable on a node (lights, cameras, props).

**Example:**
```
# List all numeric properties on a spotlight
daz_inspect_properties("Spot Light 1", filter_type="numeric")

# List transform properties only
daz_inspect_properties("Genesis 9", filter_type="transform")
```

---

#### `daz_get_property_metadata`
Get detailed metadata (min, max, default, type, path) for a single property.

**Arguments:**
- `node_label` (string): Node display label or internal name
- `property_name` (string): Property label or internal name

**Returns:**
```json
{
  "node": "Spot Light 1",
  "property": "Flux",
  "type": "numeric",
  "value": 1500,
  "default": 1500,
  "min": 0,
  "max": 100000,
  "path": "General/Luminous Flux"
}
```

**Use when:** Finding valid ranges before setting a property, validating property names.

---

#### `daz_validate_script`
Static analysis of DazScript code for known anti-patterns. Does not require a DAZ Studio connection.

**Arguments:**
- `script` (string): DazScript source code to analyze

**Returns:**
```json
{
  "valid": false,
  "issues": [
    {"severity": "error", "line": 3, "message": "Bare return at top level — wrap in IIFE"},
    {"severity": "warning", "line": 7, "message": "getElementID() is not a function — use .elementID property"}
  ],
  "issueCount": 2
}
```

**Use when:** Before running a custom script via `daz_execute`, to catch common mistakes early.

---

### 💡 Lighting Preset Tools

#### `daz_apply_lighting_preset`
Create a professional lighting setup in one command.

**Arguments:**
- `preset` (string): Lighting preset name
- `subject_label` (string): Node to light (preset positions lights relative to subject's bounding box)

**Presets:**
- `three-point` — Key (front-right) + Fill (front-left) + Rim (back). General-purpose.
- `rembrandt` — Key (45° side, high) + dim Fill. Dramatic portrait.
- `butterfly` — Key (directly front, high). Glamour/beauty lighting.
- `split` — Key (90° side). Half face lit, half in shadow. Moody.
- `loop` — Key (35° side) + Fill + Rim. Natural-looking portrait.

**Returns:**
```json
{
  "success": true,
  "preset": "three-point",
  "subject": "Genesis 9",
  "lights": ["Key Light", "Fill Light", "Rim Light"]
}
```

All presets: aim lights at the subject's face height, set environment mode to Scene Only, and remove existing lights with the same names first.

**Use when:** Setting up a scene for rendering without manually positioning individual lights.

**Example:**
```
# Classic portrait lighting
daz_apply_lighting_preset("three-point", "Genesis 9")

# Dramatic moody lighting
daz_apply_lighting_preset("rembrandt", "Genesis 9")
```

---

#### `daz_validate_scene`
Validate scene quality for rendering — checks lighting, cameras, collisions.

**Returns:**
```json
{
  "score": 75,
  "issues": [
    {"category": "lighting", "severity": "medium", "message": "Only one light source — consider adding fill or rim light"},
    {"category": "collision", "severity": "high", "message": "Alice and Bob bounding boxes overlap by 5cm"}
  ],
  "breakdown": {
    "lighting": 60,
    "cameras": 100,
    "figures": 100,
    "collisions": 50
  }
}
```

**Score:** 0-100. Issues reduce the score. Checks: bounding box collisions between figures, insufficient lighting, no cameras, no figures.

**Use when:** Before rendering to catch common setup problems.

---

### 🎭 Emotional Direction

#### `daz_set_emotion`
Apply an emotional expression to a character (morphs + body language).

**Arguments:**
- `character_label` (string): Character display label
- `emotion` (string): Emotion name
- `intensity` (float, default `0.7`): Strength of the expression (0.0–1.0)

**Supported emotions:** `happy`, `sad`, `angry`, `surprised`, `fearful`, `disgusted`, `neutral`, `excited`, `bored`, `confident`, `shy`, `loving`, `contemptuous`

**Returns:**
```json
{
  "success": true,
  "character": "Genesis 9",
  "emotion": "happy",
  "intensity": 0.7,
  "applied": ["PHMSmile", "PHMBrowsUp", "chest_forward"],
  "notFound": ["PHMEyeSquintL"]
}
```

Missing morphs (due to figure generation differences) are reported in `not_found` without raising an error.

**Use when:** Quickly applying a recognizable expression instead of manually searching for morph names.

**Example:**
```
# Apply full happy expression
daz_set_emotion("Alice", "happy")

# Subtle confident look
daz_set_emotion("Bob", "confident", intensity=0.4)
```

---

### 📚 Content Library Navigation

#### `daz_list_categories`
List subdirectories in the content library under a parent path.

**Arguments:**
- `parent_path` (string, default `""`): Path relative to content library root (e.g., `"People/Genesis 9"`)

**Returns:**
```json
{
  "path": "People/Genesis 9",
  "categories": ["Characters", "Hair", "Clothing", "Expressions"],
  "count": 4
}
```

**Use when:** Browsing the content library to discover available categories.

**Example:**
```
# List top-level categories
daz_list_categories("")

# Browse Genesis 9 subcategories
daz_list_categories("People/Genesis 9")
```

---

#### `daz_browse_category`
List `.duf` files in a content library category.

**Arguments:**
- `category_path` (string): Path relative to content library root
- `sort_by` (string, default `"name"`): Sort order: `"name"` or `"date"`

**Returns:**
```json
{
  "path": "People/Genesis 9/Hair",
  "files": [
    {"name": "Ade Hair", "path": "/Library/People/Genesis 9/Hair/Ade Hair.duf"},
    {"name": "Braid Updo", "path": "/Library/People/Genesis 9/Hair/Braid Updo.duf"}
  ],
  "count": 2
}
```

**Use when:** Finding content file paths to load with `daz_load_file`.

---

#### `daz_get_content_info`
Read metadata from a `.duf` file without loading it.

**Arguments:**
- `file_path` (string): Absolute path to `.duf` file

**Returns:**
```json
{
  "name": "Ade Hair",
  "type": "wearable",
  "requires": ["Genesis 9"],
  "author": "Daz Originals",
  "description": "Long flowing hair for Genesis 9"
}
```

**Use when:** Checking compatibility or requirements before loading content.

---

### 🎬 Scene Composition / Cinematography

#### `daz_apply_composition_rule`
Position camera using a photography composition rule.

**Arguments:**
- `camera_label` (string): Camera to position
- `subject_label` (string): Subject to compose around
- `rule` (string, default `"rule-of-thirds"`): Composition rule

**Rules:**
- `rule-of-thirds` — Subject on right vertical third at eye level
- `golden-ratio` — Subject at 1.618 golden section
- `center-frame` — Subject centered, symmetric
- `leading-lines` — Low angle with diagonal offset

**Returns:**
```json
{
  "success": true,
  "camera": "Camera 1",
  "subject": "Genesis 9",
  "rule": "rule-of-thirds"
}
```

---

#### `daz_frame_shot`
Frame camera using a standard cinematic shot type.

**Arguments:**
- `camera_label` (string): Camera to position
- `subject_label` (string): Subject to frame
- `shot_type` (string): Shot type name

**Shot types and distances:**
- `extreme-close-up` — 25 cm (eyes/mouth detail)
- `close-up` — 50 cm (face)
- `medium-close-up` — 90 cm (head and shoulders)
- `medium-shot` — 140 cm (waist up)
- `medium-full` — 200 cm (knees up)
- `full-shot` — 400 cm (whole body)
- `wide-shot` — 700 cm (body + environment)

**Returns:**
```json
{
  "success": true,
  "camera": "Camera 1",
  "subject": "Genesis 9",
  "shotType": "medium-shot",
  "distance": 140
}
```

**Example:**
```
# Frame a portrait shot
daz_frame_shot("Camera 1", "Genesis 9", "close-up")

# Frame full body
daz_frame_shot("Camera 1", "Genesis 9", "full-shot")
```

---

#### `daz_apply_camera_angle`
Apply a standard camera angle preset relative to a subject.

**Arguments:**
- `camera_label` (string): Camera to position
- `subject_label` (string): Subject to angle toward
- `angle` (string, default `"eye-level"`): Camera angle preset

**Angles:**
- `eye-level` — Neutral, camera at subject's eye height
- `high-angle` — Above subject, looking down (vulnerable)
- `low-angle` — Below eye level, looking up (powerful)
- `dutch-angle` — Eye level + 15° Z-roll (unsettling)
- `overhead` — Directly above (bird's-eye)
- `worms-eye` — Ground level looking up
- `over-shoulder` — Behind and to one side

**Returns:**
```json
{
  "success": true,
  "camera": "Camera 1",
  "subject": "Genesis 9",
  "angle": "low-angle"
}
```

---

### 💾 Scene Checkpoint System

#### `daz_save_scene_state`
Save current scene state (transforms, morphs, light properties) as a named checkpoint.

**Arguments:**
- `checkpoint_name` (string): Name for this checkpoint

**What is captured:**
- All figures/skeletons: transform properties + active (non-zero) morph values
- All cameras: transform properties
- All lights: transform properties + Flux, Shadow Softness, Spread Angle

**What is NOT captured:** Materials, geometry, HDR dome settings, parenting relationships.

**Returns:**
```json
{
  "success": true,
  "checkpoint": "before_lighting_test",
  "nodesCaptured": 5,
  "savedAt": "2026-04-09T10:15:00"
}
```

**Important:** Checkpoints are stored in MCP server process memory and are lost if the server restarts.

**Example:**
```python
# Safe experimentation workflow
daz_save_scene_state("before_lighting_test")
daz_apply_lighting_preset("rembrandt", "Genesis 9")
# Don't like it?
daz_restore_scene_state("before_lighting_test")
```

---

#### `daz_restore_scene_state`
Restore scene state from a named checkpoint.

**Arguments:**
- `checkpoint_name` (string): Name of checkpoint to restore

**Returns:**
```json
{
  "success": true,
  "checkpoint": "before_lighting_test",
  "nodesRestored": 5
}
```

---

#### `daz_list_checkpoints`
List all saved checkpoints in the current session.

**Returns:**
```json
{
  "checkpoints": [
    {"name": "before_lighting_test", "savedAt": "2026-04-09T10:15:00", "nodeCount": 5},
    {"name": "pose_v2", "savedAt": "2026-04-09T10:32:00", "nodeCount": 5}
  ],
  "count": 2
}
```

---

### 🗺️ Scene Layout & Proximity

#### `daz_get_scene_layout`
Full spatial map of all scene nodes with positions and bounding boxes.

**Arguments:**
- `include_types` (list, optional): Filter by type. Values: `"figures"`, `"cameras"`, `"lights"`, `"props"`. Omit for all types.

**Returns:**
```json
{
  "nodes": [
    {
      "label": "Genesis 9", "type": "DzFigure",
      "position": {"x": 0, "y": 0, "z": 0},
      "boundingBox": {"min": {...}, "max": {...}, "center": {...}}
    }
  ],
  "count": 8
}
```

**Use when:** Getting a complete overview of scene spatial layout before adding or moving objects.

---

#### `daz_find_nearby_nodes`
Find all nodes within a radius of a target node.

**Arguments:**
- `target_label` (string): Center node to search around
- `radius` (float, default `200.0`): Search radius in cm
- `include_types` (list, optional): Filter by type: `"figures"`, `"cameras"`, `"lights"`, `"props"`

**Returns:**
```json
{
  "target": "Alice",
  "radius": 200,
  "nearby": [
    {"label": "Bob", "type": "DzFigure", "distance": 120.5, "direction": "front-right"},
    {"label": "Chair", "type": "prop", "distance": 85.0, "direction": "right"}
  ],
  "count": 2
}
```

**Direction labels:** `front`, `front-right`, `right`, `back-right`, `back`, `back-left`, `left`, `front-left`

**Use when:** Finding all characters or props near a subject, checking interaction range.

---

### ⚡ Async Rendering Tools

For long-running operations (full renders, animation export, multi-camera batch), async tools return immediately with a `request_id`. The script executes serially on DAZ Studio's main thread — the scene is locked while it runs, so subsequent scene modifications queue behind it.

**Key constraint:** DAZ Studio is single-threaded. Async means the HTTP connection is released immediately — execution is still serial.

#### `daz_render_async`
Submit a render asynchronously. Returns immediately with a `request_id`.

**Arguments:**
- `output_path` (string, optional): Output file path

**Returns:**
```json
{
  "request_id": "render-a3f2b891",
  "status": "queued",
  "submitted_at": "2026-04-09T10:15:00"
}
```

---

#### `daz_render_with_camera_async`
Submit a camera-specific render asynchronously.

**Arguments:**
- `camera_label` (string): Camera to render from
- `output_path` (string, optional): Output file path

---

#### `daz_batch_render_cameras_async`
Submit a multi-camera batch render asynchronously.

**Arguments:**
- `cameras` (list[string]): Camera labels
- `output_dir` (string): Output directory
- `base_filename` (string, default `"render"`): Base filename

---

#### `daz_render_animation_async`
Submit an animation render asynchronously.

**Arguments:**
- `output_dir` (string): Output directory
- `start_frame` (int, optional): First frame
- `end_frame` (int, optional): Last frame
- `filename_pattern` (string, default `"frame"`): Filename prefix
- `camera` (string, optional): Camera to render from

---

#### `daz_get_request_status`
Poll the status of an async request (non-blocking, lightweight).

**Arguments:**
- `request_id` (string): Request ID from an async submit tool

**Returns:**
```json
{
  "request_id": "render-a3f2b891",
  "status": "running",
  "progress": 0.0,
  "elapsed_ms": 3200,
  "queue_position": 0
}
```

**Status values:** `queued`, `running`, `completed`, `failed`, `cancelled`

---

#### `daz_get_request_result`
Fetch the final result of an async request.

**Arguments:**
- `request_id` (string): Request ID
- `wait` (bool, default `True`): If True, blocks until complete (up to `timeout_seconds`)
- `timeout_seconds` (int, default `300`): Max wait time when `wait=True`

**Returns (completed):**
```json
{
  "success": true,
  "result": {...},
  "request_id": "render-a3f2b891",
  "duration_ms": 45230,
  "completed_at": "2026-04-09T10:15:47",
  "status": "completed"
}
```

---

#### `daz_cancel_request`
Cancel a queued or running async request.

**Arguments:**
- `request_id` (string): Request ID to cancel

Queued requests are removed immediately. Running requests set a cancel flag and call `killRender()`.

**Returns:**
```json
{
  "request_id": "render-a3f2b891",
  "status": "cancelled",
  "cancelled_at": "2026-04-09T10:15:05"
}
```

---

#### `daz_list_requests`
List all active and recently completed async requests.

**Arguments:**
- `status_filter` (string, optional): Filter by status: `"queued"`, `"running"`, `"completed"`, `"failed"`, `"cancelled"`

**Returns:**
```json
{
  "requests": [...],
  "total": 3,
  "queued": 1,
  "running": 1,
  "completed": 1
}
```

---

#### `daz_set_render_quality`
Set render quality preset before rendering.

**Arguments:**
- `preset` (string): One of `"draft"`, `"preview"`, `"good"`, `"final"`

| Preset | Typical time | Use case |
|--------|-------------|----------|
| `draft` | 30s–2min | Quick composition check |
| `preview` | 2–5min | Client review |
| `good` | 10–20min | High quality review |
| `final` | 30min–2hr | Final output |

**Returns:**
```json
{
  "preset": "draft",
  "settings": {"Max Samples": 100, "Render Quality": 0.5}
}
```

---

**Async workflow example:**

```python
# 1. Set quality and submit
daz_set_render_quality("final")
req = daz_render_async("/renders/final.png")

# 2. Poll status
while True:
    status = daz_get_request_status(req["request_id"])
    if status["status"] in ("completed", "failed", "cancelled"):
        break
    # come back later...

# 3. Or use wait=True in one step
result = daz_get_request_result(req["request_id"], wait=True, timeout_seconds=3600)
```

---

### 🎬 Cinematic Director Workflow (Phase 4)

Phase 4 tools provide high-level cinematic automation for creating professional scenes quickly.

#### `daz_create_shot_sequence`
Create multi-camera shot sequences for cinematic storytelling.

Automatically creates and positions multiple cameras with keyframe animations for standard cinematic sequences.

**Arguments:**
- `sequence_type` (string): Type of sequence - "establishing-medium-closeup", "shot-reverse-shot", "orbit", "push-in"
- `characters` (list[string]): List of character labels (1-2 depending on sequence)
- `duration` (int, default 120): Total duration in frames

**Sequence Types:**
- `"establishing-medium-closeup"` - Three cameras at different distances (wide → medium → close-up)
- `"shot-reverse-shot"` - Two over-shoulder cameras for conversation (requires 2 characters)
- `"orbit"` - Single animated camera orbiting 360° around subject
- `"push-in"` - Single animated camera dollying from wide to close-up

**Returns:**
```json
{
  "cameras": [
    {"label": "Wide Shot", "position": {...}, "frameRange": {"start": 0, "end": 59}},
    {"label": "Medium Shot", "position": {...}, "frameRange": {"start": 60, "end": 119}}
  ],
  "totalFrames": 180,
  "sequenceType": "establishing-medium-closeup",
  "subject": "Genesis 9"
}
```

**Example:**
```python
# Establishing sequence
daz_create_shot_sequence("establishing-medium-closeup", ["Genesis 9"], duration=180)

# Conversation cameras
daz_create_shot_sequence("shot-reverse-shot", ["Alice", "Bob"], duration=240)

# 360° turntable
daz_create_shot_sequence("orbit", ["Genesis 9"], duration=300)
```

---

#### `daz_animate_conversation`
Choreograph animated conversation between two characters with look-at and emotion keyframes.

**Arguments:**
- `char1_label` (string): First character label
- `char2_label` (string): Second character label
- `dialogue_beats` (list[dict]): List of dialogue beats, each containing:
  - `speaker` (string): Who's speaking (char1 or char2)
  - `startFrame` (int): Beat start frame
  - `endFrame` (int): Beat end frame
  - `emotion` (string): Emotion name - "happy", "sad", "angry", "surprised", "neutral"
  - `intensity` (float, optional): Emotion intensity 0.0-1.0 (default: 0.7)

**Returns:**
```json
{
  "char1": "Alice",
  "char2": "Bob",
  "beatsApplied": [
    {
      "beat": 1,
      "speaker": "Alice",
      "frameRange": {"start": 0, "end": 60},
      "emotion": "happy",
      "actions": ["Applied happy emotion (3 morphs)", "Listener looks at speaker"]
    }
  ],
  "totalFrames": 180,
  "beatCount": 3
}
```

**Example:**
```python
daz_animate_conversation(
    "Alice",
    "Bob",
    [
        {"speaker": "Alice", "startFrame": 0, "endFrame": 60, "emotion": "happy"},
        {"speaker": "Bob", "startFrame": 60, "endFrame": 120, "emotion": "surprised"},
        {"speaker": "Alice", "startFrame": 120, "endFrame": 180, "emotion": "neutral"}
    ]
)
```

**Features:**
- Listener automatically looks at speaker during dialogue beat
- Emotion morphs applied at beat start
- Head/neck rotation for natural look-at behavior
- Compatible with shot-reverse-shot camera sequences

---

#### `daz_create_scene`
Generate complete scene from natural language description.

Automatically creates lighting, cameras, and character positioning based on text description using template-based keyword matching.

**Arguments:**
- `description` (string): Natural language scene description
- `characters` (list[string], optional): Character labels already in scene

**Supported Scene Types:**
- **"dining" / "dinner" / "meal"** - Dining scene with characters facing across table
- **"interview" / "meeting" / "business"** - Interview setup with professional lighting
- **"portrait" / "headshot" / "photo"** - Portrait photography with three-point lighting
- **"conversation" / "talking" / "chat"** - Conversation scene with shot-reverse-shot cameras
- **Generic** - Default three-point lighting for unrecognized descriptions

**Returns:**
```json
{
  "sceneType": "dining",
  "description": "romantic dinner for two",
  "charactersUsed": 2,
  "actions": [
    "Scene type: Dining/meal scene",
    "Positioned characters facing each other across table distance",
    "Applied warm romantic lighting"
  ],
  "cameras": [
    {"label": "Wide Shot", "type": "wide", "purpose": "Establishing shot of dining scene"},
    {"label": "Over Shoulder 1", "type": "over-shoulder", "purpose": "Conversation angle"}
  ],
  "suggestions": [
    "Add table prop for dining scene",
    "Add plates, glasses, or food props for realism",
    "Consider adding candles for romantic dinner mood"
  ]
}
```

**Example:**
```python
# Romantic dinner
daz_create_scene("romantic dinner for two", ["Alice", "Bob"])

# Job interview
daz_create_scene("job interview", ["Interviewer", "Candidate"])

# Professional portrait
daz_create_scene("professional portrait", ["Genesis 9"])
```

**What Gets Created:**
1. Scene-appropriate lighting (2-3 spot lights)
2. Character positioning based on scene type
3. Multiple cameras at strategic angles
4. Environment mode set to Scene Only
5. Actionable suggestions for enhancement

---

#### `daz_start_recording`
Start recording a macro to capture sequence of operations.

**Arguments:**
- `macro_name` (string): Unique macro name (1-64 chars, letters/digits/hyphens/underscores)
- `description` (string, optional): Macro description

**Returns:**
```json
{
  "success": true,
  "macro_name": "portrait_setup",
  "description": "Standard portrait lighting and framing",
  "started_at": "2026-04-10T15:30:00",
  "message": "Recording macro 'portrait_setup'. Call daz_stop_recording() when done."
}
```

**Example:**
```python
# Start recording
daz_start_recording("portrait_setup", "Standard portrait workflow")

# Perform operations (these will be recorded)
daz_apply_lighting_preset("three-point", "Genesis 9")
daz_frame_shot("Camera 1", "Genesis 9", "medium-close-up")

# Stop and save
daz_stop_recording()
```

---

#### `daz_stop_recording`
Stop recording current macro and save to library.

**Returns:**
```json
{
  "success": true,
  "macro_name": "portrait_setup",
  "operation_count": 2,
  "saved_at": "2026-04-10T15:31:00",
  "message": "Macro 'portrait_setup' saved with 2 operations."
}
```

---

#### `daz_replay_macro`
Replay a saved macro with optional parameter substitution.

**Arguments:**
- `macro_name` (string): Name of macro to replay
- `parameters` (dict, optional): Parameter values for substitution

**Returns:**
```json
{
  "success": true,
  "macro_name": "portrait_setup",
  "results": [],
  "successful_count": 2,
  "failed_count": 0
}
```

**Example:**
```python
# Replay for different character
daz_replay_macro("portrait_setup", parameters={"subject": "Alice"})
```

**Note:** Parameter substitution not yet implemented in Phase 1 - placeholder for future.

---

#### `daz_list_macros`
List all saved macros in the library.

**Returns:**
```json
{
  "macros": [
    {
      "name": "portrait_setup",
      "description": "Standard portrait workflow",
      "operation_count": 2,
      "saved_at": "2026-04-10T15:31:00"
    }
  ],
  "count": 1
}
```

**Note:** Macros are session-only (lost when MCP server restarts).

---

### ✏️ Modification Tools

#### `daz_set_property`
Set a numeric property on a scene node.

**Arguments:**
- `node_label` (string): Node display label or internal name
- `property_name` (string): Property display label or internal name
- `value` (float): New value

**Returns:**
```json
{
  "node": "Genesis 9",
  "property": "X Translate",
  "value": 50.0
}
```

**Units:**
- Translation: centimeters
- Rotation: degrees
- Morphs: typically 0-1 or percentage

**Use when:** Moving nodes, adjusting morphs, or changing any numeric property.

**Example:**
```
daz_set_property(node_label="Genesis 9", property_name="X Translate", value=100.0)
```

---

#### `daz_load_file`
Load a DAZ Studio file into the scene.

**Arguments:**
- `file_path` (string): Absolute path to file (`.duf`, `.daz`, `.obj`, `.fbx`, etc.)
- `merge` (bool, default `True`): If true, merge into scene; if false, replace scene

**Returns:**
```json
{
  "success": true,
  "file": "/path/to/character.duf"
}
```

**Use when:** Loading characters, props, scenes, or any content files.

**Example:**
```
daz_load_file(file_path="/Library/Genesis 9/Character.duf", merge=True)
```

---

### 🎬 Rendering Tools

#### `daz_render`
Trigger a render using current DAZ Studio render settings.

**Arguments:**
- `output_path` (string, optional): Absolute path for output image (e.g., `"C:/renders/output.png"`)

**Returns:**
```json
{
  "success": true
}
```

**Notes:**
- Uses DAZ Studio's currently configured render settings (dimensions, quality, engine)
- Blocks until render completes (increase `DAZ_TIMEOUT` for long renders)
- If `output_path` is omitted, uses DAZ Studio's configured output path

**Use when:** Rendering the current scene setup.

---

### 🎭 Multi-Character Interaction Tools

#### `daz_look_at_point`
Make character look at a world-space point with cascading body involvement.

**Arguments:**
- `character_label` (string): Character display label or internal name
- `target_x` (float): World X coordinate (cm) to look at
- `target_y` (float): World Y coordinate (cm) to look at
- `target_z` (float): World Z coordinate (cm) to look at
- `mode` (string, default `"head"`): How much body to involve
  - `"eyes"` - Only rotate eyes
  - `"head"` - Eyes + head rotation
  - `"neck"` - Eyes + head + neck
  - `"torso"` - Eyes + head + neck + chest
  - `"full"` - Complete body rotation including hip

**Returns:**
```json
{
  "success": true,
  "character": "Genesis 9",
  "mode": "head",
  "rotatedBones": ["lEye", "rEye", "head"]
}
```

**Use when:** Making a character look at a specific point in 3D space with natural body movement.

**Example:**
```
# Look at point in front at eye level
daz_look_at_point("Genesis 9", 0, 160, 200, mode="head")

# Full body turn to look behind
daz_look_at_point("Genesis 9", 0, 140, -150, mode="full")
```

---

#### `daz_look_at_character`
Make one character look at another character's face.

**Arguments:**
- `source_label` (string): Character who will look
- `target_label` (string): Character to look at
- `mode` (string, default `"head"`): Body involvement level (same options as `daz_look_at_point`)

**Returns:**
```json
{
  "success": true,
  "source": "Alice",
  "target": "Bob",
  "mode": "head",
  "targetPosition": {"x": 50, "y": 163, "z": 0},
  "rotatedBones": ["lEye", "rEye", "head"]
}
```

**Use when:** Creating eye contact or attention between characters.

**Example:**
```
# Alice looks at Bob
daz_look_at_character("Alice", "Bob", mode="head")

# Bob turns whole body to face Alice
daz_look_at_character("Bob", "Alice", mode="full")
```

---

#### `daz_reach_toward`
Position character's arm to reach toward a world-space point using pseudo-IK.

**Arguments:**
- `character_label` (string): Character display label or internal name
- `side` (string): Which arm: `"left"` or `"right"`
- `target_x` (float): World X coordinate (cm) to reach toward
- `target_y` (float): World Y coordinate (cm) to reach toward
- `target_z` (float): World Z coordinate (cm) to reach toward

**Returns:**
```json
{
  "success": true,
  "character": "Genesis 9",
  "side": "right",
  "targetDistance": 45.3,
  "bones": ["right shoulder", "right forearm", "right hand"]
}
```

**Use when:** Positioning hands to grasp objects, point at things, or reach toward targets.

**Example:**
```
# Reach right hand toward object at chest height
daz_reach_toward("Genesis 9", "right", 50, 130, 80)

# Reach left hand toward object on left side
daz_reach_toward("Genesis 9", "left", -60, 100, 50)
```

**Note:** Uses simplified IK approximation. For precise hand positioning, load artist-created pose presets.

---

#### `daz_interactive_pose`
Coordinate two characters for interactive poses.

**Arguments:**
- `char1_label` (string): First character display label
- `char2_label` (string): Second character display label
- `interaction_type` (string, default `"face-each-other"`): Type of interaction
  - `"face-each-other"` - Position and rotate to face each other
  - `"hug"` - Both characters hug with arms around each other
  - `"shoulder-arm"` - Char1 puts arm around char2's shoulders
  - `"handshake"` - Both extend right hands for handshake
- `distance` (float, optional): Spacing between characters in cm

**Returns:**
```json
{
  "success": true,
  "char1": "Alice",
  "char2": "Bob",
  "interactionType": "hug",
  "applied": ["facing", "hug arms"]
}
```

**Use when:** Creating common two-character interactions quickly.

**Example:**
```
# Position characters facing each other at conversation distance
daz_interactive_pose("Alice", "Bob", "face-each-other", distance=120)

# Create tight hug
daz_interactive_pose("Alice", "Bob", "hug", distance=30)

# Bob puts arm around Alice's shoulders
daz_interactive_pose("Bob", "Alice", "shoulder-arm")
```

**Note:** These are simplified interaction poses. Fine-tune positions afterward using `daz_set_property`.

---

### 🔧 Low-Level Tools

#### `daz_execute`
Execute arbitrary inline DazScript code.

**Arguments:**
- `script` (string): DazScript (JavaScript) source code
- `args` (dict, optional): JSON object accessible in script as `args` variable

**Returns:**
```json
{
  "success": true,
  "result": 42,
  "output": ["line from print()"],
  "error": null,
  "request_id": "a3f2b891"
}
```

**Script Requirements:**
- Wrap returning scripts in IIFE: `(function(){ return 42; })()`
- Global objects available: `Scene`, `App`, `MainWindow`
- Access args via: `var value = args.myKey;`

**Use when:** You need fine-grained control or operations not covered by high-level tools.

**Example:**
```javascript
script = "(function(){ return Scene.getNumNodes(); })()"
```

---

#### `daz_execute_file`
Execute a DazScript file from disk.

**Arguments:**
- `script_file` (string): Absolute path to `.dsa` or `.ds` file
- `args` (dict, optional): JSON object accessible as `args` in the script

**Returns:** Same format as `daz_execute`

**Use when:** Running complex scripts stored in files, especially scripts that use `include()` or `getScriptFileName()`.

---

## Features

### 🚀 Script Registry
High-level tools (`daz_scene_info`, `daz_get_node`, etc.) use the DazScriptServer script registry:
- Scripts are registered once at startup
- Subsequent calls execute by ID (no retransmission)
- Auto-reregistration on 404 (when DAZ Studio restarts)

### 🔄 Automatic Reconnection
If DAZ Studio restarts and clears the session registry, the server automatically detects 404 responses, re-registers all scripts, and retries the operation.

### 🛡️ Error Handling
- Connection failures → Clear error messages ("Ensure DAZ Studio is running...")
- Timeouts → Actionable guidance (increase `DAZ_TIMEOUT`)
- Authentication failures → Token file location in error message
- Script errors → Full error details with line numbers and captured output

### 🎬 Cinematic Director Workflow (Phase 4 - NEW in v0.3.0)
High-level automation tools for professional cinematic workflows:
- **Scene Generation**: Create complete scenes from natural language (5 templates: dining, interview, portrait, conversation, generic)
- **Shot Sequences**: Multi-camera cinematography (establishing shots, shot-reverse-shot, orbit, push-in)
- **Conversation Choreography**: Automated dialogue animation with look-at behavior and emotion timing
- **Macro System**: Record and replay operation sequences for workflow automation (session-based)

Phase 4 tools combine lower-level operations into powerful high-level workflows, dramatically reducing the time to create professional cinematic scenes.

---

## Usage Examples

### Example 1: Check Status
```python
# In Claude Desktop, just ask:
"Check if DAZ Studio is running"

# Claude will use daz_status and report back
```

### Example 2: Load and Position Character
```
1. Load Genesis 9 from /Library/Genesis 9/Genesis9.duf
2. Move it 100cm to the right
3. Get the current scene info
```

Claude will:
1. Call `daz_load_file(file_path="/Library/Genesis 9/Genesis9.duf", merge=True)`
2. Call `daz_set_property(node_label="Genesis 9", property_name="X Translate", value=100.0)`
3. Call `daz_scene_info()` and report the results

### Example 3: Custom Lighting Setup
```
Execute this DazScript to create a three-point light setup:
- Key light at (200, 200, 200) pointing at origin
- Fill light at (-100, 150, 150) pointing at origin
- Rim light at (0, 180, -200) pointing at origin
```

Claude will use `daz_execute` with the appropriate DazScript code.

### Example 4: Batch Rendering
```
Render the current scene to these output paths:
- C:/renders/front.png
- C:/renders/side.png
- C:/renders/back.png

Between each render, rotate the character 90 degrees.
```

Claude will loop through, adjusting rotation and calling `daz_render` for each output.

### Example 5: Generate Complete Scene (Phase 4)
```
Create a romantic dinner scene with Alice and Bob
```

Claude will:
1. Call `daz_create_scene("romantic dinner for two", ["Alice", "Bob"])`
   - Positions characters facing each other
   - Creates warm romantic lighting (2 spot lights)
   - Creates wide shot and over-shoulder cameras
   - Returns suggestions: add table, plates, candles
2. Report the created cameras and lighting setup
3. Suggest next steps based on the suggestions

### Example 6: Animated Conversation (Phase 4)
```
Create an animated conversation between Alice and Bob:
- Alice speaks happily from frame 0-60
- Bob responds with surprise from 60-120
- Alice concludes neutrally from 120-180
```

Claude will:
1. Call `daz_animate_conversation("Alice", "Bob", [...dialogue beats...])`
   - Sets up look-at behavior (listener looks at speaker)
   - Applies emotion morphs at beat boundaries
   - Animates head/neck rotation for natural movement
2. Call `daz_create_shot_sequence("shot-reverse-shot", ["Alice", "Bob"], 180)`
   - Creates over-shoulder cameras for conversation
3. Report the animation setup and suggest render workflow

---

## Troubleshooting

### "Cannot connect to DAZ Studio"

**Cause:** DazScriptServer plugin is not running or not listening on the expected port.

**Solutions:**
1. Open DAZ Studio
2. Go to **Window → Panes → Daz Script Server**
3. Click **Start Server**
4. Verify it's running on port 18811 (or update `DAZ_PORT` env var)

---

### "Authentication failed (HTTP 401)"

**Cause:** API token is missing or incorrect.

**Solutions:**
1. Check DazScriptServer UI shows authentication is enabled
2. Verify token file exists: `~/.daz3d/dazscriptserver_token.txt`
3. Copy token exactly from DazScriptServer UI
4. Set `DAZ_API_TOKEN` environment variable if using custom location

---

### "Request timed out after 30s"

**Cause:** Script or render took longer than the timeout.

**Solutions:**
1. Increase timeout: `export DAZ_TIMEOUT=120.0`
2. Update Claude Desktop config with larger timeout in `env` section
3. Restart Claude Desktop after config change

---

### "Script execution failed" or "Node not found"

**Cause:** DazScript error (syntax, missing node, wrong property name).

**Solutions:**
1. Check the error message for line numbers and details
2. Verify node labels match exactly (case-sensitive)
3. Use `daz_get_node` to discover available property names
4. Test scripts manually in DAZ Studio Script IDE first

---

## Development

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test
uv run pytest tests/test_server.py::test_daz_status_ok -v
```

### Project Structure

```
vangard-daz-mcp/
├── src/vangard_daz_mcp/
│   ├── server.py              # Single-file MCP server (all tools)
│   └── dazscript_docs.json    # DazScript documentation loaded by daz_script_help
├── tests/
│   └── test_server.py         # Test suite with respx mocks
├── pyproject.toml             # Project config (version, dependencies)
├── ASYNC_OPERATIONS.md        # Design doc for async rendering system
├── IMPLEMENTATION_PLAN.md     # Phased feature roadmap
└── README.md
```

### Architecture

- **FastMCP 3.x server** with stdio transport
- **httpx.AsyncClient** for HTTP requests to DazScriptServer
- **Script registry** for high-level tools (auto-registration on startup)
- **Module-level `_http_client`** shared across all tool calls
- **lifespan context** manages client initialization and cleanup

---

## Requirements

- **Python:** 3.11+
- **Dependencies:**
  - `fastmcp>=2.0` - MCP server framework
  - `httpx>=0.27` - Async HTTP client
- **Dev Dependencies:**
  - `pytest>=8.0`
  - `pytest-asyncio>=0.24`
  - `respx>=0.21` - HTTP mocking for tests

---

## Limitations

- DAZ Studio must be running locally (no remote DAZ Studio support)
- DazScriptServer plugin must be installed and active
- All scene operations execute on DAZ Studio's main thread — operations are serialized even with async tools
- While a render is running, no other scene operations can execute (scene is locked)
- Scene checkpoints are in-memory only and lost if the MCP server restarts
- No support for binary data (rendered images must be saved to disk, not returned directly)

---

## Related Projects

- **DazScriptServer**: https://github.com/bluemoonfoundry/daz-script-server
  - The HTTP plugin this server wraps
  - Required prerequisite
- **Model Context Protocol**: https://modelcontextprotocol.io
  - Specification this server implements
- **FastMCP**: https://github.com/jlowin/fastmcp
  - Framework used to build this server

---

## Contributing

Contributions welcome! Areas for improvement:

- Material property tools (read/set surface colors, textures, shader settings)
- Support for binary data (screenshot capture, returning rendered images directly)
- Integration tests with a real DAZ Studio instance
- More DazScript documentation topics in `dazscript_docs.json`
- Additional lighting presets and emotion definitions

---

## License

This project is provided as-is for use with DAZ Studio.

**Author:** Blue Moon Foundry

For questions or issues, please open an issue on GitHub.
