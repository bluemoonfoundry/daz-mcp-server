"""Lighting choreography for the cinematic tools, on dazpy.

daz_animate_light, daz_create_light_sequence, daz_set_scene_atmosphere and
daz_apply_visual_style call these synchronous functions through run_tool.
Frames are timeline frames; dazpy converts them to DzTime (the scripts these
replace passed frame numbers as ticks, keying everything inside frame 1).
"""
from __future__ import annotations

import math
import random
import re
from typing import Any, Callable

from dazpy import DazRenderSettings
from fastmcp.exceptions import ToolError

from ._client import get_daz_client, get_scene

ENV_MODE_NAMES = {0: "Dome and Scene", 1: "Dome Only", 2: "Sun-Sky Only", 3: "Scene Only"}
_MODE_KEYS = {0: "dome_and_scene", 1: "dome_only", 2: "sun_sky", 3: "scene_only"}


def _flux_keys(node: Any, keys: list[tuple[int, float]], label: str) -> None:
    r = node.key_numeric_candidates([(["Flux"], keys)])[0]
    if not r.found:
        raise ToolError(f"Light has no Flux property: {label}")


# --- daz_animate_light --------------------------------------------------------

def flicker_keys(start: int, end: int, intensity: float, amount: float,
             rnd: Callable[[], float]) -> list[tuple[int, float]]:
    """Random Flux variations around *intensity*, ending on *intensity*."""
    duration = end - start
    step = max(1, duration // max(4, duration // 5))
    keys = [(f, max(0.0, intensity + (rnd() * 2 - 1) * amount * intensity))
            for f in range(start, end + 1, step)]
    if keys[-1][0] != end:
        keys.append((end, intensity))
    return keys


def pulse_keys(start: int, end: int, intensity: float, amount: float,
           pulses: int) -> list[tuple[int, float]]:
    """*pulses* sine cycles between intensity*(1-amount) and intensity."""
    n = pulses * 4 + 1
    lo = intensity * (1 - amount)
    keys = {}
    for i in range(n):
        phase = i / (n - 1) * pulses * 2 * math.pi
        keys[round(start + i * (end - start) / (n - 1))] = lo + (math.sin(phase) + 1) / 2 * (
            intensity - lo)
    return sorted(keys.items())


def strobe_keys(start: int, end: int, intensity: float, interval: int) -> list[tuple[int, float]]:
    """Square-wave on/off Flux keys every *interval* frames."""
    keys, frame, on = {}, start, True
    while frame <= end:
        value = intensity if on else 0.0
        keys[frame] = value
        if frame + interval <= end:
            keys[frame + interval - 1] = value
        frame += interval
        on = not on
    return sorted(keys.items())


def animate_light(label: str, movement: str, start: int, end: int, intensity: float,
                  amount: float, strobe_interval: int, pulse_count: int,
                  rnd: Callable[[], float] = random.random) -> dict:
    """Key a light's Flux (or Color, for color-cycle) for *movement*."""
    node = get_scene().resolve_node(label)
    keyframes: list[dict] = []
    if movement == "color-cycle":
        dur = end - start
        colors = [(start, (1.0, 0.8, 0.5)), (round(start + dur * 0.33), (1.0, 1.0, 1.0)),
                  (round(start + dur * 0.66), (0.5, 0.7, 1.0)), (end, (1.0, 0.8, 0.5))]
        node.key_color("Color", [(f, tuple(c * 255 for c in rgb)) for f, rgb in colors])
        keyframes = [{"frame": f, "r": r, "g": g, "b": b} for f, (r, g, b) in colors]
    else:
        keys = {
            "flicker": lambda: flicker_keys(start, end, intensity, amount, rnd),
            "pulse": lambda: pulse_keys(start, end, intensity, amount, pulse_count),
            "fade-in": lambda: [(start, 0.0), (end, intensity)],
            "fade-out": lambda: [(start, intensity), (end, 0.0)],
            "strobe": lambda: strobe_keys(start, end, intensity, strobe_interval),
        }[movement]()
        _flux_keys(node, keys, label)
        keyframes = [{"frame": f, "value": v} for f, v in keys]
    return {"light": node.describe().label, "movementType": movement, "startFrame": start,
            "endFrame": end, "targetIntensity": intensity,
            "keyframesCreated": len(keyframes), "keyframes": keyframes}


# --- daz_create_light_sequence -----------------------------------------------

def _sequence_lights(kind: str, start: int, end: int,
                     rnd: Callable[[], float]) -> list[tuple[str, str, list]]:
    dur = end - start
    q1, mid, q3 = round(start + dur / 4), round(start + dur / 2), round(start + dur * 0.75)
    if kind == "romantic":
        step = max(3, dur // 15)
        candle = [(f, max(200.0, 800 + (rnd() * 0.4 - 0.2) * 800))
                  for f in range(start, end + 1, step)]
        return [("Candle_Key", "spot", candle),
                ("Soft_Fill", "spot", [(start, 400), (end, 400)])]
    table: dict[str, list[tuple[str, str, list]]] = {
        "day-to-night": [
            ("Sun_Key", "distant", [(start, 8000), (q1, 6000), (mid, 3000), (q3, 800), (end, 0)]),
            ("Sky_Fill", "spot", [(start, 2000), (mid, 800), (end, 100)])],
        "night-to-dawn": [
            ("Dawn_Key", "distant", [(start, 0), (q3, 500), (end, 6000)]),
            ("Night_Ambient", "spot", [(start, 200), (mid, 300), (end, 1500)])],
        "interrogation": [
            ("Overhead_Key", "spot",
             [(start, 2000), (q1, 3000), (mid, 2500), (q3, 4000), (end, 5000)]),
            ("Reveal_Spot", "spot", [(start, 0), (q3 - 1, 0), (q3, 3000), (end, 3000)])],
        "action-tension": [
            ("Action_Key", "spot", [(start, 3000), (q3, 5000), (end, 5000)]),
            ("Action_Rim", "spot", [(start, 1000), (end, 2000)]),
            ("Flash_Light", "spot", [(start, 0), (q3 - 1, 0), (q3, 15000), (q3 + 3, 15000),
                                     (q3 + 4, 0), (end, 0)])],
    }
    return table[kind]


def _get_or_create_light(scene: Any, label: str, kind: str, create: bool) -> tuple[Any, bool]:
    found = [n for n in scene.find_nodes(label) if n.label == label]
    if found:
        return scene.resolve_node(str(found[0].element_id)), False
    if not create:
        return None, False
    light = scene.create_light(kind, name=re.sub(r"[^A-Za-z0-9_]", "_", label))
    light.label = label
    return light, True


def light_sequence(kind: str, start: int, end: int, create: bool,
                   rnd: Callable[[], float] = random.random) -> dict:
    """Create (or reuse) a sequence's lights and key their Flux over the range."""
    scene = get_scene()
    created, keyframes = [], []
    for label, light_kind, keys in _sequence_lights(kind, start, end, rnd):
        light, was_created = _get_or_create_light(scene, label, light_kind, create)
        if light is None:
            continue
        if was_created:
            created.append(label)
        keys = sorted(dict(keys).items())
        _flux_keys(light, [(int(f), float(v)) for f, v in keys], label)
        keyframes += [{"light": label, "property": "Flux", "frame": f, "value": v}
                      for f, v in keys]
    return {"sequenceType": kind, "startFrame": start, "endFrame": end,
            "lightsCreated": created, "totalKeyframes": len(keyframes),
            "keyframes": keyframes}


# --- daz_set_scene_atmosphere --------------------------------------------------

_NO_ENV = ("No environment node yet (Studio 4 creates it on the first Iray render after "
           "Scene.clear()); render once, then retry.")


def _set_env_props(rs: Any, wanted: list[tuple[str, list[str], Any]],
                   changes: list[str], results: dict) -> None:
    matched = rs.set_environment_properties([(names, value) for _, names, value in wanted])
    if matched is None:
        raise ToolError(_NO_ENV)
    for (key, _names, value), hit in zip(wanted, matched):
        if hit:
            results[key] = value
            changes.append(f"{hit} → {value}")
        else:
            results[key + "Note"] = "property not found on the environment node"


def scene_atmosphere(mode: int | None, intensity: float | None, draw_dome: bool | None,
                     dome_scale: float | None, dome_rotation: float | None,
                     sun_intensity: float | None) -> dict:
    """Set the Iray environment mode and dome/sun properties."""
    rs = DazRenderSettings(get_daz_client())
    wanted = [w for w in (
        ("environmentIntensity", ["Environment Intensity", "Dome Intensity"], intensity),
        ("drawDome", ["Draw Dome", "Dome Visible"], draw_dome),
        ("domeScale", ["Dome Scale"], dome_scale),
        ("domeRotation", ["Dome Rotation", "Dome Orientation"], dome_rotation),
        ("sunLightIntensity", ["Sun Intensity", "Sunlight Intensity"], sun_intensity),
    ) if w[2] is not None]
    changes: list[str] = []
    results: dict = {}
    if mode is not None:
        if not rs.set_environment_mode(_MODE_KEYS[mode]):
            raise ToolError(_NO_ENV)
        results["environmentMode"] = mode
        changes.append(f"Environment Mode → {ENV_MODE_NAMES[mode]}")
    if wanted:
        _set_env_props(rs, wanted, changes, results)
    return {"changesApplied": changes, "changeCount": len(changes),
            "currentEnvironmentMode": rs.environment_mode, "results": results,
            "environmentModeReference": dict(ENV_MODE_NAMES)}


# --- daz_apply_visual_style ----------------------------------------------------

# style: (key flux, fill ratio, rim ratio, key angle, rim angle, shadow softness, description)
VISUAL_STYLES: dict[str, tuple[float, float, float, float, float, float, str]] = {
    "cinematic": (5000, 0.15, 0.7, 40, -150, 0.3,
                  "High contrast, strong rim, compressed fill — film look"),
    "noir": (4000, 0.05, 0.2, 70, -160, 0.1,
             "Extreme contrast, deep shadows, minimal fill — classic noir"),
    "golden-hour": (6000, 0.3, 0.9, 25, -170, 0.5,
                    "Warm raking light, strong backlit rim, soft fill — magic hour"),
    "blue-hour": (1500, 0.6, 0.4, 20, -140, 0.8,
                  "Low intensity, even blue-toned fill, subtle — dusk/dawn"),
    "high-key": (8000, 0.8, 0.3, 10, -160, 0.9,
                 "Bright, low contrast, minimal shadows — commercial/fashion"),
    "low-key": (2500, 0.08, 0.3, 60, -150, 0.2,
                "Dark, moody, shadows dominate — thriller/horror"),
    "documentary": (4500, 0.5, 0.2, 30, -160, 0.6,
                    "Natural-feeling, moderate contrast — realistic interview look"),
    "fantasy": (3500, 0.4, 1.2, 35, -145, 0.7,
                "Ethereal, glowing rim, soft key — fantasy/magical"),
}


def _place(scene: Any, label: str, subject: dict, angle: float, height: float, dist: float,
           flux: float, softness: float) -> None:
    light, _ = _get_or_create_light(scene, label, "spot", True)
    rad = math.radians(angle)
    light.set_position(subject["x"] + dist * math.sin(rad), height,
                       subject["z"] - dist * math.cos(rad))
    light.aim_at(subject["x"], subject["y"], subject["z"])
    light.set_numeric_property("Flux", float(flux))
    light.set_numeric_property("Shadow Softness", float(softness))


def visual_style(name: str, subject_label: str | None, intensity: float) -> dict:
    """Place and set Style_Key/Fill/Rim spot lights around the subject for *name*."""
    style = VISUAL_STYLES[name]
    scene = get_scene()
    subject = {"x": 0.0, "y": 130.0, "z": 0.0}
    if subject_label:
        pos = scene.resolve_node(subject_label).position
        subject = {"x": pos["x"], "y": pos["y"] + 130.0, "z": pos["z"]}
    key = round(style[0] * intensity)
    flux = {"key": key, "fill": round(key * style[1]), "rim": round(key * style[2])}
    _place(scene, "Style_Key", subject, style[3], subject["y"] + 60, 250, key, style[5])
    _place(scene, "Style_Fill", subject, style[3] - 120, subject["y"] + 20, 300, flux["fill"],
           min(1.0, style[5] + 0.2))
    _place(scene, "Style_Rim", subject, style[4], subject["y"] + 80, 200, flux["rim"], style[5])
    env = DazRenderSettings(get_daz_client()).set_environment_mode("scene_only")
    return {
        "styleName": name, "description": style[6], "intensity": intensity,
        "subject": subject_label,
        "environmentMode": 3 if env else "unchanged (no environment node yet)",
        "lights": [{"role": "key", "label": "Style_Key", "flux": key, "angle": style[3]},
                   {"role": "fill", "label": "Style_Fill", "flux": flux["fill"],
                    "angle": style[3] - 120},
                   {"role": "rim", "label": "Style_Rim", "flux": flux["rim"], "angle": style[4]}],
        "lightingRatios": {**flux, "keyToFill": round(key / max(1, flux["fill"]), 1),
                           "keyToRim": round(key / max(1, flux["rim"]), 1)},
    }
