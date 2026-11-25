# Changelog

All notable changes to daz-mcp-server are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

Requires dazpy 2.17.0 or later (`DazNode.set_numeric_candidates`,
`DazSkeleton.set_bone_axes`/`bone_names`, `DazScene.viewport_camera`).

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

### Fixed

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
