"""MCP server wrapping the DazScriptServer HTTP API for DAZ Studio."""

import os
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

# Configuration from environment variables
DAZ_HOST = os.environ.get("DAZ_HOST", "localhost")
DAZ_PORT = int(os.environ.get("DAZ_PORT", "18811"))
DAZ_TIMEOUT = float(os.environ.get("DAZ_TIMEOUT", "30.0"))

BASE_URL = f"http://{DAZ_HOST}:{DAZ_PORT}"

_TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".daz3d", "dazscriptserver_token.txt")


def _load_token_from_file() -> str:
    """Read the API token written by DazScriptServer, if the file exists."""
    try:
        with open(_TOKEN_FILE) as f:
            return f.read().strip()
    except OSError:
        return ""


# Prefer an explicit env var; fall back to the token file DazScriptServer writes.
DAZ_API_TOKEN: str = os.environ.get("DAZ_API_TOKEN") or _load_token_from_file()

# Shared HTTP client; initialised by the lifespan, torn down on exit.
_http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Create and tear down the shared httpx.AsyncClient."""
    global _http_client
    headers = {"X-API-Token": DAZ_API_TOKEN} if DAZ_API_TOKEN else {}
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=DAZ_TIMEOUT, headers=headers) as client:
        _http_client = client
        await _register_scripts(client)
        yield
    _http_client = None


mcp = FastMCP("vangard-daz-mcp", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_client() -> httpx.AsyncClient:
    if _http_client is None:
        raise RuntimeError("HTTP client not initialised — server lifespan not running")
    return _http_client


def _handle_network_error(exc: Exception) -> None:
    """Re-raise network errors as ToolError with helpful messages."""
    if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout)):
        raise ToolError(
            "Cannot connect to DAZ Studio. Ensure DAZ Studio is running with "
            "the DazScriptServer plugin active."
        ) from exc
    if isinstance(exc, httpx.TimeoutException):
        raise ToolError(
            f"Request timed out after {DAZ_TIMEOUT}s. "
            "Increase the timeout by setting the DAZ_TIMEOUT environment variable."
        ) from exc
    raise exc


def _check_response(response: httpx.Response) -> None:
    """Raise ToolError for known HTTP error statuses, otherwise raise_for_status."""
    if response.status_code == 401:
        source = "DAZ_API_TOKEN environment variable" if os.environ.get("DAZ_API_TOKEN") else _TOKEN_FILE
        raise ToolError(
            f"Authentication failed (HTTP 401). Verify the API token in: {source}"
        )
    response.raise_for_status()


async def _execute(
    script: str,
    args: dict[str, Any] | None = None,
) -> Any:
    """POST a script to DazScriptServer, raise ToolError on failure, return result."""
    client = _get_client()
    payload: dict[str, Any] = {"script": script}
    if args is not None:
        payload["args"] = args

    try:
        response = await client.post("/execute", json=payload)
        _check_response(response)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        _handle_network_error(exc)

    data = response.json()
    if not data.get("success", False):
        output_lines = data.get("output", [])
        error_msg = data.get("error") or "Script execution failed"
        detail = error_msg
        if output_lines:
            detail += "\n\nCaptured output:\n" + "\n".join(output_lines)
        raise ToolError(detail)

    return data.get("result")


async def _register_scripts(client: httpx.AsyncClient) -> None:
    """Register all built-in scripts with DazScriptServer.

    Called at startup and automatically on 404 (DAZ Studio restarted and cleared
    the session registry). Silently skips remaining entries on connection failure.
    """
    for script_id, (description, script_text) in _REGISTRY.items():
        try:
            await client.post("/scripts/register", json={
                "name": script_id,
                "description": description,
                "script": script_text,
            })
        except httpx.RequestError:
            break  # DAZ Studio not running; remaining registrations skipped


async def _execute_by_id(script_id: str, args: dict[str, Any] | None = None) -> Any:
    """Call a registered script by ID, re-registering once on 404."""
    client = _get_client()
    payload: dict[str, Any] = {}
    if args is not None:
        payload["args"] = args

    try:
        response = await client.post(f"/scripts/{script_id}/execute", json=payload)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        _handle_network_error(exc)

    # 404 means DAZ Studio restarted and cleared the session registry — re-register and retry.
    if response.status_code == 404:
        await _register_scripts(client)
        try:
            response = await client.post(f"/scripts/{script_id}/execute", json=payload)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
            _handle_network_error(exc)

    _check_response(response)

    data = response.json()
    if not data.get("success", False):
        output_lines = data.get("output", [])
        error_msg = data.get("error") or "Script execution failed"
        detail = error_msg
        if output_lines:
            detail += "\n\nCaptured output:\n" + "\n".join(output_lines)
        raise ToolError(detail)

    return data.get("result")


# ---------------------------------------------------------------------------
# Embedded DazScript fragments
#
# All scripts must be wrapped in (function(){ ... })() — DazScript does not
# allow bare top-level return statements.
#
# Global objects available in the DAZ Studio scripting environment:
#   Scene   – the current DzScene
#   App     – the DzApp (application) object
#   MainWindow – the main window
# ---------------------------------------------------------------------------

# Returns: {sceneFile, selectedNode, figures:[{name,label,type}], cameras:[...], lights:[...], totalNodes}
# Uses skeleton list (characters + clothing) rather than all nodes (potentially thousands).
_SCENE_INFO_SCRIPT = """\
(function(){
    var figures = [];
    for (var i = 0; i < Scene.getNumSkeletons(); i++) {
        var s = Scene.getSkeleton(i);
        figures.push({ name: s.getName(), label: s.getLabel(), type: s.className() });
    }
    var cameras = [];
    for (var i = 0; i < Scene.getNumCameras(); i++) {
        var c = Scene.getCamera(i);
        cameras.push({ name: c.getName(), label: c.getLabel() });
    }
    var lights = [];
    for (var i = 0; i < Scene.getNumLights(); i++) {
        var l = Scene.getLight(i);
        lights.push({ name: l.getName(), label: l.getLabel(), type: l.className() });
    }
    var sel = Scene.getPrimarySelection();
    return {
        sceneFile: Scene.getFilename(),
        selectedNode: sel ? sel.getLabel() : null,
        figures: figures,
        cameras: cameras,
        lights: lights,
        totalNodes: Scene.getNumNodes()
    };
})()
"""

# args: {nodeLabel}
# Returns: {name, label, type, properties:{label:value}}
# Searches by label first, then internal name.
_GET_NODE_SCRIPT = """\
(function(){
    var n = Scene.findNodeByLabel(args.nodeLabel);
    if (!n) n = Scene.findNode(args.nodeLabel);
    if (!n) throw new Error("Node not found: " + args.nodeLabel);
    var props = {};
    for (var p = 0; p < n.getNumProperties(); p++) {
        var pr = n.getProperty(p);
        if (pr.inherits("DzNumericProperty")) props[pr.getLabel()] = pr.getValue();
    }
    return { name: n.getName(), label: n.getLabel(), type: n.className(), properties: props };
})()
"""

# args: {nodeLabel, propertyName, value}
# Returns: {node, property, value}
# Matches propertyName against both display label and internal name.
_SET_PROPERTY_SCRIPT = """\
(function(){
    var n = Scene.findNodeByLabel(args.nodeLabel);
    if (!n) n = Scene.findNode(args.nodeLabel);
    if (!n) throw new Error("Node not found: " + args.nodeLabel);
    var prop = null;
    for (var p = 0; p < n.getNumProperties(); p++) {
        var pr = n.getProperty(p);
        if (pr.getLabel() === args.propertyName || pr.getName() === args.propertyName) {
            prop = pr; break;
        }
    }
    if (!prop) throw new Error("Property not found: " + args.propertyName + " on " + args.nodeLabel);
    if (!prop.inherits("DzNumericProperty")) throw new Error("Property is not numeric: " + args.propertyName);
    prop.setValue(args.value);
    return { node: n.getLabel(), property: prop.getLabel(), value: prop.getValue() };
})()
"""

# args: {outputPath?}
# Returns: {success}
# Render options are set directly on the DzRenderOptions object (Qt property syntax).
_RENDER_SCRIPT = """\
(function(){
    var renderMgr = App.getRenderMgr();
    var opts = renderMgr.getRenderOptions();
    if (args.outputPath) {
        opts.renderImgToId = 0;
        opts.renderImgFilename = args.outputPath;
    }
    renderMgr.doRender();
    return { success: true };
})()
"""

# args: {filePath, merge}
# Returns: {success, file}
# openFile(path, true)  → merge into current scene
# openFile(path, false) → replace current scene
_LOAD_FILE_SCRIPT = """\
(function(){
    App.getContentMgr().openFile(args.filePath, args.merge);
    return { success: true, file: args.filePath };
})()
"""

# Registry entries: script_id → (description, script_text)
# Registered with DazScriptServer on startup so high-level tools call by ID.
_REGISTRY: dict[str, tuple[str, str]] = {
    "vangard-scene-info": (
        "Return a snapshot of the current DAZ Studio scene",
        _SCENE_INFO_SCRIPT,
    ),
    "vangard-get-node": (
        "Return all numeric properties of a scene node by label",
        _GET_NODE_SCRIPT,
    ),
    "vangard-set-property": (
        "Set a numeric property on a scene node",
        _SET_PROPERTY_SCRIPT,
    ),
    "vangard-render": (
        "Trigger a render using current DAZ Studio render settings",
        _RENDER_SCRIPT,
    ),
    "vangard-load-file": (
        "Load a file into the current DAZ Studio scene",
        _LOAD_FILE_SCRIPT,
    ),
}


# ---------------------------------------------------------------------------
# Tools — low-level (raw script execution)
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_status() -> dict[str, Any]:
    """Check DAZ Studio connectivity. Returns server status and version."""
    client = _get_client()
    try:
        response = await client.get("/status")
        _check_response(response)
        return response.json()
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        _handle_network_error(exc)


@mcp.tool()
async def daz_execute(
    script: str,
    args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute inline DazScript code in DAZ Studio.

    Scripts run in the DAZ Studio JavaScript environment. The global objects
    Scene, App, and MainWindow are available. Scripts must not use a bare
    top-level return statement; wrap returning scripts in an IIFE:
      (function(){ return 42; })()

    Args:
        script: DazScript (JavaScript) source code to execute.
        args: Optional JSON-serialisable object accessible inside the script
              as the variable `args`.

    Returns:
        Object with keys: success, result, output (list of print() lines), error.
    """
    client = _get_client()
    payload: dict[str, Any] = {"script": script}
    if args is not None:
        payload["args"] = args

    try:
        response = await client.post("/execute", json=payload)
        _check_response(response)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        _handle_network_error(exc)

    result = response.json()
    if not result.get("success", False):
        output_lines = result.get("output", [])
        error_msg = result.get("error") or "Script execution failed"
        detail = error_msg
        if output_lines:
            detail += "\n\nCaptured output:\n" + "\n".join(output_lines)
        raise ToolError(detail)

    return result


@mcp.tool()
async def daz_execute_file(
    script_file: str,
    args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a DazScript file on disk inside DAZ Studio.

    Args:
        script_file: Absolute path to the .dsa/.ds script file on the DAZ Studio machine.
        args: Optional JSON-serialisable object accessible inside the script as `args`.

    Returns:
        Object with keys: success, result, output (list of print() lines), error.
    """
    client = _get_client()
    payload: dict[str, Any] = {"scriptFile": script_file}
    if args is not None:
        payload["args"] = args

    try:
        response = await client.post("/execute", json=payload)
        _check_response(response)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        _handle_network_error(exc)

    result = response.json()
    if not result.get("success", False):
        output_lines = result.get("output", [])
        error_msg = result.get("error") or "Script execution failed"
        detail = error_msg
        if output_lines:
            detail += "\n\nCaptured output:\n" + "\n".join(output_lines)
        raise ToolError(detail)

    return result


# ---------------------------------------------------------------------------
# Tools — high-level (structured scene operations)
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_scene_info() -> dict[str, Any]:
    """Return a snapshot of the current DAZ Studio scene.

    Returns figures (characters + clothing), cameras, lights, and the
    primary selection. Does not enumerate every scene node — use
    daz_execute for finer-grained queries.

    Returns a dict with:
      - sceneFile: path to the open .duf file, or empty string if unsaved
      - selectedNode: label of the primary selection, or null
      - figures: list of {name, label, type} for all DzSkeleton objects
      - cameras: list of {name, label} for all cameras
      - lights: list of {name, label, type} for all lights
      - totalNodes: total node count in the scene
    """
    return await _execute_by_id("vangard-scene-info")


@mcp.tool()
async def daz_get_node(node_label: str) -> dict[str, Any]:
    """Return all numeric properties of a scene node by its label or internal name.

    Useful for reading transforms (X Translate, Y Translate, Z Translate,
    X Rotate, Y Rotate, Z Rotate, Scale), morph dials, and any other
    numeric property on the node.

    Args:
        node_label: The display label or internal name of the node (e.g. "Genesis 9").
                    Label is matched first; internal name is the fallback.

    Returns a dict with:
      - name: internal node name
      - label: display label
      - type: DazScript class name (e.g. DzFigure, DzBone, DzCamera)
      - properties: mapping of property label → current numeric value
    """
    return await _execute_by_id("vangard-get-node", {"nodeLabel": node_label})


@mcp.tool()
async def daz_set_property(
    node_label: str,
    property_name: str,
    value: float,
) -> dict[str, Any]:
    """Set a numeric property on a scene node.

    Works for transforms (e.g. "X Translate", "Y Rotate"), morphs
    (e.g. "Head Size"), and any other numeric dial. Use daz_get_node first
    to discover available property names.

    DAZ Studio units: centimetres for translation, degrees for rotation,
    0–1 (or percentage) for most morphs.

    Args:
        node_label: Display label or internal name of the target node.
        property_name: Display label or internal name of the property to set.
        value: New numeric value.

    Returns:
      - node: node label as confirmed by DAZ Studio
      - property: property label as confirmed by DAZ Studio
      - value: the value read back after setting
    """
    return await _execute_by_id(
        "vangard-set-property",
        {"nodeLabel": node_label, "propertyName": property_name, "value": value},
    )


@mcp.tool()
async def daz_render(
    output_path: str | None = None,
) -> dict[str, Any]:
    """Trigger a render in DAZ Studio using the current render settings.

    Render dimensions, format, and other options are whatever is currently
    configured in DAZ Studio's Render Settings panel.

    Args:
        output_path: Optional absolute path for the output image
                     (e.g. "C:/renders/scene.png"). If omitted, DAZ Studio
                     uses its currently configured output path.

    Returns:
      - success: true when the render was launched without error
    """
    args: dict[str, Any] = {}
    if output_path is not None:
        args["outputPath"] = output_path
    return await _execute_by_id("vangard-render", args or None)


@mcp.tool()
async def daz_load_file(
    file_path: str,
    merge: bool = True,
) -> dict[str, Any]:
    """Load a DAZ Studio file into the current scene.

    Args:
        file_path: Absolute path to the file on the DAZ Studio machine
                   (.duf, .daz, .obj, .fbx, etc.).
        merge: If True (default), merge the file into the existing scene.
               If False, replace the current scene entirely.

    Returns:
      - success: true on success
      - file: the path that was loaded
    """
    return await _execute_by_id("vangard-load-file", {"filePath": file_path, "merge": merge})


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
