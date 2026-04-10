"""MCP server wrapping the DazScriptServer HTTP API for DAZ Studio."""

import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
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

# Load DazScript documentation
_DOCS_FILE = Path(__file__).parent / "dazscript_docs.json"
_DAZSCRIPT_DOCS: dict[str, dict[str, str]] = {}

try:
    with open(_DOCS_FILE) as f:
        _DAZSCRIPT_DOCS = json.load(f)
except (OSError, json.JSONDecodeError) as e:
    # Docs file missing or malformed - tools will return error message
    _DAZSCRIPT_DOCS = {
        "error": {
            "title": "Documentation Error",
            "content": f"Failed to load DazScript documentation: {e}"
        }
    }

# Shared HTTP client; initialised by the lifespan, torn down on exit.
_http_client: httpx.AsyncClient | None = None

# Macro recording state (session-level, in-memory)
_macro_recording: bool = False
_current_macro: dict[str, Any] | None = None
_macro_library: dict[str, dict[str, Any]] = {}


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


async def _execute_by_id_async(
    script_id: str,
    args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Submit a registered script for async execution; returns immediately with request_id.

    On 404 (DAZ Studio restarted and cleared the registry) re-registers once and retries,
    same as _execute_by_id.  Does NOT check success/error fields — the response shape is
    {request_id, status, submitted_at}.
    """
    client = _get_client()
    payload: dict[str, Any] = {}
    if args is not None:
        payload["args"] = args

    try:
        response = await client.post(f"/scripts/{script_id}/async", json=payload)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        _handle_network_error(exc)

    if response.status_code == 404:
        await _register_scripts(client)
        try:
            response = await client.post(f"/scripts/{script_id}/async", json=payload)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
            _handle_network_error(exc)

    _check_response(response)
    return response.json()


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
    var args = getArguments()[0] || {};
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
    var args = getArguments()[0] || {};
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
    var args = getArguments()[0] || {};
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
    var args = getArguments()[0] || {};
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
    var args = getArguments()[0] || {};
    App.getContentMgr().openFile(args.filePath, args.merge);
    return { success: true, file: args.filePath };
})()
"""

# args: {nodeLabel, includeZero}
# includeZero: if true, return all morphs; if false, only return morphs with non-zero values
# Returns: {morphs: [{label, name, value, path}], count}
# Lists all numeric properties (morphs) on a node
_LIST_MORPHS_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var includeZero = args.includeZero !== undefined ? args.includeZero : false;
    var morphs = [];

    for (var i = 0; i < node.getNumProperties(); i++) {
        var prop = node.getProperty(i);
        if (prop.inherits("DzNumericProperty")) {
            var value = prop.getValue();

            // Skip zero-valued morphs if includeZero is false
            if (!includeZero && value === 0) {
                continue;
            }

            // Get property path (useful for organizing morphs)
            var path = prop.getPath ? prop.getPath() : "";

            morphs.push({
                label: prop.getLabel(),
                name: prop.getName(),
                value: value,
                path: path
            });
        }
    }

    return {
        morphs: morphs,
        count: morphs.length,
        nodeLabel: node.getLabel()
    };
})()
"""

# args: {nodeLabel, pattern, includeZero}
# pattern: substring to search for in morph label or name (case-insensitive)
# includeZero: if true, return all matching morphs; if false, only non-zero values
# Returns: {morphs: [{label, name, value, path}], count, pattern}
# Searches for morphs matching a pattern
_SEARCH_MORPHS_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var pattern = args.pattern ? args.pattern.toLowerCase() : "";
    var includeZero = args.includeZero !== undefined ? args.includeZero : false;
    var morphs = [];

    for (var i = 0; i < node.getNumProperties(); i++) {
        var prop = node.getProperty(i);
        if (prop.inherits("DzNumericProperty")) {
            var label = prop.getLabel().toLowerCase();
            var name = prop.getName().toLowerCase();
            var value = prop.getValue();

            // Check if label or name contains pattern
            var matches = (label.indexOf(pattern) !== -1) || (name.indexOf(pattern) !== -1);

            if (matches) {
                // Skip zero-valued morphs if includeZero is false
                if (!includeZero && value === 0) {
                    continue;
                }

                var path = prop.getPath ? prop.getPath() : "";

                morphs.push({
                    label: prop.getLabel(),
                    name: prop.getName(),
                    value: value,
                    path: path
                });
            }
        }
    }

    return {
        morphs: morphs,
        count: morphs.length,
        pattern: args.pattern,
        nodeLabel: node.getLabel()
    };
})()
"""

# args: {nodeLabel, maxDepth}
# maxDepth: maximum recursion depth (default 10, 0 = unlimited)
# Returns: {node, children: [{node, children}], totalDescendants}
# Gets complete hierarchy tree for a node
_GET_NODE_HIERARCHY_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var maxDepth = args.maxDepth !== undefined ? args.maxDepth : 10;
    var totalDescendants = 0;

    function buildHierarchy(n, depth) {
        if (maxDepth > 0 && depth >= maxDepth) {
            return null;
        }

        var nodeInfo = {
            label: n.getLabel(),
            name: n.getName(),
            type: n.className()
        };

        var children = [];
        for (var i = 0; i < n.getNumNodeChildren(); i++) {
            totalDescendants++;
            var childHierarchy = buildHierarchy(n.getNodeChild(i), depth + 1);
            if (childHierarchy) {
                children.push(childHierarchy);
            }
        }

        if (children.length > 0) {
            nodeInfo.children = children;
        }

        return nodeInfo;
    }

    var hierarchy = buildHierarchy(node, 0);

    return {
        node: node.getLabel(),
        hierarchy: hierarchy,
        totalDescendants: totalDescendants
    };
})()
"""

# args: {nodeLabel}
# Returns: {node, children: [{label, name, type}], count}
# Lists direct children of a node
_LIST_CHILDREN_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var children = [];
    for (var i = 0; i < node.getNumNodeChildren(); i++) {
        var child = node.getNodeChild(i);
        children.push({
            label: child.getLabel(),
            name: child.getName(),
            type: child.className()
        });
    }

    return {
        node: node.getLabel(),
        children: children,
        count: children.length
    };
})()
"""

# args: {nodeLabel}
# Returns: {node, parent: {label, name, type} | null}
# Gets parent node of a node
_GET_PARENT_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var parent = node.getNodeParent();

    return {
        node: node.getLabel(),
        parent: parent ? {
            label: parent.getLabel(),
            name: parent.getName(),
            type: parent.className()
        } : null
    };
})()
"""

# args: {nodeLabel, parentLabel, maintainWorldTransform}
# maintainWorldTransform: if true, adjust local transform to maintain world position
# Returns: {success, node, newParent, previousParent}
# Sets parent of a node
_SET_PARENT_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var newParent = Scene.findNodeByLabel(args.parentLabel);
    if (!newParent) newParent = Scene.findNode(args.parentLabel);
    if (!newParent) throw new Error("Parent node not found: " + args.parentLabel);

    var maintainWorldTransform = args.maintainWorldTransform !== undefined ? args.maintainWorldTransform : true;

    var previousParent = node.getNodeParent();
    var previousParentLabel = previousParent ? previousParent.getLabel() : null;

    // Store world transform if needed
    var worldPos = null;
    var worldRot = null;
    if (maintainWorldTransform) {
        worldPos = node.getWSPos();
        worldRot = node.getWSRot();
    }

    // Set new parent
    node.setNodeParent(newParent, maintainWorldTransform);

    return {
        success: true,
        node: node.getLabel(),
        newParent: newParent.getLabel(),
        previousParent: previousParentLabel
    };
})()
"""

# args: {characterLabel, targetX, targetY, targetZ, mode}
# mode: "eyes", "head", "neck", "torso", "full"
# Returns: {success, character, mode, rotatedBones}
# Makes character look at a world-space point with cascading body involvement
_LOOK_AT_POINT_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    function findBone(fig, name) {
        function search(node) {
            if (node.getName() === name) return node;
            for (var i = 0; i < node.getNumNodeChildren(); i++) {
                var result = search(node.getNodeChild(i));
                if (result) return result;
            }
            return null;
        }
        return search(fig);
    }

    var figure = Scene.findNodeByLabel(args.characterLabel);
    if (!figure) figure = Scene.findNode(args.characterLabel);
    if (!figure) throw new Error("Character not found: " + args.characterLabel);

    var targetX = args.targetX;
    var targetY = args.targetY;
    var targetZ = args.targetZ;
    var mode = args.mode || "head";

    var rotatedBones = [];

    // Get bone positions and calculate rotations
    function rotateBoneToward(bone, tx, ty, tz, scale) {
        if (!bone) return false;
        var pos = bone.getWSPos();
        var dx = tx - pos.x;
        var dy = ty - pos.y;
        var dz = tz - pos.z;

        // Calculate angles
        var angleY = Math.atan2(dx, dz) * (180 / Math.PI) * scale;
        var dist = Math.sqrt(dx*dx + dz*dz);
        var angleX = Math.atan2(dy, dist) * (180 / Math.PI) * scale;

        var yProp = bone.findProperty("YRotate");
        var xProp = bone.findProperty("XRotate");

        if (yProp) {
            var current = yProp.getValue();
            yProp.setValue(current + angleY);
        }
        if (xProp) {
            var current = xProp.getValue();
            xProp.setValue(current + angleX);
        }

        rotatedBones.push(bone.getLabel());
        return true;
    }

    // Eyes (if mode is eyes or higher)
    if (mode === "eyes" || mode === "head" || mode === "neck" || mode === "torso" || mode === "full") {
        var lEye = findBone(figure, "lEye");
        var rEye = findBone(figure, "rEye");
        if (lEye) rotateBoneToward(lEye, targetX, targetY, targetZ, 1.0);
        if (rEye) rotateBoneToward(rEye, targetX, targetY, targetZ, 1.0);
    }

    // Head (if mode is head or higher)
    if (mode === "head" || mode === "neck" || mode === "torso" || mode === "full") {
        var head = findBone(figure, "head");
        if (head) rotateBoneToward(head, targetX, targetY, targetZ, 0.6);
    }

    // Neck (if mode is neck or higher)
    if (mode === "neck" || mode === "torso" || mode === "full") {
        var neckUpper = findBone(figure, "neckUpper");
        var neckLower = findBone(figure, "neckLower");
        if (neckUpper) rotateBoneToward(neckUpper, targetX, targetY, targetZ, 0.3);
        if (neckLower) rotateBoneToward(neckLower, targetX, targetY, targetZ, 0.3);
    }

    // Torso (if mode is torso or full)
    if (mode === "torso" || mode === "full") {
        var chestUpper = findBone(figure, "chestUpper");
        var chestLower = findBone(figure, "chestLower");
        if (chestUpper) rotateBoneToward(chestUpper, targetX, targetY, targetZ, 0.15);
        if (chestLower) rotateBoneToward(chestLower, targetX, targetY, targetZ, 0.15);
    }

    // Full body rotation (if mode is full)
    if (mode === "full") {
        var hip = findBone(figure, "hip");
        if (hip) rotateBoneToward(hip, targetX, targetY, targetZ, 0.1);
    }

    return {
        success: true,
        character: figure.getLabel(),
        mode: mode,
        rotatedBones: rotatedBones
    };
})()
"""

# args: {sourceLabel, targetLabel, mode}
# mode: "eyes", "head", "neck", "torso", "full" (default: "head")
# Returns: {success, source, target, mode, targetPosition}
# Makes source character look at target character's head position
_LOOK_AT_CHARACTER_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    function findBone(fig, name) {
        function search(node) {
            if (node.getName() === name) return node;
            for (var i = 0; i < node.getNumNodeChildren(); i++) {
                var result = search(node.getNodeChild(i));
                if (result) return result;
            }
            return null;
        }
        return search(fig);
    }

    var source = Scene.findNodeByLabel(args.sourceLabel);
    if (!source) source = Scene.findNode(args.sourceLabel);
    if (!source) throw new Error("Source character not found: " + args.sourceLabel);

    var target = Scene.findNodeByLabel(args.targetLabel);
    if (!target) target = Scene.findNode(args.targetLabel);
    if (!target) throw new Error("Target character not found: " + args.targetLabel);

    // Find target's head to get face position
    var targetHead = findBone(target, "head");
    if (!targetHead) {
        // Fallback to figure root position + approximate head height
        var pos = target.getWSPos();
        var targetX = pos.x;
        var targetY = pos.y + 163; // Approximate head height for Genesis 9
        var targetZ = pos.z;
    } else {
        var headPos = targetHead.getWSPos();
        var targetX = headPos.x;
        var targetY = headPos.y;
        var targetZ = headPos.z;
    }

    var mode = args.mode || "head";
    var rotatedBones = [];

    // Reuse rotation logic from look-at-point
    function rotateBoneToward(bone, tx, ty, tz, scale) {
        if (!bone) return false;
        var pos = bone.getWSPos();
        var dx = tx - pos.x;
        var dy = ty - pos.y;
        var dz = tz - pos.z;

        var angleY = Math.atan2(dx, dz) * (180 / Math.PI) * scale;
        var dist = Math.sqrt(dx*dx + dz*dz);
        var angleX = Math.atan2(dy, dist) * (180 / Math.PI) * scale;

        var yProp = bone.findProperty("YRotate");
        var xProp = bone.findProperty("XRotate");

        if (yProp) yProp.setValue(yProp.getValue() + angleY);
        if (xProp) xProp.setValue(xProp.getValue() + angleX);

        rotatedBones.push(bone.getLabel());
        return true;
    }

    if (mode === "eyes" || mode === "head" || mode === "neck" || mode === "torso" || mode === "full") {
        var lEye = findBone(source, "lEye");
        var rEye = findBone(source, "rEye");
        if (lEye) rotateBoneToward(lEye, targetX, targetY, targetZ, 1.0);
        if (rEye) rotateBoneToward(rEye, targetX, targetY, targetZ, 1.0);
    }

    if (mode === "head" || mode === "neck" || mode === "torso" || mode === "full") {
        var head = findBone(source, "head");
        if (head) rotateBoneToward(head, targetX, targetY, targetZ, 0.6);
    }

    if (mode === "neck" || mode === "torso" || mode === "full") {
        var neckUpper = findBone(source, "neckUpper");
        var neckLower = findBone(source, "neckLower");
        if (neckUpper) rotateBoneToward(neckUpper, targetX, targetY, targetZ, 0.3);
        if (neckLower) rotateBoneToward(neckLower, targetX, targetY, targetZ, 0.3);
    }

    if (mode === "torso" || mode === "full") {
        var chestUpper = findBone(source, "chestUpper");
        var chestLower = findBone(source, "chestLower");
        if (chestUpper) rotateBoneToward(chestUpper, targetX, targetY, targetZ, 0.15);
        if (chestLower) rotateBoneToward(chestLower, targetX, targetY, targetZ, 0.15);
    }

    if (mode === "full") {
        var hip = findBone(source, "hip");
        if (hip) rotateBoneToward(hip, targetX, targetY, targetZ, 0.1);
    }

    return {
        success: true,
        source: source.getLabel(),
        target: target.getLabel(),
        mode: mode,
        targetPosition: {x: targetX, y: targetY, z: targetZ},
        rotatedBones: rotatedBones
    };
})()
"""

# args: {characterLabel, side, targetX, targetY, targetZ}
# side: "left" or "right"
# Returns: {success, character, side, bones}
# Position arm/hand to reach toward world-space point using pseudo-IK
_REACH_TOWARD_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    function findBone(fig, name) {
        function search(node) {
            if (node.getName() === name) return node;
            for (var i = 0; i < node.getNumNodeChildren(); i++) {
                var result = search(node.getNodeChild(i));
                if (result) return result;
            }
            return null;
        }
        return search(fig);
    }

    function clamp(val, min, max) {
        return Math.max(min, Math.min(max, val));
    }

    var figure = Scene.findNodeByLabel(args.characterLabel);
    if (!figure) figure = Scene.findNode(args.characterLabel);
    if (!figure) throw new Error("Character not found: " + args.characterLabel);

    var side = args.side || "right";
    var prefix = (side === "right") ? "r" : "l";

    var shoulder = findBone(figure, prefix + "ShldrBend");
    var forearm = findBone(figure, prefix + "ForearmBend");
    var hand = findBone(figure, prefix + "Hand");

    if (!shoulder || !forearm) {
        throw new Error("Arm bones not found for side: " + side);
    }

    var targetX = args.targetX;
    var targetY = args.targetY;
    var targetZ = args.targetZ;

    // Get shoulder world position
    var shoulderPos = shoulder.getWSPos();
    var dx = targetX - shoulderPos.x;
    var dy = targetY - shoulderPos.y;
    var dz = targetZ - shoulderPos.z;

    // Calculate distance to target
    var dist = Math.sqrt(dx*dx + dy*dy + dz*dz);

    // Calculate shoulder rotation angles
    // YRotate: turn toward target (left/right)
    var angleY = Math.atan2(dx, dz) * (180 / Math.PI);

    // XRotate: pitch toward target (up/down)
    var horizDist = Math.sqrt(dx*dx + dz*dz);
    var angleX = Math.atan2(dy, horizDist) * (180 / Math.PI);

    // ZRotate: lift arm away from body
    var angleZ = Math.atan2(Math.abs(dx), Math.abs(dy)) * (180 / Math.PI);
    if (side === "left") angleZ = -angleZ;

    // Apply shoulder rotations with realistic limits
    var xProp = shoulder.findProperty("XRotate");
    var yProp = shoulder.findProperty("YRotate");
    var zProp = shoulder.findProperty("ZRotate");

    if (xProp) xProp.setValue(clamp(angleX, -90, 180));
    if (yProp) yProp.setValue(clamp(angleY, -90, 90));
    if (zProp) zProp.setValue(clamp(angleZ, side === "right" ? -30 : -180, side === "right" ? 180 : 30));

    // Calculate elbow bend based on distance
    // Approximate arm length: shoulder to hand ~60cm
    // If target is far, straighten arm; if close, bend elbow
    var maxReach = 60; // Approximate full arm length in cm
    var bendFactor = Math.max(0, Math.min(1, 1 - (dist / maxReach)));
    var elbowBend = -140 * bendFactor; // -140 is max elbow bend

    var elbowProp = forearm.findProperty("YRotate");
    if (elbowProp) elbowProp.setValue(clamp(elbowBend, -140, 0));

    // Slight hand rotation for natural look
    if (hand) {
        var handXProp = hand.findProperty("XRotate");
        if (handXProp) handXProp.setValue(-10); // Slight downward tilt
    }

    return {
        success: true,
        character: figure.getLabel(),
        side: side,
        targetDistance: dist,
        bones: [
            shoulder.getLabel(),
            forearm.getLabel(),
            hand ? hand.getLabel() : null
        ]
    };
})()
"""

# args: {char1Label, char2Label, interactionType, distance}
# interactionType: "hug", "shoulder-arm", "handshake", "face-each-other"
# distance: optional override for character spacing (cm)
# Returns: {success, char1, char2, interactionType, applied}
# Coordinate two characters for interactive poses
_INTERACTIVE_POSE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    function findBone(fig, name) {
        function search(node) {
            if (node.getName() === name) return node;
            for (var i = 0; i < node.getNumNodeChildren(); i++) {
                var result = search(node.getNodeChild(i));
                if (result) return result;
            }
            return null;
        }
        return search(fig);
    }

    function clamp(val, min, max) {
        return Math.max(min, Math.min(max, val));
    }

    var char1 = Scene.findNodeByLabel(args.char1Label);
    if (!char1) char1 = Scene.findNode(args.char1Label);
    if (!char1) throw new Error("Character 1 not found: " + args.char1Label);

    var char2 = Scene.findNodeByLabel(args.char2Label);
    if (!char2) char2 = Scene.findNode(args.char2Label);
    if (!char2) throw new Error("Character 2 not found: " + args.char2Label);

    var interactionType = args.interactionType || "face-each-other";
    var distance = args.distance;

    var pos1 = char1.getWSPos();
    var pos2 = char2.getWSPos();

    var applied = [];

    // Face each other (base for all interactions)
    if (interactionType === "face-each-other" || interactionType === "hug" ||
        interactionType === "handshake" || interactionType === "shoulder-arm") {

        // Position characters to face each other at specified distance
        if (distance) {
            var midX = (pos1.x + pos2.x) / 2;
            var midZ = (pos1.z + pos2.z) / 2;

            char1.findProperty("XTranslate").setValue(midX - distance/2);
            char1.findProperty("ZTranslate").setValue(midZ);

            char2.findProperty("XTranslate").setValue(midX + distance/2);
            char2.findProperty("ZTranslate").setValue(midZ);
        }

        // Rotate to face each other
        var hip1 = findBone(char1, "hip");
        var hip2 = findBone(char2, "hip");

        if (hip1) hip1.findProperty("YRotate").setValue(90);
        if (hip2) hip2.findProperty("YRotate").setValue(-90);

        applied.push("facing");
    }

    // Hug pose
    if (interactionType === "hug") {
        // Both arms around each other
        var r1Shoulder = findBone(char1, "rShldrBend");
        var r1Forearm = findBone(char1, "rForearmBend");
        var l1Shoulder = findBone(char1, "lShldrBend");
        var l1Forearm = findBone(char1, "lForearmBend");

        if (r1Shoulder) {
            r1Shoulder.findProperty("XRotate").setValue(10);
            r1Shoulder.findProperty("ZRotate").setValue(70);
        }
        if (r1Forearm) r1Forearm.findProperty("YRotate").setValue(-80);

        if (l1Shoulder) {
            l1Shoulder.findProperty("XRotate").setValue(10);
            l1Shoulder.findProperty("ZRotate").setValue(-70);
        }
        if (l1Forearm) l1Forearm.findProperty("YRotate").setValue(-80);

        // Char 2 mirror
        var r2Shoulder = findBone(char2, "rShldrBend");
        var r2Forearm = findBone(char2, "rForearmBend");
        var l2Shoulder = findBone(char2, "lShldrBend");
        var l2Forearm = findBone(char2, "lForearmBend");

        if (r2Shoulder) {
            r2Shoulder.findProperty("XRotate").setValue(10);
            r2Shoulder.findProperty("ZRotate").setValue(70);
        }
        if (r2Forearm) r2Forearm.findProperty("YRotate").setValue(-80);

        if (l2Shoulder) {
            l2Shoulder.findProperty("XRotate").setValue(10);
            l2Shoulder.findProperty("ZRotate").setValue(-70);
        }
        if (l2Forearm) l2Forearm.findProperty("YRotate").setValue(-80);

        applied.push("hug arms");
    }

    // Shoulder-arm (char1 puts arm around char2's shoulders)
    if (interactionType === "shoulder-arm") {
        var r1Shoulder = findBone(char1, "rShldrBend");
        var r1Forearm = findBone(char1, "rForearmBend");

        if (r1Shoulder) {
            r1Shoulder.findProperty("XRotate").setValue(0);
            r1Shoulder.findProperty("ZRotate").setValue(90); // Arm out to side
        }
        if (r1Forearm) r1Forearm.findProperty("YRotate").setValue(-45); // Slight bend

        // Char 2 leans slightly toward char1
        var chest2 = findBone(char2, "chestUpper");
        if (chest2) chest2.findProperty("ZRotate").setValue(-10);

        applied.push("shoulder-arm");
    }

    // Handshake
    if (interactionType === "handshake") {
        var r1Shoulder = findBone(char1, "rShldrBend");
        var r1Forearm = findBone(char1, "rForearmBend");

        var r2Shoulder = findBone(char2, "rShldrBend");
        var r2Forearm = findBone(char2, "rForearmBend");

        // Char 1 reaches right hand forward
        if (r1Shoulder) {
            r1Shoulder.findProperty("XRotate").setValue(30); // Forward
            r1Shoulder.findProperty("ZRotate").setValue(10); // Slightly out
        }
        if (r1Forearm) r1Forearm.findProperty("YRotate").setValue(-90);

        // Char 2 reaches right hand forward (mirror)
        if (r2Shoulder) {
            r2Shoulder.findProperty("XRotate").setValue(30);
            r2Shoulder.findProperty("ZRotate").setValue(10);
        }
        if (r2Forearm) r2Forearm.findProperty("YRotate").setValue(-90);

        applied.push("handshake");
    }

    return {
        success: true,
        char1: char1.getLabel(),
        char2: char2.getLabel(),
        interactionType: interactionType,
        applied: applied
    };
})()
"""

# args: {operations: [{nodeLabel, propertyName, value}]}
# Returns: {results: [{success, node, property, value, error}], successCount, failureCount}
# Batch property setting with individual error handling for each operation
_BATCH_SET_PROPERTIES_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var operations = args.operations || [];
    var results = [];
    var successCount = 0;
    var failureCount = 0;

    for (var i = 0; i < operations.length; i++) {
        var op = operations[i];
        var result = { success: false, node: op.nodeLabel };

        try {
            var n = Scene.findNodeByLabel(op.nodeLabel);
            if (!n) n = Scene.findNode(op.nodeLabel);
            if (!n) throw new Error("Node not found: " + op.nodeLabel);

            var prop = null;
            for (var p = 0; p < n.getNumProperties(); p++) {
                var pr = n.getProperty(p);
                if (pr.getLabel() === op.propertyName || pr.getName() === op.propertyName) {
                    prop = pr;
                    break;
                }
            }

            if (!prop) throw new Error("Property not found: " + op.propertyName);
            if (!prop.inherits("DzNumericProperty")) throw new Error("Property is not numeric: " + op.propertyName);

            prop.setValue(op.value);
            result.success = true;
            result.property = prop.getLabel();
            result.value = prop.getValue();
            successCount++;
        } catch (e) {
            result.error = e.message || String(e);
            failureCount++;
        }

        results.push(result);
    }

    return {
        results: results,
        successCount: successCount,
        failureCount: failureCount,
        total: operations.length
    };
})()
"""

# args: {nodeLabels: [string], transforms: {propertyName: value}}
# Returns: {results: [{success, node, applied, error}], successCount, failureCount}
# Apply same transform properties to multiple nodes
_BATCH_TRANSFORM_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodeLabels = args.nodeLabels || [];
    var transforms = args.transforms || {};
    var results = [];
    var successCount = 0;
    var failureCount = 0;

    for (var i = 0; i < nodeLabels.length; i++) {
        var nodeLabel = nodeLabels[i];
        var result = { success: false, node: nodeLabel, applied: [] };

        try {
            var n = Scene.findNodeByLabel(nodeLabel);
            if (!n) n = Scene.findNode(nodeLabel);
            if (!n) throw new Error("Node not found: " + nodeLabel);

            for (var propName in transforms) {
                var prop = null;
                for (var p = 0; p < n.getNumProperties(); p++) {
                    var pr = n.getProperty(p);
                    if (pr.getLabel() === propName || pr.getName() === propName) {
                        prop = pr;
                        break;
                    }
                }

                if (prop && prop.inherits("DzNumericProperty")) {
                    prop.setValue(transforms[propName]);
                    result.applied.push(prop.getLabel());
                }
            }

            result.success = true;
            successCount++;
        } catch (e) {
            result.error = e.message || String(e);
            failureCount++;
        }

        results.push(result);
    }

    return {
        results: results,
        successCount: successCount,
        failureCount: failureCount,
        total: nodeLabels.length
    };
})()
"""

# args: {nodeLabels: [string], visible: boolean}
# Returns: {results: [{success, node, visible, error}], successCount, failureCount}
# Show or hide multiple nodes
_BATCH_VISIBILITY_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodeLabels = args.nodeLabels || [];
    var visible = args.visible !== undefined ? args.visible : true;
    var results = [];
    var successCount = 0;
    var failureCount = 0;

    for (var i = 0; i < nodeLabels.length; i++) {
        var nodeLabel = nodeLabels[i];
        var result = { success: false, node: nodeLabel };

        try {
            var n = Scene.findNodeByLabel(nodeLabel);
            if (!n) n = Scene.findNode(nodeLabel);
            if (!n) throw new Error("Node not found: " + nodeLabel);

            n.setVisible(visible);
            result.success = true;
            result.visible = visible;
            successCount++;
        } catch (e) {
            result.error = e.message || String(e);
            failureCount++;
        }

        results.push(result);
    }

    return {
        results: results,
        successCount: successCount,
        failureCount: failureCount,
        total: nodeLabels.length
    };
})()
"""

# args: {nodeLabels: [string], addToSelection: boolean}
# Returns: {selected: [labels], count}
# Select multiple nodes (replace or add to current selection)
_BATCH_SELECT_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodeLabels = args.nodeLabels || [];
    var addToSelection = args.addToSelection !== undefined ? args.addToSelection : false;
    var selected = [];

    // Clear selection if replacing
    if (!addToSelection) {
        Scene.selectAllNodes(false);
    }

    for (var i = 0; i < nodeLabels.length; i++) {
        var nodeLabel = nodeLabels[i];
        var n = Scene.findNodeByLabel(nodeLabel);
        if (!n) n = Scene.findNode(nodeLabel);

        if (n) {
            n.select(true);
            selected.push(n.getLabel());
        }
    }

    return {
        selected: selected,
        count: selected.length,
        total: nodeLabels.length
    };
})()
"""

# args: {cameraLabel}
# Returns: {success, camera, previousCamera}
# Set which camera is active in the viewport
_SET_ACTIVE_CAMERA_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cam = Scene.findNodeByLabel(args.cameraLabel);
    if (!cam) cam = Scene.findNode(args.cameraLabel);
    if (!cam) throw new Error("Camera not found: " + args.cameraLabel);
    if (!cam.inherits("DzCamera")) throw new Error("Node is not a camera: " + args.cameraLabel);

    var previousCamera = null;
    var viewportMgr = MainWindow.getViewportMgr();
    if (viewportMgr) {
        var activeViewport = viewportMgr.getActiveViewport();
        if (activeViewport) {
            var prevCam = activeViewport.get3DViewport().getCamera();
            if (prevCam) previousCamera = prevCam.getLabel();
            activeViewport.get3DViewport().setCamera(cam);
        }
    }

    return {
        success: true,
        camera: cam.getLabel(),
        previousCamera: previousCamera
    };
})()
"""

# args: {cameraLabel, targetLabel, distance, angleHorizontal, angleVertical}
# Returns: {success, camera, target, position}
# Position camera orbiting around a target node at specified angle and distance
_ORBIT_CAMERA_AROUND_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cam = Scene.findNodeByLabel(args.cameraLabel);
    if (!cam) cam = Scene.findNode(args.cameraLabel);
    if (!cam) throw new Error("Camera not found: " + args.cameraLabel);

    var target = Scene.findNodeByLabel(args.targetLabel);
    if (!target) target = Scene.findNode(args.targetLabel);
    if (!target) throw new Error("Target not found: " + args.targetLabel);

    var distance = args.distance !== undefined ? args.distance : 200;
    var angleH = args.angleHorizontal !== undefined ? args.angleHorizontal : 45;
    var angleV = args.angleVertical !== undefined ? args.angleVertical : 15;

    // Get target world position
    var targetPos = target.getWSPos();
    var targetY = targetPos.y;

    // Calculate camera position using spherical coordinates
    var angleHRad = angleH * (Math.PI / 180);
    var angleVRad = angleV * (Math.PI / 180);

    var x = targetPos.x + distance * Math.cos(angleVRad) * Math.sin(angleHRad);
    var y = targetY + distance * Math.sin(angleVRad);
    var z = targetPos.z + distance * Math.cos(angleVRad) * Math.cos(angleHRad);

    // Set camera position
    cam.findProperty("XTranslate").setValue(x);
    cam.findProperty("YTranslate").setValue(y);
    cam.findProperty("ZTranslate").setValue(z);

    // Aim camera at target
    cam.aimAt(targetPos);

    return {
        success: true,
        camera: cam.getLabel(),
        target: target.getLabel(),
        position: {x: x, y: y, z: z},
        targetPosition: {x: targetPos.x, y: targetPos.y, z: targetPos.z}
    };
})()
"""

# args: {cameraLabel, nodeLabel, distance}
# Returns: {success, camera, node, position}
# Frame camera to show a node by positioning at calculated distance
_FRAME_CAMERA_TO_NODE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cam = Scene.findNodeByLabel(args.cameraLabel);
    if (!cam) cam = Scene.findNode(args.cameraLabel);
    if (!cam) throw new Error("Camera not found: " + args.cameraLabel);

    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    // Get node bounding box (getWSBoundingBox is on DzNode; getSize() returns scalar diagonal)
    var bbox = node.getWSBoundingBox();
    var center = bbox.getCenter();
    var sizeX = bbox.maxX - bbox.minX;
    var sizeY = bbox.maxY - bbox.minY;
    var sizeZ = bbox.maxZ - bbox.minZ;
    var maxDim = Math.max(sizeX, Math.max(sizeY, sizeZ));

    // Calculate distance based on object size or use provided distance
    var distance = args.distance !== undefined ? args.distance : maxDim * 2.5;

    // Position camera in front of object (positive Z)
    var camX = center.x;
    var camY = center.y;
    var camZ = center.z + distance;

    cam.findProperty("XTranslate").setValue(camX);
    cam.findProperty("YTranslate").setValue(camY);
    cam.findProperty("ZTranslate").setValue(camZ);

    // Aim camera at center
    cam.aimAt(center);

    return {
        success: true,
        camera: cam.getLabel(),
        node: node.getLabel(),
        position: {x: camX, y: camY, z: camZ},
        nodeCenter: {x: center.x, y: center.y, z: center.z},
        nodeSize: {x: sizeX, y: sizeY, z: sizeZ}
    };
})()
"""

# args: {cameraLabel}
# Returns: {preset: {transforms, label}}
# Save camera position and rotation as preset data
_SAVE_CAMERA_PRESET_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cam = Scene.findNodeByLabel(args.cameraLabel);
    if (!cam) cam = Scene.findNode(args.cameraLabel);
    if (!cam) throw new Error("Camera not found: " + args.cameraLabel);

    var preset = {
        label: cam.getLabel(),
        transforms: {}
    };

    var props = ["XTranslate", "YTranslate", "ZTranslate",
                 "XRotate", "YRotate", "ZRotate",
                 "XScale", "YScale", "ZScale"];

    for (var i = 0; i < props.length; i++) {
        var prop = cam.findProperty(props[i]);
        if (prop) {
            preset.transforms[props[i]] = prop.getValue();
        }
    }

    return {preset: preset};
})()
"""

# args: {cameraLabel, preset}
# Returns: {success, camera, applied}
# Restore camera position and rotation from preset data
_LOAD_CAMERA_PRESET_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cam = Scene.findNodeByLabel(args.cameraLabel);
    if (!cam) cam = Scene.findNode(args.cameraLabel);
    if (!cam) throw new Error("Camera not found: " + args.cameraLabel);

    var preset = args.preset;
    if (!preset || !preset.transforms) throw new Error("Invalid preset data");

    var applied = [];
    for (var propName in preset.transforms) {
        var prop = cam.findProperty(propName);
        if (prop) {
            prop.setValue(preset.transforms[propName]);
            applied.push(propName);
        }
    }

    return {
        success: true,
        camera: cam.getLabel(),
        applied: applied
    };
})()
"""

# args: {cameraLabel, outputPath}
# Returns: {success, camera, outputPath}
# Render from specific camera (doesn't change active viewport camera)
_RENDER_WITH_CAMERA_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cam = Scene.findNodeByLabel(args.cameraLabel);
    if (!cam) cam = Scene.findNode(args.cameraLabel);
    if (!cam) throw new Error("Camera not found: " + args.cameraLabel);
    if (!cam.inherits("DzCamera")) throw new Error("Node is not a camera: " + args.cameraLabel);

    var renderMgr = App.getRenderMgr();
    var opts = renderMgr.getRenderOptions();

    // Save previous camera
    var previousCam = opts.camera;

    // Set render camera
    opts.camera = cam;

    // Set output if provided
    if (args.outputPath) {
        opts.renderImgToId = 0;
        opts.renderImgFilename = args.outputPath;
    }

    // Render
    renderMgr.doRender();

    // Restore previous camera
    if (previousCam) {
        opts.camera = previousCam;
    }

    return {
        success: true,
        camera: cam.getLabel(),
        outputPath: args.outputPath || null
    };
})()
"""

# args: none
# Returns: {renderToFile, currentCamera, aspectRatio, aspectWidth, aspectHeight}
# Get current render settings
_GET_RENDER_SETTINGS_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var renderMgr = App.getRenderMgr();
    var opts = renderMgr.getRenderOptions();

    var result = {
        renderToFile: opts.renderImgToId === 0,
        outputPath: opts.renderImgToId === 0 ? opts.renderImgFilename : null,
        aspectRatio: opts.aspect,
        aspectWidth: opts.aspectWidth,
        aspectHeight: opts.aspectHeight
    };

    // Get current render camera
    if (opts.camera) {
        result.currentCamera = opts.camera.getLabel();
    } else {
        result.currentCamera = null;
    }

    return result;
})()
"""

# args: {cameras: [labels], outputDir, baseFilename}
# Returns: {success, rendered: [{camera, outputPath}], total}
# Render from multiple cameras in sequence
_BATCH_RENDER_CAMERAS_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cameras = args.cameras || [];
    var outputDir = args.outputDir || "";
    var baseFilename = args.baseFilename || "render";

    var renderMgr = App.getRenderMgr();
    var opts = renderMgr.getRenderOptions();
    var previousCam = opts.camera;

    var rendered = [];

    for (var i = 0; i < cameras.length; i++) {
        var camLabel = cameras[i];
        var cam = Scene.findNodeByLabel(camLabel);
        if (!cam) cam = Scene.findNode(camLabel);

        if (cam && cam.inherits("DzCamera")) {
            // Build output path
            var outputPath = outputDir;
            if (outputPath && outputPath.charAt(outputPath.length - 1) !== "/" &&
                outputPath.charAt(outputPath.length - 1) !== "\\\\") {
                outputPath += "/";
            }
            outputPath += baseFilename + "_" + camLabel.replace(/[^a-zA-Z0-9]/g, "_") + ".png";

            // Set camera and output
            opts.camera = cam;
            opts.renderImgToId = 0;
            opts.renderImgFilename = outputPath;

            // Render
            renderMgr.doRender();

            rendered.push({
                camera: cam.getLabel(),
                outputPath: outputPath
            });
        }
    }

    // Restore previous camera
    if (previousCam) {
        opts.camera = previousCam;
    }

    return {
        success: true,
        rendered: rendered,
        total: cameras.length
    };
})()
"""

# args: {startFrame, endFrame, outputDir, filenamePattern, camera}
# Returns: {success, rendered: [{frame, outputPath}], total}
# Render animation frame range
_RENDER_ANIMATION_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var startFrame = args.startFrame !== undefined ? args.startFrame : Scene.getAnimRange().getStart();
    var endFrame = args.endFrame !== undefined ? args.endFrame : Scene.getAnimRange().getEnd();
    var outputDir = args.outputDir || "";
    var filenamePattern = args.filenamePattern || "frame";

    var renderMgr = App.getRenderMgr();
    var opts = renderMgr.getRenderOptions();

    // Set camera if specified
    var previousCam = opts.camera;
    if (args.camera) {
        var cam = Scene.findNodeByLabel(args.camera);
        if (!cam) cam = Scene.findNode(args.camera);
        if (cam && cam.inherits("DzCamera")) {
            opts.camera = cam;
        }
    }

    var rendered = [];
    var previousFrame = Scene.getFrame();

    for (var frame = startFrame; frame <= endFrame; frame++) {
        // Set frame
        Scene.setFrame(frame);

        // Build output path with zero-padding
        var frameStr = String(frame);
        while (frameStr.length < 4) frameStr = "0" + frameStr;

        var outputPath = outputDir;
        if (outputPath && outputPath.charAt(outputPath.length - 1) !== "/" &&
            outputPath.charAt(outputPath.length - 1) !== "\\\\") {
            outputPath += "/";
        }
        outputPath += filenamePattern + "_" + frameStr + ".png";

        // Set output
        opts.renderImgToId = 0;
        opts.renderImgFilename = outputPath;

        // Render
        renderMgr.doRender();

        rendered.push({
            frame: frame,
            outputPath: outputPath
        });
    }

    // Restore previous frame
    Scene.setFrame(previousFrame);

    // Restore previous camera
    if (previousCam) {
        opts.camera = previousCam;
    }

    return {
        success: true,
        rendered: rendered,
        total: rendered.length,
        frames: {start: startFrame, end: endFrame}
    };
})()
"""

# args: {nodeLabel, propertyName, frame, value}
# Returns: {success, node, property, frame, value}
# Set a keyframe on a property at specified frame
_SET_KEYFRAME_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var prop = null;
    for (var p = 0; p < node.getNumProperties(); p++) {
        var pr = node.getProperty(p);
        if (pr.getLabel() === args.propertyName || pr.getName() === args.propertyName) {
            prop = pr;
            break;
        }
    }

    if (!prop) throw new Error("Property not found: " + args.propertyName);
    if (!prop.inherits("DzNumericProperty")) throw new Error("Property is not numeric: " + args.propertyName);

    var frame = args.frame;
    var value = args.value;

    // Set value at frame
    prop.setKeyFrame(frame, value);

    return {
        success: true,
        node: node.getLabel(),
        property: prop.getLabel(),
        frame: frame,
        value: value
    };
})()
"""

# args: {nodeLabel, propertyName}
# Returns: {keyframes: [{frame, value}], count}
# Get all keyframes for a property
_GET_KEYFRAMES_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var prop = null;
    for (var p = 0; p < node.getNumProperties(); p++) {
        var pr = node.getProperty(p);
        if (pr.getLabel() === args.propertyName || pr.getName() === args.propertyName) {
            prop = pr;
            break;
        }
    }

    if (!prop) throw new Error("Property not found: " + args.propertyName);
    if (!prop.inherits("DzNumericProperty")) throw new Error("Property is not numeric: " + args.propertyName);

    var keyframes = [];
    var numKeys = prop.getNumKeys();

    for (var i = 0; i < numKeys; i++) {
        var frame = prop.getKeyFrame(i);
        var value = prop.getKeyValue(i);
        keyframes.push({frame: frame, value: value});
    }

    return {
        keyframes: keyframes,
        count: numKeys
    };
})()
"""

# args: {nodeLabel, propertyName, frame}
# Returns: {success, node, property, frame, removed}
# Remove a keyframe at specified frame
_REMOVE_KEYFRAME_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var prop = null;
    for (var p = 0; p < node.getNumProperties(); p++) {
        var pr = node.getProperty(p);
        if (pr.getLabel() === args.propertyName || pr.getName() === args.propertyName) {
            prop = pr;
            break;
        }
    }

    if (!prop) throw new Error("Property not found: " + args.propertyName);
    if (!prop.inherits("DzNumericProperty")) throw new Error("Property is not numeric: " + args.propertyName);

    var frame = args.frame;
    var removed = false;

    // Find and remove keyframe at frame
    var numKeys = prop.getNumKeys();
    for (var i = 0; i < numKeys; i++) {
        if (prop.getKeyFrame(i) === frame) {
            prop.deleteKey(i);
            removed = true;
            break;
        }
    }

    return {
        success: true,
        node: node.getLabel(),
        property: prop.getLabel(),
        frame: frame,
        removed: removed
    };
})()
"""

# args: {nodeLabel, propertyName}
# Returns: {success, node, property, removed}
# Remove all keyframes from a property
_CLEAR_ANIMATION_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var prop = null;
    for (var p = 0; p < node.getNumProperties(); p++) {
        var pr = node.getProperty(p);
        if (pr.getLabel() === args.propertyName || pr.getName() === args.propertyName) {
            prop = pr;
            break;
        }
    }

    if (!prop) throw new Error("Property not found: " + args.propertyName);
    if (!prop.inherits("DzNumericProperty")) throw new Error("Property is not numeric: " + args.propertyName);

    var numKeys = prop.getNumKeys();
    // Delete keys in reverse order to avoid index shifting
    for (var i = numKeys - 1; i >= 0; i--) {
        prop.deleteKey(i);
    }

    return {
        success: true,
        node: node.getLabel(),
        property: prop.getLabel(),
        removed: numKeys
    };
})()
"""

# args: {frame}
# Returns: {success, frame, previousFrame}
# Set current animation frame
_SET_FRAME_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var frame = args.frame;
    var previousFrame = Scene.getFrame();
    Scene.setFrame(frame);

    return {
        success: true,
        frame: frame,
        previousFrame: previousFrame
    };
})()
"""

# args: {startFrame, endFrame}
# Returns: {success, startFrame, endFrame, previousStart, previousEnd}
# Set animation frame range
_SET_FRAME_RANGE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var startFrame = args.startFrame;
    var endFrame = args.endFrame;

    var timeStep = Scene.getTimeStep();
    var anim = Scene.getAnimRange();
    // DzTimeRange: .start and .end are tick-count properties (not methods)
    var previousStart = Math.round(anim.start / timeStep);
    var previousEnd   = Math.round(anim.end   / timeStep);

    Scene.setAnimRange(new DzTimeRange(startFrame * timeStep, endFrame * timeStep));

    return {
        success: true,
        startFrame: startFrame,
        endFrame: endFrame,
        previousStart: previousStart,
        previousEnd: previousEnd
    };
})()
"""

# args: none
# Returns: {currentFrame, startFrame, endFrame, fps}
# Get animation timeline info
_GET_ANIMATION_INFO_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var currentFrame = Scene.getFrame();
    var timeStep     = Scene.getTimeStep();
    var anim         = Scene.getAnimRange();
    // DzTimeRange: .start and .end are tick-count properties (not methods)
    var startFrame = Math.round(anim.start / timeStep);
    var endFrame   = Math.round(anim.end   / timeStep);
    // DAZ Studio uses 4800 ticks/second; getFPS() does not exist
    var fps = Math.round(4800 / timeStep);

    return {
        currentFrame: currentFrame,
        startFrame: startFrame,
        endFrame: endFrame,
        fps: fps,
        totalFrames: endFrame - startFrame + 1,
        durationSeconds: (endFrame - startFrame + 1) / fps
    };
})()
"""

# ---------------------------------------------------------------------------
# Phase 1: Spatial Query Scripts
# ---------------------------------------------------------------------------

# args: {nodeLabel}
# Returns: {node, world_position, local_position, rotation, scale}
_GET_WORLD_POSITION_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var wsPos = node.getWSPos();
    var lPos = node.getLocalPos ? node.getLocalPos() : node.getOrigin();
    var wsRot = node.getWSRot();
    var wsScale = node.getWSScale();

    return {
        node: node.getLabel(),
        world_position: { x: wsPos.x, y: wsPos.y, z: wsPos.z },
        local_position: { x: lPos.x, y: lPos.y, z: lPos.z },
        rotation: { x: wsRot.x, y: wsRot.y, z: wsRot.z },
        scale: { x: wsScale.x, y: wsScale.y, z: wsScale.z }
    };
})()
"""

# args: {nodeLabel}
# Returns: {node, min, max, center, width, height, depth}
_GET_BOUNDING_BOX_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var bbox = node.getWSBoundingBox();
    return {
        node: node.getLabel(),
        min: { x: bbox.minX, y: bbox.minY, z: bbox.minZ },
        max: { x: bbox.maxX, y: bbox.maxY, z: bbox.maxZ },
        center: {
            x: (bbox.minX + bbox.maxX) / 2,
            y: (bbox.minY + bbox.maxY) / 2,
            z: (bbox.minZ + bbox.maxZ) / 2
        },
        width:  bbox.maxX - bbox.minX,
        height: bbox.maxY - bbox.minY,
        depth:  bbox.maxZ - bbox.minZ
    };
})()
"""

# args: {node1Label, node2Label}
# Returns: {node1, node2, distance, vector, horizontal_distance, vertical_distance}
_CALCULATE_DISTANCE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var n1 = Scene.findNodeByLabel(args.node1Label);
    if (!n1) n1 = Scene.findNode(args.node1Label);
    if (!n1) throw new Error("Node not found: " + args.node1Label);

    var n2 = Scene.findNodeByLabel(args.node2Label);
    if (!n2) n2 = Scene.findNode(args.node2Label);
    if (!n2) throw new Error("Node not found: " + args.node2Label);

    var p1 = n1.getWSPos();
    var p2 = n2.getWSPos();

    var dx = p2.x - p1.x;
    var dy = p2.y - p1.y;
    var dz = p2.z - p1.z;

    var distance = Math.sqrt(dx*dx + dy*dy + dz*dz);
    var horizontal_distance = Math.sqrt(dx*dx + dz*dz);
    var vertical_distance = Math.abs(dy);

    return {
        node1: n1.getLabel(),
        node2: n2.getLabel(),
        distance: distance,
        vector: { dx: dx, dy: dy, dz: dz },
        horizontal_distance: horizontal_distance,
        vertical_distance: vertical_distance
    };
})()
"""

# args: {node1Label, node2Label}
# Returns: {node1, node2, distance, direction, angle_horizontal, angle_vertical,
#           relative_position, overlapping}
# Provides natural language spatial relationship between two nodes.
# Angles are from node1's perspective looking toward node2.
# angle_horizontal: 0=front(+Z), 90=right, 180=back, -90=left (in node1 local space)
# angle_vertical: positive=above, negative=below
_GET_SPATIAL_RELATIONSHIP_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var n1 = Scene.findNodeByLabel(args.node1Label);
    if (!n1) n1 = Scene.findNode(args.node1Label);
    if (!n1) throw new Error("Node not found: " + args.node1Label);

    var n2 = Scene.findNodeByLabel(args.node2Label);
    if (!n2) n2 = Scene.findNode(args.node2Label);
    if (!n2) throw new Error("Node not found: " + args.node2Label);

    var p1 = n1.getWSPos();
    var p2 = n2.getWSPos();

    var dx = p2.x - p1.x;
    var dy = p2.y - p1.y;
    var dz = p2.z - p1.z;

    var distance = Math.sqrt(dx*dx + dy*dy + dz*dz);
    var horizontal_distance = Math.sqrt(dx*dx + dz*dz);

    // Horizontal angle: 0=+Z(front for Genesis), 90=+X(right), -90=-X(left), 180=back
    var angle_horizontal = Math.atan2(dx, dz) * 180 / Math.PI;
    // Vertical angle: positive=above node1, negative=below
    var angle_vertical = Math.atan2(dy, horizontal_distance) * 180 / Math.PI;

    // Direction label
    var absH = Math.abs(angle_horizontal);
    var hDir = "";
    if (absH < 22.5) hDir = "front";
    else if (absH < 67.5) hDir = angle_horizontal > 0 ? "front-right" : "front-left";
    else if (absH < 112.5) hDir = angle_horizontal > 0 ? "right" : "left";
    else if (absH < 157.5) hDir = angle_horizontal > 0 ? "back-right" : "back-left";
    else hDir = "back";

    var vDir = "";
    if (angle_vertical > 15) vDir = " above";
    else if (angle_vertical < -15) vDir = " below";

    // Bounding box overlap check
    var bb1 = n1.getWSBoundingBox();
    var bb2 = n2.getWSBoundingBox();
    var overlapping = (
        bb1.minX <= bb2.maxX && bb1.maxX >= bb2.minX &&
        bb1.minY <= bb2.maxY && bb1.maxY >= bb2.minY &&
        bb1.minZ <= bb2.maxZ && bb1.maxZ >= bb2.minZ
    );

    var n2Label = n2.getLabel();
    var n1Label = n1.getLabel();
    var relPos = n2Label + " is " + hDir + vDir + " of " + n1Label +
                 " (" + Math.round(distance) + " cm away)";

    return {
        node1: n1Label,
        node2: n2Label,
        distance: distance,
        direction: hDir + vDir,
        angle_horizontal: angle_horizontal,
        angle_vertical: angle_vertical,
        relative_position: relPos,
        overlapping: overlapping
    };
})()
"""

# args: {node1Label, node2Label}
# Returns: {node1, node2, overlapping, penetration_depth, suggestion}
_CHECK_OVERLAP_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var n1 = Scene.findNodeByLabel(args.node1Label);
    if (!n1) n1 = Scene.findNode(args.node1Label);
    if (!n1) throw new Error("Node not found: " + args.node1Label);

    var n2 = Scene.findNodeByLabel(args.node2Label);
    if (!n2) n2 = Scene.findNode(args.node2Label);
    if (!n2) throw new Error("Node not found: " + args.node2Label);

    var bb1 = n1.getWSBoundingBox();
    var bb2 = n2.getWSBoundingBox();

    var overlapX = Math.min(bb1.maxX, bb2.maxX) - Math.max(bb1.minX, bb2.minX);
    var overlapY = Math.min(bb1.maxY, bb2.maxY) - Math.max(bb1.minY, bb2.minY);
    var overlapZ = Math.min(bb1.maxZ, bb2.maxZ) - Math.max(bb1.minZ, bb2.minZ);

    var overlapping = overlapX > 0 && overlapY > 0 && overlapZ > 0;
    var penetration_depth = 0;
    var suggestion = "";

    if (overlapping) {
        // Penetration depth = minimum overlap axis
        penetration_depth = Math.min(overlapX, overlapY, overlapZ);

        // Suggest moving n2 along the axis of least penetration
        var p1 = n1.getWSPos();
        var p2 = n2.getWSPos();
        var dx = p2.x - p1.x;
        var dz = p2.z - p1.z;
        var moveAmount = Math.round(penetration_depth + 5);

        if (Math.abs(dx) >= Math.abs(dz)) {
            var dir = dx >= 0 ? "+" : "-";
            suggestion = "Move " + n2.getLabel() + " " + moveAmount +
                         " cm in " + dir + "X to resolve collision";
        } else {
            var dir2 = dz >= 0 ? "+" : "-";
            suggestion = "Move " + n2.getLabel() + " " + moveAmount +
                         " cm in " + dir2 + "Z to resolve collision";
        }
    }

    return {
        node1: n1.getLabel(),
        node2: n2.getLabel(),
        overlapping: overlapping,
        penetration_depth: penetration_depth,
        suggestion: suggestion
    };
})()
"""

# ---------------------------------------------------------------------------
# Phase 1: Property Introspection Scripts
# ---------------------------------------------------------------------------

# args: {nodeLabel, propertyType}
# propertyType: "all" | "numeric" | "transform" | "bool" | "string"
# Returns: {node, properties:[{label,name,type,value,min,max,path,is_animatable}], count}
_INSPECT_PROPERTIES_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var typeFilter = args.propertyType || "all";

    var TRANSFORM_NAMES = {
        "XTranslate": 1, "YTranslate": 1, "ZTranslate": 1,
        "XRotate": 1, "YRotate": 1, "ZRotate": 1,
        "Scale": 1, "XScale": 1, "YScale": 1, "ZScale": 1
    };

    var props = [];
    for (var i = 0; i < node.getNumProperties(); i++) {
        var prop = node.getProperty(i);
        var className = prop.className();
        var isNumeric = prop.inherits("DzNumericProperty");
        var isBool = className === "DzBoolProperty";
        var isTransform = TRANSFORM_NAMES[prop.getName()] === 1;
        var isString = className === "DzStringProperty";

        var include = false;
        if (typeFilter === "all") include = true;
        else if (typeFilter === "numeric" && isNumeric) include = true;
        else if (typeFilter === "transform" && isTransform) include = true;
        else if (typeFilter === "bool" && isBool) include = true;
        else if (typeFilter === "string" && isString) include = true;
        else if (typeFilter === "morph" && isNumeric && !isTransform) include = true;

        if (!include) continue;

        var entry = {
            label: prop.getLabel(),
            name: prop.getName(),
            type: className,
            path: prop.getPath ? prop.getPath() : "",
            is_animatable: prop.isAnimatable ? prop.isAnimatable() : false
        };

        if (isNumeric) {
            entry.value = prop.getValue();
            entry.min = prop.getMin ? prop.getMin() : null;
            entry.max = prop.getMax ? prop.getMax() : null;
        } else if (isString && prop.getValue) {
            entry.value = prop.getValue();
            entry.min = null;
            entry.max = null;
        } else {
            entry.value = null;
            entry.min = null;
            entry.max = null;
        }

        props.push(entry);
    }

    return { node: node.getLabel(), properties: props, count: props.length };
})()
"""

# args: {nodeLabel, propertyName}
# Returns: {label, name, type, current_value, default_value, min, max,
#           is_animatable, path}
_GET_PROPERTY_METADATA_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var prop = null;
    for (var i = 0; i < node.getNumProperties(); i++) {
        var p = node.getProperty(i);
        if (p.getLabel() === args.propertyName || p.getName() === args.propertyName) {
            prop = p; break;
        }
    }
    if (!prop) throw new Error("Property not found: " + args.propertyName +
                                " on " + args.nodeLabel);

    var isNumeric = prop.inherits("DzNumericProperty");

    return {
        label: prop.getLabel(),
        name: prop.getName(),
        type: prop.className(),
        current_value: isNumeric ? prop.getValue() : null,
        default_value: (isNumeric && prop.getDefaultValue) ? prop.getDefaultValue() : null,
        min: (isNumeric && prop.getMin) ? prop.getMin() : null,
        max: (isNumeric && prop.getMax) ? prop.getMax() : null,
        is_animatable: prop.isAnimatable ? prop.isAnimatable() : false,
        path: prop.getPath ? prop.getPath() : "",
        node: node.getLabel()
    };
})()
"""

# ---------------------------------------------------------------------------
# Phase 1: Lighting Preset Script
# ---------------------------------------------------------------------------

# args: {preset, subjectLabel}
# preset: "three-point" | "rembrandt" | "butterfly" | "split" | "loop"
# Returns: {preset, subject, lights_created:[{label,type,position}], environment_mode}
# Creates lights relative to subject bounding box center.
# Genesis figures face +Z so "front" = positive Z side.
_APPLY_LIGHTING_PRESET_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var preset = args.preset || "three-point";
    var subjectLabel = args.subjectLabel;

    // Get subject center if provided
    var subjectCenter = { x: 0, y: 150, z: 0 };
    var subjectHeight = 170;
    if (subjectLabel) {
        var subjectNode = Scene.findNodeByLabel(subjectLabel);
        if (!subjectNode) subjectNode = Scene.findNode(subjectLabel);
        if (subjectNode) {
            var bbox = subjectNode.getWSBoundingBox();
            subjectCenter = {
                x: (bbox.minX + bbox.maxX) / 2,
                y: (bbox.minY + bbox.maxY) / 2,
                z: (bbox.minZ + bbox.maxZ) / 2
            };
            subjectHeight = bbox.maxY - bbox.minY;
        }
    }

    var faceHeight = subjectCenter.y + subjectHeight * 0.2;  // ~head height
    var R = subjectHeight * 1.2;  // light orbit radius

    // Lighting configurations: [label, flux, azimuthDeg, elevDeg, lightClass, shadowSoftness]
    // azimuth: 0=front(+Z), 90=right(+X), 180=back, -90=left
    var configs = {
        "three-point": [
            ["Key Light",  2000, 45,   35,  "DzSpotLight", 30],
            ["Fill Light",  800, -45,  20,  "DzSpotLight", 60],
            ["Rim Light",  1200, 180,  45,  "DzDistantLight", 20]
        ],
        "rembrandt": [
            ["Key Light",  2200, 45,   45,  "DzSpotLight", 20],
            ["Fill Light",  400, -90,  10,  "DzSpotLight", 80]
        ],
        "butterfly": [
            ["Key Light",  2000,  0,   45,  "DzSpotLight", 25],
            ["Fill Light",  500,  0,   -5,  "DzSpotLight", 80]
        ],
        "split": [
            ["Key Light",  2200, 90,   15,  "DzSpotLight", 15],
            ["Rim Light",   800, -90,  20,  "DzSpotLight", 40]
        ],
        "loop": [
            ["Key Light",  2000, 35,   30,  "DzSpotLight", 35],
            ["Fill Light",  700, -50,  15,  "DzSpotLight", 70],
            ["Rim Light",   900, 160,  40,  "DzSpotLight", 25]
        ]
    };

    var lightDefs = configs[preset];
    if (!lightDefs) throw new Error("Unknown preset: " + preset +
        ". Valid: three-point, rembrandt, butterfly, split, loop");

    // Remove existing preset lights with same names to avoid duplicates
    var existingLabels = {};
    for (var d = 0; d < lightDefs.length; d++) {
        existingLabels[lightDefs[d][0]] = 1;
    }
    for (var ni = 0; ni < Scene.getNumLights(); ni++) {
        var existingLight = Scene.getLight(ni);
        if (existingLabels[existingLight.getLabel()]) {
            Scene.removeNode(existingLight);
            ni--;
        }
    }

    var created = [];

    for (var i = 0; i < lightDefs.length; i++) {
        var def = lightDefs[i];
        var label     = def[0];
        var flux      = def[1];
        var azimuthDeg = def[2];
        var elevDeg   = def[3];
        var lightClass = def[4];
        var softness  = def[5];

        var azRad = azimuthDeg * Math.PI / 180;
        var elRad = elevDeg * Math.PI / 180;

        var lx = subjectCenter.x + R * Math.sin(azRad) * Math.cos(elRad);
        var ly = subjectCenter.y + R * Math.sin(elRad) + subjectHeight * 0.1;
        var lz = subjectCenter.z + R * Math.cos(azRad) * Math.cos(elRad);

        var light = null;
        if (lightClass === "DzSpotLight") {
            light = new DzSpotLight();
        } else {
            light = new DzDistantLight();
        }

        Scene.addNode(light);
        light.setLabel(label);

        var fluxProp = light.findProperty("Flux");
        if (fluxProp) fluxProp.setValue(flux);

        var softProp = light.findProperty("Shadow Softness");
        if (softProp) softProp.setValue(softness);

        var xtp = light.findProperty("XTranslate");
        var ytp = light.findProperty("YTranslate");
        var ztp = light.findProperty("ZTranslate");
        if (xtp) xtp.setValue(lx);
        if (ytp) ytp.setValue(ly);
        if (ztp) ztp.setValue(lz);

        light.aimAt(new DzVec3(subjectCenter.x, faceHeight, subjectCenter.z));

        created.push({
            label: label,
            type: lightClass,
            position: { x: Math.round(lx), y: Math.round(ly), z: Math.round(lz) },
            flux: flux
        });
    }

    // Set environment to scene-lights-only
    var envNode = Scene.getNode(1);
    if (envNode) {
        var envMode = envNode.findProperty("Environment Mode");
        if (envMode) envMode.setValue(3);
    }

    return {
        preset: preset,
        subject: subjectLabel || null,
        lights_created: created,
        environment_mode: "Scene Only (3)"
    };
})()
"""

# ---------------------------------------------------------------------------
# Phase 1: Scene Validation Script
# ---------------------------------------------------------------------------

# args: none
# Returns: {valid, issues:[{type,severity,nodes,description,suggestion}],
#           warnings:[...], score, score_breakdown}
_VALIDATE_SCENE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var issues = [];
    var warnings = [];

    // --- 1. Collision detection between figures (bounding box AABB) ---
    var figures = [];
    for (var i = 0; i < Scene.getNumSkeletons(); i++) {
        var skel = Scene.getSkeleton(i);
        var bb = skel.getWSBoundingBox();
        figures.push({ label: skel.getLabel(), bb: bb });
    }

    for (var a = 0; a < figures.length; a++) {
        for (var b = a + 1; b < figures.length; b++) {
            var f1 = figures[a];
            var f2 = figures[b];
            var overlapX = Math.min(f1.bb.maxX, f2.bb.maxX) - Math.max(f1.bb.minX, f2.bb.minX);
            var overlapY = Math.min(f1.bb.maxY, f2.bb.maxY) - Math.max(f1.bb.minY, f2.bb.minY);
            var overlapZ = Math.min(f1.bb.maxZ, f2.bb.maxZ) - Math.max(f1.bb.minZ, f2.bb.minZ);

            if (overlapX > 0 && overlapY > 0 && overlapZ > 0) {
                var depth = Math.round(Math.min(overlapX, overlapY, overlapZ));
                issues.push({
                    type: "collision",
                    severity: "high",
                    nodes: [f1.label, f2.label],
                    description: f1.label + " and " + f2.label +
                                 " bounding boxes overlap by ~" + depth + " cm",
                    suggestion: "Move one character away to resolve interpenetration"
                });
            }
        }
    }

    // --- 2. Lighting checks ---
    var numLights = Scene.getNumLights();
    var envNode = Scene.getNode(1);
    var envMode = envNode ? envNode.findProperty("Environment Mode") : null;
    var envModeVal = envMode ? envMode.getValue() : 0;
    var hasEnvLight = (envModeVal !== 3);  // not scene-only → env dome contributes

    if (numLights === 0 && !hasEnvLight) {
        issues.push({
            type: "no-lights",
            severity: "high",
            nodes: [],
            description: "Scene has no lights and environment lighting is disabled",
            suggestion: "Use daz_apply_lighting_preset('three-point') to add lights"
        });
    } else if (numLights === 1) {
        warnings.push({
            type: "poor-lighting",
            severity: "medium",
            description: "Scene has only one light source, may cause harsh shadows",
            suggestion: "Add a fill light at low intensity to soften shadows"
        });
    }

    // --- 3. Camera framing check ---
    var numCameras = Scene.getNumCameras();
    if (numCameras === 0) {
        warnings.push({
            type: "no-camera",
            severity: "medium",
            description: "Scene has no cameras (will use default perspective view)",
            suggestion: "Add a camera with daz_execute('var c = new DzBasicCamera(); Scene.addNode(c);')"
        });
    }

    // --- 4. Empty scene check ---
    var numFigures = Scene.getNumSkeletons();
    if (numFigures === 0) {
        warnings.push({
            type: "no-figures",
            severity: "low",
            description: "Scene has no figures/characters",
            suggestion: "Load a character with daz_load_file()"
        });
    }

    // --- Score calculation ---
    var lightScore = 100;
    if (numLights === 0 && !hasEnvLight) lightScore = 0;
    else if (numLights === 1) lightScore = 50;

    var collisionScore = issues.filter(function(i){ return i.type === "collision"; }).length === 0 ? 100 : 30;
    var cameraScore = numCameras > 0 ? 100 : 60;
    var figureScore = numFigures > 0 ? 100 : 60;

    var score = Math.round((lightScore + collisionScore + cameraScore + figureScore) / 4);

    return {
        valid: issues.length === 0,
        issues: issues,
        warnings: warnings,
        score: score,
        score_breakdown: {
            lighting: lightScore,
            collision: collisionScore,
            camera: cameraScore,
            figures: figureScore
        },
        summary: {
            figures: numFigures,
            cameras: numCameras,
            lights: numLights,
            environment_lighting: hasEnvLight
        }
    };
})()
"""

# args: {preset, maxSamples, renderQuality}
# Returns: {preset, propertiesSet: [{property, value}], note}
# Sets Iray render quality via Max Samples and Render Quality properties on the
# active renderer options.  Falls back gracefully if properties are not found.
_SET_RENDER_QUALITY_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var renderMgr = App.getRenderMgr();
    if (!renderMgr) throw "No render manager available";

    // getOptionHelper() returns a DzElement (renderer's option node) which has findProperty
    var optHelper = renderMgr.getOptionHelper ? renderMgr.getOptionHelper() : null;

    var targets = ["Max Samples", "Render Quality"];
    var targetValues = {"Max Samples": args.maxSamples, "Render Quality": args.renderQuality};

    var propertiesSet = [];
    var notFound = [];

    for (var i = 0; i < targets.length; i++) {
        var name = targets[i];
        var prop = optHelper ? optHelper.findProperty(name) : null;
        if (prop) {
            prop.setValue(targetValues[name]);
            propertiesSet.push({property: name, value: prop.getValue()});
        } else {
            notFound.push(name);
        }
    }

    var result = {preset: args.preset, propertiesSet: propertiesSet};
    if (notFound.length > 0) {
        result.note = "Properties not found on active renderer option helper: " + notFound.join(", ");
    }
    return result;
})()
"""

# ---------------------------------------------------------------------------
# Phase 2 script constants
# ---------------------------------------------------------------------------

_SET_EMOTION_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var node = Scene.findNodeByLabel(args.nodeLabel);
    if (!node) node = Scene.findNode(args.nodeLabel);
    if (!node) throw new Error("Node not found: " + args.nodeLabel);

    var intensity = args.intensity || 0.7;
    var applied = [];
    var notFound = [];

    // Apply morph candidates — each entry: {names: [...], value: float}
    var morphList = args.morphList || [];
    for (var i = 0; i < morphList.length; i++) {
        var entry = morphList[i];
        var targetValue = entry.value * intensity;
        var found = false;
        for (var j = 0; j < entry.names.length; j++) {
            var prop = node.findProperty(entry.names[j]);
            if (prop && prop.inherits("DzNumericProperty")) {
                prop.setValue(targetValue);
                applied.push({morph: entry.names[j], value: prop.getValue()});
                found = true;
                break;
            }
        }
        if (!found) notFound.push(entry.names[0] || "unknown");
    }

    // Apply body adjustments (bone rotations)
    var bodyApplied = [];
    var bodyAdjustments = args.bodyAdjustments || [];
    for (var k = 0; k < bodyAdjustments.length; k++) {
        var adj = bodyAdjustments[k];
        // Try to find the bone as a child of the figure
        var bone = null;
        for (var b = 0; b < node.getNumNodeChildren(); b++) {
            var child = node.getNodeChild(b);
            if (child && (child.getLabel() === adj.bone || child.getName() === adj.bone)) {
                bone = child;
                break;
            }
        }
        if (!bone) bone = Scene.findNodeByLabel(adj.bone);
        if (bone) {
            var boneProp = bone.findProperty(adj.property);
            if (boneProp) {
                boneProp.setValue(adj.value * intensity);
                bodyApplied.push({bone: adj.bone, property: adj.property, value: boneProp.getValue()});
            }
        }
    }

    return {
        character: node.getLabel(),
        emotion: args.emotion,
        intensity: intensity,
        applied_morphs: applied,
        body_adjustments: bodyApplied,
        not_found: notFound
    };
})()
"""

_LIST_CATEGORIES_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var contentMgr = App.getContentMgr();
    var parentPath = (args.parentPath || "").replace(/^\\/|\\/$/g, "");
    var categories = [];
    var seen = {};

    for (var i = 0; i < contentMgr.getNumContentDirectories(); i++) {
        var dir = contentMgr.getContentDirectory(i);
        if (!dir) continue;
        var basePath = dir.fullPath;
        var searchPath = parentPath ? basePath + "/" + parentPath : basePath;
        var d = new DzDir(searchPath);
        if (!d.exists()) continue;

        var subdirs = d.entryList([], DzDir.Dirs | DzDir.NoDotAndDotDot);
        for (var j = 0; j < subdirs.length; j++) {
            var name = subdirs[j];
            if (seen[name]) continue;
            seen[name] = true;
            var subdir = new DzDir(d.absoluteFilePath(name));
            var dufFiles = subdir.entryList(["*.duf"], DzDir.Files);
            categories.push({
                name: name,
                path: parentPath ? parentPath + "/" + name : name,
                duf_count: dufFiles.length
            });
        }
    }

    categories.sort(function(a, b) { return a.name < b.name ? -1 : a.name > b.name ? 1 : 0; });
    return {parent: args.parentPath || "/", categories: categories, count: categories.length};
})()
"""

_BROWSE_CATEGORY_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var contentMgr = App.getContentMgr();
    var categoryPath = (args.categoryPath || "").replace(/^\\/|\\/$/g, "");
    var items = [];
    var seen = {};

    for (var i = 0; i < contentMgr.getNumContentDirectories(); i++) {
        var dir = contentMgr.getContentDirectory(i);
        if (!dir) continue;
        var basePath = dir.fullPath;
        var searchPath = categoryPath ? basePath + "/" + categoryPath : basePath;
        var d = new DzDir(searchPath);
        if (!d.exists()) continue;

        var files = d.entryList(["*.duf"], DzDir.Files);
        for (var j = 0; j < files.length; j++) {
            var fname = files[j];
            if (seen[fname]) continue;
            seen[fname] = true;
            items.push({
                name: fname.replace(/\\.duf$/i, ""),
                filename: fname,
                full_path: searchPath + "/" + fname
            });
        }
    }

    items.sort(function(a, b) { return a.name < b.name ? -1 : a.name > b.name ? 1 : 0; });
    return {category: args.categoryPath || "/", items: items, count: items.length};
})()
"""

_APPLY_COMPOSITION_RULE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cam = Scene.findNodeByLabel(args.cameraLabel);
    if (!cam) throw new Error("Camera not found: " + args.cameraLabel);

    var subject = Scene.findNodeByLabel(args.subjectLabel);
    if (!subject) subject = Scene.findNode(args.subjectLabel);
    if (!subject) throw new Error("Subject not found: " + args.subjectLabel);

    var rule = args.rule || "rule-of-thirds";

    var bbox = subject.getWSBoundingBox();
    var subCenter = bbox ? {
        x: (bbox.minX + bbox.maxX) / 2,
        y: (bbox.minY + bbox.maxY) / 2,
        z: (bbox.minZ + bbox.maxZ) / 2
    } : {x: 0, y: 85, z: 0};
    var subHeight = bbox ? bbox.maxY - bbox.minY : 170;

    // Determine working distance (maintain current or use default)
    var camPos = cam.getWSPos();
    var dx = camPos.x - subCenter.x;
    var dz = camPos.z - subCenter.z;
    var hDist = Math.sqrt(dx*dx + dz*dz);
    if (hDist < 50) hDist = 250;

    var camX, camY, camZ, aimY, explanation;

    if (rule === "rule-of-thirds") {
        camX = subCenter.x - hDist * 0.3;
        camY = subCenter.y + subHeight * 0.1;
        camZ = subCenter.z + hDist;
        aimY = subHeight * 0.85;
        explanation = "Subject on right vertical third at eye level";
    } else if (rule === "golden-ratio") {
        camX = subCenter.x - hDist * 0.236;
        camY = subCenter.y + subHeight * 0.118;
        camZ = subCenter.z + hDist;
        aimY = subHeight * 0.85;
        explanation = "Subject at golden ratio intersection (1.618 proportion)";
    } else if (rule === "center-frame") {
        camX = subCenter.x;
        camY = subCenter.y + subHeight * 0.1;
        camZ = subCenter.z + hDist;
        aimY = subHeight * 0.85;
        explanation = "Subject centered in frame";
    } else if (rule === "leading-lines") {
        camX = subCenter.x + hDist * 0.2;
        camY = Math.max(5, subCenter.y - subHeight * 0.05);
        camZ = subCenter.z + hDist * 0.85;
        aimY = subHeight * 0.9;
        explanation = "Low-angle with horizontal offset creating diagonal leading lines";
    } else {
        throw new Error("Unknown rule: " + rule + ". Valid: rule-of-thirds, golden-ratio, center-frame, leading-lines");
    }

    var xp = cam.findProperty("XTranslate");
    var yp = cam.findProperty("YTranslate");
    var zp = cam.findProperty("ZTranslate");
    if (xp) xp.setValue(camX);
    if (yp) yp.setValue(camY);
    if (zp) zp.setValue(camZ);
    cam.aimAt(new DzVec3(subCenter.x, aimY, subCenter.z));

    return {
        camera: cam.getLabel(),
        subject: subject.getLabel(),
        rule: rule,
        camera_position: {x: Math.round(camX*10)/10, y: Math.round(camY*10)/10, z: Math.round(camZ*10)/10},
        explanation: explanation
    };
})()
"""

_FRAME_SHOT_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cam = Scene.findNodeByLabel(args.cameraLabel);
    if (!cam) throw new Error("Camera not found: " + args.cameraLabel);

    var subject = Scene.findNodeByLabel(args.subjectLabel);
    if (!subject) subject = Scene.findNode(args.subjectLabel);
    if (!subject) throw new Error("Subject not found: " + args.subjectLabel);

    var shotType = args.shotType || "medium-shot";

    var bbox = subject.getWSBoundingBox();
    var subHeight = bbox ? bbox.maxY - bbox.minY : 170;
    var subBottom = bbox ? bbox.minY : 0;
    var subCenterX = bbox ? (bbox.minX + bbox.maxX) / 2 : 0;
    var subCenterZ = bbox ? (bbox.minZ + bbox.maxZ) / 2 : 0;

    // {dist, camHeightFrac relative to bottom, aimHeightFrac, framing description}
    var shots = {
        "extreme-close-up": {dist: 25,  camH: 0.95, aimH: 0.95, framing: "eyes and mouth detail"},
        "close-up":          {dist: 50,  camH: 0.93, aimH: 0.93, framing: "face and head"},
        "medium-close-up":   {dist: 90,  camH: 0.90, aimH: 0.90, framing: "head and shoulders"},
        "medium-shot":       {dist: 140, camH: 0.82, aimH: 0.80, framing: "waist up"},
        "medium-full":       {dist: 200, camH: 0.72, aimH: 0.70, framing: "knees up"},
        "full-shot":         {dist: 400, camH: 0.60, aimH: 0.55, framing: "entire body with breathing room"},
        "wide-shot":         {dist: 700, camH: 0.55, aimH: 0.50, framing: "body within environment"}
    };

    if (!shots[shotType]) {
        throw new Error("Unknown shot type: " + shotType +
            ". Valid: extreme-close-up, close-up, medium-close-up, medium-shot, medium-full, full-shot, wide-shot");
    }

    var s = shots[shotType];
    var camHeight = subBottom + subHeight * s.camH;
    var aimHeight = subBottom + subHeight * s.aimH;

    var xp = cam.findProperty("XTranslate");
    var yp = cam.findProperty("YTranslate");
    var zp = cam.findProperty("ZTranslate");
    if (xp) xp.setValue(subCenterX);
    if (yp) yp.setValue(camHeight);
    if (zp) zp.setValue(subCenterZ + s.dist);
    cam.aimAt(new DzVec3(subCenterX, aimHeight, subCenterZ));

    return {
        camera: cam.getLabel(),
        subject: subject.getLabel(),
        shot_type: shotType,
        distance: s.dist,
        camera_height: Math.round(camHeight * 10) / 10,
        framing: s.framing
    };
})()
"""

_APPLY_CAMERA_ANGLE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cam = Scene.findNodeByLabel(args.cameraLabel);
    if (!cam) throw new Error("Camera not found: " + args.cameraLabel);

    var subject = Scene.findNodeByLabel(args.subjectLabel);
    if (!subject) subject = Scene.findNode(args.subjectLabel);
    if (!subject) throw new Error("Subject not found: " + args.subjectLabel);

    var angle = args.angle || "eye-level";

    var bbox = subject.getWSBoundingBox();
    var subHeight = bbox ? bbox.maxY - bbox.minY : 170;
    var subBottom = bbox ? bbox.minY : 0;
    var subCenterX = bbox ? (bbox.minX + bbox.maxX) / 2 : 0;
    var subCenterZ = bbox ? (bbox.minZ + bbox.maxZ) / 2 : 0;
    var eyeHeight = subBottom + subHeight * 0.93;

    // Maintain current horizontal camera distance from subject
    var camPos = cam.getWSPos();
    var dx = camPos.x - subCenterX;
    var dz = camPos.z - subCenterZ;
    var hDist = Math.sqrt(dx * dx + dz * dz);
    if (hDist < 50) hDist = 250;
    var normX = dx / hDist;
    var normZ = dz / hDist;

    var camX = subCenterX + normX * hDist;
    var camZ = subCenterZ + normZ * hDist;
    var camY, aimY, note;

    if (angle === "eye-level") {
        camY = eyeHeight;
        aimY = eyeHeight;
        note = "Camera at eye height — neutral perspective";
    } else if (angle === "high-angle") {
        camY = eyeHeight + subHeight * 0.5;
        aimY = subBottom + subHeight * 0.55;
        note = "Camera above subject — creates vulnerable or diminished feel";
    } else if (angle === "low-angle") {
        camY = subBottom + subHeight * 0.15;
        aimY = eyeHeight;
        note = "Camera below eye level — creates powerful or dominant feel";
    } else if (angle === "dutch-angle") {
        camY = eyeHeight;
        aimY = eyeHeight;
        var rollProp = cam.findProperty("ZRotate");
        if (rollProp) rollProp.setValue(15);
        note = "Camera tilted 15° (dutch angle) — creates unease or tension";
    } else if (angle === "overhead") {
        camX = subCenterX;
        camY = subBottom + subHeight * 1.8;
        camZ = subCenterZ;
        aimY = subBottom + subHeight * 0.5;
        note = "Bird's eye view directly overhead";
    } else if (angle === "worms-eye") {
        camY = subBottom + 5;
        aimY = eyeHeight;
        note = "Ground level looking up — extreme dramatic low angle";
    } else if (angle === "over-shoulder") {
        camX = subCenterX + hDist * 0.3;
        camY = eyeHeight;
        camZ = subCenterZ - hDist * 0.4;
        aimY = eyeHeight;
        note = "Over-the-shoulder perspective — classic conversation/reaction shot";
    } else {
        throw new Error("Unknown angle: " + angle +
            ". Valid: eye-level, high-angle, low-angle, dutch-angle, overhead, worms-eye, over-shoulder");
    }

    var xp = cam.findProperty("XTranslate");
    var yp = cam.findProperty("YTranslate");
    var zp = cam.findProperty("ZTranslate");
    if (xp) xp.setValue(camX);
    if (yp) yp.setValue(camY);
    if (zp) zp.setValue(camZ);
    cam.aimAt(new DzVec3(subCenterX, aimY !== undefined ? aimY : eyeHeight, subCenterZ));

    return {
        camera: cam.getLabel(),
        subject: subject.getLabel(),
        angle: angle,
        camera_position: {x: Math.round(camX*10)/10, y: Math.round(camY*10)/10, z: Math.round(camZ*10)/10},
        note: note
    };
})()
"""

_SAVE_SCENE_STATE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodes = [];
    var transformKeys = ["XTranslate", "YTranslate", "ZTranslate", "XRotate", "YRotate", "ZRotate", "Scale"];
    var transformSet = {XTranslate:1, YTranslate:1, ZTranslate:1,
                        XRotate:1, YRotate:1, ZRotate:1,
                        Scale:1, XScale:1, YScale:1, ZScale:1};

    function captureTransforms(node) {
        var t = {};
        for (var i = 0; i < transformKeys.length; i++) {
            var p = node.findProperty(transformKeys[i]);
            if (p) t[transformKeys[i]] = p.getValue();
        }
        return t;
    }

    // Skeletons / figures
    for (var i = 0; i < Scene.getNumSkeletons(); i++) {
        var skel = Scene.getSkeleton(i);
        var morphs = [];
        for (var p = 0; p < skel.getNumProperties(); p++) {
            var mp = skel.getProperty(p);
            if (mp.inherits("DzFloatProperty") && !transformSet[mp.getName()]) {
                var v = mp.getValue();
                if (v !== 0) morphs.push({name: mp.getName(), value: v});
            }
        }
        nodes.push({label: skel.getLabel(), type: "skeleton",
                    transforms: captureTransforms(skel), active_morphs: morphs, extra: {}});
    }

    // Cameras
    for (var ci = 0; ci < Scene.getNumCameras(); ci++) {
        var cam = Scene.getCamera(ci);
        nodes.push({label: cam.getLabel(), type: "camera",
                    transforms: captureTransforms(cam), active_morphs: [], extra: {}});
    }

    // Lights
    for (var li = 0; li < Scene.getNumLights(); li++) {
        var light = Scene.getLight(li);
        var extra = {};
        var lightProps = ["Flux", "Shadow Softness", "Spread Angle"];
        for (var lk = 0; lk < lightProps.length; lk++) {
            var lp = light.findProperty(lightProps[lk]);
            if (lp) extra[lightProps[lk]] = lp.getValue();
        }
        nodes.push({label: light.getLabel(), type: "light",
                    transforms: captureTransforms(light), active_morphs: [], extra: extra});
    }

    return {checkpoint: args.checkpointName, nodes: nodes, node_count: nodes.length};
})()
"""

_RESTORE_SCENE_STATE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var nodes = args.nodes || [];
    var restored = [];
    var errors = [];

    for (var i = 0; i < nodes.length; i++) {
        var nd = nodes[i];
        var node = Scene.findNodeByLabel(nd.label);
        if (!node) { errors.push("Node not found: " + nd.label); continue; }

        // Restore transforms
        var transforms = nd.transforms || {};
        for (var key in transforms) {
            var prop = node.findProperty(key);
            if (prop) prop.setValue(transforms[key]);
        }

        // Restore active morphs
        var morphs = nd.active_morphs || [];
        for (var m = 0; m < morphs.length; m++) {
            var mp = node.findProperty(morphs[m].name);
            if (mp) mp.setValue(morphs[m].value);
        }

        // Restore extra properties (lights)
        var extra = nd.extra || {};
        for (var ek in extra) {
            var ep = node.findProperty(ek);
            if (ep) ep.setValue(extra[ek]);
        }

        restored.push(nd.label);
    }

    return {checkpoint: args.checkpointName, restored: restored, errors: errors};
})()
"""

_GET_SCENE_LAYOUT_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var includeTypes = args.includeTypes || ["figures", "cameras", "lights", "props"];
    var incl = {};
    for (var t = 0; t < includeTypes.length; t++) incl[includeTypes[t]] = true;

    var nodeList = [];

    function bboxData(node) {
        var bb = node.getWSBoundingBox();
        if (!bb) return null;
        return {
            width:  Math.round((bb.maxX - bb.minX) * 10) / 10,
            height: Math.round((bb.maxY - bb.minY) * 10) / 10,
            depth:  Math.round((bb.maxZ - bb.minZ) * 10) / 10,
            center: {
                x: Math.round((bb.minX + bb.maxX) / 2 * 10) / 10,
                y: Math.round((bb.minY + bb.maxY) / 2 * 10) / 10,
                z: Math.round((bb.minZ + bb.maxZ) / 2 * 10) / 10
            }
        };
    }

    function posData(node) {
        var p = node.getWSPos();
        return {x: Math.round(p.x*10)/10, y: Math.round(p.y*10)/10, z: Math.round(p.z*10)/10};
    }

    if (incl["figures"]) {
        for (var i = 0; i < Scene.getNumSkeletons(); i++) {
            var s = Scene.getSkeleton(i);
            var e = {label: s.getLabel(), type: "figure", position: posData(s)};
            var bb = bboxData(s);
            if (bb) e.bounds = bb;
            nodeList.push(e);
        }
    }

    if (incl["cameras"]) {
        for (var ci = 0; ci < Scene.getNumCameras(); ci++) {
            var c = Scene.getCamera(ci);
            nodeList.push({label: c.getLabel(), type: "camera", position: posData(c)});
        }
    }

    if (incl["lights"]) {
        for (var li = 0; li < Scene.getNumLights(); li++) {
            var l = Scene.getLight(li);
            var le = {label: l.getLabel(), type: "light", position: posData(l), nodeClass: l.className()};
            var fp = l.findProperty("Flux");
            if (fp) le.flux = fp.getValue();
            nodeList.push(le);
        }
    }

    if (incl["props"]) {
        // Enumerate non-skeleton/camera/light nodes (skip root [0] and env [1])
        var skelLabels = {};
        for (var si = 0; si < Scene.getNumSkeletons(); si++) skelLabels[Scene.getSkeleton(si).getLabel()] = true;

        for (var ni = 2; ni < Scene.getNumNodes(); ni++) {
            var n = Scene.getNode(ni);
            if (!n) continue;
            var cls = n.className();
            if (cls.indexOf("Camera") >= 0 || cls.indexOf("Light") >= 0) continue;
            if (cls.indexOf("Skeleton") >= 0 || cls.indexOf("Figure") >= 0) continue;
            if (skelLabels[n.getLabel()]) continue;
            // Skip bones (parent is a skeleton)
            var parent = n.getNodeParent();
            if (parent) {
                var pcls = parent.className();
                if (pcls.indexOf("Skeleton") >= 0 || pcls.indexOf("Figure") >= 0) continue;
            }
            var pe = {label: n.getLabel(), type: "prop", position: posData(n)};
            var pbb = bboxData(n);
            if (pbb) pe.bounds = pbb;
            nodeList.push(pe);
        }
    }

    return {nodes: nodeList, count: nodeList.length, include_types: includeTypes};
})()
"""

_FIND_NEARBY_NODES_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var center = Scene.findNodeByLabel(args.nodeLabel);
    if (!center) center = Scene.findNode(args.nodeLabel);
    if (!center) throw new Error("Node not found: " + args.nodeLabel);

    var radius = args.radius || 100;
    var includeTypes = args.includeTypes || null;
    var cp = center.getWSPos();

    var nearby = [];

    for (var i = 0; i < Scene.getNumNodes(); i++) {
        var n = Scene.getNode(i);
        if (!n || n.elementID === center.elementID) continue;

        var np = n.getWSPos();
        var dx = np.x - cp.x;
        var dy = np.y - cp.y;
        var dz = np.z - cp.z;
        var dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
        if (dist > radius) continue;

        var cls = n.className();
        var nodeType = "prop";
        if (cls.indexOf("Camera") >= 0) nodeType = "camera";
        else if (cls.indexOf("Light") >= 0) nodeType = "light";
        else if (cls.indexOf("Skeleton") >= 0 || cls.indexOf("Figure") >= 0) nodeType = "figure";

        if (includeTypes && includeTypes.indexOf(nodeType) < 0) continue;

        var hAngle = Math.atan2(dx, dz) * 180 / Math.PI;
        var dir;
        if      (hAngle > -22.5  && hAngle <=  22.5)  dir = "front";
        else if (hAngle >  22.5  && hAngle <=  67.5)  dir = "front-right";
        else if (hAngle >  67.5  && hAngle <= 112.5)  dir = "right";
        else if (hAngle > 112.5  && hAngle <= 157.5)  dir = "back-right";
        else if (hAngle >  157.5 || hAngle <= -157.5) dir = "back";
        else if (hAngle > -157.5 && hAngle <= -112.5) dir = "back-left";
        else if (hAngle > -112.5 && hAngle <=  -67.5) dir = "left";
        else                                            dir = "front-left";

        nearby.push({
            label: n.getLabel(),
            type: nodeType,
            distance: Math.round(dist * 10) / 10,
            direction: dir
        });
    }

    nearby.sort(function(a, b) { return a.distance - b.distance; });
    return {center_node: center.getLabel(), radius: radius, nearby_nodes: nearby, count: nearby.length};
})()
"""

# args: {sequenceType, characters: [], duration, fps}
# sequenceType: "establishing-medium-closeup", "shot-reverse-shot", "orbit", "push-in", "walkthrough"
# Returns: {cameras: [{label, position, frameRange}], totalFrames, sequenceType}
# Creates multiple cameras and sets up keyframes for cinematic sequences
_CREATE_SHOT_SEQUENCE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var sequenceType = args.sequenceType;
    var characters = args.characters || [];
    var duration = args.duration || 120;
    var fps = args.fps || 30;

    if (characters.length === 0) {
        throw new Error("At least one character required for shot sequence");
    }

    // Get primary subject
    var subject = Scene.findNodeByLabel(characters[0]);
    if (!subject) subject = Scene.findNode(characters[0]);
    if (!subject) throw new Error("Subject not found: " + characters[0]);

    var bbox = subject.getBoundingBox();
    var subCenter = bbox.getCenter();
    var subHeight = bbox.max.y - bbox.min.y;
    var eyeHeight = bbox.min.y + subHeight * 0.85;

    var cameras = [];
    var totalFrames = duration;

    // Helper: Create camera
    function createCamera(label, x, y, z, aimX, aimY, aimZ) {
        var cam = new DzBasicCamera();
        cam.setLabel(label);
        Scene.addNode(cam);
        var xp = cam.findProperty("XTranslate");
        var yp = cam.findProperty("YTranslate");
        var zp = cam.findProperty("ZTranslate");
        if (xp) xp.setValue(x);
        if (yp) yp.setValue(y);
        if (zp) zp.setValue(z);
        cam.aimAt(new DzVec3(aimX, aimY, aimZ));
        return cam;
    }

    // Helper: Set keyframe
    function setKeyframe(node, propName, frame, value) {
        var prop = node.findProperty(propName);
        if (!prop) return;
        var anim = prop.getAnimation();
        if (!anim) {
            anim = prop.createAnimation();
        }
        var key = anim.getKey(frame);
        if (!key) {
            key = anim.addKey(frame);
        }
        key.value = value;
    }

    if (sequenceType === "establishing-medium-closeup") {
        // Three cameras: wide → medium → close-up
        var framesPerShot = Math.floor(duration / 3);

        // Wide shot
        var cam1 = createCamera("Wide Shot", subCenter.x, eyeHeight, subCenter.z + 700,
                                subCenter.x, eyeHeight, subCenter.z);
        cameras.push({
            label: cam1.getLabel(),
            position: {x: subCenter.x, y: eyeHeight, z: subCenter.z + 700},
            frameRange: {start: 0, end: framesPerShot - 1}
        });

        // Medium shot
        var cam2 = createCamera("Medium Shot", subCenter.x, eyeHeight, subCenter.z + 200,
                                subCenter.x, eyeHeight, subCenter.z);
        cameras.push({
            label: cam2.getLabel(),
            position: {x: subCenter.x, y: eyeHeight, z: subCenter.z + 200},
            frameRange: {start: framesPerShot, end: framesPerShot * 2 - 1}
        });

        // Close-up
        var cam3 = createCamera("Close-up Shot", subCenter.x, eyeHeight, subCenter.z + 50,
                                subCenter.x, eyeHeight, subCenter.z);
        cameras.push({
            label: cam3.getLabel(),
            position: {x: subCenter.x, y: eyeHeight, z: subCenter.z + 50},
            frameRange: {start: framesPerShot * 2, end: duration - 1}
        });

    } else if (sequenceType === "shot-reverse-shot") {
        // Two cameras for conversation
        if (characters.length < 2) {
            throw new Error("shot-reverse-shot requires 2 characters");
        }

        var char2 = Scene.findNodeByLabel(characters[1]);
        if (!char2) char2 = Scene.findNode(characters[1]);
        if (!char2) throw new Error("Second character not found: " + characters[1]);

        var bbox2 = char2.getBoundingBox();
        var char2Center = bbox2.getCenter();
        var char2Eye = bbox2.min.y + (bbox2.max.y - bbox2.min.y) * 0.85;

        // Over-shoulder from char1 looking at char2
        var cam1 = createCamera("Over Shoulder 1",
                                subCenter.x - 50, eyeHeight - 10, subCenter.z - 60,
                                char2Center.x, char2Eye, char2Center.z);
        cameras.push({
            label: cam1.getLabel(),
            position: {x: subCenter.x - 50, y: eyeHeight - 10, z: subCenter.z - 60},
            frameRange: {start: 0, end: Math.floor(duration / 2) - 1}
        });

        // Over-shoulder from char2 looking at char1
        var cam2 = createCamera("Over Shoulder 2",
                                char2Center.x + 50, char2Eye - 10, char2Center.z + 60,
                                subCenter.x, eyeHeight, subCenter.z);
        cameras.push({
            label: cam2.getLabel(),
            position: {x: char2Center.x + 50, y: char2Eye - 10, z: char2Center.z + 60},
            frameRange: {start: Math.floor(duration / 2), end: duration - 1}
        });

    } else if (sequenceType === "orbit") {
        // Single camera orbiting around subject
        var cam = createCamera("Orbit Camera", subCenter.x, eyeHeight, subCenter.z + 250,
                               subCenter.x, eyeHeight, subCenter.z);

        var radius = 250;
        var frames = [0, Math.floor(duration / 4), Math.floor(duration / 2),
                      Math.floor(duration * 3 / 4), duration - 1];
        var angles = [0, 90, 180, 270, 360];

        for (var i = 0; i < frames.length; i++) {
            var angle = angles[i] * Math.PI / 180;
            var x = subCenter.x + radius * Math.sin(angle);
            var z = subCenter.z + radius * Math.cos(angle);
            setKeyframe(cam, "XTranslate", frames[i], x);
            setKeyframe(cam, "ZTranslate", frames[i], z);
            setKeyframe(cam, "YTranslate", frames[i], eyeHeight);
        }

        cameras.push({
            label: cam.getLabel(),
            position: {x: subCenter.x, y: eyeHeight, z: subCenter.z + radius},
            frameRange: {start: 0, end: duration - 1},
            animated: true
        });

    } else if (sequenceType === "push-in") {
        // Single camera dollying toward subject (wide → close-up)
        var startZ = subCenter.z + 700;
        var endZ = subCenter.z + 50;

        var cam = createCamera("Push-in Camera", subCenter.x, eyeHeight, startZ,
                               subCenter.x, eyeHeight, subCenter.z);

        setKeyframe(cam, "ZTranslate", 0, startZ);
        setKeyframe(cam, "ZTranslate", duration - 1, endZ);
        setKeyframe(cam, "XTranslate", 0, subCenter.x);
        setKeyframe(cam, "XTranslate", duration - 1, subCenter.x);
        setKeyframe(cam, "YTranslate", 0, eyeHeight);
        setKeyframe(cam, "YTranslate", duration - 1, eyeHeight);

        cameras.push({
            label: cam.getLabel(),
            position: {x: subCenter.x, y: eyeHeight, z: startZ},
            frameRange: {start: 0, end: duration - 1},
            animated: true
        });

    } else {
        throw new Error("Unknown sequence type: " + sequenceType +
            ". Valid: establishing-medium-closeup, shot-reverse-shot, orbit, push-in");
    }

    return {
        cameras: cameras,
        totalFrames: totalFrames,
        sequenceType: sequenceType,
        subject: subject.getLabel()
    };
})()
"""

# args: {char1Label, char2Label, dialogueBeats: [{speaker, startFrame, endFrame, emotion, gesture?}]}
# Returns: {char1, char2, beatsApplied: [{beat, actions}], totalFrames}
# Choreograph animated conversation between two characters
_ANIMATE_CONVERSATION_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};

    // Helper: Find bone in figure hierarchy
    function findBone(fig, name) {
        function search(node) {
            if (node.getName() === name) return node;
            for (var i = 0; i < node.getNumNodeChildren(); i++) {
                var result = search(node.getNodeChild(i));
                if (result) return result;
            }
            return null;
        }
        return search(fig);
    }

    // Helper: Set keyframe
    function setKeyframe(node, propName, frame, value) {
        var prop = node.findProperty(propName);
        if (!prop) return false;
        var anim = prop.getAnimation();
        if (!anim) anim = prop.createAnimation();
        var key = anim.getKey(frame);
        if (!key) key = anim.addKey(frame);
        key.value = value;
        return true;
    }

    // Helper: Apply emotion morphs
    function applyEmotion(figure, emotion, intensity, frame) {
        var emotionMorphs = {
            happy: [
                {names: ["PHMSmile", "Smile"], value: 0.8},
                {names: ["PHMBrowsUp", "Brows Up"], value: 0.3},
                {names: ["PHMEyesClosedL", "Eyes Closed"], value: 0.15}
            ],
            sad: [
                {names: ["PHMMouthFrownL", "Mouth Frown"], value: 0.7},
                {names: ["PHMBrowsDown", "Brows Down"], value: 0.6},
                {names: ["PHMEyesClosedL", "Eyes Closed"], value: 0.25}
            ],
            angry: [
                {names: ["PHMBrowsDown", "Brows Down"], value: 0.9},
                {names: ["PHMMouthFrownL", "Mouth Frown"], value: 0.5},
                {names: ["PHMNoseWrinkleL", "Nose Wrinkle"], value: 0.4}
            ],
            surprised: [
                {names: ["PHMEyesWide", "Eyes Wide"], value: 0.85},
                {names: ["PHMBrowsUp", "Brows Up"], value: 0.8},
                {names: ["PHMMouthOpen", "Mouth Open"], value: 0.5}
            ],
            neutral: []
        };

        var morphList = emotionMorphs[emotion] || [];
        var applied = 0;

        for (var i = 0; i < morphList.length; i++) {
            var entry = morphList[i];
            var targetValue = entry.value * intensity;
            for (var j = 0; j < entry.names.length; j++) {
                var prop = figure.findProperty(entry.names[j]);
                if (prop && prop.inherits("DzNumericProperty")) {
                    setKeyframe(figure, entry.names[j], frame, targetValue);
                    applied++;
                    break;
                }
            }
        }
        return applied;
    }

    // Helper: Rotate bone to look at target
    function rotateBoneToward(bone, targetX, targetY, targetZ, intensity, frame) {
        var boneWS = bone.getWSPos();
        var dx = targetX - boneWS.x;
        var dy = targetY - boneWS.y;
        var dz = targetZ - boneWS.z;
        var hDist = Math.sqrt(dx*dx + dz*dz);

        var yaw = Math.atan2(dx, dz) * 180 / Math.PI;
        var pitch = Math.atan2(dy, hDist) * 180 / Math.PI;

        setKeyframe(bone, "YRotate", frame, yaw * intensity);
        setKeyframe(bone, "XRotate", frame, pitch * intensity * -1);
    }

    // Get characters
    var char1 = Scene.findNodeByLabel(args.char1Label);
    if (!char1) char1 = Scene.findNode(args.char1Label);
    if (!char1) throw new Error("Character 1 not found: " + args.char1Label);

    var char2 = Scene.findNodeByLabel(args.char2Label);
    if (!char2) char2 = Scene.findNode(args.char2Label);
    if (!char2) throw new Error("Character 2 not found: " + args.char2Label);

    // Get head positions for look-at targets
    var char1Head = findBone(char1, "head");
    var char2Head = findBone(char2, "head");

    var char1Pos = char1.getWSPos();
    var char2Pos = char2.getWSPos();
    var char1TargetY = char1Pos.y + 163; // Approx head height
    var char2TargetY = char2Pos.y + 163;

    if (char1Head) {
        var char1HeadPos = char1Head.getWSPos();
        char1TargetY = char1HeadPos.y;
    }
    if (char2Head) {
        var char2HeadPos = char2Head.getWSPos();
        char2TargetY = char2HeadPos.y;
    }

    var char1TargetX = char1Pos.x;
    var char1TargetZ = char1Pos.z;
    var char2TargetX = char2Pos.x;
    var char2TargetZ = char2Pos.z;

    // Process dialogue beats
    var dialogueBeats = args.dialogueBeats || [];
    var beatsApplied = [];
    var maxFrame = 0;

    for (var i = 0; i < dialogueBeats.length; i++) {
        var beat = dialogueBeats[i];
        var speaker = beat.speaker;
        var startFrame = beat.startFrame || 0;
        var endFrame = beat.endFrame || startFrame + 30;
        var emotion = beat.emotion || "neutral";
        var intensity = beat.intensity || 0.7;

        if (endFrame > maxFrame) maxFrame = endFrame;

        var actions = [];

        // Determine who's speaking and who's listening
        var speakerFig = (speaker === args.char1Label) ? char1 : char2;
        var listenerFig = (speaker === args.char1Label) ? char2 : char1;
        var listenerTargetX = (speaker === args.char1Label) ? char2TargetX : char1TargetX;
        var listenerTargetY = (speaker === args.char1Label) ? char2TargetY : char1TargetY;
        var listenerTargetZ = (speaker === args.char1Label) ? char2TargetZ : char1TargetZ;
        var speakerTargetX = (speaker === args.char1Label) ? char1TargetX : char2TargetX;
        var speakerTargetY = (speaker === args.char1Label) ? char1TargetY : char2TargetY;
        var speakerTargetZ = (speaker === args.char1Label) ? char1TargetZ : char2TargetZ;

        // Apply emotion to speaker at start of beat
        var morphsApplied = applyEmotion(speakerFig, emotion, intensity, startFrame);
        if (morphsApplied > 0) {
            actions.push("Applied " + emotion + " emotion (" + morphsApplied + " morphs)");
        }

        // Make listener look at speaker
        var listenerHead = findBone(listenerFig, "head");
        var listenerNeck = findBone(listenerFig, "neckLower");

        if (listenerHead) {
            rotateBoneToward(listenerHead, speakerTargetX, speakerTargetY, speakerTargetZ, 0.6, startFrame);
            rotateBoneToward(listenerHead, speakerTargetX, speakerTargetY, speakerTargetZ, 0.6, endFrame);
            actions.push("Listener looks at speaker");
        }
        if (listenerNeck) {
            rotateBoneToward(listenerNeck, speakerTargetX, speakerTargetY, speakerTargetZ, 0.3, startFrame);
            rotateBoneToward(listenerNeck, speakerTargetX, speakerTargetY, speakerTargetZ, 0.3, endFrame);
        }

        beatsApplied.push({
            beat: i + 1,
            speaker: speaker,
            frameRange: {start: startFrame, end: endFrame},
            emotion: emotion,
            actions: actions
        });
    }

    return {
        char1: char1.getLabel(),
        char2: char2.getLabel(),
        beatsApplied: beatsApplied,
        totalFrames: maxFrame,
        beatCount: dialogueBeats.length
    };
})()
"""

# args: {description, characters: []}
# description: Natural language scene description
# characters: List of character labels already in scene
# Returns: {sceneType, actions: [], cameras: [], suggestions: []}
# Generate a complete scene from natural language description
_CREATE_SCENE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var description = (args.description || "").toLowerCase();
    var characters = args.characters || [];

    var actions = [];
    var cameras = [];
    var suggestions = [];
    var sceneType = "generic";

    // Helper: Create camera
    function createCamera(label, x, y, z, aimX, aimY, aimZ) {
        var cam = new DzBasicCamera();
        cam.setLabel(label);
        Scene.addNode(cam);
        var xp = cam.findProperty("XTranslate");
        var yp = cam.findProperty("YTranslate");
        var zp = cam.findProperty("ZTranslate");
        if (xp) xp.setValue(x);
        if (yp) yp.setValue(y);
        if (zp) zp.setValue(z);
        cam.aimAt(new DzVec3(aimX, aimY, aimZ));
        return cam;
    }

    // Helper: Create spot light
    function createSpotLight(label, x, y, z, flux, aimX, aimY, aimZ) {
        var light = new DzSpotLight();
        light.setLabel(label);
        Scene.addNode(light);
        var xp = light.findProperty("XTranslate");
        var yp = light.findProperty("YTranslate");
        var zp = light.findProperty("ZTranslate");
        if (xp) xp.setValue(x);
        if (yp) yp.setValue(y);
        if (zp) zp.setValue(z);
        light.aimAt(new DzVec3(aimX, aimY, aimZ));
        var fluxProp = light.findProperty("Flux");
        if (fluxProp) fluxProp.setValue(flux);
        return light;
    }

    // Helper: Set environment mode to Scene Only
    function setSceneOnlyLighting() {
        var renderMgr = App.getRenderMgr();
        var opts = renderMgr.getRenderOptions();
        opts.drawGroundPlane = false;
        var envMode = opts.findProperty("Environment Mode");
        if (envMode) envMode.setValue(3); // Scene Only
    }

    // Get primary subject if characters provided
    var subject = null;
    var subjectCenter = {x: 0, y: 100, z: 0};
    var subjectHeight = 170;
    var eyeHeight = 160;

    if (characters.length > 0) {
        subject = Scene.findNodeByLabel(characters[0]);
        if (!subject) subject = Scene.findNode(characters[0]);
        if (subject) {
            var bbox = subject.getBoundingBox();
            subjectCenter = bbox.getCenter();
            subjectHeight = bbox.max.y - bbox.min.y;
            eyeHeight = bbox.min.y + subjectHeight * 0.85;
        }
    }

    // Scene type detection and setup
    if (description.indexOf("dinner") !== -1 || description.indexOf("meal") !== -1 || description.indexOf("eat") !== -1) {
        sceneType = "dining";
        actions.push("Scene type: Dining/meal scene");

        // Position characters facing each other (if 2+ characters)
        if (characters.length >= 2) {
            var char1 = Scene.findNodeByLabel(characters[0]);
            var char2 = Scene.findNodeByLabel(characters[1]);
            if (char1 && char2) {
                var c1pos = char1.findProperty("ZTranslate");
                var c2pos = char2.findProperty("ZTranslate");
                var c1rot = char1.findProperty("YRotate");
                var c2rot = char2.findProperty("YRotate");
                if (c1pos) c1pos.setValue(-60);
                if (c2pos) c2pos.setValue(60);
                if (c1rot) c1rot.setValue(180);
                if (c2rot) c2rot.setValue(0);
                actions.push("Positioned characters facing each other across table distance");
            }
        }

        // Warm romantic lighting
        if (description.indexOf("romantic") !== -1) {
            createSpotLight("Warm Key Light", 100, 180, 100, 1500, subjectCenter.x, eyeHeight, subjectCenter.z);
            createSpotLight("Warm Fill Light", -80, 150, 80, 600, subjectCenter.x, eyeHeight, subjectCenter.z);
            actions.push("Applied warm romantic lighting");
        } else {
            createSpotLight("Key Light", 120, 180, 120, 1800, subjectCenter.x, eyeHeight, subjectCenter.z);
            createSpotLight("Fill Light", -100, 150, 100, 700, subjectCenter.x, eyeHeight, subjectCenter.z);
            actions.push("Applied dining scene lighting");
        }

        setSceneOnlyLighting();

        // Cameras
        var cam1 = createCamera("Wide Shot", 0, eyeHeight, 250, 0, eyeHeight, 0);
        cameras.push({label: "Wide Shot", type: "wide", purpose: "Establishing shot of dining scene"});

        if (characters.length >= 2) {
            var cam2 = createCamera("Over Shoulder 1", -50, eyeHeight - 10, -60, 50, eyeHeight, 60);
            cameras.push({label: "Over Shoulder 1", type: "over-shoulder", purpose: "Conversation angle"});
        }

        suggestions.push("Add table prop for dining scene");
        suggestions.push("Add plates, glasses, or food props for realism");
        suggestions.push("Consider adding candles for romantic dinner mood");

    } else if (description.indexOf("interview") !== -1 || description.indexOf("meeting") !== -1 || description.indexOf("business") !== -1) {
        sceneType = "interview";
        actions.push("Scene type: Interview/business meeting");

        // Position characters facing each other
        if (characters.length >= 2) {
            var char1 = Scene.findNodeByLabel(characters[0]);
            var char2 = Scene.findNodeByLabel(characters[1]);
            if (char1 && char2) {
                var c1x = char1.findProperty("XTranslate");
                var c1z = char1.findProperty("ZTranslate");
                var c2x = char2.findProperty("XTranslate");
                var c2z = char2.findProperty("ZTranslate");
                var c1rot = char1.findProperty("YRotate");
                var c2rot = char2.findProperty("YRotate");
                if (c1x) c1x.setValue(-80);
                if (c1z) c1z.setValue(0);
                if (c2x) c2x.setValue(80);
                if (c2z) c2z.setValue(0);
                if (c1rot) c1rot.setValue(90);
                if (c2rot) c2rot.setValue(-90);
                actions.push("Positioned characters facing each other for interview");
            }
        }

        // Professional neutral lighting
        createSpotLight("Key Light", 150, 200, 120, 2200, subjectCenter.x, eyeHeight, subjectCenter.z);
        createSpotLight("Fill Light", -120, 180, 100, 1000, subjectCenter.x, eyeHeight, subjectCenter.z);
        createSpotLight("Back Light", 0, 220, -180, 1400, subjectCenter.x, eyeHeight, subjectCenter.z);
        actions.push("Applied professional three-point lighting");
        setSceneOnlyLighting();

        // Cameras
        var cam1 = createCamera("Wide Shot", 0, eyeHeight + 10, 300, 0, eyeHeight, 0);
        cameras.push({label: "Wide Shot", type: "wide", purpose: "Establishing interview setup"});

        if (characters.length >= 1) {
            var cam2 = createCamera("Medium Shot", subjectCenter.x, eyeHeight, subjectCenter.z + 140, subjectCenter.x, eyeHeight, subjectCenter.z);
            cameras.push({label: "Medium Shot", type: "medium", purpose: "Professional medium shot"});
        }

        suggestions.push("Add desk or table prop between characters");
        suggestions.push("Add chairs for seated interview");
        suggestions.push("Consider office props (laptop, papers) for context");

    } else if (description.indexOf("portrait") !== -1 || description.indexOf("headshot") !== -1 || description.indexOf("photo") !== -1) {
        sceneType = "portrait";
        actions.push("Scene type: Portrait/headshot");

        // Three-point lighting
        if (subject) {
            createSpotLight("Key Light", subjectCenter.x + 150, eyeHeight + 30, subjectCenter.z + 120, 2000,
                           subjectCenter.x, eyeHeight, subjectCenter.z);
            createSpotLight("Fill Light", subjectCenter.x - 120, eyeHeight + 15, subjectCenter.z + 100, 800,
                           subjectCenter.x, eyeHeight, subjectCenter.z);
            createSpotLight("Rim Light", subjectCenter.x, eyeHeight + 50, subjectCenter.z - 150, 1200,
                           subjectCenter.x, eyeHeight, subjectCenter.z);
            actions.push("Applied classic three-point portrait lighting");
            setSceneOnlyLighting();
        }

        // Cameras
        if (subject) {
            var cam1 = createCamera("Close-up", subjectCenter.x, eyeHeight, subjectCenter.z + 50,
                                   subjectCenter.x, eyeHeight, subjectCenter.z);
            cameras.push({label: "Close-up", type: "close-up", purpose: "Face portrait"});

            var cam2 = createCamera("Medium Close-up", subjectCenter.x + 30, eyeHeight, subjectCenter.z + 90,
                                   subjectCenter.x, eyeHeight, subjectCenter.z);
            cameras.push({label: "Medium Close-up", type: "medium-close-up", purpose: "Head and shoulders"});
        }

        suggestions.push("Adjust character facial expression for portrait mood");
        suggestions.push("Consider neutral background or backdrop prop");
        suggestions.push("Try different camera angles (high-angle, low-angle)");

    } else if (description.indexOf("conversation") !== -1 || description.indexOf("talking") !== -1 || description.indexOf("chat") !== -1) {
        sceneType = "conversation";
        actions.push("Scene type: Conversation");

        // Position characters facing each other
        if (characters.length >= 2) {
            var char1 = Scene.findNodeByLabel(characters[0]);
            var char2 = Scene.findNodeByLabel(characters[1]);
            if (char1 && char2) {
                var c1x = char1.findProperty("XTranslate");
                var c1z = char1.findProperty("ZTranslate");
                var c2x = char2.findProperty("XTranslate");
                var c2z = char2.findProperty("ZTranslate");
                var c1rot = char1.findProperty("YRotate");
                var c2rot = char2.findProperty("YRotate");
                if (c1x) c1x.setValue(-50);
                if (c1z) c1z.setValue(0);
                if (c2x) c2x.setValue(50);
                if (c2z) c2z.setValue(0);
                if (c1rot) c1rot.setValue(90);
                if (c2rot) c2rot.setValue(-90);
                actions.push("Positioned characters facing each other at conversation distance");
            }
        }

        // Natural conversational lighting
        createSpotLight("Key Light", 120, 180, 100, 1900, subjectCenter.x, eyeHeight, subjectCenter.z);
        createSpotLight("Fill Light", -100, 160, 80, 850, subjectCenter.x, eyeHeight, subjectCenter.z);
        actions.push("Applied natural conversation lighting");
        setSceneOnlyLighting();

        // Cameras for shot-reverse-shot
        if (characters.length >= 2) {
            var cam1 = createCamera("Over Shoulder 1", -40, eyeHeight - 10, -70, 50, eyeHeight, 0);
            cameras.push({label: "Over Shoulder 1", type: "over-shoulder", purpose: "Conversation angle 1"});

            var cam2 = createCamera("Over Shoulder 2", 40, eyeHeight - 10, 70, -50, eyeHeight, 0);
            cameras.push({label: "Over Shoulder 2", type: "over-shoulder", purpose: "Conversation angle 2"});
        }

        suggestions.push("Use shot-reverse-shot camera technique for conversation");
        suggestions.push("Apply emotions and look-at for animated dialogue");
        suggestions.push("Consider adding environment props for context");

    } else {
        // Generic scene setup
        sceneType = "generic";
        actions.push("Scene type: Generic scene (no specific template matched)");

        // Basic three-point lighting
        if (subject) {
            createSpotLight("Key Light", subjectCenter.x + 150, eyeHeight + 30, subjectCenter.z + 120, 2000,
                           subjectCenter.x, eyeHeight, subjectCenter.z);
            createSpotLight("Fill Light", subjectCenter.x - 120, eyeHeight + 15, subjectCenter.z + 100, 800,
                           subjectCenter.x, eyeHeight, subjectCenter.z);
            createSpotLight("Rim Light", subjectCenter.x, eyeHeight + 50, subjectCenter.z - 150, 1200,
                           subjectCenter.x, eyeHeight, subjectCenter.z);
            actions.push("Applied default three-point lighting");
            setSceneOnlyLighting();
        }

        // Basic cameras
        if (subject) {
            var cam1 = createCamera("Wide Shot", subjectCenter.x, eyeHeight, subjectCenter.z + 400,
                                   subjectCenter.x, eyeHeight, subjectCenter.z);
            cameras.push({label: "Wide Shot", type: "wide", purpose: "Establishing shot"});

            var cam2 = createCamera("Medium Shot", subjectCenter.x, eyeHeight, subjectCenter.z + 140,
                                   subjectCenter.x, eyeHeight, subjectCenter.z);
            cameras.push({label: "Medium Shot", type: "medium", purpose: "Medium framing"});
        }

        suggestions.push("Provide more specific scene description for tailored setup");
        suggestions.push("Keywords: dinner, interview, portrait, conversation");
        suggestions.push("Add props and environment elements as needed");
    }

    // General suggestions
    if (characters.length === 0) {
        suggestions.push("Load characters into scene before generating setup");
    }

    return {
        sceneType: sceneType,
        description: args.description,
        charactersUsed: characters.length,
        actions: actions,
        cameras: cameras,
        suggestions: suggestions
    };
})()
"""

# args: {cameraLabel, movementType, startFrame, endFrame, intensity}
# movementType: "dolly-in", "dolly-out", "pan-left", "pan-right", "tilt-up", "tilt-down", "crane-up", "crane-down", "handheld-shake"
# Returns: {camera, movementType, keyframesSet, frameRange}
# Animate common camera movements with keyframes
_ANIMATE_CAMERA_MOVEMENT_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cameraLabel = args.cameraLabel;
    var movementType = args.movementType;
    var startFrame = args.startFrame || 0;
    var endFrame = args.endFrame || 120;
    var intensity = args.intensity !== undefined ? args.intensity : 1.0;

    // Find camera
    var camera = Scene.findNodeByLabel(cameraLabel);
    if (!camera) camera = Scene.findNode(cameraLabel);
    if (!camera) throw new Error("Camera not found: " + cameraLabel);
    if (!camera.inherits("DzCamera")) throw new Error("Node is not a camera: " + cameraLabel);

    // Helper: Set keyframe
    function setKeyframe(node, propName, frame, value) {
        var prop = node.findProperty(propName);
        if (!prop) return false;
        var anim = prop.getAnimation();
        if (!anim) anim = prop.createAnimation();
        var key = anim.getKey(frame);
        if (!key) key = anim.addKey(frame);
        key.value = value;
        return true;
    }

    // Get current camera position and rotation
    var startX = camera.findProperty("XTranslate").getValue();
    var startY = camera.findProperty("YTranslate").getValue();
    var startZ = camera.findProperty("ZTranslate").getValue();
    var startRotX = camera.findProperty("XRotate").getValue();
    var startRotY = camera.findProperty("YRotate").getValue();
    var startRotZ = camera.findProperty("ZRotate").getValue();

    var keyframesSet = 0;
    var description = "";

    if (movementType === "dolly-in") {
        // Move camera forward (toward aim point)
        var distance = 200 * intensity;
        var angle = startRotY * Math.PI / 180;
        var deltaX = Math.sin(angle) * distance;
        var deltaZ = Math.cos(angle) * distance;

        setKeyframe(camera, "XTranslate", startFrame, startX);
        setKeyframe(camera, "ZTranslate", startFrame, startZ);
        setKeyframe(camera, "XTranslate", endFrame, startX + deltaX);
        setKeyframe(camera, "ZTranslate", endFrame, startZ + deltaZ);
        keyframesSet = 4;
        description = "Dolly in " + distance.toFixed(0) + "cm";

    } else if (movementType === "dolly-out") {
        // Move camera backward (away from aim point)
        var distance = 200 * intensity;
        var angle = startRotY * Math.PI / 180;
        var deltaX = -Math.sin(angle) * distance;
        var deltaZ = -Math.cos(angle) * distance;

        setKeyframe(camera, "XTranslate", startFrame, startX);
        setKeyframe(camera, "ZTranslate", startFrame, startZ);
        setKeyframe(camera, "XTranslate", endFrame, startX + deltaX);
        setKeyframe(camera, "ZTranslate", endFrame, startZ + deltaZ);
        keyframesSet = 4;
        description = "Dolly out " + distance.toFixed(0) + "cm";

    } else if (movementType === "pan-left") {
        // Rotate camera left (negative Y rotation)
        var rotation = 45 * intensity;
        setKeyframe(camera, "YRotate", startFrame, startRotY);
        setKeyframe(camera, "YRotate", endFrame, startRotY - rotation);
        keyframesSet = 2;
        description = "Pan left " + rotation.toFixed(0) + "°";

    } else if (movementType === "pan-right") {
        // Rotate camera right (positive Y rotation)
        var rotation = 45 * intensity;
        setKeyframe(camera, "YRotate", startFrame, startRotY);
        setKeyframe(camera, "YRotate", endFrame, startRotY + rotation);
        keyframesSet = 2;
        description = "Pan right " + rotation.toFixed(0) + "°";

    } else if (movementType === "tilt-up") {
        // Rotate camera up (negative X rotation)
        var rotation = 30 * intensity;
        setKeyframe(camera, "XRotate", startFrame, startRotX);
        setKeyframe(camera, "XRotate", endFrame, startRotX - rotation);
        keyframesSet = 2;
        description = "Tilt up " + rotation.toFixed(0) + "°";

    } else if (movementType === "tilt-down") {
        // Rotate camera down (positive X rotation)
        var rotation = 30 * intensity;
        setKeyframe(camera, "XRotate", startFrame, startRotX);
        setKeyframe(camera, "XRotate", endFrame, startRotX + rotation);
        keyframesSet = 2;
        description = "Tilt down " + rotation.toFixed(0) + "°";

    } else if (movementType === "crane-up") {
        // Move camera vertically up
        var distance = 100 * intensity;
        setKeyframe(camera, "YTranslate", startFrame, startY);
        setKeyframe(camera, "YTranslate", endFrame, startY + distance);
        keyframesSet = 2;
        description = "Crane up " + distance.toFixed(0) + "cm";

    } else if (movementType === "crane-down") {
        // Move camera vertically down
        var distance = 100 * intensity;
        setKeyframe(camera, "YTranslate", startFrame, startY);
        setKeyframe(camera, "YTranslate", endFrame, startY - distance);
        keyframesSet = 2;
        description = "Crane down " + distance.toFixed(0) + "cm";

    } else if (movementType === "handheld-shake") {
        // Procedural shake with random keyframes
        var amplitude = 5 * intensity; // cm
        var rotAmplitude = 2 * intensity; // degrees
        var frameStep = 3; // Keyframe every 3 frames for shake

        for (var frame = startFrame; frame <= endFrame; frame += frameStep) {
            // Random offsets
            var offsetX = (Math.random() - 0.5) * amplitude * 2;
            var offsetY = (Math.random() - 0.5) * amplitude * 2;
            var offsetZ = (Math.random() - 0.5) * amplitude * 2;
            var rotX = (Math.random() - 0.5) * rotAmplitude * 2;
            var rotY = (Math.random() - 0.5) * rotAmplitude * 2;
            var rotZ = (Math.random() - 0.5) * rotAmplitude * 2;

            setKeyframe(camera, "XTranslate", frame, startX + offsetX);
            setKeyframe(camera, "YTranslate", frame, startY + offsetY);
            setKeyframe(camera, "ZTranslate", frame, startZ + offsetZ);
            setKeyframe(camera, "XRotate", frame, startRotX + rotX);
            setKeyframe(camera, "YRotate", frame, startRotY + rotY);
            setKeyframe(camera, "ZRotate", frame, startRotZ + rotZ);
            keyframesSet += 6;
        }
        description = "Handheld shake (amplitude: " + amplitude.toFixed(1) + "cm)";

    } else {
        throw new Error("Unknown movement type: " + movementType +
            ". Valid: dolly-in, dolly-out, pan-left, pan-right, tilt-up, tilt-down, crane-up, crane-down, handheld-shake");
    }

    return {
        camera: camera.getLabel(),
        movementType: movementType,
        keyframesSet: keyframesSet,
        frameRange: {start: startFrame, end: endFrame},
        description: description,
        intensity: intensity
    };
})()
"""

# args: {cameraLabel, waypoints: [{position: {x, y, z}, frame: int}], easing, aimAtTarget?}
# easing: "linear", "smooth", "ease-in", "ease-out"
# Returns: {camera, waypoints: int, easing, frameRange}
# Create smooth camera path through multiple waypoints
_CREATE_CAMERA_PATH_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var cameraLabel = args.cameraLabel;
    var waypoints = args.waypoints || [];
    var easing = args.easing || "smooth";
    var aimAtTarget = args.aimAtTarget;

    // Find camera
    var camera = Scene.findNodeByLabel(cameraLabel);
    if (!camera) camera = Scene.findNode(cameraLabel);
    if (!camera) throw new Error("Camera not found: " + cameraLabel);
    if (!camera.inherits("DzCamera")) throw new Error("Node is not a camera: " + cameraLabel);

    if (waypoints.length < 2) {
        throw new Error("At least 2 waypoints required");
    }

    // Helper: Set keyframe
    function setKeyframe(node, propName, frame, value) {
        var prop = node.findProperty(propName);
        if (!prop) return false;
        var anim = prop.getAnimation();
        if (!anim) anim = prop.createAnimation();
        var key = anim.getKey(frame);
        if (!key) key = anim.addKey(frame);
        key.value = value;
        return true;
    }

    // Sort waypoints by frame
    waypoints.sort(function(a, b) { return a.frame - b.frame; });

    // Set keyframes at each waypoint
    var keyframesSet = 0;
    for (var i = 0; i < waypoints.length; i++) {
        var wp = waypoints[i];
        var pos = wp.position;
        var frame = wp.frame;

        if (!pos || pos.x === undefined || pos.y === undefined || pos.z === undefined) {
            throw new Error("Waypoint " + i + " missing position (x, y, z)");
        }
        if (frame === undefined) {
            throw new Error("Waypoint " + i + " missing frame");
        }

        setKeyframe(camera, "XTranslate", frame, pos.x);
        setKeyframe(camera, "YTranslate", frame, pos.y);
        setKeyframe(camera, "ZTranslate", frame, pos.z);
        keyframesSet += 3;
    }

    // Optionally animate aim-at target
    var targetNode = null;
    if (aimAtTarget) {
        targetNode = Scene.findNodeByLabel(aimAtTarget);
        if (!targetNode) targetNode = Scene.findNode(aimAtTarget);
        if (targetNode) {
            var targetPos = targetNode.getWSPos();
            // For simplicity, just aim at start and end
            // Full implementation would animate pointing at target throughout
            camera.aimAt(new DzVec3(targetPos.x, targetPos.y, targetPos.z));
        }
    }

    var startFrame = waypoints[0].frame;
    var endFrame = waypoints[waypoints.length - 1].frame;

    return {
        camera: camera.getLabel(),
        waypointCount: waypoints.length,
        easing: easing,
        keyframesSet: keyframesSet,
        frameRange: {start: startFrame, end: endFrame},
        aimAtTarget: targetNode ? targetNode.getLabel() : null
    };
})()
"""

# args: {characterLabel, waypoints: [{position: {x, y, z}, frame: int}], pathType, walkingStyle}
# pathType: "straight", "curved", "circular"
# walkingStyle: "casual", "hurried", "sneaking"
# Returns: {character, waypoints: int, pathType, frameRange, distance}
# Animate character movement along a path
_CREATE_CHARACTER_PATH_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var characterLabel = args.characterLabel;
    var waypoints = args.waypoints || [];
    var pathType = args.pathType || "straight";
    var walkingStyle = args.walkingStyle || "casual";

    // Find character
    var character = Scene.findNodeByLabel(characterLabel);
    if (!character) character = Scene.findNode(characterLabel);
    if (!character) throw new Error("Character not found: " + characterLabel);

    if (waypoints.length < 2) {
        throw new Error("At least 2 waypoints required");
    }

    // Helper: Set keyframe
    function setKeyframe(node, propName, frame, value) {
        var prop = node.findProperty(propName);
        if (!prop) return false;
        var anim = prop.getAnimation();
        if (!anim) anim = prop.createAnimation();
        var key = anim.getKey(frame);
        if (!key) key = anim.addKey(frame);
        key.value = value;
        return true;
    }

    // Sort waypoints by frame
    waypoints.sort(function(a, b) { return a.frame - b.frame; });

    var keyframesSet = 0;
    var totalDistance = 0;

    // Set position keyframes and calculate distance
    for (var i = 0; i < waypoints.length; i++) {
        var wp = waypoints[i];
        var pos = wp.position;
        var frame = wp.frame;

        if (!pos || pos.x === undefined || pos.y === undefined || pos.z === undefined) {
            throw new Error("Waypoint " + i + " missing position (x, y, z)");
        }
        if (frame === undefined) {
            throw new Error("Waypoint " + i + " missing frame");
        }

        setKeyframe(character, "XTranslate", frame, pos.x);
        setKeyframe(character, "YTranslate", frame, pos.y);
        setKeyframe(character, "ZTranslate", frame, pos.z);
        keyframesSet += 3;

        // Calculate distance to next waypoint
        if (i > 0) {
            var prevPos = waypoints[i - 1].position;
            var dx = pos.x - prevPos.x;
            var dy = pos.y - prevPos.y;
            var dz = pos.z - prevPos.z;
            totalDistance += Math.sqrt(dx*dx + dy*dy + dz*dz);
        }

        // Rotate character to face direction of travel
        if (i < waypoints.length - 1) {
            var nextPos = waypoints[i + 1].position;
            var angle = Math.atan2(nextPos.x - pos.x, nextPos.z - pos.z) * 180 / Math.PI;
            setKeyframe(character, "YRotate", frame, angle);
            keyframesSet++;
        }
    }

    var startFrame = waypoints[0].frame;
    var endFrame = waypoints[waypoints.length - 1].frame;

    return {
        character: character.getLabel(),
        waypointCount: waypoints.length,
        pathType: pathType,
        walkingStyle: walkingStyle,
        keyframesSet: keyframesSet,
        frameRange: {start: startFrame, end: endFrame},
        totalDistance: Math.round(totalDistance * 10) / 10,
        note: "Character will move along path. Walking cycle animation not automatically applied."
    };
})()
"""

# args: {characters: [], arrangement, spacing, facing, centerPosition?}
# arrangement: "line", "semicircle", "triangle", "conversation-circle"
# facing: "center", "camera", "forward"
# Returns: {characters: [{label, position, rotation}], arrangement, spacing}
# Position multiple characters in formation
_ARRANGE_CHARACTERS_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var characterLabels = args.characters || [];
    var arrangement = args.arrangement || "line";
    var spacing = args.spacing || 80;
    var facing = args.facing || "forward";
    var centerPosition = args.centerPosition || {x: 0, y: 0, z: 0};

    if (characterLabels.length < 2) {
        throw new Error("At least 2 characters required for arrangement");
    }

    // Find all characters
    var characters = [];
    for (var i = 0; i < characterLabels.length; i++) {
        var char = Scene.findNodeByLabel(characterLabels[i]);
        if (!char) char = Scene.findNode(characterLabels[i]);
        if (!char) throw new Error("Character not found: " + characterLabels[i]);
        characters.push(char);
    }

    var count = characters.length;
    var positions = [];
    var cx = centerPosition.x;
    var cy = centerPosition.y;
    var cz = centerPosition.z;

    // Calculate positions based on arrangement type
    if (arrangement === "line") {
        // Straight line along X axis
        var startX = cx - (spacing * (count - 1)) / 2;
        for (var i = 0; i < count; i++) {
            positions.push({
                x: startX + i * spacing,
                y: cy,
                z: cz
            });
        }

    } else if (arrangement === "semicircle") {
        // Arc formation
        var radius = (spacing * count) / Math.PI;
        for (var i = 0; i < count; i++) {
            var angle = (i / (count - 1)) * Math.PI;
            positions.push({
                x: cx + radius * Math.sin(angle),
                y: cy,
                z: cz - radius * Math.cos(angle)
            });
        }

    } else if (arrangement === "triangle") {
        // Triangular formation
        if (count === 2) {
            positions.push({x: cx - spacing/2, y: cy, z: cz});
            positions.push({x: cx + spacing/2, y: cy, z: cz});
        } else if (count === 3) {
            positions.push({x: cx, y: cy, z: cz - spacing * 0.6});
            positions.push({x: cx - spacing/2, y: cy, z: cz + spacing * 0.3});
            positions.push({x: cx + spacing/2, y: cy, z: cz + spacing * 0.3});
        } else {
            // Arrange in rows
            var row1 = Math.floor(count / 2);
            var row2 = count - row1;
            for (var i = 0; i < row1; i++) {
                var xOffset = (i - (row1 - 1) / 2) * spacing;
                positions.push({x: cx + xOffset, y: cy, z: cz - spacing * 0.6});
            }
            for (var i = 0; i < row2; i++) {
                var xOffset = (i - (row2 - 1) / 2) * spacing;
                positions.push({x: cx + xOffset, y: cy, z: cz + spacing * 0.3});
            }
        }

    } else if (arrangement === "conversation-circle") {
        // Circle facing inward
        var radius = spacing;
        for (var i = 0; i < count; i++) {
            var angle = (i / count) * 2 * Math.PI;
            positions.push({
                x: cx + radius * Math.sin(angle),
                y: cy,
                z: cz + radius * Math.cos(angle)
            });
        }

    } else {
        throw new Error("Unknown arrangement: " + arrangement +
            ". Valid: line, semicircle, triangle, conversation-circle");
    }

    // Apply positions and rotations
    var results = [];
    for (var i = 0; i < count; i++) {
        var char = characters[i];
        var pos = positions[i];

        // Set position
        var xp = char.findProperty("XTranslate");
        var yp = char.findProperty("YTranslate");
        var zp = char.findProperty("ZTranslate");
        if (xp) xp.setValue(pos.x);
        if (yp) yp.setValue(pos.y);
        if (zp) zp.setValue(pos.z);

        // Calculate rotation based on facing
        var rotation = 0;
        if (facing === "center") {
            // Face toward center
            var angle = Math.atan2(pos.x - cx, pos.z - cz) * 180 / Math.PI;
            rotation = angle + 180;
        } else if (facing === "camera") {
            // Face camera (assuming camera at +Z)
            rotation = 0;
        } else if (facing === "forward") {
            // Face forward (+Z direction)
            rotation = 0;
        }

        var rp = char.findProperty("YRotate");
        if (rp) rp.setValue(rotation);

        results.push({
            label: char.getLabel(),
            position: {x: Math.round(pos.x * 10) / 10, y: Math.round(pos.y * 10) / 10, z: Math.round(pos.z * 10) / 10},
            rotation: Math.round(rotation * 10) / 10
        });
    }

    return {
        characters: results,
        arrangement: arrangement,
        spacing: spacing,
        facing: facing,
        count: count
    };
})()
"""

# args: {actionType, characters: [], startFrame, duration}
# actionType: "handshake", "hug", "fight", "dance"
# Returns: {actionType, characters: [], positions: [], suggestions: []}
# Choreograph simple action between characters
_CHOREOGRAPH_ACTION_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var actionType = args.actionType;
    var characterLabels = args.characters || [];
    var startFrame = args.startFrame || 0;
    var duration = args.duration || 90;

    if (characterLabels.length < 1) {
        throw new Error("At least 1 character required");
    }

    // Find all characters
    var characters = [];
    for (var i = 0; i < characterLabels.length; i++) {
        var char = Scene.findNodeByLabel(characterLabels[i]);
        if (!char) char = Scene.findNode(characterLabels[i]);
        if (!char) throw new Error("Character not found: " + characterLabels[i]);
        characters.push(char);
    }

    var positions = [];
    var suggestions = [];

    if (actionType === "handshake") {
        if (characters.length < 2) {
            throw new Error("handshake requires 2 characters");
        }

        var char1 = characters[0];
        var char2 = characters[1];

        // Position characters facing each other
        var spacing = 60; // Close enough for handshake
        var x1 = char1.findProperty("XTranslate");
        var z1 = char1.findProperty("ZTranslate");
        var x2 = char2.findProperty("XTranslate");
        var z2 = char2.findProperty("ZTranslate");
        var r1 = char1.findProperty("YRotate");
        var r2 = char2.findProperty("YRotate");

        if (x1) x1.setValue(-spacing/2);
        if (z1) z1.setValue(0);
        if (x2) x2.setValue(spacing/2);
        if (z2) z2.setValue(0);
        if (r1) r1.setValue(90); // Face right
        if (r2) r2.setValue(-90); // Face left

        positions.push({character: char1.getLabel(), position: {x: -spacing/2, y: 0, z: 0}, rotation: 90});
        positions.push({character: char2.getLabel(), position: {x: spacing/2, y: 0, z: 0}, rotation: -90});

        suggestions.push("Use daz_reach_toward to position hands for handshake");
        suggestions.push("Apply 'friendly' or 'professional' emotion to both characters");

    } else if (actionType === "hug") {
        if (characters.length < 2) {
            throw new Error("hug requires 2 characters");
        }

        var char1 = characters[0];
        var char2 = characters[1];

        // Position characters very close, facing each other
        var spacing = 30; // Very close for hug
        var x1 = char1.findProperty("XTranslate");
        var z1 = char1.findProperty("ZTranslate");
        var x2 = char2.findProperty("XTranslate");
        var z2 = char2.findProperty("ZTranslate");
        var r1 = char1.findProperty("YRotate");
        var r2 = char2.findProperty("YRotate");

        if (x1) x1.setValue(-spacing/2);
        if (z1) z1.setValue(0);
        if (x2) x2.setValue(spacing/2);
        if (z2) z2.setValue(0);
        if (r1) r1.setValue(90);
        if (r2) r2.setValue(-90);

        positions.push({character: char1.getLabel(), position: {x: -spacing/2, y: 0, z: 0}, rotation: 90});
        positions.push({character: char2.getLabel(), position: {x: spacing/2, y: 0, z: 0}, rotation: -90});

        suggestions.push("Use daz_interactive_pose with 'hug' type for arm positioning");
        suggestions.push("Apply 'loving' or 'happy' emotion to both characters");

    } else if (actionType === "fight") {
        if (characters.length < 2) {
            throw new Error("fight requires 2 characters");
        }

        var char1 = characters[0];
        var char2 = characters[1];

        // Position characters at fighting distance
        var spacing = 100;
        var x1 = char1.findProperty("XTranslate");
        var z1 = char1.findProperty("ZTranslate");
        var x2 = char2.findProperty("XTranslate");
        var z2 = char2.findProperty("ZTranslate");
        var r1 = char1.findProperty("YRotate");
        var r2 = char2.findProperty("YRotate");

        if (x1) x1.setValue(-spacing/2);
        if (z1) z1.setValue(0);
        if (x2) x2.setValue(spacing/2);
        if (z2) z2.setValue(0);
        if (r1) r1.setValue(90);
        if (r2) r2.setValue(-90);

        positions.push({character: char1.getLabel(), position: {x: -spacing/2, y: 0, z: 0}, rotation: 90});
        positions.push({character: char2.getLabel(), position: {x: spacing/2, y: 0, z: 0}, rotation: -90});

        suggestions.push("Apply fighting stance poses from content library");
        suggestions.push("Apply 'angry' or 'aggressive' emotion");
        suggestions.push("Use low-angle camera for dramatic effect");

    } else if (actionType === "dance") {
        if (characters.length < 2) {
            throw new Error("dance requires 2 characters");
        }

        var char1 = characters[0];
        var char2 = characters[1];

        // Position characters for partner dance
        var spacing = 40;
        var x1 = char1.findProperty("XTranslate");
        var z1 = char1.findProperty("ZTranslate");
        var x2 = char2.findProperty("XTranslate");
        var z2 = char2.findProperty("ZTranslate");
        var r1 = char1.findProperty("YRotate");
        var r2 = char2.findProperty("YRotate");

        if (x1) x1.setValue(-spacing/2);
        if (z1) z1.setValue(0);
        if (x2) x2.setValue(spacing/2);
        if (z2) z2.setValue(0);
        if (r1) r1.setValue(90);
        if (r2) r2.setValue(-90);

        positions.push({character: char1.getLabel(), position: {x: -spacing/2, y: 0, z: 0}, rotation: 90});
        positions.push({character: char2.getLabel(), position: {x: spacing/2, y: 0, z: 0}, rotation: -90});

        suggestions.push("Apply partner dance poses from content library");
        suggestions.push("Use daz_create_character_path for dance movement");
        suggestions.push("Apply 'happy' or 'excited' emotion");

    } else {
        throw new Error("Unknown action type: " + actionType +
            ". Valid: handshake, hug, fight, dance");
    }

    return {
        actionType: actionType,
        characters: characterLabels,
        positions: positions,
        frameRange: {start: startFrame, end: startFrame + duration},
        suggestions: suggestions
    };
})()
"""

# ---------------------------------------------------------------------------
# Phase 4.7: Cinematic Coverage Tools
# ---------------------------------------------------------------------------

_SETUP_SHOT_COVERAGE_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var subjectLabel = args.subjectLabel;
    var coverageType = args.coverageType || "standard";
    var cameraHeight = args.cameraHeight || 160;
    var autoAim = args.autoAim !== false;

    // Find subject node
    var subject = Scene.findNodeByLabel(subjectLabel);
    if (!subject) subject = Scene.findNode(subjectLabel);
    if (!subject) throw new Error("Subject not found: " + subjectLabel);

    // Get subject position
    var subX = subject.findProperty("XTranslate");
    var subY = subject.findProperty("YTranslate");
    var subZ = subject.findProperty("ZTranslate");

    var subjectPos = {
        x: subX ? subX.getValue() : 0,
        y: subY ? subY.getValue() : 0,
        z: subZ ? subZ.getValue() : 0
    };

    var cameras = [];
    var cameraNodes = [];

    // Coverage patterns
    var shots = [];

    if (coverageType === "standard") {
        // Master, Medium, Closeup
        shots = [
            {name: "Master", distance: 400, height: cameraHeight, angle: 0, focalLength: 35},
            {name: "Medium", distance: 200, height: cameraHeight, angle: 0, focalLength: 50},
            {name: "Closeup", distance: 100, height: cameraHeight + 10, angle: 0, focalLength: 85}
        ];
    } else if (coverageType === "interview") {
        // Two-shot + singles
        shots = [
            {name: "TwoShot", distance: 250, height: cameraHeight, angle: 0, focalLength: 50},
            {name: "SingleA", distance: 150, height: cameraHeight, angle: -30, focalLength: 85},
            {name: "SingleB", distance: 150, height: cameraHeight, angle: 30, focalLength: 85}
        ];
    } else if (coverageType === "dramatic") {
        // Master, Low Angle, High Angle, Profile
        shots = [
            {name: "Master", distance: 350, height: cameraHeight, angle: 0, focalLength: 35},
            {name: "LowAngle", distance: 180, height: cameraHeight - 80, angle: 0, focalLength: 50},
            {name: "HighAngle", distance: 200, height: cameraHeight + 120, angle: 0, focalLength: 50},
            {name: "Profile", distance: 180, height: cameraHeight, angle: 90, focalLength: 85}
        ];
    } else if (coverageType === "action") {
        // Wide, Medium, Tracking, Low Angle
        shots = [
            {name: "WideAction", distance: 450, height: cameraHeight, angle: 0, focalLength: 28},
            {name: "MediumAction", distance: 250, height: cameraHeight, angle: 0, focalLength: 50},
            {name: "TrackingShot", distance: 200, height: cameraHeight - 20, angle: -45, focalLength: 35},
            {name: "HeroLow", distance: 150, height: cameraHeight - 100, angle: 0, focalLength: 85}
        ];
    } else {
        throw new Error("Unknown coverageType: " + coverageType +
            ". Valid: standard, interview, dramatic, action");
    }

    // Create cameras
    for (var i = 0; i < shots.length; i++) {
        var shot = shots[i];
        var cam = Scene.createNode("DzCamera");
        cam.setLabel(shot.name + "_Camera");

        // Position camera
        var angleRad = shot.angle * (Math.PI / 180);
        var camX = subjectPos.x + (shot.distance * Math.sin(angleRad));
        var camZ = subjectPos.z - (shot.distance * Math.cos(angleRad));
        var camY = shot.height;

        var xProp = cam.findProperty("XTranslate");
        var yProp = cam.findProperty("YTranslate");
        var zProp = cam.findProperty("ZTranslate");

        if (xProp) xProp.setValue(camX);
        if (yProp) yProp.setValue(camY);
        if (zProp) zProp.setValue(camZ);

        // Set focal length
        var focalProp = cam.findProperty("FocalLength");
        if (focalProp) focalProp.setValue(shot.focalLength);

        // Point at subject if auto-aim
        if (autoAim) {
            var xRot = cam.findProperty("XRotate");
            var yRot = cam.findProperty("YRotate");

            // Calculate direction to subject
            var dx = subjectPos.x - camX;
            var dy = subjectPos.y - camY;
            var dz = subjectPos.z - camZ;
            var distXZ = Math.sqrt(dx * dx + dz * dz);

            // Y rotation (horizontal)
            var yRotValue = Math.atan2(dx, -dz) * (180 / Math.PI);
            // X rotation (vertical tilt)
            var xRotValue = Math.atan2(dy, distXZ) * (180 / Math.PI);

            if (xRot) xRot.setValue(xRotValue);
            if (yRot) yRot.setValue(yRotValue);
        }

        cameras.push({
            name: shot.name,
            label: cam.getLabel(),
            position: {x: camX, y: camY, z: camZ},
            focalLength: shot.focalLength,
            distance: shot.distance,
            angle: shot.angle
        });
        cameraNodes.push(cam);
    }

    return {
        coverageType: coverageType,
        subject: subjectLabel,
        subjectPosition: subjectPos,
        cameras: cameras,
        cameraCount: cameras.length,
        suggestions: [
            "Switch between cameras to render different angles",
            "Use daz_animate_camera_movement for dynamic shots",
            "Adjust focal lengths for desired framing"
        ]
    };
})()
"""

_CREATE_CAMERA_RIG_SCRIPT = """\
(function(){
    var args = getArguments()[0] || {};
    var rigName = args.rigName || "CameraRig";
    var centerPosition = args.centerPosition || {x: 0, y: 150, z: 0};
    var cameraCount = args.cameraCount || 3;
    var radius = args.radius || 250;
    var heightVariation = args.heightVariation || 40;
    var focalLengths = args.focalLengths || [35, 50, 85];

    if (cameraCount < 2 || cameraCount > 8) {
        throw new Error("cameraCount must be between 2 and 8");
    }

    if (focalLengths.length < cameraCount) {
        // Extend focal lengths array to match camera count
        while (focalLengths.length < cameraCount) {
            focalLengths.push(50); // Default to 50mm
        }
    }

    var cameras = [];
    var angleStep = 360 / cameraCount;

    // Create parent null for rig
    var rigParent = Scene.createNode("DzBone");
    rigParent.setLabel(rigName + "_Rig");

    var rigX = rigParent.findProperty("XTranslate");
    var rigY = rigParent.findProperty("YTranslate");
    var rigZ = rigParent.findProperty("ZTranslate");

    if (rigX) rigX.setValue(centerPosition.x);
    if (rigY) rigY.setValue(centerPosition.y);
    if (rigZ) rigZ.setValue(centerPosition.z);

    // Create cameras in circle around center
    for (var i = 0; i < cameraCount; i++) {
        var angle = i * angleStep;
        var angleRad = angle * (Math.PI / 180);

        var cam = Scene.createNode("DzCamera");
        cam.setLabel(rigName + "_Cam" + (i + 1));

        // Position relative to center
        var offsetX = radius * Math.sin(angleRad);
        var offsetZ = radius * Math.cos(angleRad);
        var offsetY = (Math.sin(i * 0.7) * heightVariation);

        var camX = cam.findProperty("XTranslate");
        var camY = cam.findProperty("YTranslate");
        var camZ = cam.findProperty("ZTranslate");

        if (camX) camX.setValue(offsetX);
        if (camY) camY.setValue(offsetY);
        if (camZ) camZ.setValue(offsetZ);

        // Set focal length
        var focalProp = cam.findProperty("FocalLength");
        if (focalProp) focalProp.setValue(focalLengths[i]);

        // Point camera at center
        var yRot = cam.findProperty("YRotate");
        if (yRot) yRot.setValue(angle + 180);

        var xRot = cam.findProperty("XRotate");
        if (xRot) {
            var tiltAngle = Math.atan2(-offsetY, radius) * (180 / Math.PI);
            xRot.setValue(tiltAngle);
        }

        // Parent to rig
        cam.setParent(rigParent);

        cameras.push({
            name: cam.getLabel(),
            angle: angle,
            focalLength: focalLengths[i],
            heightOffset: offsetY
        });
    }

    return {
        rigName: rigName,
        rigLabel: rigParent.getLabel(),
        centerPosition: centerPosition,
        radius: radius,
        cameraCount: cameraCount,
        cameras: cameras,
        suggestions: [
            "Rotate rig parent node (YRotate) to orbit all cameras around subject",
            "Animate rig position to move entire camera array",
            "Switch between cameras for bullet-time effect",
            "Adjust individual camera focal lengths for variety"
        ]
    };
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
    "vangard-list-morphs": (
        "List all morphs (numeric properties) on a node with current values",
        _LIST_MORPHS_SCRIPT,
    ),
    "vangard-search-morphs": (
        "Search morphs by name pattern (case-insensitive substring match)",
        _SEARCH_MORPHS_SCRIPT,
    ),
    "vangard-get-node-hierarchy": (
        "Get complete hierarchy tree for a node with recursive children",
        _GET_NODE_HIERARCHY_SCRIPT,
    ),
    "vangard-list-children": (
        "List direct children of a node",
        _LIST_CHILDREN_SCRIPT,
    ),
    "vangard-get-parent": (
        "Get parent node of a node",
        _GET_PARENT_SCRIPT,
    ),
    "vangard-set-parent": (
        "Set parent of a node (parenting operation)",
        _SET_PARENT_SCRIPT,
    ),
    "vangard-look-at-point": (
        "Make character look at world-space point with configurable body involvement",
        _LOOK_AT_POINT_SCRIPT,
    ),
    "vangard-look-at-character": (
        "Make one character look at another character's head position",
        _LOOK_AT_CHARACTER_SCRIPT,
    ),
    "vangard-reach-toward": (
        "Position arm/hand to reach toward world-space point using pseudo-IK",
        _REACH_TOWARD_SCRIPT,
    ),
    "vangard-interactive-pose": (
        "Coordinate two characters for interactive poses (hug, handshake, etc)",
        _INTERACTIVE_POSE_SCRIPT,
    ),
    "vangard-batch-set-properties": (
        "Set multiple properties on one or more nodes with individual error handling",
        _BATCH_SET_PROPERTIES_SCRIPT,
    ),
    "vangard-batch-transform": (
        "Apply same transform properties to multiple nodes",
        _BATCH_TRANSFORM_SCRIPT,
    ),
    "vangard-batch-visibility": (
        "Show or hide multiple nodes",
        _BATCH_VISIBILITY_SCRIPT,
    ),
    "vangard-batch-select": (
        "Select multiple nodes (replace or add to current selection)",
        _BATCH_SELECT_SCRIPT,
    ),
    "vangard-set-active-camera": (
        "Set which camera is active in the viewport",
        _SET_ACTIVE_CAMERA_SCRIPT,
    ),
    "vangard-orbit-camera-around": (
        "Position camera orbiting around a target node at specified angle and distance",
        _ORBIT_CAMERA_AROUND_SCRIPT,
    ),
    "vangard-frame-camera-to-node": (
        "Frame camera to show a node by positioning at calculated distance",
        _FRAME_CAMERA_TO_NODE_SCRIPT,
    ),
    "vangard-save-camera-preset": (
        "Save camera position and rotation as preset data",
        _SAVE_CAMERA_PRESET_SCRIPT,
    ),
    "vangard-load-camera-preset": (
        "Restore camera position and rotation from preset data",
        _LOAD_CAMERA_PRESET_SCRIPT,
    ),
    "vangard-set-keyframe": (
        "Set a keyframe on a property at specified frame",
        _SET_KEYFRAME_SCRIPT,
    ),
    "vangard-get-keyframes": (
        "Get all keyframes for a property",
        _GET_KEYFRAMES_SCRIPT,
    ),
    "vangard-remove-keyframe": (
        "Remove a keyframe at specified frame",
        _REMOVE_KEYFRAME_SCRIPT,
    ),
    "vangard-clear-animation": (
        "Remove all keyframes from a property",
        _CLEAR_ANIMATION_SCRIPT,
    ),
    "vangard-set-frame": (
        "Set current animation frame",
        _SET_FRAME_SCRIPT,
    ),
    "vangard-set-frame-range": (
        "Set animation frame range (start and end)",
        _SET_FRAME_RANGE_SCRIPT,
    ),
    "vangard-get-animation-info": (
        "Get animation timeline info (current frame, range, fps)",
        _GET_ANIMATION_INFO_SCRIPT,
    ),
    "vangard-render-with-camera": (
        "Render from specific camera without changing viewport",
        _RENDER_WITH_CAMERA_SCRIPT,
    ),
    "vangard-get-render-settings": (
        "Get current render settings and configuration",
        _GET_RENDER_SETTINGS_SCRIPT,
    ),
    "vangard-batch-render-cameras": (
        "Render from multiple cameras in sequence",
        _BATCH_RENDER_CAMERAS_SCRIPT,
    ),
    "vangard-render-animation": (
        "Render animation frame range as image sequence",
        _RENDER_ANIMATION_SCRIPT,
    ),
    # Phase 1: Spatial queries
    "vangard-get-world-position": (
        "Get world-space position, local position, rotation, and scale of a node",
        _GET_WORLD_POSITION_SCRIPT,
    ),
    "vangard-get-bounding-box": (
        "Get bounding box (min, max, center, dimensions) of a node",
        _GET_BOUNDING_BOX_SCRIPT,
    ),
    "vangard-calculate-distance": (
        "Calculate distance and direction vector between two nodes",
        _CALCULATE_DISTANCE_SCRIPT,
    ),
    "vangard-get-spatial-relationship": (
        "Get natural language spatial relationship between two nodes",
        _GET_SPATIAL_RELATIONSHIP_SCRIPT,
    ),
    "vangard-check-overlap": (
        "Check if two nodes have overlapping bounding boxes",
        _CHECK_OVERLAP_SCRIPT,
    ),
    # Phase 1: Property introspection
    "vangard-inspect-properties": (
        "List all properties on a node with metadata (type, value, min, max)",
        _INSPECT_PROPERTIES_SCRIPT,
    ),
    "vangard-get-property-metadata": (
        "Get detailed metadata for a single property on a node",
        _GET_PROPERTY_METADATA_SCRIPT,
    ),
    # Phase 1: Lighting presets
    "vangard-apply-lighting-preset": (
        "Create a professional lighting setup (three-point, rembrandt, butterfly, split, loop)",
        _APPLY_LIGHTING_PRESET_SCRIPT,
    ),
    # Phase 1: Scene validation
    "vangard-validate-scene": (
        "Validate scene for common issues: collisions, lighting, camera, figure presence",
        _VALIDATE_SCENE_SCRIPT,
    ),
    # Phase 1.5: Render quality preset (used by daz_set_render_quality)
    "vangard-set-render-quality": (
        "Set Iray render quality preset (draft/preview/good/final) via Max Samples and Render Quality properties",
        _SET_RENDER_QUALITY_SCRIPT,
    ),
    # Phase 2: Emotional direction
    "vangard-set-emotion": (
        "Apply emotion morphs and body language adjustments to a character",
        _SET_EMOTION_SCRIPT,
    ),
    # Phase 2: Content library
    "vangard-list-categories": (
        "List content library subdirectories under a parent path across all content directories",
        _LIST_CATEGORIES_SCRIPT,
    ),
    "vangard-browse-category": (
        "List .duf files in a content library category path across all content directories",
        _BROWSE_CATEGORY_SCRIPT,
    ),
    # Phase 2: Scene composition
    "vangard-apply-composition-rule": (
        "Position camera to frame subject using a photography composition rule",
        _APPLY_COMPOSITION_RULE_SCRIPT,
    ),
    "vangard-frame-shot": (
        "Frame camera to subject using a standard cinematic shot type",
        _FRAME_SHOT_SCRIPT,
    ),
    "vangard-apply-camera-angle": (
        "Apply a standard camera angle preset relative to a subject",
        _APPLY_CAMERA_ANGLE_SCRIPT,
    ),
    # Phase 2: Checkpoint system
    "vangard-save-scene-state": (
        "Serialize all node transforms, morphs, and light properties for checkpoint storage",
        _SAVE_SCENE_STATE_SCRIPT,
    ),
    "vangard-restore-scene-state": (
        "Restore node transforms, morphs, and light properties from a checkpoint snapshot",
        _RESTORE_SCENE_STATE_SCRIPT,
    ),
    # Phase 2: Scene layout & proximity
    "vangard-get-scene-layout": (
        "Get spatial map of all scene nodes (figures, cameras, lights, props) with positions and bounds",
        _GET_SCENE_LAYOUT_SCRIPT,
    ),
    "vangard-find-nearby-nodes": (
        "Find all nodes within a radius of a target node",
        _FIND_NEARBY_NODES_SCRIPT,
    ),
    "vangard-create-shot-sequence": (
        "Create multi-camera shot sequence for cinematic workflows",
        _CREATE_SHOT_SEQUENCE_SCRIPT,
    ),
    "vangard-animate-conversation": (
        "Choreograph animated conversation between two characters with look-at and emotion keyframes",
        _ANIMATE_CONVERSATION_SCRIPT,
    ),
    "vangard-create-scene": (
        "Generate a complete scene from natural language description with lighting, cameras, and positioning",
        _CREATE_SCENE_SCRIPT,
    ),
    "vangard-animate-camera-movement": (
        "Animate common camera movements (dolly, pan, tilt, crane, shake) with keyframes",
        _ANIMATE_CAMERA_MOVEMENT_SCRIPT,
    ),
    "vangard-create-camera-path": (
        "Create smooth camera path through multiple waypoints with easing",
        _CREATE_CAMERA_PATH_SCRIPT,
    ),
    "vangard-create-character-path": (
        "Animate character movement along a path with waypoints",
        _CREATE_CHARACTER_PATH_SCRIPT,
    ),
    "vangard-arrange-characters": (
        "Position multiple characters in formation (line, semicircle, triangle, circle)",
        _ARRANGE_CHARACTERS_SCRIPT,
    ),
    "vangard-choreograph-action": (
        "Choreograph simple action between characters (handshake, hug, fight, dance)",
        _CHOREOGRAPH_ACTION_SCRIPT,
    ),
    "vangard-setup-shot-coverage": (
        "Create multiple camera angles for cinematic coverage of a subject",
        _SETUP_SHOT_COVERAGE_SCRIPT,
    ),
    "vangard-create-camera-rig": (
        "Set up multi-camera rig in circular formation for bullet-time or multi-angle shots",
        _CREATE_CAMERA_RIG_SCRIPT,
    ),
}


# ---------------------------------------------------------------------------
# Phase 2: Python-side emotion definitions and checkpoint state
# ---------------------------------------------------------------------------

# Emotion → list of {names: [...], value: float} (first match per list wins)
# Multiple candidate names handle morph naming differences across figure generations.
_EMOTION_DEFINITIONS: dict[str, dict] = {
    "happy": {
        "morphs": [
            {"names": ["PHMSmile", "Smile", "CTRLSmile", "MouthSmile", "SmileSimple"], "value": 0.85},
            {"names": ["PHMEyesSquint", "EyesSquint", "EyeSquintL", "SquintEyes"], "value": 0.25},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": 3.0}],
    },
    "sad": {
        "morphs": [
            {"names": ["PHMFrown", "Frown", "MouthFrown", "CTRLFrown", "FrownSimple"], "value": 0.75},
            {"names": ["PHMBrowInnerDown", "BrowDownL", "BrowDown", "CTRLBrowDown", "BrowInnerDown"], "value": 0.6},
            {"names": ["PHMEyesSquint", "EyesSquint", "EyeSquintL"], "value": 0.3},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": -6.0}],
    },
    "angry": {
        "morphs": [
            {"names": ["PHMFrown", "Frown", "MouthFrown", "CTRLFrown"], "value": 0.5},
            {"names": ["PHMBrowDown", "BrowDown", "BrowDownLeft", "CTRLBrowDown", "BrowDownR"], "value": 0.85},
            {"names": ["PHMNoseWrinkle", "NoseWrinkle", "NoseSneerL", "NoseSneer"], "value": 0.4},
            {"names": ["PHMEyesTighten", "EyesTighten", "EyeSquintL", "CheekSquintL"], "value": 0.4},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": -3.0}],
    },
    "surprised": {
        "morphs": [
            {"names": ["PHMBrowUp", "BrowUp", "BrowInnerUpL", "CTRLBrowUp", "BrowsUp"], "value": 0.85},
            {"names": ["PHMEyesWide", "EyesWide", "EyeOpenL", "EyeWideL"], "value": 0.75},
            {"names": ["PHMMouthOpen", "MouthOpen", "CTRLMouthOpen", "JawOpen"], "value": 0.6},
        ],
        "body": [],
    },
    "fearful": {
        "morphs": [
            {"names": ["PHMBrowUp", "BrowUp", "BrowInnerUpL", "CTRLBrowUp"], "value": 0.7},
            {"names": ["PHMEyesWide", "EyesWide", "EyeOpenL", "EyeWideL"], "value": 0.6},
            {"names": ["PHMMouthOpen", "MouthOpen", "CTRLMouthOpen", "JawOpen"], "value": 0.3},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": -4.0}],
    },
    "disgusted": {
        "morphs": [
            {"names": ["PHMNoseWrinkle", "NoseWrinkle", "NoseSneerL", "NoseSneer"], "value": 0.75},
            {"names": ["PHMFrown", "Frown", "MouthFrown", "CTRLFrown"], "value": 0.4},
            {"names": ["PHMUpperLipUp", "UpperLipUp", "MouthUpperUp_L", "LipUpperUp_L"], "value": 0.3},
        ],
        "body": [],
    },
    "neutral": {
        "morphs": [],
        "body": [],
    },
    "excited": {
        "morphs": [
            {"names": ["PHMSmile", "Smile", "CTRLSmile", "MouthSmile"], "value": 1.0},
            {"names": ["PHMBrowUp", "BrowUp", "CTRLBrowUp", "BrowsUp"], "value": 0.5},
            {"names": ["PHMEyesWide", "EyesWide", "EyeOpenL"], "value": 0.4},
            {"names": ["PHMMouthOpen", "MouthOpen", "CTRLMouthOpen", "JawOpen"], "value": 0.4},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": 5.0}],
    },
    "bored": {
        "morphs": [
            {"names": ["PHMEyesClosed", "EyesClosed", "EyeClosedL", "CTRLEyesClosed"], "value": 0.4},
            {"names": ["PHMFrown", "Frown", "MouthFrown"], "value": 0.2},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": -4.0}],
    },
    "confident": {
        "morphs": [
            {"names": ["PHMSmile", "Smile", "MouthSmile", "CTRLSmile"], "value": 0.3},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": 4.0}],
    },
    "shy": {
        "morphs": [
            {"names": ["PHMSmile", "Smile", "MouthSmile"], "value": 0.2},
            {"names": ["PHMEyesSquint", "EyesSquint", "EyeSquintL"], "value": 0.15},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": -5.0}],
    },
    "loving": {
        "morphs": [
            {"names": ["PHMSmile", "Smile", "MouthSmile", "CTRLSmile"], "value": 0.6},
            {"names": ["PHMEyesSquint", "EyesSquint", "EyeSquintL"], "value": 0.35},
        ],
        "body": [{"bone": "chestUpper", "property": "XRotate", "value": 2.0}],
    },
    "contemptuous": {
        "morphs": [
            {"names": ["PHMSmileR", "SmileR", "MouthSmileR", "MouthSmile_R"], "value": 0.5},
            {"names": ["PHMFrownL", "FrownL", "MouthFrownL", "MouthFrown_L"], "value": 0.3},
        ],
        "body": [],
    },
}

# In-memory checkpoint store: {name → {"nodes": [...], "timestamp": int}}
_CHECKPOINTS: dict[str, dict] = {}


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

    Scripts run in the DAZ Studio JavaScript environment. Global objects:
    Scene (DzScene), App (DzApp), MainWindow.

    ⚠️ CRITICAL GOTCHAS - READ BEFORE WRITING SCRIPTS:

    1. ❌ NEVER use Action classes (DzNewCameraAction, DzNewLightAction, etc.)
       They pop modal dialogs and cause TIMEOUTS.
       ✅ Use direct constructors: new DzBasicCamera(), new DzSpotLight()

    2. ❌ NEVER set "Point At" property for camera/light aiming.
       ✅ Use: node.aimAt(new DzVec3(x, y, z))

    3. ✅ Wrap scripts returning values in IIFE:
       (function(){ return Scene.getNumNodes(); })()

    4. ✅ Environment node is ALWAYS Scene.getNode(1) - not findNodeByLabel()

    For detailed examples and documentation, use the daz_script_help tool first.

    Args:
        script: DazScript (JavaScript) source code to execute.
        args: Optional JSON object accessible in script as `args` variable.

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


@mcp.tool()
async def daz_script_help(topic: str = "overview") -> str:
    """Get DazScript documentation, examples, and best practices.

    Use this tool BEFORE writing DazScript to learn correct patterns and avoid
    common mistakes. Topics cover critical gotchas, working examples, and
    detailed API references.

    Available topics:
    - overview: DazScript environment basics
    - gotchas: Critical mistakes that cause timeouts or incorrect results
    - camera: Camera creation, positioning, and aiming
    - light: Light creation, types, and three-point lighting setup
    - environment: Iray environment settings and lighting modes
    - scene: Scene management (new, save, load, selection)
    - properties: Node properties, transforms, and morphs
    - content: Browsing and loading content from library
    - coordinates: Coordinate system and positioning reference
    - posing: Figure posing, bone hierarchy, morphs vs poses, rotation gotchas
    - morphs: Morph discovery, searching, value ranges, and management
    - hierarchy: Scene hierarchy, parent-child relationships, parenting operations
    - interaction: Multi-character interaction, look-at mechanics, world-space posing
    - batch: Batch operations for efficient multi-node/multi-property modifications
    - viewport: Viewport and camera control, positioning, framing, presets
    - animation: Animation system, keyframing, timeline control, rendering animations
    - rendering: Advanced rendering control, multi-camera, batch rendering, animation export

    Args:
        topic: Documentation topic to retrieve (default: "overview")

    Returns:
        Formatted documentation with examples for the requested topic.
    """
    if topic not in _DAZSCRIPT_DOCS:
        available = ", ".join(sorted(_DAZSCRIPT_DOCS.keys()))
        return f"Unknown topic: '{topic}'\n\nAvailable topics: {available}"

    doc = _DAZSCRIPT_DOCS[topic]
    title = doc.get("title", topic.title())
    content = doc.get("content", "No content available.")

    return f"# {title}\n\n{content}"


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


# ---------------------------------------------------------------------------
# Tools — morph discovery and management
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_list_morphs(
    node_label: str,
    include_zero: bool = False,
) -> dict[str, Any]:
    """List all morphs (numeric properties) on a node.

    Returns all numeric properties on a node, which includes morphs (body shapes,
    facial expressions), transforms, and other numeric dials. Useful for discovering
    what morphs are available on a figure.

    Args:
        node_label: Display label or internal name of the node (e.g., "Genesis 9").
        include_zero: If True, return all morphs including those set to 0.
                      If False (default), only return morphs with non-zero values
                      (currently active morphs).

    Returns:
      - morphs: List of morph objects with:
        - label: Display label (e.g., "Head Size")
        - name: Internal name (e.g., "HeadSize")
        - value: Current numeric value
        - path: Property path for organization (e.g., "Morphs/Head")
      - count: Number of morphs returned
      - nodeLabel: Confirmed node label

    Example:
        # List only active morphs on Genesis 9
        result = daz_list_morphs("Genesis 9", include_zero=False)
        # result["morphs"] = [
        #   {"label": "Height", "name": "Height", "value": 1.05, "path": "Morphs/Body"},
        #   {"label": "Head Size", "name": "HeadSize", "value": 0.9, "path": "Morphs/Head"}
        # ]

        # List all available morphs (including zero values)
        result = daz_list_morphs("Genesis 9", include_zero=True)
        # result["count"] might be 500+ morphs
    """
    return await _execute_by_id("vangard-list-morphs", {
        "nodeLabel": node_label,
        "includeZero": include_zero,
    })


@mcp.tool()
async def daz_search_morphs(
    node_label: str,
    pattern: str,
    include_zero: bool = False,
) -> dict[str, Any]:
    """Search for morphs matching a name pattern.

    Search through all numeric properties (morphs) on a node for those matching
    a substring pattern. Useful for finding specific morphs like all facial
    expressions, body morphs, or morphs for a specific body part.

    Args:
        node_label: Display label or internal name of the node (e.g., "Genesis 9").
        pattern: Substring to search for in morph label or name (case-insensitive).
                 Examples: "smile", "head", "muscle", "express"
        include_zero: If True, return all matching morphs including zero values.
                      If False (default), only return matching morphs that are active.

    Returns:
      - morphs: List of matching morph objects with:
        - label: Display label
        - name: Internal name
        - value: Current value
        - path: Property path
      - count: Number of matching morphs
      - pattern: The search pattern used
      - nodeLabel: Confirmed node label

    Example:
        # Find all smile-related morphs
        result = daz_search_morphs("Genesis 9", "smile", include_zero=True)
        # result["morphs"] might include: "Smile", "Smile Open", "Smile Closed", etc.

        # Find active head morphs
        result = daz_search_morphs("Genesis 9", "head", include_zero=False)
        # Only returns head morphs with non-zero values

        # Find all facial expression morphs
        result = daz_search_morphs("Genesis 9", "express", include_zero=True)
    """
    return await _execute_by_id("vangard-search-morphs", {
        "nodeLabel": node_label,
        "pattern": pattern,
        "includeZero": include_zero,
    })


# ---------------------------------------------------------------------------
# Tools — scene hierarchy and node relationships
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_get_node_hierarchy(
    node_label: str,
    max_depth: int = 10,
) -> dict[str, Any]:
    """Get complete hierarchy tree for a node with all descendants.

    Returns the full hierarchical structure of a node, including all children,
    grandchildren, etc. Useful for understanding skeleton structure, bone
    relationships, and complex scene hierarchies.

    Args:
        node_label: Display label or internal name of the root node.
        max_depth: Maximum recursion depth (default 10, 0 = unlimited).
                   Use to limit deep hierarchies (e.g., Genesis 9 skeleton has 100+ bones).

    Returns:
      - node: Root node label
      - hierarchy: Nested structure with:
        - label: Node display label
        - name: Internal name
        - type: DazScript class name
        - children: List of child hierarchies (recursive)
      - totalDescendants: Total number of descendants

    Example:
        # Get skeleton hierarchy with depth limit
        result = daz_get_node_hierarchy("Genesis 9", max_depth=3)
        # Returns nested structure: hip -> abdomen -> chest -> ...

        # Get full hierarchy (warning: can be large)
        result = daz_get_node_hierarchy("Genesis 9", max_depth=0)
        # Returns complete skeleton with all 100+ bones

        # Get prop hierarchy
        result = daz_get_node_hierarchy("Sword", max_depth=5)
    """
    return await _execute_by_id("vangard-get-node-hierarchy", {
        "nodeLabel": node_label,
        "maxDepth": max_depth,
    })


@mcp.tool()
async def daz_list_children(node_label: str) -> dict[str, Any]:
    """List direct children of a node.

    Returns only the immediate children (not grandchildren). Useful for
    exploring hierarchy one level at a time or checking if a node has children.

    Args:
        node_label: Display label or internal name of the parent node.

    Returns:
      - node: Parent node label
      - children: List of child objects with:
        - label: Child display label
        - name: Child internal name
        - type: DazScript class name
      - count: Number of children

    Example:
        # List children of Genesis 9 root
        result = daz_list_children("Genesis 9")
        # Returns: [{"label": "hip", "name": "hip", "type": "DzBone"}]

        # Check if node has children
        result = daz_list_children("Camera 1")
        # result["count"] == 0 means no children

        # List bones under hip
        result = daz_list_children("hip")
        # Returns: pelvis, lThighBend, rThighBend
    """
    return await _execute_by_id("vangard-list-children", {
        "nodeLabel": node_label,
    })


@mcp.tool()
async def daz_get_parent(node_label: str) -> dict[str, Any]:
    """Get parent node of a node.

    Returns the immediate parent of a node, or null if the node is a root node
    (no parent). Useful for traversing hierarchy upward.

    Args:
        node_label: Display label or internal name of the child node.

    Returns:
      - node: Child node label
      - parent: Parent node object with label, name, type, or null if no parent

    Example:
        # Get parent of a bone
        result = daz_get_parent("lHand")
        # Returns: {"parent": {"label": "lForearmBend", "name": "lForearmBend", ...}}

        # Check if node is root (has no parent)
        result = daz_get_parent("Genesis 9")
        # result["parent"] == null

        # Traverse hierarchy upward
        node = "lIndex3"
        while True:
            result = daz_get_parent(node)
            if not result["parent"]:
                break
            print(f"Parent of {node}: {result['parent']['label']}")
            node = result["parent"]["label"]
    """
    return await _execute_by_id("vangard-get-parent", {
        "nodeLabel": node_label,
    })


@mcp.tool()
async def daz_set_parent(
    node_label: str,
    parent_label: str,
    maintain_world_transform: bool = True,
) -> dict[str, Any]:
    """Set parent of a node (parenting operation).

    Changes the parent of a node, effectively moving it in the scene hierarchy.
    Commonly used to attach props to figures (e.g., weapon to hand) or reorganize
    scene structure.

    Args:
        node_label: Display label or internal name of node to parent.
        parent_label: Display label or internal name of new parent.
        maintain_world_transform: If True (default), adjust local transform to
                                  maintain the same world-space position/rotation.
                                  If False, keep local transform (node will move
                                  in world space).

    Returns:
      - success: true on success
      - node: Node label
      - newParent: New parent label
      - previousParent: Previous parent label (or null if was root)

    Example:
        # Attach sword to right hand (maintain position)
        result = daz_set_parent("Sword", "rHand", maintain_world_transform=True)
        # Sword stays in place, now follows hand movements

        # Parent camera to figure (follows figure)
        result = daz_set_parent("Camera 1", "Genesis 9", maintain_world_transform=True)

        # Unparent node (make it root) - parent to Scene root
        result = daz_set_parent("Prop", "Scene", maintain_world_transform=True)

    Note:
        When maintain_world_transform=True, the node's world position is preserved,
        but its local transform values (X/Y/Z Translate, Rotate) will change to
        account for the new parent's transform.
    """
    return await _execute_by_id("vangard-set-parent", {
        "nodeLabel": node_label,
        "parentLabel": parent_label,
        "maintainWorldTransform": maintain_world_transform,
    })


# ---------------------------------------------------------------------------
# Tools — multi-character interaction (advanced posing)
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_look_at_point(
    character_label: str,
    target_x: float,
    target_y: float,
    target_z: float,
    mode: str = "head",
) -> dict[str, Any]:
    """Make character look at a world-space point with configurable body involvement.

    This helper uses cascading rotations from eyes through the body to create
    natural-looking character attention. Different modes control how much of
    the body participates in the look direction.

    Args:
        character_label: Display label or internal name of the character figure.
        target_x: World X coordinate (cm) to look at.
        target_y: World Y coordinate (cm) to look at.
        target_z: World Z coordinate (cm) to look at.
        mode: How much body to involve in the look. Options:
              - "eyes": Only rotate eyes
              - "head": Eyes + head rotation (default)
              - "neck": Eyes + head + neck
              - "torso": Eyes + head + neck + chest
              - "full": Complete body rotation including hip

    Returns:
      - success: true on success
      - character: character label
      - mode: the mode used
      - rotatedBones: list of bone labels that were rotated

    Example:
        # Character looks at point in front of them at eye level
        daz_look_at_point("Genesis 9", 0, 160, 200, mode="head")

        # Full body turn to look behind
        daz_look_at_point("Genesis 9", 0, 140, -150, mode="full")
    """
    return await _execute_by_id("vangard-look-at-point", {
        "characterLabel": character_label,
        "targetX": target_x,
        "targetY": target_y,
        "targetZ": target_z,
        "mode": mode,
    })


@mcp.tool()
async def daz_look_at_character(
    source_label: str,
    target_label: str,
    mode: str = "head",
) -> dict[str, Any]:
    """Make one character look at another character's face.

    Automatically finds the target character's head position and rotates
    the source character to look at it using cascading body rotations.

    Args:
        source_label: Display label of the character who will look.
        target_label: Display label of the character to look at.
        mode: How much body to involve. Options:
              - "eyes": Only rotate eyes
              - "head": Eyes + head rotation (default)
              - "neck": Eyes + head + neck
              - "torso": Eyes + head + neck + chest
              - "full": Complete body rotation including hip

    Returns:
      - success: true on success
      - source: source character label
      - target: target character label
      - mode: the mode used
      - targetPosition: {x, y, z} world coordinates of target's head
      - rotatedBones: list of bone labels that were rotated

    Example:
        # Alice looks at Bob with head turn
        daz_look_at_character("Alice", "Bob", mode="head")

        # Bob turns his whole body to face Alice
        daz_look_at_character("Bob", "Alice", mode="full")
    """
    return await _execute_by_id("vangard-look-at-character", {
        "sourceLabel": source_label,
        "targetLabel": target_label,
        "mode": mode,
    })


@mcp.tool()
async def daz_reach_toward(
    character_label: str,
    side: str,
    target_x: float,
    target_y: float,
    target_z: float,
) -> dict[str, Any]:
    """Position character's arm to reach toward a world-space point.

    Uses pseudo-IK approximation to calculate shoulder and elbow rotations
    that position the hand near the target point. Automatically adjusts
    elbow bend based on target distance.

    Args:
        character_label: Display label or internal name of the character.
        side: Which arm to use: "left" or "right".
        target_x: World X coordinate (cm) to reach toward.
        target_y: World Y coordinate (cm) to reach toward.
        target_z: World Z coordinate (cm) to reach toward.

    Returns:
      - success: true on success
      - character: character label
      - side: which arm was posed
      - targetDistance: distance in cm from shoulder to target
      - bones: list of bone labels that were rotated

    Example:
        # Reach right hand toward point in front at chest height
        daz_reach_toward("Genesis 9", "right", 50, 130, 80)

        # Reach left hand toward object on left side
        daz_reach_toward("Genesis 9", "left", -60, 100, 50)

    Note:
        This uses simplified IK approximation. For precise hand positioning
        or complex reaching, load an artist-created pose preset instead.
    """
    return await _execute_by_id("vangard-reach-toward", {
        "characterLabel": character_label,
        "side": side,
        "targetX": target_x,
        "targetY": target_y,
        "targetZ": target_z,
    })


@mcp.tool()
async def daz_interactive_pose(
    char1_label: str,
    char2_label: str,
    interaction_type: str = "face-each-other",
    distance: float | None = None,
) -> dict[str, Any]:
    """Coordinate two characters for interactive poses.

    Applies complementary poses to two characters for common interaction
    scenarios. Handles both positioning and pose application.

    Args:
        char1_label: Display label of first character.
        char2_label: Display label of second character.
        interaction_type: Type of interaction. Options:
            - "face-each-other": Position and rotate to face each other (default)
            - "hug": Both characters hug with arms around each other
            - "shoulder-arm": Char1 puts arm around char2's shoulders
            - "handshake": Both extend right hands for handshake
        distance: Optional spacing between characters in cm (default varies by type:
                  face=100, hug=40, shoulder-arm=30, handshake=60).

    Returns:
      - success: true on success
      - char1: first character label
      - char2: second character label
      - interactionType: the interaction type used
      - applied: list of pose components that were applied

    Example:
        # Position characters facing each other at conversation distance
        daz_interactive_pose("Alice", "Bob", "face-each-other", distance=120)

        # Create tight hug
        daz_interactive_pose("Alice", "Bob", "hug", distance=30)

        # Bob puts arm around Alice's shoulders
        daz_interactive_pose("Bob", "Alice", "shoulder-arm")

    Note:
        These are simplified interaction poses. For natural-looking results,
        you may need to fine-tune positions and rotations using daz_set_property
        or load artist-created pose presets.
    """
    args: dict[str, Any] = {
        "char1Label": char1_label,
        "char2Label": char2_label,
        "interactionType": interaction_type,
    }
    if distance is not None:
        args["distance"] = distance

    return await _execute_by_id("vangard-interactive-pose", args)


# ---------------------------------------------------------------------------
# Tools — batch operations
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_batch_set_properties(
    operations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Set multiple properties on one or more nodes in a single call.

    Executes multiple property-setting operations with individual error handling.
    Failed operations don't abort the entire batch - each operation returns
    success status and error details.

    Args:
        operations: List of operation objects, each containing:
            - nodeLabel (str): Display label of the node
            - propertyName (str): Property label or internal name
            - value (float): New value for the property

    Returns:
      - results: Array of result objects with success, node, property, value, error
      - successCount: Number of successful operations
      - failureCount: Number of failed operations
      - total: Total number of operations attempted

    Example:
        # Set multiple properties on different nodes
        daz_batch_set_properties([
            {"nodeLabel": "Genesis 9", "propertyName": "XTranslate", "value": 100},
            {"nodeLabel": "Genesis 9", "propertyName": "YRotate", "value": 45},
            {"nodeLabel": "Camera 1", "propertyName": "ZTranslate", "value": 300}
        ])

        # Apply multiple morphs to a character
        daz_batch_set_properties([
            {"nodeLabel": "Genesis 9", "propertyName": "PHMSmile", "value": 0.5},
            {"nodeLabel": "Genesis 9", "propertyName": "PHMEyesWide", "value": 0.3},
            {"nodeLabel": "Genesis 9", "propertyName": "PHMBrowsUp", "value": 0.4}
        ])

    Note:
        This is significantly more efficient than calling daz_set_property
        individually for each operation. All operations execute in a single
        script call to DAZ Studio.
    """
    return await _execute_by_id("vangard-batch-set-properties", {"operations": operations})


@mcp.tool()
async def daz_batch_transform(
    node_labels: list[str],
    transforms: dict[str, float],
) -> dict[str, Any]:
    """Apply the same transform properties to multiple nodes.

    Useful for moving, rotating, or scaling multiple objects by the same amount.
    Only properties that exist on each node are applied (missing properties
    are silently skipped).

    Args:
        node_labels: List of node display labels to transform.
        transforms: Dictionary of property names to values (e.g., {"XTranslate": 50, "YRotate": 45}).

    Returns:
      - results: Array of result objects with success, node, applied properties, error
      - successCount: Number of nodes successfully transformed
      - failureCount: Number of nodes that failed
      - total: Total number of nodes attempted

    Example:
        # Move multiple props to the right
        daz_batch_transform(
            ["Prop1", "Prop2", "Prop3"],
            {"XTranslate": 100}
        )

        # Rotate and scale multiple objects
        daz_batch_transform(
            ["Chair", "Table", "Lamp"],
            {"YRotate": 45, "Scale": 1.2}
        )

        # Reset rotation for all cameras
        daz_batch_transform(
            ["Camera 1", "Camera 2", "Camera 3"],
            {"XRotate": 0, "YRotate": 0, "ZRotate": 0}
        )

    Note:
        Transform properties include: XTranslate, YTranslate, ZTranslate,
        XRotate, YRotate, ZRotate, Scale, XScale, YScale, ZScale.
    """
    return await _execute_by_id(
        "vangard-batch-transform",
        {"nodeLabels": node_labels, "transforms": transforms}
    )


@mcp.tool()
async def daz_batch_visibility(
    node_labels: list[str],
    visible: bool = True,
) -> dict[str, Any]:
    """Show or hide multiple nodes in the viewport and renders.

    Args:
        node_labels: List of node display labels to modify.
        visible: True to show nodes, False to hide them (default: True).

    Returns:
      - results: Array of result objects with success, node, visible state, error
      - successCount: Number of nodes successfully modified
      - failureCount: Number of nodes that failed
      - total: Total number of nodes attempted

    Example:
        # Hide all cameras
        daz_batch_visibility(["Camera 1", "Camera 2", "Camera 3"], visible=False)

        # Show multiple props
        daz_batch_visibility(["Sword", "Shield", "Helmet"], visible=True)

        # Hide environment elements for character close-up
        daz_batch_visibility(["Ground", "Sky Dome", "Background"], visible=False)

    Note:
        Hidden nodes are not visible in the viewport or renders, but remain
        in the scene. Use this for scene management, testing different
        configurations, or optimizing render times.
    """
    return await _execute_by_id(
        "vangard-batch-visibility",
        {"nodeLabels": node_labels, "visible": visible}
    )


@mcp.tool()
async def daz_batch_select(
    node_labels: list[str],
    add_to_selection: bool = False,
) -> dict[str, Any]:
    """Select multiple nodes in the DAZ Studio scene.

    Args:
        node_labels: List of node display labels to select.
        add_to_selection: If True, add to current selection; if False, replace
                          current selection (default: False).

    Returns:
      - selected: Array of node labels that were successfully selected
      - count: Number of nodes selected
      - total: Total number of node labels provided

    Example:
        # Select multiple characters
        daz_batch_select(["Genesis 9", "Genesis 8 Female"])

        # Add props to current selection
        daz_batch_select(["Sword", "Shield"], add_to_selection=True)

        # Select all lights in scene
        daz_batch_select(["Spot Light 1", "Distant Light 1", "Point Light 1"])

    Note:
        Selection affects which nodes appear in the Scene/Parameters panes
        in DAZ Studio. Some operations apply to the current selection.
        Nodes that don't exist are silently skipped.
    """
    return await _execute_by_id(
        "vangard-batch-select",
        {"nodeLabels": node_labels, "addToSelection": add_to_selection}
    )


# ---------------------------------------------------------------------------
# Tools — viewport and camera control
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_set_active_camera(camera_label: str) -> dict[str, Any]:
    """Set which camera is active in the DAZ Studio viewport.

    Changes the active viewport camera to show the scene from the specified
    camera's perspective. The previous active camera is returned for reference.

    Args:
        camera_label: Display label of the camera to activate.

    Returns:
      - success: true on success
      - camera: label of the camera that was activated
      - previousCamera: label of the previously active camera (or null)

    Example:
        # Switch to a specific camera
        daz_set_active_camera("Camera 1")

        # Switch to a custom camera
        daz_set_active_camera("Close Up Camera")

        # Switch back to default camera
        daz_set_active_camera("Perspective View")

    Note:
        The camera must exist in the scene. Use daz_scene_info() to list
        available cameras. The viewport updates immediately to show the
        camera's current view.
    """
    return await _execute_by_id("vangard-set-active-camera", {"cameraLabel": camera_label})


@mcp.tool()
async def daz_orbit_camera_around(
    camera_label: str,
    target_label: str,
    distance: float = 200.0,
    angle_horizontal: float = 45.0,
    angle_vertical: float = 15.0,
) -> dict[str, Any]:
    """Position camera orbiting around a target node at specified angle and distance.

    Uses spherical coordinates to position the camera at a specific angle around
    a target object. The camera is automatically aimed at the target after positioning.

    Args:
        camera_label: Display label of the camera to position.
        target_label: Display label of the target node to orbit around.
        distance: Distance from target in centimeters (default: 200).
        angle_horizontal: Horizontal angle in degrees, 0=front/+Z, 90=right/+X (default: 45).
        angle_vertical: Vertical angle in degrees, positive=above, negative=below (default: 15).

    Returns:
      - success: true on success
      - camera: camera label
      - target: target node label
      - position: camera world position {x, y, z}
      - targetPosition: target world position {x, y, z}

    Example:
        # Position camera at 45° to the right, slightly above, 200cm away
        daz_orbit_camera_around("Camera 1", "Genesis 9", distance=200,
                                angle_horizontal=45, angle_vertical=15)

        # Side view from the left
        daz_orbit_camera_around("Camera 1", "Genesis 9", distance=150,
                                angle_horizontal=-90, angle_vertical=0)

        # Bird's eye view
        daz_orbit_camera_around("Camera 1", "Genesis 9", distance=300,
                                angle_horizontal=0, angle_vertical=60)

        # Dramatic low angle
        daz_orbit_camera_around("Camera 1", "Genesis 9", distance=180,
                                angle_horizontal=25, angle_vertical=-20)

    Note:
        Angles use spherical coordinates:
        - Horizontal: 0°=front(+Z), 90°=right(+X), 180°=back(-Z), -90°=left(-X)
        - Vertical: positive=above horizon, negative=below

        Camera is automatically aimed at the target's world position after positioning.
    """
    return await _execute_by_id(
        "vangard-orbit-camera-around",
        {
            "cameraLabel": camera_label,
            "targetLabel": target_label,
            "distance": distance,
            "angleHorizontal": angle_horizontal,
            "angleVertical": angle_vertical,
        }
    )


@mcp.tool()
async def daz_frame_camera_to_node(
    camera_label: str,
    node_label: str,
    distance: float | None = None,
) -> dict[str, Any]:
    """Frame camera to show a node by positioning at calculated distance.

    Positions the camera to frame the specified node in view. Calculates the
    node's bounding box and positions the camera at an appropriate distance
    to show the entire object. Camera is positioned in front (+Z) and aimed
    at the node's center.

    Args:
        camera_label: Display label of the camera to position.
        node_label: Display label of the node to frame.
        distance: Optional distance from node center in cm. If not specified,
                  calculated as 2.5x the largest dimension of the node's bounding box.

    Returns:
      - success: true on success
      - camera: camera label
      - node: node label
      - position: camera world position {x, y, z}
      - nodeCenter: node bounding box center {x, y, z}
      - nodeSize: node bounding box size {x, y, z}

    Example:
        # Frame a character (auto distance)
        daz_frame_camera_to_node("Camera 1", "Genesis 9")

        # Frame a prop with specific distance
        daz_frame_camera_to_node("Camera 1", "Sword", distance=50)

        # Frame entire scene
        daz_frame_camera_to_node("Camera 1", "Scene", distance=500)

        # Close-up on head
        daz_frame_camera_to_node("Camera 1", "head", distance=30)

    Note:
        - Auto-calculated distance is 2.5x the largest bounding box dimension
        - Camera is positioned in front of the node (+Z direction)
        - Camera is aimed at the center of the node's bounding box
        - Useful for automatically framing objects of varying sizes
    """
    args: dict[str, Any] = {
        "cameraLabel": camera_label,
        "nodeLabel": node_label,
    }
    if distance is not None:
        args["distance"] = distance

    return await _execute_by_id("vangard-frame-camera-to-node", args)


@mcp.tool()
async def daz_save_camera_preset(camera_label: str) -> dict[str, Any]:
    """Save camera position and rotation as preset data.

    Captures the current transform properties of a camera (position, rotation,
    scale) and returns them as preset data. This data can be saved by the client
    and later restored using daz_load_camera_preset().

    Args:
        camera_label: Display label of the camera to save.

    Returns:
      - preset: Dictionary containing:
        - label: camera label
        - transforms: Dictionary of property names to values (XTranslate, YTranslate,
                     ZTranslate, XRotate, YRotate, ZRotate, XScale, YScale, ZScale)

    Example:
        # Save camera position
        preset = daz_save_camera_preset("Camera 1")

        # Client can store preset data (e.g., in a file or database)
        import json
        with open("my_camera_preset.json", "w") as f:
            json.dump(preset, f)

        # Later, restore the camera
        with open("my_camera_preset.json") as f:
            preset = json.load(f)
        daz_load_camera_preset("Camera 1", preset["preset"])

    Note:
        - Preset data is a plain dictionary that can be serialized (JSON, etc.)
        - Includes all transform properties (position, rotation, scale)
        - Does not include camera-specific settings (focal length, DOF, etc.)
        - Preset data can be applied to any camera, not just the original
    """
    return await _execute_by_id("vangard-save-camera-preset", {"cameraLabel": camera_label})


@mcp.tool()
async def daz_load_camera_preset(camera_label: str, preset: dict[str, Any]) -> dict[str, Any]:
    """Restore camera position and rotation from preset data.

    Applies saved preset data (from daz_save_camera_preset()) to a camera,
    restoring its position, rotation, and scale.

    Args:
        camera_label: Display label of the camera to modify.
        preset: Preset dictionary from daz_save_camera_preset(), containing:
                - transforms: Dictionary of property names to values

    Returns:
      - success: true on success
      - camera: camera label
      - applied: list of property names that were applied

    Example:
        # Load previously saved preset
        with open("my_camera_preset.json") as f:
            preset = json.load(f)

        result = daz_load_camera_preset("Camera 1", preset["preset"])
        print(f"Applied properties: {result['applied']}")

        # Apply same preset to multiple cameras
        cameras = ["Camera 1", "Camera 2", "Camera 3"]
        for cam in cameras:
            daz_load_camera_preset(cam, preset["preset"])

    Note:
        - Preset can be applied to any camera, not just the original
        - Only properties present in the preset are modified
        - Useful for saving/loading camera positions across sessions
        - Can be used to synchronize multiple cameras
    """
    return await _execute_by_id(
        "vangard-load-camera-preset",
        {"cameraLabel": camera_label, "preset": preset}
    )


# ---------------------------------------------------------------------------
# Tools — animation system
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_set_keyframe(
    node_label: str,
    property_name: str,
    frame: int,
    value: float,
) -> dict[str, Any]:
    """Set a keyframe on a property at specified frame.

    Creates or updates a keyframe for a numeric property at the given frame number.
    This is the fundamental operation for creating property animations.

    Args:
        node_label: Display label of the node.
        property_name: Property label or internal name.
        frame: Frame number (integer, typically 0-based).
        value: Value to set at this frame.

    Returns:
      - success: true on success
      - node: node label
      - property: property label
      - frame: frame number
      - value: value set at the keyframe

    Example:
        # Animate character moving right (0 to 100cm over 30 frames)
        daz_set_keyframe("Genesis 9", "XTranslate", frame=0, value=0)
        daz_set_keyframe("Genesis 9", "XTranslate", frame=30, value=100)

        # Animate rotation (0 to 90 degrees over 60 frames)
        daz_set_keyframe("Genesis 9", "YRotate", frame=0, value=0)
        daz_set_keyframe("Genesis 9", "YRotate", frame=60, value=90)

        # Animate morph (fade in smile)
        daz_set_keyframe("Genesis 9", "PHMSmile", frame=0, value=0)
        daz_set_keyframe("Genesis 9", "PHMSmile", frame=15, value=0.8)

    Note:
        - DAZ Studio interpolates between keyframes automatically
        - Setting a keyframe at an existing frame updates the value
        - Frames are typically 0-based integers
        - Use daz_set_frame_range() to define the animation length first
    """
    return await _execute_by_id(
        "vangard-set-keyframe",
        {
            "nodeLabel": node_label,
            "propertyName": property_name,
            "frame": frame,
            "value": value,
        }
    )


@mcp.tool()
async def daz_get_keyframes(
    node_label: str,
    property_name: str,
) -> dict[str, Any]:
    """Get all keyframes for a property.

    Returns all keyframes currently set on a property, including frame numbers
    and values. Useful for inspecting existing animations or copying keyframes.

    Args:
        node_label: Display label of the node.
        property_name: Property label or internal name.

    Returns:
      - keyframes: Array of {frame, value} objects
      - count: Number of keyframes

    Example:
        # Get keyframes for a property
        result = daz_get_keyframes("Genesis 9", "XTranslate")
        print(f"Found {result['count']} keyframes:")
        for kf in result['keyframes']:
            print(f"  Frame {kf['frame']}: {kf['value']}")

        # Copy keyframes to another property
        keyframes = daz_get_keyframes("Genesis 9", "XTranslate")
        for kf in keyframes['keyframes']:
            daz_set_keyframe("Genesis 8", "XTranslate", kf['frame'], kf['value'])

        # Check if property is animated
        result = daz_get_keyframes("Genesis 9", "YRotate")
        if result['count'] > 0:
            print("Property is animated")

    Note:
        - Returns empty array if property has no keyframes
        - Keyframes are returned in frame order
        - Frame numbers are integers, values are floats
    """
    return await _execute_by_id(
        "vangard-get-keyframes",
        {"nodeLabel": node_label, "propertyName": property_name}
    )


@mcp.tool()
async def daz_remove_keyframe(
    node_label: str,
    property_name: str,
    frame: int,
) -> dict[str, Any]:
    """Remove a keyframe at specified frame.

    Deletes a single keyframe from a property at the given frame number.
    Other keyframes on the property remain unchanged.

    Args:
        node_label: Display label of the node.
        property_name: Property label or internal name.
        frame: Frame number of keyframe to remove.

    Returns:
      - success: true
      - node: node label
      - property: property label
      - frame: frame number
      - removed: true if keyframe existed and was removed, false if no keyframe at that frame

    Example:
        # Remove specific keyframe
        daz_remove_keyframe("Genesis 9", "XTranslate", frame=15)

        # Remove all keyframes one by one
        keyframes = daz_get_keyframes("Genesis 9", "XTranslate")
        for kf in keyframes['keyframes']:
            daz_remove_keyframe("Genesis 9", "XTranslate", kf['frame'])

    Note:
        - If no keyframe exists at the frame, removed=false (not an error)
        - Other keyframes remain unchanged
        - Use daz_clear_animation() to remove all keyframes at once
    """
    return await _execute_by_id(
        "vangard-remove-keyframe",
        {"nodeLabel": node_label, "propertyName": property_name, "frame": frame}
    )


@mcp.tool()
async def daz_clear_animation(
    node_label: str,
    property_name: str,
) -> dict[str, Any]:
    """Remove all keyframes from a property.

    Clears all animation data from a property, returning it to a static (non-animated)
    state. More efficient than removing keyframes individually.

    Args:
        node_label: Display label of the node.
        property_name: Property label or internal name.

    Returns:
      - success: true
      - node: node label
      - property: property label
      - removed: number of keyframes removed

    Example:
        # Clear animation from a property
        result = daz_clear_animation("Genesis 9", "XTranslate")
        print(f"Removed {result['removed']} keyframes")

        # Clear all transform animations
        transforms = ["XTranslate", "YTranslate", "ZTranslate",
                      "XRotate", "YRotate", "ZRotate"]
        for prop in transforms:
            daz_clear_animation("Genesis 9", prop)

    Note:
        - Removes all keyframes in a single operation
        - More efficient than calling daz_remove_keyframe() repeatedly
        - Property retains its current value after clearing
        - Returns count of keyframes that were removed
    """
    return await _execute_by_id(
        "vangard-clear-animation",
        {"nodeLabel": node_label, "propertyName": property_name}
    )


@mcp.tool()
async def daz_set_frame(frame: int) -> dict[str, Any]:
    """Set current animation frame.

    Moves the timeline to the specified frame. This updates the scene to show
    the state at that frame, evaluating all animated properties.

    Args:
        frame: Frame number to move to (integer).

    Returns:
      - success: true
      - frame: new current frame
      - previousFrame: frame number before the change

    Example:
        # Jump to specific frame
        daz_set_frame(30)

        # Render each frame of animation
        info = daz_get_animation_info()
        for frame in range(info['startFrame'], info['endFrame'] + 1):
            daz_set_frame(frame)
            daz_render(output_path=f"frame_{frame:04d}.png")

        # Preview keyframes
        keyframes = daz_get_keyframes("Genesis 9", "XTranslate")
        for kf in keyframes['keyframes']:
            daz_set_frame(kf['frame'])
            # ... preview or inspect ...

    Note:
        - Scene updates to show animated state at the frame
        - All animated properties evaluate at the new frame
        - Frame numbers are typically 0-based integers
        - Use with daz_render() to export animation frames
    """
    return await _execute_by_id("vangard-set-frame", {"frame": frame})


@mcp.tool()
async def daz_set_frame_range(start_frame: int, end_frame: int) -> dict[str, Any]:
    """Set animation frame range (start and end).

    Defines the playback range for the animation timeline. This determines
    which frames are included when playing or exporting animation.

    Args:
        start_frame: First frame of animation (typically 0).
        end_frame: Last frame of animation.

    Returns:
      - success: true
      - startFrame: new start frame
      - endFrame: new end frame
      - previousStart: previous start frame
      - previousEnd: previous end frame

    Example:
        # Set 120-frame animation (4 seconds at 30fps)
        daz_set_frame_range(0, 119)

        # Set 300-frame animation (10 seconds at 30fps)
        daz_set_frame_range(0, 299)

        # Set custom range starting from frame 10
        daz_set_frame_range(10, 100)

    Note:
        - Frame range is inclusive (both start and end frames are included)
        - Default FPS in DAZ Studio is typically 30
        - Duration in seconds = (end - start + 1) / fps
        - Example: frames 0-29 at 30fps = 1 second (30 frames)
    """
    return await _execute_by_id(
        "vangard-set-frame-range",
        {"startFrame": start_frame, "endFrame": end_frame}
    )


@mcp.tool()
async def daz_get_animation_info() -> dict[str, Any]:
    """Get animation timeline info (current frame, range, fps).

    Returns information about the current animation timeline state, including
    the current frame, frame range, and frames per second.

    Returns:
      - currentFrame: current timeline position
      - startFrame: first frame of animation range
      - endFrame: last frame of animation range
      - fps: frames per second
      - totalFrames: total number of frames (endFrame - startFrame + 1)
      - durationSeconds: animation duration in seconds

    Example:
        # Get timeline info
        info = daz_get_animation_info()
        print(f"Current frame: {info['currentFrame']}")
        print(f"Range: {info['startFrame']}-{info['endFrame']}")
        print(f"Duration: {info['durationSeconds']} seconds")
        print(f"FPS: {info['fps']}")

        # Render entire animation
        info = daz_get_animation_info()
        for frame in range(info['startFrame'], info['endFrame'] + 1):
            daz_set_frame(frame)
            daz_render(output_path=f"output/frame_{frame:04d}.png")

        # Check if at end of animation
        info = daz_get_animation_info()
        if info['currentFrame'] >= info['endFrame']:
            print("At end of animation")

    Note:
        - FPS is typically 30 in DAZ Studio
        - Frame range is inclusive (both start and end are included)
        - totalFrames includes both start and end frames
        - Use before rendering animation to know frame count
    """
    return await _execute_by_id("vangard-get-animation-info", {})


# ---------------------------------------------------------------------------
# Tools — advanced rendering control
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_render_with_camera(
    camera_label: str,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Render from specific camera without changing active viewport camera.

    Renders the scene from the specified camera's viewpoint. The viewport camera
    remains unchanged, making this ideal for multi-camera renders without
    disrupting the user's viewport.

    Args:
        camera_label: Display label of the camera to render from.
        output_path: Optional output file path. If not specified, renders to viewport.

    Returns:
      - success: true on success
      - camera: camera label used for render
      - outputPath: output file path (or null if rendered to viewport)

    Example:
        # Render from specific camera
        daz_render_with_camera("Camera 1", output_path="/path/to/render.png")

        # Render from multiple cameras without changing viewport
        cameras = ["Front", "Side", "Top", "Perspective"]
        for cam in cameras:
            daz_render_with_camera(cam, output_path=f"renders/{cam}.png")

        # Test render from camera (to viewport, no file)
        daz_render_with_camera("Camera 1")

    Note:
        - Viewport camera remains unchanged after render
        - Previous render camera is restored automatically
        - Use for multi-camera batch renders
        - Combine with daz_orbit_camera_around() to set up camera first
    """
    args: dict[str, Any] = {"cameraLabel": camera_label}
    if output_path is not None:
        args["outputPath"] = output_path

    return await _execute_by_id("vangard-render-with-camera", args)


@mcp.tool()
async def daz_get_render_settings() -> dict[str, Any]:
    """Get current render settings and configuration.

    Returns information about the current render configuration, including
    render target, output path, aspect ratio, and render camera.

    Returns:
      - renderToFile: true if rendering to file, false if to viewport
      - outputPath: current output file path (or null)
      - currentCamera: label of current render camera (or null for viewport camera)
      - aspectRatio: aspect ratio value
      - aspectWidth: aspect width component
      - aspectHeight: aspect height component

    Example:
        # Check render settings
        settings = daz_get_render_settings()
        print(f"Render camera: {settings['currentCamera']}")
        print(f"Output: {settings['outputPath']}")
        print(f"Aspect: {settings['aspectWidth']}x{settings['aspectHeight']}")

        # Verify render is configured correctly before batch render
        settings = daz_get_render_settings()
        if not settings['renderToFile']:
            print("Warning: Render is configured for viewport, not file output")

    Note:
        - Aspect ratio determines render dimensions relative to each other
        - Pixel dimensions cannot be set reliably via DazScript
        - currentCamera may be null if using active viewport camera
    """
    return await _execute_by_id("vangard-get-render-settings", {})


@mcp.tool()
async def daz_batch_render_cameras(
    cameras: list[str],
    output_dir: str,
    base_filename: str = "render",
) -> dict[str, Any]:
    """Render from multiple cameras in sequence.

    Renders the same scene from multiple camera angles in a single operation.
    Each camera generates a separate output file with the camera name appended.

    Args:
        cameras: List of camera labels to render from.
        output_dir: Output directory for rendered images.
        base_filename: Base filename (default: "render"). Camera name is appended automatically.

    Returns:
      - success: true on success
      - rendered: Array of {camera, outputPath} objects
      - total: Total number of cameras attempted

    Example:
        # Render from multiple preset cameras
        daz_batch_render_cameras(
            cameras=["Front", "Side", "Top", "Perspective"],
            output_dir="/path/to/renders",
            base_filename="character"
        )
        # Generates: character_Front.png, character_Side.png, etc.

        # Render turntable (8 cameras around character)
        cameras = [f"Cam_{angle}" for angle in [0, 45, 90, 135, 180, 225, 270, 315]]
        daz_batch_render_cameras(cameras, "/path/to/turntable", "frame")

        # Render all cameras in scene
        scene_info = daz_scene_info()
        all_cameras = [cam['label'] for cam in scene_info['cameras']]
        daz_batch_render_cameras(all_cameras, "/path/to/renders")

    Note:
        - Camera names in filenames have non-alphanumeric chars replaced with underscores
        - All renders use current scene state (same lighting, poses, etc.)
        - Previous render camera is restored after batch completes
        - Cameras that don't exist are skipped
    """
    return await _execute_by_id(
        "vangard-batch-render-cameras",
        {
            "cameras": cameras,
            "outputDir": output_dir,
            "baseFilename": base_filename,
        }
    )


@mcp.tool()
async def daz_render_animation(
    output_dir: str,
    start_frame: int | None = None,
    end_frame: int | None = None,
    filename_pattern: str = "frame",
    camera: str | None = None,
) -> dict[str, Any]:
    """Render animation frame range as image sequence.

    Renders each frame of an animation to separate image files. Automatically
    advances through frames and generates zero-padded filenames for proper
    sorting. This is the recommended way to export animations.

    Args:
        output_dir: Output directory for rendered frames.
        start_frame: First frame to render (default: animation range start).
        end_frame: Last frame to render (default: animation range end).
        filename_pattern: Filename pattern (default: "frame"). Frame number is appended.
        camera: Optional camera label to render from (default: current render camera).

    Returns:
      - success: true on success
      - rendered: Array of {frame, outputPath} objects
      - total: Total number of frames rendered
      - frames: {start, end} frame range rendered

    Example:
        # Render entire animation
        daz_render_animation(output_dir="/path/to/animation")
        # Generates: frame_0000.png, frame_0001.png, ..., frame_0119.png

        # Render specific frame range
        daz_render_animation(
            output_dir="/path/to/animation",
            start_frame=30,
            end_frame=60,
            filename_pattern="clip"
        )

        # Render animation from specific camera
        daz_render_animation(
            output_dir="/path/to/animation",
            camera="Camera 1"
        )

        # Render preview (every 5th frame)
        info = daz_get_animation_info()
        for frame in range(info['startFrame'], info['endFrame'] + 1, 5):
            daz_render_animation(
                output_dir="/path/to/preview",
                start_frame=frame,
                end_frame=frame,
                filename_pattern=f"preview_frame"
            )

    Note:
        - Frame numbers are zero-padded to 4 digits (0000, 0001, etc.)
        - Current timeline frame is restored after render completes
        - If camera is specified, render camera is restored after completion
        - Use daz_get_animation_info() to get default frame range
        - Convert to video: ffmpeg -framerate 30 -i frame_%04d.png output.mp4
    """
    args: dict[str, Any] = {
        "outputDir": output_dir,
        "filenamePattern": filename_pattern,
    }
    if start_frame is not None:
        args["startFrame"] = start_frame
    if end_frame is not None:
        args["endFrame"] = end_frame
    if camera is not None:
        args["camera"] = camera

    return await _execute_by_id("vangard-render-animation", args)


# ---------------------------------------------------------------------------
# Tools — Phase 1: Spatial Queries
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_get_world_position(node_label: str) -> dict[str, Any]:
    """Get world-space position, local position, rotation, and scale of a node.

    Useful for understanding where nodes are in 3D space before making
    relative positioning decisions.

    Args:
        node_label: Display label of the node (e.g. "Genesis 9", "Camera 1")

    Returns:
        {
            "node": "Genesis 9",
            "world_position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "local_position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
            "scale": {"x": 1.0, "y": 1.0, "z": 1.0}
        }
    """
    return await _execute_by_id("vangard-get-world-position", {"nodeLabel": node_label})


@mcp.tool()
async def daz_get_bounding_box(node_label: str) -> dict[str, Any]:
    """Get the axis-aligned bounding box of a node.

    Returns min/max corners, center point, and dimensions. Use this to
    auto-calculate camera distance, detect collisions, or anchor lights
    relative to a character's actual size.

    Args:
        node_label: Display label of the node

    Returns:
        {
            "node": "Genesis 9",
            "min": {"x": -30.0, "y": 0.0, "z": -15.0},
            "max": {"x": 30.0, "y": 175.0, "z": 15.0},
            "center": {"x": 0.0, "y": 87.5, "z": 0.0},
            "width": 60.0,
            "height": 175.0,
            "depth": 30.0
        }
    """
    return await _execute_by_id("vangard-get-bounding-box", {"nodeLabel": node_label})


@mcp.tool()
async def daz_calculate_distance(
    node1_label: str,
    node2_label: str,
) -> dict[str, Any]:
    """Calculate the distance between two nodes.

    Returns total distance, horizontal distance, vertical distance, and the
    direction vector. All distances in centimeters.

    Args:
        node1_label: Display label of the first node
        node2_label: Display label of the second node

    Returns:
        {
            "node1": "Genesis 9",
            "node2": "Camera 1",
            "distance": 250.5,
            "vector": {"dx": 0.0, "dy": 50.0, "dz": 245.0},
            "horizontal_distance": 245.0,
            "vertical_distance": 50.0
        }
    """
    return await _execute_by_id("vangard-calculate-distance", {
        "node1Label": node1_label,
        "node2Label": node2_label,
    })


@mcp.tool()
async def daz_get_spatial_relationship(
    node1_label: str,
    node2_label: str,
) -> dict[str, Any]:
    """Get the spatial relationship between two nodes in natural language.

    Returns direction (front, back, left, right, above, below), angles,
    distance, and whether their bounding boxes overlap.

    Horizontal angle uses DAZ coordinate system: 0°=front(+Z for Genesis figures),
    90°=right(+X), 180°=back(-Z), -90°=left(-X).

    Args:
        node1_label: The reference node (e.g. "Genesis 9")
        node2_label: The target node to describe relative to node1 (e.g. "Camera 1")

    Returns:
        {
            "node1": "Genesis 9",
            "node2": "Camera 1",
            "distance": 250.5,
            "direction": "front",
            "angle_horizontal": 5.0,
            "angle_vertical": 12.0,
            "relative_position": "Camera 1 is front above of Genesis 9 (250 cm away)",
            "overlapping": false
        }
    """
    return await _execute_by_id("vangard-get-spatial-relationship", {
        "node1Label": node1_label,
        "node2Label": node2_label,
    })


@mcp.tool()
async def daz_check_overlap(
    node1_label: str,
    node2_label: str,
) -> dict[str, Any]:
    """Check if two nodes have overlapping bounding boxes (collision detection).

    Uses axis-aligned bounding box (AABB) intersection. Returns whether they
    overlap, the penetration depth, and a suggestion for resolving the collision.

    Args:
        node1_label: Display label of the first node
        node2_label: Display label of the second node

    Returns:
        {
            "node1": "Alice",
            "node2": "Bob",
            "overlapping": true,
            "penetration_depth": 15.0,
            "suggestion": "Move Bob 20 cm in +X direction to resolve collision"
        }
    """
    return await _execute_by_id("vangard-check-overlap", {
        "node1Label": node1_label,
        "node2Label": node2_label,
    })


# ---------------------------------------------------------------------------
# Tools — Phase 1: Property Introspection
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_inspect_properties(
    node_label: str,
    property_type: str = "all",
) -> dict[str, Any]:
    """List all properties on a node with their types, values, and constraints.

    Use this to discover what properties are available on a node before
    using daz_set_property. Much more reliable than guessing property names.

    Args:
        node_label: Display label of the node
        property_type: Filter type — one of:
            "all"       - all properties
            "numeric"   - all numeric (float/bool) properties
            "transform" - XTranslate/YTranslate/ZTranslate/XRotate/YRotate/ZRotate/Scale
            "morph"     - numeric properties that are not transforms
            "bool"      - boolean properties only
            "string"    - string properties only

    Returns:
        {
            "node": "Spotlight 1",
            "properties": [
                {
                    "label": "Luminous Flux (Lumen)",
                    "name": "Flux",
                    "type": "DzFloatProperty",
                    "value": 1500.0,
                    "min": 0.0,
                    "max": 100000.0,
                    "path": "Light/Photometrics",
                    "is_animatable": true
                }
            ],
            "count": 45
        }
    """
    return await _execute_by_id("vangard-inspect-properties", {
        "nodeLabel": node_label,
        "propertyType": property_type,
    })


@mcp.tool()
async def daz_get_property_metadata(
    node_label: str,
    property_name: str,
) -> dict[str, Any]:
    """Get detailed metadata for a single named property on a node.

    Accepts either the display label (e.g. "Luminous Flux (Lumen)") or the
    internal name (e.g. "Flux"). Use this to validate a value is within
    min/max range before setting it.

    Args:
        node_label: Display label of the node
        property_name: Property label or internal name

    Returns:
        {
            "label": "Luminous Flux (Lumen)",
            "name": "Flux",
            "type": "DzFloatProperty",
            "current_value": 1500.0,
            "default_value": 1500.0,
            "min": 0.0,
            "max": 100000.0,
            "is_animatable": true,
            "path": "Light/Photometrics",
            "node": "Spotlight 1"
        }
    """
    return await _execute_by_id("vangard-get-property-metadata", {
        "nodeLabel": node_label,
        "propertyName": property_name,
    })


@mcp.tool()
async def daz_validate_script(script: str) -> dict[str, Any]:
    """Check a DazScript string for known anti-patterns before execution.

    Performs static analysis only — no script is sent to DAZ Studio.
    Returns errors for known crash/timeout patterns and warnings for
    deprecated or error-prone usage.

    Args:
        script: DazScript (JavaScript) source code to validate

    Returns:
        {
            "valid": false,
            "errors": [
                {
                    "line": 3,
                    "pattern": "DzNewCameraAction",
                    "message": "Action classes pop modal dialogs and cause timeouts",
                    "suggestion": "Use: var cam = new DzBasicCamera(); Scene.addNode(cam);"
                }
            ],
            "warnings": [...],
            "suggestions": [...]
        }
    """
    lines = script.splitlines()
    errors = []
    warnings_list = []
    suggestions = []

    _ANTI_PATTERNS = [
        # (regex_fragment, is_error, message, suggestion)
        (
            "DzNewCameraAction",
            True,
            "Action classes pop modal dialogs and cause timeouts",
            "Use: var cam = new DzBasicCamera(); Scene.addNode(cam);",
        ),
        (
            "DzNewLightAction",
            True,
            "Action classes pop modal dialogs and cause timeouts",
            "Use: var light = new DzSpotLight(); Scene.addNode(light);",
        ),
        (
            r'findProperty\s*\(\s*["\']Point At["\']',
            True,
            "'Point At' property does not link nodes correctly via setValue",
            "Use: node.aimAt(new DzVec3(x, y, z));",
        ),
        (
            r"DzFileInfo\s*\(",
            True,
            "DzFileInfo constructor is not available in the scripting environment",
            "Use DzDir or App.getContentMgr() for file operations",
        ),
        (
            r"^\s*return\s",
            True,
            "Bare top-level return is not allowed in DazScript",
            "Wrap the script in an IIFE: (function(){ return ...; })()",
        ),
        (
            r"getElementID\s*\(",
            False,
            "node.getElementID() is not a method — elementID is a property",
            "Use: node.elementID  (not node.getElementID())",
        ),
        (
            r"setImageSize\s*\(",
            False,
            "setImageSize() is not reliably exposed in DazScript",
            "Set image dimensions in DAZ Studio UI instead",
        ),
        (
            r"Scene\.findNode\s*\(",
            False,
            "Scene.findNode() matches by internal name; multiple nodes can share a name",
            "Prefer Scene.findNodeByLabel() for unique label-based lookup",
        ),
    ]

    import re

    has_iife = "(function()" in script or "(function (" in script

    for line_idx, line in enumerate(lines, start=1):
        for pattern, is_error, message, suggestion in _ANTI_PATTERNS:
            if re.search(pattern, line):
                entry = {
                    "line": line_idx,
                    "pattern": pattern,
                    "message": message,
                    "suggestion": suggestion,
                }
                if is_error:
                    errors.append(entry)
                else:
                    warnings_list.append(entry)

    if "return" in script and not has_iife:
        suggestions.append(
            "Script uses 'return' but is not wrapped in an IIFE — "
            "wrap in (function(){ ... })() to return values to the caller"
        )

    if "Scene.getNumNodes()" in script:
        suggestions.append(
            "Avoid iterating all nodes via getNumNodes() — scenes can have 3000+ nodes. "
            "Use Scene.findNodeByLabel(), getNumSkeletons(), getNumCameras(), or getNumLights() instead"
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings_list,
        "suggestions": suggestions,
    }


# ---------------------------------------------------------------------------
# Tools — Phase 1: Lighting Presets & Scene Validation
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_apply_lighting_preset(
    preset: str,
    subject_label: str | None = None,
) -> dict[str, Any]:
    """Create a professional photography lighting setup in one command.

    Removes any existing lights with the same names, creates new lights
    at positions calculated relative to the subject's bounding box,
    aims each light at the subject's face height, and sets the environment
    to scene-lights-only mode (disables the dome).

    Available presets:
        three-point  - Key (front-right) + Fill (front-left) + Rim (back).
                       The most versatile general-purpose lighting setup.
        rembrandt    - Key (45° side, high) + dim Fill. Creates triangle of
                       light under opposite eye. Dramatic portrait lighting.
        butterfly    - Key directly in front, high. Glamour/beauty lighting.
                       Creates butterfly shadow under the nose.
        split        - Key directly to one side (90°). Half face lit, half in
                       shadow. Moody, high-contrast.
        loop         - Key (35° side) + Fill + Rim. Natural-looking portrait.
                       Small loop shadow on opposite cheek.

    Args:
        preset: Lighting preset name (see above)
        subject_label: Optional node label to anchor lights around. If omitted,
                       lights are placed relative to scene origin at 170cm height.

    Returns:
        {
            "preset": "three-point",
            "subject": "Genesis 9",
            "lights_created": [
                {"label": "Key Light", "type": "DzSpotLight",
                 "position": {"x": 150, "y": 180, "z": 150}, "flux": 2000}
            ],
            "environment_mode": "Scene Only (3)"
        }
    """
    args: dict[str, Any] = {"preset": preset}
    if subject_label is not None:
        args["subjectLabel"] = subject_label
    return await _execute_by_id("vangard-apply-lighting-preset", args)


@mcp.tool()
async def daz_validate_scene() -> dict[str, Any]:
    """Validate the current scene for common issues before rendering.

    Checks:
    - Character/figure bounding box collisions (interpenetration)
    - Lighting presence and quality
    - Camera presence
    - Empty scene (no figures)

    Returns a score (0-100) and breakdown by category, plus actionable
    suggestions for any issues found.

    Returns:
        {
            "valid": true,
            "issues": [
                {
                    "type": "collision",
                    "severity": "high",
                    "nodes": ["Alice", "Bob"],
                    "description": "Alice and Bob bounding boxes overlap by ~15 cm",
                    "suggestion": "Move one character away to resolve interpenetration"
                }
            ],
            "warnings": [...],
            "score": 75,
            "score_breakdown": {
                "lighting": 100,
                "collision": 30,
                "camera": 100,
                "figures": 100
            },
            "summary": {
                "figures": 2,
                "cameras": 1,
                "lights": 3,
                "environment_lighting": false
            }
        }
    """
    return await _execute_by_id("vangard-validate-scene")


# ---------------------------------------------------------------------------
# Tools — Phase 1.5: Async Operations
#
# These tools return immediately with a request_id.  The actual script runs
# serially on DAZ Studio's main thread (DAZ is single-threaded).
#
# Typical workflow:
#   req = await daz_render_async("/renders/final.png")
#   result = await daz_get_request_result(req["request_id"], wait=True)
#
# Or with polling:
#   req = await daz_render_async("/renders/final.png")
#   while True:
#       status = await daz_get_request_status(req["request_id"])
#       if status["status"] in ("completed", "failed", "cancelled"):
#           break
#       await asyncio.sleep(5)
#
# IMPORTANT: While a render is running, DAZ Studio's scene is locked.
# Do not attempt to modify the scene until the request has completed.
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_render_async(
    output_path: str | None = None,
) -> dict[str, Any]:
    """Start a render asynchronously — returns immediately with a request_id.

    Use daz_get_request_status() to poll progress and daz_get_request_result()
    to retrieve the final result.

    IMPORTANT: The scene is locked while the render runs. Do not modify the
    scene until the request status is "completed", "failed", or "cancelled".

    Args:
        output_path: Optional file path for the rendered image.

    Returns:
        {"request_id": "script-XXXXXXXX", "status": "queued", "submitted_at": "..."}
    """
    args: dict[str, Any] = {}
    if output_path is not None:
        args["outputPath"] = output_path
    return await _execute_by_id_async("vangard-render", args)


@mcp.tool()
async def daz_render_with_camera_async(
    camera_label: str,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Start a camera-specific render asynchronously — returns immediately with a request_id.

    Renders from the specified camera without changing the active viewport camera.
    Use daz_get_request_status() to poll and daz_get_request_result() for the result.

    Args:
        camera_label: Display label of the camera to render from.
        output_path: Optional file path for the rendered image.

    Returns:
        {"request_id": "script-XXXXXXXX", "status": "queued", "submitted_at": "..."}
    """
    args: dict[str, Any] = {"cameraLabel": camera_label}
    if output_path is not None:
        args["outputPath"] = output_path
    return await _execute_by_id_async("vangard-render-with-camera", args)


@mcp.tool()
async def daz_batch_render_cameras_async(
    cameras: list[str],
    output_dir: str,
    base_filename: str = "render",
) -> dict[str, Any]:
    """Queue renders from multiple cameras — each becomes its own async request.

    Submits one async render per camera and returns all request IDs immediately.
    Renders execute serially (DAZ is single-threaded), so they queue behind any
    already-running request. Each camera render is independently cancellable.

    Args:
        cameras: List of camera display labels.
        output_dir: Directory where rendered images are saved.
        base_filename: Filename prefix. Output is <base_filename>_<camera>.png.

    Returns:
        {
            "request_ids": ["script-XXXXXXXX", ...],
            "total": 3,
            "cameras": ["Cam_0", "Cam_45", "Cam_90"]
        }

    Example:
        batch = await daz_batch_render_cameras_async(
            cameras=["Cam_0", "Cam_45", "Cam_90"],
            output_dir="/renders/turntable"
        )
        # Monitor all renders
        for req_id in batch["request_ids"]:
            result = await daz_get_request_result(req_id, wait=True)
    """
    import os as _os
    request_ids: list[str] = []
    for cam in cameras:
        output_path = _os.path.join(output_dir, f"{base_filename}_{cam}.png")
        result = await _execute_by_id_async(
            "vangard-render-with-camera",
            {"cameraLabel": cam, "outputPath": output_path},
        )
        request_ids.append(result["request_id"])

    return {
        "request_ids": request_ids,
        "total": len(request_ids),
        "cameras": cameras,
    }


@mcp.tool()
async def daz_render_animation_async(
    output_dir: str,
    start_frame: int | None = None,
    end_frame: int | None = None,
    filename_pattern: str = "frame",
    camera: str | None = None,
) -> dict[str, Any]:
    """Start an animation render asynchronously — returns immediately with a request_id.

    Queues a full animation render (all frames as an image sequence). This can
    take hours; use daz_get_request_status() to monitor progress and
    daz_get_request_result() to confirm completion.

    Args:
        output_dir: Directory where frame images are saved.
        start_frame: First frame (default: animation range start).
        end_frame: Last frame (default: animation range end).
        filename_pattern: Filename prefix (default: "frame"). Frame number appended.
        camera: Optional camera label (default: current render camera).

    Returns:
        {"request_id": "script-XXXXXXXX", "status": "queued", "submitted_at": "..."}
    """
    args: dict[str, Any] = {
        "outputDir": output_dir,
        "filenamePattern": filename_pattern,
    }
    if start_frame is not None:
        args["startFrame"] = start_frame
    if end_frame is not None:
        args["endFrame"] = end_frame
    if camera is not None:
        args["camera"] = camera
    return await _execute_by_id_async("vangard-render-animation", args)


@mcp.tool()
async def daz_get_request_status(request_id: str) -> dict[str, Any]:
    """Get the current status of an async request (non-blocking, always fast).

    Safe to call frequently — reads directly from the server's in-memory map
    without executing any DazScript.

    Args:
        request_id: Request ID returned by an async submission tool.

    Returns:
        {
            "request_id": "script-XXXXXXXX",
            "status": "running",   # queued | running | completed | failed | cancelled
            "progress": 0.0,       # 0.0 while running (DAZ single-frame renders have no
                                   # mid-frame progress), 1.0 when complete
            "elapsed_ms": 45000,   # present while running
            "queue_position": 2    # present while queued
        }
    """
    client = _get_client()
    try:
        response = await client.get(f"/requests/{request_id}/status")
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        _handle_network_error(exc)
    if response.status_code == 404:
        raise ToolError(f"Request not found: {request_id}")
    _check_response(response)
    return response.json()


@mcp.tool()
async def daz_get_request_result(
    request_id: str,
    wait: bool = True,
    timeout_seconds: int = 3600,
) -> dict[str, Any]:
    """Get the result of a completed async request.

    Args:
        request_id: Request ID returned by an async submission tool.
        wait: If True (default), block until the request finishes (up to timeout).
              If False, return immediately with current status even if not done.
        timeout_seconds: Max seconds to wait when wait=True (default 3600 = 1 hour).

    Returns when complete:
        {
            "request_id": "script-XXXXXXXX",
            "status": "completed",
            "success": true,
            "result": {...},        # same as sync tool result
            "output": [...],        # captured DazScript print() output
            "error": null,
            "duration_ms": 267000,
            "completed_at": "2026-04-08T..."
        }

    Raises ToolError if the request failed.
    """
    client = _get_client()
    params: dict[str, Any] = {
        "wait": "true" if wait else "false",
        "timeout": timeout_seconds,
    }
    try:
        response = await client.get(
            f"/requests/{request_id}/result",
            params=params,
            timeout=timeout_seconds + 10.0,  # slightly longer than server timeout
        )
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        _handle_network_error(exc)
    _check_response(response)

    data = response.json()
    status = data.get("status", "unknown")
    if status == "failed":
        raise ToolError(f"Async request failed: {data.get('error', 'unknown error')}")
    if status == "cancelled":
        raise ToolError("Async request was cancelled")
    return data


@mcp.tool()
async def daz_cancel_request(request_id: str) -> dict[str, Any]:
    """Cancel a queued or running async request.

    For queued requests: cancellation is immediate.
    For running renders: sends a killRender() signal; may take a few seconds
    to take effect.

    Args:
        request_id: Request ID returned by an async submission tool.

    Returns:
        {"request_id": "...", "status": "cancelled", "cancelled_at": "..."}

    Raises ToolError if the request is already finished (completed/failed/cancelled)
    or not found.
    """
    client = _get_client()
    try:
        response = await client.delete(f"/requests/{request_id}")
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        _handle_network_error(exc)
    _check_response(response)
    return response.json()


@mcp.tool()
async def daz_list_requests(
    status_filter: str | None = None,
) -> dict[str, Any]:
    """List all tracked async requests and their current statuses.

    Args:
        status_filter: Optional filter — one of "queued", "running",
                       "completed", "failed", "cancelled". Returns all if omitted.

    Returns:
        {
            "requests": [
                {"request_id": "...", "status": "...", "progress": 0.0, "submitted_at": "..."},
                ...
            ],
            "total": 5,
            "queued": 2,
            "running": 1,
            "completed": 2,
            "failed": 0,
            "cancelled": 0
        }
    """
    client = _get_client()
    params: dict[str, Any] = {}
    if status_filter is not None:
        params["status"] = status_filter
    try:
        response = await client.get("/requests", params=params)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        _handle_network_error(exc)
    _check_response(response)
    return response.json()


@mcp.tool()
async def daz_set_render_quality(preset: str) -> dict[str, Any]:
    """Set the Iray render quality preset.

    Adjusts Max Samples and Render Quality on the active renderer, trading
    speed for quality. Use "draft" for quick composition checks and "final"
    for production renders.

    Presets:
        draft   - Very fast (seconds–2 min). Low quality. For quick checks.
        preview - Fast (2–5 min). Moderate quality. For composition review.
        good    - Slow (10–20 min). Good quality. For client review.
        final   - Very slow (30 min–2 hr). Maximum quality. For final output.

    Args:
        preset: One of "draft", "preview", "good", "final".

    Returns:
        {
            "preset": "draft",
            "propertiesSet": [
                {"property": "Max Samples", "value": 100},
                {"property": "Render Quality", "value": 0.5}
            ],
            "note": "..."    # present only if some properties were not found
        }

    Example:
        # Quick test render
        daz_set_render_quality("draft")
        daz_render("/test.png")

        # Final quality async render
        daz_set_render_quality("final")
        req = await daz_render_async("/final.png")
        result = await daz_get_request_result(req["request_id"], wait=True)
    """
    _presets: dict[str, dict[str, float]] = {
        "draft":   {"maxSamples": 100,  "renderQuality": 0.5},
        "preview": {"maxSamples": 500,  "renderQuality": 0.75},
        "good":    {"maxSamples": 2000, "renderQuality": 0.9},
        "final":   {"maxSamples": 5000, "renderQuality": 1.0},
    }
    if preset not in _presets:
        valid = ", ".join(f'"{k}"' for k in _presets)
        raise ToolError(f"Unknown render quality preset: '{preset}'. Valid presets: {valid}")

    args = {"preset": preset, **_presets[preset]}
    return await _execute_by_id("vangard-set-render-quality", args)


# ---------------------------------------------------------------------------
# Non-tool helper — daz_wait_for_request
#
# Not exposed as an MCP tool (no @mcp.tool() decorator).  Intended for use
# in Python scripts that coordinate multiple async operations.
# ---------------------------------------------------------------------------

async def daz_wait_for_request(
    request_id: str,
    poll_interval_seconds: float = 5.0,
    timeout_seconds: float = 3600.0,
) -> dict[str, Any]:
    """Poll an async request until it completes (or times out).

    Polls daz_get_request_status() every poll_interval_seconds until the
    request reaches a terminal state, then returns the full result.

    Args:
        request_id: Request ID from an async submission tool.
        poll_interval_seconds: Seconds between status checks (default 5).
        timeout_seconds: Maximum total wait time (default 3600 = 1 hour).

    Returns:
        Full result dict from daz_get_request_result() on success.

    Raises:
        ToolError: If the request failed or was cancelled.
        asyncio.TimeoutError: If the timeout is exceeded.
    """
    import time
    deadline = time.monotonic() + timeout_seconds

    while True:
        status = await daz_get_request_status(request_id)
        state = status.get("status", "unknown")

        if state == "completed":
            return await daz_get_request_result(request_id, wait=False)
        if state == "failed":
            raise ToolError(f"Async request failed: {status.get('error', 'unknown error')}")
        if state == "cancelled":
            raise ToolError("Async request was cancelled")

        if time.monotonic() >= deadline:
            raise asyncio.TimeoutError(
                f"Async request {request_id!r} did not complete within {timeout_seconds}s"
            )

        await asyncio.sleep(poll_interval_seconds)


# ---------------------------------------------------------------------------
# Tools — Phase 2: Emotional direction
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_set_emotion(
    character_label: str,
    emotion: str,
    intensity: float = 0.7,
) -> dict[str, Any]:
    """Apply an emotional expression to a character using morph candidates + body adjustment.

    Args:
        character_label: Node label of the character to affect.
        emotion: One of: happy, sad, angry, surprised, fearful, disgusted, neutral,
                 excited, bored, confident, shy, loving, contemptuous.
        intensity: Scale factor 0.0–1.0 applied to all morph and body values (default 0.7).

    Returns:
        Dict with applied_morphs, body_adjustments, and not_found lists.

    Notes:
        Morph candidates are tried in order; first match per slot wins. Not-found morphs
        are reported but do not raise errors — figures vary in available morphs.
    """
    valid = sorted(_EMOTION_DEFINITIONS.keys())
    if emotion not in _EMOTION_DEFINITIONS:
        raise ToolError(
            f"Unknown emotion: '{emotion}'. Valid emotions: {', '.join(valid)}"
        )
    if not (0.0 <= intensity <= 1.0):
        raise ToolError(f"intensity must be between 0.0 and 1.0, got {intensity}")

    definition = _EMOTION_DEFINITIONS[emotion]
    return await _execute_by_id("vangard-set-emotion", {
        "nodeLabel": character_label,
        "emotion": emotion,
        "intensity": intensity,
        "morphList": definition["morphs"],
        "bodyAdjustments": definition["body"],
    })


# ---------------------------------------------------------------------------
# Tools — Phase 2: Content library navigation
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_list_categories(parent_path: str = "") -> dict[str, Any]:
    """List content library category subdirectories under a parent path.

    Searches across all configured DAZ content directories and deduplicates by name.

    Args:
        parent_path: Relative path within content directories to list (e.g. "People/Genesis 9").
                     Leave empty to list top-level categories.

    Returns:
        Dict with parent, categories (list of {name, path, duf_count}), and count.

    Example:
        daz_list_categories()                      # top-level: People, Props, Environments...
        daz_list_categories("People/Genesis 9")    # sub-folders: Characters, Clothing, Hair...
    """
    return await _execute_by_id("vangard-list-categories", {"parentPath": parent_path})


@mcp.tool()
async def daz_browse_category(category_path: str, sort_by: str = "name") -> dict[str, Any]:
    """List .duf content files in a content library category path.

    Searches all configured DAZ content directories and deduplicates by filename.

    Args:
        category_path: Relative path within content directories (e.g. "People/Genesis 9/Hair").
        sort_by: Sort order — only "name" is currently supported (alphabetical).

    Returns:
        Dict with category, items (list of {name, filename, full_path}), and count.

    Example:
        daz_browse_category("People/Genesis 9/Hair")
        daz_browse_category("Props/Furniture")
    """
    return await _execute_by_id("vangard-browse-category", {"categoryPath": category_path})


@mcp.tool()
async def daz_get_content_info(file_path: str) -> dict[str, Any]:
    """Read metadata from a .duf content file without loading it into the scene.

    Parses the JSON structure of a .duf file to extract name, type, contributor,
    and other available metadata fields.

    Args:
        file_path: Absolute path to a .duf file on disk.

    Returns:
        Dict with name, type, file_version, contributor, revision, modified, and
        any scene-level asset info found in the file.

    Raises:
        ToolError: If the file does not exist, is not readable, or is not valid JSON.
    """
    import json as _json

    path = Path(file_path)
    if not path.exists():
        raise ToolError(f"File not found: {file_path}")
    if not path.suffix.lower() == ".duf":
        raise ToolError(f"Not a .duf file: {file_path}")

    try:
        with open(path, encoding="utf-8") as f:
            data = _json.load(f)
    except (OSError, _json.JSONDecodeError) as e:
        raise ToolError(f"Failed to read {file_path}: {e}") from e

    asset_info = data.get("asset_info", {})
    contributor = asset_info.get("contributor", {})

    result: dict[str, Any] = {
        "path": str(path),
        "name": path.stem,
        "file_version": data.get("file_version", "unknown"),
        "asset_id": asset_info.get("id", ""),
        "type": asset_info.get("type", "unknown"),
        "revision": asset_info.get("revision", ""),
        "modified": asset_info.get("modified", ""),
        "contributor": {
            "author": contributor.get("author", ""),
            "studio": contributor.get("studio", ""),
            "website": contributor.get("website", ""),
        },
    }

    # Try to extract a human-readable description from common locations
    if "scene" in data:
        scene = data["scene"]
        nodes = scene.get("nodes", [])
        if nodes:
            first = nodes[0]
            result["label"] = first.get("label", path.stem)
            if "description" in first:
                result["description"] = first["description"]

    return result


# ---------------------------------------------------------------------------
# Tools — Phase 2: Scene composition / cinematography
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_apply_composition_rule(
    camera_label: str,
    subject_label: str,
    rule: str = "rule-of-thirds",
) -> dict[str, Any]:
    """Position camera so subject is framed according to a photography composition rule.

    The camera maintains approximately its current horizontal distance from the subject
    while adjusting position and aim to satisfy the chosen rule.

    Args:
        camera_label: Node label of the camera to reposition.
        subject_label: Node label of the subject to frame.
        rule: One of:
            - "rule-of-thirds"  — Subject on right vertical third at eye level (default)
            - "golden-ratio"    — Subject at the golden section (1.618 proportion)
            - "center-frame"    — Subject centred, symmetric framing
            - "leading-lines"   — Low angle with diagonal offset toward subject

    Returns:
        Dict with camera, subject, rule, camera_position, and explanation string.
    """
    return await _execute_by_id("vangard-apply-composition-rule", {
        "cameraLabel": camera_label,
        "subjectLabel": subject_label,
        "rule": rule,
    })


@mcp.tool()
async def daz_frame_shot(
    camera_label: str,
    subject_label: str,
    shot_type: str = "medium-shot",
) -> dict[str, Any]:
    """Frame camera to subject using a standard cinematic shot type.

    Calculates camera distance and height from the subject's bounding box,
    then positions and aims the camera accordingly. Genesis figures face +Z,
    so the camera is placed in front (positive Z direction).

    Args:
        camera_label: Node label of the camera to reposition.
        subject_label: Node label of the subject to frame.
        shot_type: One of:
            - "extreme-close-up"  — Eyes/mouth detail (~25 cm)
            - "close-up"          — Face and head (~50 cm)
            - "medium-close-up"   — Head and shoulders (~90 cm)
            - "medium-shot"       — Waist up (~140 cm)
            - "medium-full"       — Knees up (~200 cm)
            - "full-shot"         — Entire body (~400 cm)
            - "wide-shot"         — Body within environment (~700 cm)

    Returns:
        Dict with camera, subject, shot_type, distance, camera_height, and framing description.
    """
    return await _execute_by_id("vangard-frame-shot", {
        "cameraLabel": camera_label,
        "subjectLabel": subject_label,
        "shotType": shot_type,
    })


@mcp.tool()
async def daz_apply_camera_angle(
    camera_label: str,
    subject_label: str,
    angle: str = "eye-level",
) -> dict[str, Any]:
    """Apply a standard camera angle preset relative to a subject.

    Maintains the camera's current horizontal distance from the subject while
    adjusting vertical position and aim to achieve the specified angle. If the
    camera is closer than 50 cm it defaults to 250 cm.

    Args:
        camera_label: Node label of the camera to reposition.
        subject_label: Node label of the subject.
        angle: One of:
            - "eye-level"      — Camera at subject's eye height (neutral, default)
            - "high-angle"     — Camera above subject (~1.5× head height), looking down
            - "low-angle"      — Camera at shin level, looking up (powerful/dominant)
            - "dutch-angle"    — Eye level with 15° Z-roll (unsettling, tense)
            - "overhead"       — Camera directly above (bird's-eye view)
            - "worms-eye"      — Camera at ground level looking straight up
            - "over-shoulder"  — Camera behind and to one side of subject

    Returns:
        Dict with camera, subject, angle, camera_position, and descriptive note.
    """
    return await _execute_by_id("vangard-apply-camera-angle", {
        "cameraLabel": camera_label,
        "subjectLabel": subject_label,
        "angle": angle,
    })


# ---------------------------------------------------------------------------
# Tools — Phase 2: Scene checkpoint system
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_save_scene_state(checkpoint_name: str) -> dict[str, Any]:
    """Save current scene state as a named in-memory checkpoint.

    Captures transforms (position, rotation, scale), active morphs, and light
    properties for all skeletons, cameras, and lights in the scene. Use this
    before experimental changes so you can restore with daz_restore_scene_state.

    Args:
        checkpoint_name: Unique name for this checkpoint (e.g. "before_lighting_test").
                         Overwrites any existing checkpoint with the same name.

    Returns:
        Dict with checkpoint_name, node_count, and saved_at (ISO timestamp).

    Notes:
        Checkpoints are stored in the MCP server process memory and are lost if
        the server is restarted. They do not save materials, geometry, or HDR domes.
    """
    import datetime as _dt

    result = await _execute_by_id("vangard-save-scene-state", {
        "checkpointName": checkpoint_name,
    })

    now = _dt.datetime.utcnow().isoformat() + "Z"
    _CHECKPOINTS[checkpoint_name] = {
        "nodes": result.get("nodes", []),
        "saved_at": now,
        "node_count": result.get("node_count", 0),
    }

    return {
        "checkpoint_name": checkpoint_name,
        "node_count": result.get("node_count", 0),
        "saved_at": now,
    }


@mcp.tool()
async def daz_restore_scene_state(checkpoint_name: str) -> dict[str, Any]:
    """Restore scene state from a previously saved checkpoint.

    Applies the transforms, morphs, and light properties captured by
    daz_save_scene_state back to the scene. Nodes that no longer exist
    are skipped and reported in the errors list.

    Args:
        checkpoint_name: Name of the checkpoint to restore.

    Returns:
        Dict with checkpoint_name, restored (list of node labels), and errors.

    Raises:
        ToolError: If no checkpoint with the given name exists.
    """
    if checkpoint_name not in _CHECKPOINTS:
        available = sorted(_CHECKPOINTS.keys())
        avail_str = ", ".join(f'"{n}"' for n in available) if available else "(none saved)"
        raise ToolError(
            f"Checkpoint '{checkpoint_name}' not found. Available: {avail_str}"
        )

    cp = _CHECKPOINTS[checkpoint_name]
    result = await _execute_by_id("vangard-restore-scene-state", {
        "checkpointName": checkpoint_name,
        "nodes": cp["nodes"],
    })
    return result


@mcp.tool()
async def daz_list_checkpoints() -> dict[str, Any]:
    """List all saved scene state checkpoints in the current session.

    Returns:
        Dict with checkpoints (list of {name, node_count, saved_at}) and count.

    Notes:
        Checkpoints are in-process memory; they are cleared when the server restarts.
    """
    items = [
        {
            "name": name,
            "node_count": data["node_count"],
            "saved_at": data["saved_at"],
        }
        for name, data in sorted(_CHECKPOINTS.items())
    ]
    return {"checkpoints": items, "count": len(items)}


# ---------------------------------------------------------------------------
# Tools — Phase 2: Scene layout & proximity
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_get_scene_layout(
    include_types: list[str] | None = None,
) -> dict[str, Any]:
    """Get a spatial map of all scene nodes with positions and bounding boxes.

    Provides a bird's-eye view of where everything is positioned in the scene,
    useful for reasoning about character spacing, prop placement, and camera coverage.

    Args:
        include_types: List of node type strings to include. Defaults to all types.
                       Valid values: "figures", "cameras", "lights", "props".

    Returns:
        Dict with nodes (list of {label, type, position, bounds?}) and count.

    Example:
        daz_get_scene_layout()                              # everything
        daz_get_scene_layout(["figures", "cameras"])        # characters + cameras only
        daz_get_scene_layout(["lights"])                    # just lights with flux values
    """
    types = include_types or ["figures", "cameras", "lights", "props"]
    return await _execute_by_id("vangard-get-scene-layout", {"includeTypes": types})


@mcp.tool()
async def daz_find_nearby_nodes(
    node_label: str,
    radius: float = 100.0,
    include_types: list[str] | None = None,
) -> dict[str, Any]:
    """Find all scene nodes within a specified radius of a target node.

    Uses world-space positions to calculate distances. Returns nodes sorted
    nearest-first with cardinal direction labels.

    Args:
        node_label: Label of the centre node to search around.
        radius: Search radius in centimetres (default 100 cm).
        include_types: Filter by type — "figures", "cameras", "lights", "props".
                       None means return all types within radius.

    Returns:
        Dict with center_node, radius, nearby_nodes (list of {label, type, distance, direction}),
        and count.

    Example:
        daz_find_nearby_nodes("Genesis 9", radius=150)           # everything within 1.5 m
        daz_find_nearby_nodes("Chair", radius=80, include_types=["figures"])  # people near chair
    """
    return await _execute_by_id("vangard-find-nearby-nodes", {
        "nodeLabel": node_label,
        "radius": radius,
        "includeTypes": include_types,
    })


# ---------------------------------------------------------------------------
# Macro System Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_start_recording(
    macro_name: str,
    description: str = "",
) -> dict[str, Any]:
    """Start recording a macro — all subsequent MCP tool calls will be captured.

    Macros allow you to record sequences of operations and replay them later,
    optionally with parameter substitution. This is useful for:
    - Creating reusable workflows
    - Batch operations
    - Complex multi-step processes
    - Sharing workflows across scenes

    Args:
        macro_name: Unique name for this macro (1-64 characters, letters/digits/hyphens/underscores)
        description: Optional description of what this macro does

    Returns:
        Dict with success, macro_name, description, and started_at timestamp.

    Example:
        # Start recording a portrait setup workflow
        daz_start_recording("portrait_setup", "Standard portrait lighting and framing")

        # Perform operations (these will be recorded)
        daz_apply_lighting_preset("three-point", "Genesis 9")
        daz_frame_shot("Camera 1", "Genesis 9", "medium-close-up")

        # Stop recording
        daz_stop_recording()

    Note:
        - Only one macro can be recorded at a time
        - Macros are stored in memory and lost when MCP server restarts
        - Use daz_replay_macro() to execute saved macros
    """
    global _macro_recording, _current_macro

    # Validate macro name
    if not macro_name or len(macro_name) > 64:
        raise ToolError("Macro name must be 1-64 characters")
    if not macro_name.replace("-", "").replace("_", "").isalnum():
        raise ToolError("Macro name must contain only letters, digits, hyphens, and underscores")

    # Check if already recording
    if _macro_recording:
        raise ToolError(
            f"Already recording macro '{_current_macro['name']}'. "
            "Stop current recording with daz_stop_recording() first."
        )

    # Initialize recording session
    from datetime import datetime
    _macro_recording = True
    _current_macro = {
        "name": macro_name,
        "description": description,
        "started_at": datetime.now().isoformat(),
        "operations": [],
    }

    return {
        "success": True,
        "macro_name": macro_name,
        "description": description,
        "started_at": _current_macro["started_at"],
        "message": f"Recording macro '{macro_name}'. Call daz_stop_recording() when done.",
    }


@mcp.tool()
async def daz_stop_recording() -> dict[str, Any]:
    """Stop recording the current macro and save it to the macro library.

    The recorded macro will be saved in memory and can be replayed using
    daz_replay_macro(). Recording is automatically stopped.

    Returns:
        Dict with success, macro details (name, description, operation_count),
        and saved_at timestamp.

    Example:
        # Start recording
        daz_start_recording("my_workflow")

        # ... perform operations ...

        # Stop and save
        result = daz_stop_recording()
        print(f"Saved macro with {result['operation_count']} operations")

    Note:
        - Macros are stored in memory only (lost on MCP server restart)
        - If macro name already exists, it will be overwritten
        - No operations are actually recorded yet — this is placeholder for future implementation
    """
    global _macro_recording, _current_macro, _macro_library

    # Check if recording is active
    if not _macro_recording:
        raise ToolError("No macro recording in progress. Use daz_start_recording() first.")

    from datetime import datetime

    # Finalize macro
    _current_macro["saved_at"] = datetime.now().isoformat()
    operation_count = len(_current_macro["operations"])

    # Save to library
    macro_name = _current_macro["name"]
    _macro_library[macro_name] = _current_macro

    # Clear recording state
    result = {
        "success": True,
        "macro_name": macro_name,
        "description": _current_macro["description"],
        "operation_count": operation_count,
        "saved_at": _current_macro["saved_at"],
        "message": f"Macro '{macro_name}' saved with {operation_count} operations.",
    }

    _macro_recording = False
    _current_macro = None

    return result


@mcp.tool()
async def daz_replay_macro(
    macro_name: str,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Replay a saved macro with optional parameter substitution.

    Executes all operations recorded in a macro sequentially. Supports parameter
    substitution to customize behavior at replay time.

    Args:
        macro_name: Name of the macro to replay (from daz_list_macros)
        parameters: Optional dict of parameter values for substitution.
                    Use keys like "subject", "camera", "intensity" etc.
                    The macro will replace placeholder values with these runtime values.

    Returns:
        Dict with success, macro_name, results list (one per operation),
        successful_count, failed_count, and duration_ms.

    Example:
        # Record a macro for one character
        daz_start_recording("portrait_setup")
        daz_apply_lighting_preset("three-point", "Genesis 9")
        daz_frame_shot("Camera 1", "Genesis 9", "close-up")
        daz_stop_recording()

        # Replay for different character
        daz_replay_macro("portrait_setup", parameters={"subject": "Alice"})

    Note:
        - Parameter substitution not yet implemented in Phase 1
        - Operations execute sequentially; failure in one doesn't stop others
        - Results include success/failure status for each operation
    """
    global _macro_library

    # Look up macro
    if macro_name not in _macro_library:
        available = list(_macro_library.keys())
        raise ToolError(
            f"Macro '{macro_name}' not found. "
            f"Available macros: {available if available else '(none)'}"
        )

    macro = _macro_library[macro_name]
    operations = macro["operations"]

    if not operations:
        return {
            "success": True,
            "macro_name": macro_name,
            "message": "Macro has no operations to replay.",
            "results": [],
            "successful_count": 0,
            "failed_count": 0,
        }

    # TODO: Implement operation replay
    # For now, return placeholder response
    return {
        "success": True,
        "macro_name": macro_name,
        "message": f"Macro '{macro_name}' replay not yet implemented (Phase 1 placeholder).",
        "results": [],
        "successful_count": 0,
        "failed_count": 0,
        "operation_count": len(operations),
    }


@mcp.tool()
async def daz_list_macros() -> dict[str, Any]:
    """List all saved macros in the macro library.

    Returns all macros with their metadata. Useful for discovering available
    workflows and checking macro details before replay.

    Returns:
        Dict with macros list (each containing name, description, operation_count,
        saved_at), and total count.

    Example:
        result = daz_list_macros()
        for macro in result['macros']:
            print(f"{macro['name']}: {macro['operation_count']} operations")

    Note:
        - Macros are session-only (lost when MCP server restarts)
        - Use daz_replay_macro() to execute a saved macro
    """
    global _macro_library

    macros_list = []
    for name, macro in _macro_library.items():
        macros_list.append({
            "name": name,
            "description": macro.get("description", ""),
            "operation_count": len(macro.get("operations", [])),
            "saved_at": macro.get("saved_at", ""),
        })

    # Sort by name
    macros_list.sort(key=lambda m: m["name"])

    return {
        "macros": macros_list,
        "count": len(macros_list),
    }


# ---------------------------------------------------------------------------
# Cinematic Shot Sequence Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_create_shot_sequence(
    sequence_type: str,
    characters: list[str],
    duration: int = 120,
) -> dict[str, Any]:
    """Create a multi-camera shot sequence for cinematic storytelling.

    Automatically creates and positions multiple cameras with keyframe animations
    for standard cinematic sequences. Useful for:
    - Conversations (shot-reverse-shot)
    - Establishing shots (wide → medium → close-up)
    - Product showcases (orbit)
    - Dramatic reveals (push-in)

    Args:
        sequence_type: Type of sequence to create. Options:
            - "establishing-medium-closeup": Three cameras at different distances
              (wide → medium → close-up). Frames divided equally into thirds.
            - "shot-reverse-shot": Two cameras for conversation, alternating between
              over-shoulder angles. Requires 2 characters. Frames split 50/50.
            - "orbit": Single camera orbiting 360° around subject with keyframe animation.
            - "push-in": Single camera dollying from wide shot to close-up with smooth animation.

        characters: List of character labels (1-2 depending on sequence).
            First character is primary subject. Second character used for shot-reverse-shot.

        duration: Total duration in frames (default: 120 frames = 4 seconds at 30fps).

    Returns:
        Dict with:
        - cameras: List of created cameras with position and frame range info
        - totalFrames: Total duration
        - sequenceType: Confirmed sequence type
        - subject: Primary subject character label

    Example:
        # Establishing sequence for single character
        daz_create_shot_sequence(
            "establishing-medium-closeup",
            ["Genesis 9"],
            duration=180
        )
        # Creates: Wide Shot (0-59), Medium Shot (60-119), Close-up Shot (120-179)

        # Conversation between two characters
        daz_create_shot_sequence(
            "shot-reverse-shot",
            ["Alice", "Bob"],
            duration=240
        )
        # Creates: Over Shoulder 1 (0-119), Over Shoulder 2 (120-239)

        # 360° orbit around character
        daz_create_shot_sequence(
            "orbit",
            ["Genesis 9"],
            duration=300
        )
        # Creates animated camera orbiting over 300 frames

        # Dolly push-in
        daz_create_shot_sequence(
            "push-in",
            ["Genesis 9"],
            duration=120
        )
        # Creates animated camera moving from wide to close-up

    Notes:
        - Cameras are automatically aimed at subject's eye level
        - For animated sequences (orbit, push-in), keyframes are set automatically
        - For multi-shot sequences (establishing, shot-reverse-shot), use frame ranges
          to determine which camera to render for each frame
        - Use daz_set_active_camera() to preview each camera angle
        - Use daz_set_frame() to scrub through animation timeline
    """
    # Validate sequence type
    valid_types = [
        "establishing-medium-closeup",
        "shot-reverse-shot",
        "orbit",
        "push-in",
    ]
    if sequence_type not in valid_types:
        raise ToolError(
            f"Invalid sequence_type '{sequence_type}'. "
            f"Valid options: {', '.join(valid_types)}"
        )

    # Validate characters
    if not characters or len(characters) == 0:
        raise ToolError("At least one character required")

    if sequence_type == "shot-reverse-shot" and len(characters) < 2:
        raise ToolError("shot-reverse-shot requires 2 characters")

    # Validate duration
    if duration < 10 or duration > 10000:
        raise ToolError("Duration must be between 10 and 10000 frames")

    return await _execute_by_id("vangard-create-shot-sequence", {
        "sequenceType": sequence_type,
        "characters": characters,
        "duration": duration,
        "fps": 30,
    })


@mcp.tool()
async def daz_animate_conversation(
    char1_label: str,
    char2_label: str,
    dialogue_beats: list[dict[str, Any]],
) -> dict[str, Any]:
    """Choreograph an animated conversation between two characters.

    Automatically sets up keyframe animations for a dialogue sequence, including:
    - Look-at behavior (listener looks at speaker)
    - Emotion morphs timed to dialogue beats
    - Head/neck rotation for natural conversation dynamics

    Perfect for creating animated conversations without manually keyframing each movement.

    Args:
        char1_label: Label of first character
        char2_label: Label of second character
        dialogue_beats: List of dialogue beat dicts, each containing:
            - speaker: Label of who's speaking (must match char1_label or char2_label)
            - startFrame: Frame where beat starts (int)
            - endFrame: Frame where beat ends (int)
            - emotion: Emotion for speaker ("happy", "sad", "angry", "surprised", "neutral")
            - intensity: Optional emotion intensity 0.0-1.0 (default: 0.7)

    Returns:
        Dict with:
        - char1, char2: Character labels
        - beatsApplied: List of applied beats with actions performed
        - totalFrames: Total animation length
        - beatCount: Number of dialogue beats processed

    Example:
        # Create a 3-beat conversation
        result = daz_animate_conversation(
            "Alice",
            "Bob",
            [
                {
                    "speaker": "Alice",
                    "startFrame": 0,
                    "endFrame": 60,
                    "emotion": "happy",
                    "intensity": 0.8
                },
                {
                    "speaker": "Bob",
                    "startFrame": 60,
                    "endFrame": 120,
                    "emotion": "surprised",
                    "intensity": 0.9
                },
                {
                    "speaker": "Alice",
                    "startFrame": 120,
                    "endFrame": 180,
                    "emotion": "neutral"
                }
            ]
        )
        # Result shows 3 beats applied with emotion morphs and look-at animations

    Notes:
        - Characters automatically look at whoever is speaking
        - Emotion morphs are applied at beat start and held until beat end
        - Head and neck bones rotate for natural look-at behavior
        - Missing morphs are silently skipped (different Genesis generations have different morphs)
        - Use daz_set_frame() to preview animation at specific frames
        - Combine with daz_create_shot_sequence("shot-reverse-shot", ...) for camera angles
    """
    # Validate characters
    if not char1_label or not char2_label:
        raise ToolError("Both char1_label and char2_label are required")

    if char1_label == char2_label:
        raise ToolError("char1_label and char2_label must be different characters")

    # Validate dialogue beats
    if not dialogue_beats or len(dialogue_beats) == 0:
        raise ToolError("At least one dialogue beat required")

    # Validate each beat
    for i, beat in enumerate(dialogue_beats):
        if "speaker" not in beat:
            raise ToolError(f"Beat {i+1}: 'speaker' field required")
        if "startFrame" not in beat:
            raise ToolError(f"Beat {i+1}: 'startFrame' field required")
        if "endFrame" not in beat:
            raise ToolError(f"Beat {i+1}: 'endFrame' field required")

        speaker = beat["speaker"]
        if speaker not in [char1_label, char2_label]:
            raise ToolError(
                f"Beat {i+1}: speaker '{speaker}' must be either '{char1_label}' or '{char2_label}'"
            )

        start = beat["startFrame"]
        end = beat["endFrame"]
        if not isinstance(start, int) or not isinstance(end, int):
            raise ToolError(f"Beat {i+1}: startFrame and endFrame must be integers")
        if start < 0 or end < 0:
            raise ToolError(f"Beat {i+1}: startFrame and endFrame must be non-negative")
        if end <= start:
            raise ToolError(f"Beat {i+1}: endFrame ({end}) must be > startFrame ({start})")

        # Validate emotion if present
        if "emotion" in beat:
            valid_emotions = ["happy", "sad", "angry", "surprised", "neutral"]
            if beat["emotion"] not in valid_emotions:
                raise ToolError(
                    f"Beat {i+1}: emotion '{beat['emotion']}' invalid. "
                    f"Valid: {', '.join(valid_emotions)}"
                )

    return await _execute_by_id("vangard-animate-conversation", {
        "char1Label": char1_label,
        "char2Label": char2_label,
        "dialogueBeats": dialogue_beats,
    })


@mcp.tool()
async def daz_create_scene(
    description: str,
    characters: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a complete scene from a natural language description.

    Automatically creates a scene setup including lighting, cameras, and character
    positioning based on a text description. Uses template-based scene generation
    with keyword matching to identify scene types and apply appropriate setups.

    Perfect for quickly setting up common scene types without manual configuration.

    Supported Scene Types (detected via keywords):
        - "dining" / "dinner" / "meal" / "eat" - Dining/meal scene
        - "interview" / "meeting" / "business" - Interview/business meeting
        - "portrait" / "headshot" / "photo" - Portrait/photography
        - "conversation" / "talking" / "chat" - Conversation scene
        - Generic fallback for unrecognized descriptions

    Args:
        description: Natural language description of the scene.
            Examples:
            - "romantic dinner for two"
            - "job interview scene"
            - "professional portrait"
            - "two friends having a conversation"
            - "business meeting"

        characters: Optional list of character labels already loaded in the scene.
            Characters will be positioned appropriately for the scene type.
            If empty/None, scene will still be set up but positioning skipped.

    Returns:
        Dict with:
        - sceneType: Detected scene type ("dining", "interview", "portrait", "conversation", "generic")
        - description: Original description
        - charactersUsed: Number of characters processed
        - actions: List of actions performed (what was set up)
        - cameras: List of created cameras with type and purpose
        - suggestions: List of suggestions for improving the scene

    Example:
        # Romantic dinner scene
        result = daz_create_scene(
            "romantic dinner for two",
            ["Alice", "Bob"]
        )
        # Creates:
        # - Positions Alice and Bob facing each other
        # - Warm romantic lighting (2 spot lights)
        # - Wide shot camera
        # - Over-shoulder camera (for conversation)
        # - Suggestions: add table, plates, candles

        # Portrait setup
        result = daz_create_scene(
            "professional portrait",
            ["Genesis 9"]
        )
        # Creates:
        # - Three-point portrait lighting
        # - Close-up camera (50cm)
        # - Medium close-up camera (90cm)
        # - Suggestions: adjust expression, add backdrop

        # Job interview
        result = daz_create_scene(
            "job interview",
            ["Interviewer", "Candidate"]
        )
        # Creates:
        # - Characters positioned facing each other
        # - Professional three-point lighting
        # - Wide and medium shot cameras
        # - Suggestions: add desk, chairs, office props

    What Gets Created:
        1. **Lighting**: Scene-appropriate lighting setup (spot lights)
           - Dining: Warm romantic or standard dining lights
           - Interview: Professional three-point lighting
           - Portrait: Classic three-point portrait lighting
           - Conversation: Natural conversational lighting
           - Environment mode set to "Scene Only" (disables dome)

        2. **Character Positioning**: Logical positioning for scene type
           - Dining: Facing across table distance
           - Interview: Facing each other at interview distance
           - Conversation: Facing at conversation distance (closer than interview)

        3. **Cameras**: Multiple camera angles appropriate for scene
           - Wide shots for establishing
           - Medium shots for general coverage
           - Close-ups for portraits
           - Over-shoulder for conversations

        4. **Suggestions**: Actionable next steps for scene enhancement

    Notes:
        - Requires characters to be already loaded in scene
        - Creates new cameras and lights (doesn't delete existing)
        - Scene type detection is keyword-based (simple matching)
        - Generic fallback if no template matches
        - Props are not automatically loaded (suggested in suggestions list)
        - All positioning uses world-space coordinates
        - Lighting intensities calibrated for Iray rendering

    Limitations:
        - Does not load props automatically (manual loading required)
        - Does not apply poses or emotions (use daz_set_emotion separately)
        - Simple keyword matching (not full NL understanding)
        - Limited to pre-defined scene templates
        - Works best with 1-2 characters

    Follow-up Actions:
        After scene generation, you can:
        - Load props manually with daz_load_file()
        - Apply character emotions with daz_set_emotion()
        - Fine-tune lighting with daz_set_property()
        - Adjust camera positions with daz_set_property()
        - Preview cameras with daz_set_active_camera()
    """
    # Validate description
    if not description or len(description.strip()) == 0:
        raise ToolError("Description cannot be empty")

    if len(description) > 500:
        raise ToolError("Description too long (max 500 characters)")

    # Validate characters
    chars = characters or []
    if len(chars) > 10:
        raise ToolError("Too many characters (max 10)")

    return await _execute_by_id("vangard-create-scene", {
        "description": description,
        "characters": chars,
    })


# ---------------------------------------------------------------------------
# Camera Movement & Animation Tools (Phase 4.5)
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_animate_camera_movement(
    camera_label: str,
    movement_type: str,
    start_frame: int = 0,
    end_frame: int = 120,
    intensity: float = 1.0,
) -> dict[str, Any]:
    """Animate common camera movements with keyframes.

    Creates keyframe animation for standard cinematic camera moves. Perfect for
    adding professional camera motion without manual keyframing.

    Args:
        camera_label: Label of camera to animate
        movement_type: Type of camera movement. Options:
            - "dolly-in": Move camera forward toward aim point
            - "dolly-out": Move camera backward away from aim point
            - "pan-left": Rotate camera left (horizontal)
            - "pan-right": Rotate camera right (horizontal)
            - "tilt-up": Rotate camera up (vertical)
            - "tilt-down": Rotate camera down (vertical)
            - "crane-up": Move camera vertically upward
            - "crane-down": Move camera vertically downward
            - "handheld-shake": Procedural shake animation
        start_frame: Animation start frame (default: 0)
        end_frame: Animation end frame (default: 120)
        intensity: Movement amount multiplier 0.0-2.0 (default: 1.0)
            - dolly/crane: Distance in cm (200cm * intensity)
            - pan/tilt: Rotation in degrees (45° * intensity for pan, 30° for tilt)
            - shake: Amplitude (5cm * intensity)

    Returns:
        Dict with:
        - camera: Camera label
        - movementType: Type of movement applied
        - keyframesSet: Number of keyframes created
        - frameRange: {start, end} frame range
        - description: Human-readable description of movement
        - intensity: Applied intensity value

    Example:
        # Slow dolly-in
        daz_animate_camera_movement("Camera 1", "dolly-in", 0, 180, intensity=1.0)

        # Quick pan right
        daz_animate_camera_movement("Camera 1", "pan-right", 0, 60, intensity=1.5)

        # Subtle handheld shake
        daz_animate_camera_movement("Camera 1", "handheld-shake", 0, 300, intensity=0.3)

        # Dramatic crane up
        daz_animate_camera_movement("Camera 1", "crane-up", 60, 150, intensity=2.0)

    Notes:
        - Creates smooth motion by default
        - Dolly moves camera along current aim direction
        - Pan/tilt preserve camera position
        - Crane moves only vertically
        - Shake creates randomized keyframes every 3 frames
        - All movements create proper keyframe animations
        - Intensity scales movement amount (useful for subtle vs dramatic moves)
        - Handheld shake uses random offsets for natural camera shake
    """
    # Validate camera label
    if not camera_label:
        raise ToolError("camera_label is required")

    # Validate movement type
    valid_movements = [
        "dolly-in", "dolly-out",
        "pan-left", "pan-right",
        "tilt-up", "tilt-down",
        "crane-up", "crane-down",
        "handheld-shake"
    ]
    if movement_type not in valid_movements:
        raise ToolError(
            f"Invalid movement_type '{movement_type}'. "
            f"Valid options: {', '.join(valid_movements)}"
        )

    # Validate frame range
    if start_frame < 0:
        raise ToolError("start_frame must be >= 0")
    if end_frame <= start_frame:
        raise ToolError(f"end_frame ({end_frame}) must be > start_frame ({start_frame})")
    if end_frame - start_frame > 10000:
        raise ToolError("Frame range too large (max 10000 frames)")

    # Validate intensity
    if intensity < 0 or intensity > 10:
        raise ToolError("intensity must be between 0 and 10")

    return await _execute_by_id("vangard-animate-camera-movement", {
        "cameraLabel": camera_label,
        "movementType": movement_type,
        "startFrame": start_frame,
        "endFrame": end_frame,
        "intensity": intensity,
    })


@mcp.tool()
async def daz_create_camera_path(
    camera_label: str,
    waypoints: list[dict[str, Any]],
    easing: str = "smooth",
    aim_at_target: str | None = None,
) -> dict[str, Any]:
    """Create smooth camera path through multiple waypoints.

    Creates a smooth animated camera path by interpolating between position waypoints.
    Perfect for tracking shots, reveals, and complex camera moves.

    Args:
        camera_label: Label of camera to animate
        waypoints: List of waypoint dicts, each containing:
            - position: Dict with x, y, z coordinates (world space, cm)
            - frame: Frame number for this waypoint
            Minimum 2 waypoints required. Automatically sorted by frame.
        easing: Interpolation type (default: "smooth")
            - "linear": Constant speed between waypoints
            - "smooth": Ease-in-out (slow start/end, fast middle)
            - "ease-in": Slow start, fast end
            - "ease-out": Fast start, slow end
        aim_at_target: Optional node label to track throughout movement

    Returns:
        Dict with:
        - camera: Camera label
        - waypointCount: Number of waypoints
        - easing: Easing type used
        - keyframesSet: Number of keyframes created
        - frameRange: {start, end} frame range
        - aimAtTarget: Target node label if specified

    Example:
        # Simple 3-waypoint path
        daz_create_camera_path(
            "Camera 1",
            [
                {"position": {"x": 0, "y": 160, "z": 500}, "frame": 0},
                {"position": {"x": 200, "y": 180, "z": 300}, "frame": 90},
                {"position": {"x": 0, "y": 200, "z": 100}, "frame": 180}
            ],
            easing="smooth"
        )

        # Tracking shot following character
        daz_create_camera_path(
            "Camera 1",
            [
                {"position": {"x": -100, "y": 160, "z": 300}, "frame": 0},
                {"position": {"x": 100, "y": 160, "z": 300}, "frame": 120}
            ],
            aim_at_target="Genesis 9"
        )

        # Circular reveal
        import math
        radius = 300
        center_x, center_z = 0, 0
        waypoints = []
        for i in range(8):
            angle = (i / 8) * 2 * math.pi
            x = center_x + radius * math.sin(angle)
            z = center_z + radius * math.cos(angle)
            waypoints.append({
                "position": {"x": x, "y": 160, "z": z},
                "frame": i * 30
            })
        daz_create_camera_path("Camera 1", waypoints, easing="linear")

    Notes:
        - Waypoints are automatically sorted by frame
        - Creates 3 keyframes per waypoint (X, Y, Z translate)
        - Easing currently applied at DazScript keyframe level
        - aim_at_target points camera at target throughout path
        - Use more waypoints for tighter curves
        - World space coordinates (same as daz_set_property)
        - Good for: dolly shots, crane shots, tracking shots, reveals
    """
    # Validate camera label
    if not camera_label:
        raise ToolError("camera_label is required")

    # Validate waypoints
    if not waypoints or len(waypoints) < 2:
        raise ToolError("At least 2 waypoints required")

    if len(waypoints) > 100:
        raise ToolError("Too many waypoints (max 100)")

    # Validate each waypoint
    for i, wp in enumerate(waypoints):
        if "position" not in wp:
            raise ToolError(f"Waypoint {i}: missing 'position' field")
        if "frame" not in wp:
            raise ToolError(f"Waypoint {i}: missing 'frame' field")

        pos = wp["position"]
        if not isinstance(pos, dict):
            raise ToolError(f"Waypoint {i}: position must be a dict")
        if "x" not in pos or "y" not in pos or "z" not in pos:
            raise ToolError(f"Waypoint {i}: position must have x, y, z fields")

        # Validate frame
        frame = wp["frame"]
        if not isinstance(frame, int) or frame < 0:
            raise ToolError(f"Waypoint {i}: frame must be a non-negative integer")

    # Validate easing
    valid_easing = ["linear", "smooth", "ease-in", "ease-out"]
    if easing not in valid_easing:
        raise ToolError(
            f"Invalid easing '{easing}'. "
            f"Valid options: {', '.join(valid_easing)}"
        )

    return await _execute_by_id("vangard-create-camera-path", {
        "cameraLabel": camera_label,
        "waypoints": waypoints,
        "easing": easing,
        "aimAtTarget": aim_at_target,
    })


# ---------------------------------------------------------------------------
# Character Choreography Tools (Phase 4.6)
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_create_character_path(
    character_label: str,
    waypoints: list[dict[str, Any]],
    path_type: str = "straight",
    walking_style: str = "casual",
) -> dict[str, Any]:
    """Animate character movement along a path with waypoints.

    Creates keyframe animation for character walking/moving through multiple positions.
    Character automatically rotates to face direction of travel.

    Args:
        character_label: Label of character to animate
        waypoints: List of waypoint dicts, each containing:
            - position: Dict with x, y, z coordinates (world space, cm)
            - frame: Frame number for this waypoint
            Minimum 2 waypoints required. Automatically sorted by frame.
        path_type: Type of path (currently visual only):
            - "straight": Straight line between waypoints
            - "curved": Curved path (future implementation)
            - "circular": Circular path (future implementation)
        walking_style: Walking animation style (informational):
            - "casual": Normal walking pace
            - "hurried": Fast walking
            - "sneaking": Slow, careful movement

    Returns:
        Dict with:
        - character: Character label
        - waypointCount: Number of waypoints
        - pathType: Path type used
        - walkingStyle: Walking style
        - keyframesSet: Number of keyframes created (position + rotation)
        - frameRange: {start, end} frame range
        - totalDistance: Total distance traveled (cm)
        - note: Reminder about walking cycle animation

    Example:
        # Simple straight path
        daz_create_character_path(
            "Genesis 9",
            [
                {"position": {"x": -200, "y": 0, "z": 0}, "frame": 0},
                {"position": {"x": 0, "y": 0, "z": 0}, "frame": 60},
                {"position": {"x": 200, "y": 0, "z": 0}, "frame": 120}
            ],
            walking_style="casual"
        )

        # Character walks across room
        daz_create_character_path(
            "Alice",
            [
                {"position": {"x": -300, "y": 0, "z": 100}, "frame": 0},
                {"position": {"x": 300, "y": 0, "z": 100}, "frame": 180}
            ],
            walking_style="hurried"
        )

    Notes:
        - Character automatically rotates to face direction of movement
        - Creates 3 position keyframes + 1 rotation keyframe per waypoint
        - Walking cycle animation must be applied separately
        - Use with animation poses for realistic walking motion
        - Y position can be animated for stairs/slopes
        - Total distance calculated for reference
        - For running: use shorter duration between waypoints
        - For sneaking: use longer duration between waypoints
    """
    # Validate character label
    if not character_label:
        raise ToolError("character_label is required")

    # Validate waypoints
    if not waypoints or len(waypoints) < 2:
        raise ToolError("At least 2 waypoints required")

    if len(waypoints) > 100:
        raise ToolError("Too many waypoints (max 100)")

    # Validate each waypoint
    for i, wp in enumerate(waypoints):
        if "position" not in wp:
            raise ToolError(f"Waypoint {i}: missing 'position' field")
        if "frame" not in wp:
            raise ToolError(f"Waypoint {i}: missing 'frame' field")

        pos = wp["position"]
        if not isinstance(pos, dict):
            raise ToolError(f"Waypoint {i}: position must be a dict")
        if "x" not in pos or "y" not in pos or "z" not in pos:
            raise ToolError(f"Waypoint {i}: position must have x, y, z fields")

        frame = wp["frame"]
        if not isinstance(frame, int) or frame < 0:
            raise ToolError(f"Waypoint {i}: frame must be a non-negative integer")

    # Validate path type
    valid_path_types = ["straight", "curved", "circular"]
    if path_type not in valid_path_types:
        raise ToolError(
            f"Invalid path_type '{path_type}'. "
            f"Valid options: {', '.join(valid_path_types)}"
        )

    # Validate walking style
    valid_styles = ["casual", "hurried", "sneaking"]
    if walking_style not in valid_styles:
        raise ToolError(
            f"Invalid walking_style '{walking_style}'. "
            f"Valid options: {', '.join(valid_styles)}"
        )

    return await _execute_by_id("vangard-create-character-path", {
        "characterLabel": character_label,
        "waypoints": waypoints,
        "pathType": path_type,
        "walkingStyle": walking_style,
    })


@mcp.tool()
async def daz_arrange_characters(
    characters: list[str],
    arrangement: str,
    spacing: float = 80.0,
    facing: str = "forward",
    center_position: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Position multiple characters in formation.

    Arranges characters in standard formations (line, semicircle, triangle, circle)
    with automatic positioning and rotation. Perfect for group shots and scenes.

    Args:
        characters: List of character labels (minimum 2)
        arrangement: Formation type:
            - "line": Straight line along X axis
            - "semicircle": Arc formation facing forward
            - "triangle": Triangular formation (2-3 chars: triangle, 4+: rows)
            - "conversation-circle": Circle facing inward
        spacing: Distance between characters in cm (default: 80)
        facing: Direction characters face:
            - "forward": All face +Z direction (camera at origin)
            - "center": All face formation center (for circle)
            - "camera": All face toward camera (same as forward)
        center_position: Optional center point for formation.
            Dict with x, y, z keys. Default: {x: 0, y: 0, z: 0}

    Returns:
        Dict with:
        - characters: List of dicts with label, position {x, y, z}, rotation
        - arrangement: Formation type used
        - spacing: Spacing value
        - facing: Facing direction
        - count: Number of characters arranged

    Example:
        # Line up 5 characters
        daz_arrange_characters(
            ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            arrangement="line",
            spacing=100,
            facing="forward"
        )

        # Semicircle for group portrait
        daz_arrange_characters(
            ["Person1", "Person2", "Person3", "Person4"],
            arrangement="semicircle",
            spacing=120,
            facing="forward"
        )

        # Conversation circle
        daz_arrange_characters(
            ["Alice", "Bob", "Charlie"],
            arrangement="conversation-circle",
            spacing=100,
            facing="center",
            center_position={"x": 0, "y": 0, "z": 200}
        )

        # Triangle formation
        daz_arrange_characters(
            ["Leader", "Left", "Right"],
            arrangement="triangle",
            spacing=90
        )

    Notes:
        - Formations centered at center_position (default: origin)
        - Line: Arranged left-to-right along X axis
        - Semicircle: Arc radius calculated from spacing and character count
        - Triangle: 2-3 chars form triangle, 4+ form two rows
        - Conversation-circle: All face inward at equal angles
        - Use larger spacing for formal arrangements
        - Use smaller spacing for intimate/crowded scenes
        - Spacing measured center-to-center between characters
        - Y position preserved from center_position (for platforms/stages)
    """
    # Validate characters
    if not characters or len(characters) < 2:
        raise ToolError("At least 2 characters required")

    if len(characters) > 20:
        raise ToolError("Too many characters (max 20)")

    # Validate arrangement
    valid_arrangements = ["line", "semicircle", "triangle", "conversation-circle"]
    if arrangement not in valid_arrangements:
        raise ToolError(
            f"Invalid arrangement '{arrangement}'. "
            f"Valid options: {', '.join(valid_arrangements)}"
        )

    # Validate spacing
    if spacing < 10 or spacing > 500:
        raise ToolError("spacing must be between 10 and 500 cm")

    # Validate facing
    valid_facing = ["forward", "center", "camera"]
    if facing not in valid_facing:
        raise ToolError(
            f"Invalid facing '{facing}'. "
            f"Valid options: {', '.join(valid_facing)}"
        )

    # Validate center_position
    center_pos = center_position or {"x": 0, "y": 0, "z": 0}
    if not isinstance(center_pos, dict):
        raise ToolError("center_position must be a dict")
    if "x" not in center_pos or "y" not in center_pos or "z" not in center_pos:
        raise ToolError("center_position must have x, y, z fields")

    return await _execute_by_id("vangard-arrange-characters", {
        "characters": characters,
        "arrangement": arrangement,
        "spacing": spacing,
        "facing": facing,
        "centerPosition": center_pos,
    })


@mcp.tool()
async def daz_choreograph_action(
    action_type: str,
    characters: list[str],
    start_frame: int = 0,
    duration: int = 90,
) -> dict[str, Any]:
    """Choreograph simple action between characters.

    Automatically positions characters for common interactions (handshake, hug,
    fight, dance) with appropriate spacing and facing. Provides suggestions for
    completing the choreography.

    Args:
        action_type: Type of action to choreograph:
            - "handshake": Business/friendly handshake (60cm apart)
            - "hug": Intimate embrace (30cm apart)
            - "fight": Combat stance (100cm apart)
            - "dance": Partner dance position (40cm apart)
        characters: List of character labels (requires 2 for all types)
        start_frame: Frame to start action (default: 0)
        duration: Length of action in frames (default: 90 = 3 seconds at 30fps)

    Returns:
        Dict with:
        - actionType: Type of action
        - characters: List of character labels
        - positions: List of dicts with character, position {x, y, z}, rotation
        - frameRange: {start, end} frame range
        - suggestions: List of recommended next steps

    Example:
        # Handshake between two business people
        result = daz_choreograph_action(
            "handshake",
            ["Alice", "Bob"],
            start_frame=0,
            duration=60
        )
        # Positions characters facing each other
        # Suggestions include using daz_reach_toward for hands

        # Emotional hug
        result = daz_choreograph_action(
            "hug",
            ["Mother", "Child"],
            start_frame=30,
            duration=120
        )
        # Positions very close, facing each other
        # Suggests using daz_interactive_pose for arms

        # Action fight scene
        result = daz_choreograph_action(
            "fight",
            ["Hero", "Villain"],
            start_frame=0,
            duration=180
        )
        # Positions at fighting distance
        # Suggests combat poses and angry emotions

        # Romantic dance
        result = daz_choreograph_action(
            "dance",
            ["Dancer1", "Dancer2"],
            start_frame=0,
            duration=240
        )
        # Positions for partner dance
        # Suggests dance poses and path animation

    Notes:
        - All actions require exactly 2 characters
        - Characters positioned facing each other
        - Spacing automatically determined by action type
        - Handshake: 60cm (arm's reach)
        - Hug: 30cm (intimate distance)
        - Fight: 100cm (combat distance)
        - Dance: 40cm (close dance position)
        - This is positioning only - use suggestions for complete choreography
        - Follow up with daz_reach_toward, daz_interactive_pose, or pose loading
        - Use daz_set_emotion for appropriate facial expressions
        - Use daz_create_character_path for dance movement
    """
    # Validate action type
    valid_actions = ["handshake", "hug", "fight", "dance"]
    if action_type not in valid_actions:
        raise ToolError(
            f"Invalid action_type '{action_type}'. "
            f"Valid options: {', '.join(valid_actions)}"
        )

    # Validate characters
    if not characters or len(characters) != 2:
        raise ToolError("Exactly 2 characters required for action choreography")

    # Validate frame range
    if start_frame < 0:
        raise ToolError("start_frame must be >= 0")

    if duration < 10 or duration > 1000:
        raise ToolError("duration must be between 10 and 1000 frames")

    return await _execute_by_id("vangard-choreograph-action", {
        "actionType": action_type,
        "characters": characters,
        "startFrame": start_frame,
        "duration": duration,
    })


# ---------------------------------------------------------------------------
# Phase 4.7: Cinematic Coverage Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_setup_shot_coverage(
    subject_label: str,
    coverage_type: str = "standard",
    camera_height: float = 160.0,
    auto_aim: bool = True,
) -> dict[str, Any]:
    """Create multiple camera angles for cinematic coverage of a subject.

    Automatically positions multiple cameras for professional shot coverage (master,
    medium, closeup, etc.) based on cinematic conventions. All cameras aim at the
    subject and use appropriate focal lengths for each shot type.

    Args:
        subject_label: Label of subject node (character, prop, etc.)
        coverage_type: Type of coverage to set up:
            - "standard": Master (wide), Medium, Closeup (3 cameras)
            - "interview": Two-shot + two singles at angles (3 cameras)
            - "dramatic": Master, Low Angle, High Angle, Profile (4 cameras)
            - "action": Wide, Medium, Tracking, Hero Low (4 cameras)
        camera_height: Height of cameras in cm (default: 160 = eye level)
        auto_aim: Automatically point cameras at subject (default: True)

    Returns:
        Dict with:
        - coverageType: Type of coverage used
        - subject: Subject label
        - subjectPosition: {x, y, z} position of subject
        - cameras: List of dicts with name, label, position, focalLength, distance, angle
        - cameraCount: Number of cameras created
        - suggestions: List of recommended next steps

    Example:
        # Standard 3-camera coverage for dialogue scene
        result = daz_setup_shot_coverage(
            "Alice",
            coverage_type="standard",
            camera_height=165,
            auto_aim=True
        )
        # Creates Master (35mm, 400cm), Medium (50mm, 200cm), Closeup (85mm, 100cm)

        # Interview setup with two-shot + singles
        result = daz_setup_shot_coverage(
            "Interviewer",
            coverage_type="interview",
            camera_height=160
        )
        # Creates TwoShot (50mm), SingleA (85mm, -30°), SingleB (85mm, +30°)

        # Dramatic multi-angle coverage
        result = daz_setup_shot_coverage(
            "Hero",
            coverage_type="dramatic",
            camera_height=170
        )
        # Creates Master, LowAngle (-80cm), HighAngle (+120cm), Profile (90°)

        # Action scene with dynamic angles
        result = daz_setup_shot_coverage(
            "Stunt_Character",
            coverage_type="action",
            camera_height=150
        )
        # Creates WideAction (28mm), MediumAction, TrackingShot (-45°), HeroLow

    Notes:
        - All cameras automatically created and positioned
        - Focal lengths chosen for each shot type (28-85mm range)
        - Standard coverage: 3 cameras (most common setup)
        - Interview: 3 cameras (two-shot + singles)
        - Dramatic: 4 cameras (varied angles and heights)
        - Action: 4 cameras (wide coverage + low angles)
        - Cameras named by shot type (Master_Camera, Closeup_Camera, etc.)
        - Switch active camera to render different angles
        - Use with daz_animate_camera_movement for dynamic shots
        - Combine with daz_render_animation to output multiple angles
    """
    # Validate coverage type
    valid_types = ["standard", "interview", "dramatic", "action"]
    if coverage_type not in valid_types:
        raise ToolError(
            f"Invalid coverage_type '{coverage_type}'. "
            f"Valid options: {', '.join(valid_types)}"
        )

    # Validate camera height
    if camera_height < 0 or camera_height > 500:
        raise ToolError("camera_height must be between 0 and 500 cm")

    return await _execute_by_id("vangard-setup-shot-coverage", {
        "subjectLabel": subject_label,
        "coverageType": coverage_type,
        "cameraHeight": camera_height,
        "autoAim": auto_aim,
    })


@mcp.tool()
async def daz_create_camera_rig(
    rig_name: str = "CameraRig",
    center_position: dict[str, float] | None = None,
    camera_count: int = 3,
    radius: float = 250.0,
    height_variation: float = 40.0,
    focal_lengths: list[int] | None = None,
) -> dict[str, Any]:
    """Set up multi-camera rig for bullet-time or simultaneous multi-angle shots.

    Creates multiple cameras arranged in a circle around a center point, all parented
    to a rig controller. Rotate the rig to orbit all cameras around the subject, or
    switch between cameras for instant angle changes.

    Args:
        rig_name: Base name for rig (default: "CameraRig")
        center_position: Center point {x, y, z} in cm (default: {x:0, y:150, z:0})
        camera_count: Number of cameras in rig, 2-8 (default: 3)
        radius: Distance from center to cameras in cm (default: 250)
        height_variation: Variation in camera heights in cm (default: 40)
        focal_lengths: List of focal lengths in mm (default: [35, 50, 85])

    Returns:
        Dict with:
        - rigName: Name of rig
        - rigLabel: Label of rig parent node
        - centerPosition: {x, y, z} center point
        - radius: Distance from center
        - cameraCount: Number of cameras
        - cameras: List of dicts with name, angle, focalLength, heightOffset
        - suggestions: List of recommended next steps

    Example:
        # 3-camera rig for product visualization
        result = daz_create_camera_rig(
            rig_name="ProductRig",
            center_position={"x": 0, "y": 100, "z": 0},
            camera_count=3,
            radius=200,
            focal_lengths=[50, 50, 50]
        )
        # Creates 3 cameras at 120° intervals, all 200cm from center

        # 8-camera bullet-time rig
        result = daz_create_camera_rig(
            rig_name="BulletTime",
            center_position={"x": 0, "y": 150, "z": 0},
            camera_count=8,
            radius=300,
            height_variation=20,
            focal_lengths=[85, 85, 85, 85, 85, 85, 85, 85]
        )
        # Creates 8 cameras at 45° intervals for smooth frozen-time effect

        # 4-camera interview rig with varied focal lengths
        result = daz_create_camera_rig(
            rig_name="InterviewRig",
            camera_count=4,
            radius=250,
            focal_lengths=[35, 50, 85, 85]
        )
        # Wide, medium, two closeups at different angles

    Notes:
        - All cameras parented to rig controller node
        - Rotate rig YRotate to orbit all cameras around subject
        - Animate rig position to move entire camera array
        - Switch between cameras for instant angle changes (bullet-time)
        - Height variation adds subtle vertical offsets for visual interest
        - Cameras automatically point at center
        - If focal_lengths list too short, remaining cameras use 50mm
        - Cameras named RigName_Cam1, RigName_Cam2, etc.
        - Evenly spaced around circle (360° / camera_count)
        - Perfect for:
          * Bullet-time effects (8+ cameras)
          * Product turntables (3-4 cameras)
          * Multi-angle coverage (4-6 cameras)
          * 360° video (6-8 cameras)
    """
    # Validate camera count
    if camera_count < 2 or camera_count > 8:
        raise ToolError("camera_count must be between 2 and 8")

    # Validate radius
    if radius < 50 or radius > 2000:
        raise ToolError("radius must be between 50 and 2000 cm")

    # Validate height variation
    if height_variation < 0 or height_variation > 200:
        raise ToolError("height_variation must be between 0 and 200 cm")

    # Default center position
    if center_position is None:
        center_position = {"x": 0.0, "y": 150.0, "z": 0.0}

    # Default focal lengths
    if focal_lengths is None:
        focal_lengths = [35, 50, 85]

    # Validate focal lengths
    if focal_lengths:
        for fl in focal_lengths:
            if fl < 10 or fl > 200:
                raise ToolError("All focal lengths must be between 10 and 200 mm")

    return await _execute_by_id("vangard-create-camera-rig", {
        "rigName": rig_name,
        "centerPosition": center_position,
        "cameraCount": camera_count,
        "radius": radius,
        "heightVariation": height_variation,
        "focalLengths": focal_lengths,
    })


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
