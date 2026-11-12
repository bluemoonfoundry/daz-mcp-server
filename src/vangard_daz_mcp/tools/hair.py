"""Strand-Based Hair tools for DAZ Studio scene nodes.

DAZ Studio's native Strand-Based Hair (Create > New Hair) has a hard split
between what's scriptable and what isn't, confirmed by live testing against
a running DAZ Studio 6 instance:

- Node creation, target-figure fitting, and reading back which nodes exist
  and whether they have generated geometry: fully scriptable (this module).
- Hair color, shader (Marschner R/TT/TRT/G channels), and thickness
  (Line Start/End Width): fully scriptable, but through the *existing*
  generic material tools — ``daz_list_materials`` / ``daz_get_material`` /
  ``daz_set_material_property`` already work on a Strand-Based Hair node's
  ``DzStrandHairRSLMaterial`` zone with no extra code needed.
- Guide density, guide count, scraggle/frizz styling, and the scalp growth
  region (the DAZ SDK's ``DzDForceSettingsProvider`` parameter surface):
  **not reachable**. Every DazScript path tried (bare constructor, both a
  generic and a hair-specific ``DzActionMgr`` action, on both an empty node
  and one created through the working GUI action) leaves
  ``shape.findSimulationSettingsProvider()`` returning null. There is no
  known way to set these from a script — they must be adjusted by hand in
  DAZ Studio's Surfaces pane after ``daz_create_strand_hair`` returns.
"""
from __future__ import annotations

from typing import Any

from .._mcp import mcp, _execute_by_id, _execute_by_id_async


@mcp.tool()
async def daz_create_strand_hair(target_node_label: str) -> dict[str, Any]:
    """Create a native Strand-Based Hair node fit to a target figure.

    Triggers DAZ Studio's own ``DzStrandHairCreateNodeAction`` (the same
    action behind Create > New Hair in the GUI) with the target figure
    selected. This is the only DazScript-reachable path that produces a
    hair node with real generated geometry — a bare ``new DzStrandHairNode()``
    never gets geometry, no matter what's set on it afterward.

    **This shows a confirmation dialog in the DAZ Studio window that a human
    must click.** The underlying script blocks until that happens, so this
    tool submits it via the async endpoint and returns immediately with a
    ``request_id`` instead of waiting synchronously (a synchronous wait would
    hit the client timeout while the dialog sits there).

    Workflow:
    1. Call this tool. It returns ``{"request_id": ..., "status": "queued"}``.
    2. Tell the user: "DAZ Studio is showing a confirmation dialog — please
       click it in the DAZ Studio window."
    3. Poll ``daz_get_request_status(request_id)`` until it's no longer
       "running"/"queued", or use ``daz_get_request_result(request_id,
       wait=true)`` to long-poll for the final result.
    4. On success the result includes the new node's label — pass it to
       ``daz_get_material`` / ``daz_set_material_property`` to set hair
       color/shader/thickness, or to ``daz_list_strand_hair_nodes`` to
       re-verify.

    **What this does NOT give you:** guide density, guide count, and
    scraggle/frizz styling are not scriptable at all (see module docstring)
    — after this completes, those still need to be set by hand in DAZ
    Studio's Surfaces pane.

    Args:
        target_node_label: Display label of the figure to grow hair on
            (e.g. ``"Genesis 8 Female"``). Must already be in the scene.

    Returns:
        ``{"request_id": "script-XXXXXXXX", "status": "queued", "submitted_at": "..."}``

    Examples:
        daz_create_strand_hair("Genesis 8 Female")
    """
    return await _execute_by_id_async(
        "vangard-create-strand-hair",
        {"targetNodeLabel": target_node_label},
    )


@mcp.tool()
async def daz_list_strand_hair_nodes() -> dict[str, Any]:
    """List every Strand-Based Hair node in the scene.

    For each ``DzStrandHairNode`` found, reports its target figure, whether
    it has generated geometry yet (``has_geometry``), and its material zone
    labels (pass those to ``daz_get_material`` / ``daz_set_material_property``
    to read/set color, shader, or thickness).

    Use this to check the result of ``daz_create_strand_hair`` after the
    user confirms the dialog, or to discover hair nodes that were already in
    a loaded scene/preset.

    Returns:
        Dict with keys:
        - count: number of Strand-Based Hair nodes found
        - nodes: list of {label, name, target, has_geometry, materials}

    Examples:
        daz_list_strand_hair_nodes()
        # → {"count": 1, "nodes": [{"label": "Strand-Based Hair",
        #     "target": "Genesis 8 Female", "has_geometry": true,
        #     "materials": [""]}]}
    """
    return await _execute_by_id("vangard-list-strand-hair-nodes")
