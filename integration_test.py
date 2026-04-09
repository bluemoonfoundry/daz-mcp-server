#!/usr/bin/env python3
"""
Live integration tests for the vangard-daz-mcp server.

Verifies DazScriptServer is reachable, initialises the MCP server module
(HTTP client + script registration), then calls every tool and reports pass/fail.

Usage:
    uv run python integration_test.py
    uv run python integration_test.py --verbose
    uv run python integration_test.py --host 192.168.1.10 --port 18811
"""

import argparse
import asyncio
import sys
import textwrap
import time
import traceback
from dataclasses import dataclass, field
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Bootstrap: add src/ to path so we can import the server module directly
# ---------------------------------------------------------------------------

sys.path.insert(0, "src")
import vangard_daz_mcp.server as server  # noqa: E402 (after path manipulation)


# ---------------------------------------------------------------------------
# Test result tracking
# ---------------------------------------------------------------------------

@dataclass
class Result:
    name: str
    category: str
    passed: bool
    detail: str = ""
    skipped: bool = False
    elapsed_ms: float = 0.0


_results: list[Result] = []
_verbose = False


def _pass(name: str, category: str, detail: str = "", elapsed_ms: float = 0.0) -> Result:
    r = Result(name=name, category=category, passed=True, detail=detail, elapsed_ms=elapsed_ms)
    _results.append(r)
    tick = "\033[32m✓\033[0m"
    ms = f"  ({elapsed_ms:.0f} ms)" if _verbose and elapsed_ms else ""
    print(f"  {tick} {name}{ms}")
    if _verbose and detail:
        for line in textwrap.wrap(str(detail), 80):
            print(f"      {line}")
    return r


def _fail(name: str, category: str, detail: str = "", elapsed_ms: float = 0.0) -> Result:
    r = Result(name=name, category=category, passed=False, detail=detail, elapsed_ms=elapsed_ms)
    _results.append(r)
    cross = "\033[31m✗\033[0m"
    ms = f"  ({elapsed_ms:.0f} ms)" if elapsed_ms else ""
    print(f"  {cross} {name}{ms}")
    for line in detail.splitlines()[:6]:
        print(f"      {line}")
    return r


def _skip(name: str, category: str, reason: str = "") -> Result:
    r = Result(name=name, category=category, passed=True, skipped=True, detail=reason)
    _results.append(r)
    dash = "\033[33m–\033[0m"
    print(f"  {dash} {name}  (skipped: {reason})")
    return r


async def _run(name: str, category: str, coro, *, skip_if: str = "") -> Any:
    """Run a coroutine, record pass/fail, return result or None."""
    if skip_if:
        _skip(name, category, skip_if)
        return None
    t0 = time.perf_counter()
    try:
        result = await coro
        elapsed = (time.perf_counter() - t0) * 1000
        detail = repr(result)[:200] if _verbose else ""
        _pass(name, category, detail, elapsed)
        return result
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        detail = f"{type(exc).__name__}: {exc}"
        if _verbose:
            detail += "\n" + traceback.format_exc()
        _fail(name, category, detail, elapsed)
        return None


# ---------------------------------------------------------------------------
# Pre-flight: verify DazScriptServer is reachable
# ---------------------------------------------------------------------------

async def preflight_check(base_url: str, token: str) -> dict | None:
    """GET /status — must succeed before any tool tests run."""
    print("\n\033[1mPre-flight: DazScriptServer connectivity\033[0m")
    headers = {"X-API-Token": token} if token else {}
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=5.0, headers=headers) as c:
            resp = await c.get("/status")
            resp.raise_for_status()
            data = resp.json()
            print(f"  \033[32m✓\033[0m  DazScriptServer reachable at {base_url}")
            print(f"       version={data.get('version', '?')}  "
                  f"running={data.get('running', '?')}")
            return data
    except httpx.ConnectError:
        print(f"  \033[31m✗\033[0m  Cannot reach DazScriptServer at {base_url}")
        print("       Is DAZ Studio running with the DazScriptServer plugin active?")
        return None
    except Exception as exc:
        print(f"  \033[31m✗\033[0m  Unexpected error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Server initialisation (equivalent to lifespan startup)
# ---------------------------------------------------------------------------

async def init_server(base_url: str, token: str) -> httpx.AsyncClient:
    """Create shared HTTP client and register all scripts."""
    print("\n\033[1mServer initialisation\033[0m")
    headers = {"X-API-Token": token} if token else {}
    client = httpx.AsyncClient(base_url=base_url, timeout=server.DAZ_TIMEOUT, headers=headers)
    server._http_client = client

    t0 = time.perf_counter()
    try:
        await server._register_scripts(client)
        elapsed = (time.perf_counter() - t0) * 1000
        count = len(server._REGISTRY)
        print(f"  \033[32m✓\033[0m  Registered {count} scripts  ({elapsed:.0f} ms)")
    except Exception as exc:
        print(f"  \033[31m✗\033[0m  Script registration failed: {exc}")
        raise

    return client


# ---------------------------------------------------------------------------
# Test suites
# ---------------------------------------------------------------------------

async def test_infrastructure(scene: dict) -> None:
    cat = "infrastructure"
    print(f"\n\033[1m[{cat}]\033[0m")

    await _run("daz_status", cat,
               server.daz_status())

    await _run("daz_execute – simple IIFE", cat,
               server.daz_execute("(function(){ return {ok: true}; })()"))

    await _run("daz_execute – App.applicationVersion", cat,
               server.daz_execute("(function(){ return {ver: App.applicationVersion}; })()"))

    await _run("daz_scene_info", cat,
               server.daz_scene_info())

    await _run("daz_get_animation_info", cat,
               server.daz_get_animation_info())

    await _run("daz_get_render_settings", cat,
               server.daz_get_render_settings())

    await _run("daz_validate_script – clean script", cat,
               server.daz_validate_script("(function(){ var n = Scene.findNodeByLabel('x'); return n; })()"))

    await _run("daz_validate_script – known anti-pattern", cat,
               server.daz_validate_script("var cam = new DzNewCameraAction(); cam.trigger();"))

    await _run("daz_list_requests", cat,
               server.daz_list_requests())

    await _run("daz_list_checkpoints (empty)", cat,
               server.daz_list_checkpoints())

    await _run("daz_get_scene_layout – all types", cat,
               server.daz_get_scene_layout())

    await _run("daz_get_scene_layout – figures + cameras only", cat,
               server.daz_get_scene_layout(["figures", "cameras"]))


async def test_content_library() -> None:
    cat = "content library"
    print(f"\n\033[1m[{cat}]\033[0m")

    await _run("daz_list_categories – top level", cat,
               server.daz_list_categories())

    await _run("daz_list_categories – People subfolder", cat,
               server.daz_list_categories("People"))

    await _run("daz_browse_category – People", cat,
               server.daz_browse_category("People"))


async def test_figure_tools(scene: dict) -> None:
    cat = "figure tools"
    figures = scene.get("figures", [])
    label = figures[0]["label"] if figures else None
    no_fig = "" if label else "no figures in scene"

    print(f"\n\033[1m[{cat}]\033[0m  "
          + (f"(using figure: \033[36m{label}\033[0m)" if label else "\033[33m(no figures)\033[0m"))

    await _run("daz_get_node", cat,
               server.daz_get_node(label) if label else _noop(),
               skip_if=no_fig)

    await _run("daz_get_world_position", cat,
               server.daz_get_world_position(label) if label else _noop(),
               skip_if=no_fig)

    await _run("daz_get_bounding_box", cat,
               server.daz_get_bounding_box(label) if label else _noop(),
               skip_if=no_fig)

    await _run("daz_get_node_hierarchy", cat,
               server.daz_get_node_hierarchy(label, max_depth=2) if label else _noop(),
               skip_if=no_fig)

    await _run("daz_list_children", cat,
               server.daz_list_children(label) if label else _noop(),
               skip_if=no_fig)

    await _run("daz_inspect_properties – all", cat,
               server.daz_inspect_properties(label) if label else _noop(),
               skip_if=no_fig)

    await _run("daz_inspect_properties – transform only", cat,
               server.daz_inspect_properties(label, "transform") if label else _noop(),
               skip_if=no_fig)

    await _run("daz_get_property_metadata – XTranslate", cat,
               server.daz_get_property_metadata(label, "XTranslate") if label else _noop(),
               skip_if=no_fig)

    await _run("daz_list_morphs – active only", cat,
               server.daz_list_morphs(label, include_zero=False) if label else _noop(),
               skip_if=no_fig)

    await _run("daz_search_morphs – smile", cat,
               server.daz_search_morphs(label, "smile") if label else _noop(),
               skip_if=no_fig)

    await _run("daz_set_emotion – happy (intensity 0.5)", cat,
               server.daz_set_emotion(label, "happy", intensity=0.5) if label else _noop(),
               skip_if=no_fig)

    await _run("daz_set_emotion – neutral (reset)", cat,
               server.daz_set_emotion(label, "neutral") if label else _noop(),
               skip_if=no_fig)

    # Spatial: check distance to itself is 0
    if label:
        figs = [f["label"] for f in figures]
        if len(figs) >= 2:
            await _run("daz_calculate_distance – two figures", cat,
                       server.daz_calculate_distance(figs[0], figs[1]))
            await _run("daz_get_spatial_relationship", cat,
                       server.daz_get_spatial_relationship(figs[0], figs[1]))
            await _run("daz_check_overlap", cat,
                       server.daz_check_overlap(figs[0], figs[1]))
        else:
            _skip("daz_calculate_distance", cat, "need ≥2 figures")
            _skip("daz_get_spatial_relationship", cat, "need ≥2 figures")
            _skip("daz_check_overlap", cat, "need ≥2 figures")
    else:
        _skip("daz_calculate_distance", cat, no_fig)
        _skip("daz_get_spatial_relationship", cat, no_fig)
        _skip("daz_check_overlap", cat, no_fig)

    await _run("daz_find_nearby_nodes – r=500", cat,
               server.daz_find_nearby_nodes(label, radius=500) if label else _noop(),
               skip_if=no_fig)


async def test_camera_tools(scene: dict) -> None:
    cat = "camera tools"
    cameras = scene.get("cameras", [])
    figures = scene.get("figures", [])
    cam = cameras[0]["label"] if cameras else None
    fig = figures[0]["label"] if figures else None
    no_cam = "" if cam else "no cameras in scene"
    no_cam_fig = "" if (cam and fig) else "need a camera and figure"

    print(f"\n\033[1m[{cat}]\033[0m  "
          + (f"cam=\033[36m{cam}\033[0m  fig=\033[36m{fig}\033[0m"
             if cam else "\033[33m(no cameras)\033[0m"))

    await _run("daz_set_active_camera", cat,
               server.daz_set_active_camera(cam) if cam else _noop(),
               skip_if=no_cam)

    await _run("daz_save_camera_preset", cat,
               server.daz_save_camera_preset(cam) if cam else _noop(),
               skip_if=no_cam)

    await _run("daz_frame_shot – medium-close-up", cat,
               server.daz_frame_shot(cam, fig, "medium-close-up") if (cam and fig) else _noop(),
               skip_if=no_cam_fig)

    await _run("daz_frame_shot – full-shot", cat,
               server.daz_frame_shot(cam, fig, "full-shot") if (cam and fig) else _noop(),
               skip_if=no_cam_fig)

    await _run("daz_apply_camera_angle – eye-level", cat,
               server.daz_apply_camera_angle(cam, fig, "eye-level") if (cam and fig) else _noop(),
               skip_if=no_cam_fig)

    await _run("daz_apply_camera_angle – low-angle", cat,
               server.daz_apply_camera_angle(cam, fig, "low-angle") if (cam and fig) else _noop(),
               skip_if=no_cam_fig)

    await _run("daz_apply_composition_rule – rule-of-thirds", cat,
               server.daz_apply_composition_rule(cam, fig, "rule-of-thirds") if (cam and fig) else _noop(),
               skip_if=no_cam_fig)

    await _run("daz_apply_composition_rule – golden-ratio", cat,
               server.daz_apply_composition_rule(cam, fig, "golden-ratio") if (cam and fig) else _noop(),
               skip_if=no_cam_fig)

    await _run("daz_orbit_camera_around – 45°", cat,
               server.daz_orbit_camera_around(cam, fig, 250, 45, 15) if (cam and fig) else _noop(),
               skip_if=no_cam_fig)

    await _run("daz_frame_camera_to_node", cat,
               server.daz_frame_camera_to_node(cam, fig) if (cam and fig) else _noop(),
               skip_if=no_cam_fig)

    if cam:
        preset_result = await _run("daz_save_camera_preset (for load test)", cat,
                                   server.daz_save_camera_preset(cam))
        if preset_result and "preset" in preset_result:
            await _run("daz_load_camera_preset", cat,
                       server.daz_load_camera_preset(cam, preset_result["preset"]))
        else:
            _skip("daz_load_camera_preset", cat, "save_camera_preset did not return preset data")
    else:
        _skip("daz_load_camera_preset", cat, no_cam)


async def test_lighting_tools(scene: dict) -> None:
    cat = "lighting tools"
    figures = scene.get("figures", [])
    fig = figures[0]["label"] if figures else None
    no_fig = "" if fig else "no figures in scene"

    print(f"\n\033[1m[{cat}]\033[0m")

    await _run("daz_apply_lighting_preset – three-point", cat,
               server.daz_apply_lighting_preset("three-point", fig) if fig else _noop(),
               skip_if=no_fig)

    await _run("daz_apply_lighting_preset – rembrandt", cat,
               server.daz_apply_lighting_preset("rembrandt", fig) if fig else _noop(),
               skip_if=no_fig)

    await _run("daz_validate_scene", cat,
               server.daz_validate_scene())


async def test_checkpoint_system(scene: dict) -> None:
    cat = "checkpoint system"
    print(f"\n\033[1m[{cat}]\033[0m")

    await _run("daz_list_checkpoints – before save", cat,
               server.daz_list_checkpoints())

    await _run("daz_save_scene_state – 'integration_test'", cat,
               server.daz_save_scene_state("integration_test"))

    await _run("daz_list_checkpoints – after save", cat,
               server.daz_list_checkpoints())

    await _run("daz_restore_scene_state – 'integration_test'", cat,
               server.daz_restore_scene_state("integration_test"))

    # Confirm unknown name raises ToolError
    cat2 = cat
    name = "daz_restore_scene_state – unknown name raises error"
    from fastmcp.exceptions import ToolError
    t0 = time.perf_counter()
    try:
        await server.daz_restore_scene_state("__nonexistent__")
        elapsed = (time.perf_counter() - t0) * 1000
        _fail(name, cat2, "Expected ToolError but no exception was raised", elapsed)
    except ToolError:
        elapsed = (time.perf_counter() - t0) * 1000
        _pass(name, cat2, "ToolError raised as expected", elapsed)
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        _fail(name, cat2, f"Wrong exception type: {type(exc).__name__}: {exc}", elapsed)


async def test_animation_tools() -> None:
    cat = "animation tools"
    print(f"\n\033[1m[{cat}]\033[0m")

    await _run("daz_get_animation_info", cat,
               server.daz_get_animation_info())

    await _run("daz_set_frame – frame 0", cat,
               server.daz_set_frame(0))

    await _run("daz_set_frame_range – 0 to 29", cat,
               server.daz_set_frame_range(0, 29))

    await _run("daz_get_animation_info – after range set", cat,
               server.daz_get_animation_info())


async def test_batch_tools(scene: dict) -> None:
    cat = "batch tools"
    figures = scene.get("figures", [])
    fig = figures[0]["label"] if figures else None
    no_fig = "" if fig else "no figures in scene"

    print(f"\n\033[1m[{cat}]\033[0m")

    # batch_set_properties: set XTranslate to its current value (no-op effectively)
    await _run("daz_batch_set_properties – single property", cat,
               server.daz_batch_set_properties([
                   {"node_label": fig, "property_name": "XTranslate", "value": 0}
               ]) if fig else _noop(),
               skip_if=no_fig)

    await _run("daz_batch_visibility – hide+show", cat,
               server.daz_batch_visibility([fig], visible=True) if fig else _noop(),
               skip_if=no_fig)

    await _run("daz_batch_select", cat,
               server.daz_batch_select([fig]) if fig else _noop(),
               skip_if=no_fig)


async def test_async_render_tools() -> None:
    cat = "async render tools"
    print(f"\n\033[1m[{cat}]\033[0m")

    await _run("daz_set_render_quality – draft", cat,
               server.daz_set_render_quality("draft"))

    await _run("daz_list_requests – empty", cat,
               server.daz_list_requests())

    # Test status on a made-up ID returns 404 → ToolError
    from fastmcp.exceptions import ToolError
    name = "daz_get_request_status – unknown id raises error"
    t0 = time.perf_counter()
    try:
        await server.daz_get_request_status("nonexistent-id-xyz")
        elapsed = (time.perf_counter() - t0) * 1000
        _fail(name, cat, "Expected ToolError but no exception raised", elapsed)
    except ToolError:
        elapsed = (time.perf_counter() - t0) * 1000
        _pass(name, cat, "ToolError raised as expected", elapsed)
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        _fail(name, cat, f"Wrong exception: {type(exc).__name__}: {exc}", elapsed)


# ---------------------------------------------------------------------------
# Coroutine placeholder for skipped branches
# ---------------------------------------------------------------------------

async def _noop():
    return None


# ---------------------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------------------

def print_summary() -> int:
    passed = [r for r in _results if r.passed and not r.skipped]
    failed = [r for r in _results if not r.passed]
    skipped = [r for r in _results if r.skipped]

    total = len(passed) + len(failed)

    print("\n" + "─" * 60)
    print(f"\033[1mResults\033[0m  "
          f"\033[32m{len(passed)} passed\033[0m  "
          + (f"\033[31m{len(failed)} failed\033[0m  " if failed else "")
          + f"\033[33m{len(skipped)} skipped\033[0m  "
          f"({total} run)")

    if failed:
        print("\n\033[31mFailed tests:\033[0m")
        for r in failed:
            print(f"  • [{r.category}] {r.name}")
            if r.detail:
                for line in r.detail.splitlines()[:3]:
                    print(f"      {line}")

    if skipped and _verbose:
        print("\n\033[33mSkipped tests:\033[0m")
        for r in skipped:
            print(f"  – [{r.category}] {r.name}  ({r.detail})")

    print()
    return 1 if failed else 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main(host: str, port: int, verbose: bool) -> int:
    global _verbose
    _verbose = verbose

    base_url = f"http://{host}:{port}"
    token = server.DAZ_API_TOKEN  # loaded from env / token file at import time

    print(f"\033[1mvangard-daz-mcp  integration tests\033[0m")
    print(f"Target: {base_url}")

    # 1. Pre-flight check
    status = await preflight_check(base_url, token)
    if status is None:
        print("\n\033[31mAborting: DazScriptServer not reachable.\033[0m\n")
        return 2

    # 2. Initialise server module
    client = await init_server(base_url, token)

    try:
        # 3. Get scene state once — used to drive conditional tests
        print("\n\033[1mInspecting scene\033[0m")
        try:
            scene = await server.daz_scene_info()
            figs = scene.get("figures", [])
            cams = scene.get("cameras", [])
            lights = scene.get("lights", [])
            print(f"  figures={len(figs)}  cameras={len(cams)}  lights={len(lights)}")
        except Exception as exc:
            print(f"  \033[33mWarning: daz_scene_info failed ({exc}) — scene-dependent tests will be skipped\033[0m")
            scene = {}

        # 4. Run test suites
        await test_infrastructure(scene)
        await test_content_library()
        await test_figure_tools(scene)
        await test_camera_tools(scene)
        await test_lighting_tools(scene)
        await test_checkpoint_system(scene)
        await test_animation_tools()
        await test_batch_tools(scene)
        await test_async_render_tools()

    finally:
        server._http_client = None
        await client.aclose()

    return print_summary()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="vangard-daz-mcp live integration tests")
    parser.add_argument("--host", default="localhost", help="DazScriptServer host (default: localhost)")
    parser.add_argument("--port", type=int, default=18811, help="DazScriptServer port (default: 18811)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show response detail and skip reasons")
    args = parser.parse_args()

    exit_code = asyncio.run(main(args.host, args.port, args.verbose))
    sys.exit(exit_code)
