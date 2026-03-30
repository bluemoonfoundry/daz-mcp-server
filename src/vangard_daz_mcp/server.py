"""MCP server wrapping the DazScriptServer HTTP API for DAZ Studio."""

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

# args: {nodeLabel, includeZero}
# includeZero: if true, return all morphs; if false, only return morphs with non-zero values
# Returns: {morphs: [{label, name, value, path}], count}
# Lists all numeric properties (morphs) on a node
_LIST_MORPHS_SCRIPT = """\
(function(){
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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
