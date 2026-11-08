"""NCC: the minimum distance between the polygons of a Gerber layer.

``find_optim_mp`` is the public seam behind the "find optimal tool diameter" check for
non-copper clearance. It collects the solid of every aperture, buffers it by 1e-7 and keeps
only the valid results, so a self-intersecting solid contributes nothing. A layer that
contributes fewer than two measurable polygons has no pair to compare: the check has to
report that and hand back an unusable distance instead of dying inside ``min()`` on an empty
dict.
"""

import math

import pytest
from shapely.geometry import box

# ``flatcam_plus/appPlugins/__init__.py`` overwrites the package attribute with the plugin
# class itself, so ``import flatcam_plus.appPlugins.ToolNCC as m`` binds the class, not the
# module.
from flatcam_plus.appPlugins.ToolNCC import NonCopperClear


def aperture_storage(*solids):
    entry = {"geometry": [{"solid": solid} for solid in solids]}
    return {10: entry}


def test_reports_a_layer_with_no_geometry_to_measure():
    # Nothing to contribute at all: no pair exists, so the report replaces the distance.
    msg, min_dist = NonCopperClear.find_optim_mp(aperture_storage(), 2)
    assert msg.startswith("[ERROR_NOTCL]")
    assert "Too few polygons" in msg
    assert "determine distances" in msg
    assert math.isinf(min_dist)


def test_reports_a_layer_with_a_single_polygon():
    # One piece cannot be compared with anything either, and reaches the same report.
    msg, min_dist = NonCopperClear.find_optim_mp(aperture_storage(box(0, 0, 1, 1)), 2)
    assert msg.startswith("[ERROR_NOTCL]")
    assert "Too few polygons" in msg
    assert math.isinf(min_dist)


def test_measures_the_distance_between_separate_elements():
    # Two 1 mm squares, 2 mm apart along X. The 1e-7 buffer of each solid narrows the gap by
    # 2e-7, which the rounding to two decimals absorbs, and the result is then trimmed by one
    # decimal step so that the reported diameter stays clear of the measured gap.
    msg, min_dist = NonCopperClear.find_optim_mp(
        aperture_storage(box(0, 0, 1, 1), box(3, 0, 4, 1)), 2
    )
    assert msg == "ok"
    assert min_dist == pytest.approx(1.99)
