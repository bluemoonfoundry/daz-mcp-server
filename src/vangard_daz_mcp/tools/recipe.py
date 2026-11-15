"""Scene-recipe tools: thin MCP wrappers over the ``dazpy.recipe`` facade.

The loop is validate -> plan -> apply -> render.  All recipe logic lives in
dazpy; these tools only marshal arguments and turn fixable input mistakes into
data the model can act on instead of ``ToolError``.
"""
from __future__ import annotations

import json
from typing import Any

from dazpy import recipe as dz_recipe
from dazpy.exceptions import RecipeNotAppliedError, RecipeValidationError

from .._client import get_scene, run_dazpy
from .._errors import handle_dazpy_error
from .._mcp import mcp

_DEFAULT_TAG = {"default"}

_CONFLICT_HELP = """
Conflicts: each has ``path`` (``<entity>.<channel>``, e.g.
``cameras.close_up.transform``), ``kind``, and the ``desired`` (recipe),
``base`` (last applied) and ``live`` (scene) values.  A conflict means the recipe
and the scene both changed since the last apply.  ``on_conflict``: ``ask``
(default; any conflict writes nothing and is returned), ``recipe_wins``
(overwrite hand edits), ``scene_wins`` (keep hand edits).  Use the user's
remembered preference: "always override" -> ``recipe_wins``, "always defer" ->
``scene_wins``, otherwise ``ask``, show the user the conflicts, then send
``resolutions`` mapping each conflict path to ``"recipe"`` or ``"scene"``.
"""


def _invalid(error: RecipeValidationError) -> dict[str, Any]:
    report = error.report.to_dict()
    return {"ok": False, "errors": report["errors"], "warnings": report.get("warnings", [])}


def _with_conflict_help(fn):
    fn.__doc__ = (fn.__doc__ or "") + _CONFLICT_HELP
    return fn


async def _call(fn) -> dict[str, Any]:
    """Run *fn* (a sync dazpy call) off-thread; map fixable errors to data."""
    try:
        return await run_dazpy(fn)
    except RecipeValidationError as e:
        return _invalid(e)
    except RecipeNotAppliedError as e:
        return {"ok": False, "reason": str(e), "observe": e.report.to_dict()}
    except ValueError as e:  # invalid on_conflict / resolution / unknown shot id
        return {"ok": False, "error": str(e)}
    except Exception as e:
        handle_dazpy_error(e)
        raise  # unreachable: handle_dazpy_error always raises


@mcp.tool(tags=_DEFAULT_TAG)
async def daz_recipe_validate(recipe: dict[str, Any]) -> dict[str, Any]:
    """Validate a scene recipe and check that the files it references exist.

    Start of the loop: validate -> plan -> apply -> render.  Read the
    ``daz://recipe/schema`` resource for the recipe format.  Returns
    ``{ok, errors, warnings}``; each error has ``path``, ``code``, ``message``
    and often a ``suggestion``.  Fix errors and validate again before planning.
    """
    def _run() -> dict:
        return dz_recipe.validate(recipe, get_scene()).to_dict()

    return await _call(_run)


@mcp.tool(tags=_DEFAULT_TAG)
@_with_conflict_help
async def daz_recipe_plan(
    recipe: dict[str, Any],
    on_conflict: str = "ask",
    resolutions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Dry run: show the steps, conflicts and warnings an apply would produce.

    Reads the scene, changes nothing.  Invalid recipes return
    ``{ok: false, errors}``.
    """
    def _run() -> dict:
        return dz_recipe.plan(
            recipe, get_scene(), on_conflict=on_conflict, resolutions=resolutions
        ).to_dict()

    return await _call(_run)


@mcp.tool(tags=_DEFAULT_TAG)
@_with_conflict_help
async def daz_recipe_apply(
    recipe: dict[str, Any],
    on_conflict: str = "ask",
    resolutions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Apply a scene recipe to the open scene (idempotent; re-run after edits).

    Loop: validate -> plan -> apply -> render.  Only nodes the recipe created are
    touched.  Returns ``applied`` plus ``conflicts``, ``overwritten``, ``kept``
    and ``warnings``.  Under ``ask`` a conflict returns ``applied: false`` and
    writes nothing.  A failure part-way rolls back.  Invalid recipes return
    ``{ok: false, errors}`` so you can fix them.
    """
    def _run() -> dict:
        return dz_recipe.apply(
            recipe, get_scene(), on_conflict=on_conflict, resolutions=resolutions
        ).to_dict()

    return await _call(_run)


@mcp.tool(tags=_DEFAULT_TAG)
async def daz_recipe_observe(recipe: dict[str, Any]) -> dict[str, Any]:
    """Compare the scene with a recipe without changing anything.

    Returns ``applied``, ``in_sync``, ``drift`` (hand edits kept or nodes deleted
    by hand), ``pending`` (what an apply would change) and ``conflicts``.  Use it
    to see whether the user edited the scene since the last apply.
    """
    def _run() -> dict:
        return dz_recipe.observe(recipe, get_scene()).to_dict()

    return await _call(_run)


@mcp.tool(tags=_DEFAULT_TAG)
async def daz_recipe_render(
    recipe: dict[str, Any],
    shots: list[str] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Render the recipe's shots (all, or the shot ids in ``shots``).

    Last step of validate -> plan -> apply -> render.  Returns
    ``{shots: [{id, camera, output, ...}]}``.  Refuses with
    ``{ok: false, reason, observe}`` when the recipe is not applied, has pending
    changes or conflicts, or a shot camera was changed by hand; apply first, or
    pass ``force=True`` to render the scene as it is.
    """
    def _run() -> dict:
        out = dz_recipe.render(recipe, get_scene(), shots=shots, force=force)
        return {"shots": [s.to_dict() for s in out]}

    return await _call(_run)


@mcp.resource("daz://recipe/schema")
def daz_recipe_schema_resource() -> str:
    """JSON Schema for scene recipes (current version)."""
    return json.dumps(dz_recipe.recipe_schema())


@mcp.resource("daz://recipe/schema/{version}")
def daz_recipe_schema_version_resource(version: str) -> str:
    """JSON Schema for scene recipes of a given version."""
    return json.dumps(dz_recipe.recipe_schema(int(version)))
