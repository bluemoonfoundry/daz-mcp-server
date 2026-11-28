"""Tests for the compact workflow facade and expert opt-in profile."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from fastmcp.exceptions import ToolError
from fastmcp.utilities.types import File, Image

from daz_mcp_server.tools import workflow


DEFAULT_TOOLS = {
    "daz_fetch_artifact",
    "daz_inspect_scene",
    "daz_run_script_job",
    "daz_observe_job",
    "daz_submit_job",
    "daz_recipe_validate",
    "daz_recipe_plan",
    "daz_recipe_apply",
    "daz_recipe_observe",
    "daz_recipe_render",
}


def _profile_snapshot(profile: str) -> dict:
    code = """
import asyncio, json
from daz_mcp_server.server import ACTIVE_PROFILE, mcp
async def main():
    tools = await mcp.list_tools(run_middleware=False)
    resources = await mcp.list_resources(run_middleware=False)
    templates = await mcp.list_resource_templates(run_middleware=False)
    print(json.dumps({
        "profile": ACTIVE_PROFILE,
        "tools": [tool.name for tool in tools],
        "resources": [str(resource.uri) for resource in resources],
        "templates": [str(template.uri_template) for template in templates],
    }))
asyncio.run(main())
"""
    env = os.environ.copy()
    env["DAZ_MCP_PROFILE"] = profile
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return json.loads(result.stdout)


def test_compact_profile_exposes_only_workflow_tools_and_help_resources():
    snapshot = _profile_snapshot("compact")
    assert snapshot["profile"] == "compact"
    assert set(snapshot["tools"]) == DEFAULT_TOOLS
    assert "daz://profiles" in snapshot["resources"]
    assert "daz://help/{topic}" in snapshot["templates"]
    assert "daz://guides" in snapshot["resources"]
    assert "daz://guide/{name}" in snapshot["templates"]


def test_profiles_resource_describes_every_compact_tool():
    text = workflow.daz_profiles_resource()
    assert "ten" in text and "five" not in text
    for name in ("validate", "plan", "apply", "observe", "render"):
        assert name in text
    assert "daz://guide/recipe" in text


def test_daz_studio_skill_counts_the_compact_tools():
    text = (Path(__file__).parents[1] / "src" / "daz_mcp_server" / "guides" / "daz_studio.md").read_text(encoding="utf-8")
    assert "five tools" not in text
    assert "daz://guide/recipe" in text
    for name in sorted(DEFAULT_TOOLS):
        assert f"`{name}`" in text, name


def test_expert_profile_preserves_detailed_surface():
    snapshot = _profile_snapshot("expert")
    assert snapshot["profile"] == "expert"
    assert DEFAULT_TOOLS < set(snapshot["tools"])
    assert "daz_set_property" in snapshot["tools"]
    assert "daz_execute" in snapshot["tools"]
    assert len(snapshot["tools"]) == 162


async def test_run_script_job_delegates_file_job(monkeypatch):
    calls = []

    async def submit(script_file, args, report_file):
        calls.append((script_file, args, report_file))
        return {"request_id": "job-1", "status": "queued"}

    monkeypatch.setattr(workflow, "daz_execute_file_async", submit)
    result = await workflow.daz_run_script_job(
        "C:/recipes/pose-probe.dsa",
        {"doggy": True},
        "C:/runs/job-1.jsonl",
    )
    assert result == {"request_id": "job-1", "status": "queued"}
    assert calls == [
        (
            "C:/recipes/pose-probe.dsa",
            {"doggy": True},
            "C:/runs/job-1.jsonl",
        )
    ]


async def test_run_script_job_takes_script_file_keyword(monkeypatch):
    calls = []

    async def submit(script_file, args, report_file):
        calls.append((script_file, args, report_file))
        return {"request_id": "job-2", "status": "queued"}

    monkeypatch.setattr(workflow, "daz_execute_file_async", submit)
    await workflow.daz_run_script_job(script_file="C:/scripts/probe.dsa", parameters={"a": 1})
    assert calls == [("C:/scripts/probe.dsa", {"a": 1}, None)]


async def test_run_script_job_rejects_non_script_file():
    with pytest.raises(ToolError, match="must be a .dsa or .ds file"):
        await workflow.daz_run_script_job("C:/recipes/pose.json")


async def test_observe_job_routes_each_action(monkeypatch):
    async def status(request_id):
        return {"route": "status", "request_id": request_id}

    async def result(request_id, wait, timeout):
        return {"route": "result", "request_id": request_id, "wait": wait, "timeout": timeout}

    async def cancel(request_id):
        return {"route": "cancel", "request_id": request_id}

    monkeypatch.setattr(workflow, "daz_get_request_status", status)
    monkeypatch.setattr(workflow, "daz_get_request_result", result)
    monkeypatch.setattr(workflow, "daz_cancel_request", cancel)

    assert (await workflow.daz_observe_job("job-1"))["route"] == "status"
    collected = await workflow.daz_observe_job(
        "job-1", "result", wait=False, timeout_seconds=12
    )
    assert collected == {
        "route": "result",
        "request_id": "job-1",
        "wait": False,
        "timeout": 12,
    }
    assert (await workflow.daz_observe_job("job-1", "cancel"))["route"] == "cancel"


async def test_fetch_artifact_returns_only_manifest_files(monkeypatch, tmp_path: Path):
    image_path = tmp_path / "plate.png"
    image_path.write_bytes(b"not-a-real-png")
    report_path = tmp_path / "manifest.json"
    report_path.write_text("{}", encoding="utf-8")

    async def status(_request_id):
        return {
            "observation": {
                "output_manifest": {
                    "outputs": [
                        {"path": str(image_path), "kind": "image", "label": "plate"},
                        {"path": str(report_path), "kind": "manifest", "label": "run"},
                    ]
                }
            }
        }

    monkeypatch.setattr(workflow, "daz_get_request_status", status)
    assert isinstance(await workflow.daz_fetch_artifact("job-1", "plate"), Image)
    assert isinstance(await workflow.daz_fetch_artifact("job-1", 1), File)
    with pytest.raises(ToolError, match="not in job"):
        await workflow.daz_fetch_artifact("job-1", str(tmp_path / "secret.txt"))


# --- desktop profile: compact plus direct script authoring and read-only scene tools ---

DESKTOP_EXTRA = {
    "daz_execute",
    "daz_submit_script",
    "daz_write_script",
    "daz_script_help",
    "daz_validate_script",
    "daz_explain_last_error",
    "daz_status",
    "daz_get_node",
    "daz_find_nodes",
    "daz_get_selected_nodes",
    "daz_list_cameras",
    "daz_list_lights",
    "daz_get_render_settings",
}


def test_desktop_profile_is_compact_plus_direct_tools():
    compact = _profile_snapshot("compact")
    desktop = _profile_snapshot("desktop")
    assert desktop["profile"] == "desktop"
    assert set(compact["tools"]) <= set(desktop["tools"])  # additive: every compact tool stays
    assert set(desktop["tools"]) == DEFAULT_TOOLS | DESKTOP_EXTRA
    assert desktop["resources"] == compact["resources"]
    assert desktop["templates"] == compact["templates"]


def test_compact_profile_does_not_gain_desktop_tools():
    assert not DESKTOP_EXTRA & set(_profile_snapshot("compact")["tools"])


def test_expert_profile_includes_desktop_tools():
    assert DESKTOP_EXTRA <= set(_profile_snapshot("expert")["tools"])


def test_unknown_profile_names_every_choice():
    env = os.environ.copy()
    env["DAZ_MCP_PROFILE"] = "bogus"
    result = subprocess.run(
        [sys.executable, "-c", "import daz_mcp_server.server"],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode != 0
    assert "compact, desktop, expert" in result.stderr


def test_profiles_resource_describes_desktop():
    text = workflow.daz_profiles_resource()
    assert "DAZ_MCP_PROFILE=desktop" in text
    assert "Claude Desktop" in text
    for name in ("daz_execute", "daz_submit_script", "daz_write_script"):
        assert f"`{name}`" in text, name


class _FakeAsyncClient:
    def __init__(self):
        self.submitted = []

    async def execute_async_submit(self, script, args=None, *, report_file=None):
        self.submitted.append((script, args, report_file))
        return "job-9"


async def test_submit_script_queues_inline_job(monkeypatch):
    fake = _FakeAsyncClient()
    monkeypatch.setattr(workflow, "get_async_daz_client", lambda: fake)
    result = await workflow.daz_submit_script(
        "print(args.n); return args.n;", {"n": 3}, "C:/runs/job-9.jsonl")
    assert result == {"request_id": "job-9", "status": "queued"}
    assert fake.submitted == [("var args = getArguments()[0]; print(args.n); return args.n;",
                               {"n": 3}, "C:/runs/job-9.jsonl")]


async def test_submit_script_rejects_empty_script():
    with pytest.raises(ToolError, match="script is empty"):
        await workflow.daz_submit_script("   ")


async def test_write_script_saves_through_studio_and_returns_path(monkeypatch):
    calls = []

    async def execute_raw(script, args=None):
        calls.append((script, args))
        return {"success": True, "result": {"path": "C:/Temp/DAZ/daz-mcp-scripts/pose_sweep.dsa",
                                             "bytes": 21}, "error": None}

    monkeypatch.setattr(workflow, "_execute_raw", execute_raw)
    body = 'print("a \\ \\"quoted\\" é");'
    result = await workflow.daz_write_script("pose_sweep", body)
    assert result == {"path": "C:/Temp/DAZ/daz-mcp-scripts/pose_sweep.dsa", "bytes": 21}
    (source, args), = calls
    # the content travels as a job argument, never spliced into the source
    assert args == {"file_name": "pose_sweep.dsa", "content": body}
    assert body not in source
    assert "DzFile" in source and "getTempPath" in source
    # the plugin defines no `args` variable: the writer reads getArguments()[0]
    assert "getArguments()[0]" in source


@pytest.mark.parametrize("name, expected", [
    ("pose_sweep", "pose_sweep.dsa"),
    ("pose-sweep.dsa", "pose-sweep.dsa"),
    ("Probe2.ds", "Probe2.ds"),
])
async def test_write_script_keeps_or_adds_script_suffix(monkeypatch, name, expected):
    seen = []

    async def execute_raw(script, args=None):
        seen.append(args["file_name"])
        return {"success": True, "result": {"path": "X/" + args["file_name"], "bytes": 1}}

    monkeypatch.setattr(workflow, "_execute_raw", execute_raw)
    await workflow.daz_write_script(name, "return 1;")
    assert seen == [expected]


@pytest.mark.parametrize("name", ["", "../evil", "a/b", "C:\\x", ".hidden", "x" * 80, "na me", "x.txt"])
async def test_write_script_rejects_unsafe_names(name):
    with pytest.raises(ToolError, match="name"):
        await workflow.daz_write_script(name, "return 1;")


async def test_write_script_reports_studio_failure(monkeypatch):
    async def execute_raw(script, args=None):
        return {"success": True, "result": {"error": "cannot open X for writing"}, "error": None}

    monkeypatch.setattr(workflow, "_execute_raw", execute_raw)
    with pytest.raises(ToolError, match="cannot open X for writing"):
        await workflow.daz_write_script("probe", "return 1;")
