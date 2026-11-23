# Skill: Character Choreographer
Tools for morphs, emotions, and movement. The tools named here are in the
`expert` profile (`DAZ_MCP_PROFILE=expert`); each tool's own description lists
its exact arguments and values.

## Morph Discovery
- `daz_list_morphs`: Use `include_zero=False` to see active morphs.
- `daz_search_morphs`: Pattern match (e.g., "smile", "muscle").
- `daz_set_morph`: Set a single morph by name and value.
- `daz_load_morph_pro`: Import a new OBJ morph target via Morph Loader Pro (load mode,
  mirroring, overwrite mode, reverse deformations, subdivision, attenuation maps, ERC
  control-property linking). See daz://guide/dazscript's "Morph Loader Pro" gotchas.

## Emotional Direction
- `daz_set_emotion`: Expression plus a small body adjustment, scaled by `intensity`: `happy`, `sad`, `angry`, `surprised`, `fearful`, `disgusted`, `neutral`, `excited`, `bored`, `confident`, `shy`, `loving`, `contemptuous`.
- `daz_set_body_language`: Upper-body posture (`confident`, `defensive`, `relaxed`, `tense`).
- `daz_direct_gaze`: Turn the head toward `camera`, `away`, `up`, `down`, `left`, `right`, or `character` (with `target_label`).
- These handle the bone and morph naming differences between Genesis 8 and 9.

## Posing & Interaction
- `daz_look_at_character`, `daz_look_at_point`: Cascading rotation (eyes to torso, by `mode`). Rotations are absolute and clamp to the bones' limits (Genesis head twist ±22°).
- `daz_reach_toward`: Pseudo-IK for arms.
- `daz_interactive_pose`: Two-character poses: `face-each-other`, `hug`, `shoulder-arm`, `handshake`.
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
- `daz_arrange_characters`: Formations (`line`, `semicircle`, `triangle`, `conversation-circle`).
- `daz_choreograph_action`: Coordinated two-character actions (`handshake`, `hug`, `fight`, `dance`).
