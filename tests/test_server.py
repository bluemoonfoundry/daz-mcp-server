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
    mock_daz.post("/execute").mock(return_value=_ok(_SCENE_RESULT))
    result = await daz_scene_info()
    assert result["nodeCount"] == 2
    assert result["selectedNode"] == "Genesis 9"
    assert len(result["nodes"]) == 2


async def test_daz_scene_info_unsaved(mock_daz):
    payload = {**_SCENE_RESULT, "sceneFile": "", "selectedNode": None}
    mock_daz.post("/execute").mock(return_value=_ok(payload))
    result = await daz_scene_info()
    assert result["sceneFile"] == ""
    assert result["selectedNode"] is None


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
    mock_daz.post("/execute").mock(return_value=_ok(_NODE_RESULT))
    result = await daz_get_node("Genesis 9")
    assert result["label"] == "Genesis 9"
    assert result["properties"]["Rotation X"] == 15.0


async def test_daz_get_node_not_found(mock_daz):
    mock_daz.post("/execute").mock(return_value=_fail("Node not found: Ghost"))
    with pytest.raises(ToolError, match="Node not found"):
        await daz_get_node("Ghost")


# ---------------------------------------------------------------------------
# daz_set_property
# ---------------------------------------------------------------------------

async def test_daz_set_property_ok(mock_daz):
    mock_daz.post("/execute").mock(
        return_value=_ok({"node": "Genesis 9", "property": "Rotation X", "value": 45.0})
    )
    result = await daz_set_property("Genesis 9", "Rotation X", 45.0)
    assert result["value"] == 45.0
    assert result["property"] == "Rotation X"


async def test_daz_set_property_node_not_found(mock_daz):
    mock_daz.post("/execute").mock(return_value=_fail("Node not found: Ghost"))
    with pytest.raises(ToolError, match="Node not found"):
        await daz_set_property("Ghost", "Rotation X", 0.0)


async def test_daz_set_property_prop_not_found(mock_daz):
    mock_daz.post("/execute").mock(return_value=_fail("Property not found: Foo on Genesis 9"))
    with pytest.raises(ToolError, match="Property not found"):
        await daz_set_property("Genesis 9", "Foo", 1.0)


async def test_daz_set_property_not_numeric(mock_daz):
    mock_daz.post("/execute").mock(return_value=_fail("Property is not numeric: Label"))
    with pytest.raises(ToolError, match="not numeric"):
        await daz_set_property("Genesis 9", "Label", 1.0)


# ---------------------------------------------------------------------------
# daz_render
# ---------------------------------------------------------------------------

async def test_daz_render_default(mock_daz):
    mock_daz.post("/execute").mock(return_value=_ok({"success": True}))
    result = await daz_render()
    assert result["success"] is True


async def test_daz_render_with_output_path(mock_daz):
    mock_daz.post("/execute").mock(return_value=_ok({"success": True}))
    result = await daz_render(output_path="C:/renders/out.png")
    assert result["success"] is True



# ---------------------------------------------------------------------------
# daz_load_file
# ---------------------------------------------------------------------------

async def test_daz_load_file_merge(mock_daz):
    mock_daz.post("/execute").mock(
        return_value=_ok({"success": True, "file": "C:/scenes/char.duf"})
    )
    result = await daz_load_file("C:/scenes/char.duf")
    assert result["success"] is True
    assert result["file"] == "C:/scenes/char.duf"


async def test_daz_load_file_replace(mock_daz):
    mock_daz.post("/execute").mock(
        return_value=_ok({"success": True, "file": "C:/scenes/scene.duf"})
    )
    result = await daz_load_file("C:/scenes/scene.duf", merge=False)
    assert result["success"] is True


async def test_daz_load_file_not_found(mock_daz):
    mock_daz.post("/execute").mock(return_value=_fail("File not found: C:/missing.duf"))
    with pytest.raises(ToolError, match="File not found"):
        await daz_load_file("C:/missing.duf")
