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
- `daz_load_file`: Merging content into the scene.
