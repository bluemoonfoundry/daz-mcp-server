"""Guard DS6 export/import contract in registered DazScript payloads."""
from daz_mcp_server._registry import _REGISTRY


def test_import_obj_forces_unit_scale_and_run_silent():
    script = _REGISTRY["vangard-import-obj"][1]
    assert "DzObjImporter" in script
    assert "readFile" in script
    assert 'setFloatValue("Scale", scaleFactor)' in script
    assert 'setIntValue("RunSilent", 1)' in script
    assert "getDefaultOptions" in script


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
