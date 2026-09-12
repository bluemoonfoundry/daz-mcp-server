"""Mock tests for Phase 6.12 tool: daz_save_wearable_preset.

Only the tool's own orchestration is under test here: firing the async
DazScript trigger, requiring pywinauto, and delegating the dialog-driving
work to ``_ui_automation.drive_wearable_preset_save``. The Windows UI
Automation internals of that function are exercised live only (see
SKILL_DAZSCRIPT.md) — they have no meaningful mock-test surface, same as
the fork commit that introduced them shipped none.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
import respx
import httpx

from fastmcp.exceptions import ToolError

from vangard_daz_mcp._client import set_http_client
from vangard_daz_mcp.tools import content

BASE_URL = "http://localhost:18811"


@pytest_asyncio.fixture(autouse=True)
async def http_client():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        set_http_client(client)
        yield client
    set_http_client(None)


@pytest.fixture
def mock_daz():
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


class TestSaveWearablePreset:
    async def test_successful_save(self, mock_daz, monkeypatch):
        mock_daz.post("/scripts/vangard-trigger-wearable-save/async").mock(
            return_value=httpx.Response(200, json={"request_id": "req-1"})
        )
        monkeypatch.setattr(content._ui_automation, "_require_pywinauto", lambda: None)
        driven: dict = {}

        def fake_drive(output_path, dialog_timeout):
            driven["output_path"] = output_path
            driven["dialog_timeout"] = dialog_timeout
            return {"success": True, "outputPath": output_path}

        monkeypatch.setattr(
            content._ui_automation, "drive_wearable_preset_save", fake_drive
        )

        result = await content.daz_save_wearable_preset(
            "Genesis 8 Female", "C:/Library/Presets/Wearables/My Hair.duf"
        )

        assert result == {
            "success": True,
            "outputPath": "C:/Library/Presets/Wearables/My Hair.duf",
        }
        assert driven["output_path"] == "C:/Library/Presets/Wearables/My Hair.duf"
        assert driven["dialog_timeout"] == 30.0
        trigger_call = mock_daz.calls[0]
        assert trigger_call.request.content
        import json as _json

        assert _json.loads(trigger_call.request.content) == {
            "args": {"figureLabel": "Genesis 8 Female"}
        }

    async def test_custom_dialog_timeout_forwarded(self, mock_daz, monkeypatch):
        mock_daz.post("/scripts/vangard-trigger-wearable-save/async").mock(
            return_value=httpx.Response(200, json={"request_id": "req-2"})
        )
        monkeypatch.setattr(content._ui_automation, "_require_pywinauto", lambda: None)
        driven: dict = {}

        def fake_drive(output_path, dialog_timeout):
            driven["dialog_timeout"] = dialog_timeout
            return {"success": True, "outputPath": output_path}

        monkeypatch.setattr(
            content._ui_automation, "drive_wearable_preset_save", fake_drive
        )

        await content.daz_save_wearable_preset(
            "Genesis 8 Female", "C:/out.duf", dialog_timeout=60.0
        )

        assert driven["dialog_timeout"] == 60.0

    async def test_requires_pywinauto(self, mock_daz, monkeypatch):
        def raise_missing():
            raise ToolError("pywinauto/pywin32 required")

        monkeypatch.setattr(content._ui_automation, "_require_pywinauto", raise_missing)

        with pytest.raises(ToolError, match="pywinauto"):
            await content.daz_save_wearable_preset("Genesis 8 Female", "C:/out.duf")

        assert not mock_daz.calls

    async def test_trigger_failure_propagates(self, mock_daz, monkeypatch):
        mock_daz.post("/scripts/vangard-trigger-wearable-save/async").mock(
            return_value=httpx.Response(503)
        )
        monkeypatch.setattr(content._ui_automation, "_require_pywinauto", lambda: None)

        with pytest.raises(httpx.HTTPStatusError):
            await content.daz_save_wearable_preset("Genesis 8 Female", "C:/out.duf")
