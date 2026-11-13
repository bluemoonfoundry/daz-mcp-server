"""Shared FastMCP instance, lifespan, and DazScriptServer execution helpers.

All tool modules import ``mcp`` from here to register ``@mcp.tool()`` functions
without creating circular imports with ``server.py``.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

import httpx
from dazpy.aio import AsyncDazClient
import dazpy.exceptions as daz_exc
from fastmcp import FastMCP

from ._client import (
    DAZ_API_TOKEN,
    CONTENT_BROWSER_URL,
    DAZ_HOST,
    DAZ_PORT,
    DAZ_TIMEOUT,
    get_async_daz_client,
    set_async_daz_client,
    set_content_browser_client,
)
from ._errors import handle_dazpy_error
from ._registry import _register_scripts


# ---------------------------------------------------------------------------
# Execute helpers — used by all tool modules
# ---------------------------------------------------------------------------

def _execution_payload(result: Any) -> dict[str, Any]:
    """Preserve the public diagnostic shape for any dazpy execution result."""
    return {
        "success": result.success,
        "result": result.value,
        "output": result.output,
        "error": result.error or None,
        "request_id": result.request_id,
        "duration_ms": result.duration_ms,
    }


async def _execute_raw(script: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute inline source through dazpy and preserve the diagnostic shape."""
    try:
        result = await get_async_daz_client().execute(script, args)
    except daz_exc.DazError as exc:
        handle_dazpy_error(exc)
    return _execution_payload(result)


async def _execute(script: str, args: dict[str, Any] | None = None) -> Any:
    """Execute inline DazScript and unwrap its result value."""
    data = await _execute_raw(script, args)
    return data.get("result")


async def _execute_by_id(script_id: str, args: dict[str, Any] | None = None) -> Any:
    """Call a registered script by ID; re-registers once on 404 (DAZ Studio restart)."""
    client = get_async_daz_client()
    try:
        result = await client.execute_registered(script_id, args)
    except daz_exc.ServerResponseError as exc:
        if exc.status_code != 404:
            handle_dazpy_error(exc)
        await _register_scripts(client)
        try:
            result = await client.execute_registered(script_id, args)
        except daz_exc.DazError as retry_exc:
            handle_dazpy_error(retry_exc)
    except daz_exc.DazError as exc:
        handle_dazpy_error(exc)
    return result.value


async def _execute_by_id_async(
    script_id: str,
    args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Submit a registered script for async execution; returns immediately with request_id."""
    client = get_async_daz_client()
    try:
        request_id = await client.execute_registered_async_submit(script_id, args)
    except daz_exc.ServerResponseError as exc:
        if exc.status_code != 404:
            handle_dazpy_error(exc)
        await _register_scripts(client)
        try:
            request_id = await client.execute_registered_async_submit(script_id, args)
        except daz_exc.DazError as retry_exc:
            handle_dazpy_error(retry_exc)
    except daz_exc.DazError as exc:
        handle_dazpy_error(exc)
    return {"request_id": request_id, "status": "queued"}


async def _execute_render(params: dict[str, Any]) -> dict[str, Any]:
    """Submit a render through dazpy's typed protocol surface."""
    try:
        return await get_async_daz_client().render_submit(
            params["output_path"],
            width=params.get("width", 0),
            height=params.get("height", 0),
            camera=params.get("camera", ""),
            engine=params.get("engine", ""),
            iray_samples=params.get("iray_samples", 0),
        )
    except daz_exc.DazError as exc:
        handle_dazpy_error(exc)


async def _execute_render_batch(body: dict[str, Any]) -> dict[str, Any]:
    """Submit a render batch through dazpy's typed protocol surface."""
    try:
        return await get_async_daz_client().render_batch_submit(
            body["variants"], body.get("base")
        )
    except daz_exc.DazError as exc:
        handle_dazpy_error(exc)


# ---------------------------------------------------------------------------
# Lifespan and shared FastMCP instance
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(server: FastMCP):  # pylint: disable=unused-argument
    # `server` is required by FastMCP's lifespan callback signature.
    async with AsyncDazClient(
        host=DAZ_HOST, port=DAZ_PORT, token=DAZ_API_TOKEN, timeout=DAZ_TIMEOUT
    ) as client:
        set_async_daz_client(client)
        await _register_scripts(client)
        async with httpx.AsyncClient(
            base_url=CONTENT_BROWSER_URL, timeout=DAZ_TIMEOUT
        ) as cb_client:
            set_content_browser_client(cb_client)
            yield
        set_content_browser_client(None)
    set_async_daz_client(None)


mcp = FastMCP("vangard-daz-mcp", lifespan=_lifespan)
