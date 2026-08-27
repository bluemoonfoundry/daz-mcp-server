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

from vangard_daz_mcp.tools import workflow


DEFAULT_TOOLS = {
    "daz_fetch_artifact",
    "daz_inspect_scene",
    "daz_materialize_recipe",
    "daz_observe_job",
    "daz_submit_job",
}


def _profile_snapshot(profile: str) -> dict:
    code = """
import asyncio, json
from vangard_daz_mcp.server import ACTIVE_PROFILE, mcp
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


def test_expert_profile_preserves_detailed_surface():
    snapshot = _profile_snapshot("expert")
    assert snapshot["profile"] == "expert"
    assert DEFAULT_TOOLS < set(snapshot["tools"])
    assert "daz_set_property" in snapshot["tools"]
    assert "daz_execute" in snapshot["tools"]
    assert len(snapshot["tools"]) == 144


async def test_materialize_recipe_delegates_file_job(monkeypatch):
    calls = []

    async def submit(script_file, args, report_file):
        calls.append((script_file, args, report_file))
        return {"request_id": "job-1", "status": "queued"}

    monkeypatch.setattr(workflow, "daz_execute_file_async", submit)
    result = await workflow.daz_materialize_recipe(
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


async def test_materialize_recipe_rejects_non_script_file():
    with pytest.raises(ToolError, match="must be a .dsa or .ds file"):
        await workflow.daz_materialize_recipe("C:/recipes/pose.json")


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
