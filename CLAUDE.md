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

This server exposes 23 tools to MCP clients:

### Documentation Tools

| Tool | Description |
|------|-------------|
| `daz_script_help` | Get DazScript documentation, examples, and best practices by topic |

**Topics available:** `overview`, `gotchas`, `camera`, `light`, `environment`, `scene`, `properties`, `content`, `coordinates`, `posing`, `morphs`, `hierarchy`, `interaction`, `batch`

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
1. At startup, `_register_scripts()` registers 19 named scripts:
   - **Basic operations:** `vangard-scene-info`, `vangard-get-node`, `vangard-set-property`, `vangard-render`, `vangard-load-file`
   - **Morph discovery:** `vangard-list-morphs`, `vangard-search-morphs`
   - **Scene hierarchy:** `vangard-get-node-hierarchy`, `vangard-list-children`, `vangard-get-parent`, `vangard-set-parent`
   - **Multi-character interaction:** `vangard-look-at-point`, `vangard-look-at-character`, `vangard-reach-toward`, `vangard-interactive-pose`
   - **Batch operations:** `vangard-batch-set-properties`, `vangard-batch-transform`, `vangard-batch-visibility`, `vangard-batch-select`
2. High-level tools call `POST /scripts/:id/execute` with just args (no script body)
3. On 404 (DAZ Studio restarted), `_execute_by_id()` calls `_register_scripts()` and retries

**Arguments:** Both `/execute` and `/scripts/:id/execute` accept an optional `args` JSON object accessible inside the script as the variable `args`.

### Testing

- Tests call the tool functions **directly** (e.g. `await daz_status()`) — `@mcp.tool()` returns the original function unchanged.
- `respx` mocks HTTP at the transport level; each test gets a fresh `httpx.AsyncClient` via the `http_client` autouse fixture which also sets `server_module._http_client`.
- `asyncio_mode = "auto"` (set in `pyproject.toml`) — no `@pytest.mark.asyncio` needed on individual tests.
- Async fixtures require `@pytest_asyncio.fixture`, not plain `@pytest.fixture`.
