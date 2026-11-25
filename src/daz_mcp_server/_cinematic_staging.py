"""Character staging for the cinematic tools, on dazpy: formations and
keyframed walking paths. Frames are timeline frames (the scripts these
replace passed frame numbers as DzTime ticks)."""
from __future__ import annotations

import math
from typing import Any

from fastmcp.exceptions import ToolError

from ._client import get_scene


def formation(arrangement: str, count: int, spacing: float,
              center: dict[str, float]) -> list[dict[str, float]]:
    """World positions for *count* characters in *arrangement* around *center*."""
    cx, cy, cz = center["x"], center["y"], center["z"]
    if arrangement == "line":
        start = cx - spacing * (count - 1) / 2
        return [{"x": start + i * spacing, "y": cy, "z": cz} for i in range(count)]
    if arrangement == "semicircle":
        radius = spacing * count / math.pi
        angles = [(i / (count - 1)) * math.pi if count > 1 else 0.0 for i in range(count)]
        return [{"x": cx + radius * math.sin(a), "y": cy, "z": cz - radius * math.cos(a)}
                for a in angles]
    if arrangement == "conversation-circle":
        return [{"x": cx + spacing * math.sin(2 * math.pi * i / count), "y": cy,
                 "z": cz + spacing * math.cos(2 * math.pi * i / count)} for i in range(count)]
    # triangle
    if count == 2:
        return [{"x": cx - spacing / 2, "y": cy, "z": cz},
                {"x": cx + spacing / 2, "y": cy, "z": cz}]
    if count == 3:
        return [{"x": cx, "y": cy, "z": cz - spacing * 0.6},
                {"x": cx - spacing / 2, "y": cy, "z": cz + spacing * 0.3},
                {"x": cx + spacing / 2, "y": cy, "z": cz + spacing * 0.3}]
    row1 = count // 2
    rows = [(row1, -0.6), (count - row1, 0.3)]
    return [{"x": cx + (i - (n - 1) / 2) * spacing, "y": cy, "z": cz + spacing * dz}
            for n, dz in rows for i in range(n)]


def _yaw_toward(pos: dict, target: tuple[float, float]) -> float:
    """Y rotation (degrees) turning a +Z-facing figure at *pos* toward (x, z)."""
    return math.degrees(math.atan2(target[0] - pos["x"], target[1] - pos["z"]))


def _facing_target(scene: Any, facing: str,
                   center: dict[str, float]) -> tuple[float, float] | None:
    """(x, z) the characters should face, or None to keep rotation 0."""
    if facing == "center":
        return (center["x"], center["z"])
    if facing == "camera":
        cam = scene.viewport_camera()
        if cam is None:
            raise ToolError("No active viewport camera to face")
        return (cam.position[0], cam.position[2])
    return None


def _placement_ops(ref: str, pos: dict, rot: float) -> list[tuple[str, str, float]]:
    return [(ref, "XTranslate", pos["x"]), (ref, "YTranslate", pos["y"]),
            (ref, "ZTranslate", pos["z"]), (ref, "YRotate", rot)]


def _plan(nodes: list, positions: list[dict],
          target: tuple[float, float] | None) -> tuple[list, list[dict]]:
    """Batched property writes and the per-character report for a formation."""
    ops, results = [], []
    for node, pos in zip(nodes, positions):
        info = node.describe()
        rot = _yaw_toward(pos, target) if target else 0.0
        ops += _placement_ops(str(info.element_id), pos, rot)
        results.append({"label": info.label,
                        "position": {k: round(v, 1) for k, v in pos.items()},
                        "rotation": round(rot, 1)})
    return ops, results


def arrange(labels: list[str], arrangement: str, spacing: float, facing: str,
            center: dict[str, float]) -> dict:
    """Place *labels* in a formation and turn them (one batched write)."""
    scene = get_scene()
    nodes = [scene.resolve_node(label) for label in labels]
    positions = formation(arrangement, len(nodes), spacing, center)
    target = _facing_target(scene, facing, center)
    ops, results = _plan(nodes, positions, target)
    failed = [r.error for r in scene.set_numeric_properties(ops) if not r.ok]
    if failed:
        raise ToolError(f"Could not place every character: {failed[0]}")
    return {"characters": results, "arrangement": arrangement, "spacing": spacing,
            "facing": facing, "count": len(results)}


def character_path(label: str, waypoints: list[dict[str, Any]]) -> dict:
    """Key the character's translation at each waypoint, and its Y rotation
    toward the next waypoint, in one call."""
    node = get_scene().resolve_node(label)
    wps = sorted(waypoints, key=lambda w: w["frame"])
    channels: dict[str, list[tuple[int, float]]] = {
        "XTranslate": [], "YTranslate": [], "ZTranslate": [], "YRotate": []}
    distance = 0.0
    for i, wp in enumerate(wps):
        pos, frame = wp["position"], int(wp["frame"])
        for axis in "xyz":
            channels[f"{axis.upper()}Translate"].append((frame, float(pos[axis])))
        if i:
            prev = wps[i - 1]["position"]
            distance += math.dist([pos[a] for a in "xyz"], [prev[a] for a in "xyz"])
        if i < len(wps) - 1:
            nxt = wps[i + 1]["position"]
            channels["YRotate"].append((frame, _yaw_toward(pos, (nxt["x"], nxt["z"]))))
    matches = node.key_numeric_candidates([([name], keys) for name, keys in channels.items()])
    missing = [m.candidates[0] for m in matches if not m.found]
    if missing:
        raise ToolError(f"{label} has no {', '.join(missing)} property")
    return {"character": node.describe().label, "waypointCount": len(wps),
            "keyframesSet": sum(len(k) for k in channels.values()),
            "frameRange": {"start": wps[0]["frame"], "end": wps[-1]["frame"]},
            "totalDistance": round(distance, 1)}
