"""Spatial analysis tools: bounding boxes, overlap, and scene layout."""
from __future__ import annotations

import math
from typing import Any

from .._mcp import mcp
from .._client import get_scene, run_dazpy
from .._errors import handle_dazpy_error


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
    def _run() -> dict[str, Any]:
        scene = get_scene()
        node = scene.find_node_by_label(node_label)
        world_pos = node.position
        local_pos = node.local_position
        euler = node.local_euler  # tuple (x, y, z) in degrees
        scale = node.scale  # dict {"x", "y", "z", "general"}
        rotation: dict[str, Any] | None = None
        if euler is not None:
            rotation = {"x": euler[0], "y": euler[1], "z": euler[2]}
        return {
            "node": node_label,
            "world_position": world_pos,
            "local_position": local_pos,
            "rotation": rotation,
            "scale": scale,
        }

    try:
        return await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)


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
    def _run() -> dict[str, Any]:
        scene = get_scene()
        node = scene.find_node_by_label(node_label)
        bb = node.bounding_box()
        if bb is None:
            return {"node": node_label, "error": "bounding box not available"}
        mn = bb["min"]
        mx = bb["max"]
        center = {
            "x": (mn["x"] + mx["x"]) / 2.0,
            "y": (mn["y"] + mx["y"]) / 2.0,
            "z": (mn["z"] + mx["z"]) / 2.0,
        }
        return {
            "node": node_label,
            "min": mn,
            "max": mx,
            "center": center,
            "width": mx["x"] - mn["x"],
            "height": mx["y"] - mn["y"],
            "depth": mx["z"] - mn["z"],
        }

    try:
        return await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)


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
    def _run() -> dict[str, Any]:
        scene = get_scene()
        n1 = scene.find_node_by_label(node1_label)
        n2 = scene.find_node_by_label(node2_label)
        p1 = n1.position
        p2 = n2.position
        dx = p2["x"] - p1["x"]
        dy = p2["y"] - p1["y"]
        dz = p2["z"] - p1["z"]
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        horizontal = math.sqrt(dx * dx + dz * dz)
        return {
            "node1": node1_label,
            "node2": node2_label,
            "distance": distance,
            "vector": {"dx": dx, "dy": dy, "dz": dz},
            "horizontal_distance": horizontal,
            "vertical_distance": abs(dy),
        }

    try:
        return await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)


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
    def _run() -> dict[str, Any]:
        scene = get_scene()
        n1 = scene.find_node_by_label(node1_label)
        n2 = scene.find_node_by_label(node2_label)
        p1 = n1.position
        p2 = n2.position
        dx = p2["x"] - p1["x"]
        dy = p2["y"] - p1["y"]
        dz = p2["z"] - p1["z"]
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        horizontal = math.sqrt(dx * dx + dz * dz)

        # Horizontal direction: DAZ +Z = front, +X = right
        if abs(dx) >= abs(dz):
            h_dir = "right" if dx >= 0 else "left"
        else:
            h_dir = "front" if dz >= 0 else "back"

        v_dir = "above" if dy >= 0 else "below"

        # Angles in degrees
        angle_h = math.degrees(math.atan2(dx, dz))
        if horizontal > 0:
            angle_v = math.degrees(math.atan2(dy, horizontal))
        else:
            angle_v = 90.0 if dy >= 0 else -90.0

        # Bounding-box overlap check
        bb1 = n1.bounding_box()
        bb2 = n2.bounding_box()
        overlapping = False
        if bb1 is not None and bb2 is not None:
            overlapping = (
                bb1["min"]["x"] <= bb2["max"]["x"]
                and bb1["max"]["x"] >= bb2["min"]["x"]
                and bb1["min"]["y"] <= bb2["max"]["y"]
                and bb1["max"]["y"] >= bb2["min"]["y"]
                and bb1["min"]["z"] <= bb2["max"]["z"]
                and bb1["max"]["z"] >= bb2["min"]["z"]
            )

        relative_position = (
            f"{node2_label} is {h_dir} {v_dir} of {node1_label} "
            f"({int(distance)} cm away)"
        )

        return {
            "node1": node1_label,
            "node2": node2_label,
            "distance": distance,
            "direction": h_dir,
            "angle_horizontal": angle_h,
            "angle_vertical": angle_v,
            "relative_position": relative_position,
            "overlapping": overlapping,
        }

    try:
        return await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)


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
    def _run() -> dict[str, Any]:
        scene = get_scene()
        n1 = scene.find_node_by_label(node1_label)
        n2 = scene.find_node_by_label(node2_label)
        bb1 = n1.bounding_box()
        bb2 = n2.bounding_box()

        if bb1 is None or bb2 is None:
            return {"overlaps": False, "reason": "bounding box not available"}

        overlaps = (
            bb1["min"]["x"] <= bb2["max"]["x"]
            and bb1["max"]["x"] >= bb2["min"]["x"]
            and bb1["min"]["y"] <= bb2["max"]["y"]
            and bb1["max"]["y"] >= bb2["min"]["y"]
            and bb1["min"]["z"] <= bb2["max"]["z"]
            and bb1["max"]["z"] >= bb2["min"]["z"]
        )

        result: dict[str, Any] = {
            "node1": node1_label,
            "node2": node2_label,
            "overlapping": overlaps,
        }

        if overlaps:
            x_overlap = (
                min(bb1["max"]["x"], bb2["max"]["x"]) - max(bb1["min"]["x"], bb2["min"]["x"])
            )
            y_overlap = (
                min(bb1["max"]["y"], bb2["max"]["y"]) - max(bb1["min"]["y"], bb2["min"]["y"])
            )
            z_overlap = (
                min(bb1["max"]["z"], bb2["max"]["z"]) - max(bb1["min"]["z"], bb2["min"]["z"])
            )
            pen_depth = min(x_overlap, y_overlap, z_overlap)

            if x_overlap <= y_overlap and x_overlap <= z_overlap:
                suggestion = (
                    f"Move {node2_label} {x_overlap:.0f} cm in +X direction to resolve collision"
                )
            elif z_overlap <= x_overlap and z_overlap <= y_overlap:
                suggestion = (
                    f"Move {node2_label} {z_overlap:.0f} cm in +Z direction to resolve collision"
                )
            else:
                suggestion = (
                    f"Move {node2_label} {y_overlap:.0f} cm in +Y direction to resolve collision"
                )

            result["penetration_depth"] = pen_depth
            result["suggestion"] = suggestion

        return result

    try:
        return await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)


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
    def _run() -> dict[str, Any]:
        scene = get_scene()
        transforms = scene.all_node_transforms()
        nodes = []
        for t in transforms:
            pos_raw = t.get("position", [0.0, 0.0, 0.0])
            rot_raw = t.get("rotation", [0.0, 0.0, 0.0])
            entry: dict[str, Any] = {
                "label": t.get("label", t.get("name", "")),
                "position": {"x": pos_raw[0], "y": pos_raw[1], "z": pos_raw[2]},
                "rotation": {"x": rot_raw[0], "y": rot_raw[1], "z": rot_raw[2]},
                "visible": t.get("visible", True),
            }
            nodes.append(entry)
        return {"nodes": nodes, "count": len(nodes)}

    try:
        return await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)


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
    def _run() -> dict[str, Any]:
        scene = get_scene()
        center_node = scene.find_node_by_label(node_label)
        center_pos = center_node.position  # {"x", "y", "z"}

        transforms = scene.all_node_transforms()
        nearby: list[dict[str, Any]] = []

        for t in transforms:
            label = t.get("label", t.get("name", ""))
            if label == node_label:
                continue  # skip the centre node itself

            pos_raw = t.get("position", [0.0, 0.0, 0.0])
            dx = pos_raw[0] - center_pos["x"]
            dy = pos_raw[1] - center_pos["y"]
            dz = pos_raw[2] - center_pos["z"]
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)

            if dist > radius:
                continue

            # Cardinal direction (horizontal plane, DAZ +Z=front, +X=right)
            if abs(dx) >= abs(dz):
                direction = "right" if dx >= 0 else "left"
            else:
                direction = "front" if dz >= 0 else "back"

            nearby.append({
                "label": label,
                "distance": dist,
                "direction": direction,
            })

        nearby.sort(key=lambda n: n["distance"])

        return {
            "center_node": node_label,
            "radius": radius,
            "nearby_nodes": nearby,
            "count": len(nearby),
        }

    try:
        return await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)
