"""Guard fitted-item detection against counting the figure's own skeleton (bd f34)."""
import re

import pytest

from vangard_daz_mcp._registry import _REGISTRY


@pytest.mark.parametrize(
    "script_id", ["vangard-list-fitted-items", "vangard-get-figure-info"]
)
def test_fitted_item_scan_skips_bones_before_parent_check(script_id):
    script = _REGISTRY[script_id][1]
    skip = re.search(r'inherits\("DzBone"\)\)\s*continue;', script)
    assert skip, f"{script_id} must skip DzBone nodes"
    # The bone skip must come before the getNodeParent fallback, otherwise the
    # Hip root bone (parented to the figure) is counted as a fitted prop.
    scan_start = script.index("getFollowTarget")
    parent_check = script.index("getNodeParent", scan_start)
    assert skip.start() < parent_check, script_id
    # Real props parented to the figure must still count.
    assert "getNodeParent" in script
