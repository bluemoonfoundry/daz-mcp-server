"""Morph, expression, and body-language tools for DAZ Studio figures."""
from __future__ import annotations

import json
import math
from typing import Any

from dazpy.exceptions import NodeNotFoundError
from fastmcp.exceptions import ToolError

from .._mcp import mcp, _execute_by_id
from .._client import get_daz_client, get_scene, run_dazpy
from .._emotions import (
    AXIS_BY_PROPERTY,
    POSTURES,
    _EMOTION_DEFINITIONS,
    resolve_bone,
)
from .._errors import handle_dazpy_error


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_list_morphs(
    node_label: str,
    include_zero: bool = False,
) -> dict[str, Any]:
    """List all morphs (numeric properties) on a node.

    Returns all numeric properties on a node, which includes morphs (body shapes,
    facial expressions), transforms, and other numeric dials. Useful for discovering
    what morphs are available on a figure.

    Args:
        node_label: Display label or internal name of the node (e.g., "Genesis 9").
        include_zero: If True, return all morphs including those set to 0.
                      If False (default), only return morphs with non-zero values
                      (currently active morphs).

    Returns:
      - morphs: List of morph objects with:
        - label: Display label (e.g., "Head Size")
        - name: Internal name (e.g., "HeadSize")
        - value: Current numeric value
        - path: Property path for organization (e.g., "Morphs/Head")
      - count: Number of morphs returned
      - nodeLabel: Confirmed node label

    Example:
        # List only active morphs on Genesis 9
        result = daz_list_morphs("Genesis 9", include_zero=False)
        # result["morphs"] = [
        #   {"label": "Height", "name": "Height", "value": 1.05, "path": "Morphs/Body"},
        #   {"label": "Head Size", "name": "HeadSize", "value": 0.9, "path": "Morphs/Head"}
        # ]

        # List all available morphs (including zero values)
        result = daz_list_morphs("Genesis 9", include_zero=True)
        # result["count"] might be 500+ morphs
    """
    include_zero_js = "true" if include_zero else "false"

    def _run() -> list | None:
        client = get_daz_client()
        script = f"""(function() {{
            var node = Scene.findNodeByLabel({json.dumps(node_label)});
            if (!node) return null;
            var obj = node.getObject();
            if (!obj) return [];
            var includeZero = {include_zero_js};
            var result = [];
            for (var i = 0; i < obj.getNumModifiers(); i++) {{
                var m = obj.getModifier(i);
                if (m.className() === "DzMorph") {{
                    var ch = m.getValueChannel();
                    var val = ch.getValue();
                    if (includeZero || val !== 0) {{
                        var path = "";
                        try {{
                            var pg = ch.getPropertyGroup();
                            if (pg) path = pg.getPath();
                        }} catch(e) {{}}
                        result.push({{
                            name: m.getName(),
                            label: m.getLabel(),
                            value: val,
                            path: path
                        }});
                    }}
                }}
            }}
            return result;
        }})();"""
        return client.execute(script).value

    try:
        morphs = await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)
    if morphs is None:
        raise ToolError(f"Node not found: {node_label!r}")
    return {"morphs": morphs, "count": len(morphs), "nodeLabel": node_label}


@mcp.tool()
async def daz_search_morphs(
    node_label: str,
    pattern: str,
    include_zero: bool = False,
) -> dict[str, Any]:
    """Search for morphs matching a name pattern.

    Search through all numeric properties (morphs) on a node for those matching
    a substring pattern. Useful for finding specific morphs like all facial
    expressions, body morphs, or morphs for a specific body part.

    Args:
        node_label: Display label or internal name of the node (e.g., "Genesis 9").
        pattern: Substring to search for in morph label or name (case-insensitive).
                 Examples: "smile", "head", "muscle", "express"
        include_zero: If True, return all matching morphs including zero values.
                      If False (default), only return matching morphs that are active.

    Returns:
      - morphs: List of matching morph objects with:
        - label: Display label
        - name: Internal name
        - value: Current value
        - path: Property path
      - count: Number of matching morphs
      - pattern: The search pattern used
      - nodeLabel: Confirmed node label

    Example:
        # Find all smile-related morphs
        result = daz_search_morphs("Genesis 9", "smile", include_zero=True)
        # result["morphs"] might include: "Smile", "Smile Open", "Smile Closed", etc.

        # Find active head morphs
        result = daz_search_morphs("Genesis 9", "head", include_zero=False)
        # Only returns head morphs with non-zero values

        # Find all facial expression morphs
        result = daz_search_morphs("Genesis 9", "express", include_zero=True)
    """
    include_zero_js = "true" if include_zero else "false"
    pat_lower = pattern.lower()

    def _run() -> list | None:
        client = get_daz_client()
        script = f"""(function() {{
            var node = Scene.findNodeByLabel({json.dumps(node_label)});
            if (!node) return null;
            var obj = node.getObject();
            if (!obj) return [];
            var includeZero = {include_zero_js};
            var pat = {json.dumps(pat_lower)};
            var result = [];
            for (var i = 0; i < obj.getNumModifiers(); i++) {{
                var m = obj.getModifier(i);
                if (m.className() === "DzMorph") {{
                    var name = m.getName();
                    var label = m.getLabel();
                    if (name.toLowerCase().indexOf(pat) === -1 &&
                            label.toLowerCase().indexOf(pat) === -1) continue;
                    var ch = m.getValueChannel();
                    var val = ch.getValue();
                    if (includeZero || val !== 0) {{
                        var path = "";
                        try {{
                            var pg = ch.getPropertyGroup();
                            if (pg) path = pg.getPath();
                        }} catch(e) {{}}
                        result.push({{
                            name: name,
                            label: label,
                            value: val,
                            path: path
                        }});
                    }}
                }}
            }}
            return result;
        }})();"""
        return client.execute(script).value

    try:
        morphs = await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)
    if morphs is None:
        raise ToolError(f"Node not found: {node_label!r}")
    return {
        "morphs": morphs,
        "count": len(morphs),
        "pattern": pattern,
        "nodeLabel": node_label,
    }


@mcp.tool()
async def daz_set_morph(
    node_label: str,
    morph_name: str,
    value: float,
) -> dict[str, Any]:
    """Set a morph dial on a node by display label.

    Matches by exact label first, then exact internal name, then substring of
    label — so ``"smile"`` will match ``"Mouth Smile"`` if no exact match
    exists. Returns the matched label and internal name so you can confirm
    which morph was applied.

    For most morphs the useful range is 0.0–1.0 (fully off to fully on).
    Negative values and values above 1.0 are accepted for special morphs that
    support them.

    Args:
        node_label: Display label of the figure or prop.
        morph_name: Full or partial label of the morph dial.
        value: Target value for the morph.

    Returns:
        Dict with node, morph (display label), internal_name, and value read back.

    Examples:
        daz_set_morph("Genesis 9", "Mouth Smile", 0.8)
        daz_set_morph("Genesis 9", "smile", 0.8)          # substring match
        daz_set_morph("Genesis 9", "Head Size", 1.15)
        daz_set_morph("Genesis 9", "Breast Size", 0.0)    # zero out a morph

    Notes:
        - Use daz_search_morphs to browse available morph names before setting.
        - daz_set_property also works but requires the exact internal property name.
    """
    return await _execute_by_id(
        "vangard-set-morph",
        {"nodeLabel": node_label, "morphName": morph_name, "value": value},
    )


def _resolve_body(skel: Any, adjustments: list[dict], intensity: float) -> tuple[list, list]:
    """Write *adjustments* (Genesis 8 bone roles) onto *skel*, one axis each.

    Returns ``(applied, not_found)``: applied entries name the bone actually
    written; not_found lists roles with no matching bone on this figure.
    """
    if not adjustments:
        return [], []
    bone_names = set(skel.bone_names())
    data: dict[str, dict[str, float]] = {}
    applied: list[dict] = []
    not_found: list[str] = []
    for adj in adjustments:
        bone = resolve_bone(adj["bone"], bone_names)
        if bone is None:
            not_found.append(adj["bone"])
            continue
        value = adj["value"] * intensity
        data.setdefault(bone, {})[AXIS_BY_PROPERTY[adj["property"]]] = value
        applied.append({"bone": bone, "property": adj["property"], "value": value})
    missing = set(skel.set_bone_axes(data)) if data else set()
    if missing:  # bone vanished between the two calls
        not_found += sorted(missing)
        applied = [a for a in applied if a["bone"] not in missing]
    return applied, not_found


@mcp.tool()
async def daz_set_emotion(
    character_label: str,
    emotion: str,
    intensity: float = 0.7,
) -> dict[str, Any]:
    """Apply an emotional expression to a character: face controls + body adjustment.

    Uses the figure's stock full-face expression controller when it has one
    (Genesis 9 ``facs_ctrl_Happy``, Genesis 8 ``eCTRLHappy_HD``, ...) and
    otherwise falls back to individual feature dials (smile, brows, eyes).
    Other emotions' full-face controllers are reset to 0 first, so switching
    emotion doesn't stack expressions; ``neutral`` just clears them.

    Args:
        character_label: Node label of the character to affect.
        emotion: One of: happy, sad, angry, surprised, fearful, disgusted, neutral,
                 excited, bored, confident, shy, loving, contemptuous.
        intensity: Scale factor 0.0–1.0 applied to all morph and body values (default 0.7).

    Returns:
        Dict with character, emotion, intensity, applied_morphs ({morph, value}
        read back), body_adjustments ({bone, property, value}), not_found
        (feature slots with no matching dial) and body_not_found (bone roles
        missing on this figure).

    Notes:
        Not-found dials and bones are reported but do not raise errors —
        figures vary in available morphs.
    """
    valid = sorted(_EMOTION_DEFINITIONS.keys())
    if emotion not in _EMOTION_DEFINITIONS:
        raise ToolError(
            f"Unknown emotion: '{emotion}'. Valid emotions: {', '.join(valid)}"
        )
    if not 0.0 <= intensity <= 1.0:
        raise ToolError(f"intensity must be between 0.0 and 1.0, got {intensity}")

    definition = _EMOTION_DEFINITIONS[emotion]

    def _run() -> dict[str, Any]:
        skel = get_scene().find_skeleton_by_label(character_label)
        face = definition.get("face", [])
        # Slot 0 is this emotion's face controller (if any); the rest zero
        # every other emotion's face controller.
        slots: list[tuple[list[str], float]] = [(face, intensity)] if face else []
        slots += [
            (d["face"], 0.0)
            for name, d in _EMOTION_DEFINITIONS.items()
            if name != emotion and d.get("face")
        ]
        results = skel.set_numeric_candidates(slots) if slots else []
        applied: list[dict] = []
        not_found: list[str] = []
        if face and results[0].found:
            applied.append({"morph": results[0].matched, "value": results[0].value})
        elif definition["morphs"]:
            features = skel.set_numeric_candidates(
                [(m["names"], m["value"] * intensity) for m in definition["morphs"]]
            )
            for r in features:
                if r.found:
                    applied.append({"morph": r.matched, "value": r.value})
                else:
                    not_found.append(r.candidates[0] if r.candidates else "unknown")
        body_applied, body_missing = _resolve_body(skel, definition["body"], intensity)
        return {
            "character": character_label,
            "emotion": emotion,
            "intensity": intensity,
            "applied_morphs": applied,
            "body_adjustments": body_applied,
            "not_found": not_found,
            "body_not_found": body_missing,
        }

    try:
        return await run_dazpy(_run)
    except ToolError:
        raise
    except Exception as e:  # pylint: disable=broad-exception-caught
        handle_dazpy_error(e)
        raise  # unreachable: handle_dazpy_error always raises


@mcp.tool()
async def daz_set_body_language(
    figure_label: str,
    posture: str,
    intensity: float = 1.0,
) -> dict[str, Any]:
    """Apply a body-language posture to a figure via bone rotation adjustments.

    Adjusts key skeleton bones (chest, shoulders, neck) to convey a physical
    attitude. Bones are matched per figure generation (Genesis 8
    ``chestUpper``/``lShldrBend``, Genesis 9 ``spine4``/``l_upperarm``, ...),
    and only the one axis each adjustment names is written.

    Args:
        figure_label: Display label of the skeleton/figure (e.g., "Genesis 9").
        posture: One of: confident, defensive, relaxed, tense.
        intensity: Scale factor 0.0–1.0 applied to all bone rotations (default 1.0).

    Returns:
        Dict with success, figure, posture, intensity, applied (list of bone
        adjustments that were set, naming the figure's own bone), and not_found
        (bone roles not present on this figure).

    Notes:
        - Bones missing on non-Genesis figures are skipped and reported in not_found.
        - Combine with daz_set_emotion for full expressive character poses.
    """
    valid_postures = tuple(POSTURES)
    if posture not in valid_postures:
        raise ToolError(
            f"Unknown posture: '{posture}'. Valid postures: {', '.join(valid_postures)}"
        )
    if not 0.0 <= intensity <= 1.0:
        raise ToolError(f"intensity must be between 0.0 and 1.0, got {intensity}")

    def _run() -> dict[str, Any]:
        skel = get_scene().find_skeleton_by_label(figure_label)
        applied, not_found = _resolve_body(skel, POSTURES[posture], intensity)
        return {
            "success": True,
            "figure": figure_label,
            "posture": posture,
            "intensity": intensity,
            "applied": applied,
            "not_found": not_found,
        }

    try:
        return await run_dazpy(_run)
    except ToolError:
        raise
    except Exception as e:  # pylint: disable=broad-exception-caught
        handle_dazpy_error(e)
        raise  # unreachable: handle_dazpy_error always raises


_GAZE_FIXED: dict[str, tuple[float, float]] = {
    "up": (-25.0, 0.0),
    "down": (20.0, 0.0),
    "left": (0.0, -35.0),
    "right": (0.0, 35.0),
    "away": (0.0, 180.0),
}


def _aim_angles(head: dict, target: tuple[float, float, float]) -> tuple[float, float]:
    """Rough (pitch, yaw) degrees to turn a head at *head* toward *target*.

    World-space and approximate, as before: yaw ignores the figure's own
    facing and pitch is halved so the head doesn't over-tilt.
    """
    dx, dy, dz = target[0] - head["x"], target[1] - head["y"], target[2] - head["z"]
    yaw = math.degrees(math.atan2(dx, dz))
    pitch = -math.degrees(math.atan2(dy, math.hypot(dx, dz))) * 0.5
    return pitch, yaw


def _gaze_target(scene: Any, label: str) -> tuple[float, float, float]:
    """World point to look at for *label*: a figure's head, else the node's origin."""
    try:
        figure = scene.find_skeleton_by_label(label)
    except NodeNotFoundError:
        figure = None
    if figure is not None:
        head = resolve_bone("head", figure.bone_names())
        if head is not None:
            pos = figure.find_bone(head).position
            return (pos["x"], pos["y"], pos["z"])
    pos = scene.find_node_by_label(label).position
    return (pos["x"], pos["y"], pos["z"])


@mcp.tool()
async def daz_direct_gaze(
    figure_label: str,
    direction: str,
    target_label: str | None = None,
) -> dict[str, Any]:
    """Point a figure's head/gaze toward a direction or scene object.

    Rotates the head bone to face a named direction or a target node.  For the
    "camera" direction the active viewport camera is used (including Studio's
    built-in Perspective View); for "character" a ``target_label`` must be
    supplied.

    Args:
        figure_label: Display label of the skeleton/figure (e.g., "Genesis 9").
        direction: One of: camera, away, up, down, left, right, character.
        target_label: Required when direction is "character" — the display label
                      of the node or skeleton to look toward.

    Returns:
        Dict with success, figure, direction, applied (list of bone/property
        adjustments), and not_found (bones/properties missing on this figure).

    Notes:
        - "camera" computes a rough angle toward the active viewport camera.
        - "character" aims at the target figure's head bone, or at the target
          node's origin when it is not a figure.
        - ``requested`` holds the computed angles; ``applied`` holds what the
          head kept after its joint limits.
        - Head bone search falls back to the upper neck bone if "head" is not found.
        - Angle computation is approximate (good for typical scene proportions).
    """
    valid_directions = ("camera", "away", "up", "down", "left", "right", "character")
    if direction not in valid_directions:
        raise ToolError(
            f"Unknown direction: '{direction}'. "
            f"Valid directions: {', '.join(valid_directions)}"
        )
    if direction == "character" and not target_label:
        raise ToolError("target_label is required when direction is 'character'")

    def _run() -> dict[str, Any]:
        scene = get_scene()
        skel = scene.find_skeleton_by_label(figure_label)
        names = set(skel.bone_names())
        head_bone = resolve_bone("head", names) or resolve_bone("neckUpper", names)
        if head_bone is None:
            raise ToolError(f"Head/upper neck bone not found on {figure_label!r}")

        if direction in _GAZE_FIXED:
            rot_x, rot_y = _GAZE_FIXED[direction]
        else:
            if direction == "camera":
                cam = scene.viewport_camera()
                if cam is None:
                    raise ToolError("No active viewport camera to look at")
                target = cam.position
            else:
                target = _gaze_target(scene, target_label)
            rot_x, rot_y = _aim_angles(skel.find_bone(head_bone).position, target)

        missing = skel.set_bone_axes({head_bone: {"x": rot_x, "y": rot_y}})
        applied: list[dict] = []
        if not missing:
            # Report what Studio kept: the head's joint limits can clamp it.
            euler = skel.find_bone(head_bone).local_euler or (rot_x, rot_y, 0.0)
            applied = [
                {"bone": head_bone, "property": "XRotate", "value": euler[0]},
                {"bone": head_bone, "property": "YRotate", "value": euler[1]},
            ]
        return {
            "success": True,
            "figure": figure_label,
            "direction": direction,
            "requested": {"x": rot_x, "y": rot_y},
            "applied": applied,
            "not_found": [f"{head_bone}.XRotate", f"{head_bone}.YRotate"] if missing else [],
        }

    try:
        return await run_dazpy(_run)
    except ToolError:
        raise
    except Exception as e:  # pylint: disable=broad-exception-caught
        handle_dazpy_error(e)
        raise  # unreachable: handle_dazpy_error always raises


# ---------------------------------------------------------------------------
# Phase 6.12: Morph Loader Pro
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_load_morph_pro(
    node_label: str,
    obj_path: str,
    morph_name: str | None = None,
    load_mode: str = "EntireFigure",
    overwrite_mode: str = "MakeUnique",
    mirroring: str = "DoNotMirror",
    scale: float = 1.0,
    preserve_existing_deltas: bool | None = None,
    clean_up_orphans: bool | None = None,
    delta_tolerance: float | None = None,
    reverse_deformations: bool = False,
    reverse_deformations_pose_path: str | None = None,
    subdivision: bool | None = None,
    subdivision_mapping: str | None = None,
    subdivision_min_resolution: int | None = None,
    subdivision_max_resolution: int | None = None,
    subdivision_built_resolution: int | None = None,
    subdivision_smooth_cage: bool | None = None,
    attenuate_strength: float | None = None,
    attenuate_edge_strength: float | None = None,
    attenuate_map_path: str | None = None,
    property_group_path: str | None = None,
    hide_secondary_properties: bool | None = None,
    create_control_property: bool = False,
    control_node_label: str | None = None,
    control_property_name: str | None = None,
    control_property_custom_label: str | None = None,
    control_property_erc_type: str | None = None,
    control_property_erc_custom_value: float | None = None,
    only_errors_or_warnings: bool = True,
) -> dict[str, Any]:
    """Load an OBJ morph target onto a figure via Morph Loader Pro (``DzMorphLoader``).

    Headless equivalent of File > Import > Morph Loader Pro (or the right-click
    "Load Morph(s)..." action in the Parameters pane), covering the full option
    set exposed by the Morph Loader Pro plugin's scripting API. The target OBJ
    must share the same vertex order/count as the node's base geometry (a
    "morph target" export, not an arbitrary mesh).

    Args:
        node_label: Display label, internal name, elementID, or ``Parent/Label``
            of the figure/prop to create the morph on.
        obj_path: Absolute path to the source ``.obj`` morph target.
        morph_name: Name for the new morph dial. Defaults to a name derived from
            the OBJ filename if omitted.
        load_mode: One of ``EntireFigure`` (default), ``SelectedNodes``,
            ``PrimaryNode``, ``SingleSkinFigure``, ``SingleSkinFigureFromGraft``.
            Which values are valid depends on what ``node_label`` actually is
            (confirmed live): a plain prop (no skeleton) only accepts
            ``PrimaryNode`` — ``EntireFigure`` raises immediately. A legacy
            (non-"single skin") figure only accepts ``EntireFigure``,
            ``SelectedNodes``, or ``PrimaryNode``. A "single skin" figure only
            accepts ``SingleSkinFigure`` or ``SingleSkinFigureFromGraft``. The
            default of ``EntireFigure`` is only correct for that middle case —
            pass ``PrimaryNode`` explicitly for props.
        overwrite_mode: How to handle an existing morph of the same name — one of
            ``MakeUnique`` (default, renames the new one), ``DeltasAndERCLinks``,
            ``DeltasOnly``. Attention (confirmed live): if a morph with the
            target name already exists, ``MakeUnique`` does **not** silently
            auto-rename it — DAZ Studio pops an interactive "morph already
            exists" rename dialog that blocks the process regardless of
            ``RunSilent``. Avoid this by checking ``daz_search_morphs``/
            ``daz_list_morphs`` first and passing a name you know is unique,
            rather than relying on ``MakeUnique`` to resolve collisions for you.
        mirroring: One of ``DoNotMirror`` (default), ``XSwap``, ``XPosToNeg``,
            ``XNegToPos``, ``YSwap``, ``YPosToNeg``, ``YNegToPos``, ``ZSwap``,
            ``ZPosToNeg``, ``ZNegToPos``.
        scale: Scale factor applied to the OBJ geometry on load (default 1.0).
        preserve_existing_deltas: Keep deltas from an existing morph of the same
            name instead of replacing them.
        clean_up_orphans: Remove same-named morphs left with no deltas after
            overwriting (default plugin behavior if omitted).
        delta_tolerance: Minimum vertex deviation to record as a delta.
        reverse_deformations: If True, "reverses" a posed base mesh before
            diffing so the morph is captured in rest pose. Requires the base
            OBJ to have been exported while posed.
        reverse_deformations_pose_path: Path to the pose file describing the
            pose the OBJ was exported in. Required (and applied before the
            morph is created) when ``reverse_deformations`` is True and the
            current scene pose is not already that pose.
        subdivision: Enable SubD-aware morph creation.
        subdivision_mapping: One of ``Catmark`` (default), ``FacetOrder``,
            ``ZBrushCage``, ``MudboxCage``. Only relevant if ``subdivision``.
        subdivision_min_resolution: Minimum SubD level the morph applies at.
        subdivision_max_resolution: Maximum SubD level the morph applies at.
        subdivision_built_resolution: SubD level the OBJ geometry was authored at.
        subdivision_smooth_cage: Smooth the base cage before diffing.
        attenuate_strength: Strength (0-1) for attenuating the morph at the
            boundary of the current geometry selection.
        attenuate_edge_strength: Edge-specific attenuation strength.
        attenuate_map_path: Path to a weight map image used to attenuate the effect.
        property_group_path: Custom property-group path for the new morph dial
            (e.g. ``"Morphs/Custom/Body"``).
        hide_secondary_properties: Hide the ERC-driven secondary properties this
            load creates (only meaningful with ``create_control_property``).
        create_control_property: If True, ERC-link the new morph to an existing
            numeric property so it is driven by that property's dial instead of
            (or in addition to) its own. Requires ``control_property_name``.
        control_node_label: Node that owns the control property. Defaults to
            ``node_label`` if omitted.
        control_property_name: Label or internal name of the existing numeric
            property to link to. Required when ``create_control_property`` is True.
        control_property_custom_label: Custom label shown for the linked
            (secondary) property instead of the morph's own name.
        control_property_erc_type: ERC formula linking the morph to the control
            property — one of ``ERCDeltaAdd`` (default), ``ERCDivideInto``,
            ``ERCDivideBy``, ``ERCMultiply``, ``ERCSubtract``, ``ERCAdd``,
            ``ERCKeyed``.
        control_property_erc_custom_value: Override value used in the ERC link
            instead of the control property's live value.
        only_errors_or_warnings: If True (default), the returned log only
            contains errors/warnings rather than a full verbose trace.

    Returns:
        Dict with success, node, file, morphName (resolved/actual name used),
        loadMode, overwriteMode, mirroring, controlProperty (label, or null),
        and log (any errors/warnings from the load).

    Examples:
        daz_load_morph_pro("Genesis 9", "C:/morphs/bicep_flex.obj")
        daz_load_morph_pro(
            "Genesis 9", "C:/morphs/bicep_flex.obj",
            morph_name="BicepFlex",
            create_control_property=True,
            control_property_name="Bicep Flex",
        )

    Notes:
        - Requires the Morph Loader Pro plugin to be active in the running DAZ
          Studio instance; raises a clear error if ``DzMorphLoader`` is missing.
        - Use ``daz_erc_freeze`` instead if you need to link an *existing* posed
          shape to a controller — this tool is specifically for importing a new
          OBJ-based morph target.
        - On a plain prop, pass ``load_mode="PrimaryNode"`` — the default
          ``"EntireFigure"`` only works on (non-"single skin") figures and
          raises immediately on props (confirmed live).
        - Pick a ``morph_name`` you've confirmed is unique via
          ``daz_search_morphs``/``daz_list_morphs`` first. ``overwrite_mode``
          does not silently resolve a name collision — DAZ Studio opens a
          blocking interactive rename dialog instead, even with
          ``MakeUnique`` (confirmed live).
    """
    payload: dict[str, Any] = {
        "nodeLabel": node_label,
        "objPath": obj_path,
        "loadMode": load_mode,
        "overwriteMode": overwrite_mode,
        "mirroring": mirroring,
        "scale": scale,
        "reverseDeformations": reverse_deformations,
        "createControlProperty": create_control_property,
        "onlyErrorsOrWarnings": only_errors_or_warnings,
    }
    if morph_name is not None:
        payload["morphName"] = morph_name
    if preserve_existing_deltas is not None:
        payload["preserveExistingDeltas"] = preserve_existing_deltas
    if clean_up_orphans is not None:
        payload["cleanUpOrphans"] = clean_up_orphans
    if delta_tolerance is not None:
        payload["deltaTolerance"] = delta_tolerance
    if reverse_deformations_pose_path is not None:
        payload["reverseDeformationsPosePath"] = reverse_deformations_pose_path
    if subdivision is not None:
        payload["subdivision"] = subdivision
    if subdivision_mapping is not None:
        payload["subdivisionMapping"] = subdivision_mapping
    if subdivision_min_resolution is not None:
        payload["subdivisionMinResolution"] = subdivision_min_resolution
    if subdivision_max_resolution is not None:
        payload["subdivisionMaxResolution"] = subdivision_max_resolution
    if subdivision_built_resolution is not None:
        payload["subdivisionBuiltResolution"] = subdivision_built_resolution
    if subdivision_smooth_cage is not None:
        payload["subdivisionSmoothCage"] = subdivision_smooth_cage
    if attenuate_strength is not None:
        payload["attenuateStrength"] = attenuate_strength
    if attenuate_edge_strength is not None:
        payload["attenuateEdgeStrength"] = attenuate_edge_strength
    if attenuate_map_path is not None:
        payload["attenuateMapPath"] = attenuate_map_path
    if property_group_path is not None:
        payload["propertyGroupPath"] = property_group_path
    if hide_secondary_properties is not None:
        payload["hideSecondaryProperties"] = hide_secondary_properties
    if control_node_label is not None:
        payload["controlNodeLabel"] = control_node_label
    if control_property_name is not None:
        payload["controlPropertyName"] = control_property_name
    if control_property_custom_label is not None:
        payload["controlPropertyCustomLabel"] = control_property_custom_label
    if control_property_erc_type is not None:
        payload["controlPropertyErcType"] = control_property_erc_type
    if control_property_erc_custom_value is not None:
        payload["controlPropertyErcCustomValue"] = control_property_erc_custom_value

    if create_control_property and not control_property_name:
        raise ToolError(
            "control_property_name is required when create_control_property=True"
        )

    return await _execute_by_id("vangard-load-morph-pro", payload)
