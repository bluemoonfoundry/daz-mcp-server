"""Mock tests for Phase 6.12 tool: daz_load_morph_pro.

All tests use respx to intercept HTTP at the transport layer — no DAZ Studio
or DazScriptServer required. Per SKILL_DAZSCRIPT.md's "Morph Loader Pro"
gotchas, load_mode validity is node-type-dependent (plain prop -> PrimaryNode
only; legacy figure -> EntireFigure/SelectedNodes/PrimaryNode; single-skin
figure -> SingleSkinFigure/SingleSkinFigureFromGraft only) — the DazScriptServer
enforces this, so these tests mock the server's success/failure responses for
each branch rather than re-implementing the enum logic.
"""

from __future__ import annotations

import json

import pytest
import pytest_asyncio
import respx
import httpx
from fastmcp.exceptions import ToolError

from dazpy.aio import AsyncDazClient
from vangard_daz_mcp._client import set_async_daz_client
from vangard_daz_mcp.tools.morph import daz_load_morph_pro

BASE_URL = "http://localhost:18811"


def _ok(result):
    return httpx.Response(
        200,
        json={"success": True, "result": result, "output": [], "error": None},
    )


def _fail(error):
    return httpx.Response(
        200,
        json={"success": False, "result": None, "output": [], "error": error},
    )


@pytest_asyncio.fixture(autouse=True)
async def daz_client():
    """Provide the protocol client (respx patches its internal transport)."""
    # check_version=False keeps the version probe out of the recorded calls.
    async with AsyncDazClient(
        host="localhost", port=18811, token="", check_version=False
    ) as client:
        set_async_daz_client(client)
        yield client
    set_async_daz_client(None)


@pytest.fixture
def mock_daz():
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


def _capture(store):
    def side_effect(request, route):
        store["args"] = json.loads(request.content).get("args", {})
        return _ok({"success": True, "node": "Target", "morphName": "MyMorph"})

    return side_effect


class TestLoadModeByNodeType:
    """Per-node-type load-mode branches — the acceptance criterion this issue
    exists to cover (the original fork commit shipped no tests at all)."""

    async def test_prop_requires_primary_node(self, mock_daz):
        captured = {}
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            side_effect=_capture(captured)
        )
        result = await daz_load_morph_pro(
            "My Prop", "C:/morphs/prop_bulge.obj", load_mode="PrimaryNode"
        )
        assert result["success"] is True
        assert captured["args"]["loadMode"] == "PrimaryNode"

    async def test_prop_with_entire_figure_raises(self, mock_daz):
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            return_value=_fail(
                "setLoadMode failed for mode EntireFigure on node My Prop"
            )
        )
        with pytest.raises(ToolError):
            await daz_load_morph_pro(
                "My Prop", "C:/morphs/prop_bulge.obj", load_mode="EntireFigure"
            )

    async def test_legacy_figure_entire_figure(self, mock_daz):
        captured = {}
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            side_effect=_capture(captured)
        )
        result = await daz_load_morph_pro(
            "Genesis 8 Female", "C:/morphs/bicep_flex.obj", load_mode="EntireFigure"
        )
        assert result["success"] is True
        assert captured["args"]["loadMode"] == "EntireFigure"

    async def test_legacy_figure_selected_nodes(self, mock_daz):
        captured = {}
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            side_effect=_capture(captured)
        )
        await daz_load_morph_pro(
            "Genesis 8 Female", "C:/morphs/bicep_flex.obj", load_mode="SelectedNodes"
        )
        assert captured["args"]["loadMode"] == "SelectedNodes"

    async def test_single_skin_figure_requires_single_skin_mode(self, mock_daz):
        captured = {}
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            side_effect=_capture(captured)
        )
        result = await daz_load_morph_pro(
            "Genesis 9", "C:/morphs/bicep_flex.obj", load_mode="SingleSkinFigure"
        )
        assert result["success"] is True
        assert captured["args"]["loadMode"] == "SingleSkinFigure"

    async def test_single_skin_figure_with_entire_figure_raises(self, mock_daz):
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            return_value=_fail(
                "setLoadMode failed for mode EntireFigure on node Genesis 9"
            )
        )
        with pytest.raises(ToolError):
            await daz_load_morph_pro(
                "Genesis 9", "C:/morphs/bicep_flex.obj", load_mode="EntireFigure"
            )

    async def test_single_skin_figure_from_graft(self, mock_daz):
        captured = {}
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            side_effect=_capture(captured)
        )
        await daz_load_morph_pro(
            "Genesis 9",
            "C:/morphs/graft_patch.obj",
            load_mode="SingleSkinFigureFromGraft",
        )
        assert captured["args"]["loadMode"] == "SingleSkinFigureFromGraft"


class TestBasicBehavior:
    async def test_node_not_found_raises(self, mock_daz):
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            return_value=_fail("Node not found: Ghost")
        )
        with pytest.raises(ToolError):
            await daz_load_morph_pro("Ghost", "C:/morphs/x.obj")

    async def test_missing_morph_loader_plugin_raises(self, mock_daz):
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            return_value=_fail(
                "DzMorphLoader is not available (enable the Morph Loader Pro plugin)"
            )
        )
        with pytest.raises(ToolError):
            await daz_load_morph_pro("Genesis 9", "C:/morphs/x.obj")

    async def test_default_args_sent(self, mock_daz):
        captured = {}
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            side_effect=_capture(captured)
        )
        await daz_load_morph_pro("Genesis 9", "C:/morphs/bicep_flex.obj")
        args = captured["args"]
        assert args["nodeLabel"] == "Genesis 9"
        assert args["objPath"] == "C:/morphs/bicep_flex.obj"
        assert args["loadMode"] == "EntireFigure"
        assert args["overwriteMode"] == "MakeUnique"
        assert args["mirroring"] == "DoNotMirror"
        assert args["scale"] == 1.0
        assert args["reverseDeformations"] is False
        assert args["createControlProperty"] is False
        assert args["onlyErrorsOrWarnings"] is True
        # Optional fields omitted entirely when not passed.
        assert "morphName" not in args
        assert "subdivision" not in args
        assert "attenuateStrength" not in args
        assert "controlPropertyName" not in args

    async def test_resolved_morph_name_returned(self, mock_daz):
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            return_value=_ok(
                {
                    "success": True,
                    "node": "Genesis 9",
                    "file": "C:/morphs/bicep_flex.obj",
                    "morphName": "BicepFlex 2",
                    "loadMode": "EntireFigure",
                    "overwriteMode": "MakeUnique",
                    "mirroring": "DoNotMirror",
                    "controlProperty": None,
                    "log": "",
                }
            )
        )
        result = await daz_load_morph_pro(
            "Genesis 9", "C:/morphs/bicep_flex.obj", morph_name="BicepFlex"
        )
        # MakeUnique renamed the dial — resolved name differs from the requested one.
        assert result["morphName"] == "BicepFlex 2"

    async def test_rename_dialog_collision_surfaces_as_tool_error(self, mock_daz):
        # Confirmed live (SKILL_DAZSCRIPT.md): MakeUnique does not silently
        # resolve a name collision; DAZ Studio blocks on an interactive
        # rename dialog. The bridge cannot click through that dialog, so a
        # collision must surface as an error rather than hang.
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            return_value=_fail(
                "createMorph blocked on interactive rename dialog for existing "
                "morph 'BicepFlex' — pass a unique morph_name"
            )
        )
        with pytest.raises(ToolError):
            await daz_load_morph_pro(
                "Genesis 9", "C:/morphs/bicep_flex.obj", morph_name="BicepFlex"
            )


class TestOptionalFieldsSent:
    async def test_subdivision_options_sent(self, mock_daz):
        captured = {}
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            side_effect=_capture(captured)
        )
        await daz_load_morph_pro(
            "Genesis 9",
            "C:/morphs/bicep_flex.obj",
            subdivision=True,
            subdivision_mapping="Catmark",
            subdivision_min_resolution=0,
            subdivision_max_resolution=2,
            subdivision_built_resolution=1,
            subdivision_smooth_cage=True,
        )
        args = captured["args"]
        assert args["subdivision"] is True
        assert args["subdivisionMapping"] == "Catmark"
        assert args["subdivisionMinResolution"] == 0
        assert args["subdivisionMaxResolution"] == 2
        assert args["subdivisionBuiltResolution"] == 1
        assert args["subdivisionSmoothCage"] is True

    async def test_attenuation_options_sent(self, mock_daz):
        captured = {}
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            side_effect=_capture(captured)
        )
        await daz_load_morph_pro(
            "Genesis 9",
            "C:/morphs/bicep_flex.obj",
            attenuate_strength=0.5,
            attenuate_edge_strength=0.25,
            attenuate_map_path="C:/maps/weight.png",
        )
        args = captured["args"]
        assert args["attenuateStrength"] == 0.5
        assert args["attenuateEdgeStrength"] == 0.25
        assert args["attenuateMapPath"] == "C:/maps/weight.png"

    async def test_reverse_deformations_options_sent(self, mock_daz):
        captured = {}
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            side_effect=_capture(captured)
        )
        await daz_load_morph_pro(
            "Genesis 9",
            "C:/morphs/posed_export.obj",
            reverse_deformations=True,
            reverse_deformations_pose_path="C:/poses/tpose.duf",
        )
        args = captured["args"]
        assert args["reverseDeformations"] is True
        assert args["reverseDeformationsPosePath"] == "C:/poses/tpose.duf"


class TestControlProperty:
    async def test_create_control_property_sends_erc_fields(self, mock_daz):
        captured = {}
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            side_effect=_capture(captured)
        )
        await daz_load_morph_pro(
            "Genesis 9",
            "C:/morphs/bicep_flex.obj",
            morph_name="BicepFlex",
            create_control_property=True,
            control_node_label="Genesis 9",
            control_property_name="Bicep Flex",
            control_property_custom_label="Flex",
            control_property_erc_type="ERCDeltaAdd",
            control_property_erc_custom_value=1.0,
        )
        args = captured["args"]
        assert args["createControlProperty"] is True
        assert args["controlNodeLabel"] == "Genesis 9"
        assert args["controlPropertyName"] == "Bicep Flex"
        assert args["controlPropertyCustomLabel"] == "Flex"
        assert args["controlPropertyErcType"] == "ERCDeltaAdd"
        assert args["controlPropertyErcCustomValue"] == 1.0

    async def test_create_control_property_without_name_raises_locally(self, mock_daz):
        # Guarded client-side — must not even hit the network.
        route = mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            return_value=_ok({"success": True})
        )
        with pytest.raises(ToolError, match="control_property_name is required"):
            await daz_load_morph_pro(
                "Genesis 9",
                "C:/morphs/bicep_flex.obj",
                create_control_property=True,
            )
        assert route.call_count == 0

    async def test_control_property_not_found_raises(self, mock_daz):
        mock_daz.post("/scripts/vangard-load-morph-pro/execute").mock(
            return_value=_fail(
                "Control property not found: Ghost Dial on Genesis 9"
            )
        )
        with pytest.raises(ToolError):
            await daz_load_morph_pro(
                "Genesis 9",
                "C:/morphs/bicep_flex.obj",
                create_control_property=True,
                control_property_name="Ghost Dial",
            )
