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

This is a [FastMCP](https://github.com/jlowin/fastmcp) 3.x server that bridges Claude (or any MCP client) to DAZ Studio via the **DazScriptServer** HTTP plugin. DAZ Studio must be running locally with DazScriptServer active on port 18811.

### Request flow

```
MCP client → FastMCP tool → httpx.AsyncClient → DazScriptServer (HTTP) → DAZ Studio
```

### Key design points

- **Single file server**: all tools live in `src/vangard_daz_mcp/server.py`. The `mcp` FastMCP instance is the module-level singleton.
- **Shared HTTP client**: a single `httpx.AsyncClient` is created at startup via the `lifespan` async context manager and stored in the module-level `_http_client` global. FastMCP 3.x removed `server.state`; the global variable is the correct pattern.
- **`_execute()` helper**: all high-level tools go through this single coroutine which handles POST, HTTP errors, and script-level `success: false` → `ToolError` conversion.
- **DazScript constants**: embedded scripts are module-level string constants (`_SCENE_INFO_SCRIPT` etc.) so they can be read and edited without hunting through function bodies.
- **Configuration**: `DAZ_HOST`, `DAZ_PORT`, `DAZ_TIMEOUT` environment variables are read at module import time. Changing them requires a server restart.

### DazScriptServer API surface

| Endpoint | Used by |
|----------|---------|
| `GET /status` | `daz_status` |
| `POST /execute` with `script` | `daz_execute`, all high-level tools |
| `POST /execute` with `scriptFile` | `daz_execute_file` |

Both execute endpoints accept an optional `args` JSON object accessible inside the script as the variable `args`.

### Testing

- Tests call the tool functions **directly** (e.g. `await daz_status()`) — `@mcp.tool()` returns the original function unchanged.
- `respx` mocks HTTP at the transport level; each test gets a fresh `httpx.AsyncClient` via the `http_client` autouse fixture which also sets `server_module._http_client`.
- `asyncio_mode = "auto"` (set in `pyproject.toml`) — no `@pytest.mark.asyncio` needed on individual tests.
- Async fixtures require `@pytest_asyncio.fixture`, not plain `@pytest.fixture`.
