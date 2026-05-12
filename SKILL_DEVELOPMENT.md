# Skill: MCP Systems Architect
Technical documentation for server internals and the MCP bridge.

## Communication Flow
`MCP client → FastMCP → httpx.AsyncClient → DazScriptServer (18811) → DAZ Studio`

## Script Registry System
- **Registration:** `_register_scripts()` runs at startup.
- **Execution:** Uses `POST /scripts/:id/execute` for performance.
- **Auto-Retry:** On 404 (DAZ restart), the server re-registers and retries the call.

## Testing Standards
- Use `respx` for HTTP transport mocking.
- Tests call tool functions directly (e.g., `await daz_status()`).
- All new tools must be added to the `_REGISTRY` constants.

## Macros & Checkpoints
- `daz_start_recording` / `daz_stop_recording`: Session-based macro storage.
- `daz_save_scene_state`: Checkpoint transforms/morphs/lights in server memory.
