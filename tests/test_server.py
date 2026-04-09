"""Tests for vangard-daz-mcp server tools."""

import pytest
import pytest_asyncio
import respx
import httpx
from fastmcp.exceptions import ToolError

import vangard_daz_mcp.server as server_module
from vangard_daz_mcp.server import (
    daz_status,
    daz_execute,
    daz_execute_file,
    daz_scene_info,
    daz_get_node,
    daz_set_property,
    daz_render,
    daz_load_file,
    _register_scripts,
    # Phase 1.5 async tools
    daz_render_async,
    daz_render_with_camera_async,
    daz_batch_render_cameras_async,
    daz_render_animation_async,
    daz_get_request_status,
    daz_get_request_result,
    daz_cancel_request,
    daz_list_requests,
    daz_set_render_quality,
    daz_wait_for_request,
)


BASE_URL = "http://localhost:18811"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(autouse=True)
async def http_client():
    """Provide a real AsyncClient (respx patches its transport per test)."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        server_module._http_client = client
        yield client
    server_module._http_client = None


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
    with pytest.raises(ToolError, match="401"):
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
    mock_daz.post("/execute").mock(return_value=_fail("ReferenceError: foo is not defined", ["line1"]))
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
    with pytest.raises(ToolError, match="401"):
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
            return httpx.Response(404, json={"success": False, "error": "Script not found: 'vangard-scene-info'"})
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
    mock_daz.post("/scripts/vangard-get-node/execute").mock(return_value=_fail("Node not found: Ghost"))
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
    mock_daz.post("/scripts/vangard-set-property/execute").mock(return_value=_fail("Node not found: Ghost"))
    with pytest.raises(ToolError, match="Node not found"):
        await daz_set_property("Ghost", "Rotation X", 0.0)


async def test_daz_set_property_prop_not_found(mock_daz):
    mock_daz.post("/scripts/vangard-set-property/execute").mock(return_value=_fail("Property not found: Foo on Genesis 9"))
    with pytest.raises(ToolError, match="Property not found"):
        await daz_set_property("Genesis 9", "Foo", 1.0)


async def test_daz_set_property_not_numeric(mock_daz):
    mock_daz.post("/scripts/vangard-set-property/execute").mock(return_value=_fail("Property is not numeric: Label"))
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

async def test_daz_load_file_merge(mock_daz):
    mock_daz.post("/scripts/vangard-load-file/execute").mock(
        return_value=_ok({"success": True, "file": "C:/scenes/char.duf"})
    )
    result = await daz_load_file("C:/scenes/char.duf")
    assert result["success"] is True
    assert result["file"] == "C:/scenes/char.duf"


async def test_daz_load_file_replace(mock_daz):
    mock_daz.post("/scripts/vangard-load-file/execute").mock(
        return_value=_ok({"success": True, "file": "C:/scenes/scene.duf"})
    )
    result = await daz_load_file("C:/scenes/scene.duf", merge=False)
    assert result["success"] is True


async def test_daz_load_file_not_found(mock_daz):
    mock_daz.post("/scripts/vangard-load-file/execute").mock(return_value=_fail("File not found: C:/missing.duf"))
    with pytest.raises(ToolError, match="File not found"):
        await daz_load_file("C:/missing.duf")


# ---------------------------------------------------------------------------
# Phase 1.5: Async operations — helpers
# ---------------------------------------------------------------------------

def _async_submitted(request_id: str, script_id: str = "vangard-render") -> httpx.Response:
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
            "completed_at": "2026-04-08T12:00:10.000" if status in ("completed", "failed", "cancelled") else None,
        },
    )


def _result_response(request_id: str, status: str = "completed", result=None, error: str = "") -> httpx.Response:
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
# daz_render_async
# ---------------------------------------------------------------------------

async def test_daz_render_async_ok(mock_daz):
    mock_daz.post("/scripts/vangard-render/async").mock(
        return_value=_async_submitted("render-abc123")
    )
    result = await daz_render_async()
    assert result["request_id"] == "render-abc123"
    assert result["status"] == "queued"


async def test_daz_render_async_with_path(mock_daz):
    mock_daz.post("/scripts/vangard-render/async").mock(
        return_value=_async_submitted("render-def456")
    )
    result = await daz_render_async(output_path="C:/renders/out.png")
    assert result["request_id"] == "render-def456"


async def test_daz_render_async_retries_on_404(mock_daz):
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(404, json={"error": "Script not found"})
        return _async_submitted("render-retry")

    mock_daz.post("/scripts/vangard-render/async").mock(side_effect=side_effect)
    mock_daz.post("/scripts/register").mock(
        return_value=httpx.Response(200, json={"success": True, "id": "x", "updated": False})
    )

    result = await daz_render_async()
    assert result["request_id"] == "render-retry"
    assert call_count == 2


async def test_daz_render_async_connect_error(mock_daz):
    mock_daz.post("/scripts/vangard-render/async").mock(
        side_effect=httpx.ConnectError("refused")
    )
    with pytest.raises(ToolError, match="DAZ Studio is running"):
        await daz_render_async()


# ---------------------------------------------------------------------------
# daz_render_with_camera_async
# ---------------------------------------------------------------------------

async def test_daz_render_with_camera_async_ok(mock_daz):
    mock_daz.post("/scripts/vangard-render-with-camera/async").mock(
        return_value=_async_submitted("render-cam-abc")
    )
    result = await daz_render_with_camera_async("Camera 1", "C:/out.png")
    assert result["request_id"] == "render-cam-abc"
    assert result["status"] == "queued"


# ---------------------------------------------------------------------------
# daz_batch_render_cameras_async
# ---------------------------------------------------------------------------

async def test_daz_batch_render_cameras_async_ok(mock_daz):
    cameras = ["Cam_0", "Cam_90", "Cam_180"]
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        rid = f"render-batch-{call_count}"
        call_count += 1
        return _async_submitted(rid)

    mock_daz.post("/scripts/vangard-render-with-camera/async").mock(side_effect=side_effect)

    result = await daz_batch_render_cameras_async(cameras, "/renders/turntable", "angle")
    assert result["total"] == 3
    assert len(result["request_ids"]) == 3
    assert result["cameras"] == cameras


async def test_daz_batch_render_cameras_async_single(mock_daz):
    mock_daz.post("/scripts/vangard-render-with-camera/async").mock(
        return_value=_async_submitted("render-single")
    )
    result = await daz_batch_render_cameras_async(["OnlyCam"], "/out")
    assert result["total"] == 1
    assert result["request_ids"][0] == "render-single"


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


async def test_daz_get_request_result_cancelled_raises(mock_daz):
    mock_daz.get("/requests/render-abc/result").mock(
        return_value=_result_response("render-abc", status="cancelled")
    )
    with pytest.raises(ToolError, match="cancelled"):
        await daz_get_request_result("render-abc")


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
    with pytest.raises(httpx.HTTPStatusError, match="404"):
        await daz_get_request_result("missing")


# ---------------------------------------------------------------------------
# daz_cancel_request
# ---------------------------------------------------------------------------

async def test_daz_cancel_request_queued(mock_daz):
    mock_daz.delete("/requests/render-abc").mock(
        return_value=httpx.Response(
            200,
            json={
                "request_id": "render-abc",
                "status": "cancelled",
                "cancelled_at": "2026-04-08T12:00:05.000",
            },
        )
    )
    result = await daz_cancel_request("render-abc")
    assert result["status"] == "cancelled"
    assert result["request_id"] == "render-abc"


async def test_daz_cancel_request_already_done(mock_daz):
    mock_daz.delete("/requests/render-abc").mock(
        return_value=httpx.Response(
            409, json={"error": "Cannot cancel completed request"}
        )
    )
    with pytest.raises(httpx.HTTPStatusError, match="409"):
        await daz_cancel_request("render-abc")


async def test_daz_cancel_request_not_found(mock_daz):
    mock_daz.delete("/requests/missing").mock(
        return_value=httpx.Response(404, json={"error": "Request not found"})
    )
    with pytest.raises(httpx.HTTPStatusError, match="404"):
        await daz_cancel_request("missing")


# ---------------------------------------------------------------------------
# daz_list_requests
# ---------------------------------------------------------------------------

_LIST_RESPONSE = {
    "requests": [
        {"request_id": "render-aaa", "status": "completed", "progress": 1.0, "submitted_at": "2026-04-08T12:00:00.000"},
        {"request_id": "render-bbb", "status": "queued",    "progress": 0.0, "submitted_at": "2026-04-08T12:01:00.000"},
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
    mock_daz.get("/requests/render-abc/status").mock(
        return_value=_status_response("render-abc", "cancelled")
    )
    with pytest.raises(ToolError, match="cancelled"):
        await daz_wait_for_request("render-abc", poll_interval_seconds=0.0)


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
