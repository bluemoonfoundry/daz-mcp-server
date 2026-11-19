"""Scene lookups for the cinematic tools; every shot is built by ``dazpy.shot_library``.

The tools resolve labels to subject positions and cameras here, build
``dazpy.shots.Shot`` models with ``dazpy.shot_library``, and apply them with
``dazpy.shots.apply_shot`` / ``shot_library.apply_coverage``. No camera
geometry lives in this package.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dazpy import shot_library as sl
from dazpy.exceptions import NodeNotFoundError
from dazpy.math3 import Vec3
from dazpy.shots import Shot

#: MCP shot-type names -> dazpy shot sizes.
SHOT_TYPES: dict[str, str] = {
    "extreme-close-up": "extreme_close_up",
    "close-up": "close_up",
    "medium-close-up": "medium_close_up",
    "medium-shot": "medium",
    "medium-full": "medium_wide",
    "full-shot": "full_body",
    "wide-shot": "wide",
    "extreme-wide": "extreme_wide",
}

#: What each shot size shows, for tool results.
FRAMING_NOTES: dict[str, str] = {
    "extreme_close_up": "eyes and mouth detail",
    "close_up": "face and head",
    "medium_close_up": "head and shoulders",
    "medium": "waist up",
    "medium_wide": "knees up",
    "full_body": "entire body with breathing room",
    "wide": "body within environment",
    "extreme_wide": "figure small in a wide environment",
}


@dataclass
class Subject:
    """A scene node resolved for framing: its label, root point and whether it is a figure."""

    label: str
    root: Vec3
    is_figure: bool
    center: Vec3

    @property
    def focus_point(self) -> Vec3:
        """Eyes for a figure, bounding-box centre otherwise."""
        return sl.focus_point(self.label, {self.label: self.root}) if self.is_figure else self.center


def _find(scene: Any, label: str) -> tuple[Any, bool]:
    try:
        return scene.find_skeleton_by_label(label), True
    except NodeNotFoundError:
        pass
    try:
        return scene.find_node_by_label(label), False
    except NodeNotFoundError:
        return scene.find_node(label), False


def subject(scene: Any, label: str) -> Subject:
    """Resolve *label* (a figure, prop or any node) to a :class:`Subject`.

    A figure's root is its world position (on the floor under it); another
    node's is the bottom centre of its bounding box, falling back to its
    position when it has no geometry.

    Raises:
        NodeNotFoundError: No node has that label or name.
    """
    node, is_figure = _find(scene, label)
    pos = Vec3.from_dict(node.position or {"x": 0.0, "y": 0.0, "z": 0.0})
    bb = node.bounding_box()
    if bb and bb["max"]["y"] >= bb["min"]["y"] and abs(bb["max"]["y"]) < 1e8:
        mn, mx = bb["min"], bb["max"]
        cx, cz = (mn["x"] + mx["x"]) / 2, (mn["z"] + mx["z"]) / 2
        center = Vec3(cx, (mn["y"] + mx["y"]) / 2, cz)
        root = pos if is_figure else Vec3(cx, mn["y"], cz)
    else:
        root, center = pos, pos
    return Subject(label=label, root=root, is_figure=is_figure, center=center)


def camera(scene: Any, label: str) -> Any:
    """The camera labelled (or, failing that, named) *label*."""
    try:
        return scene.find_camera_by_label(label)
    except NodeNotFoundError:
        from dazpy import DazCamera
        node = scene.find_node(label)  # raises NodeNotFoundError when absent
        return DazCamera(node._client, node._identifier)  # pylint: disable=protected-access


def camera_pose(cam: Any) -> tuple[Vec3, dict]:
    """``(world position, world rotation quaternion)`` of *cam*."""
    return Vec3.from_dict(cam.position), cam.rotation


def horizontal_view(cam_pos: Vec3, target: Vec3, minimum: float = 50.0,
                    fallback: float = 250.0) -> tuple[float, float]:
    """``(azimuth_deg, horizontal distance)`` of a camera around *target*;
    a camera closer than *minimum* gets *fallback* distance on the ``+Z`` side."""
    import math
    dx, dz = cam_pos.x - target.x, cam_pos.z - target.z
    dist = math.hypot(dx, dz)
    if dist < minimum:
        return 0.0, fallback
    return math.degrees(math.atan2(dx, dz)), dist


def vec(v: Vec3, ndigits: int = 1) -> dict[str, float]:
    return {"x": round(v.x, ndigits), "y": round(v.y, ndigits), "z": round(v.z, ndigits)}


def shot_summary(shot: Shot, cam_label: str, positions: dict[str, Vec3]) -> dict[str, Any]:
    """Result entry for an applied shot."""
    pos = sl.camera_position(shot, positions)
    out: dict[str, Any] = {
        "label": cam_label,
        "shotId": shot.id,
        "position": vec(pos),
        "focalLength": shot.lens.focal_length,
        "animated": shot.movement is not None,
    }
    if shot.frame_range is not None:
        out["frameRange"] = {"start": shot.frame_range[0], "end": shot.frame_range[1]}
    size = getattr(shot.camera, "size", None)
    if size is not None and shot.movement is None:
        out["size"] = size
    return out


def issues(found: list[sl.ContinuityIssue]) -> list[dict[str, Any]]:
    return [{"kind": i.kind, "shot": i.shot_id, "message": i.message,
             **({"previousShot": i.other_shot_id} if i.other_shot_id else {})} for i in found]


async def run(fn: Any) -> Any:
    """Run the synchronous dazpy body *fn* off the event loop, mapping errors to ToolError."""
    from fastmcp.exceptions import ToolError

    from ._client import run_dazpy
    from ._errors import handle_dazpy_error

    try:
        return await run_dazpy(fn)
    except ToolError:
        raise
    except ValueError as exc:  # invalid shot geometry/arguments from dazpy.shot_library
        raise ToolError(str(exc)) from exc
    except Exception as exc:  # pylint: disable=broad-exception-caught
        handle_dazpy_error(exc)
