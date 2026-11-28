"""Select the model-facing MCP component profile."""
from __future__ import annotations

import os

from fastmcp import FastMCP


PROFILE_ENV = "DAZ_MCP_PROFILE"
DEFAULT_PROFILE = "compact"
VALID_PROFILES = {"compact", "desktop", "expert"}

# Tags that make a tool visible in each restricted profile. ``desktop`` is
# additive: every compact tool plus direct script authoring (inline execution,
# inline jobs, writing .dsa files on the DAZ Studio machine) and read-only scene
# tools, for clients such as Claude Desktop that cannot write files on the DAZ
# host themselves.
PROFILE_TAGS = {
    "compact": {"default"},
    "desktop": {"default", "desktop"},
}


def configure_profile(server: FastMCP) -> str:
    """Apply the configured tool visibility profile and return its name."""
    profile = os.getenv(PROFILE_ENV, DEFAULT_PROFILE).strip().lower()
    if profile not in VALID_PROFILES:
        choices = ", ".join(sorted(VALID_PROFILES))
        raise RuntimeError(f"{PROFILE_ENV} must be one of: {choices}")
    if profile in PROFILE_TAGS:
        server.enable(tags=PROFILE_TAGS[profile], components={"tool"}, only=True)
        # ``only=True`` begins with a global deny transform. Static guidance is
        # intentionally available in both profiles and does not consume tool
        # selection context, so re-enable resources after the tool allowlist.
        server.enable(components={"resource", "template"})
    return profile
