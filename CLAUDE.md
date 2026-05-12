# CLAUDE.md (Project Index)

## Primary Commands
- `uv sync` - Install dependencies
- `uv run pytest tests/ -v` - Run all tests
- `uv run vangard-daz-mcp` - Run the MCP server

## Skill Modules (Reference with @)
- **@SKILL_DEVELOPMENT.md**: Server architecture, MCP registry, and testing.
- **@SKILL_DAZSCRIPT.md**: DazScript environment, globals, syntax rules, and "gotchas."
- **@SKILL_SCENE.md**: Scene layout, hierarchy, batch operations, and content browsing.
- **@SKILL_ACTORS.md**: Morphs, emotions, posing, interaction, and character movement.
- **@SKILL_CINEMA.md**: Cameras, lighting, animation, shot composition, and rendering.

## Architecture Summary
- **Version:** 0.3.0
- **Bridge:** Connects to DazScriptServer (port 18811)
- **Registry:** 89 tools registered for high-performance execution.
- **Phase 4.8:** Lighting Animation — `daz_animate_light`, `daz_create_light_sequence`
- **Phase 4.9:** Shot Planning — `daz_plan_shot`, `daz_create_storyboard`
- **Phase 4.10:** Focus & DOF — `daz_set_focus_point`, `daz_animate_focus_pull`
- **Phase 4.11:** Visual Composition — `daz_set_scene_atmosphere`, `daz_apply_visual_style`
- **Phase 4.12:** Multi-Scene Management — `daz_export_node_config`, `daz_import_node_config`
- **Phase 4.13:** Performance Timing — `daz_time_expression`, `daz_sync_character_beats`
- **Phase 5:** Gap Coverage — `daz_list_materials`, `daz_get_material`, `daz_set_material_property`, `daz_set_morph`, `daz_delete_node`, `daz_list_lights`, `daz_create_light`, `daz_list_cameras`, `daz_create_camera`, `daz_save_scene`, `daz_get_selected_nodes`, `daz_set_render_output`, `daz_reset_pose`
