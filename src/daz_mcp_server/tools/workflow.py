"""Small task-oriented facade for ordinary model-driven DAZ work.

The detailed tools in the sibling modules remain the expert API.  This module
provides the stable workflow boundary advertised by the default MCP profile.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

import dazpy.exceptions as daz_exc
from fastmcp.exceptions import ToolError
from fastmcp.utilities.types import File, Image

from .. import _compat
from .._client import get_async_daz_client
from .._errors import handle_dazpy_error
from .._guides import guide_index, read_guide
from .._mcp import _execute_raw, mcp, with_args_variable
from .render import (
    daz_cancel_request,
    daz_get_request_result,
    daz_get_request_status,
)
from .scene import daz_scene_info
from .utility import daz_execute_file_async, daz_script_help


_DEFAULT_TAG = {"default"}
_DESKTOP_TAG = {"desktop"}
_IMAGE_SUFFIXES = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"}

# A script file name: letters, digits, "_" and "-", starting with a letter or
# digit, optionally ending in .dsa / .ds. No path separators, so a name can
# never leave the scripts folder.
_SCRIPT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}(\.dsa|\.ds)?$", re.IGNORECASE)

# Runs inside DAZ Studio: writes args.content to <Studio temp>/daz-mcp-scripts/
# <args.file_name>. The content arrives as a job argument, never spliced into
# this source, so any script text is written byte for byte.
_WRITE_SCRIPT_JS = """(function () {
    var args = getArguments()[0];
    var base = App.getTempPath();
    var dir = base + "/daz-mcp-scripts";
    if (!new DzDir(dir).exists() && !new DzDir(base).mkpath("daz-mcp-scripts"))
        return {error: "cannot create the scripts folder " + dir};
    var path = dir + "/" + args.file_name;
    var file = new DzFile(path);
    if (!file.open(DzFile.WriteOnly | DzFile.Truncate))
        return {error: "cannot open " + path + " for writing"};
    file.write(args.content);
    file.close();
    return {path: path, bytes: new DzFileInfo(path).size()};
})()"""


@mcp.tool(tags=_DEFAULT_TAG)
async def daz_inspect_scene() -> dict[str, Any]:
    """Inspect the open scene before choosing or running a script job.

    Returns the scene file, selected node, figures, cameras, lights, and node
    count.  Use the ``daz://help/{topic}`` resource for static DazScript help.
    When the Daz Studio plugin is too old for this server, the result also has
    ``plugin_compatibility`` with upgrade advice.
    """
    info = await daz_scene_info()
    if _compat.incompatible_note() is not None and isinstance(info, dict):
        info = {**info, "plugin_compatibility": _compat.summary()}
    return info


@mcp.tool(tags=_DEFAULT_TAG)
async def daz_submit_job(
    script_file: str,
    args: dict[str, Any] | None = None,
    report_file: str | None = None,
) -> dict[str, Any]:
    """Submit a file-backed DazScript job and return immediately.

    This is the general escape hatch for file-backed work.  Prefer a unique ``report_file`` so observation can
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
async def daz_run_script_job(
    script_file: str,
    parameters: dict[str, Any] | None = None,
    report_file: str | None = None,
) -> dict[str, Any]:
    """Run a .dsa/.ds script file through the asynchronous job boundary.

    The script owns its own scene construction and run manifest; this tool
    only supplies parameters and queues it. The file must be a ``.dsa`` or
    ``.ds`` file. Poll the returned request with ``daz_observe_job``.
    """
    suffix = Path(script_file).suffix.lower()
    if suffix not in {".ds", ".dsa"}:
        raise ToolError("A script job file must be a .dsa or .ds file")
    return await daz_execute_file_async(script_file, parameters, report_file)


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


@mcp.tool(tags=_DESKTOP_TAG)
async def daz_submit_script(
    script: str,
    parameters: dict[str, Any] | None = None,
    report_file: str | None = None,
) -> dict[str, Any]:
    """Queue inline DazScript as a background job and return immediately.

    Use this for long work (renders, simulations, sweeps) when you have the
    script text but no file on the DAZ Studio machine. ``parameters`` is
    available in the script as ``args`` (and ``getArguments()[0]``). A
    top-level ``return`` is a syntax error: wrap the script in an IIFE or end
    it with an expression, whose value becomes the job's result. Poll the
    returned request with ``daz_observe_job``. For short calls whose result you
    want back at once, use ``daz_execute``. A script that needs
    ``getScriptFileName()`` or relative ``include()`` must be saved first with
    ``daz_write_script`` and run with ``daz_run_script_job``.
    """
    if not script.strip():
        raise ToolError("The script is empty")
    try:
        request_id = await get_async_daz_client().execute_async_submit(
            with_args_variable(script), parameters, report_file=report_file
        )
    except daz_exc.DazError as exc:
        handle_dazpy_error(exc)
    return {"request_id": request_id, "status": "queued"}


@mcp.tool(tags=_DESKTOP_TAG)
async def daz_write_script(name: str, script: str) -> dict[str, Any]:
    """Save DazScript as a file on the DAZ Studio machine and return its path.

    DAZ Studio itself writes the file, into ``daz-mcp-scripts`` under its temp
    folder, so this works even when you cannot write files on that machine
    (for example from Claude Desktop). Pass the returned ``path`` to
    ``daz_run_script_job`` or ``daz_submit_job``. ``name`` is a plain file name
    (letters, digits, ``_`` and ``-``, up to 64 characters); ``.dsa`` is added
    unless it ends in ``.dsa`` or ``.ds``. Writing the same name again replaces
    the file. The file is saved exactly as given: inside it, read job
    parameters with ``getArguments()[0]`` (a file has no ``args`` variable),
    and end with an expression rather than a top-level ``return``.
    """
    if not _SCRIPT_NAME.match(name or ""):
        raise ToolError(
            "The script name must be 1-64 letters, digits, '_' or '-' (starting "
            "with a letter or digit), optionally ending in .dsa or .ds; got "
            f"{name!r}"
        )
    file_name = name if name.lower().endswith((".dsa", ".ds")) else f"{name}.dsa"
    payload = await _execute_raw(_WRITE_SCRIPT_JS, {"file_name": file_name, "content": script})
    result = payload.get("result")
    if not payload.get("success") or not isinstance(result, dict):
        raise ToolError(f"DAZ Studio could not write {file_name}: {payload.get('error')}")
    if result.get("error"):
        raise ToolError(f"DAZ Studio could not write {file_name}: {result['error']}")
    return {"path": result.get("path"), "bytes": result.get("bytes")}


@mcp.resource("daz://help/{topic}")
async def daz_help_resource(topic: str) -> str:
    """Read static DazScript guidance without adding another visible tool."""
    return await daz_script_help(topic)


@mcp.resource("daz://guides")
def daz_guides_resource() -> str:
    """List the bundled agent guides (read one at daz://guide/{name})."""
    return guide_index()


@mcp.resource("daz://guide/{name}")
def daz_guide_resource(name: str) -> str:
    """Read one bundled agent guide: actors, cinema, daz_studio, dazscript, recipe, scene."""
    return read_guide(name)


@mcp.resource("daz://profiles")
def daz_profiles_resource() -> str:
    """Describe the compact, desktop and expert MCP profiles."""
    return (
        "The default compact profile exposes ten tools. Five job tools: inspect "
        "scene, submit job, observe job, run script job, and fetch artifact. Five "
        "scene recipe tools: recipe validate, plan, apply, observe, and render "
        "(the declarative way to build a scene; see daz://guide/recipe and the "
        "daz://recipe/schema resource).\n\n"
        "Set DAZ_MCP_PROFILE=desktop for clients that cannot write files on the "
        "DAZ Studio machine, such as Claude Desktop. It keeps every compact tool "
        "and adds direct scripting: `daz_execute` runs DazScript and returns its "
        "result, `daz_submit_script` queues inline DazScript as a job, and "
        "`daz_write_script` has DAZ Studio save a .dsa file and returns its path "
        "for `daz_run_script_job`. It also adds `daz_script_help`, "
        "`daz_validate_script`, `daz_explain_last_error`, `daz_status` and "
        "read-only scene tools (nodes, selection, cameras, lights, render "
        "settings).\n\n"
        "Set DAZ_MCP_PROFILE=expert to expose the full low-level DAZ operation "
        "catalogue as well."
    )
