# daz-mcp-server release architecture

Repo: daz-mcp-server. First PyPI release: **daz-mcp-server 0.8.0**.
Depends on: dazpy 2.13.0 being on PyPI (see the daz-script-server spec
`2026-11-16-dazpy-plugin-version-check-design.md`).
Status: design, awaiting approval.

## Why

Today people clone the repo and run the server with `uv run --project <clone>
vangard-daz-mcp`. The repo has no tags, no GitHub releases and no published
package. The user's main reason for releases is **version compatibility**:
knowing which MCP server goes with which dazpy and which Daz Studio plugin, and
being told clearly when the plugin they're connected to is too old.

The user chose to publish to PyPI so that `uvx daz-mcp-server` works with no
clone.

## Goals

1. **One name everywhere: `daz-mcp-server`** (user's decision, following their
   convention: `daz-` for Daz Studio support work, `bmf-` for Blue Moon Foundry
   products). Repo name (unchanged), PyPI distribution, import package
   `daz_mcp_server`, console command `daz-mcp-server`, FastMCP server name.
   The name is free on PyPI (checked 2026-11-16). `vangard-daz-mcp` never
   appears on PyPI.
2. **Tag-driven releases** copying daz-script-server's pattern: pushing a
   `vX.Y.Z` tag builds, checks the tag matches the version, publishes to PyPI
   via Trusted Publishing, and creates a GitHub release.
3. **CI runs the unit tests** on every push/PR, and the release workflow runs
   them before publishing.
4. **The package is self-sufficient for AI use**: the agent guides
   (`SKILL_*.md`) ship inside the package and are served to the AI (user's
   decision: the guides are for the AI, so bundle them).
5. **A too-old plugin is reported where users and the AI see it**, using
   dazpy 2.13's version-check result. The server starts regardless (user's
   decision).
6. **Release notes state compatibility**: required dazpy, minimum plugin
   version.

## Non-goals

- No change to how the server talks to Studio (env vars `DAZ_HOST`,
  `DAZ_PORT`, `DAZ_API_TOKEN`, `DAZ_TIMEOUT`, `DAZ_CONTENT_BROWSER_URL`,
  `DAZ_MCP_PROFILE` stay as they are).
- No MCP registry / marketplace listing, Docker image or standalone binary.
- No version-checking logic of the server's own; dazpy owns it.
- No compatibility alias for the old command name (my call: users run it from
  a clone today, so the migration is a one-line config edit, covered in
  release notes and README).

## Anti-goals

- Publishing repo-internal material to PyPI (`.beads/`, `.agents/`, personal
  paths).
- A release that passes CI but whose installed package can't find its data
  files or guides.
- Refusing to start, or failing tools outright, because of the plugin version.

## Design

### 1. Rename

- `src/vangard_daz_mcp/` → `src/daz_mcp_server/`; update all imports in
  `src/` and `tests/`.
- `pyproject.toml`: `name = "daz-mcp-server"`;
  `[project.scripts] daz-mcp-server = "daz_mcp_server.server:main"`;
  wheel `packages = ["src/daz_mcp_server"]`.
- FastMCP: `FastMCP("daz-mcp-server", version=_package_version("daz-mcp-server"), ...)`.
- `tests/test_version_consistency.py` and its README/CLAUDE.md checks follow
  the new names.
- README: title, architecture line, every config example (key, `command`,
  `args`), module tree. New primary install path:

  ```json
  "daz-mcp-server": {
    "command": "uvx",
    "args": ["daz-mcp-server"],
    "env": { "DAZ_HOST": "localhost", "DAZ_PORT": "18811" }
  }
  ```

  The clone + `uv run --project` route stays documented as the developer
  setup.
- A "Migrating from vangard-daz-mcp" section in README and the 0.8.0 release
  notes.
- Other repo docs (`CLAUDE.md`, `AGENTS.md`, `SKILL_DEVELOPMENT.md`, ...):
  replace the old names where they refer to the package/command.

### 2. Bundled agent guides

- Move the AI-facing guides into the package:
  `src/daz_mcp_server/guides/` holding `actors.md`, `cinema.md`,
  `daz_studio.md`, `dazscript.md`, `recipe.md`, `scene.md` (from
  `SKILL_ACTORS.md`, `SKILL_CINEMA.md`, `SKILL_DAZ_STUDIO.md`,
  `SKILL_DAZSCRIPT.md`, `SKILL_RECIPE.md`, `SKILL_SCENE.md`).
- `SKILL_DEVELOPMENT.md` is for humans developing the server; it stays at the
  repo root and is not bundled.
- Serve each as an MCP resource `daz://guide/{name}` (e.g.
  `daz://guide/recipe`), plus a listing resource `daz://guides`, in the same
  style as the existing `daz://help/{topic}` and `daz://recipe/schema`.
- Also reachable from a tool, because some MCP clients don't show resources to
  the AI (my call): extend the existing help path (`daz_script_help` /
  `daz://help/{topic}`) so topic `guide:<name>` (or equivalent) returns the
  guide. No new visible tool in the compact profile.
- Every tool description, resource text and error message that says "see
  SKILL_X.md" points at `daz://guide/x` instead (known spots:
  `tools/workflow.py:156`, `tools/material.py:270`, `_registry.py:7541`,
  `server.py:16`; grep for any others).
- Repo-root `CLAUDE.md` `@SKILL_*.md` includes are updated to the new paths so
  developers' agents still load them.
- A test asserts every guide referenced in source exists in the installed
  package and is served.

### 3. Packaging hygiene

- sdist excludes: `.beads/`, `.agents/`, `.claude/`, `.github/`, `scratch*`,
  local test scripts at the root (`_test_server.py`-style), `uv.lock` is fine
  either way. Builder confirms with `uv build` + listing the sdist.
- Wheel must contain `dazscript_docs.json`, `genesis_bones.json` and
  `guides/*.md` (already true for the two JSON files).
- Remove the personal path from the BVH error in `tools/scene.py:77`; the
  message keeps its advice without the file reference.
- `pyproject.toml` metadata is published as-is to PyPI, including `authors`.
  The author entry becomes `authors = [{name = "Blue Moon Foundry"}]` with
  no email (user's decision): PyPI metadata can't be withdrawn, and dazpy
  publishes none either. A test or CI check asserts no `email` key in
  `[project].authors` before the first tag.

### 4. CI

- Replace/extend `.github/workflows/pylint.yml` with a `ci.yml` that runs on
  push and PR, Python 3.11 and 3.12, using `uv`:
  - `uv run pytest tests/ -m "not integration and not slow"` (no Studio in CI;
    integration tests also skip themselves when Studio is unreachable)
  - pylint as today (fail-under 7.0)
  - `uv build`, then install the built wheel into a clean venv and smoke it:
    `daz-mcp-server --help` (or equivalent import + tool-count check) and the
    guides resource loads.
- Builder decides whether pylint stays a separate workflow.

### 5. Release workflow

New `.github/workflows/release.yml`, modelled on daz-script-server's
`release-tagged.yml`:

- Trigger: push of a tag matching `v*.*.*`.
- Jobs: check tag matches `pyproject.toml` version (a small script, or reuse
  the test) → run the CI checks above → `uv build` → publish to PyPI with
  `pypa/gh-action-pypi-publish@release/v1` and Trusted Publishing
  (`id-token: write`, GitHub environment `pypi`) → create the GitHub release
  with `softprops/action-gh-release@v2`, attaching the wheel and sdist, notes
  generated from commits since the previous tag plus a compatibility block.
- Compatibility block in the release body, generated from the repo:
  - `dazpy >= <pin from pyproject.toml>`
  - `Daz Studio plugin >= <dazpy.MIN_SERVER_VERSION>`, read by installing the
    **floor** of the pin (`dazpy==<pin>`) in the release job, so the claim
    holds for the oldest dazpy a user could get (my call)
  - link to the plugin releases page.
- `CHANGELOG.md` is introduced (Keep a Changelog style, like daz-script-server)
  starting at 0.8.0; the release notes include that section.

**User one-time setup (cannot be automated):** register a *pending publisher*
on PyPI for project `daz-mcp-server`, owner `bluemoonfoundry`, repo
`daz-mcp-server`, workflow `release.yml`, environment `pypi`, before the first
tag is pushed. Also create the `pypi` environment in the GitHub repo settings.

### 6. Plugin compatibility reporting

Uses dazpy 2.13's `VersionCheck` / `on_version_check` callback.

- `pyproject.toml`: `dazpy>=2.13.0`.
- Both clients the server creates (`AsyncDazClient` in `_mcp.py` lifespan, the
  sync `DazClient` in `_client.py`) are constructed with an
  `on_version_check` callback that stores the latest `VersionCheck` in one
  shared, lock-guarded place (the sync client's callback runs on worker
  threads). The callback only stores; surfacing happens in tool code, which
  has the request context (my call).
- When the latest check says `compatible is False`:
  - `daz_status` includes a `plugin_compatibility` field with the plugin
    version, required minimum, `DAZ_HOST:DAZ_PORT`, and the upgrade advice;
  - tool errors that look like a missing feature (404 unknown route, unknown
    script/function, `NOT_FOUND`-style error codes) append one line: "The Daz
    Studio plugin at HOST:PORT is X, older than the required Y; upgrade it";
  - an MCP log message at `warning` level is sent once per new incompatible
    check, from the first tool call that sees it (tool code has the context);
    the callback itself also logs to stderr.
- When a later check says compatible, the extra field and hints disappear.
- `daz_status` always reports plugin version, dazpy version, minimum plugin
  version and the target `DAZ_HOST:DAZ_PORT`, compatible or not.

### 7. Version and compatibility statement

- 0.8.0 is the first release (rename + PyPI). `tests/test_version_consistency.py`
  keeps README badge, `CLAUDE.md`, and FastMCP version aligned.
- README gains a short "Compatibility" table: MCP server version → minimum
  dazpy → minimum plugin, updated each release (the release-notes block is
  generated; the README table is maintained by hand and checked by the
  consistency test for the current version's row).

## Order of work

1. daz-script-server: dazpy version check (separate spec) → release v2.13.0.
   MCP work starts only once dazpy 2.13.0 is on PyPI, so the MCP branch is
   built and CI-tested against the published package (no local/editable dazpy
   source in the committed lockfile).
2. daz-mcp-server: this spec, on a branch → PR → merge.
3. User registers the PyPI pending publisher and the `pypi` environment.
4. Push tag `v0.8.0` (user's go-ahead) → verify PyPI + GitHub release →
   `uvx daz-mcp-server` smoke against a running Studio.
5. The user's own MCP client configs switch to the new command: Claude Desktop
   (`%APPDATA%\Claude\claude_desktop_config.json`, currently `uv run
   --project Y:/working/BlueMoonFoundry/daz-mcp-server vangard-daz-mcp`) and
   any Claude Code MCP entry. The builder prepares the exact snippet; the user
   applies it.

6. After 0.8.0 is on PyPI, in daz-script-server: remove the `vangard_daz_mcp`
   fallback from the `mcp` stage snippet in `tests/smoke_live.py` (added in
   2.13.0 so the smoke run worked across the rename), leaving only the
   `daz_mcp_server` imports, and drop "(formerly vangard-daz-mcp)" from
   `docs/LIVE_SMOKE.md`. A small PR on that repo; no release needed.

Every outward step (push, PR, merge, tag, PyPI setup) stops for the user's
go-ahead; the builder verifies results after each.

No other repos depend on the old name: a search of the BlueMoonFoundry
workspace found only docs (handled in dazpy 2.13.0), dated plans/specs and
scratch copies.

## Left to the builder

- Exact sdist exclude list and how the clean-venv smoke is scripted.
- Which tool errors count as "looks like a missing feature".
- File names inside `guides/`, and how `daz_script_help` exposes them.
- Whether pylint stays its own workflow.
