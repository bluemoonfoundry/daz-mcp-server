"""Guard the DS6 render-option contract in registered DazScript payloads."""
from vangard_daz_mcp._registry import _REGISTRY

_RENDER_IDS = (
    "vangard-render",
    "vangard-render-with-camera",
    "vangard-batch-render-cameras",
    "vangard-render-animation",
    "vangard-set-render-output",
)


def test_render_scripts_use_direct_to_file_not_zero():
    for script_id in _RENDER_IDS:
        script = _REGISTRY[script_id][1]
        assert "renderImgToId = 0" not in script, script_id
        assert "opts.DirectToFile" in script, script_id
        assert "opts.applyChanges()" in script, script_id
        if script_id != "vangard-set-render-output":
            assert "doRender(opts)" in script, script_id


def test_render_script_requires_output_path_before_dorender():
    script = _REGISTRY["vangard-render"][1]
    assert "Render output path is not set" in script
    assert script.index("if (!path)") < script.index("doRender(opts)")


def test_render_and_render_with_camera_both_sync_option_helper_path():
    for script_id in ("vangard-render", "vangard-render-with-camera"):
        script = _REGISTRY[script_id][1]
        assert "getOptionHelper" in script, script_id
        assert 'findProperty("Image Name")' in script, script_id
        assert 'findProperty("Image Path")' in script, script_id


def test_set_render_output_uses_image_size():
    script = _REGISTRY["vangard-set-render-output"][1]
    assert "opts.imageSize" in script
    assert "new QSize" in script
    assert "opts.aspectWidth" not in script


def test_get_render_settings_reports_image_size():
    script = _REGISTRY["vangard-get-render-settings"][1]
    assert "opts.imageSize" in script
    assert "opts.DirectToFile" in script
    assert "opts.renderType" in script


def test_get_render_settings_reports_engine_via_render_type():
    script = _REGISTRY["vangard-get-render-settings"][1]
    assert "opts.renderType" in script
    assert "opts.ScreenShot" in script
    assert "opts.HardwareAssisted" in script
    assert "opts.Software" in script
    assert "getActiveRenderer" in script


def test_set_render_engine_uses_render_type_not_renderer_count():
    script = _REGISTRY["vangard-set-render-engine"][1]
    assert "opts.renderType = opts.ScreenShot" in script
    assert "opts.renderType = opts.HardwareAssisted" in script
    assert "opts.renderType = opts.Software" in script
    assert "opts.applyChanges()" in script
    assert "getNumRenderers" not in script
