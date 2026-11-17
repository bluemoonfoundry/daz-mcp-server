# Changelog

All notable changes to daz-mcp-server are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
