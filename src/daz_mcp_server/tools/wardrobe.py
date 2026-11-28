"""Wardrobe tools: fitting, unfitting, and inspecting clothing/hair items."""
from __future__ import annotations

from typing import Any

from dazpy.exceptions import DazError, NodeNotFoundError, PropertyNotFoundError
from fastmcp.exceptions import ToolError

from .._mcp import mcp
from .._client import get_scene
from .._errors import run_tool



_MORPH_PATH_KEYS = ("morph", "actor", "shape", "expression", "pose")
_GENERATION_HINTS = (("Genesis9", ("genesis 9", "genesis9", "g9f", "g9m")),
                     ("Genesis8", ("genesis 8", "genesis8", "g8f", "g8m")),
                     ("Genesis3", ("genesis 3", "genesis3", "g3f", "g3m")),
                     ("Genesis2", ("genesis 2", "genesis2", "g2f", "g2m")))


def _generation(text: str, bone_names: list[str]) -> str:
    """Genesis generation from the figure's name/label, else its bone naming."""
    for gen, hints in _GENERATION_HINTS:
        if any(h in text for h in hints):
            return gen
    bones = set(bone_names)
    if "l_upperarm" in bones:
        return "Genesis9"
    if "lShldrBend" in bones:
        return "Genesis3/8"
    return "Genesis" if "genesis" in text else "other"


def _sex(text: str) -> str:
    if any(k in text for k in ("female", "victoria", "aiko", "stephanie", "g9f", "g8f", "g3f",
                               "g2f")):
        return "female"
    if any(k in text for k in ("male", "michael", "victor", "g9m", "g8m", "g3m", "g2m")):
        return "male"
    return "unknown"


def _subdivision_value(node: Any) -> Any:
    levels = node.subdivision() or {}
    return levels.get("view") or 0


async def _dforce_tool(fn: Any) -> dict[str, Any]:
    """run_tool, with dazpy's dForce/transfer DazError messages as ToolError."""
    def _wrapped() -> dict[str, Any]:
        try:
            return fn()
        except (NodeNotFoundError, PropertyNotFoundError):
            raise
        except DazError as e:
            raise ToolError(str(e)) from e
    return await run_tool(_wrapped)


async def _export(kind: str, output_path: str, node_labels: list[str] | None,
                  include_morphs: bool, apply_current_pose: bool,
                  scale_factor: float) -> dict[str, Any]:
    """FBX/OBJ export of the named nodes (or the whole scene) via dazpy."""
    if not output_path:
        raise ToolError("output_path is required")

    def _run() -> dict[str, Any]:
        scene = get_scene()
        exported: list[str] = []
        if node_labels:
            scene.select_all(False)
            for label in node_labels:
                try:
                    node = scene.resolve_node(label)
                except NodeNotFoundError:
                    continue
                node.select(True)
                exported.append(node.describe().label)
            if not exported:
                raise ToolError("None of the specified nodes were found in the scene: "
                                + ", ".join(node_labels))
        options = {"Scale": float(scale_factor), "Morphs": include_morphs,
                   "IncludeMorphs": include_morphs, "Pose": apply_current_pose,
                   "IncludeAnimations": apply_current_pose,
                   "SelectedRootsOnly": bool(node_labels)}
        export = scene.export_fbx if kind == "fbx" else scene.export_obj
        try:
            export(output_path, selected_only=bool(node_labels), options=options)
        except DazError as e:
            raise ToolError(str(e)) from e
        return {"success": True, "format": "Filmbox" if kind == "fbx" else "Wavefront Object",
                "output_path": output_path,
                "exported_nodes": exported or ["(whole scene)"],
                "node_count": len(exported), "include_morphs": include_morphs,
                "apply_current_pose": apply_current_pose, "scale_factor": scale_factor}

    return await run_tool(_run)


@mcp.tool()
async def daz_list_fitted_items(figure_label: str) -> dict[str, Any]:
    """List all clothing, hair, and prop nodes currently fitted to a figure.

    Returns every scene node that either follows the named figure (figure-based
    conforming clothing and hair) or is directly parented to it (props and
    accessories).  Each item includes its display label, internal name, type
    classification (``clothing``, ``hair``, or ``prop``), and element ID.

    Args:
        figure_label: Display label of the base figure (e.g. ``"Genesis 9"``).

    Returns:
        Dict with keys:
        - figure: confirmed figure label
        - fitted_count: total number of fitted items
        - fitted_items: list of {label, name, type, element_id}

    Examples:
        daz_list_fitted_items("Genesis 9")
        daz_list_fitted_items("Victoria 9")
    """
    def _run() -> dict[str, Any]:
        fig = get_scene().resolve_node(figure_label)
        items = [{"label": i.label, "name": i.name, "type": i.type, "element_id": i.element_id}
                 for i in fig.fitted_item_info()]
        return {"figure": fig.describe().label, "fitted_count": len(items),
                "fitted_items": items}

    return await run_tool(_run)



@mcp.tool()
async def daz_fit_clothing(clothing_label: str, figure_label: str) -> dict[str, Any]:
    """Fit a clothing or prop item to a base figure.

    For figure-based conforming clothing (items that are themselves a DzFigure),
    this sets the follow target so the clothing deforms with the figure's pose.
    For props and accessories, it parents the item to the figure.

    The clothing item must already be loaded into the scene.  Use
    ``daz_load_file`` or ``daz_load_product`` to add it first.

    Args:
        clothing_label: Display label of the clothing/prop node to fit.
        figure_label: Display label of the target base figure.

    Returns:
        Dict with keys:
        - success: true on success
        - clothing: confirmed clothing label
        - figure: confirmed figure label
        - method: which API was used (``setFollowTarget``, ``followSkeleton``,
          or ``addNodeChild`` for the parenting fallback)

    Examples:
        daz_fit_clothing("Sci-Fi Bodysuit", "Genesis 9")
        daz_fit_clothing("Leather Jacket", "Genesis 8 Female")
    """
    def _run() -> dict[str, Any]:
        scene = get_scene()
        clothing = scene.resolve_node(clothing_label)
        figure = scene.resolve_node(figure_label)
        method = clothing.fit_to(figure)
        return {"success": True, "clothing": clothing.describe().label,
                "figure": figure.describe().label, "method": method}

    return await run_tool(_run)



@mcp.tool()
async def daz_unfit_item(item_label: str) -> dict[str, Any]:
    """Remove the fitting relationship between a clothing/prop item and its figure.

    Clears any follow-target relationship (conforming clothing) and detaches the
    item from its parent figure (props), leaving it as a free-standing scene node
    at its current world position.

    Args:
        item_label: Display label of the item to unfit.

    Returns:
        Dict with keys:
        - success: true on success
        - item: confirmed item label
        - previous_figure: label of the figure it was detached from (or null)
        - actions: list of operations performed

    Examples:
        daz_unfit_item("Sci-Fi Bodysuit")
        daz_unfit_item("Hat Prop")
    """
    def _run() -> dict[str, Any]:
        item = get_scene().resolve_node(item_label)
        r = item.unfit()
        return {"success": True, "item": item.describe().label,
                "previous_figure": r.get("previous_figure"),
                "actions": r.get("actions") or ["no fitting relationship found"]}

    return await run_tool(_run)



@mcp.tool()
async def daz_run_transfer_utility(
    source_label: str,
    target_label: str,
    transfer_binding: bool = True,
    transfer_morphs: bool = True,
    transfer_uvs: bool = False,
    transfer_material_groups: bool = False,
    transfer_face_groups: bool = False,
    fit_to_figure: bool = True,
    parent_to_figure: bool = False,
    merge_hierarchies: bool = False,
) -> dict[str, Any]:
    """Project rigging, morphs, UVs, or groups from one node onto another.

    Headless equivalent of Edit > Object > Rigging > Transfer Utility...,
    using the scriptable ``DzTransferUtility`` object (``setSource`` /
    ``setTarget`` / ``doTransfer``) instead of the GUI dialog. Unlike the
    dialog's "Item Type" template (e.g. "Hair"), each aspect of the transfer
    is toggled explicitly here, so a prop or hair mesh doesn't end up with an
    unrelated full body skeleton just because "Hair" pulled one in.

    Typical use: project a figure's skin binding onto a static prop so it
    conforms to the figure's pose, and/or project morphs so the prop follows
    shape changes.

    Args:
        source_label: Display label of the source node (usually the figure
            whose rigging/morphs are the reference).
        target_label: Display label of the target node (the prop/hair mesh
            receiving the projection).
        transfer_binding: Project skin/bone weights onto the target (default True).
        transfer_morphs: Project morphs onto the target (default True).
        transfer_uvs: Project UV maps onto the target (default False).
        transfer_material_groups: Project material zone groups (default False).
        transfer_face_groups: Project face groups (default False).
        fit_to_figure: Fit the target onto the figure as a conforming item
            after the transfer (default True).
        parent_to_figure: Parent the target node to the figure (default False).
        merge_hierarchies: Merge the target's node hierarchy into the figure's
            (default False).

    Returns:
        Dict with keys:
        - success: true on success
        - source: confirmed source node label
        - target: confirmed target node label

    Examples:
        daz_run_transfer_utility("Genesis 8 Female", "Custom Hair Prop")
        daz_run_transfer_utility(
            "Genesis 9", "Bracelet", fit_to_figure=True, parent_to_figure=False
        )
        daz_run_transfer_utility(
            "Genesis 8 Female", "Cape", transfer_binding=True, transfer_morphs=False
        )
    """
    def _run() -> dict[str, Any]:
        scene = get_scene()
        source = scene.resolve_node(source_label)
        target = scene.resolve_node(target_label)
        scene.transfer_utility(
            source, target, binding=transfer_binding, morphs=transfer_morphs,
            uvs=transfer_uvs, material_groups=transfer_material_groups,
            face_groups=transfer_face_groups, fit_to_figure=fit_to_figure,
            parent_to_figure=parent_to_figure, merge_hierarchies=merge_hierarchies)
        return {"success": True, "source": source.describe().label,
                "target": target.describe().label}

    return await _dforce_tool(_run)



@mcp.tool()
async def daz_add_dforce_dynamic_surface(node_label: str) -> dict[str, Any]:
    """Add a dForce Dynamic Surface modifier to a scene node.

    Triggers the ``DzActionMgr`` action behind Edit > Object > Geometry >
    Add dForce Modifier: Dynamic Surface, which is the step that makes a
    mesh simulatable by dForce in the first place. Selects the node, then
    invokes the action; if a ``DzDForceModifier`` is already present the
    call is a no-op that reports the existing modifier instead of adding
    a duplicate.

    Use this before ``daz_set_dforce_property`` or ``daz_run_dforce_simulation``
    on a node that isn't dForce-enabled yet (e.g. custom props or clothing
    that didn't ship with a dForce modifier).

    This does not set up any pinning. A newly added modifier has no
    influence weights, so the whole surface is free to simulate — for
    anything that should hang or drape from a fixed point (hair rooted on
    a scalp, a cape's collar, a curtain's rod), pin the anchor vertices
    with ``daz_set_dforce_influence_weights`` first, or the object will
    simply fly away under gravity on the first simulation run.

    Args:
        node_label: Display label of the node to make dForce-simulatable.

    Returns:
        Dict with keys:
        - success: true on success
        - node: confirmed node label
        - already_present: true if a DzDForceModifier already existed
        - modifier: "DzDForceModifier"

    Examples:
        daz_add_dforce_dynamic_surface("Tablecloth")
        daz_add_dforce_dynamic_surface("Custom Cape")
    """
    def _run() -> dict[str, Any]:
        node = get_scene().resolve_node(node_label)
        added = node.add_dforce_dynamic_surface()
        return {"success": True, "node": node.describe().label, "already_present": not added,
                "modifier": "DzDForceModifier"}

    return await _dforce_tool(_run)



@mcp.tool()
async def daz_set_dforce_influence_weights(
    node_label: str,
    vertex_weights: dict[int, float] | None = None,
    default_weight: float = 1.0,
) -> dict[str, Any]:
    """Pin or free individual vertices for dForce simulation.

    Controls how strongly each vertex follows the simulation versus staying
    fixed to the base shape, via ``DzDForceModifier.setInfluenceWeights``:
    ``0.0`` means fully fixed/pinned, ``1.0`` means fully simulated/free.

    Without this, a dForce dynamic surface (added via
    ``daz_add_dforce_dynamic_surface``) has nothing anchoring it — it flies
    off under gravity on the very first simulation run instead of hanging or
    draping from a fixed point (Bug-Katalog #20: confirmed live with a
    hair-strand-style repro — an unpinned strand rooted on a collision
    sphere flew ~220 units away on the first simulation; pinning the two
    root vertices to 0.0 instead made it drape smoothly along the sphere's
    surface, staying within the sphere's own radius the whole way down).

    Args:
        node_label: Display label of the node (must already have a dForce
            modifier from ``daz_add_dforce_dynamic_surface``).
        vertex_weights: Mapping of vertex index to weight (0.0-1.0) for
            vertices that should differ from ``default_weight``. Typical
            use: pin the root/scalp-adjacent vertices of a hair strand or
            clothing seam to ``0.0`` while leaving the rest at the default.
        default_weight: Weight applied to every vertex not listed in
            ``vertex_weights`` (default ``1.0``, fully simulated).

    Returns:
        Dict with keys:
        - success: true on success
        - node: confirmed node label
        - vertex_count: total vertices in the node's geometry
        - default_weight: echoed default weight
        - overridden_count: number of vertices set via vertex_weights

    Examples:
        daz_set_dforce_influence_weights("Hair Strand", {0: 0.0, 1: 0.0})
        daz_set_dforce_influence_weights("Cape", default_weight=0.0)
    """
    def _run() -> dict[str, Any]:
        node = get_scene().resolve_node(node_label)
        count, overridden = node.set_dforce_influence_weights(
            default_weight, {int(k): float(v) for k, v in (vertex_weights or {}).items()})
        return {"success": True, "node": node.describe().label, "vertex_count": count,
                "default_weight": default_weight, "overridden_count": overridden}

    return await _dforce_tool(_run)



@mcp.tool()
async def daz_get_dforce_influence_weights(node_label: str) -> dict[str, Any]:
    """Read the per-vertex dForce influence (pinning) weights on a node.

    Counterpart to ``daz_set_dforce_influence_weights``. Useful to verify
    pinning took effect, or to check whether a node has any influence
    weights set at all before assuming it will drape rather than fly free.

    Args:
        node_label: Display label of the node (must already have a dForce
            modifier).

    Returns:
        Dict with keys:
        - success: true on success
        - node: confirmed node label
        - has_influence_weights: false if no weight map has been set yet
        - vertex_count: number of weights returned (only present when
          has_influence_weights is true)
        - weights: list of per-vertex weights, index-aligned with the
          node's geometry (empty when has_influence_weights is false)

    Examples:
        daz_get_dforce_influence_weights("Hair Strand")
    """
    def _run() -> dict[str, Any]:
        node = get_scene().resolve_node(node_label)
        weights = node.dforce_influence_weights()
        label = node.describe().label
        if weights is None:
            return {"success": True, "node": label, "has_influence_weights": False,
                    "weights": []}
        return {"success": True, "node": label, "has_influence_weights": True,
                "vertex_count": len(weights), "weights": weights}

    return await _dforce_tool(_run)



@mcp.tool()
async def daz_run_dforce_simulation(node_label: str | None = None) -> dict[str, Any]:
    """Run dForce cloth or hair simulation.

    Triggers the DAZ Studio simulation engine (``DzSimulationMgr``) for all
    simulatable nodes in the scene, or limits the simulation to a single node
    when ``node_label`` is provided (the node is selected before the sim runs).

    dForce modifiers must already be present on the target clothing or hair
    node.  Use ``daz_set_dforce_property`` to tune modifier settings before
    calling this tool.

    There is no way to control how much is simulated per call from here.
    ``DzSimulationMgr.simulate()``'s time-range argument does not affect the
    actual simulated duration — verified live (Bug-Katalog #21): a 0-frame
    range and a 30-frame range produced bit-identical results, and
    pre-setting the scene's anim range first made no difference either. The
    real duration comes from DAZ Studio's own Simulation Settings > Duration
    panel and can currently only be changed through the DAZ Studio UI.

    Args:
        node_label: Display label of the clothing or hair node to simulate.
            When omitted the entire scene is simulated.

    Returns:
        Dict with keys:
        - success: true on success
        - node: node label that was targeted, or "all simulatable nodes"

    Examples:
        daz_run_dforce_simulation("Outfit")
        daz_run_dforce_simulation()
    """
    def _run() -> dict[str, Any]:
        scene = get_scene()
        nodes = [scene.resolve_node(node_label)] if node_label else None
        scene.run_dforce_simulation(nodes, wait=True)
        return {"success": True, "node": node_label or "all simulatable nodes"}

    return await run_tool(_run)



@mcp.tool()
async def daz_bake_simulation(node_label: str | None = None) -> dict[str, Any]:
    """Bake dForce simulation results to keyframes.

    Converts the in-memory dForce simulation cache to actual keyframes on the
    simulated vertices/bones so the result is preserved when the scene is saved
    or the simulation cache is cleared.

    Call this after ``daz_run_dforce_simulation`` to lock down the simulated
    shape.  The node selection behaviour mirrors ``daz_run_dforce_simulation``:
    when ``node_label`` is given the node is selected first; otherwise all
    currently simulated nodes are baked.

    Args:
        node_label: Display label of the node to bake.  When omitted all
            simulated nodes are baked.

    Returns:
        Dict with keys:
        - success: true on success
        - node: node label that was targeted, or "all"
        - method: the DazScript method used to bake

    Examples:
        daz_bake_simulation("Outfit")
        daz_bake_simulation()
    """
    def _run() -> dict[str, Any]:
        scene = get_scene()
        if node_label is None:
            return {"success": True, "node": "all", "method": "freeze",
                    "modifiers_frozen": scene.freeze_dforce()}
        node = scene.resolve_node(node_label)
        frozen = node.freeze_dforce()
        if not frozen:
            raise ToolError(f"No dForce modifier on '{node_label}' to bake")
        return {"success": True, "node": node.describe().label, "method": "freeze",
                "modifiers_frozen": frozen}

    return await _dforce_tool(_run)



@mcp.tool()
async def daz_set_dforce_property(
    node_label: str,
    property_name: str,
    value: float,
) -> dict[str, Any]:
    """Set a property directly on a node's dForce modifier object.

    Locates the ``DzDForceModifier`` attached to the named node (checking both
    node-level and shape-level modifiers) and sets the named property to the
    given value. The modifier itself only carries a handful of properties —
    typically ``"Freeze Simulation"``, ``"Simulation Object Type"``, and
    ``"Simulation Base Shape"``.

    Most of the sliders visible in the Surfaces-pane "Simulation" category —
    ``"Dynamics Strength"``, ``"Stretch/Shear/Bend Stiffness"``,
    ``"Collision Offset"``, ``"Self Collide"``, ``"Friction"``, etc. — live
    on a *separate* per-material object instead, not on this modifier. Use
    ``daz_set_dforce_surface_property`` for those.

    If the property name is not found exactly, a case-insensitive fallback
    search is attempted.  On failure the error lists all available properties.

    Args:
        node_label: Display label of the clothing or hair node.
        property_name: Internal name of the dForce modifier property to set.
        value: Numeric value to apply.

    Returns:
        Dict with keys:
        - success: true on success
        - node: confirmed node label
        - modifier: class name of the dForce modifier that was modified
        - property: confirmed property name (may differ from input if fuzzy-matched)
        - old_value: value before the change
        - new_value: value that was set

    Examples:
        daz_set_dforce_property("Outfit", "Freeze Simulation", 1.0)
        daz_set_dforce_property("Hair", "Simulation Object Type", 0)
    """
    def _run() -> dict[str, Any]:
        node = get_scene().resolve_node(node_label)
        r = node.set_dforce_property(property_name, value)
        return {"success": True, "node": node.describe().label, **r}

    return await _dforce_tool(_run)



@mcp.tool()
async def daz_get_dforce_surface_properties(
    node_label: str, material_name: str | None = None
) -> dict[str, Any]:
    """List per-surface dForce simulation properties for a material zone.

    These are the sliders shown in the Surfaces pane under the "Simulation"
    category once a dForce modifier is present — ``Collision Offset``,
    ``Self Collide``, ``Friction``, ``Dynamics Strength``, ``Stretch/Shear/
    Bend Stiffness``, and many more (135 properties on a typical figure
    surface, including hair-specific pre-sim/pre-render tunables). They live
    on a ``DzDForceSettingsProvider`` object reached via
    ``shape.findSimulationSettingsProvider(materialName)`` — a separate
    object from the material itself, which is why ``daz_get_material``
    never shows them.

    Args:
        node_label: Display label of the node (must have a dForce modifier).
        material_name: Internal name of the material/surface zone. When
            omitted, the node's first material is used.

    Returns:
        Dict with keys:
        - node: confirmed node label
        - material: confirmed material name
        - property_count: number of properties returned
        - properties: list of {name, label, type, value}

    Examples:
        daz_get_dforce_surface_properties("Outfit", "Fabric")
        daz_get_dforce_surface_properties("Genesis 8 Female")
    """
    def _run() -> dict[str, Any]:
        node = get_scene().resolve_node(node_label)
        material, props = node.dforce_surface_properties(material_name)
        return {"node": node.describe().label, "material": material,
                "property_count": len(props), "properties": props}

    return await _dforce_tool(_run)



@mcp.tool()
async def daz_set_dforce_surface_property(
    node_label: str,
    property_name: str,
    value: float,
    material_name: str | None = None,
) -> dict[str, Any]:
    """Set a per-surface dForce simulation property on a material zone.

    Counterpart to ``daz_set_dforce_property``: while that tool only reaches
    the three properties on the ``DzDForceModifier`` object itself, this one
    reaches the ``DzDForceSettingsProvider`` for a specific material —
    ``Collision Offset``, ``Self Collide``, ``Friction``, ``Dynamics
    Strength``, ``Stretch/Shear/Bend Stiffness``, ``Density``, and more (use
    ``daz_get_dforce_surface_properties`` to see the full list for a node).

    Args:
        node_label: Display label of the node (must have a dForce modifier).
        property_name: Exact property name, e.g. ``"Collision Offset"``.
        value: Numeric value to apply.
        material_name: Internal name of the material/surface zone. When
            omitted, the node's first material is used — pass this
            explicitly for multi-material nodes where zones should differ.

    Returns:
        Dict with keys:
        - success: true on success
        - node: confirmed node label
        - material: confirmed material name
        - property: confirmed property name
        - old_value: value before the change
        - new_value: value after the change

    Examples:
        daz_set_dforce_surface_property("Outfit", "Collision Offset", 0.5)
        daz_set_dforce_surface_property("Outfit", "Self Collide", 1, material_name="Fabric")
        daz_set_dforce_surface_property("Hair", "Dynamics Strength", 0.8)
    """
    def _run() -> dict[str, Any]:
        node = get_scene().resolve_node(node_label)
        r = node.set_dforce_surface_property(property_name, value, material_name)
        return {"success": True, "node": node.describe().label, **r}

    return await _dforce_tool(_run)



@mcp.tool()
async def daz_get_figure_info(figure_label: str) -> dict[str, Any]:
    """Return diagnostic information about a loaded figure.

    Detects the Genesis generation and biological sex from the figure's internal
    name and label, lists all morphs that currently have a non-zero value, counts
    the number of clothing/prop items fitted to the figure, and reports the active
    subdivision level.

    This is the recommended first call when working with an unfamiliar figure, as
    it determines which morph names, bone names, and fitting approaches apply.

    Args:
        figure_label: Display label of the figure to inspect
            (e.g. ``"Genesis 9"`` or ``"Victoria 9"``).

    Returns:
        Dict with keys:
        - label: confirmed display label
        - name: internal node name
        - generation: ``"Genesis9"``, ``"Genesis8"``, ``"Genesis3"``, ``"Genesis2"``,
          ``"Genesis"``, or ``"other"``
        - sex: ``"female"``, ``"male"``, or ``"unknown"``
        - active_morphs: list of {name, label, value, path} for morphs with |value| > 0.0005
        - active_morph_count: length of active_morphs list
        - fitted_item_count: number of clothing/prop nodes following or parented to this figure
        - subdivision_level: current SubDivision Level value (0 if property absent)

    Examples:
        daz_get_figure_info("Genesis 9")
        daz_get_figure_info("Victoria 9")
        daz_get_figure_info("Michael 8")
    """
    def _run() -> dict[str, Any]:
        fig = get_scene().resolve_node(figure_label)
        info = fig.describe()
        text = f"{info.name} {info.label}".lower()
        morphs = [{"name": d.name, "label": d.label, "value": d.value, "path": d.path}
                  for d in fig.property_details("morph")
                  if isinstance(d.value, (int, float)) and abs(d.value) > 0.0005
                  and any(k in d.path.lower() for k in _MORPH_PATH_KEYS)]
        return {"label": info.label, "name": info.name,
                "generation": _generation(text, fig.bone_names()),
                "sex": _sex(text), "active_morphs": morphs,
                "active_morph_count": len(morphs),
                "fitted_item_count": len(fig.fitted_item_info()),
                "subdivision_level": _subdivision_value(fig)}

    return await run_tool(_run)



@mcp.tool()
async def daz_set_subdivision(node_label: str, level: int) -> dict[str, Any]:
    """Set the SubDivision Level property on a figure or prop.

    Higher subdivision levels smooth geometry at the cost of memory and render
    time.  Level 0 is base mesh; levels 1–4 progressively refine the mesh.
    DAZ Studio's default render subdivision is typically 1 or 2.

    Args:
        node_label: Display label of the figure or prop to adjust
            (e.g. ``"Genesis 9"`` or ``"Car Prop"``).
        level: Desired subdivision level.  Clamped to the range 0–4.

    Returns:
        Dict with keys:
        - success: true on success
        - node: confirmed node label
        - property: name of the subdivision property that was set
        - old_level: previous value
        - new_level: value after update

    Examples:
        daz_set_subdivision("Genesis 9", 2)
        daz_set_subdivision("Car Prop", 0)
        daz_set_subdivision("Hair", 1)

    Notes:
        Raises ToolError if the node has no subdivision property (e.g. a light
        or camera).  Use ``daz_get_figure_info`` to check the current level first.
    """
    if level < 0 or level > 4:
        raise ToolError(f"Subdivision level must be between 0 and 4, got {level}")
    new_level = int(level)

    def _run() -> dict[str, Any]:
        node = get_scene().resolve_node(node_label)
        try:
            r = node.set_subdivision(new_level)
        except PropertyNotFoundError as e:
            raise ToolError(f"No subdivision property found on '{node_label}'. "
                            "This node may not support subdivision.") from e
        return {"success": True, "node": node.describe().label, "property": "SubDIALevel",
                "old_level": r["previous"]["view"], "new_level": r["current"]["view"],
                "render_level": r["current"]["render"]}

    return await run_tool(_run)



@mcp.tool()
async def daz_export_fbx(
    output_path: str,
    node_labels: list[str] | None = None,
    include_morphs: bool = True,
    apply_current_pose: bool = True,
    scale_factor: float = 1.0,
) -> dict[str, Any]:
    """Export scene nodes to an FBX file via DAZ Studio's Filmbox exporter.

    Selects the specified nodes (or all scene nodes if none are given) and
    calls ``DzExporter.writeFile`` with the Filmbox exporter.  Returns a
    graceful error if the FBX exporter plugin is not installed in DAZ Studio.

    FBX is the standard interchange format for game engines (Unreal, Unity) and
    VFX pipelines (Maya, 3ds Max, Blender).

    Args:
        output_path: Absolute path for the output ``.fbx`` file
            (e.g. ``"C:/exports/hero.fbx"``).  The parent directory must exist.
        node_labels: List of node display labels to export.  Pass ``None`` or an
            empty list to export all nodes in the scene.
        include_morphs: Whether to bake morph targets into the export (default True).
        apply_current_pose: Whether to export the current frame's pose (default True).
        scale_factor: Uniform scale applied to exported geometry (default 1.0).
            Use ``0.01`` to convert DAZ's centimetres to metres for Unity/Unreal.

    Returns:
        Dict with keys:
        - success: true on success
        - format: ``"Filmbox"``
        - output_path: path written
        - exported_nodes: list of node labels included in the export
        - node_count: number of exported nodes
        - include_morphs, apply_current_pose, scale_factor: echoed settings

    Examples:
        daz_export_fbx("C:/exports/hero.fbx")
        daz_export_fbx("C:/exports/hero.fbx", node_labels=["Genesis 9", "Sci-Fi Suit"])
        daz_export_fbx("C:/exports/hero.fbx", scale_factor=0.01, include_morphs=False)

    Notes:
        Raises ToolError if the FBX exporter is not installed.  The error message
        lists available exporters so you can choose an alternative format.
    """
    return await _export("fbx", output_path, node_labels, include_morphs,
                         apply_current_pose, scale_factor)



@mcp.tool()
async def daz_export_obj(
    output_path: str,
    node_labels: list[str] | None = None,
    apply_current_pose: bool = True,
    scale_factor: float = 1.0,
) -> dict[str, Any]:
    """Export scene nodes to a Wavefront OBJ file via DAZ Studio's OBJ exporter.

    Selects the specified nodes (or all scene nodes if none are given) and
    calls ``DzExporter.writeFile`` with the Wavefront OBJ exporter.
    Returns a graceful error if the OBJ exporter plugin is not installed.

    OBJ is a widely supported geometry-only format suitable for Blender,
    ZBrush, Marvelous Designer, and other tools that need a static mesh.
    It does not carry animations or morph targets.

    Args:
        output_path: Absolute path for the output ``.obj`` file
            (e.g. ``"C:/exports/hero_base.obj"``).  Parent directory must exist.
        node_labels: List of node display labels to export.  Pass ``None`` or an
            empty list to export all nodes in the scene.
        apply_current_pose: Whether to export the geometry in the current
            frame's posed state (default True).
        scale_factor: Uniform scale applied to exported geometry (default 1.0).

    Returns:
        Dict with keys:
        - success: true on success
        - format: ``"Wavefront Object"``
        - output_path: path written
        - exported_nodes: list of node labels included in the export
        - node_count: number of exported nodes
        - apply_current_pose, scale_factor: echoed settings

    Examples:
        daz_export_obj("C:/exports/hero_base.obj")
        daz_export_obj("C:/exports/suit.obj", node_labels=["Sci-Fi Suit"])
        daz_export_obj("C:/exports/hero_base.obj", scale_factor=0.01)

    Notes:
        OBJ does not support morph targets or animations.  Use ``daz_export_fbx``
        when you need those features.  Raises ToolError if the OBJ exporter is
        not installed.
    """
    return await _export("obj", output_path, node_labels, False,
                         apply_current_pose, scale_factor)
