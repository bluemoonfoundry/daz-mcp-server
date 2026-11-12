"""Node transform tools: properties, selection, parenting, and deletion."""
from __future__ import annotations

from typing import Any

from .._mcp import mcp, _execute_by_id
from .._client import get_scene, run_dazpy
from .._errors import handle_dazpy_error


@mcp.tool()
async def daz_get_node(node_label: str) -> dict[str, Any]:
    """Return all numeric properties of a scene node.

    Useful for reading transforms (X Translate, Y Translate, Z Translate,
    X Rotate, Y Rotate, Z Rotate, Scale), morph dials, and any other
    numeric property on the node.

    Args:
        node_label: Display label, internal name, numeric elementID, or
                    ``Parent/Label`` path (e.g. ``"Genesis 8 Female/hip"``).
                    Duplicate labels raise instead of picking the first match.

    Returns a dict with:
      - name: internal node name
      - label: display label
      - type: DazScript class name (e.g. DzFigure, DzBone, DzCamera)
      - elementID: unique scene element id
      - parent: parent node label, or null
      - properties: mapping of property label → current numeric value
    """
    return await _execute_by_id("vangard-get-node", {"nodeLabel": node_label})


@mcp.tool()
async def daz_find_nodes(query: str) -> dict[str, Any]:
    """List every scene node whose label or internal name equals ``query``.

    Use this when a label is shared (e.g. two nodes named ``Hip``). Each match
    includes ``elementID`` and ``parent`` so a later ``daz_get_node`` /
    ``daz_set_property`` can target one node uniquely.

    Args:
        query: Exact display label or internal name.

    Returns:
        Dict with query, count, and matches[{label, name, type, elementID, parent}].
    """
    return await _execute_by_id("vangard-find-nodes", {"query": query})


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
async def daz_delete_node(node_label: str) -> dict[str, Any]:
    """Remove a node and its children from the scene.

    This is a destructive operation — the node cannot be recovered without
    reloading from file. DAZ Studio's remove operation always includes child
    nodes; bones attached to a figure should not be deleted directly (delete
    the root figure instead).

    Args:
        node_label: Display label or internal name of the node to delete.

    Returns:
        Dict with deleted (label confirmed) and child_count (children removed).

    Examples:
        daz_delete_node("Key Light")
        daz_delete_node("Fill Light")
        daz_delete_node("Camera 2")

    Notes:
        - Use daz_scene_info or daz_list_lights / daz_list_cameras first to
          confirm the exact label before deleting.
        - Save the scene first with daz_save_scene if you want a recovery point.
    """
    return await _execute_by_id("vangard-delete-node", {"nodeLabel": node_label})


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
# Property name → dazpy setter mapping
# ---------------------------------------------------------------------------

def _apply_transforms_to_node(node: Any, transforms: dict[str, float]) -> list[str]:
    """Apply a transforms dict to a DazNode; return list of applied property names."""
    applied: list[str] = []

    # Collect translation axes, then apply as a single call if any present
    tx = transforms.get("XTranslate")
    ty = transforms.get("YTranslate")
    tz = transforms.get("ZTranslate")
    if tx is not None or ty is not None or tz is not None:
        cur = node.local_position or {"x": 0.0, "y": 0.0, "z": 0.0}
        nx = float(tx) if tx is not None else cur["x"]
        ny = float(ty) if ty is not None else cur["y"]
        nz = float(tz) if tz is not None else cur["z"]
        node.set_local_position(nx, ny, nz)
        if tx is not None:
            applied.append("XTranslate")
        if ty is not None:
            applied.append("YTranslate")
        if tz is not None:
            applied.append("ZTranslate")

    # Rotation axes
    rx = transforms.get("XRotate")
    ry = transforms.get("YRotate")
    rz = transforms.get("ZRotate")
    if rx is not None or ry is not None or rz is not None:
        cur_euler = node.local_euler
        cx = cur_euler[0] if cur_euler else 0.0
        cy = cur_euler[1] if cur_euler else 0.0
        cz = cur_euler[2] if cur_euler else 0.0
        node.set_local_rotation(
            float(rx) if rx is not None else cx,
            float(ry) if ry is not None else cy,
            float(rz) if rz is not None else cz,
        )
        if rx is not None:
            applied.append("XRotate")
        if ry is not None:
            applied.append("YRotate")
        if rz is not None:
            applied.append("ZRotate")

    return applied


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
        transforms: Dictionary of property names to values
            (e.g., {"XTranslate": 50, "YRotate": 45}).

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
    def _run() -> dict[str, Any]:
        scene = get_scene()
        results: list[dict[str, Any]] = []
        for label in node_labels:
            try:
                node = scene.find_node_by_label(label)
                applied = _apply_transforms_to_node(node, transforms)
                results.append({
                    "nodeLabel": label,
                    "success": True,
                    "applied": applied,
                })
            except Exception as e:
                results.append({
                    "nodeLabel": label,
                    "success": False,
                    "error": str(e),
                })
        success_count = sum(1 for r in results if r["success"])
        return {
            "results": results,
            "successCount": success_count,
            "failureCount": len(results) - success_count,
            "total": len(results),
        }

    try:
        return await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)


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
    def _run() -> dict[str, Any]:
        scene = get_scene()
        results: list[dict[str, Any]] = []
        for label in node_labels:
            try:
                node = scene.find_node_by_label(label)
                node.visible = visible
                results.append({
                    "nodeLabel": label,
                    "success": True,
                    "visible": visible,
                })
            except Exception as e:
                results.append({
                    "nodeLabel": label,
                    "success": False,
                    "error": str(e),
                })
        success_count = sum(1 for r in results if r["success"])
        return {
            "results": results,
            "successCount": success_count,
            "failureCount": len(results) - success_count,
            "total": len(results),
        }

    try:
        return await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)


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
    def _run() -> dict[str, Any]:
        scene = get_scene()
        selected: list[str] = []
        for label in node_labels:
            try:
                node = scene.find_node_by_label(label)
                node.select(True)
                selected.append(label)
            except Exception:
                pass  # silently skip nodes that don't exist
        return {
            "selected": selected,
            "count": len(selected),
            "total": len(node_labels),
        }

    try:
        return await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)
