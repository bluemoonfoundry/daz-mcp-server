"""What gets published: the sdist and wheel built from this repo."""

import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "src" / "daz_mcp_server"


def build_dists(out_dir: Path) -> tuple[Path, Path]:
    """Build the sdist and wheel into *out_dir*; return (sdist, wheel)."""
    subprocess.run(
        ["uv", "build", "--out-dir", str(out_dir)],
        cwd=ROOT, check=True, capture_output=True,
    )
    return next(out_dir.glob("*.tar.gz")), next(out_dir.glob("*.whl"))


@pytest.fixture(scope="module")
def dists(tmp_path_factory):
    return build_dists(tmp_path_factory.mktemp("dist"))


@pytest.fixture(scope="module")
def sdist_names(dists):
    with tarfile.open(dists[0]) as tf:
        return tf.getnames()


@pytest.fixture(scope="module")
def wheel_names(dists):
    with zipfile.ZipFile(dists[1]) as zf:
        return zf.namelist()


def test_sdist_excludes_repo_internals(sdist_names):
    banned = ("/.beads/", "/.agents/", "/.claude/", "/.github/", "/.worktrees/", "/.venv/",
              "/docs/superpowers/")
    leaked = [n for n in sdist_names if any(b in n + "/" for b in banned)]
    assert leaked == []
    root_level = [n.split("/", 1)[1] for n in sdist_names if n.count("/") == 1]
    assert not [n for n in root_level if n.startswith("_test_")]


def test_wheel_has_data_files(wheel_names):
    assert "daz_mcp_server/dazscript_docs.json" in wheel_names
    assert "daz_mcp_server/genesis_bones.json" in wheel_names


def test_no_personal_paths_in_source():
    hits = [
        str(p.relative_to(ROOT))
        for p in PKG.rglob("*")
        if p.is_file() and p.suffix in {".py", ".md", ".json"}
        and any(s in p.read_text(encoding="utf-8", errors="ignore") for s in ("OpenCode",))
    ]
    assert hits == []


def test_wheel_has_guides(wheel_names):
    from daz_mcp_server._guides import GUIDE_NAMES

    for name in GUIDE_NAMES:
        assert f"daz_mcp_server/guides/{name}.md" in wheel_names, name
