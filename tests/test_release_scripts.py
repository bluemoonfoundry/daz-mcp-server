"""Release helper scripts used by .github/workflows/release.yml."""

import subprocess
import sys
import tomllib
from pathlib import Path

import dazpy

ROOT = Path(__file__).resolve().parent.parent
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]


def _run(*args):
    return subprocess.run(
        [sys.executable, *args], cwd=ROOT, capture_output=True, text=True, check=False
    )


def test_tag_matches():
    assert _run("scripts/check_release_version.py", "--tag", f"v{VERSION}").returncode == 0


def test_tag_mismatch_fails():
    result = _run("scripts/check_release_version.py", "--tag", "v9.9.9")
    assert result.returncode != 0
    assert "9.9.9" in result.stdout and VERSION in result.stdout


def test_compat_block():
    result = _run("scripts/compat_block.py")
    assert result.returncode == 0, result.stderr
    assert "dazpy >= 2.13.0" in result.stdout
    assert f"plugin (DazScriptServer) >= {dazpy.MIN_SERVER_VERSION}" in result.stdout
    assert "daz-script-server/releases" in result.stdout
