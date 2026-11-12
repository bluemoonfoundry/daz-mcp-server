# Skill: Character Choreographer
Tools for morphs, emotions, and movement.

## Morph Discovery
- `daz_list_morphs`: Use `include_zero=False` to see active morphs.
- `daz_search_morphs`: Pattern match (e.g., "smile", "muscle").
- `daz_set_morph`: Set a single morph by name and value.
- `daz_load_morph_pro`: Import a new OBJ morph target via Morph Loader Pro (load mode,
  mirroring, overwrite mode, reverse deformations, subdivision, attenuation maps, ERC
  control-property linking). See SKILL_DAZSCRIPT.md's "Morph Loader Pro" gotchas.

## Emotional Direction
- `daz_set_emotion`: Apply `happy`, `angry`, `confident`, etc., with `intensity`.
- `daz_set_body_language`: Full-body posture archetypes (`confident`, `defeated`, `alert`, `relaxed`).
- `daz_direct_gaze`: Eye-direction control (`camera`, `up`, `down`, `left`, `right`, `away`).
- Handles naming differences between Genesis 8 and 9.

## Posing & Interaction
- `daz_look_at_character`, `daz_look_at_point`: Cascading rotation (eyes to torso).
- `daz_reach_toward`: Pseudo-IK for arms.
- `daz_interactive_pose`: Pre-built handshake, hug, or fight spacing.
- `daz_reset_pose`: Clear all pose values to default.
- `daz_save_pose` / `daz_load_pose`: Save/restore figure poses to/from file.

## Wardrobe & dForce
- `daz_list_fitted_items`: See what clothing/hair is fitted to a figure.
- `daz_fit_clothing` / `daz_unfit_item`: Attach or detach clothing.
- `daz_run_dforce_simulation`: Run cloth physics simulation.
- `daz_bake_simulation`: Bake sim results; `daz_set_dforce_property` to tune parameters.
- `daz_get_figure_info`, `daz_set_subdivision`: Diagnostics and mesh LOD.
- `daz_export_fbx`, `daz_export_obj`: Export figure/scene to interchange formats.

## Action & Pathing
- `daz_create_character_path`: Animate walking with auto-rotation.
- `daz_arrange_characters`: Formations (semicircle, circle, line).
- `daz_choreograph_action`: Coordinated multi-character sequences.
