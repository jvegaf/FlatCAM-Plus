"""NCC: the minimum distance between the polygons of a Gerber layer.

``find_optim_mp`` is the public seam behind the "find optimal tool diameter" check for
non-copper clearance. It collects the solid of every aperture, buffers it by 1e-7 and keeps
the results that are valid *after* buffering, so a self-intersecting solid is repaired rather
than dropped. The pieces are then flattened but never unioned, so touching pieces stay
separate. Both choices have a visible result: a gap of 0 mm is measured as 0 and reported
trimmed, and a layer whose only defect is a self-intersecting solid still gets a distance. A
layer that contributes fewer than two measurable polygons has no pair to compare: the check
has to report that and hand back an unusable distance instead of dying inside ``min()`` on an
empty dict.
"""

import math

import numpy as np
import pytest
from shapely import Polygon
from shapely.geometry import box

# ``flatcam_plus/appPlugins/__init__.py`` overwrites the package attribute with the plugin
# class itself, so ``import flatcam_plus.appPlugins.ToolNCC as m`` binds the class, not the
# module.
from flatcam_plus.appPlugins.ToolNCC import NonCopperClear
from flatcam_plus.camlib import grace


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


def test_measures_two_touching_squares_as_a_zero_gap():
    # Two 1 mm squares sharing an edge. Each solid is buffered by 1e-7 before the distance is
    # measured and the pieces are not unioned afterwards, so they stay two pieces 0 mm apart
    # instead of merging into the one-polygon report. The result is the 0 mm gap trimmed by
    # one decimal step: a diameter that cannot clear anything.
    msg, min_dist = NonCopperClear.find_optim_mp(
        aperture_storage(box(0, 0, 1, 1), box(1, 0, 2, 1)), 2
    )
    assert msg == "ok"
    assert min_dist == pytest.approx(-0.01)


def test_keeps_a_self_intersecting_solid_instead_of_dropping_it():
    # The validity check runs on the buffered solid, not on the raw one: the 1e-7 buffer
    # repairs the bowtie, so the layer keeps it. It overlaps the first square, so the measured
    # gap is 0 mm and the trimmed result is -0.01. Dropping the invalid solid instead would
    # leave the two squares and report the 2 mm gap between them.
    tolerance = Polygon([(0.5, 0), (1.5, 1), (0.5, 1), (1.5, 0)])  # self-intersecting bowtie
    msg, min_dist = NonCopperClear.find_optim_mp(
        aperture_storage(box(0, 0, 1, 1), tolerance, box(3, 0, 4, 1)), 2
    )
    assert msg == "ok"
    assert min_dist == pytest.approx(-0.01)


def test_measures_the_distance_between_separate_elements():
    # Two 1 mm squares, 2 mm apart along X. The 1e-7 buffer of each solid narrows the gap by
    # 2e-7, which the rounding to two decimals absorbs, and the result is then trimmed by one
    # decimal step so that the reported diameter stays clear of the measured gap.
    msg, min_dist = NonCopperClear.find_optim_mp(
        aperture_storage(box(0, 0, 1, 1), box(3, 0, 4, 1)), 2
    )
    assert msg == "ok"
    assert min_dist == pytest.approx(1.99)


def test_reports_progress_for_every_measured_pair():
    # The GUI worker drives its progress bar from `on_pair`, so this callback is the seam
    # the panel uses. Three pieces make three pairs, and the total arrives with each call.
    calls = []
    msg, min_dist = NonCopperClear.find_optim_mp(
        aperture_storage(box(0, 0, 1, 1), box(3, 0, 4, 1), box(6, 0, 7, 1)),
        2,
        on_pair=lambda processed, total: calls.append((processed, total)),
    )
    assert msg == "ok"
    assert min_dist == pytest.approx(1.99)
    assert [processed for processed, _ in calls] == [1, 2, 3]
    assert {total for _, total in calls} == {3}

    # The percentages the panel renders from these numbers start above 0 and reach 100.
    percentages = [int(np.interp(processed, [0, total], [0, 100])) for processed, total in calls]
    assert percentages == [33, 66, 100]


def test_aborts_before_measuring_the_pair_that_asks_for_it():
    # A user abort arrives between pairs; no distance is handed back afterwards.
    pairs = []
    result = None

    with pytest.raises(grace):
        result = NonCopperClear.find_optim_mp(
            aperture_storage(box(0, 0, 1, 1), box(3, 0, 4, 1), box(6, 0, 7, 1)),
            2,
            on_pair=lambda processed, total: pairs.append(processed),
            abort_check=lambda: len(pairs) == 1,
        )

    assert result is None
    assert pairs == [1]


def test_aborts_during_collection_before_measuring_anything():
    # The GUIs check the abort flag while the solids are still being collected, so an abort
    # requested up front must leave before the first distance is measured.
    pairs = []
    result = None

    with pytest.raises(grace):
        result = NonCopperClear.find_optim_mp(
            aperture_storage(box(0, 0, 1, 1), box(3, 0, 4, 1), box(6, 0, 7, 1)),
            2,
            on_pair=lambda processed, total: pairs.append(processed),
            abort_check=lambda: True,
        )

    assert result is None
    assert pairs == []
