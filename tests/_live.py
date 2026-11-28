"""Opt-in gate for tests that talk to a real DAZ Studio.

Live tests render, add and delete nodes, and change the user's scene, so they
never run just because Studio happens to answer. Set ``DAZ_LIVE_TESTS=1`` to
run them; they then use ``DAZ_HOST``/``DAZ_PORT`` like the server does.
"""
from __future__ import annotations

import os
import socket

import pytest

from daz_mcp_server._client import DAZ_HOST, DAZ_PORT

LIVE_ENV = "DAZ_LIVE_TESTS"
BASE_URL = f"http://{DAZ_HOST}:{DAZ_PORT}"
NOT_ENABLED_REASON = (
    f"live DAZ Studio test: set {LIVE_ENV}=1 to run (it changes the open scene)"
)


def live_enabled() -> bool:
    """True only when the user opted in with DAZ_LIVE_TESTS=1."""
    return os.environ.get(LIVE_ENV, "").strip() == "1"


def daz_available() -> bool:
    """True if DazScriptServer accepts connections at DAZ_HOST:DAZ_PORT."""
    try:
        with socket.create_connection((DAZ_HOST, DAZ_PORT), timeout=2):
            return True
    except OSError:
        return False


def require_live() -> None:
    """Skip unless live tests are enabled and Studio is reachable."""
    if not live_enabled():
        pytest.skip(NOT_ENABLED_REASON)
    if not daz_available():
        pytest.skip(f"DAZ Studio not reachable at {BASE_URL}")
