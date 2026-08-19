"""Small task-oriented facade for ordinary model-driven DAZ work.

The detailed tools in the sibling modules remain the expert API.  This module
provides the stable workflow boundary advertised by the default MCP profile.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastmcp.exceptions import ToolError
from fastmcp.utilities.types import File, Image

from .._mcp import mcp
from .render import (
    daz_cancel_request,
    daz_get_request_result,
    daz_get_request_status,
)
from .scene import daz_scene_info
from .utility import daz_execute_file_async, daz_script_help


_DEFAULT_TAG = {"default"}
_IMAGE_SUFFIXES = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"}


@mcp.tool(tags=_DEFAULT_TAG)
async def daz_inspect_scene() -> dict[str, Any]:
    """Inspect the open scene before choosing or running a recipe.

    Returns the scene file, selected node, figures, cameras, lights, and node
    count.  Use the ``daz://help/{topic}`` resource for static DazScript help.
    """
    return await daz_scene_info()


@mcp.tool(tags=_DEFAULT_TAG)
async def daz_submit_job(
    script_file: str,
    args: dict[str, Any] | None = None,
    report_file: str | None = None,
) -> dict[str, Any]:
    """Submit a file-backed DazScript job and return immediately.

    This is the general escape hatch for work that is not expressed as a
    materializer recipe.  Prefer a unique ``report_file`` so observation can
    expose structured progress, logs, and an output manifest.
    """
    return await daz_execute_file_async(script_file, args, report_file)


@mcp.tool(tags=_DEFAULT_TAG)
async def daz_observe_job(
    request_id: str,
    action: Literal["status", "result", "cancel"] = "status",
    wait: bool = True,
    timeout_seconds: int = 3600,
) -> dict[str, Any]:
    """Observe, collect, or cancel one asynchronous DAZ job.

    ``status`` is non-blocking and includes live structured observations.
    ``result`` optionally waits for the terminal response. ``cancel`` stops a
    queued job or requests cancellation of running work.
    """
    if action == "status":
        return await daz_get_request_status(request_id)
    if action == "result":
        return await daz_get_request_result(request_id, wait, timeout_seconds)
    return await daz_cancel_request(request_id)


@mcp.tool(tags=_DEFAULT_TAG)
async def daz_materialize_recipe(
    recipe_file: str,
    parameters: dict[str, Any] | None = None,
    report_file: str | None = None,
) -> dict[str, Any]:
    """Run a file-backed scene recipe through the asynchronous job boundary.

    A recipe owns scene construction and its immutable run manifest; this tool
    only supplies parameters and queues it.  The recipe must be a ``.dsa`` or
    ``.ds`` file. Poll the returned request with ``daz_observe_job``.
    """
    suffix = Path(recipe_file).suffix.lower()
    if suffix not in {".ds", ".dsa"}:
        raise ToolError("A materializer recipe must be a .dsa or .ds file")
    return await daz_execute_file_async(recipe_file, parameters, report_file)


@mcp.tool(tags=_DEFAULT_TAG)
async def daz_fetch_artifact(
    request_id: str,
    artifact: int | str = 0,
) -> Any:
    """Fetch one file declared by a job's structured output manifest.

    Select by zero-based manifest index, exact path, or output label. Images
    are returned as MCP image content; other files as embedded resources. The
    MCP process must share the DAZ host's filesystem. Arbitrary paths are not
    accepted: the file must have been declared by this job.
    """
    status = await daz_get_request_status(request_id)
    observation = status.get("observation") or {}
    manifest = observation.get("output_manifest") or {}
    outputs = manifest.get("outputs") or []
    if not outputs:
        raise ToolError(f"Job {request_id} has not declared any artifacts")

    selected: dict[str, Any] | None = None
    if isinstance(artifact, int):
        if artifact < 0 or artifact >= len(outputs):
            raise ToolError(
                f"Artifact index {artifact} is outside the manifest range "
                f"0..{len(outputs) - 1}"
            )
        selected = outputs[artifact]
    else:
        selected = next(
            (
                item
                for item in outputs
                if item.get("path") == artifact or item.get("label") == artifact
            ),
            None,
        )
        if selected is None:
            raise ToolError(f"Artifact is not in job {request_id}'s manifest: {artifact}")

    path_text = selected.get("path")
    if not isinstance(path_text, str) or not path_text:
        raise ToolError("The selected artifact has no usable path")
    path = Path(path_text)
    if not path.is_file():
        raise ToolError(
            "The artifact is not readable from the MCP host. DAZ and the MCP "
            f"must share a filesystem: {path_text}"
        )
    if path.suffix.lower() in _IMAGE_SUFFIXES or selected.get("kind") == "image":
        return Image(path=path)
    return File(path=path)


@mcp.resource("daz://help/{topic}")
async def daz_help_resource(topic: str) -> str:
    """Read static DazScript guidance without adding another visible tool."""
    return await daz_script_help(topic)


@mcp.resource("daz://profiles")
def daz_profiles_resource() -> str:
    """Describe the compact and expert MCP profiles."""
    return (
        "The default compact profile exposes five workflow tools: inspect scene, "
        "submit job, observe job, materialize recipe, and fetch artifact. Set "
        "DAZ_MCP_PROFILE=expert in the MCP server environment to expose the full "
        "low-level DAZ operation catalogue as well."
    )
