"""Shared pytest fixtures for DAZ Studio integration tests.

All integration test files (except test_phase5_integration.py, which manages
its own fixtures) import from here via pytest's automatic conftest discovery.

Usage
-----
Tests in any new test file that accept `live_client`, `figure_label`, or
`second_figure_label` as arguments will receive these fixtures automatically.
Tests that need a temporary camera or light should use `temp_camera` /
`temp_light`, which create the object and clean it up after the test.

Skip behaviour
--------------
- If DAZ Studio is not reachable, every test that uses `live_client` is
  automatically skipped.
- If no figure is loaded in the scene, `figure_label` skips the test.
- If fewer than 2 figures are loaded, `second_figure_label` skips the test.
"""

from __future__ import annotations

import os
import socket

import httpx
import pytest
import pytest_asyncio

import vangard_daz_mcp.server as server_module
from vangard_daz_mcp.server import (
    _register_scripts,
    daz_create_camera,
    daz_create_light,
    daz_delete_node,
    daz_scene_info,
)

BASE_URL = "http://localhost:18811"

# Module-level cache: avoids re-registering scripts and re-querying the scene
# on every test in the same process run.
_cache: dict = {}


def _daz_available() -> bool:
    """Synchronous probe — True if DazScriptServer is reachable."""
    try:
        with socket.create_connection(("localhost", 18811), timeout=2):
            return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Core connectivity fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def live_client():
    """Real AsyncClient wired into the server module.

    Skips automatically if DAZ Studio is not reachable.
    Registers all scripts once per process (cached).
    """
    if not _daz_available():
        pytest.skip(f"DAZ Studio not reachable at {BASE_URL}")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        server_module._http_client = client
        if not _cache.get("scripts_registered"):
            await _register_scripts(client)
            _cache["scripts_registered"] = True
        yield client

    server_module._http_client = None


# ---------------------------------------------------------------------------
# Scene-aware fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def figure_label(live_client):
    """Label of the first root-level figure in the scene, or skip.

    Override with env var DAZ_FIGURE_1=<label> to pin a specific character.
    """
    if "figure_label" not in _cache:
        override = os.environ.get("DAZ_FIGURE_1")
        if override:
            _cache["figure_label"] = override
        else:
            scene = await daz_scene_info()
            figures = scene.get("figures", [])
            if not figures:
                pytest.skip(
                    "No figure found in scene — load a Genesis figure to run character tests"
                )
            _cache["figure_label"] = figures[0]["label"]
    return _cache["figure_label"]


@pytest_asyncio.fixture()
async def second_figure_label(live_client):
    """Label of the second root-level figure in the scene, or skip if fewer than 2.

    Override with env var DAZ_FIGURE_2=<label> to pin a specific character.
    """
    if "second_figure_label" not in _cache:
        override = os.environ.get("DAZ_FIGURE_2")
        if override:
            _cache["second_figure_label"] = override
        else:
            scene = await daz_scene_info()
            figures = scene.get("figures", [])
            if len(figures) < 2:
                pytest.skip(
                    "Need at least 2 figures in scene for multi-character tests"
                )
            _cache["second_figure_label"] = figures[1]["label"]
    return _cache["second_figure_label"]


# ---------------------------------------------------------------------------
# Ephemeral object fixtures — create before test, delete after
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def temp_camera(live_client):
    """Create a test camera before the test, delete it after."""
    result = await daz_create_camera(
        label="TestCamera_Temp", x=0.0, y=150.0, z=300.0
    )
    label = result["label"]
    yield label
    try:
        await daz_delete_node(label)
    except Exception:
        pass  # already deleted by test or cleanup failed


@pytest_asyncio.fixture()
async def temp_spot_light(live_client):
    """Create a test spot light before the test, delete it after."""
    result = await daz_create_light(
        light_type="spot", label="TestLight_Temp",
        x=0.0, y=300.0, z=200.0, flux=5000.0,
    )
    label = result["label"]
    yield label
    try:
        await daz_delete_node(label)
    except Exception:
        pass
