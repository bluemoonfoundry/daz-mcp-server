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


# --- daz_animate_conversation -------------------------------------------------

_LISTEN_CHAIN = (("neckLower", 0.3), ("head", 0.6))


def _key_speaker_emotion(skel: Any, emotion: str, intensity: float, frame: int) -> int:
    """Key the speaker's expression at *frame*: the stock face controller,
    else the feature dials. Returns how many dials were keyed."""
    from ._emotions import _EMOTION_DEFINITIONS  # pylint: disable=import-outside-toplevel
    definition = _EMOTION_DEFINITIONS.get(emotion, {"morphs": []})
    if definition.get("face"):
        if skel.key_numeric_candidates([(definition["face"], [(frame, intensity)])])[0].found:
            return 1
    slots = [(m["names"], [(frame, m["value"] * intensity)]) for m in definition["morphs"]]
    return sum(1 for r in (skel.key_numeric_candidates(slots) if slots else []) if r.found)


def _key_listener_look(skel: Any, target: tuple[float, float, float],
                       frames: tuple[int, int]) -> bool:
    """Aim the listener's neck/head at *target* and key that at both frames."""
    from ._emotions import resolve_bone  # pylint: disable=import-outside-toplevel
    names = set(skel.bone_names())
    chain = [(b, w) for b, w in ((resolve_bone(r, names), w) for r, w in _LISTEN_CHAIN) if b]
    if not chain:
        return False
    aimed = skel.look_at(target, chain)
    skel.key_bone_axes({a.bone: {"x": [(f, a.x) for f in frames],
                                 "y": [(f, a.y) for f in frames]} for a in aimed.applied})
    return bool(aimed.applied)


def _conversation_beat(scene: Any, figs: dict, char1: str, char2: str, index: int,
                       beat: dict) -> dict:
    from .tools.morph import _gaze_target  # pylint: disable=import-outside-toplevel
    speaker = beat["speaker"]
    listener = char2 if speaker == char1 else char1
    start = beat.get("startFrame", 0)
    end = beat.get("endFrame", start + 30)
    emotion = beat.get("emotion", "neutral")
    actions = []
    n = _key_speaker_emotion(figs[speaker], emotion, beat.get("intensity", 0.7), start)
    if n:
        actions.append(f"Applied {emotion} emotion ({n} morphs)")
    if _key_listener_look(figs[listener], _gaze_target(scene, speaker), (start, end)):
        actions.append("Listener looks at speaker")
    return {"beat": index + 1, "speaker": speaker, "frameRange": {"start": start, "end": end},
            "emotion": emotion, "actions": actions}


def conversation(char1: str, char2: str, beats: list[dict]) -> dict:
    """Key emotions on each beat's speaker and the listener looking at them."""
    scene = get_scene()
    figs = {char1: scene.resolve_node(char1), char2: scene.resolve_node(char2)}
    applied = [_conversation_beat(scene, figs, char1, char2, i, beat)
               for i, beat in enumerate(beats)]
    max_frame = max((b["frameRange"]["end"] for b in applied), default=0)
    return {"char1": figs[char1].describe().label, "char2": figs[char2].describe().label,
            "beatsApplied": applied, "totalFrames": max_frame, "beatCount": len(beats)}


# --- daz_choreograph_action / daz_interactive_pose ---------------------------

ACTION_SPACING = {"handshake": 60.0, "hug": 30.0, "fight": 100.0, "dance": 40.0}
ACTION_SUGGESTIONS = {
    "handshake": ["Use daz_interactive_pose with 'handshake' to bring the hands together",
                  "Apply 'happy' or 'confident' emotion to both characters"],
    "hug": ["Use daz_interactive_pose with 'hug' type for arm positioning",
            "Apply 'loving' or 'happy' emotion to both characters"],
    "fight": ["Apply fighting stance poses from content library",
              "Apply 'angry' emotion", "Use low-angle camera for dramatic effect"],
    "dance": ["Apply partner dance poses from content library",
              "Use daz_create_character_path for dance movement",
              "Apply 'happy' or 'excited' emotion"],
}


def choreograph(action: str, characters: list[str]) -> list[dict]:
    """Face the first two characters toward each other at *action*'s spacing,
    centred on the origin (as the replaced script did)."""
    placed = arrange(characters[:2], "line", ACTION_SPACING[action], "center",
                     {"x": 0.0, "y": 0.0, "z": 0.0})
    return [{"character": c["label"], "position": c["position"], "rotation": c["rotation"]}
            for c in placed["characters"]]


def _space_pair(scene: Any, char1: str, char2: str, distance: float) -> None:
    """Face two figures toward each other *distance* apart about their midpoint."""
    p1 = scene.resolve_node(char1).position
    p2 = scene.resolve_node(char2).position
    mid = {"x": (p1["x"] + p2["x"]) / 2, "y": 0.0, "z": (p1["z"] + p2["z"]) / 2}
    arrange([char1, char2], "line", distance, "center", mid)


def interactive_pose(char1: str, char2: str, kind: str, distance: float | None) -> dict:
    """Stage two figures with a dazpy interaction recipe (facing, then limb
    targets solved per figure generation)."""
    # pylint: disable=import-outside-toplevel
    from dazpy._interaction import (build_face_each_other_recipe, build_handshake_recipe,
                                    build_hug_recipe, build_touch_recipe)
    scene = get_scene()
    applied = []
    if distance:
        _space_pair(scene, char1, char2, float(distance))
        applied.append(f"spaced {distance:g} cm apart")
    recipe = {
        "face-each-other": lambda: build_face_each_other_recipe(char1, char2),
        "hug": lambda: build_hug_recipe(char1, char2),
        "handshake": lambda: build_handshake_recipe(char1, char2),
        "shoulder-arm": lambda: build_touch_recipe(char1, char2, source_anchor="r_hand",
                                                   target_anchor="l_shoulder"),
    }[kind]()
    result = scene.apply_interaction_recipe(recipe, align_limb_targets=True).to_dict()
    issues = result["prepared"].get("validation_issues", [])
    if issues:
        raise ToolError(f"Interaction recipe could not be prepared: {issues}")
    applied.append("facing" if kind == "face-each-other" else kind)
    return {"success": True, "char1": char1, "char2": char2, "interactionType": kind,
            "applied": applied,
            "alignment": [{"anchor": a["anchor_name"], "converged": a["converged"],
                           "finalError": a["final_error"]}
                          for a in result["alignment_results"]]}


# --- daz_create_scene templates -------------------------------------------------

_SCENE_TYPES = (("dining", ("dinner", "dining", "meal", "eat")),
                ("interview", ("interview", "meeting", "business")),
                ("portrait", ("portrait", "headshot", "photo")),
                ("conversation", ("conversation", "talking", "chat")))
# scene type -> per-character {property: value} for the first two characters
_SCENE_BLOCKING = {
    "dining": [{"ZTranslate": -60, "YRotate": 0}, {"ZTranslate": 60, "YRotate": 180}],
    "interview": [{"XTranslate": -80, "ZTranslate": 0, "YRotate": 90},
                  {"XTranslate": 80, "ZTranslate": 0, "YRotate": -90}],
    "conversation": [{"XTranslate": -50, "ZTranslate": 0, "YRotate": 90},
                     {"XTranslate": 50, "ZTranslate": 0, "YRotate": -90}],
}
_SCENE_SUGGESTIONS = {
    "dining": ["Add table prop for dining scene",
               "Add plates, glasses, or food props for realism",
               "Consider adding candles for romantic dinner mood"],
    "interview": ["Add desk or table prop between characters", "Add chairs for seated interview",
                  "Consider office props (laptop, papers) for context"],
    "portrait": ["Adjust character facial expression for portrait mood",
                 "Consider neutral background or backdrop prop",
                 "Try different camera angles (high-angle, low-angle)"],
    "conversation": ["Use shot-reverse-shot camera technique for conversation",
                     "Apply emotions and look-at for animated dialogue",
                     "Consider adding environment props for context"],
    "generic": ["Provide more specific scene description for tailored setup",
                "Keywords: dinner, interview, portrait, conversation",
                "Add props and environment elements as needed"],
}


def _scene_type(description: str) -> str:
    text = description.lower()
    return next((t for t, words in _SCENE_TYPES if any(w in text for w in words)), "generic")


def _scene_lights(kind: str, description: str, c: dict,
                  eye: float) -> tuple[list[tuple[str, tuple, float]], str]:
    """[(label, (x, y, z), flux)] and an action note for a template."""
    three_point = [("Key Light", (c["x"] + 150, eye + 30, c["z"] + 120), 2000),
                   ("Fill Light", (c["x"] - 120, eye + 15, c["z"] + 100), 800),
                   ("Rim Light", (c["x"], eye + 50, c["z"] - 150), 1200)]
    if kind == "dining" and "romantic" in description.lower():
        return ([("Warm Key Light", (100, 180, 100), 1500),
                 ("Warm Fill Light", (-80, 150, 80), 600)], "Applied warm romantic lighting")
    return {
        "dining": ([("Key Light", (120, 180, 120), 1800), ("Fill Light", (-100, 150, 100), 700)],
                   "Applied dining scene lighting"),
        "interview": ([("Key Light", (150, 200, 120), 2200), ("Fill Light", (-120, 180, 100), 1000),
                       ("Back Light", (0, 220, -180), 1400)],
                      "Applied professional three-point lighting"),
        "conversation": ([("Key Light", (120, 180, 100), 1900),
                          ("Fill Light", (-100, 160, 80), 850)],
                         "Applied natural conversation lighting"),
        "portrait": (three_point, "Applied classic three-point portrait lighting"),
        "generic": (three_point, "Applied default three-point lighting"),
    }[kind]


def _found_nodes(scene: Any, labels: list[str]) -> dict[str, Any]:
    """Resolve *labels*, skipping ones not in the scene (the caller reports them)."""
    from dazpy.exceptions import NodeNotFoundError  # pylint: disable=import-outside-toplevel
    out = {}
    for label in labels:
        try:
            out[label] = scene.resolve_node(label)
        except NodeNotFoundError:
            continue
    return out


def _subject_frame(found: dict, characters: list[str]) -> tuple[dict, float, bool]:
    """(bounding-box centre, eye height, have_subject) of the first character."""
    center, eye = {"x": 0.0, "y": 100.0, "z": 0.0}, 160.0
    if not characters or characters[0] not in found:
        return center, eye, False
    box = found[characters[0]].bounding_box()
    if box:
        center = {k: (box["min"][k] + box["max"][k]) / 2 for k in "xyz"}
        eye = box["min"]["y"] + (box["max"]["y"] - box["min"]["y"]) * 0.85
    return center, eye, True


def _light_scene(scene: Any, kind: str, description: str, center: dict, eye: float) -> str:
    """Create/reuse the template's spot lights aimed at eye height; hide the ground plane."""
    from dazpy import DazRenderSettings  # pylint: disable=import-outside-toplevel
    from ._cinematic_lighting import (  # pylint: disable=import-outside-toplevel
        _get_or_create_light)
    from ._client import get_daz_client  # pylint: disable=import-outside-toplevel
    lights, note = _scene_lights(kind, description, center, eye)
    for label, pos, flux in lights:
        light, _ = _get_or_create_light(scene, label, "spot", True)
        light.set_position(*pos)
        light.aim_at(center["x"], eye, center["z"])
        light.set_numeric_property("Flux", float(flux))
    DazRenderSettings(get_daz_client()).draw_ground_plane = False
    return note


def scene_template(description: str, characters: list[str]) -> dict:
    """Block characters, light the scene for its template and hide the ground plane."""
    scene = get_scene()
    kind = _scene_type(description)
    actions = [f"Scene type: {kind}"]
    found = _found_nodes(scene, characters[:2])
    center, eye, has_subject = _subject_frame(found, characters)
    if kind in _SCENE_BLOCKING and len(found) == 2:
        ops = [(str(found[label].describe().element_id), prop, float(value))
               for label, props in zip(characters[:2], _SCENE_BLOCKING[kind])
               for prop, value in props.items()]
        scene.set_numeric_properties(ops)
        actions.append("Positioned the first two characters facing each other")
    if has_subject or kind not in ("portrait", "generic"):
        actions.append(_light_scene(scene, kind, description, center, eye))
    suggestions = list(_SCENE_SUGGESTIONS[kind])
    if not characters:
        suggestions.append("Load characters into scene before generating setup")
    return {"sceneType": kind, "description": description, "charactersUsed": len(characters),
            "actions": actions, "suggestions": suggestions}
