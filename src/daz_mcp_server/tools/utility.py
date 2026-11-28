"""Utility tools: status, script execution, script help, property inspection,
scene validation, event waiting, session stats and the last error.
"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

import dazpy.exceptions as daz_exc
from fastmcp.exceptions import ToolError

from .._mcp import (
    mcp,
    _execution_payload,
    _execute_by_id,
    _execute_raw,
    with_args_variable,
)
from .._client import get_async_daz_client, get_scene
from .._errors import handle_dazpy_error, run_tool
from .._validation import validate_scene
from .._guides import GUIDE_NAMES, guide_index, read_guide
from .. import _compat
from .. import _session_stats

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



# ---------------------------------------------------------------------------
# Tools — connectivity / execution
# ---------------------------------------------------------------------------


@mcp.tool(tags={"desktop"})
async def daz_status() -> dict[str, Any]:
    """Check DAZ Studio connectivity. Returns server status and version, plus
    ``plugin_compatibility``: the target host:port, plugin and dazpy versions,
    the minimum plugin version, and upgrade advice when the plugin is too old."""
    try:
        status = await get_async_daz_client().status()
    except daz_exc.DazError as exc:
        handle_dazpy_error(exc)
    return {**status, "plugin_compatibility": _compat.summary()}


@mcp.tool(tags={"desktop"})
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

    3. ✅ A top-level ``return`` is a syntax error. Wrap scripts returning
       values in an IIFE, or end with an expression (its value is the result):
       (function(){ return Scene.getNumNodes(); })()

    4. ✅ Environment node is ALWAYS Scene.getNode(1) - not findNodeByLabel()

    5. ❌ NEVER use MainWindow.menuBar() — not Q_INVOKABLE (undefined on DS6).
       ✅ MainWindow.getActionMgr().findAction("DzERCFreezeAction")
       ✅ mgr.getMenu() walks DzActionMenu (item.label / item.action)
       ✅ new DzERCFreeze() for headless ERC freeze — do not act.trigger()

    For detailed examples and documentation, use the daz_script_help tool first.

    Args:
        script: DazScript (JavaScript) source code to execute.
        args: Optional JSON object, available in the script as the ``args``
            variable (and as ``getArguments()[0]``).

    Returns:
        Object with keys: success, result, output (list of print() lines), error.
    """
    return await _execute_raw(with_args_variable(script), args)


@mcp.tool()
async def daz_execute_file(
    script_file: str,
    args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a DazScript file on disk inside DAZ Studio.

    Args:
        script_file: Absolute path to the .dsa/.ds script file on the DAZ Studio machine.
        args: Optional JSON-serialisable object, read inside the file with
            ``getArguments()[0]`` (a file has no ``args`` variable).

    Returns:
        Object with keys: success, result, output (list of print() lines), error.
    """
    try:
        result = await get_async_daz_client().execute_file(script_file, args)
    except daz_exc.DazError as exc:
        handle_dazpy_error(exc)
    return _execution_payload(result)


@mcp.tool()
async def daz_execute_file_async(
    script_file: str,
    args: dict[str, Any] | None = None,
    report_file: str | None = None,
) -> dict[str, Any]:
    """Submit a DazScript file as a background job and return immediately.

    Use this for long-running file-backed work such as pose sweeps, simulations,
    exports, and batch renders. DAZ Studio loads the file when the queued job
    starts, so ``getScriptFileName()`` and relative ``include()`` calls keep
    working. Poll with ``daz_get_request_status``, fetch the final response with
    ``daz_get_request_result``, or stop queued work with ``daz_cancel_request``.

    Args:
        script_file: Absolute path to the .dsa/.ds file on the DAZ Studio machine.
        args: Optional JSON-serialisable object available through
            ``getArguments()[0]`` in the script.
        report_file: Optional absolute path to a per-job JSONL event file. The
            server truncates it on submission and exposes its structured
            progress, bounded log tail, and output manifest through the normal
            request status/result tools.

    Returns:
        The queued job record: request_id, status, and submitted_at.
    """
    try:
        request_id = await get_async_daz_client().execute_file_async_submit(
            script_file, args, report_file=report_file
        )
    except daz_exc.DazError as exc:
        handle_dazpy_error(exc)
    return {"request_id": request_id, "status": "queued"}


@mcp.tool(tags={"desktop"})
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
    - guides: list the bundled agent guides; guide:<name> returns one
      (actors, cinema, daz_studio, dazscript, recipe, scene)

    Args:
        topic: Documentation topic to retrieve (default: "overview")

    Returns:
        Formatted documentation with examples for the requested topic.
    """
    if topic == "guides":
        return guide_index()
    if topic.startswith("guide:"):
        try:
            return read_guide(topic.split(":", 1)[1])
        except KeyError:
            return (
                f"Unknown topic: '{topic}'\n\nAvailable guides: "
                + ", ".join(f"guide:{name}" for name in GUIDE_NAMES)
            )
    if topic not in _DAZSCRIPT_DOCS:
        available = ", ".join(sorted(_DAZSCRIPT_DOCS.keys()))
        return f"Unknown topic: '{topic}'\n\nAvailable topics: {available}"

    doc = _DAZSCRIPT_DOCS[topic]
    title = doc.get("title", topic.title())
    content = doc.get("content", "No content available.")

    return f"# {title}\n\n{content}"


@mcp.tool()
async def daz_find_actions(
    query: str,
    max_results: int = 30,
) -> dict[str, Any]:
    """Search DAZ Studio actions without walking Qt menus.

    ``MainWindow.menuBar()`` is not scriptable (not Q_INVOKABLE). Use this
    instead of guessing menu APIs. Searches ``DzActionMgr`` by className,
    simpleText, description, defaultMenu, and actionGroup.

    Does **not** trigger actions — many ``Dz*Action`` classes open modal
    dialogs and time out the script server.

    Args:
        query: Case-insensitive substring (e.g. ``"ERC Freeze"``,
            ``"DzERCFreezeAction"``, ``"Transfer Utility"``).
        max_results: Cap on returned matches (default 30, max 100).

    Returns:
        Dict with query, count, scanned, truncated, and
        matches[{className, simpleText, description, defaultMenu, actionGroup}].

    Examples:
        daz_find_actions("ERC Freeze")
        daz_find_actions("DzStrandHairCreateNodeAction")
    """
    # Stays on its registered script: dazpy has no DzActionMgr API, and this
    # is read-only discovery (it never triggers an action).
    return await _execute_by_id(
        "vangard-find-actions",
        {"query": query, "maxResults": max_results},
    )


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
    ops = []
    for i, op in enumerate(operations):
        if not isinstance(op, dict) or not {"nodeLabel", "propertyName", "value"} <= op.keys():
            raise ToolError(
                f"operations[{i}] needs nodeLabel, propertyName and value; got {op!r}")
        ops.append((op["nodeLabel"], op["propertyName"], op["value"]))

    def _run() -> dict[str, Any]:
        results = []
        for (node_label, _prop, _value), r in zip(ops, get_scene().set_numeric_properties(ops)):
            if r.ok:
                results.append({"success": True, "node": r.node, "property": r.property,
                                "value": r.value})
            else:
                results.append({"success": False, "node": node_label, "error": r.error})
        ok = sum(1 for r in results if r["success"])
        return {"results": results, "successCount": ok, "failureCount": len(results) - ok,
                "total": len(results)}

    return await run_tool(_run)


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
    kinds = ("all", "numeric", "transform", "morph", "bool", "string")
    if property_type not in kinds:
        raise ToolError(f"property_type must be one of {', '.join(kinds)}; got {property_type!r}")

    def _run() -> dict[str, Any]:
        node = get_scene().resolve_node(node_label)
        props = [{"label": d.label, "name": d.name, "type": d.type, "value": d.value,
                  "min": d.min, "max": d.max, "path": d.path, "is_animatable": d.is_animatable}
                 for d in node.property_details(property_type)]
        return {"node": node.describe().label, "properties": props, "count": len(props)}

    return await run_tool(_run)


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
    def _run() -> dict[str, Any]:
        node = get_scene().resolve_node(node_label)
        try:
            d = node.property_detail(property_name)
        except daz_exc.PropertyNotFoundError as e:
            raise ToolError(f"Property not found: {property_name} on {node_label}") from e
        return {"label": d.label, "name": d.name, "type": d.type, "current_value": d.value,
                "default_value": d.default, "min": d.min, "max": d.max,
                "is_animatable": d.is_animatable, "path": d.path,
                "node": node.describe().label}

    return await run_tool(_run)


# ---------------------------------------------------------------------------
# Tools — script / scene validation
# ---------------------------------------------------------------------------

@mcp.tool(tags={"desktop"})
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

    anti_patterns = [
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
        for pattern, is_error, message, suggestion in anti_patterns:
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
            "Use Scene.findNodeByLabel(), getNumSkeletons(), getNumCameras(), or "
            "getNumLights() instead"
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
    - Character/figure bounding box collisions (top-level figures only)
    - Whether anything lights the render (lights, environment dome/sun, camera
      headlamp; dazpy ``DazScene.check``), and single-light scenes
    - Whether each figure is in the active viewport camera's frame
    - Camera presence
    - Empty scene (no figures)

    Issue/warning ``type`` is ``collision``, a dazpy check code (``no_light``,
    ``no_subject_in_frame``, ``subject_out_of_frame``,
    ``subject_not_in_frame``), ``poor-lighting``, ``no-camera`` or
    ``no-figures``. ``findings`` holds the raw dazpy check findings.

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
                "lit": true
            },
            "findings": [...]
        }
    """
    return await run_tool(lambda: validate_scene(get_scene()))


# ---------------------------------------------------------------------------
# Tools — scene events
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_wait_for_scene_event(
    event_types: list[str],
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    """Wait for one of the specified scene events via the server's SSE stream.

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
    client = get_async_daz_client()

    async def _listen() -> dict[str, Any] | None:
        async for _, event in client.stream_scene_events(
            sorted(categories), stream_timeout=float(timeout_seconds + 5)
        ):
            if event.get("type") in event_types_set:
                return event
        return None

    try:
        result = await asyncio.wait_for(_listen(), timeout=float(timeout_seconds))
    except asyncio.TimeoutError as exc:
        raise ToolError(
            f"Timeout: none of {event_types} fired within {timeout_seconds}s"
        ) from exc
    except daz_exc.DazError as exc:
        handle_dazpy_error(exc)

    if result is None:
        raise ToolError(
            f"SSE stream closed before any of {event_types} was received"
        )
    return result


# ---------------------------------------------------------------------------
# Tools — intelligence / meta
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_auto_improve_scene() -> dict[str, Any]:
    """Automatically validate the scene and attempt to fix common issues."""
    validation = await run_tool(lambda: validate_scene(get_scene()))
    fixed = []
    if any(i["type"] == "no_light" for i in validation["issues"]):
        def _add_light() -> None:
            light = get_scene().create_light("distant")
            light.label = "Auto Light"
        await run_tool(_add_light)
        fixed.append("Added missing light")
    return {"validation": validation, "fixed": fixed, "count": len(fixed)}


@mcp.tool()
async def daz_get_performance_stats() -> dict[str, Any]:
    """Tool call statistics for this MCP server session.

    Returns ``tools`` (per tool: ``calls``, ``errors``, ``total_ms``, ``avg_ms``,
    ``max_ms``), ``total_calls`` and ``total_errors``. Counts start when the MCP
    server starts and cover every tool call except this one and
    daz_explain_last_error.
    """
    return _session_stats.performance_stats()


@mcp.tool(tags={"desktop"})
async def daz_explain_last_error() -> dict[str, Any]:
    """Explain the most recent tool error in this session and how to fix it.

    Returns ``last_error`` (``tool``, ``error_type``, ``message``, ``arguments``
    and ``at``, or null when no tool has failed yet) and ``hints``: fixes for
    the kind of error it was. With no error yet, ``hints`` lists the common
    errors and their fixes.
    """
    error = _session_stats.last_error()
    if error is None:
        return {
            "last_error": None,
            "hints": [hint for _, hint in _session_stats.ERROR_HINTS],
        }
    hints = _session_stats.hints_for(error["message"]) or [
        "No known cause matched. Read the message: a DazScript error names the "
        "line; a dazpy error names the node or property it couldn't use."
    ]
    return {"last_error": error, "hints": hints}
