# Skill: Scene Architect
Tools for scene layout, hierarchy, and library management.

## Scene & Hierarchy
- `daz_scene_info`: Snapshot of the scene.
- `daz_get_node_hierarchy`: Skeleton/tree mapping.
- `daz_set_parent`: Attaching props or organizing the tree.
- `daz_get_scene_layout`: Full spatial map.

## Batch Operations (Performance)
Use these for 5-10x speedup when changing 3+ items:
- `daz_batch_set_properties`, `daz_batch_transform`, `daz_batch_visibility`, `daz_batch_select`.

## Spatial Analysis
- `daz_get_world_position`, `daz_get_bounding_box`.
- `daz_check_overlap`: Collision/penetration detection.
- `daz_find_nearby_nodes`: Find items within a radius.

## Content Library
- `daz_list_categories`, `daz_browse_category`: Navigating `.duf` files.
- `daz_search_content`: Keyword search across the library.
- `daz_load_file`, `daz_load_product`: Load by path or product name.
- `daz_check_compatibility`: Verify an asset works with a given figure.

## Materials
- `daz_list_materials`, `daz_get_material`: Inspect surfaces on a node.
- `daz_set_material_property`: Set a surface property (color, reflectivity, etc.).
- `daz_apply_material_preset`, `daz_copy_material`: Apply presets or clone surfaces.
- `daz_convert_to_iray_uber`: Fix content that lands as legacy `DzDefaultMaterial` instead of
  `DzUberIrayMaterial` (common after merging raw/hand-authored `.duf` content) — see
  SKILL_DAZSCRIPT.md's "Materials — DzDefaultMaterial vs DzUberIrayMaterial" for why this happens
  and why the fix goes through shader-preset application rather than editing channel data.

## Scene Utilities
- `daz_save_scene`, `daz_save_scene_copy`: Save current or copy scene.
- `daz_get_selected_nodes`: Query current DAZ Studio selection.
- `daz_delete_node`: Remove a node from the scene.
