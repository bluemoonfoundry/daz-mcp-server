# Changelog

All notable changes to daz-mcp-server are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.9.0] - Unreleased

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
