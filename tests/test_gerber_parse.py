"""Gerber input: a board outline parsed into geometry.

Covers the PCB input domain without a display: the parser, the aperture table and the
resulting solid geometry. The sample source lives in ``tests/data/square_outline.gbr``.
"""

from collections import namedtuple

import pytest
from shapely.ops import unary_union

from flatcam_plus.appParsers.ParseGerber import Gerber

ParsedGerber = namedtuple("ParsedGerber", "gerber warning")


@pytest.fixture(scope="module")
def parsed_square(fc_app, sample_input):
    gerber = Gerber(app=fc_app, steps_per_circle=64)
    warning = gerber.parse_lines(sample_input("square_outline.gbr"))
    return ParsedGerber(gerber=gerber, warning=warning)


def test_accepts_a_clean_file(parsed_square):
    assert parsed_square.warning is None


def test_reads_units_and_apertures(parsed_square):
    assert parsed_square.gerber.units == "MM"
    assert list(parsed_square.gerber.tools) == [10]


def test_builds_the_stroked_outline(parsed_square):
    outline = unary_union(parsed_square.gerber.solid_geometry)
    # A 1 mm round aperture stroked along the 10x10 mm path, grown by half the aperture on
    # every side. The chorded circle leaves a sub-micron error, hence the tolerance.
    assert outline.bounds == pytest.approx((-0.5, -0.5, 10.5, 10.5), abs=1e-3)
    # 11x11 mm outer square minus the 9x9 mm hole. The area catches a vertex that still
    # spans the same extent, which a bounds-only assertion cannot see.
    assert outline.area == pytest.approx(40.0, abs=0.5)
