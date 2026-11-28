# Changelog

All notable changes to daz-mcp-server are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

Requires dazpy 2.17.0 or later, for the new primitives these tools use
(node references, property search, material, keyframe and pose helpers).

### Added

- **`desktop` tool profile** (`DAZ_MCP_PROFILE=desktop`) for Claude Desktop and
  other clients that cannot write files on the DAZ Studio machine. The compact
  job tools need a `.dsa` file that already exists there, so in Claude Desktop
  (whose scripts live in its own sandbox) `daz_run_script_job` failed with a
  path DAZ Studio could not see. `desktop` keeps every compact tool and adds
  `daz_execute`, two new tools, `daz_submit_script` (queue inline DazScript as
  a job) and `daz_write_script` (DAZ Studio saves a `.dsa` under its temp
  folder and returns the path for `daz_run_script_job`), plus
  `daz_script_help`, `daz_validate_script`, `daz_explain_last_error`,
  `daz_status` and read-only scene tools. `compact` is unchanged; `expert` now
  lists 167 tools. The README's Claude Desktop config uses `desktop`.
- Scene recipe v2 in the recipe tools: asset references (`path`, `product`,
  `sku`, `find`, `file`, `type`, `resolved`), actor `node` take-over,
  `presets` and `wearing`. `daz://recipe/schema` now serves the v2 schema
  (`daz://recipe/schema/1` still serves v1). `find` uses the content browser
  when `DAZ_BROWSER_URL` is set and reachable, otherwise Studio's search.

### Changed

- `daz_set_emotion`, `daz_set_body_language` and `daz_direct_gaze` are built
  on dazpy primitives and send no DazScript of their own. The registered
  `vangard-set-emotion` script is removed.
- `daz_set_emotion` uses the figure's stock full-face expression controller
  (Genesis 9 `facs_ctrl_Happy`, Genesis 8 `eCTRLHappy_HD`, ...) when it has
  one, otherwise the per-feature dials, and resets the other emotions' face
  controllers first so expressions don't stack. `neutral` clears them. The
  result adds `body_not_found`.
- `daz_direct_gaze` with `direction="character"` aims at the target figure's
  head instead of its root (feet). The result adds `requested`, and
  `applied` now reports the rotation the head kept after its joint limits.
- Node tools use dazpy and accept an elementID or `Parent/Label` path
  anywhere a node label is taken. An ambiguous label is an error that lists
  the candidates' elementIDs. Covered: `daz_get_node`, `daz_find_nodes`,
  `daz_set_property`, `daz_delete_node`, `daz_set_parent`, `daz_set_morph`,
  `daz_list_morphs`, `daz_search_morphs`, `daz_get_node_hierarchy` and the
  material and keyframe tools.
  - `daz_get_node` also returns modifier-stack properties (morph dials). The
    old script meant to, but its dedupe kept only one, because every morph
    channel is named `Value`.
  - Property and morph names match case-insensitively.
  - `daz_set_parent(node, "Scene")` un-parents the node. It used to fail with
    "Node not found: Scene".
- `daz_scene_info`, `daz_load_file(merge=False)` and the checkpoint tools use
  dazpy.
  - Replace-mode load clears the scene and then merges, so Studio's "save
    changes?" prompt can't block the server.
  - `daz_save_scene_state`/`daz_restore_scene_state` use `DazSceneState`.
    They now restore bone rotations and fit-to targets too, check each
    figure after restoring, and report `skipped` and `complete`. `restored`
    lists internal node names.
- The material tools use dazpy. A missing-zone error lists the available
  zones, and `daz_set_material_property` reports the value Studio kept.
- `daz_batch_set_properties`, `daz_inspect_properties`,
  `daz_get_property_metadata`, `daz_validate_scene` and
  `daz_auto_improve_scene` use dazpy. Batch set is still one Studio call.
  `is_animatable` is now right (it was always `false`: the old scripts
  called a non-existent `isAnimatable()`).
- `daz_validate_scene` takes lighting and framing from dazpy's
  `DazScene.check`. Changes:
  - It no longer reports collisions between a figure and its own eyelashes,
    tear or mouth (it now checks top-level figures only).
  - It no longer misreads the environment from `Scene.getNode(1)`.
  - Issue types for lighting/framing are dazpy check codes (`no_light`,
    `subject_out_of_frame`, ...) and the raw findings are in `findings`.
  - `summary.environment_lighting` is replaced by `summary.lit`.
  - `daz_auto_improve_scene` now adds the missing light. It looked for an
    issue type validate never emitted.
- `daz_look_at_point`, `daz_look_at_character`, `daz_reach_toward` and
  `daz_reset_pose` use dazpy (`DazSkeleton.look_at`, `hand_to_target`,
  `set_bone_rotations`).
  - Look-at aims in each bone's own frame. It used to turn heads down when
    the target was up, ignore the figure's facing, and push Genesis 8/9
    eyes (oriented 180° about Z) the wrong way. Genesis 9's upper chest is
    `spine4`, not `spine3`.
  - Results add `rotations` (the angles each bone kept). `rotatedBones`
    lists internal bone names.
  - `daz_reach_toward` reports `converged`, `finalError` and `iterations`
    instead of `targetDistance`.
- The camera and light tools use dazpy: set active camera, orbit, frame,
  camera presets, list/create lights and cameras, lighting presets, mood
  and time of day.
  - `daz_set_active_camera` also accepts Studio's built-in view cameras
    ("Perspective View", ...).
  - `daz_set_mood_lighting` and `daz_apply_time_of_day` now set the light
    color. They wrote to a "Diffuse Color" property that Studio lights
    don't have.
  - `daz_apply_lighting_preset` sets Scene Only on the real environment
    node (on Studio 4 and 6) instead of on whatever node was second in the
    scene. When no environment node exists yet, it says so.
- The sync render tools (`daz_render`, `daz_render_with_camera`,
  `daz_batch_render_cameras`, `daz_render_animation`) submit through
  dazpy's `/render` and `/render/animation` endpoints, wait for the
  request, and return `request_id` and `result`. A camera render switches
  the viewport back to its previous camera afterwards.
  `daz_render_animation_async` moves to `/render/animation` too. Settings
  tools use `DazRenderSettings`.
  - `daz_set_render_quality` applies dazpy's quality presets (for example,
    "good" is 1500 samples, not 2000). It also sets Max Time and the
    Rendering Quality toggle. The old script wrote a "Render Quality"
    property that doesn't exist.
  - `daz_get_render_settings` returns `engineState` (dazpy's verified
    engine readback) and drops `aspectRatio`/`aspectWidth`/`aspectHeight`/
    `renderType`.
- The animation render tools default to the scene's animation range in
  frames. The old script read DzTime ticks as frame numbers, so a default
  range meant thousands of renders.
- Wardrobe tools on dazpy: `daz_list_fitted_items`, `daz_fit_clothing`,
  `daz_unfit_item`, `daz_get_figure_info`, `daz_set_subdivision`,
  `daz_run_dforce_simulation`, `daz_export_fbx` and `daz_export_obj`.
  - `daz_set_subdivision` sets the mesh's View SubD Level. It always failed
    on Genesis 8/9: it searched the figure for a "SubDivision Level"
    property, but the level lives on the mesh shape. The result adds
    `render_level`.
  - `daz_run_dforce_simulation(node_label)` simulates only that node. It
    used to just select the node and simulate the whole scene.
  - Export errors (missing exporter, write failure) are now reported.
    `exported_nodes` is `["(whole scene)"]` when no nodes are named.
- The dForce and Transfer Utility tools use dazpy:
  `daz_add_dforce_dynamic_surface`, `daz_get/set_dforce_influence_weights`,
  `daz_set_dforce_property`, `daz_get/set_dforce_surface_property(ies)`,
  `daz_bake_simulation` and `daz_run_transfer_utility`.
  - `daz_bake_simulation` now works: it freezes the node's dForce modifiers,
    or every one in the scene. It always failed before, because it called
    bake methods `DzSimulationMgr` doesn't have. The result reports
    `method: "freeze"` and `modifiers_frozen`.
- `daz_export_node_config` / `daz_import_node_config` use dazpy. Import
  applies the whole file in one Studio call.
- `daz_time_expression` and `daz_sync_character_beats` key the stock
  full-face controller (or the feature dials) and the body bones on dazpy.
  This fixes three bugs: frames were used as DzTime ticks, body bones were
  never found (they were looked up only among the figure's direct
  children; daz-mcp-server-onf), and expression names missed stock
  Genesis 8/9 controls. Results add `bodyNotFound`.
- `daz_animate_light`, `daz_create_light_sequence`,
  `daz_set_scene_atmosphere` and `daz_apply_visual_style` use dazpy (new
  module `_cinematic_lighting.py`). Fixes:
  - Light keys land on real frames; they used DzTime ticks.
  - `color-cycle` now animates the light's Color. It keyed "Color/Red"
    etc., which don't exist, and silently fell back to flux.
  - Atmosphere and visual style set the real environment node instead of
    `Scene.getNode(1)`. Without an environment node they say so instead
    of failing silently.
  - The environment mode names are corrected: 0 Dome and Scene, 1 Dome
    Only, 2 Sun-Sky Only, 3 Scene Only.
  - Visual-style lights are aimed with `aimAt`.
- `daz_arrange_characters` and `daz_create_character_path` use dazpy (new
  module `_cinematic_staging.py`).
  - Arranging places every character in one batched call.
  - `facing="camera"` now turns characters toward the active viewport
    camera; it used to just set rotation 0.
  - Paths key real frames; they used DzTime ticks.
- `daz_animate_conversation` uses dazpy.
  - The speaker's emotion uses the shared emotion definitions, so stock
    Genesis 8/9 face controllers resolve.
  - The listener's neck and head turn toward the speaker's head through
    `DazSkeleton.look_at`, keyed at the beat's start and end frames. The
    old script keyed DzTime ticks and aimed with world angles.
- `daz_interactive_pose` stages pairs with dazpy interaction recipes:
  face-each-other, hug, handshake, and shoulder-arm (a touch recipe). The
  hand/foot targets are solved per figure generation. The old script
  hard-coded Genesis 8 arm bones (`rShldrBend`, ...), so its arm poses did
  nothing on Genesis 9. The result adds `alignment` (each limb target's
  convergence).
- `daz_choreograph_action` places the pair facing each other at the
  action's spacing through dazpy's batched staging.
- `daz_create_scene` builds its blocking and lights with dazpy, so no
  cinematic tool sends DazScript any more.
  - Template lights are reused by label instead of duplicated each run.
  - A missing character is skipped and reported; it used to stop the
    template.
  - The first `actions` entry is now `Scene type: <type>`.
- `daz_list_categories`, `daz_browse_category`, `daz_save_prop_asset`,
  `daz_load_morph_pro` and `daz_list_strand_hair_nodes` use dazpy.
- `daz_create_strand_hair(auto_confirm=True)` clicks Studio's "Create New
  Strand-Based Hair" dialog through Windows UI Automation, waits, and
  returns the finished result. It needs `pywinauto` on the DAZ Studio
  machine. The default (`auto_confirm=False`) still returns a `request_id`
  for a human to confirm. The dialog driver is ported from the blackbyte
  fork, commit 2ba9a37.
- Five tools stay on registered scripts on purpose, with a code comment
  saying why:
  - `daz_save_wearable_preset` and `daz_create_strand_hair` open Studio
    dialogs.
  - `daz_erc_freeze` needs an ERC editing API dazpy doesn't have.
  - `daz_find_actions` searches DzActionMgr, which dazpy doesn't cover.
  - `daz_load_file` for OBJ uses the silent unit-scale importer.
  `daz_execute`, `daz_execute_file(_async)` and `daz_validate_script` run
  your own script by design.
- `daz_get_animation_info` and the spatial tools (`daz_get_scene_layout`,
  `daz_find_nearby`) no longer send inline DazScript; they use dazpy's
  `time_step()` and typed `all_node_transforms()`.
- 102 registered scripts are removed (107 to 5), and a unit test fails if any
  registered script is no longer called by a tool.

### Fixed

- **`daz_execute`'s `args` did not exist in the script.** The tool documented
  its `args` as an `args` variable, but the plugin passes arguments only through
  `getArguments()[0]`, so any script reading `args` failed with
  `ReferenceError: Can't find variable: args`. `daz_execute` (and the new
  `daz_submit_script`) now define `args` on the script's first line, so error
  line numbers are unchanged. The descriptions also say that a top-level
  `return` is a syntax error (wrap the script in an IIFE or end with an
  expression), and `daz_execute_file` says a file reads `getArguments()[0]`.

- `daz_set_emotion` did almost nothing on stock Genesis 8 and 9: its morph
  names matched no dial on either figure, and its body adjustment never found
  `chestUpper`, which only looked at the figure's direct children
  (daz-mcp-server-3oq).
- `daz_set_body_language` posture bones (`lShldr`, `chestUpper`, ...) are
  matched per figure generation, so postures apply on Genesis 8 and 9
  (daz-mcp-server-7w8).
- `daz_direct_gaze` with `direction="camera"` always failed:
  `Scene.getActiveCamera` doesn't exist. It now uses the active viewport
  camera, including Studio's built-in Perspective View. The neck fallback
  also finds Genesis 9's `neck2` (daz-mcp-server-w88).
- The keyframe tools (`daz_set_keyframe`, `daz_get_keyframes`,
  `daz_remove_keyframe`, `daz_clear_animation`) used the frame number as a
  DzTime tick count, so "frame 30" was keyed at frame 0.19 (Studio runs at
  160 ticks per frame). Frames are now converted, and `daz_get_keyframes`
  reports real frames.

## [0.10.0] - 2026-11-24

Requires dazpy 2.16.0 or later.

### Changed

- `daz_plan_shot`, `daz_create_storyboard`, `daz_create_camera_rig` and
  `daz_create_camera_path` are built on `dazpy.shot_library`, and their
  four DazScript programs are removed. `daz_create_scene` keeps its script
  for lights and blocking but builds its cameras with dazpy. Behaviour
  changes:
  - `daz_plan_shot` returns the planned `shot` (`Shot.to_dict()`); its camera
    stands on the subject's front (it used to be behind it), fits the shot
    type's lens, and two-shot / over-shoulder pair with the nearest figure.
  - `daz_create_storyboard` cameras face the subject's front (`angle` 0 =
    `+Z`), a reused camera is re-aimed, `partnerLabel` picks the second
    figure for two-shot / over-shoulder, snake_case shot keys are accepted,
    and the result adds `sequence` (`Sequence.to_dict()`) and `cameras`.
    A missing `subjectLabel` is an error instead of framing the origin.
  - `daz_create_camera_rig` aims every camera exactly at the centre and reuses
    the rig and its cameras when run again with the same `rig_name`. Its
    `<name>_Rig` group is made with `DazScene.create_group`, so the
    cinematic tools send no inline DazScript of their own.
  - `daz_create_camera_path` with `aim_at_target` aims at the target on every
    waypoint (it used to aim once); it clears the camera's existing position
    keys first and rejects duplicate waypoint frames. `easing` is still not
    applied (Studio's default interpolation).
  - `daz_create_scene` cameras are labelled with shot ids, conversation
    cameras keep the 180-degree rule (`continuity` in the result), and no
    cameras are made without a character. Dining characters now face each
    other (they faced away) and "dining" is recognised as a keyword.
- Shot framing uses dazpy 2.16.0's frame geometry: Studio's Frame Width
  spans the frame height, not the width. Shot sizes used to stand 1/aspect
  too far back (33% too loose at 4:3), and `daz_apply_composition_rule`'s
  thirds and golden-section placements were off by the same factor.

## [0.9.0] - 2026-11-22

Requires dazpy 2.15.0 or later.

### Added

- `daz_cover_conversation`: cut a two-person conversation from dialogue beats
  (`{speaker, start, end, line}`), one over-the-shoulder or single shot per
  beat with an optional opening master, or set up master / two-shot / OTS /
  singles coverage when no beats are given. Built on
  `dazpy.shot_library.conversation` / `dialogue_coverage` / `check_plan`;
  returns the cameras, the cut list and any continuity issues.

### Changed

- The camera and shot tools now build their shots with `dazpy.shot_library`
  instead of carrying their own DazScript: `daz_create_shot_sequence`,
  `daz_setup_shot_coverage`, `daz_animate_camera_movement`,
  `daz_set_focus_point`, `daz_animate_focus_pull`, `daz_frame_shot`,
  `daz_apply_camera_angle` and `daz_apply_composition_rule`. Requires dazpy
  2.15.0 or later. Behaviour changes:
  - Shot/reverse-shot cameras stay on one side of the line between the two
    characters (180-degree rule) and frame the speaker on a third over the
    listener's shoulder; new `side` argument picks the side, and the result
    reports any `continuity` issue.
  - Shots fit their size to the camera's lens; cameras are labelled with
    consistent shot ids (`WS_Alice`, `OTS_Bob_over_Alice`, ...). Coverage
    cameras face the subject's front (they used to stand behind it).
  - `pan-right` / `tilt-up` turn the way their names say (they were
    reversed), moves start from the camera's true world pose, and
    handheld shake is repeatable.
  - `daz_apply_camera_angle("dutch-angle")` rolls about the lens axis and
    keeps the aim; `daz_set_focus_point`'s `dofPreview` uses the hyperfocal
    formula (`nearSharp` / `farSharp`).
  - `daz_setup_shot_coverage(camera_height=...)` is now optional: the aim
    height for every shot; by default each size uses its own.

### Fixed

- `daz_batch_select(add_to_selection=False)` replaces the current selection
  as documented; it used to add to it.
- `daz_get_scene_layout` and `daz_find_nearby_nodes` apply `include_types`
  (it was accepted and ignored). Each entry now has a `type`: `figures`,
  `wearables` (follower figures such as clothing), `bones`, `cameras`,
  `lights` or `props`; an unknown type is an error.
- The bundled guides (`daz://guide/<name>`) match the tools again: corrected
  option lists (body-language postures, gaze directions, interaction and
  formation types, mood lighting, camera angles and moves), dropped
  limitations that no longer apply (`daz_look_at_point` direction,
  `daz_render_with_camera_async`), pointed portrait work at `daz_frame_shot` /
  `daz_set_focus_point`, noted which tools need the `expert` profile, and
  removed a personal project path. A test now checks that every tool and
  example argument a guide names exists.

## [0.8.0] - 2026-11-16

First release on PyPI. Run it with `uvx daz-mcp-server`.

### Changed

- **Renamed** from `vangard-daz-mcp` to `daz-mcp-server`: the PyPI package,
  the `daz-mcp-server` command, the `daz_mcp_server` import package and the
  MCP server name. Update your MCP client config (see "Migrating from
  vangard-daz-mcp" in the README); the old command no longer exists.
- Requires dazpy 2.13.0 or later.

### Added

- Agent guides ship in the package and are served as the `daz://guides` and
  `daz://guide/<name>` resources (`actors`, `cinema`, `daz_studio`,
  `dazscript`, `recipe`, `scene`), and through `daz_script_help("guides")` /
  `daz_script_help("guide:<name>")`. Tool descriptions point at them by URI.
- Plugin compatibility reporting: when the Daz Studio plugin at
  `DAZ_HOST:DAZ_PORT` is older than dazpy needs, `daz_status` and
  `daz_inspect_scene` report `plugin_compatibility` with upgrade advice, tool
  errors from missing plugin routes add the same advice, and the MCP client log
  gets one warning. A plugin upgrade is noticed without restarting the server.
- CI runs the unit tests, pylint and a built-wheel smoke test on every push and
  pull request; pushing a `vX.Y.Z` tag publishes to PyPI and creates the
  GitHub release.

### Removed

- A personal file path from the BVH `daz_load_file` error message.

## [0.7.0]

See "Changes in 0.7.0" in the README.
