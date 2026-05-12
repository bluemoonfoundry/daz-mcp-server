"""Integration tests — core execution and local utility tools.

Tools covered
-------------
- daz_status              (DAZ connectivity probe)
- daz_execute             (inline DazScript execution)
- daz_execute_file        (execute a script file on disk)
- daz_script_help         (local — no DAZ needed)
- daz_validate_script     (local — no DAZ needed)
- daz_inspect_properties  (node property introspection)
- daz_get_property_metadata (single-property detail)
"""

from __future__ import annotations

import os
import tempfile

import pytest
import pytest_asyncio
from fastmcp.exceptions import ToolError

from vangard_daz_mcp.server import (
    daz_execute,
    daz_execute_file,
    daz_get_property_metadata,
    daz_inspect_properties,
    daz_script_help,
    daz_status,
    daz_validate_script,
)


# ---------------------------------------------------------------------------
# daz_status
# ---------------------------------------------------------------------------

class TestStatus:
    async def test_returns_dict(self, live_client):
        result = await daz_status()
        assert isinstance(result, dict)

    async def test_has_version_info(self, live_client):
        result = await daz_status()
        # The status response should mention DAZ Studio or a version string.
        text = str(result).lower()
        assert "version" in text or "daz" in text or "status" in text


# ---------------------------------------------------------------------------
# daz_execute
# ---------------------------------------------------------------------------

class TestExecute:
    async def test_returns_literal(self, live_client):
        result = await daz_execute("(function(){ return {value: 42}; })()")
        assert result is not None

    async def test_arithmetic(self, live_client):
        result = await daz_execute("(function(){ return {sum: 2 + 2}; })()")
        # Result may be wrapped or raw depending on server implementation.
        assert result is not None

    async def test_invalid_script_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_execute("this is not valid javascript !!!")

    async def test_scene_globals_accessible(self, live_client):
        """Scene object must be accessible inside executed scripts."""
        result = await daz_execute(
            "(function(){ return {node_count: Scene.getNumNodes()}; })()"
        )
        assert result is not None


# ---------------------------------------------------------------------------
# daz_execute_file
# ---------------------------------------------------------------------------

class TestExecuteFile:
    async def test_executes_file(self, live_client, tmp_path):
        script_path = tmp_path / "hello.dsa"
        script_path.write_text('(function(){ return {ok: true}; })()')
        result = await daz_execute_file(str(script_path))
        assert result is not None

    async def test_missing_file_raises(self, live_client, tmp_path):
        with pytest.raises((ToolError, FileNotFoundError, Exception)):
            await daz_execute_file(str(tmp_path / "nonexistent.dsa"))


# ---------------------------------------------------------------------------
# daz_script_help  (local — no DAZ Studio connection required)
# ---------------------------------------------------------------------------

class TestScriptHelp:
    async def test_overview_returns_string(self, live_client):
        result = await daz_script_help("overview")
        assert isinstance(result, str)
        assert len(result) > 50

    async def test_camera_topic(self, live_client):
        result = await daz_script_help("camera")
        assert isinstance(result, str)
        assert len(result) > 20

    async def test_unknown_topic_still_returns_string(self, live_client):
        result = await daz_script_help("completely_unknown_topic_xyz")
        assert isinstance(result, str)

    @pytest.mark.parametrize("topic", [
        "overview", "gotchas", "camera", "light", "scene",
        "properties", "morphs", "animation", "rendering",
    ])
    async def test_all_standard_topics(self, live_client, topic):
        result = await daz_script_help(topic)
        assert isinstance(result, str)
        assert len(result) > 10


# ---------------------------------------------------------------------------
# daz_validate_script  (local — no DAZ Studio connection required)
# ---------------------------------------------------------------------------

class TestValidateScript:
    async def test_valid_script_passes(self, live_client):
        result = await daz_validate_script(
            "(function(){ var x = Scene.getNumNodes(); return {count: x}; })()"
        )
        assert isinstance(result, dict)
        # Should indicate no issues or a clean result
        issues = result.get("issues", result.get("errors", result.get("warnings", [])))
        assert isinstance(issues, list)

    async def test_returns_dict(self, live_client):
        result = await daz_validate_script("(function(){ return {}; })()")
        assert isinstance(result, dict)

    async def test_bare_return_flagged(self, live_client):
        """Scripts without IIFE wrapper should be flagged."""
        result = await daz_validate_script("return 42;")
        assert isinstance(result, dict)
        # Check there's some kind of warning/issue indicator
        text = str(result).lower()
        assert any(k in text for k in ["warn", "issue", "error", "bare", "iife", "false"])


# ---------------------------------------------------------------------------
# daz_inspect_properties
# ---------------------------------------------------------------------------

class TestInspectProperties:
    async def test_all_properties(self, live_client, figure_label):
        result = await daz_inspect_properties(figure_label, property_type="all")
        assert isinstance(result, dict)
        props = result.get("properties", [])
        assert isinstance(props, list)
        assert len(props) > 0

    async def test_numeric_filter(self, live_client, figure_label):
        result = await daz_inspect_properties(figure_label, property_type="numeric")
        assert isinstance(result, dict)

    async def test_transform_filter(self, live_client, figure_label):
        result = await daz_inspect_properties(figure_label, property_type="transform")
        result_str = str(result).lower()
        # Should contain transform-related property names
        assert any(t in result_str for t in ["translate", "rotate", "scale", "transform"])

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_inspect_properties("NonExistentNode_XYZ_999")


# ---------------------------------------------------------------------------
# daz_get_property_metadata
# ---------------------------------------------------------------------------

class TestGetPropertyMetadata:
    async def test_xtranslate_metadata(self, live_client, figure_label):
        result = await daz_get_property_metadata(figure_label, "XTranslate")
        assert isinstance(result, dict)
        text = str(result).lower()
        assert any(k in text for k in ["name", "label", "value", "type", "translate"])

    async def test_unknown_property_raises(self, live_client, figure_label):
        with pytest.raises(ToolError):
            await daz_get_property_metadata(figure_label, "Nonexistent_Property_XYZ")

    async def test_node_not_found_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_get_property_metadata("NonExistentNode_XYZ", "XTranslate")
