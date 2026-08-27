"""Material and surface tools for DAZ Studio scene nodes."""
from __future__ import annotations

import json
from typing import Any

from fastmcp.exceptions import ToolError

from .._mcp import mcp, _execute_by_id
from .._client import get_daz_client, run_dazpy
from .._errors import handle_dazpy_error


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_list_materials(node_label: str) -> dict[str, Any]:
    """List all material zones on a scene node.

    Returns the index, internal name, display label, and DAZ shader class for
    every surface zone on the node's geometry. Use the returned ``label`` value
    as the ``material_name`` argument in ``daz_get_material`` and
    ``daz_set_material_property``.

    Args:
        node_label: Display label or internal name of the target node.

    Returns:
        Dict with keys:
        - node: confirmed node label
        - material_count: number of surface zones
        - materials: list of {index, name, label, shader}

    Examples:
        daz_list_materials("Genesis 9")
        # → {"material_count": 18, "materials": [{"label": "Skin", ...}, ...]}

        daz_list_materials("My Dress Prop")
    """
    def _run() -> dict | None:
        client = get_daz_client()
        script = f"""(function() {{
            var node = Scene.findNodeByLabel({json.dumps(node_label)});
            if (!node) return null;
            var obj = node.getObject();
            if (!obj) return [];
            var shape = obj.getCurrentShape();
            if (!shape) return [];
            var result = [];
            for (var i = 0; i < shape.getNumMaterials(); i++) {{
                var m = shape.getMaterial(i);
                var lbl = (typeof m.getLabel === "function") ? m.getLabel() : m.getName();
                result.push({{
                    index:  i,
                    name:   m.getName(),
                    label:  lbl,
                    shader: m.className()
                }});
            }}
            return result;
        }})();"""
        data = client.execute(script).value
        if data is None:
            return None
        return {
            "node": node_label,
            "material_count": len(data),
            "materials": data,
        }

    try:
        result = await run_dazpy(_run)
    except Exception as e:
        handle_dazpy_error(e)
    if result is None:
        raise ToolError(f"Node not found: {node_label!r}")
    return result


@mcp.tool()
async def daz_get_material(node_label: str, material_name: str) -> dict[str, Any]:
    """Get all properties of a named material zone on a node.

    Returns every property on the surface with its type (numeric, color, image)
    and current value. Use this to discover settable property names before
    calling ``daz_set_material_property``.

    Color values are returned as ``"#RRGGBB"`` hex strings.
    Image values are returned as file paths (or null if no map is loaded).

    Args:
        node_label: Display label or internal name of the target node.
        material_name: Label or name of the material zone (from daz_list_materials).

    Returns:
        Dict with keys:
        - node, material, shader: confirmed identifiers
        - property_count: total number of properties
        - properties: list of {name, label, type, value}

    Examples:
        daz_get_material("Genesis 9", "Skin")
        daz_get_material("Genesis 9", "Cornea")
    """
    return await _execute_by_id(
        "vangard-get-material",
        {"nodeLabel": node_label, "materialName": material_name},
    )


@mcp.tool()
async def daz_set_material_property(
    node_label: str,
    material_name: str,
    property_name: str,
    value: Any,
) -> dict[str, Any]:
    """Set a property on a named material zone.

    For **numeric** properties (e.g. "Metallic Weight", "Glossy Roughness",
    "Cutout Opacity") pass a float in the property's native range (usually 0–1).

    For **color** properties (e.g. "Diffuse Color", "Emission Color") pass a
    hex string: ``"#RRGGBB"`` (e.g. ``"#FF8040"``).

    Use ``daz_list_materials`` to find zone names and ``daz_get_material`` to
    discover property names and their types.

    Args:
        node_label: Display label of the target node.
        material_name: Label of the material zone to modify.
        property_name: Display label or internal name of the property.
        value: Float for numeric properties; ``"#RRGGBB"`` string for color properties.

    Returns:
        Dict confirming node, material, property, type, and the value applied.

    Examples:
        # Adjust skin roughness
        daz_set_material_property("Genesis 9", "Skin", "Glossy Roughness", 0.4)

        # Change eye colour
        daz_set_material_property("Genesis 9", "Irises", "Diffuse Color", "#3A6EA5")

        # Make a surface transparent
        daz_set_material_property("My Prop", "Glass", "Cutout Opacity", 0.1)
    """
    return await _execute_by_id(
        "vangard-set-material-property",
        {
            "nodeLabel": node_label,
            "materialName": material_name,
            "propertyName": property_name,
            "value": value,
        },
    )


@mcp.tool()
async def daz_apply_material_preset(node_label: str, preset_path: str) -> dict[str, Any]:
    """Apply a DAZ material preset (.duf) file to a scene node.

    Selects the named node and calls ``App.getContentMgr().openFile()`` with the
    preset path so DAZ Studio applies the material channels defined in the file.
    This is the same operation as dragging a material preset from Smart Content
    onto a figure in the DAZ Studio UI.

    The node must already be present in the scene.  The preset must be a material
    preset ``.duf`` file — not a full scene or prop file.

    Args:
        node_label: Display label of the node to apply the material to
            (e.g. ``"Genesis 9"``).
        preset_path: Absolute path to the ``.duf`` material preset file
            (e.g. ``"C:/DAZ/My Library/Materials/Skin/Hero Skin.duf"``).

    Returns:
        Dict with keys:
        - success: true on success
        - node: confirmed node label
        - preset: path used
        - materials: list of material slot labels on the node after application
        - material_count: number of material slots

    Examples:
        daz_apply_material_preset("Genesis 9", "C:/Library/Materials/Skin/Hero Skin.duf")
        daz_apply_material_preset("Genesis 9", "D:/assets/Mats/Sci-Fi Suit.duf")
    """
    return await _execute_by_id(
        "vangard-apply-material-preset",
        {"nodeLabel": node_label, "presetPath": preset_path},
    )


@mcp.tool()
async def daz_convert_to_iray_uber(node_label: str, preset_path: str | None = None) -> dict[str, Any]:
    """Upgrade every material zone on a node from DzDefaultMaterial to DzUberIrayMaterial.

    Content merged into a scene as raw DSON (a hand-authored .duf, or output from a
    from-scratch scene-merge exporter) reliably instantiates materials as the legacy
    ``DzDefaultMaterial`` ("DAZ Studio Default (RSL)" in Daz's UI) instead of the real
    Iray Uber shader class, no matter how complete the material's channel data is.
    That legacy shader does not read modern channel fields like ``image_file`` at all,
    so textures silently fail to display regardless of how correct the underlying data is.

    This tool fixes it by going through Daz's own shader-preset **application** codepath
    instead — the same thing that runs when a user drags a Shader Preset from Smart
    Content onto a figure (``App.getContentMgr().openFile()`` on the selected node).
    That path builds a genuine native shader object rather than parsing one from JSON,
    and reliably promotes every material zone on the node to ``DzUberIrayMaterial``.

    **This resets every channel on every zone to shader defaults.** Follow up with
    ``daz_get_material`` / ``daz_set_material_property`` per zone to restore actual
    diffuse/PBR values and texture maps (color values you set afterward should already
    be in Daz's expected space — see the color-property gotcha in SKILL_DAZSCRIPT.md if
    you're feeding in already-linear values from another DCC rather than a UI hex color).

    Args:
        node_label: Display label of the node whose materials should be upgraded.
        preset_path: Absolute path to a "preset_shader"-type .duf file. If omitted,
            resolves Daz Studio's own stock "!Iray Uber Base" preset (ships with every
            installation) via the content manager — no need to know where the user's
            library lives.

    Returns:
        Dict with keys:
        - success: true on success
        - node: confirmed node label
        - preset: the preset path that was applied
        - before: list of {label, shader} for every zone before conversion
        - after: list of {label, shader} for every zone after conversion

    Examples:
        daz_convert_to_iray_uber("Genesis 9")
        daz_convert_to_iray_uber("MyImportedProp", "C:/Library/Shader Presets/Custom.duf")
    """
    return await _execute_by_id(
        "vangard-convert-to-iray-uber",
        {"nodeLabel": node_label, "presetPath": preset_path},
    )


@mcp.tool()
async def daz_copy_material(
    source_node: str,
    source_material_name: str,
    dest_node: str,
    dest_material_name: str,
) -> dict[str, Any]:
    """Copy all property values from one material slot to another within the scene.

    Iterates every property on the source material and sets the matching property
    on the destination material.  Properties that exist on the source but not the
    destination are silently skipped.  Both nodes must already be loaded in the scene.

    Useful for duplicating a skin material from one character to another, or
    copying a surface finish between props of the same type.

    Args:
        source_node: Display label of the node that owns the source material.
        source_material_name: Label or name of the source material slot
            (e.g. ``"Skin"`` or ``"1_SkinFace"``).
        dest_node: Display label of the node that owns the destination material.
        dest_material_name: Label or name of the destination material slot.

    Returns:
        Dict with keys:
        - success: true on success
        - source: "NodeLabel/MaterialLabel" for the source
        - destination: "NodeLabel/MaterialLabel" for the destination
        - properties_copied: number of properties successfully copied
        - properties_skipped: number of properties not found on the destination

    Examples:
        daz_copy_material("Genesis 9", "Skin", "Clone 1", "Skin")
        daz_copy_material("Hero Suit", "Metal", "Villain Suit", "Metal")
    """
    return await _execute_by_id(
        "vangard-copy-material",
        {
            "sourceNodeLabel": source_node,
            "sourceMaterialName": source_material_name,
            "destNodeLabel": dest_node,
            "destMaterialName": dest_material_name,
        },
    )
