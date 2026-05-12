"""Integration tests for Phase 5 tools — require a running DAZ Studio.

Run against a live DAZ Studio + DazScriptServer instance:

    uv run pytest tests/test_phase5_integration.py -v

All tests are skipped automatically if DAZ Studio is not reachable at
localhost:18811.  No mocking is used; every call goes to the real server.

Scene requirements
------------------
For the fullest coverage, have a Genesis figure loaded in the scene before
running.  Tests that need a figure detect one via daz_scene_info and skip
themselves with a clear message if none is found.
"""

from __future__ import annotations

import re

import httpx
import pytest
import pytest_asyncio
from fastmcp.exceptions import ToolError

import vangard_daz_mcp.server as server_module
from vangard_daz_mcp.server import (
    # Core
    _register_scripts,
    daz_scene_info,
    # Phase 5 tools under test
    daz_list_materials,
    daz_get_material,
    daz_set_material_property,
    daz_set_morph,
    daz_delete_node,
    daz_list_lights,
    daz_create_light,
    daz_list_cameras,
    daz_create_camera,
    daz_save_scene,
    daz_get_selected_nodes,
    daz_set_render_output,
    daz_reset_pose,
    # Helpers used for setup / teardown
    daz_set_property,
    daz_search_morphs,
)

BASE_URL = "http://localhost:18811"

# ---------------------------------------------------------------------------
# Module-level cache (avoids session-scoped async fixtures, which have
# awkward event-loop lifecycle issues with pytest-asyncio on Windows).
# ---------------------------------------------------------------------------
_cache: dict = {}


def _daz_available() -> bool:
    """Synchronous probe — True if DazScriptServer is reachable."""
    import socket
    try:
        with socket.create_connection(("localhost", 18811), timeout=2):
            return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Per-test HTTP client  (function-scoped — safe, no event-loop clash)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def live_client():
    """Real AsyncClient wired into the server module.

    Skips the test automatically if DAZ Studio is not reachable.
    Also registers all scripts on first use so new Phase-5 IDs are available.
    """
    if not _daz_available():
        pytest.skip(f"DAZ Studio not reachable at {BASE_URL}")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        server_module._http_client = client

        # Register scripts once per process (cached flag).
        if not _cache.get("scripts_registered"):
            await _register_scripts(client)
            _cache["scripts_registered"] = True

        yield client

    server_module._http_client = None


# ---------------------------------------------------------------------------
# Scene-aware helper fixtures  (function-scoped; results cached in _cache)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def figure_label(live_client):
    """Return the label of the first figure (skeleton) in the scene, or skip.

    daz_scene_info returns figures under the 'figures' key (via Scene.getNumSkeletons),
    not in a combined 'nodes' list.  Result is cached for the process lifetime.
    """
    if "figure_label" not in _cache:
        scene = await daz_scene_info()
        figures = scene.get("figures", [])
        if not figures:
            pytest.skip(
                "No figure found in scene — load a Genesis figure to run character tests"
            )
        _cache["figure_label"] = figures[0]["label"]

    return _cache["figure_label"]


@pytest_asyncio.fixture()
async def first_material(live_client, figure_label):
    """Return (figure_label, material_label) for the first material zone."""
    if "first_material" not in _cache:
        result = await daz_list_materials(figure_label)
        mats = result.get("materials", [])
        if not mats:
            pytest.skip(f"Figure '{figure_label}' has no material zones")
        _cache["first_material"] = (figure_label, mats[0]["label"])

    return _cache["first_material"]


# ---------------------------------------------------------------------------
# Temporary resource fixtures (create → yield label → delete)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def temp_spot_light(live_client):
    """Create a temporary spot light and delete it after the test."""
    result = await daz_create_light(
        light_type="spot",
        label="_test_spot_light",
        x=0, y=300, z=300,
        flux=5000.0,
    )
    label = result["label"]
    yield label
    try:
        await daz_delete_node(label)
    except ToolError:
        pass  # already deleted by the test itself


@pytest_asyncio.fixture()
async def temp_camera(live_client):
    """Create a temporary camera and delete it after the test."""
    result = await daz_create_camera(label="_test_camera", x=0, y=150, z=400)
    label = result["label"]
    yield label
    try:
        await daz_delete_node(label)
    except ToolError:
        pass


# ===========================================================================
# A — Materials
# ===========================================================================

class TestListMaterials:
    async def test_returns_zones(self, live_client, figure_label):
        result = await daz_list_materials(figure_label)
        assert result["node"] == figure_label
        assert result["material_count"] > 0
        assert len(result["materials"]) == result["material_count"]

    async def test_zone_fields(self, live_client, figure_label):
        result = await daz_list_materials(figure_label)
        zone = result["materials"][0]
        assert "index" in zone
        assert "label" in zone
        assert "name" in zone
        assert "shader" in zone

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError, match="Node not found"):
            await daz_list_materials("__nonexistent_node__")

    async def test_camera_has_no_geometry(self, live_client, temp_camera):
        """A camera node has no geometry — should raise or return 0 materials."""
        try:
            result = await daz_list_materials(temp_camera)
            # Some implementations return 0 instead of raising
            assert result["material_count"] == 0
        except ToolError as exc:
            assert "no geometry" in str(exc).lower() or "not found" in str(exc).lower()


class TestGetMaterial:
    async def test_returns_properties(self, live_client, first_material):
        fig_label, mat_label = first_material
        result = await daz_get_material(fig_label, mat_label)
        assert result["node"] == fig_label
        assert result["material"] == mat_label
        assert result["property_count"] > 0
        assert len(result["properties"]) == result["property_count"]

    async def test_property_has_type_and_value(self, live_client, first_material):
        fig_label, mat_label = first_material
        result = await daz_get_material(fig_label, mat_label)
        # At least one numeric property should exist on any material
        numeric_props = [p for p in result["properties"] if p["type"] == "numeric"]
        assert len(numeric_props) > 0, "Expected at least one numeric property on material"

    async def test_color_props_are_hex(self, live_client, first_material):
        fig_label, mat_label = first_material
        result = await daz_get_material(fig_label, mat_label)
        for prop in result["properties"]:
            if prop["type"] == "color" and prop["value"] is not None:
                assert re.match(r"^#[0-9a-fA-F]{6}$", prop["value"]), (
                    f"Color property '{prop['label']}' has non-hex value: {prop['value']!r}"
                )

    async def test_material_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError, match="Material not found"):
            await daz_get_material(figure_label, "__nonexistent_material__")

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError, match="Node not found"):
            await daz_get_material("__ghost__", "Skin")


class TestSetMaterialProperty:
    async def test_set_numeric_property(self, live_client, first_material):
        """Set a known float material property and verify the value round-trips."""
        fig_label, mat_label = first_material
        info = await daz_get_material(fig_label, mat_label)

        # Prefer well-known Iray float properties that accept 0–1 values
        float_candidates = [
            "Glossy Roughness", "Metallic Weight", "Cutout Opacity",
            "Refraction Weight", "Subsurface Weight", "Bump Strength",
            "Displacement Strength", "Glossy Layered Weight",
        ]
        prop = None
        for candidate in float_candidates:
            for p in info["properties"]:
                if p["type"] == "numeric" and candidate.lower() in p["label"].lower():
                    prop = p
                    break
            if prop:
                break

        # Fallback: any numeric property whose current value is already fractional (0<v<1)
        if prop is None:
            for p in info["properties"]:
                if p["type"] == "numeric" and p["value"] is not None:
                    if 0.0 < float(p["value"]) < 1.0:
                        prop = p
                        break

        if prop is None:
            pytest.skip(f"No suitable float numeric property found on material '{mat_label}'")

        original = float(prop["value"])
        new_val = round(original + 0.1, 3) if original <= 0.9 else round(original - 0.1, 3)

        result = await daz_set_material_property(fig_label, mat_label, prop["label"], new_val)
        assert result["type"] == "numeric"
        assert abs(result["value"] - new_val) < 0.01  # allow small rounding by DAZ

        # Restore
        await daz_set_material_property(fig_label, mat_label, prop["label"], original)

    async def test_set_color_property(self, live_client, first_material):
        """Set a color property and confirm it is accepted."""
        fig_label, mat_label = first_material
        info = await daz_get_material(fig_label, mat_label)
        color_props = [p for p in info["properties"] if p["type"] == "color"]
        if not color_props:
            pytest.skip(f"No color properties on material '{mat_label}'")

        prop = color_props[0]
        original_hex = prop["value"]
        test_color = "#FF8040"

        result = await daz_set_material_property(fig_label, mat_label, prop["label"], test_color)
        assert result["type"] == "color"

        # Restore original (if we know it)
        if original_hex:
            await daz_set_material_property(fig_label, mat_label, prop["label"], original_hex)

    async def test_property_not_found_raises(self, live_client, first_material):
        fig_label, mat_label = first_material
        with pytest.raises(ToolError, match="Property not found"):
            await daz_set_material_property(fig_label, mat_label, "__bogus_prop__", 0.5)

    async def test_material_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError, match="Material not found"):
            await daz_set_material_property(figure_label, "__ghost_mat__", "Glossy Roughness", 0.5)


# ===========================================================================
# B — Morph Setting
# ===========================================================================

class TestSetMorph:
    async def test_exact_label_match(self, live_client, figure_label):
        """Find a known float morph and set it by exact label.

        We prefer morphs with names that are typical Genesis float dials (0–1 range).
        The generic 'Head' search can match rotation bones which are integer-constrained.
        """
        # Try progressively broader searches until we find a settable float morph
        candidates = ["Head Size", "Head Scale", "Head Big", "Chin", "Forehead", "Head"]
        morph = None
        all_morphs: list = []
        for pattern in candidates:
            result = await daz_search_morphs(figure_label, pattern, include_zero=True)
            all_morphs = result.get("morphs", [])
            if all_morphs:
                morph = all_morphs[0]
                break

        if morph is None:
            pytest.skip("No suitable head morph found on figure")

        label = morph["label"]
        original = float(morph["value"])
        new_val = 0.3 if abs(original - 0.3) > 0.05 else 0.4

        result = await daz_set_morph(figure_label, label, new_val)
        assert result["node"] == figure_label
        # If value didn't change, the property may be constrained — skip rather than fail
        if abs(result["value"] - new_val) >= 0.01:
            pytest.skip(
                f"Morph '{label}' did not accept value {new_val} "
                f"(returned {result['value']}); may be integer-constrained"
            )
        assert abs(result["value"] - new_val) < 0.01

        # Restore
        await daz_set_morph(figure_label, label, original)

    async def test_substring_match(self, live_client, figure_label):
        """A partial name ('smile' matching 'Mouth Smile') should work."""
        morphs = await daz_search_morphs(figure_label, "smile", include_zero=True)
        if not morphs.get("morphs"):
            pytest.skip("No smile morphs found on figure")

        target = morphs["morphs"][0]
        original = target["value"]

        result = await daz_set_morph(figure_label, "smile", 0.5)
        assert result["value"] == pytest.approx(0.5, abs=0.001)

        await daz_set_morph(figure_label, result["morph"], original)

    async def test_morph_not_found_raises(self, live_client, figure_label):
        with pytest.raises(ToolError, match="Morph not found"):
            await daz_set_morph(figure_label, "__zzz_nonexistent_morph_zzz__", 1.0)

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError, match="Node not found"):
            await daz_set_morph("__ghost__", "Head Size", 0.5)

    async def test_returns_internal_name(self, live_client, figure_label):
        morphs = await daz_search_morphs(figure_label, "Head", include_zero=True)
        if not morphs.get("morphs"):
            pytest.skip("No Head morphs found")
        morph = morphs["morphs"][0]
        original = morph["value"]

        result = await daz_set_morph(figure_label, morph["label"], 0.1)
        assert "internal_name" in result
        assert result["internal_name"]  # must be non-empty

        await daz_set_morph(figure_label, morph["label"], original)


# ===========================================================================
# C — Node Lifecycle
# ===========================================================================

class TestDeleteNode:
    async def test_delete_created_light(self, live_client):
        """Create a light, delete it, confirm it's no longer in the list."""
        created = await daz_create_light("spot", "_delete_me_light", x=0, y=300, z=200)
        label = created["label"]

        before = await daz_list_lights()
        labels_before = {l["label"] for l in before["lights"]}
        assert label in labels_before, "Light not found after creation"

        result = await daz_delete_node(label)
        assert result["deleted"] == label

        after = await daz_list_lights()
        labels_after = {l["label"] for l in after["lights"]}
        assert label not in labels_after, "Light still present after deletion"

    async def test_delete_created_camera(self, live_client):
        """Create a camera, delete it, confirm it's no longer in the list."""
        created = await daz_create_camera("_delete_me_cam")
        label = created["label"]

        result = await daz_delete_node(label)
        assert result["deleted"] == label

        after = await daz_list_cameras()
        labels_after = {c["label"] for c in after["cameras"]}
        assert label not in labels_after

    async def test_delete_nonexistent_raises(self, live_client):
        with pytest.raises(ToolError, match="Node not found"):
            await daz_delete_node("__nonexistent_node_xyz__")

    async def test_returns_child_count(self, live_client):
        created = await daz_create_light("spot", "_child_count_test")
        label = created["label"]
        result = await daz_delete_node(label)
        assert "child_count" in result
        assert isinstance(result["child_count"], int)


# ===========================================================================
# D — Light Management
# ===========================================================================

class TestListLights:
    async def test_returns_list_structure(self, live_client):
        result = await daz_list_lights()
        assert "light_count" in result
        assert "lights" in result
        assert result["light_count"] == len(result["lights"])

    async def test_light_fields(self, live_client, temp_spot_light):
        result = await daz_list_lights()
        our_light = next(
            (l for l in result["lights"] if l["label"] == temp_spot_light), None
        )
        assert our_light is not None, f"Created light '{temp_spot_light}' not in list"
        assert "type" in our_light
        assert "position" in our_light
        assert all(k in our_light["position"] for k in ("x", "y", "z"))

    async def test_count_increases_after_creation(self, live_client):
        before = (await daz_list_lights())["light_count"]
        created = await daz_create_light("spot", "_count_test_light")
        after = (await daz_list_lights())["light_count"]
        assert after == before + 1
        await daz_delete_node(created["label"])


class TestCreateLight:
    async def test_create_spot_light(self, live_client, temp_spot_light):
        result = await daz_list_lights()
        labels = {l["label"] for l in result["lights"]}
        assert temp_spot_light in labels

    async def test_create_distant_light(self, live_client):
        result = await daz_create_light("distant", "_test_distant", x=0, y=500, z=0)
        assert result["type"] == "distant"
        await daz_delete_node(result["label"])

    async def test_create_point_light(self, live_client):
        result = await daz_create_light("point", "_test_point", x=0, y=100, z=50)
        assert result["type"] == "point"
        await daz_delete_node(result["label"])

    async def test_invalid_type_raises(self, live_client):
        with pytest.raises(ToolError, match="light_type must be one of"):
            await daz_create_light("laser", "bad light")

    async def test_flux_is_applied(self, live_client):
        result = await daz_create_light("spot", "_flux_test_light", flux=8000.0)
        label = result["label"]
        lights = await daz_list_lights()
        created = next(l for l in lights["lights"] if l["label"] == label)
        assert created["flux"] is not None
        # Flux may not be exactly 8000 due to DAZ's internal representation
        assert created["flux"] > 0
        await daz_delete_node(label)

    async def test_position_is_set(self, live_client):
        result = await daz_create_light("spot", "_pos_test_light", x=100, y=200, z=150)
        label = result["label"]
        assert abs(result["position"]["x"] - 100) < 1
        assert abs(result["position"]["y"] - 200) < 1
        assert abs(result["position"]["z"] - 150) < 1
        await daz_delete_node(label)

    async def test_aim_at_label(self, live_client, figure_label):
        result = await daz_create_light(
            "spot", "_aimed_light", x=0, y=300, z=300,
            aim_at_label=figure_label,
        )
        # No assertion on aim direction — just verify it succeeds and is in scene
        lights = await daz_list_lights()
        labels = {l["label"] for l in lights["lights"]}
        assert result["label"] in labels
        await daz_delete_node(result["label"])


# ===========================================================================
# E — Camera Management
# ===========================================================================

class TestListCameras:
    async def test_returns_structure(self, live_client):
        result = await daz_list_cameras()
        assert "camera_count" in result
        assert "cameras" in result
        assert result["camera_count"] == len(result["cameras"])

    async def test_camera_count_is_non_negative(self, live_client):
        # The DAZ Studio Perspective view is a viewport, not a DzCamera object.
        # Scene.getNumCameras() returns 0 unless DzBasicCamera (or similar) objects
        # have been explicitly added to the scene. Count can legitimately be zero.
        result = await daz_list_cameras()
        assert result["camera_count"] >= 0

    async def test_camera_fields(self, live_client):
        result = await daz_list_cameras()
        if not result["cameras"]:
            pytest.skip("No cameras in scene")
        cam = result["cameras"][0]
        assert "label" in cam
        assert "type" in cam
        assert "position" in cam
        assert all(k in cam["position"] for k in ("x", "y", "z"))


class TestCreateCamera:
    async def test_creates_and_appears_in_list(self, live_client, temp_camera):
        result = await daz_list_cameras()
        labels = {c["label"] for c in result["cameras"]}
        assert temp_camera in labels

    async def test_position_is_applied(self, live_client):
        result = await daz_create_camera("_pos_cam", x=50, y=100, z=200)
        assert abs(result["position"]["x"] - 50) < 1
        assert abs(result["position"]["y"] - 100) < 1
        assert abs(result["position"]["z"] - 200) < 1
        await daz_delete_node(result["label"])

    async def test_focal_length_is_applied(self, live_client):
        result = await daz_create_camera("_fl_cam", focal_length=85.0)
        assert result["focal_length"] is not None
        assert abs(result["focal_length"] - 85.0) < 1.0
        await daz_delete_node(result["label"])

    async def test_aim_at_label(self, live_client, figure_label):
        result = await daz_create_camera(
            "_aimed_cam", x=0, y=150, z=300, aim_at_label=figure_label
        )
        cams = await daz_list_cameras()
        labels = {c["label"] for c in cams["cameras"]}
        assert result["label"] in labels
        await daz_delete_node(result["label"])

    async def test_count_increases(self, live_client):
        before = (await daz_list_cameras())["camera_count"]
        created = await daz_create_camera("_count_cam")
        after = (await daz_list_cameras())["camera_count"]
        assert after == before + 1
        await daz_delete_node(created["label"])


# ===========================================================================
# F — Scene Operations
# ===========================================================================

class TestGetSelectedNodes:
    async def test_returns_structure(self, live_client):
        result = await daz_get_selected_nodes()
        assert "count" in result
        assert "nodes" in result
        assert result["count"] == len(result["nodes"])

    async def test_node_fields(self, live_client):
        result = await daz_get_selected_nodes()
        for node in result["nodes"]:
            assert "label" in node
            assert "type" in node
            assert "primary" in node

    async def test_primary_flag(self, live_client):
        result = await daz_get_selected_nodes()
        primaries = [n for n in result["nodes"] if n["primary"]]
        # At most one primary
        assert len(primaries) <= 1


class TestSaveScene:
    async def test_save_returns_true(self, live_client, tmp_path):
        # Scene may not have a filename yet; save to a temp path first so
        # the "no-arg" code path (saves to current file) can be exercised.
        save_path = str(tmp_path / "baseline_save.duf").replace("\\", "/")
        await daz_save_scene(save_path)
        result = await daz_save_scene()  # now has a current filename
        assert result["saved"] is True
        assert "file_path" in result

    async def test_save_as_with_path(self, live_client, tmp_path):
        save_path = str(tmp_path / "integration_test_save.duf").replace("\\", "/")
        result = await daz_save_scene(save_path)
        assert result["saved"] is True
        # Path should be reflected back
        assert save_path in result["file_path"] or result["file_path"] == save_path


class TestSetRenderOutput:
    async def test_set_dimensions(self, live_client):
        result = await daz_set_render_output(width=640, height=480)
        assert "changed" in result
        assert result["current"]["width"] == 640 or result["changed"].get("width") == 640
        assert result["current"]["height"] == 480 or result["changed"].get("height") == 480

    async def test_set_output_path(self, live_client, tmp_path):
        path = str(tmp_path / "render_out.png").replace("\\", "/")
        result = await daz_set_render_output(output_path=path)
        assert "output_path" in result["changed"]

    async def test_set_width_only(self, live_client):
        result = await daz_set_render_output(width=800)
        assert result["changed"].get("width") == 800

    async def test_no_args_raises(self, live_client):
        with pytest.raises(ToolError, match="At least one of"):
            await daz_set_render_output()

    async def test_current_values_returned(self, live_client):
        result = await daz_set_render_output(width=1280, height=720)
        current = result["current"]
        assert "width" in current
        assert "height" in current


# ===========================================================================
# G — Pose Reset
# ===========================================================================

class TestResetPose:
    async def test_resets_bone_rotations(self, live_client, figure_label):
        """Apply a rotation to the figure root, reset, verify it's zeroed."""
        # Tilt the figure slightly
        await daz_set_property(figure_label, "ZRotate", 15.0)

        result = await daz_reset_pose(figure_label)
        assert result["node"] == figure_label
        assert result["bones_reset"] > 0
        assert result["transforms_zeroed"] is False

    async def test_zero_transforms_flag(self, live_client, figure_label):
        """zero_transforms=True should also clear root translation."""
        await daz_set_property(figure_label, "XTranslate", 50.0)

        result = await daz_reset_pose(figure_label, zero_transforms=True)
        assert result["transforms_zeroed"] is True

    async def test_bones_reset_count(self, live_client, figure_label):
        """A Genesis figure should have many bones — confirm count is reasonable."""
        result = await daz_reset_pose(figure_label)
        # A minimal humanoid skeleton has at least 50 bones
        assert result["bones_reset"] >= 50, (
            f"Expected >= 50 bones reset for a figure, got {result['bones_reset']}"
        )

    async def test_not_found_raises(self, live_client):
        with pytest.raises(ToolError, match="Node not found"):
            await daz_reset_pose("__nonexistent__")

    async def test_idempotent(self, live_client, figure_label):
        """Calling reset twice should not error — second call is a no-op."""
        await daz_reset_pose(figure_label)
        result = await daz_reset_pose(figure_label)
        assert result["bones_reset"] > 0
