"""Tests for vangard-daz-mcp server tools."""

from unittest.mock import MagicMock

import pytest
import pytest_asyncio
import respx
import httpx
import dazpy.exceptions as daz_exc
from dazpy.aio import AsyncDazClient
from fastmcp.exceptions import ToolError

from vangard_daz_mcp._client import set_async_daz_client, set_scene
from vangard_daz_mcp.tools.render import (
    daz_render,
    daz_render_async,
    daz_render_with_camera_async,
    daz_batch_render_cameras_async,
    daz_render_batch,
    daz_render_animation_async,
    daz_get_request_status,
    daz_get_request_result,
    daz_cancel_request,
    daz_list_requests,
    daz_set_render_quality,
    daz_wait_for_request,
)
from vangard_daz_mcp.tools.scene import daz_scene_info, daz_load_file, daz_save_scene_copy
from vangard_daz_mcp.tools.transform import daz_get_node, daz_set_property
from vangard_daz_mcp.tools.utility import (
    daz_status,
    daz_execute,
    daz_execute_file,
    daz_execute_file_async,
    daz_wait_for_scene_event,
)


BASE_URL = "http://localhost:18811"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(autouse=True)
async def daz_client():
    """Provide the protocol client (respx patches its internal transport)."""
    async with AsyncDazClient(host="localhost", port=18811, token="") as client:
        set_async_daz_client(client)
        yield client
    set_async_daz_client(None)


@pytest.fixture(autouse=True)
def mock_scene():
    """Replace the dazpy DazScene singleton with a MagicMock.

    Tools that go through get_scene()/run_dazpy() (e.g. daz_load_file with
    merge=True, daz_save_scene_copy) use a separate connection from the httpx
    client that respx mocks. Without this, those calls silently fall through
    to a real DazClient and can reach a live, shared DAZ Studio instance —
    do not remove this without giving every dazpy-routed tool an explicit
    mock in its own test.
    """
    scene = MagicMock()
    set_scene(scene)
    yield scene
    set_scene(None)


@pytest.fixture
def mock_daz():
    """Activate respx mock router for the DazScriptServer base URL."""
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


def _ok(result):
    """Return a 200 success response carrying `result` as the DAZ payload."""
    return httpx.Response(
        200,
        json={"success": True, "result": result, "output": [], "error": None},
    )


def _fail(error, output=None):
    """Return a 200 failure response."""
    return httpx.Response(
        200,
        json={"success": False, "result": None, "output": output or [], "error": error},
    )


# ---------------------------------------------------------------------------
# daz_status
# ---------------------------------------------------------------------------

async def test_daz_status_ok(mock_daz):
    mock_daz.get("/status").mock(
        return_value=httpx.Response(200, json={"running": True, "version": "1.0.0.0"})
    )
    result = await daz_status()
    assert result["running"] is True
    assert result["version"] == "1.0.0.0"


async def test_daz_status_connect_error(mock_daz):
    mock_daz.get("/status").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(ToolError, match="DAZ Studio is running"):
        await daz_status()


async def test_daz_status_unauthorized(mock_daz):
    mock_daz.get("/status").mock(return_value=httpx.Response(401))
    with pytest.raises(ToolError, match="Authentication failed"):
        await daz_status()


# ---------------------------------------------------------------------------
# daz_execute
# ---------------------------------------------------------------------------

async def test_daz_execute_success(mock_daz):
    mock_daz.post("/execute").mock(return_value=_ok(42))
    result = await daz_execute(script="return 42;")
    assert result["success"] is True
    assert result["result"] == 42


async def test_daz_execute_with_args(mock_daz):
    mock_daz.post("/execute").mock(return_value=_ok("ok"))
    result = await daz_execute(script="return args.x;", args={"x": 99})
    assert result["success"] is True


async def test_daz_execute_script_failure(mock_daz):
    mock_daz.post("/execute").mock(
        return_value=_fail("ReferenceError: foo is not defined", ["line1"])
    )
    with pytest.raises(ToolError, match="ReferenceError"):
        await daz_execute(script="foo();")


async def test_daz_execute_output_appended_to_error(mock_daz):
    mock_daz.post("/execute").mock(return_value=_fail("SomeError", ["debug line"]))
    with pytest.raises(ToolError, match="debug line"):
        await daz_execute(script="bad();")


async def test_daz_execute_timeout(mock_daz):
    mock_daz.post("/execute").mock(side_effect=httpx.ReadTimeout("timed out"))
    with pytest.raises(ToolError, match="DAZ_TIMEOUT"):
        await daz_execute(script="while(true){}")


async def test_daz_execute_unauthorized(mock_daz):
    mock_daz.post("/execute").mock(return_value=httpx.Response(401))
    with pytest.raises(ToolError, match="Authentication failed"):
        await daz_execute(script="return 1;")


# ---------------------------------------------------------------------------
# daz_execute_file
# ---------------------------------------------------------------------------

async def test_daz_execute_file_success(mock_daz):
    mock_daz.post("/execute").mock(return_value=_ok("done"))
    result = await daz_execute_file(script_file="C:/scripts/test.dsa")
    assert result["result"] == "done"


async def test_daz_execute_file_failure(mock_daz):
    mock_daz.post("/execute").mock(return_value=_fail("File not found"))
    with pytest.raises(ToolError, match="File not found"):
        await daz_execute_file(script_file="C:/scripts/missing.dsa")


async def test_daz_execute_file_async_returns_job_and_preserves_payload(mock_daz):
    route = mock_daz.post("/execute/async").mock(
        return_value=httpx.Response(
            200,
            json={
                "request_id": "execute-file-123",
                "status": "queued",
                "submitted_at": "2026-08-18T12:00:00Z",
            },
        )
    )

    result = await daz_execute_file_async(
        script_file="C:/scripts/pose-probe.dsa",
        args={"mode": "probe"},
        report_file="C:/runs/probe/job.jsonl",
    )

    assert result["request_id"] == "execute-file-123"
    assert result["status"] == "queued"
    assert route.calls.last.request.content == (
        b'{"scriptFile":"C:/scripts/pose-probe.dsa","args":{"mode":"probe"},'
        b'"reportFile":"C:/runs/probe/job.jsonl"}'
    )


async def test_daz_execute_file_async_http_failure(mock_daz):
    mock_daz.post("/execute/async").mock(
        return_value=httpx.Response(400, json={"error": "File not found"})
    )
    with pytest.raises(ToolError, match="File not found"):
        await daz_execute_file_async(script_file="C:/scripts/missing.dsa")


# ---------------------------------------------------------------------------
# daz_scene_info
# ---------------------------------------------------------------------------

_SCENE_RESULT = {
    "sceneFile": "C:/scenes/test.duf",
    "nodeCount": 2,
    "selectedNode": "Genesis 9",
    "nodes": [
        {"name": "Genesis9", "label": "Genesis 9", "type": "DzFigure"},
        {"name": "Camera", "label": "Camera", "type": "DzCamera"},
    ],
}


async def test_daz_scene_info_ok(mock_daz):
    mock_daz.post("/scripts/vangard-scene-info/execute").mock(return_value=_ok(_SCENE_RESULT))
    result = await daz_scene_info()
    assert result["nodeCount"] == 2
    assert result["selectedNode"] == "Genesis 9"
    assert len(result["nodes"]) == 2


async def test_daz_scene_info_unsaved(mock_daz):
    payload = {**_SCENE_RESULT, "sceneFile": "", "selectedNode": None}
    mock_daz.post("/scripts/vangard-scene-info/execute").mock(return_value=_ok(payload))
    result = await daz_scene_info()
    assert result["sceneFile"] == ""
    assert result["selectedNode"] is None


async def test_execute_by_id_retries_on_404(mock_daz):
    """On 404, scripts are re-registered with DazScriptServer and the call retried."""
    call_count = 0

    def scene_info_side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(
                404,
                json={"success": False, "error": "Script not found: 'vangard-scene-info'"},
            )
        return _ok(_SCENE_RESULT)

    mock_daz.post("/scripts/vangard-scene-info/execute").mock(side_effect=scene_info_side_effect)
    mock_daz.post("/scripts/register").mock(
        return_value=httpx.Response(200, json={"success": True, "id": "x", "updated": False})
    )

    result = await daz_scene_info()
    assert result["nodeCount"] == 2
    assert call_count == 2


# ---------------------------------------------------------------------------
# daz_get_node
# ---------------------------------------------------------------------------

_NODE_RESULT = {
    "name": "Genesis9",
    "label": "Genesis 9",
    "type": "DzFigure",
    "properties": {
        "Translation X": 0.0,
        "Translation Y": 0.0,
        "Translation Z": 0.0,
        "Rotation X": 15.0,
        "Head Size": 0.5,
    },
}


async def test_daz_get_node_ok(mock_daz):
    mock_daz.post("/scripts/vangard-get-node/execute").mock(return_value=_ok(_NODE_RESULT))
    result = await daz_get_node("Genesis 9")
    assert result["label"] == "Genesis 9"
    assert result["properties"]["Rotation X"] == 15.0


async def test_daz_get_node_not_found(mock_daz):
    mock_daz.post("/scripts/vangard-get-node/execute").mock(
        return_value=_fail("Node not found: Ghost")
    )
    with pytest.raises(ToolError, match="Node not found"):
        await daz_get_node("Ghost")


# ---------------------------------------------------------------------------
# daz_set_property
# ---------------------------------------------------------------------------

async def test_daz_set_property_ok(mock_daz):
    mock_daz.post("/scripts/vangard-set-property/execute").mock(
        return_value=_ok({"node": "Genesis 9", "property": "Rotation X", "value": 45.0})
    )
    result = await daz_set_property("Genesis 9", "Rotation X", 45.0)
    assert result["value"] == 45.0
    assert result["property"] == "Rotation X"


async def test_daz_set_property_node_not_found(mock_daz):
    mock_daz.post("/scripts/vangard-set-property/execute").mock(
        return_value=_fail("Node not found: Ghost")
    )
    with pytest.raises(ToolError, match="Node not found"):
        await daz_set_property("Ghost", "Rotation X", 0.0)


async def test_daz_set_property_prop_not_found(mock_daz):
    mock_daz.post("/scripts/vangard-set-property/execute").mock(
        return_value=_fail("Property not found: Foo on Genesis 9")
    )
    with pytest.raises(ToolError, match="Property not found"):
        await daz_set_property("Genesis 9", "Foo", 1.0)


async def test_daz_set_property_not_numeric(mock_daz):
    mock_daz.post("/scripts/vangard-set-property/execute").mock(
        return_value=_fail("Property is not numeric: Label")
    )
    with pytest.raises(ToolError, match="not numeric"):
        await daz_set_property("Genesis 9", "Label", 1.0)


# ---------------------------------------------------------------------------
# daz_render
# ---------------------------------------------------------------------------

async def test_daz_render_default(mock_daz):
    mock_daz.post("/scripts/vangard-render/execute").mock(return_value=_ok({"success": True}))
    result = await daz_render()
    assert result["success"] is True


async def test_daz_render_with_output_path(mock_daz):
    mock_daz.post("/scripts/vangard-render/execute").mock(return_value=_ok({"success": True}))
    result = await daz_render(output_path="C:/renders/out.png")
    assert result["success"] is True



# ---------------------------------------------------------------------------
# daz_load_file
# ---------------------------------------------------------------------------

async def test_daz_load_file_merge(mock_scene):
    """merge=True (default) routes through get_scene().load(), not the script registry."""
    result = await daz_load_file("C:/scenes/char.duf")
    mock_scene.load.assert_called_once_with("C:/scenes/char.duf")
    assert result["success"] is True
    assert result["file"] == "C:/scenes/char.duf"


async def test_daz_load_file_replace(mock_daz):
    mock_daz.post("/scripts/vangard-load-file/execute").mock(
        return_value=_ok({"success": True, "file": "C:/scenes/scene.duf"})
    )
    result = await daz_load_file("C:/scenes/scene.duf", merge=False)
    assert result["success"] is True


async def test_daz_load_file_not_found(mock_scene):
    """merge=True: get_scene().load() raising a dazpy ScriptRuntimeError becomes a ToolError."""
    mock_scene.load.side_effect = daz_exc.ScriptRuntimeError("File not found: C:/missing.duf")
    with pytest.raises(ToolError, match="File not found"):
        await daz_load_file("C:/missing.duf")


# ---------------------------------------------------------------------------
# Phase 1.5: Async operations — helpers
# ---------------------------------------------------------------------------

def _async_submitted(request_id: str) -> httpx.Response:
    """Return a 202 Accepted response for an async submission."""
    return httpx.Response(
        202,
        json={
            "request_id": request_id,
            "status": "queued",
            "submitted_at": "2026-04-08T12:00:00.000",
        },
    )


def _status_response(request_id: str, status: str, progress: float = 0.0) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "request_id": request_id,
            "status": status,
            "progress": progress,
            "submitted_at": "2026-04-08T12:00:00.000",
            "started_at": "2026-04-08T12:00:01.000" if status != "queued" else None,
            "completed_at": (
                "2026-04-08T12:00:10.000" if status in ("completed", "failed", "cancelled")
                else None
            ),
        },
    )


def _result_response(
    request_id: str, status: str = "completed", result=None, error: str = ""
) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "request_id": request_id,
            "status": status,
            "result": result,
            "output": [],
            "error": error,
            "submitted_at": "2026-04-08T12:00:00.000",
            "completed_at": "2026-04-08T12:00:10.000",
            "duration_ms": 10000,
        },
    )


# ---------------------------------------------------------------------------
# daz_render_async — now uses POST /render directly
# ---------------------------------------------------------------------------

async def test_daz_render_async_ok(mock_daz):
    mock_daz.post("/render").mock(return_value=_async_submitted("rnd-abc123"))
    result = await daz_render_async("C:/renders/out.png")
    assert result["request_id"] == "rnd-abc123"
    assert result["status"] == "queued"


async def test_daz_render_async_with_all_params(mock_daz):
    captured = {}

    def capture(request):
        captured.update(request.content and __import__("json").loads(request.content))
        return _async_submitted("rnd-params")

    mock_daz.post("/render").mock(side_effect=capture)
    result = await daz_render_async(
        "C:/out.png", width=1920, height=1080, camera="Camera 1",
        engine="iray", iray_samples=500,
    )
    assert result["request_id"] == "rnd-params"
    assert captured["output_path"] == "C:/out.png"
    assert captured["width"] == 1920
    assert captured["height"] == 1080
    assert captured["camera"] == "Camera 1"
    assert captured["engine"] == "iray"
    assert captured["iray_samples"] == 500


async def test_daz_render_async_connect_error(mock_daz):
    mock_daz.post("/render").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(ToolError, match="DAZ Studio is running"):
        await daz_render_async("C:/out.png")


# ---------------------------------------------------------------------------
# daz_render_with_camera_async — now uses POST /render with camera param
# ---------------------------------------------------------------------------

async def test_daz_render_with_camera_async_ok(mock_daz):
    captured = {}

    def capture(request):
        captured.update(__import__("json").loads(request.content))
        return _async_submitted("rnd-cam-abc")

    mock_daz.post("/render").mock(side_effect=capture)
    result = await daz_render_with_camera_async("Camera 1", "C:/out.png")
    assert result["request_id"] == "rnd-cam-abc"
    assert captured["camera"] == "Camera 1"
    assert captured["output_path"] == "C:/out.png"


# ---------------------------------------------------------------------------
# daz_batch_render_cameras_async — now uses POST /render/batch
# ---------------------------------------------------------------------------

async def test_daz_batch_render_cameras_async_ok(mock_daz):
    cameras = ["Cam_0", "Cam_90", "Cam_180"]
    mock_daz.post("/render/batch").mock(
        return_value=httpx.Response(
            202,
            json={"request_ids": ["rnd-0", "rnd-1", "rnd-2"], "total": 3},
        )
    )
    result = await daz_batch_render_cameras_async(cameras, "/renders/turntable", "angle")
    assert result["total"] == 3
    assert len(result["request_ids"]) == 3
    assert result["cameras"] == cameras


async def test_daz_batch_render_cameras_async_passes_engine(mock_daz):
    captured = {}

    def capture(request):
        captured.update(__import__("json").loads(request.content))
        return httpx.Response(202, json={"request_ids": ["rnd-0"], "total": 1})

    mock_daz.post("/render/batch").mock(side_effect=capture)
    await daz_batch_render_cameras_async(["OnlyCam"], "/out", engine="3delight")
    assert captured.get("base", {}).get("engine") == "3delight"


async def test_daz_batch_render_cameras_async_single(mock_daz):
    mock_daz.post("/render/batch").mock(
        return_value=httpx.Response(202, json={"request_ids": ["rnd-single"], "total": 1})
    )
    result = await daz_batch_render_cameras_async(["OnlyCam"], "/out")
    assert result["total"] == 1
    assert result["request_ids"][0] == "rnd-single"


# ---------------------------------------------------------------------------
# daz_render_batch — new tool using POST /render/batch
# ---------------------------------------------------------------------------

async def test_daz_render_batch_ok(mock_daz):
    mock_daz.post("/render/batch").mock(
        return_value=httpx.Response(
            202,
            json={"request_ids": ["rnd-0", "rnd-1"], "total": 2},
        )
    )
    result = await daz_render_batch(
        variants=[
            {"output_path": "C:/out/neutral.png"},
            {"output_path": "C:/out/smile.png", "morphs": {"Smile": 1.0}},
        ]
    )
    assert result["total"] == 2
    assert result["request_ids"] == ["rnd-0", "rnd-1"]


async def test_daz_render_batch_with_base(mock_daz):
    captured = {}

    def capture(request):
        captured.update(__import__("json").loads(request.content))
        return httpx.Response(202, json={"request_ids": ["rnd-0"], "total": 1})

    mock_daz.post("/render/batch").mock(side_effect=capture)
    await daz_render_batch(
        base={"figure": "Genesis 9", "width": 1920, "height": 1080},
        variants=[{"output_path": "C:/out/v1.png"}],
    )
    assert captured["base"]["figure"] == "Genesis 9"
    assert captured["base"]["width"] == 1920
    assert len(captured["variants"]) == 1


# ---------------------------------------------------------------------------
# daz_render_animation_async
# ---------------------------------------------------------------------------

async def test_daz_render_animation_async_ok(mock_daz):
    mock_daz.post("/scripts/vangard-render-animation/async").mock(
        return_value=_async_submitted("anim-xyz")
    )
    result = await daz_render_animation_async("/renders/anim")
    assert result["request_id"] == "anim-xyz"


async def test_daz_render_animation_async_with_range(mock_daz):
    mock_daz.post("/scripts/vangard-render-animation/async").mock(
        return_value=_async_submitted("anim-range")
    )
    result = await daz_render_animation_async(
        "/renders/anim", start_frame=10, end_frame=50, camera="Camera 1"
    )
    assert result["request_id"] == "anim-range"


# ---------------------------------------------------------------------------
# daz_get_request_status
# ---------------------------------------------------------------------------

async def test_daz_get_request_status_queued(mock_daz):
    mock_daz.get("/requests/render-abc/status").mock(
        return_value=_status_response("render-abc", "queued")
    )
    result = await daz_get_request_status("render-abc")
    assert result["status"] == "queued"
    assert result["request_id"] == "render-abc"


async def test_daz_get_request_status_running(mock_daz):
    mock_daz.get("/requests/render-abc/status").mock(
        return_value=_status_response("render-abc", "running", progress=0.5)
    )
    result = await daz_get_request_status("render-abc")
    assert result["status"] == "running"
    assert result["progress"] == 0.5


async def test_daz_get_request_status_completed(mock_daz):
    mock_daz.get("/requests/render-abc/status").mock(
        return_value=_status_response("render-abc", "completed", progress=1.0)
    )
    result = await daz_get_request_status("render-abc")
    assert result["status"] == "completed"


async def test_daz_get_request_status_not_found(mock_daz):
    mock_daz.get("/requests/missing/status").mock(
        return_value=httpx.Response(404, json={"error": "Request not found: missing"})
    )
    with pytest.raises(ToolError, match="not found"):
        await daz_get_request_status("missing")


# ---------------------------------------------------------------------------
# daz_get_request_result
# ---------------------------------------------------------------------------

async def test_daz_get_request_result_completed(mock_daz):
    mock_daz.get("/requests/render-abc/result").mock(
        return_value=_result_response("render-abc", result={"success": True})
    )
    result = await daz_get_request_result("render-abc")
    assert result["status"] == "completed"
    assert result["result"]["success"] is True


async def test_daz_get_request_result_failed_raises(mock_daz):
    mock_daz.get("/requests/render-abc/result").mock(
        return_value=_result_response("render-abc", status="failed", error="Render crashed")
    )
    with pytest.raises(ToolError, match="Render crashed"):
        await daz_get_request_result("render-abc")


async def test_daz_get_request_result_cancelled_returns(mock_daz):
    """Cancelled is an intentional outcome, not an error — should return the status dict."""
    mock_daz.get("/requests/render-abc/result").mock(
        return_value=_result_response("render-abc", status="cancelled")
    )
    result = await daz_get_request_result("render-abc")
    assert result["status"] == "cancelled"


async def test_daz_get_request_result_no_wait(mock_daz):
    mock_daz.get("/requests/render-abc/result").mock(
        return_value=_result_response("render-abc", result=42)
    )
    result = await daz_get_request_result("render-abc", wait=False)
    assert result["result"] == 42


async def test_daz_get_request_result_not_found(mock_daz):
    mock_daz.get("/requests/missing/result").mock(
        return_value=httpx.Response(404, json={"error": "Request not found"})
    )
    with pytest.raises(ToolError, match="Request not found"):
        await daz_get_request_result("missing")


# ---------------------------------------------------------------------------
# daz_cancel_request — routes rnd- to POST /render/:id/cancel, others to DELETE /requests/:id
# ---------------------------------------------------------------------------

async def test_daz_cancel_script_request(mock_daz):
    """Script request IDs (script-*) use DELETE /requests/:id."""
    mock_daz.delete("/requests/script-abc").mock(
        return_value=httpx.Response(
            200,
            json={
                "request_id": "script-abc",
                "status": "cancelled",
                "cancelled_at": "2026-04-08T12:00:05.000",
            },
        )
    )
    result = await daz_cancel_request("script-abc")
    assert result["status"] == "cancelled"


async def test_daz_cancel_render_request(mock_daz):
    """Render request IDs (rnd-*) use POST /render/:id/cancel."""
    mock_daz.post("/render/rnd-abc123/cancel").mock(
        return_value=httpx.Response(
            200,
            json={
                "request_id": "rnd-abc123",
                "status": "cancelled",
                "cancelled_at": "2026-04-08T12:00:05.000",
            },
        )
    )
    result = await daz_cancel_request("rnd-abc123")
    assert result["status"] == "cancelled"
    assert result["request_id"] == "rnd-abc123"


async def test_daz_cancel_request_already_done(mock_daz):
    mock_daz.delete("/requests/script-done").mock(
        return_value=httpx.Response(409, json={"error": "Cannot cancel completed request"})
    )
    with pytest.raises(ToolError, match="Cannot cancel completed request"):
        await daz_cancel_request("script-done")


async def test_daz_cancel_request_not_found(mock_daz):
    mock_daz.delete("/requests/script-missing").mock(
        return_value=httpx.Response(404, json={"error": "Request not found"})
    )
    with pytest.raises(ToolError, match="not found"):
        await daz_cancel_request("script-missing")


async def test_daz_cancel_render_not_found(mock_daz):
    mock_daz.post("/render/rnd-missing/cancel").mock(
        return_value=httpx.Response(404, json={"error": "Request not found"})
    )
    with pytest.raises(ToolError, match="not found"):
        await daz_cancel_request("rnd-missing")


# ---------------------------------------------------------------------------
# daz_list_requests
# ---------------------------------------------------------------------------

_LIST_RESPONSE = {
    "requests": [
        {
            "request_id": "render-aaa",
            "status": "completed",
            "progress": 1.0,
            "submitted_at": "2026-04-08T12:00:00.000",
        },
        {
            "request_id": "render-bbb",
            "status": "queued",
            "progress": 0.0,
            "submitted_at": "2026-04-08T12:01:00.000",
        },
    ],
    "total": 2,
    "queued": 1,
    "running": 0,
    "completed": 1,
    "failed": 0,
    "cancelled": 0,
}


async def test_daz_list_requests_all(mock_daz):
    mock_daz.get("/requests").mock(return_value=httpx.Response(200, json=_LIST_RESPONSE))
    result = await daz_list_requests()
    assert result["total"] == 2
    assert result["completed"] == 1
    assert result["queued"] == 1
    assert len(result["requests"]) == 2


async def test_daz_list_requests_filtered(mock_daz):
    filtered = {
        **_LIST_RESPONSE,
        "requests": [_LIST_RESPONSE["requests"][0]],
        "total": 1,
        "queued": 0,
    }
    mock_daz.get("/requests").mock(return_value=httpx.Response(200, json=filtered))
    result = await daz_list_requests(status_filter="completed")
    assert result["total"] == 1
    assert result["requests"][0]["status"] == "completed"


async def test_daz_list_requests_empty(mock_daz):
    mock_daz.get("/requests").mock(
        return_value=httpx.Response(
            200,
            json={"requests": [], "total": 0, "queued": 0, "running": 0,
                  "completed": 0, "failed": 0, "cancelled": 0},
        )
    )
    result = await daz_list_requests()
    assert result["total"] == 0
    assert result["requests"] == []


# ---------------------------------------------------------------------------
# daz_set_render_quality
# ---------------------------------------------------------------------------

async def test_daz_set_render_quality_draft(mock_daz):
    mock_daz.post("/scripts/vangard-set-render-quality/execute").mock(
        return_value=_ok({
            "preset": "draft",
            "propertiesSet": [
                {"property": "Max Samples", "value": 100},
                {"property": "Render Quality", "value": 0.5},
            ],
        })
    )
    result = await daz_set_render_quality("draft")
    assert result["preset"] == "draft"
    assert len(result["propertiesSet"]) == 2


async def test_daz_set_render_quality_final(mock_daz):
    mock_daz.post("/scripts/vangard-set-render-quality/execute").mock(
        return_value=_ok({
            "preset": "final",
            "propertiesSet": [
                {"property": "Max Samples", "value": 5000},
                {"property": "Render Quality", "value": 1.0},
            ],
        })
    )
    result = await daz_set_render_quality("final")
    assert result["preset"] == "final"


async def test_daz_set_render_quality_invalid_preset():
    with pytest.raises(ToolError, match="Unknown render quality preset"):
        await daz_set_render_quality("ultra")


async def test_daz_set_render_quality_all_presets(mock_daz):
    """All four presets should reach the execute endpoint without error."""
    for preset in ("draft", "preview", "good", "final"):
        mock_daz.post("/scripts/vangard-set-render-quality/execute").mock(
            return_value=_ok({"preset": preset, "propertiesSet": []})
        )
        result = await daz_set_render_quality(preset)
        assert result["preset"] == preset


# ---------------------------------------------------------------------------
# daz_wait_for_request (non-tool helper)
# ---------------------------------------------------------------------------

async def test_daz_wait_for_request_already_completed(mock_daz):
    mock_daz.get("/requests/render-abc/status").mock(
        return_value=_status_response("render-abc", "completed")
    )
    mock_daz.get("/requests/render-abc/result").mock(
        return_value=_result_response("render-abc", result={"success": True})
    )
    result = await daz_wait_for_request("render-abc", poll_interval_seconds=0.0)
    assert result["status"] == "completed"


async def test_daz_wait_for_request_polls_until_complete(mock_daz):
    call_count = 0

    def status_side_effect(request):
        nonlocal call_count
        call_count += 1
        status = "running" if call_count < 3 else "completed"
        return _status_response("render-abc", status)

    mock_daz.get("/requests/render-abc/status").mock(side_effect=status_side_effect)
    mock_daz.get("/requests/render-abc/result").mock(
        return_value=_result_response("render-abc", result={"done": True})
    )

    result = await daz_wait_for_request("render-abc", poll_interval_seconds=0.0)
    assert call_count == 3
    assert result["result"]["done"] is True


async def test_daz_wait_for_request_failed(mock_daz):
    mock_daz.get("/requests/render-abc/status").mock(
        return_value=_status_response("render-abc", "failed")
    )
    with pytest.raises(ToolError, match="failed"):
        await daz_wait_for_request("render-abc", poll_interval_seconds=0.0)


async def test_daz_wait_for_request_cancelled(mock_daz):
    """Cancelled is an intentional outcome — wait should return the status dict immediately."""
    mock_daz.get("/requests/render-abc/status").mock(
        return_value=_status_response("render-abc", "cancelled")
    )
    result = await daz_wait_for_request("render-abc", poll_interval_seconds=0.0)
    assert result["status"] == "cancelled"


async def test_daz_wait_for_request_timeout(mock_daz):
    import asyncio
    mock_daz.get("/requests/render-abc/status").mock(
        return_value=_status_response("render-abc", "running")
    )
    with pytest.raises(asyncio.TimeoutError):
        await daz_wait_for_request(
            "render-abc",
            poll_interval_seconds=0.0,
            timeout_seconds=0.0,
        )


# ---------------------------------------------------------------------------
# daz_save_scene_copy — routes through get_scene().save_copy(), not the
# script registry or the httpx client directly (dazpy's DazScene wraps
# POST /scene/save-copy over its own connection).
# ---------------------------------------------------------------------------

async def test_daz_save_scene_copy_ok(mock_scene):
    mock_scene.save_copy.return_value = {
        "ok": True,
        "path": "C:/backups/hero_v02.duf",
        "source": "C:/scenes/hero.duf",
        "method": "file-copy",
    }
    result = await daz_save_scene_copy("C:/backups/hero_v02.duf")
    assert result["ok"] is True
    assert result["path"] == "C:/backups/hero_v02.duf"
    assert result["source"] == "C:/scenes/hero.duf"
    assert result["method"] == "file-copy"


async def test_daz_save_scene_copy_sends_correct_path(mock_scene):
    mock_scene.save_copy.return_value = {
        "ok": True,
        "path": "C:/out/copy.duf",
        "source": "C:/scenes/orig.duf",
        "method": "file-copy",
    }
    await daz_save_scene_copy("C:/out/copy.duf")
    mock_scene.save_copy.assert_called_once_with("C:/out/copy.duf")


async def test_daz_save_scene_copy_dirty_scene(mock_scene):
    mock_scene.save_copy.return_value = {
        "ok": True,
        "path": "C:/backups/dirty.duf",
        "source": "C:/scenes/active.duf",
        "method": "save-restore",
    }
    result = await daz_save_scene_copy("C:/backups/dirty.duf")
    assert result["method"] == "save-restore"


async def test_daz_save_scene_copy_connect_error(mock_scene):
    mock_scene.save_copy.side_effect = daz_exc.ConnectionError("refused")
    with pytest.raises(ToolError, match="DAZ Studio is running"):
        await daz_save_scene_copy("C:/backups/hero.duf")


async def test_daz_save_scene_copy_does_not_use_script_registry(mock_daz, mock_scene):
    """Verify the tool calls get_scene().save_copy() and never hits the script registry."""
    registry_called = False

    def fail_if_registry(request):
        nonlocal registry_called
        registry_called = True
        return httpx.Response(200, json={})

    mock_daz.post("/scripts/vangard-save-scene/execute").mock(side_effect=fail_if_registry)
    mock_scene.save_copy.return_value = {
        "ok": True, "path": "C:/out.duf", "source": "C:/src.duf", "method": "file-copy",
    }
    await daz_save_scene_copy("C:/out.duf")
    assert not registry_called, "daz_save_scene_copy must not use the script registry"


# ---------------------------------------------------------------------------
# daz_wait_for_scene_event
# ---------------------------------------------------------------------------

import json as _json


def _sse_body(*events: dict) -> bytes:
    """Build a minimal SSE body from a list of event dicts."""
    lines = []
    for event in events:
        lines.append(f"data: {_json.dumps(event)}\n\n")
    return "".join(lines).encode()


async def test_daz_wait_for_scene_event_returns_matching_event(mock_daz):
    event = {"type": "render.finished", "ts": "2026-01-01T00:00:00Z", "data": {"path": "/out.png"}}
    mock_daz.get("/scene/events").mock(
        return_value=httpx.Response(
            200,
            content=_sse_body(event),
            headers={"content-type": "text/event-stream"},
        )
    )
    result = await daz_wait_for_scene_event(["render.finished"], timeout_seconds=5)
    assert result["type"] == "render.finished"
    assert result["data"]["path"] == "/out.png"


async def test_daz_wait_for_scene_event_skips_non_matching_events(mock_daz):
    """Events before the matching one should be skipped."""
    events = [
        {"type": "time.changed", "ts": "2026-01-01T00:00:00Z", "data": {}},
        {"type": "scene.loaded", "ts": "2026-01-01T00:00:01Z", "data": {"file": "hero.duf"}},
    ]
    mock_daz.get("/scene/events").mock(
        return_value=httpx.Response(
            200,
            content=_sse_body(*events),
            headers={"content-type": "text/event-stream"},
        )
    )
    result = await daz_wait_for_scene_event(["scene.loaded"], timeout_seconds=5)
    assert result["type"] == "scene.loaded"


async def test_daz_wait_for_scene_event_multiple_types(mock_daz):
    """Returns first event whose type is in the requested set."""
    events = [
        {"type": "node.added", "ts": "2026-01-01T00:00:00Z", "data": {}},
        {"type": "render.started", "ts": "2026-01-01T00:00:01Z", "data": {}},
    ]
    mock_daz.get("/scene/events").mock(
        return_value=httpx.Response(
            200,
            content=_sse_body(*events),
            headers={"content-type": "text/event-stream"},
        )
    )
    result = await daz_wait_for_scene_event(
        ["render.started", "render.finished"], timeout_seconds=5
    )
    assert result["type"] == "render.started"


async def test_daz_wait_for_scene_event_stream_closed_without_match_raises(mock_daz):
    """If the stream ends without a matching event, ToolError is raised."""
    events = [
        {"type": "time.changed", "ts": "2026-01-01T00:00:00Z", "data": {}},
    ]
    mock_daz.get("/scene/events").mock(
        return_value=httpx.Response(
            200,
            content=_sse_body(*events),
            headers={"content-type": "text/event-stream"},
        )
    )
    with pytest.raises(ToolError, match="SSE stream closed"):
        await daz_wait_for_scene_event(["render.finished"], timeout_seconds=5)


async def test_daz_wait_for_scene_event_connect_error_raises(mock_daz):
    mock_daz.get("/scene/events").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(ToolError, match="DAZ Studio is running"):
        await daz_wait_for_scene_event(["render.finished"], timeout_seconds=5)


async def test_daz_wait_for_scene_event_empty_event_types_raises(mock_daz):
    with pytest.raises(ToolError, match="empty"):
        await daz_wait_for_scene_event([], timeout_seconds=5)


async def test_daz_wait_for_scene_event_filter_param_derived_from_categories(mock_daz):
    """The ?filter query param should use category prefixes, not full event type names."""
    event = {"type": "render.finished", "ts": "2026-01-01T00:00:00Z", "data": {}}

    captured_params = {}

    def capture_request(request):
        captured_params["filter"] = request.url.params.get("filter", "")
        return httpx.Response(
            200,
            content=_sse_body(event),
            headers={"content-type": "text/event-stream"},
        )

    mock_daz.get("/scene/events").mock(side_effect=capture_request)
    await daz_wait_for_scene_event(["render.finished", "scene.loaded"], timeout_seconds=5)

    # Filter should contain category prefixes, not full dotted names
    filter_val = captured_params["filter"]
    assert "render" in filter_val
    assert "scene" in filter_val
    assert "render.finished" not in filter_val
