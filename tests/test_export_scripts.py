"""Guard DS6 export/import contract in registered DazScript payloads."""
from daz_mcp_server._registry import _REGISTRY


def test_export_scene_uses_write_file_not_do_export():
    script = _REGISTRY["vangard-export-scene"][1]
    assert "doExport" not in script
    assert "findExporter" in script
    assert "writeFile" in script
    assert 'setIntValue("RunSilent", 1)' in script
    assert "getDefaultOptions" in script


def test_import_obj_forces_unit_scale_and_run_silent():
    script = _REGISTRY["vangard-import-obj"][1]
    assert "DzObjImporter" in script
    assert "readFile" in script
    assert 'setFloatValue("Scale", scaleFactor)' in script
    assert 'setIntValue("RunSilent", 1)' in script
    assert "getDefaultOptions" in script


def test_set_dforce_property_searches_object_modifier_stack():
    script = _REGISTRY["vangard-set-dforce-property"][1]
    assert "getNumModifiers" in script
    assert "searchMods(obj)" in script
    assert "Freeze Simulation" in script


_RESOLVE_IDS = (
    "vangard-get-node-hierarchy",
)


def test_core_node_scripts_resolve_uniquely():
    for script_id in _RESOLVE_IDS:
        script = _REGISTRY[script_id][1]
        assert "function resolveNode" in script, script_id
        assert "findNodeByElementID" in script, script_id
        assert "Ambiguous node" in script, script_id
        assert "Scene.findNodeByLabel(args.nodeLabel)" not in script, script_id


def test_apply_material_preset_preflights_missing_maps():
    script = _REGISTRY["vangard-apply-material-preset"][1]
    assert "Missing texture files" in script
    assert script.index("mapPaths") < script.index("openFile(presetPath")
    assert "allowMissing" in script


def test_every_registered_script_is_called_by_a_tool():
    """A registered script no tool calls is dead weight re-registered on every
    connection (daz-mcp-server-b7q)."""
    import pathlib

    src = pathlib.Path(__file__).resolve().parent.parent / "src" / "daz_mcp_server"
    callers = "".join(
        p.read_text(encoding="utf-8") for p in src.rglob("*.py") if p.name != "_registry.py"
    )
    unused = sorted(sid for sid in _REGISTRY if f'"{sid}"' not in callers)
    assert not unused, f"registered but never called: {unused}"
