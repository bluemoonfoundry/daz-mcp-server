# daz-mcp-server Release Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship daz-mcp-server 0.8.0 to PyPI under one name (`daz-mcp-server`), self-sufficient for `uvx`, with CI, a tag-driven release, and plugin-compatibility reporting built on dazpy 2.13.

**Architecture:** Rename first (everything later uses the new names). Then packaging hygiene, bundled guides served as MCP resources, a small `_compat` module fed by dazpy's `on_version_check` callback, and two GitHub workflows (`ci.yml`, `release.yml`) modelled on daz-script-server's `release-tagged.yml`.

**Tech Stack:** Python ≥3.11, uv, hatchling, FastMCP 3.0.1, dazpy 2.13.0, pytest + respx, GitHub Actions, PyPI Trusted Publishing.

**Spec:** `docs/superpowers/specs/2026-11-16-mcp-release-architecture-design.md`

## Global Constraints

- Names: distribution `daz-mcp-server`, import package `daz_mcp_server`, console command `daz-mcp-server`, FastMCP server name `"daz-mcp-server"`. No `vangard` alias anywhere in the shipped package.
- First release version: `0.8.0`.
- `pyproject.toml` `authors = [{name = "Blue Moon Foundry"}]` — no email.
- Dependency: `dazpy>=2.13.0` from PyPI (no path/editable source in `uv.lock`).
- Env vars unchanged: `DAZ_HOST`, `DAZ_PORT`, `DAZ_API_TOKEN`, `DAZ_TIMEOUT`, `DAZ_CONTENT_BROWSER_URL`, `DAZ_MCP_PROFILE`.
- PyPI Trusted Publishing: workflow file `release.yml`, GitHub environment `pypi` (must match the pending publisher exactly).
- **Daz Studio may be running.** Only ever run `uv run pytest tests/ -m "not integration and not slow"` (plus single named unit test files). Never a bare `pytest tests/`.
- The server starts regardless of plugin version; a too-old plugin is reported, never blocked.
- Every push, PR, merge and tag waits for the user's explicit go-ahead.

## Review Focus

1. `uvx daz-mcp-server` from the built wheel in a clean venv: tools register, guides and data files load (Task 3 wheel test, Task 5 CI smoke).
2. A user's existing MCP config still pointing at `vangard-daz-mcp` → fails clearly; README/CHANGELOG migration snippet is exact (Task 6 doc check).
3. Plugin too old while using only the compact profile (no `daz_status` visible) → `daz_inspect_scene` and 404-type tool errors still carry the upgrade note (Task 4 tests).
4. Plugin upgraded and Studio restarted mid-session → note disappears without restarting the MCP server (Task 4 test with a second, compatible `VersionCheck`).
5. Tag that doesn't match `pyproject.toml` → release workflow fails before publishing (Task 6 script test).

---

### Task 1: Rename to `daz-mcp-server`

**Files:**
- Move: `src/vangard_daz_mcp/` → `src/daz_mcp_server/` (`git mv`)
- Modify: `pyproject.toml` (`name`, `authors`, `[project.scripts]`, wheel `packages`), `src/daz_mcp_server/_mcp.py` (FastMCP name + `_package_version`), every `vangard_daz_mcp` import in `src/`, `tests/`, `integration_test.py`; docstrings naming the old package/command (`server.py:1-17`)
- Modify: `tests/test_version_consistency.py` (`installed_version("daz-mcp-server")`, imports)
- Create: `tests/test_package_identity.py`

**Interfaces:**
- Produces: package `daz_mcp_server`; `daz_mcp_server.server:main`; `mcp.name == "daz-mcp-server"`.

- [ ] **Step 1: Failing tests** in `tests/test_package_identity.py`:
  - `test_import_name`: `import daz_mcp_server`; `importlib.util.find_spec("vangard_daz_mcp") is None`.
  - `test_server_name`: `from daz_mcp_server._mcp import mcp`; `mcp.name == "daz-mcp-server"`.
  - `test_console_script`: `importlib.metadata.entry_points(group="console_scripts")` has `daz-mcp-server` with value `daz_mcp_server.server:main`, and none named `vangard-daz-mcp`.
  - `test_authors_have_no_email`: `tomllib` load of `pyproject.toml`; `[project].authors == [{"name": "Blue Moon Foundry"}]`.
- [ ] **Step 2: Run** `uv run pytest tests/test_package_identity.py -q` → FAIL (import error).
- [ ] **Step 3: Implement** the rename; then `uv sync` so the installed metadata/entry point update. `grep -rn "vangard" src tests integration_test.py pyproject.toml` must be empty.
- [ ] **Step 4: Run** `uv run pytest tests/ -m "not integration and not slow" -q` → all pass (≈239 tests).
- [ ] **Step 5: Commit** `refactor: rename package to daz-mcp-server` (all moved/modified files).

### Task 2: Packaging hygiene

**Files:**
- Modify: `pyproject.toml` (add `[tool.hatch.build.targets.sdist]` `exclude`), `src/daz_mcp_server/tools/scene.py:~77` (BVH message)
- Create: `tests/test_packaging.py`

**Interfaces:**
- Produces: helper `build_dists(tmp_path) -> tuple[Path, Path]` in `tests/test_packaging.py` (runs `uv build --out-dir <tmp>`; returns sdist, wheel). Task 3 adds a wheel assertion that uses it.

- [ ] **Step 1: Failing tests** in `tests/test_packaging.py` (module-scoped fixture builds once):
  - `test_sdist_excludes_repo_internals`: no sdist member path contains `/.beads/`, `/.agents/`, `/.claude/`, `/.github/`, `/.worktrees/`, `/.venv/`, or a root-level `_test_*.py`.
  - `test_wheel_has_data_files`: wheel names include `daz_mcp_server/dazscript_docs.json` and `daz_mcp_server/genesis_bones.json`.
  - `test_no_personal_paths_in_source`: no file under `src/daz_mcp_server` contains `OpenCode` or `D:/`.
- [ ] **Step 2: Run** `uv run pytest tests/test_packaging.py -q` → sdist and personal-path tests FAIL.
- [ ] **Step 3: Implement**: sdist `exclude = [".beads", ".agents", ".claude", ".github", ".worktrees", ".venv", "_test_*.py", "docs/superpowers"]`; BVH error keeps its advice ("Parse the BVH and apply keys with setValue(time, value), or use a dedicated pipeline script.") without the file reference.
- [ ] **Step 4: Run** `uv run pytest tests/test_packaging.py -q` → pass.
- [ ] **Step 5: Commit** `build: keep repo internals out of the sdist; drop personal path`.

### Task 3: Bundled agent guides

**Files:**
- Move (`git mv`): `SKILL_ACTORS.md`→`src/daz_mcp_server/guides/actors.md`, `SKILL_CINEMA.md`→`cinema.md`, `SKILL_DAZ_STUDIO.md`→`daz_studio.md`, `SKILL_DAZSCRIPT.md`→`dazscript.md`, `SKILL_RECIPE.md`→`recipe.md`, `SKILL_SCENE.md`→`scene.md`. `SKILL_DEVELOPMENT.md` stays at the root.
- Create: `src/daz_mcp_server/_guides.py`
- Modify: `src/daz_mcp_server/tools/workflow.py` (resources, `daz://profiles` text), `tools/utility.py` (`daz_script_help`), `tools/material.py:~270`, `_registry.py:~7541`, `server.py` docstring, `CLAUDE.md` / `AGENTS.md` / `SKILL_DEVELOPMENT.md` / `README.md` references to the moved files (CLAUDE.md `@` includes point at the new paths)
- Test: `tests/test_guides.py`, `tests/test_packaging.py` (one added test)

**Interfaces:**
- Produces (`daz_mcp_server._guides`):
  - `GUIDE_NAMES: tuple[str, ...] = ("actors", "cinema", "daz_studio", "dazscript", "recipe", "scene")`
  - `read_guide(name: str) -> str` — reads `guides/<name>.md` via `importlib.resources`; `KeyError` for unknown names.
  - `guide_index() -> str` — one line per guide: `daz://guide/<name> — <first heading of the file>`.
- MCP resources: `daz://guides` → `guide_index()`; `daz://guide/{name}` → `read_guide(name)`.
- `daz_script_help(topic)`: topic `guide:<name>` returns `read_guide(name)`; `guides` returns `guide_index()`; unknown guide → the same "Unknown topic" style message listing guide names. `daz://help/{topic}` gets this for free (it calls `daz_script_help`).

- [ ] **Step 1: Failing tests** in `tests/test_guides.py`:
  - `test_every_guide_reads`: each name in `GUIDE_NAMES` → non-empty text starting with `#`.
  - `test_guides_resources_registered`: `asyncio.run(mcp.list_resources())` / `list_resource_templates()` include `daz://guides` and `daz://guide/{name}`.
  - `test_help_tool_serves_guides`: `daz_script_help("guide:recipe") == read_guide("recipe")`; `"daz://guide/recipe" in daz_script_help("guides")`.
  - `test_no_stale_skill_references`: no file under `src/daz_mcp_server` contains `SKILL_`; every `daz://guide/<x>` mentioned in source has `x in GUIDE_NAMES`.
  - `test_guides_visible_in_compact_profile`: with the compact profile applied (as `tests/test_workflow_profile.py` does), the guide resources are listed.
  - In `tests/test_packaging.py`: `test_wheel_has_guides`: wheel contains `daz_mcp_server/guides/<name>.md` for every name.
- [ ] **Step 2: Run** `uv run pytest tests/test_guides.py tests/test_packaging.py -q` → FAIL.
- [ ] **Step 3: Implement** the moves, `_guides.py`, resources, help-tool topics, and replace every "see SKILL_X.md" with `daz://guide/x`. Hatchling includes `guides/*.md` because it's inside the package; confirm via the wheel test.
- [ ] **Step 4: Run** `uv run pytest tests/ -m "not integration and not slow" -q` → all pass.
- [ ] **Step 5: Commit** `feat: bundle agent guides and serve them as daz://guide resources`.

### Task 4: dazpy 2.13 and plugin compatibility reporting

**Files:**
- Modify: `pyproject.toml` (`dazpy>=2.13.0`), `uv.lock` (`uv lock --upgrade-package dazpy`)
- Create: `src/daz_mcp_server/_compat.py`
- Modify: `src/daz_mcp_server/_mcp.py` (lifespan `AsyncDazClient(..., on_version_check=_compat.record)`; register middleware), `_client.py` (`get_daz_client` passes `on_version_check=_compat.record`), `_errors.py` (`handle_dazpy_error`), `tools/utility.py` (`daz_status`), `tools/workflow.py` (`daz_inspect_scene`)
- Test: `tests/test_compat.py`

**Interfaces:**
- Consumes (dazpy 2.13.0): `dazpy.VersionCheck` (fields `server_url, server_version, min_server_version, client_version, server_instance_id, compatible, message`), `on_version_check=` kwarg on `DazClient`/`AsyncDazClient`, `dazpy.MIN_SERVER_VERSION`.
- Produces (`daz_mcp_server._compat`), all thread-safe (one `threading.Lock`):
  - `record(check: VersionCheck) -> None` — stores latest; if `compatible is False`, also prints `check.message` to stderr once per distinct `(server_url, server_instance_id, server_version)`.
  - `latest() -> VersionCheck | None`
  - `summary() -> dict` — `{"target": f"{DAZ_HOST}:{DAZ_PORT}", "plugin_version", "min_plugin_version", "dazpy_version", "compatible", "message"}` (`plugin_version`/`compatible`/`message` are `None` before any check; `min_plugin_version` = `dazpy.MIN_SERVER_VERSION`, `dazpy_version` = `dazpy.__version__`).
  - `incompatible_note() -> str | None` — when latest `compatible is False`: `f"The Daz Studio plugin at {DAZ_HOST}:{DAZ_PORT} is {plugin_version}, older than the required {min}; upgrade it (https://github.com/bluemoonfoundry/daz-script-server/releases)."`, else `None`.
  - `take_unannounced() -> VersionCheck | None` — returns the latest incompatible check once per distinct key (for the MCP log); `None` otherwise.
  - `reset() -> None` — test helper.
- Behaviour:
  - `daz_status` returns the plugin's status dict plus `"plugin_compatibility": summary()` (always).
  - `daz_inspect_scene` adds `"plugin_compatibility": summary()` only when `incompatible_note()` is not `None`.
  - `handle_dazpy_error`: for `ServerResponseError` with `status_code == 404`, append `"\n" + incompatible_note()` to the ToolError text when a note exists. Other branches unchanged.
  - FastMCP middleware (`fastmcp.server.middleware.Middleware`, `on_call_tool`): after the call (success or error), if `take_unannounced()` returns a check, `await context.fastmcp_context.warning(check.message)`; any exception there is swallowed. Confirm the exact middleware/context API against the installed FastMCP 3.0.1 before writing it.

- [ ] **Step 1: Failing tests** in `tests/test_compat.py` (autouse fixture: `_compat.reset()`; build checks with `dazpy.VersionCheck(...)` directly):
  - `test_summary_before_any_check`: `compatible is None`, `target == "localhost:18811"` (defaults), `min_plugin_version == dazpy.MIN_SERVER_VERSION`.
  - `test_incompatible_note`: record `compatible=False, server_version="2.11.0"` → note contains `"2.11.0"`, the minimum, `"localhost:18811"`, `"daz-script-server/releases"`.
  - `test_note_clears_after_compatible_check`: record incompatible then compatible → `incompatible_note() is None`.
  - `test_take_unannounced_once_per_plugin`: same incompatible check recorded twice → first `take_unannounced()` returns it, second `None`; a new instance ID → returned again.
  - `test_record_thread_safe`: 10 threads × 100 `record` calls with alternating checks → no exception; `latest()` is one of them.
  - `test_daz_status_includes_compatibility`: mock `get_async_daz_client().status()` → result has `plugin_compatibility`.
  - `test_inspect_scene_only_when_incompatible`: mock `daz_scene_info`; compatible → key absent; incompatible → present.
  - `test_404_error_carries_note`: incompatible recorded; `handle_dazpy_error(ServerResponseError(..., status_code=404))` raises `ToolError` whose text contains the note; with a compatible check it doesn't.
  - `test_clients_wired_to_record`: `get_daz_client()._versions._callback is _compat.record` (reset the singleton around it) and the lifespan constructs `AsyncDazClient` with `on_version_check=_compat.record` (patch `AsyncDazClient` in `_mcp` and assert the kwarg).
- [ ] **Step 2: Run** `uv run pytest tests/test_compat.py -q` → FAIL.
- [ ] **Step 3: Implement** (pin + lock first; `uv sync`; then code).
- [ ] **Step 4: Run** `uv run pytest tests/ -m "not integration and not slow" -q` → all pass; `uv tree --package dazpy` (or `uv pip show dazpy`) shows 2.13.0 from PyPI.
- [ ] **Step 5: Commit** `feat: report a too-old Daz Studio plugin via dazpy 2.13 version checks`.

### Task 5: CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`
- Delete: `.github/workflows/pylint.yml` (its pylint steps move into `ci.yml` unchanged)
- Create: `scripts/smoke_wheel.py`

**Interfaces:**
- Produces: `scripts/smoke_wheel.py` — run with the *installed* package's Python (no repo on `sys.path`; invoke with `python -I`): imports `daz_mcp_server.server`, asserts `len(asyncio.run(mcp.list_tools())) > 0`, `read_guide("recipe")` non-empty, `dazscript_docs.json` loaded (non-empty `_DAZSCRIPT_DOCS`), prints `OK <n> tools`; exit 1 otherwise. Must not contact Studio (no lifespan run).
- `ci.yml`: on `push` and `pull_request`; matrix Python 3.11, 3.12; steps: checkout → `astral-sh/setup-uv` (pin a released major, e.g. `@v6`) → `uv sync` → `uv run pytest tests/ -m "not integration and not slow" -q` → the two pylint commands from `pylint.yml` (via `uv run --with pylint`) → `uv build` → create a clean venv, `pip install dist/*.whl`, run `python -I scripts/smoke_wheel.py` and `daz-mcp-server --help` if the entry point supports it (otherwise only the smoke script). Job name `ci (<python>)`.

- [ ] **Step 1: Failing check**: locally run `uv build --out-dir <scratch>/dist` then, in a fresh `uv venv <scratch>/venv` with the wheel installed, `python -I scripts/smoke_wheel.py` → fails (script missing).
- [ ] **Step 2: Implement** `scripts/smoke_wheel.py` and `ci.yml`; delete `pylint.yml`.
- [ ] **Step 3: Verify locally**: the smoke run prints `OK <n> tools`; `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml'))"` parses (use `uv run --with pyyaml`); the pytest and both pylint commands from `ci.yml` pass when run locally exactly as written.
- [ ] **Step 4: Commit** `ci: run unit tests, pylint and a built-wheel smoke on every push and PR`.

### Task 6: Release workflow, changelog, docs, 0.8.0

**Files:**
- Create: `.github/workflows/release.yml`, `scripts/check_release_version.py`, `scripts/compat_block.py`, `CHANGELOG.md`, `tests/test_release_scripts.py`
- Modify: `pyproject.toml` (`version = "0.8.0"`), `README.md` (title, badge `**Version 0.8.0**`, architecture line, install section, every MCP config example, module tree, new "Compatibility" and "Migrating from vangard-daz-mcp" sections), `CLAUDE.md` (version note), `tests/test_version_consistency.py` (compatibility-row check)

**Interfaces:**
- `scripts/check_release_version.py --tag vX.Y.Z` → exit 0 iff tag (minus `v`) equals `pyproject.toml` version; prints both on mismatch.
- `scripts/compat_block.py` → prints Markdown:
  ```
  ### Compatibility
  - dazpy >= <floor of the dazpy requirement in pyproject.toml>
  - Daz Studio plugin (DazScriptServer) >= <dazpy.MIN_SERVER_VERSION of the installed dazpy>
  - Plugin downloads: https://github.com/bluemoonfoundry/daz-script-server/releases
  ```
  Reads the floor by parsing `pyproject.toml`'s `dazpy>=X` requirement; the release job installs exactly `dazpy==<floor>` before running it, so the minimum is the floor's.
- README "Compatibility" table: columns `daz-mcp-server | dazpy | Daz Studio plugin`; first row `0.8.0 | >= 2.13.0 | >= 2.12`. `test_version_consistency.py` gains `test_readme_compatibility_row`: the row for the current version exists and its dazpy floor equals `pyproject.toml`'s.
- README primary install is the `uvx` config from the spec (`"command": "uvx", "args": ["daz-mcp-server"]`, env block); clone + `uv run --project <path> daz-mcp-server` stays as the developer setup. Migration section shows the before/after `claude_desktop_config.json` entry.
- `release.yml`: trigger `push: tags: ["v*.*.*"]`. Jobs:
  1. `check-version`: `python scripts/check_release_version.py --tag "${GITHUB_REF_NAME}"`.
  2. `test`: same steps as `ci.yml` (one Python, 3.12), `needs: check-version`.
  3. `build`: `uv build`; upload `dist/` artifact; `needs: test`.
  4. `publish-pypi`: `needs: build`; `environment: pypi`; `permissions: id-token: write`; download artifact; `pypa/gh-action-pypi-publish@release/v1` (no `skip-existing`: a duplicate version must fail loudly).
  5. `create-release`: `needs: publish-pypi`; `permissions: contents: write`; install `dazpy==<floor>` and run `scripts/compat_block.py > compat.md`; extract this version's `CHANGELOG.md` section; `softprops/action-gh-release@v2` with `body_path` = changelog section + compat block, `generate_release_notes: true`, attach `dist/*`.
- `CHANGELOG.md` (Keep a Changelog): `## [0.8.0] - <release date>` — Changed: renamed to daz-mcp-server (package, command, server name), published on PyPI, run with `uvx daz-mcp-server`; Added: bundled guides (`daz://guides`, `daz://guide/<name>`, `daz_script_help("guide:<name>")`), plugin compatibility reporting, CI; Removed: personal path in BVH message; migration note.

- [ ] **Step 1: Failing tests** in `tests/test_release_scripts.py` (run scripts via `subprocess` with `sys.executable`):
  - `test_tag_matches`: `--tag v<pyproject version>` → exit 0.
  - `test_tag_mismatch_fails`: `--tag v9.9.9` → exit ≠ 0, output names both versions.
  - `test_compat_block`: output contains `dazpy >= 2.13.0` and `plugin (DazScriptServer) >= ` followed by `dazpy.MIN_SERVER_VERSION`.
  - plus `test_readme_compatibility_row` in `tests/test_version_consistency.py`.
- [ ] **Step 2: Run** `uv run pytest tests/test_release_scripts.py tests/test_version_consistency.py -q` → FAIL.
- [ ] **Step 3: Implement** scripts, workflow, CHANGELOG, README, version bump.
- [ ] **Step 4: Verify**: `uv run pytest tests/ -m "not integration and not slow" -q` → all pass; `release.yml` parses as YAML; `uv build` produces `daz_mcp_server-0.8.0-py3-none-any.whl` and `daz_mcp_server-0.8.0.tar.gz`.
- [ ] **Step 5: Commit** `release: 0.8.0 — tag-driven PyPI release, changelog, docs`.

### Task 7: Ship and follow-ups (each outward step only after the user's go-ahead)

- [ ] **Step 1:** User confirms the GitHub environment `pypi` exists and allows `v*` tags (it must match the PyPI pending publisher's environment field).
- [ ] **Step 2:** Push `feat/pypi-release`, open a PR to `master`; CI (`ci.yml`) green on the PR. User reviews and merges (the repo requires an approving review).
- [ ] **Step 3:** Push tag `v0.8.0` on the merge commit. Verify: `gh run list --workflow release.yml -L 1` all jobs success; `pip index versions daz-mcp-server` lists 0.8.0; the GitHub release has the wheel + sdist and the compatibility block.
- [ ] **Step 4:** With the user's Studio running: `uvx daz-mcp-server` starts (stdio), and an MCP client call to `daz_status` (or the scoped `tests/smoke_live.py --mcp-dir` stage in daz-script-server, which now picks up `daz_mcp_server`) returns `plugin_compatibility.compatible == True`. Nothing broader runs against Studio.
- [ ] **Step 5:** Give the user the exact replacement `claude_desktop_config.json` entry (`"daz-mcp-server": {"command": "uvx", "args": ["daz-mcp-server"], "env": {...}}`); the user applies it.
- [ ] **Step 6:** In daz-script-server (separate small PR, after 0.8.0 is on PyPI): remove the `vangard_daz_mcp` fallback from the `mcp` stage in `tests/smoke_live.py`, keep only `daz_mcp_server` imports, and drop "(formerly vangard-daz-mcp)" from `docs/LIVE_SMOKE.md`; close the matching beads issue there.
