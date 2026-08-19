"""Render tools for the Vangard DAZ MCP server."""
from __future__ import annotations

import asyncio
import os
from typing import Any

import dazpy.exceptions as daz_exc
from fastmcp.exceptions import ToolError

from .._mcp import mcp, _execute_by_id, _execute_by_id_async, _execute_render, _execute_render_batch
from .._client import get_async_daz_client
from .._errors import handle_dazpy_error


# ---------------------------------------------------------------------------
# Synchronous render tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_render(
    output_path: str | None = None,
) -> dict[str, Any]:
    """Trigger a render in DAZ Studio using the current render settings.

    Render dimensions, format, and other options are whatever is currently
    configured in DAZ Studio's Render Settings panel.

    Args:
        output_path: Optional absolute path for the output image
                     (e.g. "C:/renders/scene.png"). If omitted, DAZ Studio
                     uses its currently configured output path.

    Returns:
      - success: true when the render was launched without error
    """
    args: dict[str, Any] = {}
    if output_path is not None:
        args["outputPath"] = output_path
    return await _execute_by_id("vangard-render", args or None)


@mcp.tool()
async def daz_render_with_camera(
    camera_label: str,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Render from specific camera without changing active viewport camera.

    Renders the scene from the specified camera's viewpoint. The viewport camera
    remains unchanged, making this ideal for multi-camera renders without
    disrupting the user's viewport.

    Args:
        camera_label: Display label of the camera to render from.
        output_path: Optional output file path. If not specified, renders to viewport.

    Returns:
      - success: true on success
      - camera: camera label used for render
      - outputPath: output file path (or null if rendered to viewport)

    Example:
        # Render from specific camera
        daz_render_with_camera("Camera 1", output_path="/path/to/render.png")

        # Render from multiple cameras without changing viewport
        cameras = ["Front", "Side", "Top", "Perspective"]
        for cam in cameras:
            daz_render_with_camera(cam, output_path=f"renders/{cam}.png")

        # Test render from camera (to viewport, no file)
        daz_render_with_camera("Camera 1")

    Note:
        - Viewport camera remains unchanged after render
        - Previous render camera is restored automatically
        - Use for multi-camera batch renders
        - Combine with daz_orbit_camera_around() to set up camera first
    """
    args: dict[str, Any] = {"cameraLabel": camera_label}
    if output_path is not None:
        args["outputPath"] = output_path

    return await _execute_by_id("vangard-render-with-camera", args)


@mcp.tool()
async def daz_get_render_settings() -> dict[str, Any]:
    """Get current render settings and configuration.

    Returns information about the current render configuration, including
    render target, output path, aspect ratio, and render camera.

    Returns:
      - renderToFile: true if rendering to file, false if to viewport
      - outputPath: current output file path (or null)
      - currentCamera: label of current render camera (or null for viewport camera)
      - aspectRatio: aspect ratio value
      - aspectWidth: aspect width component
      - aspectHeight: aspect height component

    Example:
        # Check render settings
        settings = daz_get_render_settings()
        print(f"Render camera: {settings['currentCamera']}")
        print(f"Output: {settings['outputPath']}")
        print(f"Aspect: {settings['aspectWidth']}x{settings['aspectHeight']}")

        # Verify render is configured correctly before batch render
        settings = daz_get_render_settings()
        if not settings['renderToFile']:
            print("Warning: Render is configured for viewport, not file output")

    Note:
        - Aspect ratio determines render dimensions relative to each other
        - Pixel dimensions cannot be set reliably via DazScript
        - currentCamera may be null if using active viewport camera
    """
    return await _execute_by_id("vangard-get-render-settings", {})


@mcp.tool()
async def daz_batch_render_cameras(
    cameras: list[str],
    output_dir: str,
    base_filename: str = "render",
) -> dict[str, Any]:
    """Render from multiple cameras in sequence.

    Renders the same scene from multiple camera angles in a single operation.
    Each camera generates a separate output file with the camera name appended.

    Args:
        cameras: List of camera labels to render from.
        output_dir: Output directory for rendered images.
        base_filename: Base filename (default: "render"). Camera name is appended automatically.

    Returns:
      - success: true on success
      - rendered: Array of {camera, outputPath} objects
      - total: Total number of cameras attempted

    Example:
        # Render from multiple preset cameras
        daz_batch_render_cameras(
            cameras=["Front", "Side", "Top", "Perspective"],
            output_dir="/path/to/renders",
            base_filename="character"
        )
        # Generates: character_Front.png, character_Side.png, etc.

        # Render turntable (8 cameras around character)
        cameras = [f"Cam_{angle}" for angle in [0, 45, 90, 135, 180, 225, 270, 315]]
        daz_batch_render_cameras(cameras, "/path/to/turntable", "frame")

        # Render all cameras in scene
        scene_info = daz_scene_info()
        all_cameras = [cam['label'] for cam in scene_info['cameras']]
        daz_batch_render_cameras(all_cameras, "/path/to/renders")

    Note:
        - Camera names in filenames have non-alphanumeric chars replaced with underscores
        - All renders use current scene state (same lighting, poses, etc.)
        - Previous render camera is restored after batch completes
        - Cameras that don't exist are skipped
    """
    return await _execute_by_id(
        "vangard-batch-render-cameras",
        {
            "cameras": cameras,
            "outputDir": output_dir,
            "baseFilename": base_filename,
        },
    )


@mcp.tool()
async def daz_render_animation(
    output_dir: str,
    start_frame: int | None = None,
    end_frame: int | None = None,
    filename_pattern: str = "frame",
    camera: str | None = None,
) -> dict[str, Any]:
    """Render animation frame range as image sequence.

    Renders each frame of an animation to separate image files. Automatically
    advances through frames and generates zero-padded filenames for proper
    sorting. This is the recommended way to export animations.

    Args:
        output_dir: Output directory for rendered frames.
        start_frame: First frame to render (default: animation range start).
        end_frame: Last frame to render (default: animation range end).
        filename_pattern: Filename pattern (default: "frame"). Frame number is appended.
        camera: Optional camera label to render from (default: current render camera).

    Returns:
      - success: true on success
      - rendered: Array of {frame, outputPath} objects
      - total: Total number of frames rendered
      - frames: {start, end} frame range rendered

    Example:
        # Render entire animation
        daz_render_animation(output_dir="/path/to/animation")
        # Generates: frame_0000.png, frame_0001.png, ..., frame_0119.png

        # Render specific frame range
        daz_render_animation(
            output_dir="/path/to/animation",
            start_frame=30,
            end_frame=60,
            filename_pattern="clip"
        )

        # Render animation from specific camera
        daz_render_animation(
            output_dir="/path/to/animation",
            camera="Camera 1"
        )

        # Render preview (every 5th frame)
        info = daz_get_animation_info()
        for frame in range(info['startFrame'], info['endFrame'] + 1, 5):
            daz_render_animation(
                output_dir="/path/to/preview",
                start_frame=frame,
                end_frame=frame,
                filename_pattern=f"preview_frame"
            )

    Note:
        - Frame numbers are zero-padded to 4 digits (0000, 0001, etc.)
        - Current timeline frame is restored after render completes
        - If camera is specified, render camera is restored after completion
        - Use daz_get_animation_info() to get default frame range
        - Convert to video: ffmpeg -framerate 30 -i frame_%04d.png output.mp4
    """
    args: dict[str, Any] = {
        "outputDir": output_dir,
        "filenamePattern": filename_pattern,
    }
    if start_frame is not None:
        args["startFrame"] = start_frame
    if end_frame is not None:
        args["endFrame"] = end_frame
    if camera is not None:
        args["camera"] = camera

    return await _execute_by_id("vangard-render-animation", args)


# ---------------------------------------------------------------------------
# Async render tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_render_async(
    output_path: str,
    width: int | None = None,
    height: int | None = None,
    camera: str | None = None,
    engine: str | None = None,
    iray_samples: int | None = None,
) -> dict[str, Any]:
    """Start a native render asynchronously and return immediately.

    Supports native render parameters and cancellation via daz_cancel_request().
    Render request IDs have the prefix "rnd-" so the protocol client selects
    the correct cancellation operation automatically.

    Use daz_get_request_status() to poll and daz_get_request_result() for the result.

    IMPORTANT: The scene is locked while the render runs. Do not modify the
    scene until the request status is "completed", "failed", or "cancelled".

    Args:
        output_path: Absolute file path for the rendered image (required).
        width: Render width in pixels. Must be paired with height.
        height: Render height in pixels. Must be paired with width.
        camera: Camera label to render from (default: active render camera).
        engine: Render engine — "iray", "3delight", or "filament".
        iray_samples: Iray max samples (overrides current quality settings).

    Returns:
        {"request_id": "rnd-XXXXXXXX", "status": "queued", "submitted_at": "..."}
    """
    params: dict[str, Any] = {"output_path": output_path}
    if width is not None:
        params["width"] = width
    if height is not None:
        params["height"] = height
    if camera is not None:
        params["camera"] = camera
    if engine is not None:
        params["engine"] = engine
    if iray_samples is not None:
        params["iray_samples"] = iray_samples
    return await _execute_render(params)


@mcp.tool()
async def daz_render_with_camera_async(
    camera_label: str,
    output_path: str,
    width: int | None = None,
    height: int | None = None,
    engine: str | None = None,
    iray_samples: int | None = None,
) -> dict[str, Any]:
    """Start a camera-specific render asynchronously — returns immediately with a request_id.

    Convenience wrapper over daz_render_async that pins the camera. Renders from
    the specified camera without changing the active viewport camera.

    Args:
        camera_label: Display label of the camera to render from.
        output_path: Absolute file path for the rendered image.
        width: Render width in pixels (must pair with height).
        height: Render height in pixels (must pair with width).
        engine: Render engine — "iray", "3delight", or "filament".
        iray_samples: Iray max samples override.

    Returns:
        {"request_id": "rnd-XXXXXXXX", "status": "queued", "submitted_at": "..."}
    """
    params: dict[str, Any] = {"output_path": output_path, "camera": camera_label}
    if width is not None:
        params["width"] = width
    if height is not None:
        params["height"] = height
    if engine is not None:
        params["engine"] = engine
    if iray_samples is not None:
        params["iray_samples"] = iray_samples
    return await _execute_render(params)


@mcp.tool()
async def daz_batch_render_cameras_async(
    cameras: list[str],
    output_dir: str,
    base_filename: str = "render",
    engine: str | None = None,
    iray_samples: int | None = None,
) -> dict[str, Any]:
    """Queue renders from multiple cameras as a validated batch.

    The server validates ALL cameras before enqueuing any render.
    This is all-or-nothing: if any camera name is invalid the entire batch is rejected.

    Args:
        cameras: List of camera display labels.
        output_dir: Directory where rendered images are saved.
        base_filename: Filename prefix. Output is <base_filename>_<camera>.png.
        engine: Render engine for all variants — "iray", "3delight", or "filament".
        iray_samples: Iray max samples override for all variants.

    Returns:
        {
            "request_ids": ["rnd-XXXXXXXX", ...],
            "total": 3,
            "cameras": ["Cam_0", "Cam_45", "Cam_90"]
        }

    Example:
        batch = await daz_batch_render_cameras_async(
            cameras=["Cam_0", "Cam_45", "Cam_90"],
            output_dir="C:/renders/turntable"
        )
        for req_id in batch["request_ids"]:
            result = await daz_get_request_result(req_id, wait=True)
    """
    base: dict[str, Any] = {}
    if engine is not None:
        base["engine"] = engine
    if iray_samples is not None:
        base["iray_samples"] = iray_samples

    variants = [
        {"output_path": os.path.join(output_dir, f"{base_filename}_{cam}.png"), "camera": cam}
        for cam in cameras
    ]
    body: dict[str, Any] = {"variants": variants}
    if base:
        body["base"] = base

    data = await _execute_render_batch(body)
    return {
        "request_ids": data.get("request_ids", []),
        "total": data.get("total", len(cameras)),
        "cameras": cameras,
    }


@mcp.tool()
async def daz_render_batch(
    variants: list[dict[str, Any]],
    base: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Submit a batch of render variants — validated and queued atomically.

    All variants are validated before any render is enqueued (all-or-nothing).
    Renders execute serially but are each independently
    cancellable via daz_cancel_request().

    Args:
        variants: List of render specs. Each must include ``output_path``. Optional
                  per-variant overrides: ``width``, ``height``, ``camera``, ``engine``,
                  ``iray_samples``, ``figure``/``figures``, ``morphs``.
        base: Default settings shared by all variants. Same keys as variants. Overridden
              by any key present in the variant itself.

    Returns:
        {
            "request_ids": ["rnd-XXXXXXXX", ...],
            "total": 5
        }

    Example — product photography with expression variants:
        daz_render_batch(
            base={"figure": "Genesis 9", "width": 1920, "height": 1080},
            variants=[
                {"output_path": "C:/out/neutral.png", "morphs": {"Smile": 0.0}},
                {"output_path": "C:/out/smile.png",   "morphs": {"Smile": 1.0}},
                {"output_path": "C:/out/serious.png", "morphs": {"Brow Down": 0.5}},
            ]
        )
    """
    body: dict[str, Any] = {"variants": variants}
    if base is not None:
        body["base"] = base
    return await _execute_render_batch(body)


@mcp.tool()
async def daz_render_animation_async(
    output_dir: str,
    start_frame: int | None = None,
    end_frame: int | None = None,
    filename_pattern: str = "frame",
    camera: str | None = None,
) -> dict[str, Any]:
    """Start an animation render asynchronously — returns immediately with a request_id.

    Queues a full animation render (all frames as an image sequence). This can
    take hours; use daz_get_request_status() to monitor progress and
    daz_get_request_result() to confirm completion.

    Args:
        output_dir: Directory where frame images are saved.
        start_frame: First frame (default: animation range start).
        end_frame: Last frame (default: animation range end).
        filename_pattern: Filename prefix (default: "frame"). Frame number appended.
        camera: Optional camera label (default: current render camera).

    Returns:
        {"request_id": "script-XXXXXXXX", "status": "queued", "submitted_at": "..."}
    """
    args: dict[str, Any] = {
        "outputDir": output_dir,
        "filenamePattern": filename_pattern,
    }
    if start_frame is not None:
        args["startFrame"] = start_frame
    if end_frame is not None:
        args["endFrame"] = end_frame
    if camera is not None:
        args["camera"] = camera
    return await _execute_by_id_async("vangard-render-animation", args)


# ---------------------------------------------------------------------------
# Request management tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_get_request_status(request_id: str) -> dict[str, Any]:
    """Get the current status of an async request (non-blocking, always fast).

    Safe to call frequently — reads directly from the server's in-memory map
    without executing any DazScript.

    Args:
        request_id: Request ID returned by an async submission tool.

    Returns:
        {
            "request_id": "script-XXXXXXXX",
            "status": "running",   # queued | running | completed | failed | cancelled
            "progress": 0.0,       # 0.0 while running (DAZ single-frame renders have no
                                   # mid-frame progress), 1.0 when complete
            "observation": {       # populated when submit used report_file
                "progress": {"value": 0.5, "phase": "render"},
                "log_tail": [],
                "log_total": 0,
                "log_truncated": False,
                "output_manifest": {"count": 0, "outputs": []},
            },
            "elapsed_ms": 45000,   # present while running
            "queue_position": 2    # present while queued
        }
    """
    client = get_async_daz_client()
    try:
        data = await client.get_request_status(request_id)
    except daz_exc.DazError as exc:
        handle_dazpy_error(exc)
    if data.get("status") == "not_found":
        raise ToolError(f"Request not found: {request_id}")
    return data


@mcp.tool()
async def daz_get_request_result(
    request_id: str,
    wait: bool = True,
    timeout_seconds: int = 3600,
) -> dict[str, Any]:
    """Get the result of a completed async request.

    Args:
        request_id: Request ID returned by an async submission tool.
        wait: If True (default), block until the request finishes (up to timeout).
              If False, return immediately with current status even if not done.
        timeout_seconds: Max seconds to wait when wait=True (default 3600 = 1 hour).

    Returns when complete:
        {
            "request_id": "script-XXXXXXXX",
            "status": "completed",
            "success": true,
            "result": {...},        # same as sync tool result
            "output": [...],        # captured DazScript print() output
            "error": null,
            "duration_ms": 267000,
            "completed_at": "2026-04-08T..."
        }

    Raises ToolError if the request failed.
    """
    client = get_async_daz_client()
    try:
        data = await client.get_request_result(
            request_id,
            wait=wait,
            wait_timeout=timeout_seconds,
        )
    except daz_exc.DazError as exc:
        handle_dazpy_error(exc)

    status = data.get("status", "unknown")
    if status == "not_found":
        raise ToolError(f"Request not found: {request_id}")
    if status == "failed":
        raise ToolError(f"Async request failed: {data.get('error', 'unknown error')}")
    if status == "cancelled":
        return data
    return data


@mcp.tool()
async def daz_cancel_request(request_id: str) -> dict[str, Any]:
    """Cancel a queued or running async request.

    For queued requests: cancellation is immediate.
    For running renders: sends a killRender() signal to DAZ Studio; may take a
    few seconds to take effect as the renderer finishes the current tile.

    Render requests (IDs starting with "rnd-") issue the server's render
    cancellation operation; script requests use ordinary request cancellation.

    Args:
        request_id: Request ID returned by an async submission tool
                    (e.g. "rnd-XXXXXXXX" from daz_render_async,
                     "script-XXXXXXXX" from _execute_by_id_async).

    Returns:
        {"request_id": "...", "status": "cancelled", "cancelled_at": "..."}

    Raises ToolError if the request is already finished (completed/failed/cancelled)
    or not found.
    """
    client = get_async_daz_client()
    try:
        return await client.cancel_request_detail(request_id)
    except daz_exc.ServerResponseError as exc:
        if exc.status_code == 404:
            raise ToolError(f"Request not found: {request_id}") from exc
        handle_dazpy_error(exc)
    except daz_exc.DazError as exc:
        handle_dazpy_error(exc)


@mcp.tool()
async def daz_list_requests(
    status_filter: str | None = None,
) -> dict[str, Any]:
    """List all tracked async requests and their current statuses.

    Args:
        status_filter: Optional filter — one of "queued", "running",
                       "completed", "failed", "cancelled". Returns all if omitted.

    Returns:
        {
            "requests": [
                {"request_id": "...", "status": "...", "progress": 0.0, "submitted_at": "..."},
                ...
            ],
            "total": 5,
            "queued": 2,
            "running": 1,
            "completed": 2,
            "failed": 0,
            "cancelled": 0
        }
    """
    client = get_async_daz_client()
    try:
        return await client.list_requests(status_filter)
    except daz_exc.DazError as exc:
        handle_dazpy_error(exc)


# ---------------------------------------------------------------------------
# Render quality preset
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_set_render_quality(preset: str) -> dict[str, Any]:
    """Set the Iray render quality preset.

    Adjusts Max Samples and Render Quality on the active renderer, trading
    speed for quality. Use "draft" for quick composition checks and "final"
    for production renders.

    Presets:
        draft   - Very fast (seconds–2 min). Low quality. For quick checks.
        preview - Fast (2–5 min). Moderate quality. For composition review.
        good    - Slow (10–20 min). Good quality. For client review.
        final   - Very slow (30 min–2 hr). Maximum quality. For final output.

    Args:
        preset: One of "draft", "preview", "good", "final".

    Returns:
        {
            "preset": "draft",
            "propertiesSet": [
                {"property": "Max Samples", "value": 100},
                {"property": "Render Quality", "value": 0.5}
            ],
            "note": "..."    # present only if some properties were not found
        }

    Example:
        # Quick test render
        daz_set_render_quality("draft")
        daz_render("/test.png")

        # Final quality async render
        daz_set_render_quality("final")
        req = await daz_render_async("/final.png")
        result = await daz_get_request_result(req["request_id"], wait=True)
    """
    _presets: dict[str, dict[str, float]] = {
        "draft":   {"maxSamples": 100,  "renderQuality": 0.5},
        "preview": {"maxSamples": 500,  "renderQuality": 0.75},
        "good":    {"maxSamples": 2000, "renderQuality": 0.9},
        "final":   {"maxSamples": 5000, "renderQuality": 1.0},
    }
    if preset not in _presets:
        valid = ", ".join(f'"{k}"' for k in _presets)
        raise ToolError(f"Unknown render quality preset: '{preset}'. Valid presets: {valid}")

    args = {"preset": preset, **_presets[preset]}
    return await _execute_by_id("vangard-set-render-quality", args)


# ---------------------------------------------------------------------------
# Poll helper (not an MCP tool — for use in Python scripts)
# ---------------------------------------------------------------------------

async def daz_wait_for_request(
    request_id: str,
    poll_interval_seconds: float = 5.0,
    timeout_seconds: float = 3600.0,
) -> dict[str, Any]:
    """Poll an async request until it completes (or times out).

    Polls daz_get_request_status() every poll_interval_seconds until the
    request reaches a terminal state, then returns the full result.

    Args:
        request_id: Request ID from an async submission tool.
        poll_interval_seconds: Seconds between status checks (default 5).
        timeout_seconds: Maximum total wait time (default 3600 = 1 hour).

    Returns:
        Full result dict from daz_get_request_result() on success.

    Raises:
        ToolError: If the request failed or was cancelled.
        asyncio.TimeoutError: If the timeout is exceeded.
    """
    import time
    deadline = time.monotonic() + timeout_seconds

    while True:
        status = await daz_get_request_status(request_id)
        state = status.get("status", "unknown")

        if state == "completed":
            return await daz_get_request_result(request_id, wait=False)
        if state == "failed":
            raise ToolError(f"Async request failed: {status.get('error', 'unknown error')}")
        if state == "cancelled":
            return status

        if time.monotonic() >= deadline:
            raise asyncio.TimeoutError(
                f"Async request {request_id!r} did not complete within {timeout_seconds}s"
            )

        await asyncio.sleep(poll_interval_seconds)


# ---------------------------------------------------------------------------
# Render output configuration
# ---------------------------------------------------------------------------

@mcp.tool()
async def daz_set_render_output(
    output_path: str | None = None,
    width: int | None = None,
    height: int | None = None,
) -> dict[str, Any]:
    """Configure render output path and/or image dimensions.

    At least one of ``output_path``, ``width``, or ``height`` must be provided.
    Unspecified parameters are left unchanged.

    Args:
        output_path: Absolute path for the rendered image file, including
                     extension (e.g. ``"C:/renders/hero_shot.png"``). DAZ Studio
                     determines the format from the extension.
        width: Render image width in pixels.
        height: Render image height in pixels.

    Returns:
        Dict with changed (the settings that were modified) and current
        (the full current render output configuration after changes).

    Examples:
        daz_set_render_output(output_path="C:/renders/scene01.png")
        daz_set_render_output(width=3840, height=2160)           # 4K
        daz_set_render_output("C:/out/final.png", 1920, 1080)   # 1080p with path

    Notes:
        - These settings persist in the DAZ Studio render options for the session.
        - Use daz_render or daz_render_async to trigger the render after setting up.
    """
    if output_path is None and width is None and height is None:
        raise ToolError(
            "At least one of output_path, width, or height must be provided."
        )
    return await _execute_by_id(
        "vangard-set-render-output",
        {"outputPath": output_path, "width": width, "height": height},
    )
