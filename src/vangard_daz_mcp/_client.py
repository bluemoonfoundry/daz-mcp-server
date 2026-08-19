"""Singleton accessors for dazpy clients and the separate content browser."""
from __future__ import annotations

import asyncio
import os
from typing import Callable, TypeVar

import httpx
from dazpy import DazClient, DazScene
from dazpy.aio import AsyncDazClient

_T = TypeVar("_T")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DAZ_HOST: str = os.environ.get("DAZ_HOST", "localhost")
DAZ_PORT: int = int(os.environ.get("DAZ_PORT", "18811"))
DAZ_TIMEOUT: float = float(os.environ.get("DAZ_TIMEOUT", "30.0"))

CONTENT_BROWSER_URL: str = os.environ.get("DAZ_CONTENT_BROWSER_URL", "http://localhost:8080")

TOKEN_FILE: str = os.path.join(os.path.expanduser("~"), ".daz3d", "dazscriptserver_token.txt")


def _load_token_from_file() -> str:
    try:
        with open(TOKEN_FILE) as f:
            return f.read().strip()
    except OSError:
        return ""


DAZ_API_TOKEN: str = os.environ.get("DAZ_API_TOKEN") or _load_token_from_file()

# ---------------------------------------------------------------------------
# Shared protocol/content clients — set/cleared by the server lifespan
# ---------------------------------------------------------------------------

_async_daz_client: AsyncDazClient | None = None
_content_browser_client: httpx.AsyncClient | None = None


def set_async_daz_client(client: AsyncDazClient | None) -> None:
    """Set or clear the sole async Daz Script Server protocol client."""
    global _async_daz_client
    _async_daz_client = client


def set_content_browser_client(client: httpx.AsyncClient | None) -> None:
    """Set (or clear) the shared content-browser httpx client."""
    global _content_browser_client
    _content_browser_client = client


def get_async_daz_client() -> AsyncDazClient:
    """Return the shared async dazpy client once lifespan has initialized it."""
    if _async_daz_client is None:
        raise RuntimeError("AsyncDazClient not initialised — server lifespan not running")
    return _async_daz_client


def get_content_browser_client() -> httpx.AsyncClient:
    """Return the shared content-browser httpx client, once the server lifespan has set it."""
    if _content_browser_client is None:
        raise RuntimeError("Content browser client not initialised — server lifespan not running")
    return _content_browser_client


# ---------------------------------------------------------------------------
# dazpy singletons — created lazily on first access
# ---------------------------------------------------------------------------

_daz_client: DazClient | None = None
_daz_scene: DazScene | None = None


def get_daz_client() -> DazClient:
    """Return the singleton DazClient, creating it on first access."""
    global _daz_client
    if _daz_client is None:
        _daz_client = DazClient(
            host=DAZ_HOST,
            port=DAZ_PORT,
            token=DAZ_API_TOKEN or None,
            timeout=DAZ_TIMEOUT,
        )
    return _daz_client


def get_scene() -> DazScene:
    """Return the singleton DazScene, creating it on first access."""
    global _daz_scene
    if _daz_scene is None:
        _daz_scene = DazScene(get_daz_client())
    return _daz_scene


def set_scene(scene: DazScene | None) -> None:
    """Override the DazScene singleton — for injecting a test double.

    Without this, tests that mock only the httpx client (e.g. via respx) can
    silently fall through to a real DazScene/DazClient connection for any tool
    that uses get_scene()/run_dazpy(), reaching a live DAZ Studio instance.
    """
    global _daz_scene
    _daz_scene = scene


async def run_dazpy(fn: Callable[[], _T]) -> _T:
    """Run a synchronous dazpy call in a thread pool to avoid blocking the event loop."""
    return await asyncio.to_thread(fn)
