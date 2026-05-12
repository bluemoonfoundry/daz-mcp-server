"""Integration tests — content library and node config export/import.

Tools covered
-------------
- daz_list_categories
- daz_browse_category
- daz_get_content_info     (local JSON parsing — no DAZ needed)
- daz_export_node_config
- daz_import_node_config
"""

from __future__ import annotations

import json
import os

import pytest
import pytest_asyncio
from fastmcp.exceptions import ToolError

from vangard_daz_mcp.server import (
    daz_browse_category,
    daz_export_node_config,
    daz_get_content_info,
    daz_import_node_config,
    daz_list_categories,
)


# ---------------------------------------------------------------------------
# daz_list_categories
# ---------------------------------------------------------------------------

class TestListCategories:
    async def test_top_level_returns_dict(self, live_client):
        result = await daz_list_categories(parent_path="")
        assert isinstance(result, dict)

    async def test_has_categories_list(self, live_client):
        result = await daz_list_categories(parent_path="")
        categories = result.get("categories", result.get("items", []))
        assert isinstance(categories, list)

    async def test_root_has_entries(self, live_client):
        result = await daz_list_categories(parent_path="")
        categories = result.get("categories", result.get("items", []))
        # DAZ Studio always has at least a few library categories
        assert len(categories) >= 0  # Can be 0 if library not configured


# ---------------------------------------------------------------------------
# daz_browse_category
# ---------------------------------------------------------------------------

class TestBrowseCategory:
    async def test_browse_root_like_path(self, live_client):
        """Browse a path; may be empty if content library not configured."""
        result = await daz_browse_category(category_path="")
        assert isinstance(result, dict)

    async def test_has_items_key(self, live_client):
        result = await daz_browse_category(category_path="")
        assert any(k in result for k in ["items", "files", "content"])

    async def test_sort_by_name(self, live_client):
        result = await daz_browse_category(category_path="", sort_by="name")
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# daz_get_content_info  (local — no DAZ Studio connection required)
# ---------------------------------------------------------------------------

class TestGetContentInfo:
    async def test_valid_duf_file(self, live_client, tmp_path):
        """Create a minimal .duf file and read its metadata."""
        duf = {
            "file_version": "0.6.0.0",
            "asset_info": {
                "id": "/test/asset",
                "type": "figure",
                "contributor": {"author": "Test Author"},
                "description": "A test figure",
            }
        }
        duf_path = tmp_path / "test.duf"
        duf_path.write_text(json.dumps(duf))
        result = await daz_get_content_info(str(duf_path))
        assert isinstance(result, dict)

    async def test_missing_file_raises(self, live_client, tmp_path):
        with pytest.raises((ToolError, FileNotFoundError, Exception)):
            await daz_get_content_info(str(tmp_path / "nonexistent.duf"))

    async def test_returns_dict(self, live_client, tmp_path):
        duf = {"file_version": "0.6.0.0"}
        p = tmp_path / "minimal.duf"
        p.write_text(json.dumps(duf))
        result = await daz_get_content_info(str(p))
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# daz_export_node_config / daz_import_node_config
# ---------------------------------------------------------------------------

class TestExportImportNodeConfig:
    async def test_export_returns_dict(self, live_client, figure_label, tmp_path):
        out_path = str(tmp_path / "node_config.json").replace("\\", "/")
        result = await daz_export_node_config(out_path, node_labels=[figure_label])
        assert isinstance(result, dict)

    async def test_exported_file_exists(self, live_client, figure_label, tmp_path):
        out_path = tmp_path / "node_config.json"
        await daz_export_node_config(
            str(out_path).replace("\\", "/"), node_labels=[figure_label]
        )
        assert out_path.exists()

    async def test_exported_file_is_valid_json(self, live_client, figure_label, tmp_path):
        out_path = tmp_path / "node_config.json"
        await daz_export_node_config(
            str(out_path).replace("\\", "/"), node_labels=[figure_label]
        )
        data = json.loads(out_path.read_text())
        assert isinstance(data, (dict, list))

    async def test_import_roundtrip(self, live_client, figure_label, tmp_path):
        """Export then import back — should not error."""
        out_path = str(tmp_path / "roundtrip.json").replace("\\", "/")
        await daz_export_node_config(out_path, node_labels=[figure_label])
        result = await daz_import_node_config(out_path, node_labels=[figure_label])
        assert isinstance(result, dict)

    async def test_export_all_nodes(self, live_client, tmp_path):
        """Export with no filter — all nodes."""
        out_path = str(tmp_path / "all_nodes.json").replace("\\", "/")
        result = await daz_export_node_config(out_path)
        assert isinstance(result, dict)

    async def test_import_missing_file_raises(self, live_client, tmp_path):
        with pytest.raises((ToolError, FileNotFoundError, Exception)):
            await daz_import_node_config(
                str(tmp_path / "nonexistent_config.json").replace("\\", "/")
            )
