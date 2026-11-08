"""Isolation: the minimum distance between geometry elements.

``find_optim_mp`` feeds the "find optimal tool diameter" check, and it collects the solid
geometry of every aperture before measuring distances between the pieces. Aperture macros
can contribute a ``MultiPolygon`` as a single solid, which used to reach ``MultiPolygon()``
as a nested sequence and abort the check with
``"Sequences of multi-polygons are not valid arguments"``.
"""

import pytest
from shapely import MultiPolygon, Polygon, box

from flatcam_plus.appPlugins.ToolIsolation import ToolIsolation


def aperture_storage(*solids):
    entry = {"geometry": [{"solid": solid} for solid in solids]}
    return {10: entry}


def test_measures_the_distance_between_separate_elements():
    # Two 1 mm squares, 2 mm apart along X. Unchanged behaviour: flat polygons are measured
    # exactly as before, and the result is trimmed by one decimal step.
    msg, min_dist = ToolIsolation.find_optim_mp(
        aperture_storage(box(0, 0, 1, 1), box(3, 0, 4, 1)), 2
    )
    assert msg == "ok"
    assert min_dist == pytest.approx(1.99)


def test_accepts_a_multi_polygon_solid():
    # The first solid is a MultiPolygon holding two 1 mm squares; the third piece sits 5 mm
    # up. The nearest pair is still the two squares inside the MultiPolygon.
    nested = MultiPolygon([box(0, 0, 1, 1), box(3, 0, 4, 1)])
    msg, min_dist = ToolIsolation.find_optim_mp(aperture_storage(nested, box(0, 5, 1, 6)), 2)
    assert msg == "ok"
    assert min_dist == pytest.approx(1.99)


def test_flattens_the_multi_polygon_into_measurable_pieces():
    # A single MultiPolygon solid must be split before measuring, otherwise there is nothing
    # to compare and the report cannot be produced.
    nested = MultiPolygon([box(0, 0, 1, 1), box(0, 10, 1, 11)])
    msg, min_dist = ToolIsolation.find_optim_mp(aperture_storage(nested), 2)
    assert msg == "ok"
    assert min_dist == pytest.approx(8.99)


def test_reports_a_layer_that_merges_into_one_polygon():
    # Two touching 1 mm squares merge into a single polygon, so there is no pair to
    # measure. The check must return the "one Polygon as geometry" report and no
    # distance, instead of dying inside `min()` on an empty dict. The message is the
    # caller's contract: it is emitted as-is and the caller stops before using the
    # distance, so a missing distance must never come back with an 'ok' status.
    msg, min_dist = ToolIsolation.find_optim_mp(
        aperture_storage(box(0, 0, 1, 1), box(1, 0, 2, 1)), 2
    )
    assert msg.startswith("[ERROR_NOTCL]")
    assert "one Polygon as geometry" in msg
    assert "no distances between geometry elements" in msg
    assert min_dist is None


def test_reports_a_layer_with_no_geometry_to_measure():
    # A layer that contributes no usable solid (here none at all) has no pair to
    # measure either. It used to borrow the one-Polygon report, which describes a layer
    # that does have a solid; the empty layer says what it is.
    msg, min_dist = ToolIsolation.find_optim_mp(aperture_storage(), 2)
    assert msg.startswith("[ERROR_NOTCL]")
    assert "no usable geometry to measure distances between" in msg
    assert min_dist is None


def test_reports_a_layer_with_a_single_solid():
    # One piece cannot be compared with anything: that is the one-Polygon report, and its
    # text is unchanged.
    msg, min_dist = ToolIsolation.find_optim_mp(aperture_storage(box(0, 0, 1, 1)), 2)
    assert msg.startswith("[ERROR_NOTCL]")
    assert "one Polygon as geometry" in msg
    assert "no distances between geometry elements" in msg
    assert min_dist is None


def test_ignores_invalid_solids():
    tolerance = Polygon([(0, 0), (1, 1), (0, 1), (1, 0)])  # self-intersecting bowtie
    msg, min_dist = ToolIsolation.find_optim_mp(
        aperture_storage(box(0, 0, 1, 1), tolerance, box(3, 0, 4, 1)), 2
    )
    assert msg == "ok"
    assert min_dist == pytest.approx(1.99)
