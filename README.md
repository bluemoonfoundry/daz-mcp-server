# vangard-daz-mcp

**Version 0.1.0** | MCP Server for DAZ Studio

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that exposes DAZ Studio operations to Claude and other MCP clients. Built on [FastMCP](https://github.com/jlowin/fastmcp) and wraps the [DazScriptServer](https://github.com/bluemoonfoundry/daz-script-server) HTTP plugin.

---

## What Is This?

This MCP server allows Claude (via Claude Desktop or other MCP clients) to control DAZ Studio directly:
- Query scene information (figures, cameras, lights)
- Read and modify node properties (transforms, morphs)
- Load content files
- Trigger renders
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
  "version": "1.2.0"
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
│   └── server.py          # Single-file MCP server (all tools)
├── tests/
│   └── test_server.py     # Test suite with respx mocks
├── pyproject.toml         # Project config
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
- Single concurrent client (MCP server is single-threaded)
- Scripts execute on DAZ Studio's main thread (operations are serialized)
- No support for binary data (images must be saved to disk, not returned directly)

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

- Additional high-level tools (materials, animation, viewport)
- Better error messages and recovery strategies
- Support for binary data (screenshot capture, texture upload)
- Documentation and examples
- Integration tests with real DAZ Studio instance

---

## License

This project is provided as-is for use with DAZ Studio.

**Author:** Blue Moon Foundry

For questions or issues, please open an issue on GitHub.
