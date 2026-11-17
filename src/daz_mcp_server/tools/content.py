"""Content browser tools: category listing, browsing, metadata, search, and product loading."""
from __future__ import annotations

import asyncio
import json as _json
import os
from pathlib import Path
from typing import Any

import httpx
from fastmcp.exceptions import ToolError

from .._mcp import mcp, _execute_by_id, _execute_by_id_async
from .._client import get_content_browser_client, CONTENT_BROWSER_URL
from .. import _ui_automation


# ---------------------------------------------------------------------------
# Tools — content library (DAZ Studio Script Server registered scripts)
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_list_categories(parent_path: str = "") -> dict[str, Any]:
    """List content library category subdirectories under a parent path.

    Searches across all configured DAZ content directories and deduplicates by name.

    Args:
        parent_path: Relative path within content directories to list (e.g. "People/Genesis 9").
                     Leave empty to list top-level categories.

    Returns:
        Dict with parent, categories (list of {name, path, duf_count}), and count.

    Example:
        daz_list_categories()                      # top-level: People, Props, Environments...
        daz_list_categories("People/Genesis 9")    # sub-folders: Characters, Clothing, Hair...
    """
    return await _execute_by_id("vangard-list-categories", {"parentPath": parent_path})


@mcp.tool()
async def daz_browse_category(
    category_path: str,
    sort_by: str = "name",  # pylint: disable=unused-argument
    # Only "name" is currently supported; see docstring below.
) -> dict[str, Any]:
    """List .duf content files in a content library category path.

    Searches all configured DAZ content directories and deduplicates by filename.

    Args:
        category_path: Relative path within content directories (e.g. "People/Genesis 9/Hair").
        sort_by: Sort order — only "name" is currently supported (alphabetical).

    Returns:
        Dict with category, items (list of {name, filename, full_path}), and count.

    Example:
        daz_browse_category("People/Genesis 9/Hair")
        daz_browse_category("Props/Furniture")
    """
    return await _execute_by_id("vangard-browse-category", {"categoryPath": category_path})


@mcp.tool()
async def daz_get_content_info(file_path: str) -> dict[str, Any]:
    """Read metadata from a .duf content file without loading it into the scene.

    Parses the JSON structure of a .duf file to extract name, type, contributor,
    and other available metadata fields.

    Args:
        file_path: Absolute path to a .duf file on disk.

    Returns:
        Dict with name, type, file_version, contributor, revision, modified, and
        any scene-level asset info found in the file.

    Raises:
        ToolError: If the file does not exist, is not readable, or is not valid JSON.
    """
    path = Path(file_path)
    if not path.exists():
        raise ToolError(f"File not found: {file_path}")
    if not path.suffix.lower() == ".duf":
        raise ToolError(f"Not a .duf file: {file_path}")

    try:
        with open(path, encoding="utf-8") as f:
            data = _json.load(f)
    except (OSError, _json.JSONDecodeError) as e:
        raise ToolError(f"Failed to read {file_path}: {e}") from e

    asset_info = data.get("asset_info", {})
    contributor = asset_info.get("contributor", {})

    result: dict[str, Any] = {
        "path": str(path),
        "name": path.stem,
        "file_version": data.get("file_version", "unknown"),
        "asset_id": asset_info.get("id", ""),
        "type": asset_info.get("type", "unknown"),
        "revision": asset_info.get("revision", ""),
        "modified": asset_info.get("modified", ""),
        "contributor": {
            "author": contributor.get("author", ""),
            "studio": contributor.get("studio", ""),
            "website": contributor.get("website", ""),
        },
    }

    # Try to extract a human-readable description from common locations
    if "scene" in data:
        scene = data["scene"]
        nodes = scene.get("nodes", [])
        if nodes:
            first = nodes[0]
            result["label"] = first.get("label", path.stem)
            if "description" in first:
                result["description"] = first["description"]

    return result


# ---------------------------------------------------------------------------
# Tools — content browser FastAPI server
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_search_content(query: str, max_results: int = 10) -> dict[str, Any]:
    """Search the DAZ product catalog using semantic vector search.

    Calls the daz-content-browser FastAPI server (POST /api/v1/search).
    Returns a list of matching products with sku, name, description,
    compatible_figures, tags, and store_url fields.

    Returns {"available": false, "reason": "..."} gracefully if the content
    browser is not running.

    Args:
        query: Natural-language search query, e.g. "sci-fi armor for Genesis 9".
        max_results: Maximum number of results to return (default 10).
    """
    client = get_content_browser_client()
    try:
        response = await client.post(
            "/api/v1/search",
            json={"query": query, "max_results": max_results},
        )
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException):
        return {
            "available": False,
            "reason": "Content browser not reachable at " + CONTENT_BROWSER_URL,
        }
    if response.status_code != 200:
        return {
            "available": False,
            "reason": f"Content browser returned HTTP {response.status_code}",
        }
    return response.json()


@mcp.tool()
async def daz_load_product(product_name: str) -> dict[str, Any]:
    """Find a DAZ product by name and load it into the current scene.

    Queries the daz-content-browser product index (GET /api/v1/products?q=<name>)
    to resolve the absolute .duf path, then calls POST /api/v1/scene/load which
    delegates to the DazScriptServer to merge the asset into the scene.

    Returns {"available": false, "reason": "..."} gracefully if the content
    browser is not running or no matching product is found.

    Args:
        product_name: Partial or full product name to search for.
    """
    client = get_content_browser_client()
    try:
        search_response = await client.get("/api/v1/products", params={"q": product_name})
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException):
        return {
            "available": False,
            "reason": "Content browser not reachable at " + CONTENT_BROWSER_URL,
        }
    if search_response.status_code != 200:
        return {
            "available": False,
            "reason": f"Content browser returned HTTP {search_response.status_code}",
        }

    products = search_response.json()
    if isinstance(products, dict):
        products = products.get("products", products.get("results", []))
    if not products:
        return {
            "available": True,
            "found": False,
            "reason": f"No product found matching '{product_name}'",
        }

    product = products[0]
    duf_path = product.get("path") or product.get("file_path") or product.get("duf_path")
    if not duf_path:
        return {
            "available": True,
            "found": True,
            "error": "Product record has no file path",
            "product": product,
        }

    try:
        load_response = await client.post("/api/v1/scene/load", json={"path": duf_path})
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException):
        return {"available": False, "reason": "Content browser not reachable during load"}
    if load_response.status_code != 200:
        return {
            "available": False,
            "reason": f"Scene load returned HTTP {load_response.status_code}",
        }

    result = load_response.json()
    result["product"] = product
    return result


# ---------------------------------------------------------------------------
# Tools — asset compatibility
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_check_compatibility(asset_path: str, figure_label: str) -> dict[str, Any]:
    """Check if an asset is compatible with the specified figure generation.

    Reads the asset's .duf file to inspect compatible_figures metadata.
    """
    try:
        if not os.path.exists(asset_path):
            return {"compatible": False, "reason": "Asset file not found"}
        with open(asset_path, encoding="utf-8") as f:
            data = _json.load(f)
        asset_info = data.get("asset_info", {})
        compatible = asset_info.get("compatible_figures", [])
        return {
            "asset_path": asset_path,
            "figure_label": figure_label,
            "compatible_figures": compatible,
            "likely_compatible": any(
                figure_label.lower() in str(c).lower() or str(c).lower() in figure_label.lower()
                for c in compatible
            ) if compatible else None,
        }
    except Exception as e:
        return {"compatible": None, "error": str(e)}


# ---------------------------------------------------------------------------
# Tools — Content-Library asset creation
# ---------------------------------------------------------------------------


@mcp.tool()
async def daz_save_prop_asset(
    node_label: str,
    output_path: str,
    vendor_name: str = "Author",
    product_name: str = "Product",
    item_name: str | None = None,
    category: str | None = None,
    compatibility_base: str | None = None,
    compatible_with: str | None = None,
    smart_parent: bool | None = None,
    write_geometry: bool | None = None,
    write_parameters: bool | None = None,
    write_uvs: bool | None = None,
    force_unique_ids: bool | None = None,
    compress_output: bool | None = None,
) -> dict[str, Any]:
    """Save a node as a reusable Content-Library Prop/Figure Support Asset (.duf).

    Headless equivalent of **File > Save As > Support Asset > Prop Asset** (or
    "Figure Asset" for a rigged node), via ``DzNodeSupportAssetFilter``. Writes
    two things: the ``.duf`` preset at ``output_path``, and the actual geometry/
    UV/rigging data under ``<content dir>/data/<vendor>/<product>/<item>/...``.
    Once saved, the asset shows up like any other library prop and can be
    reloaded with ``daz_load_file`` or dragged from Smart Content/Content Library.

    Args:
        node_label: Display label, internal name, elementID, or ``Parent/Label``
            of the node to save.
        output_path: Absolute path for the ``.duf`` file. **Must be inside one of
            the DAZ Studio instance's configured content directories** (e.g.
            under "My Library" or a shared content root) — the tool resolves
            which content directory it belongs to and errors with the list of
            configured directories if it isn't inside any of them.
        vendor_name: Vendor/author name embedded in the asset metadata (default
            "Author").
        product_name: Product name embedded in the asset metadata (default
            "Product").
        item_name: Item name embedded in the asset metadata. Defaults to
            ``node_label`` if omitted.
        category: Content-Library category path to tag the asset with (e.g.
            "Props/Furniture").
        compatibility_base: Figure/base this asset declares compatibility with
            (e.g. "Genesis 9").
        compatible_with: Additional compatible-figure declaration string.
        smart_parent: Enable Smart Parent behavior when the asset is applied.
        write_geometry: Include geometry data (default plugin behavior if
            omitted — normally on).
        write_parameters: Include parameter/morph definitions (default plugin
            behavior if omitted — normally on).
        write_uvs: Include UV set definitions (default plugin behavior if
            omitted — normally on).
        force_unique_ids: Force regeneration of unique asset IDs instead of
            reusing existing ones.
        compress_output: Compress the written ``.duf``/``.dsf`` files (default
            plugin behavior if omitted — normally on).

    Returns:
        Dict with success, node, outputPath, baseDataPath (the resolved content
        directory), vendorName, productName, itemName.

    Examples:
        daz_save_prop_asset(
            "Long Wavy Hair",
            "C:/Users/me/Documents/DAZ 3D/Studio/My Library/Props/MyHair/My Hair.duf",
            vendor_name="MyStudio", product_name="Custom Hair", item_name="Long Wavy Hair",
        )

    Notes:
        - Live-verified: writes correct ``.duf`` + ``data/.../*.dsf`` files,
          fully silent (no dialog), confirmed round-trip-loadable via
          ``daz_load_file``.
        - Does **not** generate a thumbnail image — Daz's Content Library pane
          generates one lazily the first time it browses the folder, or you can
          render/place one yourself as ``<output_path>.png`` next to the .duf.
        - For a "Wearable Preset" (auto-fit-to-figure behavior when dragged
          from Smart Content, like a clothing/hair outfit), the underlying
          ``DzWearablesAssetFilter`` was investigated but not solved — its
          ``doSave()`` reproducibly failed with a generic error code across
          several configurations (asset-backed vs. ad-hoc geometry, with/
          without a parent node, various ``NodeNames``/``MaterialNames``
          settings). Use this Prop Asset tool instead; it covers the
          "Support Asset" half of the original request.
    """
    payload: dict[str, Any] = {
        "nodeLabel": node_label,
        "outputPath": output_path,
        "vendorName": vendor_name,
        "productName": product_name,
    }
    if item_name is not None:
        payload["itemName"] = item_name
    if category is not None:
        payload["category"] = category
    if compatibility_base is not None:
        payload["compatibilityBase"] = compatibility_base
    if compatible_with is not None:
        payload["compatibleWith"] = compatible_with
    if smart_parent is not None:
        payload["smartParent"] = smart_parent
    if write_geometry is not None:
        payload["writeGeometry"] = write_geometry
    if write_parameters is not None:
        payload["writeParameters"] = write_parameters
    if write_uvs is not None:
        payload["writeUvs"] = write_uvs
    if force_unique_ids is not None:
        payload["forceUniqueIds"] = force_unique_ids
    if compress_output is not None:
        payload["compressOutput"] = compress_output

    return await _execute_by_id("vangard-save-prop-asset", payload)


@mcp.tool()
async def daz_save_wearable_preset(
    figure_label: str,
    output_path: str,
    dialog_timeout: float = 30.0,
) -> dict[str, Any]:
    """Save a figure (with everything currently fitted to it) as a reusable
    Wearable(s) Preset — the fit-to-figure asset type, as opposed to
    ``daz_save_prop_asset``'s plain geometry-only Support Asset.

    Headless-*ish* equivalent of **File > Save As > Wearable(s) Preset**.
    "Headless-ish" because the underlying ``DzWearablesAssetFilter`` script
    API (``doSave()``) was found to reproducibly fail with an unexplained
    generic error code under every configuration tried (see
    ``docs/daz-mcp-bridge-bugs.md`` Bug 22 Teil 2 for the full investigation)
    — but the real GUI action works, so this tool drives *that* action's two
    native dialogs directly via Windows UI Automation (``pywinauto``)
    instead. No DAZ Studio window needs to be focused or in the foreground
    for this — everything is done via the accessibility tree and posted
    window messages.

    **Windows-only, and only works when this MCP server process runs on the
    same machine as DAZ Studio** — there is no remote-UI-automation path.

    Args:
        figure_label: Display label of the figure to save (e.g.
            ``"Genesis 8 Female"``). Must already have at least one item
            fit or parented to it — DAZ Studio itself refuses to save a
            Wearable(s) Preset otherwise ("A figure in the scene with other
            objects fit or parented to it must be selected...").
        output_path: Absolute path for the ``.duf`` file. Its parent
            directory is created automatically if missing (the native save
            dialog does **not** create missing subfolders on its own and
            errors instead).
        dialog_timeout: Seconds to wait for each native dialog to appear/
            close before giving up (default 30s). Increase if DAZ Studio is
            slow to respond (e.g. a very heavy scene).

    Returns:
        Dict with success and outputPath.

    Examples:
        daz_save_wearable_preset(
            "Genesis 8 Female",
            "C:/Users/me/Documents/DAZ 3D/Studio/My Library/Presets/Wearables/My Hair.duf",
        )

    Notes:
        - Bundles **every** item currently fit/parented to the figure, not
          just one you care about — the dialog's own node-selection
          checklist has no confirmed programmatic toggle mechanism (its
          items are custom-painted, not standard checkable controls; see
          Bug 22 Teil 2). If the figure is wearing other things you don't
          want included, unfit them first (``daz_unfit_item``), save, then
          re-fit them.
        - Produces a real thumbnail (``<output>.duf.png``/``.tip.png``)
          automatically — unlike ``daz_save_prop_asset``, which does not.
        - Live-verified end to end (2026-09-09) against a real figure with
          a fitted test prop, then fully reverted — no lasting scene changes.
    """
    _ui_automation._require_pywinauto()  # pylint: disable=protected-access
    await _execute_by_id_async("vangard-trigger-wearable-save", {"figureLabel": figure_label})
    return await asyncio.to_thread(
        _ui_automation.drive_wearable_preset_save, output_path, dialog_timeout
    )
