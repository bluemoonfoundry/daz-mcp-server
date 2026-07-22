"""Utility tools: status, script execution, script help, property inspection,
scene validation, event waiting, and macro recording/replay.
"""
from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from importlib.metadata import version as _pkg_version
from pathlib import Path
from typing import Any

import httpx
from fastmcp.exceptions import ToolError

from .._mcp import mcp, _execute_by_id
from .._client import get_daz_client, get_http_client, get_scene, run_dazpy
from .._errors import handle_dazpy_error, handle_network_error, check_response

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_DOCS_FILE = Path(__file__).parent.parent / "dazscript_docs.json"
_DAZSCRIPT_DOCS: dict = {}
try:
    with open(_DOCS_FILE) as f:
        _DAZSCRIPT_DOCS = json.load(f)
except (OSError, json.JSONDecodeError):
    pass

_macro_recording: bool = False
_current_macro: dict[str, Any] | None = None
_macro_library: dict[str, dict[str, Any]] = {}
_call_stats: dict[str, int] = {}


# ---------------------------------------------------------------------------
# Inline scripts for tools that need custom introspection/aggregation logic
# beyond what dazpy's typed primitives expose directly. Routed through
# DazClient.execute() (dazpy) rather than the httpx-based script registry.
# ---------------------------------------------------------------------------

# args: {nodeLabel, propertyType}. Returns: {node, properties: [...], count}
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
# Returns: {label, name, type, current_value, default_value, min, max, is_animatable, path, node}
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

# args: {operations: [{nodeLabel, propertyName, value}]}
# Returns: {results: [...], successCount, failureCount, total}
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

# args: none. Returns: {valid, issues, warnings, score, score_breakdown, summary}
_VALIDATE_SCENE_SCRIPT = """\
(function(){
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
    var envNode = Scene.findNodeByLabel("Environment Options");
    var envMode = envNode ? envNode.findProperty("Environment Mode") : null;
    var envModeVal = envMode ? envMode.getValue() : 0;
    var hasEnvLight = (envModeVal !== 3);  // not scene-only -> env dome contributes

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


# ---------------------------------------------------------------------------
# Tools — connectivity / execution
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_status() -> dict[str, Any]:
    """Check DAZ Studio connectivity. Returns MCP server and DazScriptServer status/version.

    Returns:
      - mcp_server_version: version of this MCP server (vangard-daz-mcp)
      - running: true if the DazScriptServer plugin responded
      - version: DazScriptServer plugin version — a different piece of software
                 running inside DAZ Studio, not this MCP server
    """
    try:
        result = await run_dazpy(get_daz_client().status)
    except Exception as e:
        handle_dazpy_error(e)
    result["mcp_server_version"] = _pkg_version("vangard-daz-mcp")
    return result


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

    4. ✅ Environment node: use Scene.findNodeByLabel("Environment Options")
       (not a fixed Scene.getNode(index) - node order is scene-dependent)

    For detailed examples and documentation, use the daz_script_help tool first.

    Args:
        script: DazScript (JavaScript) source code to execute.
        args: Optional JSON object accessible in script as `args` variable.

    Returns:
        Object with keys: success, result, output (list of print() lines), error.
    """
    try:
        result = await run_dazpy(lambda: get_daz_client().execute(script, args))
    except Exception as e:
        handle_dazpy_error(e)
    return {
        "success": result.success,
        "result": result.value,
        "output": result.output,
        "error": result.error,
    }


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
    try:
        result = await run_dazpy(lambda: get_daz_client().execute_file(script_file, args))
    except Exception as e:
        handle_dazpy_error(e)
    return {
        "success": result.success,
        "result": result.value,
        "output": result.output,
        "error": result.error,
    }


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
# Tools — property operations
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
    def _run() -> dict:
        return get_daz_client().execute(
            _BATCH_SET_PROPERTIES_SCRIPT, {"operations": operations}
        ).value

    try:
        return await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)


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
    def _run() -> dict:
        return get_daz_client().execute(
            _INSPECT_PROPERTIES_SCRIPT,
            {"nodeLabel": node_label, "propertyType": property_type},
        ).value

    try:
        return await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)


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
    def _run() -> dict:
        return get_daz_client().execute(
            _GET_PROPERTY_METADATA_SCRIPT,
            {"nodeLabel": node_label, "propertyName": property_name},
        ).value

    try:
        return await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)


# ---------------------------------------------------------------------------
# Tools — script / scene validation
# ---------------------------------------------------------------------------


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
    try:
        return await run_dazpy(lambda: get_daz_client().execute(_VALIDATE_SCENE_SCRIPT).value)
    except Exception as e:
        handle_dazpy_error(e)


# ---------------------------------------------------------------------------
# Tools — scene events
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_wait_for_scene_event(
    event_types: list[str],
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    """Wait for one of the specified scene events via the SSE stream at GET /scene/events.

    Opens a Server-Sent Events connection and returns as soon as any of the
    requested event types fires, or raises ToolError if the timeout is reached.

    Common use-cases:
    - Wait for a render to finish: event_types=["render.finished"]
    - Detect when a file load completes: event_types=["scene.loaded"]
    - Detect any scene or render completion: event_types=["render.finished", "scene.loaded"]

    Available event types (from daz-script-server):
        render.started, render.finished, render.progress,
        scene.loaded, scene.saved,
        node.added, node.removed, node.renamed,
        selection.primary_changed,
        time.changed,
        playback.started, playback.stopped,
        light.added, light.removed,
        camera.added, camera.removed,
        skeleton.added, skeleton.removed

    The filter query param is derived automatically from the event type prefixes
    (e.g. ["render.finished", "scene.loaded"] → ?filter=render,scene).

    Args:
        event_types: One or more event type strings to wait for.
        timeout_seconds: Maximum seconds to wait before raising ToolError (default 30).

    Returns:
        The first matching SSE event dict, e.g.:
        {"type": "render.finished", "ts": "2026-01-01T12:00:00Z", "data": {...}}
    """
    if not event_types:
        raise ToolError("event_types must not be empty")

    event_types_set = set(event_types)
    categories = list({t.split(".")[0] for t in event_types})
    params = {"filter": ",".join(sorted(categories))}

    client = get_http_client()

    async def _listen() -> dict[str, Any] | None:
        try:
            async with client.stream(
                "GET",
                "/scene/events",
                params=params,
                timeout=float(timeout_seconds + 5),
            ) as response:
                check_response(response)
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        event = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
                    if event.get("type") in event_types_set:
                        return event
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
            handle_network_error(exc)
        return None

    try:
        result = await asyncio.wait_for(_listen(), timeout=float(timeout_seconds))
    except asyncio.TimeoutError:
        raise ToolError(
            f"Timeout: none of {event_types} fired within {timeout_seconds}s"
        )

    if result is None:
        raise ToolError(
            f"SSE stream closed before any of {event_types} was received"
        )
    return result


# ---------------------------------------------------------------------------
# Tools — macro recording / replay
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
# Tools — intelligence / meta
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_auto_improve_scene() -> dict[str, Any]:
    """Automatically validate the scene and attempt to fix common issues."""
    try:
        validation = await run_dazpy(lambda: get_daz_client().execute(_VALIDATE_SCENE_SCRIPT).value)
    except Exception as e:
        handle_dazpy_error(e)
    issues = validation.get("issues", []) if isinstance(validation, dict) else []
    fixed = []
    for issue in issues:
        issue_type = issue.get("type", "") if isinstance(issue, dict) else ""
        if issue_type == "missing_lights":
            await _execute_by_id("vangard-create-light", {"lightType": "distant", "label": "Auto Light"})
            fixed.append("Added missing light")
    return {"validation": validation, "fixed": fixed, "count": len(fixed)}


@mcp.tool()
async def daz_suggest_next_action() -> dict[str, Any]:
    """Suggest the next action to take based on scene state."""
    def _run() -> tuple[int, int, int]:
        scene = get_scene()
        return len(scene.skeletons()), len(scene.lights()), len(scene.cameras())

    try:
        num_figures, num_lights, num_cameras = await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)

    suggestions = []
    if not num_figures:
        suggestions.append({"action": "daz_load_file", "reason": "No figures in scene - load a character"})
    if not num_lights:
        suggestions.append({"action": "daz_create_light", "reason": "No lights - add lighting"})
    if not num_cameras:
        suggestions.append({"action": "daz_create_camera", "reason": "No cameras - add a camera"})
    if not suggestions:
        suggestions.append({"action": "daz_render", "reason": "Scene looks ready to render"})
    return {"suggestions": suggestions}


@mcp.tool()
async def daz_get_performance_stats() -> dict[str, Any]:
    """Return session performance statistics."""
    return {"call_stats": _call_stats, "total_calls": sum(_call_stats.values())}


@mcp.tool()
async def daz_explain_last_error() -> dict[str, Any]:
    """Explain common DAZ Studio errors and how to fix them."""
    return {
        "common_errors": [
            {"error": "Node not found", "fix": "Check node label spelling; use daz_scene_info to list nodes"},
            {"error": "Script execution failed", "fix": "Validate script with daz_validate_script first"},
            {"error": "Connection refused", "fix": "Ensure DAZ Studio is running and DazScriptServer plugin is active"},
            {"error": "Rate limit exceeded", "fix": "Wait a moment and retry; or increase rate limit in plugin settings"},
        ]
    }
