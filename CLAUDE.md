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
- **Version:** 0.4.0
- **Bridge:** Connects to DazScriptServer (port 18811)
- **Registry:** 138 tools registered across 13 tool modules.
- **Structure:** Modular — `_mcp.py` holds shared FastMCP instance; `tools/__init__.py` imports all 13 modules so `@mcp.tool()` decorators fire at import time.
- **Phase 4.8:** Lighting Animation — `daz_animate_light`, `daz_create_light_sequence`
- **Phase 4.9:** Shot Planning — `daz_plan_shot`, `daz_create_storyboard`
- **Phase 4.10:** Focus & DOF — `daz_set_focus_point`, `daz_animate_focus_pull`
- **Phase 4.11:** Visual Composition — `daz_set_scene_atmosphere`, `daz_apply_visual_style`
- **Phase 4.12:** Multi-Scene Management — `daz_export_node_config`, `daz_import_node_config`
- **Phase 4.13:** Performance Timing — `daz_time_expression`, `daz_sync_character_beats`
- **Phase 5:** Gap Coverage — `daz_list_materials`, `daz_get_material`, `daz_set_material_property`, `daz_set_morph`, `daz_delete_node`, `daz_list_lights`, `daz_create_light`, `daz_list_cameras`, `daz_create_camera`, `daz_save_scene`, `daz_get_selected_nodes`, `daz_set_render_output`, `daz_reset_pose`
- **Phase 6.1:** Wardrobe — `daz_list_fitted_items`, `daz_fit_clothing`, `daz_unfit_item`
- **Phase 6.2:** dForce Simulation — `daz_run_dforce_simulation`, `daz_bake_simulation`, `daz_set_dforce_property`
- **Phase 6.3:** Pose Library — `daz_save_pose`, `daz_load_pose`
- **Phase 6.4:** Material Preset — `daz_apply_material_preset`, `daz_copy_material`
- **Phase 6.5:** Figure Diagnostics — `daz_get_figure_info`, `daz_set_subdivision`
- **Phase 6.6:** Scene Export — `daz_export_fbx`, `daz_export_obj`
- **Phase 6.7:** Shader-class fixup — `daz_convert_to_iray_uber` (fixes content that lands as
  legacy `DzDefaultMaterial` instead of `DzUberIrayMaterial` after a raw/merged `.duf` import)

## Render API (DazScriptServer native endpoints)
`daz_render_async`, `daz_render_with_camera_async`, `daz_batch_render_cameras_async` use
`POST /render` and `POST /render/batch` directly (not the script registry). Render IDs have
prefix `rnd-`; `daz_cancel_request` routes these to `POST /render/:id/cancel` automatically.
`daz_render_batch` — new: submit up to 100 variants with per-variant morph overrides.


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:6cd5cc61 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->
