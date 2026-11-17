"""Figure/character MCP tools for DAZ Studio.

Covers look-at helpers, reach-toward IK, interactive posing, pose reset,
and pose file save/load via dazpy.
"""
from __future__ import annotations

from typing import Any

from fastmcp.exceptions import ToolError

from dazpy import DazPose

from .._mcp import mcp, _execute_by_id
from .._client import get_scene, run_dazpy
from .._errors import handle_dazpy_error

# ---------------------------------------------------------------------------
# Bone-group filter map (mirrors server.py _POSE_BONE_GROUPS)
# ---------------------------------------------------------------------------

_POSE_BONE_GROUPS: dict[str, set[str]] = {
    "arms_only": {
        "lShldrBend", "rShldrBend", "lShldrTwist", "rShldrTwist",
        "lForearmBend", "rForearmBend", "lForearmTwist", "rForearmTwist",
        "lHand", "rHand",
        "l_upperarm", "r_upperarm", "l_forearm", "r_forearm",
        "l_hand", "r_hand",
    },
    "legs_only": {
        "lThighBend", "rThighBend", "lThighTwist", "rThighTwist",
        "lShin", "rShin", "lFoot", "rFoot", "lToe", "rToe",
        "l_thigh", "r_thigh", "l_shin", "r_shin", "l_foot", "r_foot",
    },
    "spine": {
        "hip", "pelvis",
        "abdomenLower", "abdomenUpper", "chestLower", "chestUpper",
        "neckLower", "neckUpper", "head",
        "spine1", "spine2", "spine3", "spine4",
        "neck1", "neck2",
    },
}


# ---------------------------------------------------------------------------
# Look-at / reach helpers
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_look_at_point(
    character_label: str,
    target_x: float,
    target_y: float,
    target_z: float,
    mode: str = "head",
) -> dict[str, Any]:
    """Make character look at a world-space point with configurable body involvement.

    This helper uses cascading rotations from eyes through the body to create
    natural-looking character attention. Different modes control how much of
    the body participates in the look direction.

    Args:
        character_label: Display label or internal name of the character figure.
        target_x: World X coordinate (cm) to look at.
        target_y: World Y coordinate (cm) to look at.
        target_z: World Z coordinate (cm) to look at.
        mode: How much body to involve in the look. Options:
              - "eyes": Only rotate eyes
              - "head": Eyes + head rotation (default)
              - "neck": Eyes + head + neck
              - "torso": Eyes + head + neck + chest
              - "full": Complete body rotation including hip

    Returns:
      - success: true on success
      - character: character label
      - mode: the mode used
      - rotatedBones: list of bone labels that were rotated

    Example:
        # Character looks at point in front of them at eye level
        daz_look_at_point("Genesis 9", 0, 160, 200, mode="head")

        # Full body turn to look behind
        daz_look_at_point("Genesis 9", 0, 140, -150, mode="full")
    """
    return await _execute_by_id("vangard-look-at-point", {
        "characterLabel": character_label,
        "targetX": target_x,
        "targetY": target_y,
        "targetZ": target_z,
        "mode": mode,
    })


@mcp.tool()
async def daz_look_at_character(
    source_label: str,
    target_label: str,
    mode: str = "head",
) -> dict[str, Any]:
    """Make one character look at another character's face.

    Automatically finds the target character's head position and rotates
    the source character to look at it using cascading body rotations.

    Args:
        source_label: Display label of the character who will look.
        target_label: Display label of the character to look at.
        mode: How much body to involve. Options:
              - "eyes": Only rotate eyes
              - "head": Eyes + head rotation (default)
              - "neck": Eyes + head + neck
              - "torso": Eyes + head + neck + chest
              - "full": Complete body rotation including hip

    Returns:
      - success: true on success
      - source: source character label
      - target: target character label
      - mode: the mode used
      - targetPosition: {x, y, z} world coordinates of target's head
      - rotatedBones: list of bone labels that were rotated

    Example:
        # Alice looks at Bob with head turn
        daz_look_at_character("Alice", "Bob", mode="head")

        # Bob turns his whole body to face Alice
        daz_look_at_character("Bob", "Alice", mode="full")
    """
    return await _execute_by_id("vangard-look-at-character", {
        "sourceLabel": source_label,
        "targetLabel": target_label,
        "mode": mode,
    })


@mcp.tool()
async def daz_reach_toward(
    character_label: str,
    side: str,
    target_x: float,
    target_y: float,
    target_z: float,
) -> dict[str, Any]:
    """Position character's arm to reach toward a world-space point.

    Uses pseudo-IK approximation to calculate shoulder and elbow rotations
    that position the hand near the target point. Automatically adjusts
    elbow bend based on target distance.

    Args:
        character_label: Display label or internal name of the character.
        side: Which arm to use: "left" or "right".
        target_x: World X coordinate (cm) to reach toward.
        target_y: World Y coordinate (cm) to reach toward.
        target_z: World Z coordinate (cm) to reach toward.

    Returns:
      - success: true on success
      - character: character label
      - side: which arm was posed
      - targetDistance: distance in cm from shoulder to target
      - bones: list of bone labels that were rotated

    Example:
        # Reach right hand toward point in front at chest height
        daz_reach_toward("Genesis 9", "right", 50, 130, 80)

        # Reach left hand toward object on left side
        daz_reach_toward("Genesis 9", "left", -60, 100, 50)

    Note:
        This uses simplified IK approximation. For precise hand positioning
        or complex reaching, load an artist-created pose preset instead.
    """
    return await _execute_by_id("vangard-reach-toward", {
        "characterLabel": character_label,
        "side": side,
        "targetX": target_x,
        "targetY": target_y,
        "targetZ": target_z,
    })


@mcp.tool()
async def daz_interactive_pose(
    char1_label: str,
    char2_label: str,
    interaction_type: str = "face-each-other",
    distance: float | None = None,
) -> dict[str, Any]:
    """Coordinate two characters for interactive poses.

    Applies complementary poses to two characters for common interaction
    scenarios. Handles both positioning and pose application.

    Args:
        char1_label: Display label of first character.
        char2_label: Display label of second character.
        interaction_type: Type of interaction. Options:
            - "face-each-other": Position and rotate to face each other (default)
            - "hug": Both characters hug with arms around each other
            - "shoulder-arm": Char1 puts arm around char2's shoulders
            - "handshake": Both extend right hands for handshake
        distance: Optional spacing between characters in cm (default varies by type:
                  face=100, hug=40, shoulder-arm=30, handshake=60).

    Returns:
      - success: true on success
      - char1: first character label
      - char2: second character label
      - interactionType: the interaction type used
      - applied: list of pose components that were applied

    Example:
        # Position characters facing each other at conversation distance
        daz_interactive_pose("Alice", "Bob", "face-each-other", distance=120)

        # Create tight hug
        daz_interactive_pose("Alice", "Bob", "hug", distance=30)

        # Bob puts arm around Alice's shoulders
        daz_interactive_pose("Bob", "Alice", "shoulder-arm")

    Note:
        These are simplified interaction poses. For natural-looking results,
        you may need to fine-tune positions and rotations using daz_set_property
        or load artist-created pose presets.
    """
    args: dict[str, Any] = {
        "char1Label": char1_label,
        "char2Label": char2_label,
        "interactionType": interaction_type,
    }
    if distance is not None:
        args["distance"] = distance
    return await _execute_by_id("vangard-interactive-pose", args)


# ---------------------------------------------------------------------------
# Pose reset / save / load
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_reset_pose(
    node_label: str,
    zero_transforms: bool = False,
) -> dict[str, Any]:
    """Zero all bone rotations on a figure, returning it to its rest pose.

    Recursively walks the node's skeleton and sets XRotate, YRotate, and
    ZRotate to 0 on every bone. Optionally also zeroes the root node's
    translation and scale.

    Args:
        node_label: Display label of the figure whose pose should be cleared.
        zero_transforms: If True, also zero the root XYZ translation and reset
                         Scale to 1.0 (default False — only rotations are reset).

    Returns:
        Dict with node, bones_reset (count), and transforms_zeroed.

    Examples:
        daz_reset_pose("Genesis 9")
        daz_reset_pose("Genesis 9", zero_transforms=True)  # also move to origin

    Notes:
        - This does not affect morph values. Use daz_set_morph or daz_set_property
          to zero morphs individually.
        - Keyframes on bone properties are not removed; use daz_clear_animation
          if you also need to strip animation data.
    """
    return await _execute_by_id(
        "vangard-reset-pose",
        {"nodeLabel": node_label, "zeroTransforms": zero_transforms},
    )


@mcp.tool()
async def daz_save_pose(
    figure_label: str,
    pose_name: str,
    output_path: str,
) -> dict[str, Any]:
    """Capture all bone rotations and translations from a figure and save to a JSON pose file.

    Walks the entire bone hierarchy of the named figure, reads XRotate/YRotate/ZRotate
    and XTranslate/YTranslate/ZTranslate for each bone, and writes the result as a JSON
    file at ``output_path``.  The file can later be loaded with ``daz_load_pose``.

    Args:
        figure_label: Display label of the source figure (e.g. ``"Genesis 9"``).
        pose_name: Human-readable name stored inside the pose file (e.g. ``"T-Pose"``).
        output_path: Absolute path where the ``.json`` pose file will be written
            (e.g. ``"C:/poses/hero_idle.json"``).

    Returns:
        Dict with keys:
        - success: true on success
        - figure: confirmed figure label
        - pose_name: name stored in the file
        - bone_count: number of bones captured
        - file: absolute path written

    Examples:
        daz_save_pose("Genesis 9", "Hero Idle", "C:/poses/hero_idle.json")
        daz_save_pose("Victoria 9", "Sitting Pose", "D:/assets/sitting.json")
    """
    def _run() -> dict[str, Any]:
        scene = get_scene()
        skel = scene.find_skeleton_by_label(figure_label)
        pose = DazPose.capture(skel)
        pose.save(output_path)
        return {
            "success": True,
            "figure": figure_label,
            "pose_name": pose_name,
            "bone_count": len(pose.bones),
            "file": output_path,
        }

    try:
        return await run_dazpy(_run)
    except ToolError:
        raise
    except Exception as e:
        handle_dazpy_error(e)


@mcp.tool()
async def daz_load_pose(
    figure_label: str,
    pose_path: str,
    bone_group: str = "full",
) -> dict[str, Any]:
    """Load a saved pose JSON file and apply it to a figure.

    Reads a pose file created by ``daz_save_pose`` and applies bone rotations
    and translations to the named figure.  The optional ``bone_group`` filter
    limits which bones are updated.

    Args:
        figure_label: Display label of the target figure (e.g. ``"Genesis 9"``).
        pose_path: Absolute path to the ``.json`` pose file created by
            ``daz_save_pose`` (e.g. ``"C:/poses/hero_idle.json"``).
        bone_group: Which bones to apply.  Options:
            - ``"full"`` (default) — all bones in the file
            - ``"arms_only"`` — shoulders, forearms, hands
            - ``"legs_only"`` — thighs, shins, feet
            - ``"spine"`` — hip, pelvis, spine chain, neck, head

    Returns:
        Dict with keys:
        - success: true on success
        - figure: confirmed figure label
        - pose_name: name from the pose file
        - bones_applied: number of bones whose values were written
        - bones_skipped: number of bones not found on the figure

    Examples:
        daz_load_pose("Genesis 9", "C:/poses/hero_idle.json")
        daz_load_pose("Genesis 9", "C:/poses/hero_idle.json", bone_group="arms_only")
        daz_load_pose("Clone 1", "C:/poses/sitting.json", bone_group="spine")
    """
    if bone_group != "full" and bone_group not in _POSE_BONE_GROUPS:
        raise ToolError(
            f"Unknown bone_group {bone_group!r}. "
            "Valid values: full, arms_only, legs_only, spine"
        )

    def _run() -> dict[str, Any]:
        scene = get_scene()
        skel = scene.find_skeleton_by_label(figure_label)
        pose = DazPose.load(pose_path)

        if bone_group != "full":
            allowed = _POSE_BONE_GROUPS[bone_group]
            skipped = len([k for k in pose.bones if k not in allowed])
            filtered_bones = {k: v for k, v in pose.bones.items() if k in allowed}
            filtered_pose = DazPose(
                figure=pose.figure,
                bones=filtered_bones,
                morphs={},
                props={},
            )
            filtered_pose.apply(skel)
            return {
                "success": True,
                "figure": figure_label,
                "pose_name": pose.figure,
                "bones_applied": len(filtered_bones),
                "bones_skipped": skipped,
            }

        pose.apply(skel)
        return {
            "success": True,
            "figure": figure_label,
            "pose_name": pose.figure,
            "bones_applied": len(pose.bones),
            "bones_skipped": 0,
        }

    try:
        return await run_dazpy(_run)
    except ToolError:
        raise
    except Exception as e:
        handle_dazpy_error(e)


@mcp.tool()
async def daz_erc_freeze(
    controller_node: str,
    controller_property: str,
    freeze_nodes: list[str] | None = None,
    restore_figure: bool = True,
    restore_rigging: bool = True,
    apply_controller: bool = True,
    keyed: bool = False,
) -> dict[str, Any]:
    """Headless ERC Freeze — link current non-default numeric values to a controller.

    Uses ``new DzERCFreeze()`` from the Property Hierarchy plugin, not the
    ``DzERCFreezeAction`` menu item (which opens a dialog and will time out).
    ``MainWindow.menuBar()`` is not needed and is not scriptable.

    The controller property must already exist. Properties to freeze are
    whatever currently differs from raw/default on each freeze node
    (``addPropertiesToFreeze``). If everything is at default, the call errors.

    Args:
        controller_node: Figure or bone that owns the controlling dial
            (label, name, elementID, or ``Parent/Label``).
        controller_property: Label or internal name of the controlling
            numeric property (e.g. a custom morph).
        freeze_nodes: Nodes whose non-default numeric properties are linked.
            Defaults to ``controller_node`` itself.
        restore_figure: Restore figure shape after freeze (default True).
        restore_rigging: Restore rigging after freeze (default True).
        apply_controller: Apply the controller as part of the freeze (default True).
        keyed: Use keyed ERC instead of delta-add (default False).

    Returns:
        Dict with success, controllerNode, controllerProperty, freezeNodes,
        propertiesFrozen.

    Examples:
        daz_erc_freeze("Genesis 8 Female", "MyShape", freeze_nodes=["Genesis 8 Female"])
    """
    payload: dict[str, Any] = {
        "controllerNode": controller_node,
        "controllerProperty": controller_property,
        "restoreFigure": restore_figure,
        "restoreRigging": restore_rigging,
        "applyController": apply_controller,
        "keyed": keyed,
    }
    if freeze_nodes:
        payload["freezeNodes"] = freeze_nodes
    return await _execute_by_id("vangard-erc-freeze", payload)
