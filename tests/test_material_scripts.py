"""Material preset texture-map extraction (used to preflight preset application)."""
import gzip
import json
from pathlib import Path

from daz_mcp_server.tools.material import extract_preset_map_paths


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
