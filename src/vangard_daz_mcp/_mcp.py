"""Shared FastMCP instance, lifespan, and DazScriptServer execution helpers.

All tool modules import ``mcp`` from here to register ``@mcp.tool()`` functions
without creating circular imports with ``server.py``.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from ._client import (
    DAZ_API_TOKEN,
    BASE_URL,
    CONTENT_BROWSER_URL,
    DAZ_TIMEOUT,
    get_http_client,
    set_http_client,
    set_content_browser_client,
)
from ._errors import handle_network_error, check_response
from ._registry import _register_scripts


# ---------------------------------------------------------------------------
# Execute helpers — used by all tool modules
# ---------------------------------------------------------------------------

async def _execute_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """POST a prebuilt /execute payload to DazScriptServer; raise ToolError on failure.

    Returns the full response payload (success/result/output/error) — shared by
    _execute_raw() (inline script), daz_execute_file (script-on-disk, a different
    payload shape hitting the same /execute endpoint), and _execute() (which
    further unwraps just "result").
    """
    client = get_http_client()
    try:
        response = await client.post("/execute", json=payload)
        check_response(response)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        handle_network_error(exc)
    data = response.json()
    if not data.get("success", False):
        output_lines = data.get("output", [])
        error_msg = data.get("error") or "Script execution failed"
        detail = error_msg
        if output_lines:
            detail += "\n\nCaptured output:\n" + "\n".join(output_lines)
        raise ToolError(detail)
    return data


async def _execute_raw(script: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    """POST an inline DazScript to DazScriptServer; raise ToolError on failure.

    Returns the full response payload (success/result/output/error) — used by
    both _execute() (which unwraps just "result") and daz_execute (the public
    MCP tool, which returns the full diagnostic payload to the caller).
    """
    payload: dict[str, Any] = {"script": script}
    if args is not None:
        payload["args"] = args
    return await _execute_payload(payload)


async def _execute_async_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Submit a prebuilt payload to ``/execute/async`` and return its job record."""
    client = get_http_client()
    try:
        response = await client.post("/execute/async", json=payload)
        check_response(response)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        handle_network_error(exc)
    return response.json()


async def _execute(script: str, args: dict[str, Any] | None = None) -> Any:
    """POST an inline DazScript to DazScriptServer; raise ToolError on failure."""
    data = await _execute_raw(script, args)
    return data.get("result")


async def _execute_by_id(script_id: str, args: dict[str, Any] | None = None) -> Any:
    """Call a registered script by ID; re-registers once on 404 (DAZ Studio restart)."""
    client = get_http_client()
    payload: dict[str, Any] = {}
    if args is not None:
        payload["args"] = args
    try:
        response = await client.post(f"/scripts/{script_id}/execute", json=payload)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        handle_network_error(exc)
    if response.status_code == 404:
        await _register_scripts(client)
        try:
            response = await client.post(f"/scripts/{script_id}/execute", json=payload)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
            handle_network_error(exc)
    check_response(response)
    data = response.json()
    if not data.get("success", False):
        output_lines = data.get("output", [])
        error_msg = data.get("error") or "Script execution failed"
        detail = error_msg
        if output_lines:
            detail += "\n\nCaptured output:\n" + "\n".join(output_lines)
        raise ToolError(detail)
    return data.get("result")


async def _execute_by_id_async(
    script_id: str,
    args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Submit a registered script for async execution; returns immediately with request_id."""
    client = get_http_client()
    payload: dict[str, Any] = {}
    if args is not None:
        payload["args"] = args
    try:
        response = await client.post(f"/scripts/{script_id}/async", json=payload)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        handle_network_error(exc)
    if response.status_code == 404:
        await _register_scripts(client)
        try:
            response = await client.post(f"/scripts/{script_id}/async", json=payload)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
            handle_network_error(exc)
    check_response(response)
    return response.json()


async def _execute_render(params: dict[str, Any]) -> dict[str, Any]:
    """Submit a render via POST /render."""
    client = get_http_client()
    try:
        response = await client.post("/render", json=params)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        handle_network_error(exc)
    check_response(response)
    return response.json()


async def _execute_render_batch(body: dict[str, Any]) -> dict[str, Any]:
    """Submit a render batch via POST /render/batch."""
    client = get_http_client()
    try:
        response = await client.post("/render/batch", json=body)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
        handle_network_error(exc)
    check_response(response)
    return response.json()


# ---------------------------------------------------------------------------
# Lifespan and shared FastMCP instance
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(server: FastMCP):  # pylint: disable=unused-argument
    # `server` is required by FastMCP's lifespan callback signature.
    headers = {"X-API-Token": DAZ_API_TOKEN} if DAZ_API_TOKEN else {}
    async with httpx.AsyncClient(
        base_url=BASE_URL, timeout=DAZ_TIMEOUT, headers=headers
    ) as client:
        set_http_client(client)
        await _register_scripts(client)
        async with httpx.AsyncClient(
            base_url=CONTENT_BROWSER_URL, timeout=DAZ_TIMEOUT
        ) as cb_client:
            set_content_browser_client(cb_client)
            yield
        set_content_browser_client(None)
    set_http_client(None)


mcp = FastMCP("vangard-daz-mcp", lifespan=_lifespan)
