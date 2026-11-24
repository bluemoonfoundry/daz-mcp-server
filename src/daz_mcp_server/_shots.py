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


#: Default lens (mm) per dazpy shot size, for tools that create a camera for a size.
SIZE_LENSES: dict[str, float] = {
    "extreme_wide": 24.0, "wide": 35.0, "full_body": 35.0, "medium_wide": 50.0,
    "medium": 50.0, "medium_close_up": 85.0, "close_up": 85.0, "extreme_close_up": 100.0,
}

#: MCP shot types that frame a subject together with a partner.
PAIR_TYPES = frozenset({"two-shot", "over-shoulder"})

_AHEAD = "_view"  # stand-in actor for "where the subject looks" when there is no partner


def orbit_position(target: Vec3, azimuth: float, elevation: float, distance: float,
                   focal_length: float = 50.0) -> Vec3:
    """Camera position *distance* from *target* at the given angles (dazpy framing math)."""
    from dazpy.shots import Framing, framing_transform
    framing = Framing(subjects=(target,), azimuth_deg=azimuth, elevation_deg=elevation,
                      distance_cm=distance)
    return framing_transform([(target, False)], framing, focal_length)[0]


def pose(shot: Shot, positions: dict[str, Vec3]) -> tuple[Vec3, Vec3]:
    """``(camera position, aim point)`` of a static *shot*, without touching the scene."""
    from dazpy.shots import Framing, framing_transform
    c = shot.camera
    if isinstance(c, Framing):
        points = [(positions[s], True) if isinstance(s, str) else (s, False) for s in c.subjects]
        return framing_transform(points, c, shot.lens.focal_length)
    look = c.look_at
    if isinstance(look, str):
        look = positions[look] + Vec3(0.0, c.look_at_offset_cm, 0.0)
    if look is None:
        look = sl.aim_from_rotation(c.position, c.rotation) if c.rotation else c.position
    return c.position, look


def size_shot(shot_type: str, key: str, positions: dict[str, Vec3], *,
              partner: str | None = None, focal_length: float | None = None,
              distance: float | None = None, azimuth: float = 0.0,
              elevation: float | None = None, composition: str = "center",
              shot_id: str | None = None, **shot_kw: Any) -> Shot:
    """A dazpy :class:`Shot` for an MCP *shot_type* on subject *key*.

    Sizes are a :class:`~dazpy.shots.Framing` at *azimuth* (0 = the subject's
    front, ``+Z``). ``"two-shot"`` frames *key* and *partner* from the side of
    the line between them; ``"over-shoulder"`` looks over *partner*'s
    shoulder onto *key*. Without a partner, a two-shot falls back to a
    medium-wide single and an over-shoulder looks over *key*'s own shoulder
    in the direction it faces.
    """
    from dataclasses import replace

    from dazpy.shots import Framing, Lens
    lens = Lens(focal_length=focal_length) if focal_length else None
    if shot_type == "over-shoulder":
        if partner is None:
            root = positions[key]
            ahead = root + Vec3(0.0, 0.0, 150.0)  # Genesis figures face +Z
            line = sl.LineOfAction(key, _AHEAD, root, ahead)
            shot = sl.over_the_shoulder(line, key, _AHEAD, lens=lens,
                                        id=shot_id or sl.shot_name("ots", key, tag="view"))
        else:
            line = sl.LineOfAction.between(positions, partner, key)
            shot = sl.over_the_shoulder(line, partner, key, lens=lens, id=shot_id)
        return replace(shot, **shot_kw) if shot_kw else shot
    if shot_type == "two-shot" and partner is not None:
        line = sl.LineOfAction.between(positions, key, partner)
        shot = sl.two_shot(line, lens=lens, id=shot_id)
        return replace(shot, **shot_kw) if shot_kw else shot
    size = SHOT_TYPES.get(shot_type, "medium_wide")
    framing = Framing(subjects=(key,), size=size, azimuth_deg=azimuth, elevation_deg=elevation,
                      composition=composition, distance_cm=distance)
    return Shot(id=shot_id or sl.shot_name(size, key), camera=framing,
                lens=lens or Lens(focal_length=SIZE_LENSES[size]), **shot_kw)


def figure_positions(scene: Any) -> dict[str, Vec3]:
    """Root positions of the scene's root-level figures, by label."""
    out: dict[str, Vec3] = {}
    for fig in scene.overview().get("figures", []):
        label = fig.get("label") or fig.get("name")
        if label and label not in out:
            try:
                out[label] = subject(scene, label).root
            except NodeNotFoundError:
                continue
    return out


def nearest(positions: dict[str, Vec3], key: str) -> str | None:
    """The label in *positions* (other than *key*) closest to *key*, or ``None``."""
    here = positions[key]
    others = [(here.distance(p), k) for k, p in positions.items() if k != key]
    return min(others)[1] if others else None


def find_camera(scene: Any, label: str) -> Any | None:
    """The camera labelled *label*, or ``None``."""
    try:
        return camera(scene, label)
    except NodeNotFoundError:
        return None


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


def group_node(scene: Any, label: str, at: Vec3) -> Any:
    """The group node labelled *label*, created at *at* when absent."""
    try:
        return scene.find_node_by_label(label)
    except NodeNotFoundError:
        return scene.create_group(label, position=(at.x, at.y, at.z))
