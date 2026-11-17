"""Scene-level MCP tools for DAZ Studio.

Covers scene I/O, node hierarchy traversal, viewport selection, and
in-memory scene state checkpoints.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

from fastmcp.exceptions import ToolError

from .._mcp import mcp, _execute_by_id
from .._client import get_scene, run_dazpy
from .._errors import handle_dazpy_error

# ---------------------------------------------------------------------------
# In-memory checkpoint store (cleared on server restart)
# ---------------------------------------------------------------------------

_CHECKPOINTS: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Scene info / load / save
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
               Ignored for ``.obj`` — OBJ import always merges via the silent
               importer at scale 1 (1 unit = 1 cm).

    Returns:
      - success: true on success
      - file: the path that was loaded

    Do not pass ``.bvh`` files. The native BVH importer always opens a modal
    Studio dialog (Bug 11); this call blocks until a human clicks it, and
    leaving the dialog open can hang or crash Studio. Parse the BVH and set
    keys with ``setValue(time, value)`` instead.
    """
    if file_path.lower().endswith(".bvh"):
        raise ToolError(
            "BVH cannot be loaded via daz_load_file: DzBvhImporter always "
            "opens a modal dialog that blocks the script server until a human "
            "confirms it (Bug 11). Do not wait on this call. Parse the BVH and "
            "apply keys with setValue(time, value), or use a dedicated pipeline "
            "script. See D:/OpenCode/Projects/bvh-dialog-loesung.md"
        )
    if file_path.lower().endswith(".obj"):
        return await _execute_by_id(
            "vangard-import-obj",
            {"filePath": file_path, "scaleFactor": 1.0},
        )
    if merge:
        try:
            await run_dazpy(lambda: get_scene().load(file_path))
            return {"success": True, "file": file_path}
        except ToolError:
            raise
        except Exception as e:
            handle_dazpy_error(e)
    # merge=False: replace mode — fall back to the registered DazScript
    return await _execute_by_id("vangard-load-file", {"filePath": file_path, "merge": False})


@mcp.tool()
async def daz_save_scene(file_path: str | None = None) -> dict[str, Any]:
    """Save the current DAZ Studio scene to disk.

    Without ``file_path`` this is equivalent to File → Save (Ctrl+S) — it
    overwrites the scene's existing file. With ``file_path`` it performs a
    Save As to a new location.

    Args:
        file_path: Absolute path for Save As (e.g. ``"C:/scenes/hero_v02.duf"``).
                   If omitted, saves to the scene's current filename.

    Returns:
        Dict with saved (True) and file_path used.

    Examples:
        daz_save_scene()                              # overwrite current file
        daz_save_scene("C:/projects/scene_v02.duf")  # save as new file

    Notes:
        - If the scene has never been saved and no file_path is given, DAZ may
          open a Save dialog; provide an explicit path to avoid this.
        - Call before daz_delete_node or major scene changes as a safety checkpoint.
    """
    def _run() -> dict[str, Any]:
        scene = get_scene()
        target = file_path
        if target is None:
            target = scene.filename()
            if not target:
                raise ToolError(
                    "Scene has not been saved yet; provide a file_path."
                )
        scene.save(target)
        return {"saved": True, "file_path": target}

    try:
        return await run_dazpy(_run)
    except ToolError:
        raise
    except Exception as e:
        handle_dazpy_error(e)


@mcp.tool()
async def daz_save_scene_copy(path: str) -> dict[str, Any]:
    """Save a copy of the current scene to a new path without changing the scene's filename.

    Unlike ``daz_save_scene`` with a new path (which performs a Save As and updates
    the scene's internal filename pointer), this tool preserves the original filename.
    For clean scenes it does a pure file copy; for dirty scenes it saves to the
    destination then restores the original filename.

    Args:
        path: Absolute destination path for the copy
              (e.g. ``"C:/backups/scene_backup.duf"``).

    Returns:
        Dict with:
        - ok: True on success
        - path: destination path written
        - source: original scene path that was copied
        - method: ``"file-copy"`` (clean scene) or ``"save-restore"`` (dirty scene)

    Examples:
        daz_save_scene_copy("C:/backups/hero_v02.duf")
        daz_save_scene_copy("D:/archive/shot_001_backup.duf")

    Notes:
        - The scene's active filename remains unchanged after this call.
        - Use ``daz_save_scene`` when you actually want to switch to a new file.
        - If the destination directory does not exist the server will raise an error.
    """
    try:
        return await run_dazpy(lambda: get_scene().save_copy(path))
    except ToolError:
        raise
    except Exception as e:
        handle_dazpy_error(e)


# ---------------------------------------------------------------------------
# Node hierarchy
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_get_node_hierarchy(
    node_label: str | None = None,
    max_depth: int | None = None,
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
    args: dict[str, Any] = {}
    if node_label is not None:
        args["nodeLabel"] = node_label
    if max_depth is not None:
        args["maxDepth"] = max_depth
    return await _execute_by_id("vangard-get-node-hierarchy", args or None)


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
      - count: Number of children

    Example:
        # List children of Genesis 9 root
        result = daz_list_children("Genesis 9")
        # Returns: [{"label": "hip", "name": "hip"}]

        # Check if node has children
        result = daz_list_children("Camera 1")
        # result["count"] == 0 means no children

        # List bones under hip
        result = daz_list_children("hip")
        # Returns: pelvis, lThighBend, rThighBend
    """
    def _run() -> dict[str, Any]:
        scene = get_scene()
        node = scene.find_node_by_label(node_label)
        children = node.children
        items = [
            {"name": child._identifier.value, "label": child.label}  # pylint: disable=protected-access
            for child in children
        ]
        return {"node": node_label, "children": items, "count": len(items)}

    try:
        return await run_dazpy(_run)
    except ToolError:
        raise
    except Exception as e:
        handle_dazpy_error(e)


@mcp.tool()
async def daz_get_parent(node_label: str) -> dict[str, Any]:
    """Get parent node of a node.

    Returns the immediate parent of a node, or null if the node is a root node
    (no parent). Useful for traversing hierarchy upward.

    Args:
        node_label: Display label or internal name of the child node.

    Returns:
      - node: Child node label
      - parent: Parent node object with label and name, or null if no parent

    Example:
        # Get parent of a bone
        result = daz_get_parent("lHand")
        # Returns: {"parent": {"label": "lForearmBend", "name": "lForearmBend"}}

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
    def _run() -> dict[str, Any]:
        scene = get_scene()
        node = scene.find_node_by_label(node_label)
        parent = node.parent
        if parent is None:
            return {"node": node_label, "parent": None}
        return {
            "node": node_label,
            "parent": {
                "name": parent._identifier.value,  # pylint: disable=no-member,protected-access
                # astroid can't narrow `parent`'s type past the None-check above;
                # ._identifier.value is dazpy's documented way to read a node's
                # internal name (see daz-script-server's own README examples) —
                # used identically elsewhere in this file and camera_light.py.
                "label": parent.label,
            },
        }

    try:
        return await run_dazpy(_run)
    except ToolError:
        raise
    except Exception as e:
        handle_dazpy_error(e)


# ---------------------------------------------------------------------------
# Viewport selection
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_get_selected_nodes() -> dict[str, Any]:
    """Return the nodes currently selected in the DAZ Studio viewport.

    Useful when the user has manually selected items in DAZ Studio and wants
    the AI to act on that selection. The primary selection (last clicked) is
    flagged separately from any additional multi-selected nodes.

    Returns:
        Dict with:
        - count: total number of selected nodes
        - nodes: list of {label, name}

    Examples:
        daz_get_selected_nodes()
        # → {"count": 2, "nodes": [{"label": "Genesis 9", "name": "Genesis9"}, ...]}
    """
    def _run() -> dict[str, Any]:
        scene = get_scene()
        nodes = scene.selected_nodes()
        items = [
            {"name": n._identifier.value, "label": n.label}  # pylint: disable=protected-access
            for n in nodes
        ]
        return {"count": len(items), "nodes": items}

    try:
        return await run_dazpy(_run)
    except ToolError:
        raise
    except Exception as e:
        handle_dazpy_error(e)


# ---------------------------------------------------------------------------
# In-memory scene state checkpoints
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
        avail_str = (
            ", ".join(f'"{n}"' for n in available) if available else "(none saved)"
        )
        raise ToolError(
            f"Checkpoint '{checkpoint_name}' not found. Available: {avail_str}"
        )

    cp = _CHECKPOINTS[checkpoint_name]
    return await _execute_by_id("vangard-restore-scene-state", {
        "checkpointName": checkpoint_name,
        "nodes": cp["nodes"],
    })


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
