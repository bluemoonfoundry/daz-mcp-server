# Skill: MCP Systems Architect
Technical documentation for server internals and the MCP bridge. For humans and
coding agents working on this repository; the AI using the server gets the
bundled guides (`daz://guide/<name>`) and the tool descriptions instead.

## Communication Flow
`MCP client → FastMCP → dazpy (AsyncDazClient / DazClient) → DazScriptServer (18811) → DAZ Studio`

The content browser (`DAZ_CONTENT_BROWSER_URL`) is a separate service, reached with plain httpx.

## Module Layout
- `server.py` — entry point (`main()` runs stdio); imports `_mcp` then `tools`, applies the profile, re-exports every tool function
- `_mcp.py` — shared `FastMCP` instance, lifespan, `_execute*` / `_execute_render*` helpers
- `_client.py` — dazpy client/scene singletons (`get_daz_client`, `get_async_daz_client`, `get_scene`), `run_dazpy`, env config (`DAZ_HOST`, `DAZ_PORT`, `DAZ_TIMEOUT`, `DAZ_API_TOKEN`, `DAZ_CONTENT_BROWSER_URL`)
- `_errors.py` — `handle_dazpy_error()`: maps every dazpy exception to one well-formed `ToolError`
- `_registry.py` — `_register_scripts()` with all pre-registered script payloads
- `_profile.py` — `compact` / `expert` tool visibility (`DAZ_MCP_PROFILE`)
- `_guides.py` + `guides/*.md` — the bundled agent guides served as `daz://guides` / `daz://guide/<name>`
- `_compat.py` — plugin compatibility reporting (`plugin_compatibility` in `daz_status` / `daz_inspect_scene`)
- `_shots.py` — scene lookups and result helpers for the cinematic tools (shots themselves come from `dazpy.shot_library`)
- `_emotions.py`, `genesis_bones.json` — emotion definitions and per-generation bone names
- `_ui_automation.py` — Windows UI Automation for `daz_save_wearable_preset`
- `tools/__init__.py` — imports all 16 tool modules (165 tools total)
- `tools/<module>.py` — each module imports `mcp` from `_mcp` and registers `@mcp.tool()` functions

## Adding a New Tool
1. Pick the appropriate module in `tools/` (or create a new one and add it to `tools/__init__.py`)
2. Import `mcp` from `.._mcp` and decorate with `@mcp.tool()`. Only tools tagged
   `default` (`@mcp.tool(tags=_DEFAULT_TAG)`, see `tools/workflow.py`) appear in the `compact` profile; add a tool there only deliberately
   (`tests/test_workflow_profile.py` pins that list).
3. Implement it with dazpy inside a sync `_run()` passed to `run_dazpy()` (or `_shots.run()`
   for shot tools), or with a registered script via `_execute_by_id()`
4. If using a registered script, add its payload to `_registry.py`
5. The tool's docstring is its MCP description: list every argument and its valid values there
6. Update the tool counts (README, CLAUDE.md, this file) and the guide that covers the area;
   `tests/test_version_consistency.py` and `tests/test_guides.py` check them

## Script Registry System
- **Registration:** `_register_scripts()` runs at startup via lifespan.
- **Execution:** Uses `POST /scripts/:id/execute` for performance.
- **Auto-Retry:** On 404 (DAZ restart), the server re-registers and retries the call once.

## Testing Standards
- Mock at the boundary: `respx` for HTTP-level tests, or fake scene/client objects via
  `monkeypatch` for dazpy-routed tools (see `tests/test_cinematic_shots.py`).
- Tests call tool functions directly (e.g., `await daz_status()`), imported from their
  module (e.g., `from daz_mcp_server.tools.utility import daz_status`).
- Run the unit suite the way CI does: `uv run pytest tests/ -m "not integration and not slow" -q`.
  `addopts` only excludes `slow`, so a bare `pytest tests/` **also runs the integration
  tests** whenever DAZ Studio is reachable. A `pytest_collection_modifyitems` hook in
  `tests/conftest.py` auto-tags any test using a live-DAZ fixture (`live_client`,
  `figure_label`, etc.) with `integration`, so `-m "not integration"` reliably excludes it
  (Bug-Katalog #19). Run `-m slow` / `-m integration` explicitly and only against a scene
  you can afford to have modified.

## Macros & Checkpoints
- `daz_start_recording` / `daz_stop_recording`: Session-based macro storage.
- `daz_save_scene_state`: Checkpoint transforms/morphs/lights in server memory.
