"""Guard color-channel reading in registered material DazScript."""
import gzip
import json
from pathlib import Path

from vangard_daz_mcp._registry import _REGISTRY
from vangard_daz_mcp.tools.material import extract_preset_map_paths


def test_set_property_and_morph_search_modifier_stack():
    for script_id in ("vangard-set-property", "vangard-set-morph", "vangard-get-node"):
        script = _REGISTRY[script_id][1]
        assert "getNumModifiers" in script, script_id
        assert "getValueChannel" in script, script_id


def test_get_material_reads_float_color_properties():
    script = _REGISTRY["vangard-get-material"][1]
    assert "getFloatColorValue" in script
    assert "DzFloatColorProperty" in script
    assert "col.red()" not in script
    assert "readColorProp" in script


def test_extract_preset_map_paths_gzip_and_plain(tmp_path: Path):
    payload = {
        "image_library": [
            {"url": "skin.jpg#0", "filename": "/Runtime/Textures/skin.jpg"},
        ],
        "note": "not a map",
    }
    plain = tmp_path / "plain.duf"
    plain.write_text(json.dumps(payload), encoding="utf-8")
    gz = tmp_path / "gz.duf"
    gz.write_bytes(gzip.compress(json.dumps(payload).encode("utf-8")))
    assert extract_preset_map_paths(str(plain)) == [
        "skin.jpg",
        "/Runtime/Textures/skin.jpg",
    ]
    assert extract_preset_map_paths(str(gz)) == [
        "skin.jpg",
        "/Runtime/Textures/skin.jpg",
    ]
