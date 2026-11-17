"""Agent guides bundled with the package (``guides/*.md``).

Served to the AI as the ``daz://guides`` / ``daz://guide/{name}`` resources and
through ``daz_script_help("guide:<name>")`` for clients that don't surface
resources.
"""
from __future__ import annotations

from importlib.resources import files

GUIDE_NAMES: tuple[str, ...] = ("actors", "cinema", "daz_studio", "dazscript", "recipe", "scene")


def read_guide(name: str) -> str:
    """Return the text of guide *name*; ``KeyError`` for an unknown name."""
    if name not in GUIDE_NAMES:
        raise KeyError(name)
    return files(__package__).joinpath("guides", f"{name}.md").read_text(encoding="utf-8")


def _title(name: str) -> str:
    for line in read_guide(name).splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return name


def guide_index() -> str:
    """One line per guide: its resource URI and title."""
    return "\n".join(f"daz://guide/{name} — {_title(name)}" for name in GUIDE_NAMES)
