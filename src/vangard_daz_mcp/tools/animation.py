"""Animation timeline and keyframe tools for DAZ Studio."""
from __future__ import annotations

from typing import Any

from fastmcp.exceptions import ToolError

from .._mcp import mcp, _execute_by_id
from .._client import get_scene, get_daz_client, run_dazpy
from .._errors import handle_dazpy_error


# ---------------------------------------------------------------------------
# Tools — keyframe management (delegate to registered DazScript)
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_set_keyframe(
    node_label: str,
    property_name: str,
    frame: int,
    value: float,
) -> dict[str, Any]:
    """Set a keyframe on a property at specified frame.

    Creates or updates a keyframe for a numeric property at the given frame number.
    This is the fundamental operation for creating property animations.

    Args:
        node_label: Display label of the node.
        property_name: Property label or internal name.
        frame: Frame number (integer, typically 0-based).
        value: Value to set at this frame.

    Returns:
      - success: true on success
      - node: node label
      - property: property label
      - frame: frame number
      - value: value set at the keyframe

    Example:
        # Animate character moving right (0 to 100cm over 30 frames)
        daz_set_keyframe("Genesis 9", "XTranslate", frame=0, value=0)
        daz_set_keyframe("Genesis 9", "XTranslate", frame=30, value=100)

        # Animate rotation (0 to 90 degrees over 60 frames)
        daz_set_keyframe("Genesis 9", "YRotate", frame=0, value=0)
        daz_set_keyframe("Genesis 9", "YRotate", frame=60, value=90)

        # Animate morph (fade in smile)
        daz_set_keyframe("Genesis 9", "PHMSmile", frame=0, value=0)
        daz_set_keyframe("Genesis 9", "PHMSmile", frame=15, value=0.8)

    Note:
        - DAZ Studio interpolates between keyframes automatically
        - Setting a keyframe at an existing frame updates the value
        - Frames are typically 0-based integers
        - Use daz_set_frame_range() to define the animation length first
    """
    return await _execute_by_id(
        "vangard-set-keyframe",
        {
            "nodeLabel": node_label,
            "propertyName": property_name,
            "frame": frame,
            "value": value,
        },
    )


@mcp.tool()
async def daz_get_keyframes(
    node_label: str,
    property_name: str,
) -> dict[str, Any]:
    """Get all keyframes for a property.

    Returns all keyframes currently set on a property, including frame numbers
    and values. Useful for inspecting existing animations or copying keyframes.

    Args:
        node_label: Display label of the node.
        property_name: Property label or internal name.

    Returns:
      - keyframes: Array of {frame, value} objects
      - count: Number of keyframes

    Example:
        # Get keyframes for a property
        result = daz_get_keyframes("Genesis 9", "XTranslate")
        print(f"Found {result['count']} keyframes:")
        for kf in result['keyframes']:
            print(f"  Frame {kf['frame']}: {kf['value']}")

        # Copy keyframes to another property
        keyframes = daz_get_keyframes("Genesis 9", "XTranslate")
        for kf in keyframes['keyframes']:
            daz_set_keyframe("Genesis 8", "XTranslate", kf['frame'], kf['value'])

        # Check if property is animated
        result = daz_get_keyframes("Genesis 9", "YRotate")
        if result['count'] > 0:
            print("Property is animated")

    Note:
        - Returns empty array if property has no keyframes
        - Keyframes are returned in frame order
        - Frame numbers are integers, values are floats
    """
    return await _execute_by_id(
        "vangard-get-keyframes",
        {"nodeLabel": node_label, "propertyName": property_name},
    )


@mcp.tool()
async def daz_remove_keyframe(
    node_label: str,
    property_name: str,
    frame: int,
) -> dict[str, Any]:
    """Remove a keyframe at specified frame.

    Deletes a single keyframe from a property at the given frame number.
    Other keyframes on the property remain unchanged.

    Args:
        node_label: Display label of the node.
        property_name: Property label or internal name.
        frame: Frame number of keyframe to remove.

    Returns:
      - success: true
      - node: node label
      - property: property label
      - frame: frame number
      - removed: true if keyframe existed and was removed, false if no keyframe at that frame

    Example:
        # Remove specific keyframe
        daz_remove_keyframe("Genesis 9", "XTranslate", frame=15)

        # Remove all keyframes one by one
        keyframes = daz_get_keyframes("Genesis 9", "XTranslate")
        for kf in keyframes['keyframes']:
            daz_remove_keyframe("Genesis 9", "XTranslate", kf['frame'])

    Note:
        - If no keyframe exists at the frame, removed=false (not an error)
        - Other keyframes remain unchanged
        - Use daz_clear_animation() to remove all keyframes at once
    """
    return await _execute_by_id(
        "vangard-remove-keyframe",
        {"nodeLabel": node_label, "propertyName": property_name, "frame": frame},
    )


@mcp.tool()
async def daz_clear_animation(
    node_label: str,
    property_name: str,
) -> dict[str, Any]:
    """Remove all keyframes from a property.

    Clears all animation data from a property, returning it to a static (non-animated)
    state. More efficient than removing keyframes individually.

    Args:
        node_label: Display label of the node.
        property_name: Property label or internal name.

    Returns:
      - success: true
      - node: node label
      - property: property label
      - removed: number of keyframes removed

    Example:
        # Clear animation from a property
        result = daz_clear_animation("Genesis 9", "XTranslate")
        print(f"Removed {result['removed']} keyframes")

        # Clear all transform animations
        transforms = ["XTranslate", "YTranslate", "ZTranslate",
                      "XRotate", "YRotate", "ZRotate"]
        for prop in transforms:
            daz_clear_animation("Genesis 9", prop)

    Note:
        - Removes all keyframes in a single operation
        - More efficient than calling daz_remove_keyframe() repeatedly
        - Property retains its current value after clearing
        - Returns count of keyframes that were removed
    """
    return await _execute_by_id(
        "vangard-clear-animation",
        {"nodeLabel": node_label, "propertyName": property_name},
    )


# ---------------------------------------------------------------------------
# Tools — timeline navigation (dazpy migration)
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_set_frame(frame: int) -> dict[str, Any]:
    """Set current animation frame.

    Moves the timeline to the specified frame. This updates the scene to show
    the state at that frame, evaluating all animated properties.

    Args:
        frame: Frame number to move to (integer).

    Returns:
      - success: true
      - frame: new current frame
      - previousFrame: frame number before the change

    Example:
        # Jump to specific frame
        daz_set_frame(30)

        # Render each frame of animation
        info = daz_get_animation_info()
        for frame in range(info['startFrame'], info['endFrame'] + 1):
            daz_set_frame(frame)
            daz_render(output_path=f"frame_{frame:04d}.png")

        # Preview keyframes
        keyframes = daz_get_keyframes("Genesis 9", "XTranslate")
        for kf in keyframes['keyframes']:
            daz_set_frame(kf['frame'])
            # ... preview or inspect ...

    Note:
        - Scene updates to show animated state at the frame
        - All animated properties evaluate at the new frame
        - Frame numbers are typically 0-based integers
        - Use with daz_render() to export animation frames
    """
    def _run() -> dict:
        scene = get_scene()
        prev = scene.frame()
        scene.set_frame(int(frame))
        return {"success": True, "frame": frame, "previousFrame": prev}

    try:
        return await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)


@mcp.tool()
async def daz_set_frame_range(start_frame: int, end_frame: int) -> dict[str, Any]:
    """Set animation frame range (start and end).

    Defines the playback range for the animation timeline. This determines
    which frames are included when playing or exporting animation.

    Args:
        start_frame: First frame of animation (typically 0).
        end_frame: Last frame of animation.

    Returns:
      - success: true
      - startFrame: new start frame
      - endFrame: new end frame
      - previousStart: previous start frame
      - previousEnd: previous end frame

    Example:
        # Set 120-frame animation (4 seconds at 30fps)
        daz_set_frame_range(0, 119)

        # Set 300-frame animation (10 seconds at 30fps)
        daz_set_frame_range(0, 299)

        # Set custom range starting from frame 10
        daz_set_frame_range(10, 100)

    Note:
        - Frame range is inclusive (both start and end frames are included)
        - Default FPS in DAZ Studio is typically 30
        - Duration in seconds = (end - start + 1) / fps
        - Example: frames 0-29 at 30fps = 1 second (30 frames)
    """
    if end_frame < start_frame:
        raise ToolError(
            f"end_frame ({end_frame}) must be >= start_frame ({start_frame})"
        )

    def _run() -> dict:
        scene = get_scene()
        prev = scene.anim_range()
        scene.set_play_range(int(start_frame), int(end_frame))
        scene.set_anim_range(int(start_frame), int(end_frame))
        return {
            "success": True,
            "startFrame": start_frame,
            "endFrame": end_frame,
            "previousStart": prev["start"],
            "previousEnd": prev["end"],
        }

    try:
        return await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)


@mcp.tool()
async def daz_get_animation_info() -> dict[str, Any]:
    """Get animation timeline info (current frame, range, fps).

    Returns information about the current animation timeline state, including
    the current frame, frame range, and frames per second.

    Returns:
      - currentFrame: current timeline position
      - startFrame: first frame of animation range
      - endFrame: last frame of animation range
      - fps: frames per second
      - totalFrames: total number of frames (endFrame - startFrame + 1)
      - durationSeconds: animation duration in seconds

    Example:
        # Get timeline info
        info = daz_get_animation_info()
        print(f"Current frame: {info['currentFrame']}")
        print(f"Range: {info['startFrame']}-{info['endFrame']}")
        print(f"Duration: {info['durationSeconds']} seconds")
        print(f"FPS: {info['fps']}")

        # Render entire animation
        info = daz_get_animation_info()
        for frame in range(info['startFrame'], info['endFrame'] + 1):
            daz_set_frame(frame)
            daz_render(output_path=f"output/frame_{frame:04d}.png")

        # Check if at end of animation
        info = daz_get_animation_info()
        if info['currentFrame'] >= info['endFrame']:
            print("At end of animation")

    Note:
        - FPS is typically 30 in DAZ Studio
        - Frame range is inclusive (both start and end are included)
        - totalFrames includes both start and end frames
        - Use before rendering animation to know frame count
    """
    def _run() -> dict:
        scene = get_scene()
        client = get_daz_client()
        current = scene.frame()
        anim = scene.anim_range()
        # DAZ Studio uses 4800 ticks/second; time_step = ticks per frame
        # getTimeStep() returns a DzTime object, which serialises to a dict;
        # .valueOf() yields the tick count (Number(ts) would return 0).
        ts_result = client.execute(
            "(function(){ return Scene.getTimeStep().valueOf(); })();"
        )
        raw_step = ts_result.value
        step = (
            raw_step
            if isinstance(raw_step, (int, float)) and not isinstance(raw_step, bool) and raw_step > 0
            else 160  # 160 ticks @ 30 fps
        )
        fps = round(4800 / step)
        start = anim["start"]
        end = anim["end"]
        total = max(0, end - start + 1)
        return {
            "currentFrame": current,
            "startFrame": start,
            "endFrame": end,
            "fps": fps,
            "totalFrames": total,
            "durationSeconds": round(total / fps, 3) if fps > 0 else 0.0,
        }

    try:
        return await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)
