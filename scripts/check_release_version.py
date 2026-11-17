"""Fail unless a release tag matches the pyproject.toml version.

Usage: python scripts/check_release_version.py --tag v0.8.0
"""
from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="release tag, e.g. v0.8.0")
    tag = parser.parse_args().tag
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    tagged = tag[1:] if tag.startswith("v") else tag
    if tagged != version:
        print(f"Tag {tag} ({tagged}) does not match pyproject.toml version {version}")
        return 1
    print(f"Tag {tag} matches version {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
