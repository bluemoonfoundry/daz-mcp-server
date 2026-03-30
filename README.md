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
