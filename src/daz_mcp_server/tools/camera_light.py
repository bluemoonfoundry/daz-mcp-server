"""Camera and lighting tools for the Vangard DAZ MCP server."""
from __future__ import annotations

import math
import re
from typing import Any

from fastmcp.exceptions import ToolError

from dazpy import shot_library as sl
from dazpy.math3 import Vec3
from dazpy.shots import CAMERA_ANGLES, Framing, Lens, Placement, Shot, apply_shot, framing_transform

from dazpy import DazRenderSettings
from dazpy.exceptions import PropertyNotFoundError

from .._mcp import mcp
from .._client import get_daz_client, get_scene
from .._errors import run_tool
from .. import _shots


# ---------------------------------------------------------------------------
# Mood / time-of-day presets (used by new inline-script tools)
# ---------------------------------------------------------------------------

MOOD_PRESETS: dict[str, dict[str, Any]] = {
    "romantic":     {"intensity": 0.6,  "color": [255, 200, 150]},  # warm, soft
    "dramatic":     {"intensity": 1.5,  "color": [200, 200, 220]},  # high contrast, blue-white
    "scary":        {"intensity": 0.4,  "color": [100, 130, 180]},  # cold, dim
    "golden-hour":  {"intensity": 1.2,  "color": [255, 200, 100]},  # golden warm
    "mysterious":   {"intensity": 0.5,  "color": [150, 150, 200]},  # cool blue
    "peaceful":     {"intensity": 0.8,  "color": [255, 220, 180]},  # soft warm
}

TIME_OF_DAY_PRESETS: dict[str, dict[str, Any]] = {
    "dawn":         {"intensity": 0.5,  "color": [255, 180, 120]},
    "morning":      {"intensity": 0.8,  "color": [255, 220, 180]},
    "noon":         {"intensity": 1.5,  "color": [255, 255, 240]},
    "golden-hour":  {"intensity": 1.2,  "color": [255, 200, 100]},
    "dusk":         {"intensity": 0.6,  "color": [200, 120, 100]},
    "night":        {"intensity": 0.15, "color": [60,  60,  120]},
}


# ---------------------------------------------------------------------------
# Camera tools
# ---------------------------------------------------------------------------

_COMPOSITION_RULES: dict[str, tuple[float, float, str]] = {
    # rule: (screen x of the subject, camera elevation deg, explanation)
    "rule-of-thirds": (sl.THIRD_X, 0.0, "Subject on the right vertical third at eye level"),
    "golden-ratio": (sl.GOLDEN_X, 0.0, "Subject on the right golden section (0.382 / 0.618 split)"),
    "center-frame": (0.0, 0.0, "Subject centred in frame"),
    "leading-lines": (-sl.THIRD_X, -10.0,
                      "Low angle, subject on the left third: the frame leads in diagonally"),
}

#: angle: (camera elevation deg, roll deg, note)
_CAMERA_ANGLES: dict[str, tuple[float, float, str]] = {
    "eye-level": (CAMERA_ANGLES["eye_level"], 0.0, "Camera at eye height — neutral perspective"),
    "high-angle": (CAMERA_ANGLES["high"], 0.0,
                   "Camera above subject — creates vulnerable or diminished feel"),
    "low-angle": (CAMERA_ANGLES["low"], 0.0,
                  "Camera below eye level — creates powerful or dominant feel"),
    "dutch-angle": (0.0, 15.0, "Camera rolled 15° about the lens axis — unease or tension"),
    "overhead": (89.0, 0.0, "Bird's eye view from directly overhead"),
    "worms-eye": (CAMERA_ANGLES["worms_eye"], 0.0, "Low looking up — extreme dramatic low angle"),
    "over-shoulder": (0.0, 0.0, "Over-the-shoulder perspective — conversation/reaction shot"),
}


_PRESET_TRANSFORMS = ("XTranslate", "YTranslate", "ZTranslate", "XRotate", "YRotate",
                      "ZRotate", "XScale", "YScale", "ZScale")

# preset -> [(label, flux, azimuth deg, elevation deg, light type, shadow softness)]
_LIGHTING_PRESETS: dict[str, list[tuple[str, float, float, float, str, float]]] = {
    "three-point": [("Key Light", 2000, 45, 35, "spot", 30),
                    ("Fill Light", 800, -45, 20, "spot", 60),
                    ("Rim Light", 1200, 180, 45, "distant", 20)],
    "rembrandt": [("Key Light", 2200, 45, 45, "spot", 20),
                  ("Fill Light", 400, -90, 10, "spot", 80)],
    "butterfly": [("Key Light", 2000, 0, 45, "spot", 25),
                  ("Fill Light", 500, 0, -5, "spot", 80)],
    "split": [("Key Light", 2200, 90, 15, "spot", 15),
              ("Rim Light", 800, -90, 20, "spot", 40)],
    "loop": [("Key Light", 2000, 35, 30, "spot", 35),
             ("Fill Light", 700, -50, 15, "spot", 70),
             ("Rim Light", 900, 160, 40, "spot", 25)],
}


def _unique_name(scene: Any, label: str, fallback: str) -> str:
    """An internal node name from *label* that no scene node uses yet."""
    base = re.sub(r"[^A-Za-z0-9_]", "_", label) or fallback
    name, n = base, 1
    while scene.find_nodes(name):
        n += 1
        name = f"{base}_{n}"
    return name


def _box_center(node: Any) -> tuple[float, float, float]:
    """World centre of *node*'s bounding box (its origin if it has no geometry)."""
    box = node.bounding_box()
    if not box:
        p = node.position
        return (p["x"], p["y"], p["z"])
    return tuple((box["min"][k] + box["max"][k]) / 2 for k in "xyz")  # type: ignore[return-value]


def _tint_lights(intensity: float, color: tuple[int, int, int] | list[int]) -> int:
    """Set every scene light's Intensity and Color; returns how many."""
    lights = get_scene().lights()
    for light in lights:
        light.intensity = intensity
        light.set_color(*color)
    return len(lights)


def _preset_light_position(center: dict, radius: float, height: float,
                           az_deg: float, el_deg: float) -> tuple[float, float, float]:
    a, e = math.radians(az_deg), math.radians(el_deg)
    return (center["x"] + radius * math.sin(a) * math.cos(e),
            center["y"] + radius * math.sin(e) + height * 0.1,
            center["z"] + radius * math.cos(a) * math.cos(e))


def _place_preset_light(scene: Any, spec: tuple, center: dict, radius: float, height: float,
                        aim: tuple[float, float, float]) -> dict[str, Any]:
    """Create one preset light on a sphere around *center*, aimed at *aim*."""
    label, flux, az, el, kind, softness = spec
    pos = _preset_light_position(center, radius, height, az, el)
    light = scene.create_light(kind)
    light.label = label
    light.set_position(*pos)
    light.set_numeric_property("Flux", float(flux))
    light.set_numeric_property("Shadow Softness", float(softness))
    light.aim_at(*aim)
    return {"label": label, "type": "DzSpotLight" if kind == "spot" else "DzDistantLight",
            "position": {k: round(v) for k, v in zip("xyz", pos)}, "flux": flux}


def _apply_lighting_preset(preset: str, subject_label: str | None) -> dict[str, Any]:
    scene = get_scene()
    center, height = {"x": 0.0, "y": 150.0, "z": 0.0}, 170.0
    if subject_label:
        box = scene.resolve_node(subject_label).bounding_box()
        if box:
            center = {k: (box["min"][k] + box["max"][k]) / 2 for k in "xyz"}
            height = box["max"]["y"] - box["min"]["y"]
    face_y = center["y"] + height * 0.2
    radius = height * 1.2
    defs = _LIGHTING_PRESETS[preset]
    labels = {d[0] for d in defs}
    for old in scene.light_info():  # replace a previous run's lights
        if old.label in labels:
            scene.resolve_node(str(old.element_id)).delete()
    aim = (center["x"], face_y, center["z"])
    created = [_place_preset_light(scene, d, center, radius, height, aim) for d in defs]
    env_set = DazRenderSettings(get_daz_client()).set_environment_mode("scene_only")
    return {"preset": preset, "subject": subject_label, "lights_created": created,
            "environment_mode": "Scene Only (3)" if env_set else
            "unchanged (no environment node yet; it is created by the first Iray render)"}


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
    def _run() -> dict[str, Any]:
        scene = get_scene()
        previous = scene.set_viewport_camera(camera_label)
        return {"success": True, "camera": scene.viewport_camera().label,
                "previousCamera": previous}

    return await run_tool(_run)


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
    def _run() -> dict[str, Any]:
        scene = get_scene()
        cam = scene.resolve_node(camera_label)
        target = scene.resolve_node(target_label)
        t = target.position
        h, v = math.radians(angle_horizontal), math.radians(angle_vertical)
        pos = {"x": t["x"] + distance * math.cos(v) * math.sin(h),
               "y": t["y"] + distance * math.sin(v),
               "z": t["z"] + distance * math.cos(v) * math.cos(h)}
        cam.set_position(pos["x"], pos["y"], pos["z"])
        cam.aim_at(t["x"], t["y"], t["z"])
        return {"success": True, "camera": cam.describe().label,
                "target": target.describe().label, "position": pos, "targetPosition": t}

    return await run_tool(_run)


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
    def _run() -> dict[str, Any]:
        scene = get_scene()
        cam = scene.resolve_node(camera_label)
        node = scene.resolve_node(node_label)
        box = node.bounding_box()
        if not box:
            raise ToolError(f"Node has no geometry to frame: {node_label}")
        center = {k: (box["min"][k] + box["max"][k]) / 2 for k in "xyz"}
        size = {k: box["max"][k] - box["min"][k] for k in "xyz"}
        dist = distance if distance is not None else max(size.values()) * 2.5
        pos = {"x": center["x"], "y": center["y"], "z": center["z"] + dist}
        cam.set_position(pos["x"], pos["y"], pos["z"])
        cam.aim_at(center["x"], center["y"], center["z"])
        return {"success": True, "camera": cam.describe().label,
                "node": node.describe().label, "position": pos, "nodeCenter": center,
                "nodeSize": size}

    return await run_tool(_run)


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
    def _run() -> dict[str, Any]:
        cam = get_scene().resolve_node(camera_label)
        transforms = {d.name: d.value for d in cam.property_details("transform")
                      if d.name in _PRESET_TRANSFORMS}
        return {"preset": {"label": cam.describe().label, "transforms": transforms}}

    return await run_tool(_run)


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
    if not isinstance(preset, dict) or not isinstance(preset.get("transforms"), dict):
        raise ToolError("Invalid preset data: expected {'transforms': {...}}")

    def _run() -> dict[str, Any]:
        scene = get_scene()
        cam = scene.resolve_node(camera_label)
        info = cam.describe()
        names = list(preset["transforms"])
        results = scene.set_numeric_properties(
            [(str(info.element_id), n, preset["transforms"][n]) for n in names])
        return {"success": True, "camera": info.label,
                "applied": [n for n, r in zip(names, results) if r.ok]}

    return await run_tool(_run)


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
    if preset not in _LIGHTING_PRESETS:
        raise ToolError(f"Unknown preset: {preset}. Valid: {', '.join(_LIGHTING_PRESETS)}")
    return await run_tool(lambda: _apply_lighting_preset(preset, subject_label))


@mcp.tool()
async def daz_apply_composition_rule(
    camera_label: str,
    subject_label: str,
    rule: str = "rule-of-thirds",
) -> dict[str, Any]:
    """Position camera so subject is framed according to a photography composition rule.

    The camera keeps its current direction and distance from the subject
    (250 cm on the subject's +Z side if it is closer than 50 cm) and its lens;
    it turns so the subject's eyes (a prop's centre) land on the rule's
    position. Built with ``dazpy.shot_library.compose_aim``.

    Args:
        camera_label: Node label of the camera to reposition.
        subject_label: Node label of the subject to frame.
        rule: One of:
            - "rule-of-thirds"  — Subject on right vertical third at eye level (default)
            - "golden-ratio"    — Subject at the golden section (0.382 / 0.618 split)
            - "center-frame"    — Subject centred, symmetric framing
            - "leading-lines"   — Low angle, subject on the left third

    Returns:
        Dict with camera, subject, rule, camera_position, explanation and the
        applied shot (``dazpy.shots.Shot.to_dict()``).
    """
    if rule not in _COMPOSITION_RULES:
        raise ToolError(f"Unknown rule: {rule}. Valid: {', '.join(_COMPOSITION_RULES)}")
    screen_x, elevation, explanation = _COMPOSITION_RULES[rule]

    def _run() -> dict[str, Any]:
        scene = get_scene()
        subj = _shots.subject(scene, subject_label)
        cam = _shots.camera(scene, camera_label)
        lens = Lens(focal_length=cam.focal_length or 50.0)
        target = subj.focus_point
        azimuth, distance = _shots.horizontal_view(Vec3.from_dict(cam.position), target)
        position = _shots.orbit_position(target, azimuth, elevation, distance, lens.focal_length)
        aim = sl.compose_aim(position, target, screen_x, lens.focal_length)
        shot = Shot(id=sl.shot_name("medium", subject_label, tag=rule), lens=lens,
                    camera=Placement(position=position, look_at=aim))
        apply_shot(scene, shot, camera=cam)
        return {"camera": camera_label, "subject": subject_label, "rule": rule,
                "camera_position": _shots.vec(position), "explanation": explanation,
                "shot": shot.to_dict()}

    return await _shots.run(_run)


@mcp.tool()
async def daz_frame_shot(
    camera_label: str,
    subject_label: str,
    shot_type: str = "medium-shot",
) -> dict[str, Any]:
    """Frame camera to subject using a standard cinematic shot type.

    Fits the shot size to the camera's current lens (``dazpy.shots.Framing``):
    the camera stands in front of the subject (Genesis figures face +Z) at the
    distance where the size fills the frame height, aimed at the size's
    height on a standing figure. A prop is framed around its centre.

    Args:
        camera_label: Node label of the camera to reposition.
        subject_label: Node label of the subject to frame.
        shot_type: One of:
            - "extreme-close-up"  — Eyes/mouth detail
            - "close-up"          — Face and head
            - "medium-close-up"   — Head and shoulders
            - "medium-shot"       — Waist up
            - "medium-full"       — Knees up
            - "full-shot"         — Entire body
            - "wide-shot"         — Body within environment
            - "extreme-wide"      — Figure small in a wide environment

    Returns:
        Dict with camera, subject, shot_type, distance, camera_height, framing
        description and the applied shot (``Shot.to_dict()``).
    """
    if shot_type not in _shots.SHOT_TYPES:
        raise ToolError(f"Unknown shot type: {shot_type}. Valid: {', '.join(_shots.SHOT_TYPES)}")
    size = _shots.SHOT_TYPES[shot_type]

    def _run() -> dict[str, Any]:
        scene = get_scene()
        subj = _shots.subject(scene, subject_label)
        cam = _shots.camera(scene, camera_label)
        lens = Lens(focal_length=cam.focal_length or 50.0)
        target = subject_label if subj.is_figure else subj.center
        positions = {subject_label: subj.root}
        shot = Shot(id=sl.shot_name(size, subject_label), lens=lens,
                    camera=Framing(subjects=(target,), size=size))
        apply_shot(scene, shot, camera=cam, subjects=positions)
        position = sl.camera_position(shot, positions)
        _, aim = framing_transform([(subj.root, True) if subj.is_figure else (subj.center, False)],
                                   shot.camera, lens.focal_length)
        return {"camera": camera_label, "subject": subject_label, "shot_type": shot_type,
                "distance": round(position.distance(aim), 1), "camera_height": round(position.y, 1),
                "framing": _shots.FRAMING_NOTES[size], "shot": shot.to_dict()}

    return await _shots.run(_run)


@mcp.tool()
async def daz_apply_camera_angle(
    camera_label: str,
    subject_label: str,
    angle: str = "eye-level",
) -> dict[str, Any]:
    """Apply a standard camera angle preset relative to a subject.

    Keeps the camera's current direction and distance from the subject (250 cm
    on the subject's +Z side if it is closer than 50 cm) and its lens, and
    aims at the subject's eyes (a prop's centre). Built with
    ``dazpy.shot_library``.

    Args:
        camera_label: Node label of the camera to reposition.
        subject_label: Node label of the subject.
        angle: One of:
            - "eye-level"      — Camera at subject's eye height (neutral, default)
            - "high-angle"     — 30° above the eyes, looking down
            - "low-angle"      — 20° below the eyes, looking up (powerful/dominant)
            - "dutch-angle"    — Eye level, rolled 15° about the lens axis (unsettling, tense)
            - "overhead"       — Directly above (bird's-eye view)
            - "worms-eye"      — 45° below the eyes looking up
            - "over-shoulder"  — Behind the subject's shoulder, looking where they face (+Z)

    Returns:
        Dict with camera, subject, angle, camera_position, descriptive note and
        the applied shot (``Shot.to_dict()``).
    """
    if angle not in _CAMERA_ANGLES:
        raise ToolError(f"Unknown angle: {angle}. Valid: {', '.join(_CAMERA_ANGLES)}")
    elevation, roll, note = _CAMERA_ANGLES[angle]

    def _run() -> dict[str, Any]:
        scene = get_scene()
        subj = _shots.subject(scene, subject_label)
        cam = _shots.camera(scene, camera_label)
        lens = Lens(focal_length=cam.focal_length or 50.0)
        target = subj.focus_point
        azimuth, distance = _shots.horizontal_view(Vec3.from_dict(cam.position), target)
        if angle == "over-shoulder":
            view = "_view"
            ahead = subj.root + Vec3(0.0, 0.0, distance)  # Genesis figures face +Z
            line = sl.LineOfAction(subject_label, view, subj.root, ahead)
            shot = sl.over_the_shoulder(line, subject_label, view, lens=lens)
        else:
            position = _shots.orbit_position(target, azimuth, elevation, distance,
                                             lens.focal_length)
            if roll:
                placement = Placement(position=position,
                                      rotation=sl.look_rotation(position, target, roll))
            else:
                placement = Placement(position=position, look_at=target)
            shot = Shot(id=sl.shot_name("medium", subject_label, tag=angle), camera=placement,
                        lens=lens)
        apply_shot(scene, shot, camera=cam)
        return {"camera": camera_label, "subject": subject_label, "angle": angle,
                "camera_position": _shots.vec(shot.camera.position), "note": note,
                "shot": shot.to_dict()}

    return await _shots.run(_run)


# ---------------------------------------------------------------------------
# Light listing / creation (dazpy-migrated + registered script)
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_list_lights() -> dict[str, Any]:
    """List all lights currently in the scene.

    Returns position, type, and flux (intensity) for every light node. Use the
    returned ``label`` values with ``daz_set_property``, ``daz_delete_node``,
    or ``daz_animate_light``.

    Returns:
        Dict with:
        - light_count: number of lights
        - lights: list of {index, label, name, type, position, flux, enabled}

    Examples:
        daz_list_lights()
        # → {"light_count": 3, "lights": [{"label": "Key Light", ...}]}

    Notes:
        - ``type`` is the DazScript class name (e.g. "DzSpotLight", "DzDistantLight").
        - ``flux`` is in DAZ Studio's internal units (roughly equivalent to
          Watts for Iray); ``null`` if the light has no Flux property.
    """
    def _run() -> dict[str, Any]:
        lights = [{"index": li.index, "label": li.label, "name": li.name, "type": li.type,
                   "position": {k: round(v, 2) for k, v in zip("xyz", li.position)},
                   "flux": round(li.flux) if li.flux is not None else None,
                   "enabled": li.on}
                  for li in get_scene().light_info()]
        return {"light_count": len(lights), "lights": lights}

    return await run_tool(_run)


@mcp.tool()
async def daz_create_light(
    light_type: str,
    label: str,
    x: float = 0.0,
    y: float = 200.0,
    z: float = 200.0,
    flux: float | None = None,
    aim_at_label: str | None = None,
) -> dict[str, Any]:
    """Create a new light and add it to the scene.

    Creates the light at the given world-space position (in centimetres) and
    optionally aims it at a scene node's bounding-box centre.

    Args:
        light_type: One of ``"spot"`` (default), ``"distant"``, or ``"point"``.
        label: Display name to assign to the new light.
        x: World-space X position in cm (default 0).
        y: World-space Y position in cm (default 200).
        z: World-space Z position in cm (default 200).
        flux: Light intensity in DAZ flux units. If omitted, DAZ default is used.
        aim_at_label: If provided, aim the light at this node's centre.

    Returns:
        Dict with label, type, position, and flux.

    Examples:
        daz_create_light("spot", "Key Light", x=150, y=250, z=200, flux=10000,
                         aim_at_label="Genesis 9")
        daz_create_light("distant", "Sun", x=0, y=500, z=0, flux=5000)
        daz_create_light("point", "Candle", x=0, y=80, z=50, flux=2000)

    Notes:
        - For complex multi-light setups prefer daz_apply_lighting_preset.
        - Use daz_list_lights to verify the light was added.
    """
    valid_types = ("spot", "distant", "point")
    if light_type not in valid_types:
        raise ToolError(
            f"light_type must be one of {valid_types}, got '{light_type}'"
        )
    def _run() -> dict[str, Any]:
        scene = get_scene()
        light = scene.create_light(light_type, name=_unique_name(scene, label, "Light"))
        light.label = label
        light.set_position(x, y, z)
        if flux is not None:
            light.set_numeric_property("Flux", float(flux))
        if aim_at_label:
            light.aim_at(*_box_center(scene.resolve_node(aim_at_label)))
        try:  # "Flux" is the property name; its label is "Luminous Flux (Lumen)"
            flux_now = light.property_detail("Flux").value
        except PropertyNotFoundError:
            flux_now = None  # light types without a Flux dial
        return {"label": label, "type": light_type, "position": light.position,
                "flux": flux_now}

    return await run_tool(_run)


@mcp.tool()
async def daz_list_cameras() -> dict[str, Any]:
    """List all cameras currently in the scene.

    Returns position and focal length for every camera node. Use the returned
    ``label`` values with ``daz_set_active_camera``, ``daz_render_with_camera``,
    or ``daz_delete_node``.

    Returns:
        Dict with:
        - camera_count: number of cameras
        - cameras: list of {index, label, name, type, position, focal_length}

    Examples:
        daz_list_cameras()
        # → {"camera_count": 2, "cameras": [{"label": "Camera 1", ...}]}
    """
    def _run() -> dict[str, Any]:
        cams = [{"index": c.index, "label": c.label, "name": c.name, "type": c.type,
                 "position": {k: round(v, 2) for k, v in zip("xyz", c.position)},
                 "focal_length": round(c.focal_length, 1) if c.focal_length is not None else None}
                for c in get_scene().camera_info()]
        return {"camera_count": len(cams), "cameras": cams}

    return await run_tool(_run)


@mcp.tool()
async def daz_create_camera(
    label: str,
    x: float = 0.0,
    y: float = 150.0,
    z: float = 300.0,
    aim_at_label: str | None = None,
    focal_length: float | None = None,
) -> dict[str, Any]:
    """Create a new camera and add it to the scene.

    Creates a basic camera at the given world-space position (in centimetres) and
    optionally aims it at a scene node's bounding-box centre.

    Args:
        label: Display name to assign to the new camera.
        x: World-space X position in cm (default 0).
        y: World-space Y position in cm (default 150).
        z: World-space Z position in cm (default 300).
        aim_at_label: If provided, aim the camera at this node's centre.
        focal_length: Lens focal length in mm. If omitted, DAZ default is used.

    Returns:
        Dict with label, position, and focal_length.

    Examples:
        daz_create_camera("Close-up Cam", x=0, y=160, z=120,
                          aim_at_label="Genesis 9", focal_length=85)
        daz_create_camera("Wide Shot", x=-200, y=180, z=350,
                          aim_at_label="Genesis 9")

    Notes:
        - Use daz_set_active_camera to switch the active viewport camera.
        - Use daz_list_cameras to confirm the camera was added.
    """
    def _run() -> dict[str, Any]:
        scene = get_scene()
        cam = scene.create_camera(_unique_name(scene, label, "Camera"))
        cam.label = label
        cam.set_position(x, y, z)
        if focal_length:
            cam.focal_length = focal_length
        if aim_at_label:
            cam.aim_at(*_box_center(scene.resolve_node(aim_at_label)))
        return {"label": label, "position": cam.position, "focal_length": cam.focal_length}

    return await run_tool(_run)


@mcp.tool()
async def daz_set_mood_lighting(
    mood: str,
    figure_label: str | None = None,  # pylint: disable=unused-argument
    # Reserved for future per-figure filtering; see docstring below.
) -> dict[str, Any]:
    """Apply a mood-based lighting colour and intensity adjustment to all scene lights.

    Iterates every light in the scene and sets its intensity and diffuse colour
    to match the requested mood.  Optionally focuses the adjustment on lights
    that aim at a particular figure (by name).

    Available moods:
        romantic     - Warm, soft (intensity 0.6, warm orange)
        dramatic     - High contrast, blue-white (intensity 1.5)
        scary        - Cold and dim (intensity 0.4, steel blue)
        golden-hour  - Rich golden warm (intensity 1.2)
        mysterious   - Cool blue, mid-dim (intensity 0.5)
        peaceful     - Soft warm (intensity 0.8)

    Args:
        mood: One of the mood names listed above.
        figure_label: Optional figure label to aim-check. Currently unused by the
                      DazScript; reserved for future per-figure filtering.

    Returns:
        {
            "mood": "romantic",
            "lights_adjusted": 3,
            "intensity": 0.6,
            "color": [255, 200, 150]
        }
    """
    if mood not in MOOD_PRESETS:
        valid = ", ".join(f'"{k}"' for k in MOOD_PRESETS)
        raise ToolError(f"Unknown mood '{mood}'. Valid moods: {valid}")

    preset = MOOD_PRESETS[mood]
    preset = MOOD_PRESETS[mood]
    adjusted = await run_tool(lambda: _tint_lights(preset["intensity"], preset["color"]))
    return {"mood": mood, "lights_adjusted": adjusted, "intensity": preset["intensity"],
            "color": list(preset["color"])}


@mcp.tool()
async def daz_apply_time_of_day(
    time_of_day: str,
    figure_label: str | None = None,  # pylint: disable=unused-argument
    # Reserved for future per-figure filtering; see docstring below.
) -> dict[str, Any]:
    """Adjust all scene lights to simulate a particular time of day.

    Sets light intensity and colour temperature across all scene lights to
    approximate the natural lighting quality for the chosen time.

    Available times:
        dawn         - Soft orange-pink (intensity 0.5)
        morning      - Warm soft daylight (intensity 0.8)
        noon         - Bright near-white (intensity 1.5)
        golden-hour  - Rich golden warm (intensity 1.2)
        dusk         - Deep red-orange (intensity 0.6)
        night        - Very dim cool blue (intensity 0.15)

    Args:
        time_of_day: One of the time names listed above.
        figure_label: Optional figure label. Reserved for future per-figure
                      filtering; currently applies to all scene lights.

    Returns:
        {
            "time_of_day": "golden-hour",
            "lights_adjusted": 3,
            "intensity": 1.2,
            "color": [255, 200, 100]
        }
    """
    if time_of_day not in TIME_OF_DAY_PRESETS:
        valid = ", ".join(f'"{k}"' for k in TIME_OF_DAY_PRESETS)
        raise ToolError(f"Unknown time_of_day '{time_of_day}'. Valid values: {valid}")

    preset = TIME_OF_DAY_PRESETS[time_of_day]
    preset = TIME_OF_DAY_PRESETS[time_of_day]
    adjusted = await run_tool(lambda: _tint_lights(preset["intensity"], preset["color"]))
    return {"time_of_day": time_of_day, "lights_adjusted": adjusted,
            "intensity": preset["intensity"], "color": list(preset["color"])}
