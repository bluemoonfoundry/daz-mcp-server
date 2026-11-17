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


def _ancestors(jobs: dict, name: str) -> set:
    needs = jobs[name].get("needs", [])
    needs = [needs] if isinstance(needs, str) else needs
    out = set(needs)
    for n in needs:
        out |= _ancestors(jobs, n)
    return out


def test_release_notes_are_built_before_publishing():
    # A missing CHANGELOG section must stop the release before PyPI, which
    # can't be undone, not after it.
    import yaml

    jobs = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8"))["jobs"]
    makers = [name for name, job in jobs.items()
              if any("notes.md" in (step.get("run") or "") and "CHANGELOG.md" in (step.get("run") or "")
                     for step in job.get("steps", []))]
    assert makers, "no job extracts the CHANGELOG section into notes.md"
    assert all(m in _ancestors(jobs, "publish-pypi") for m in makers), makers
