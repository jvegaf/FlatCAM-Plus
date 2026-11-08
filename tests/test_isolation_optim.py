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


def test_reports_a_single_polygon_as_geometry_without_distances():
    # A plain Polygon is not a multi-element layer; the check reports it instead of
    # measuring. The message is the pre-existing one, kept verbatim.
    with pytest.raises(ValueError):
        ToolIsolation.find_optim_mp(aperture_storage(box(0, 0, 1, 1)), 2)


def test_ignores_invalid_solids():
    tolerance = Polygon([(0, 0), (1, 1), (0, 1), (1, 0)])  # self-intersecting bowtie
    msg, min_dist = ToolIsolation.find_optim_mp(
        aperture_storage(box(0, 0, 1, 1), tolerance, box(3, 0, 4, 1)), 2
    )
    assert msg == "ok"
    assert min_dist == pytest.approx(1.99)
