"""Print the release notes' Compatibility section.

The dazpy floor comes from pyproject.toml; the minimum plugin version comes from
the *installed* dazpy's ``MIN_SERVER_VERSION``. The release job installs exactly
``dazpy==<floor>`` before running this, so the claim holds for the oldest dazpy a
user could get.
"""
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import dazpy

ROOT = Path(__file__).resolve().parent.parent


def dazpy_floor() -> str:
    """The X in pyproject.toml's ``dazpy>=X`` requirement."""
    deps = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["dependencies"]
    for dep in deps:
        if dep.replace(" ", "").startswith("dazpy>="):
            return dep.replace(" ", "").split(">=", 1)[1].split(",", 1)[0]
    raise SystemExit("pyproject.toml has no dazpy>= requirement")


def main() -> int:
    print("### Compatibility")
    print(f"- dazpy >= {dazpy_floor()}")
    print(f"- Daz Studio plugin (DazScriptServer) >= {dazpy.MIN_SERVER_VERSION}")
    print("- Plugin downloads: https://github.com/bluemoonfoundry/daz-script-server/releases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
