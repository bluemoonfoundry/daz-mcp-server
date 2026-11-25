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
