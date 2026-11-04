"""Gerber input: a board outline parsed into geometry.

Covers the PCB input domain without a display: the parser, the aperture table and the
resulting solid geometry.
"""

import pytest
from shapely.ops import unary_union

from appParsers.ParseGerber import Gerber

SQUARE_OUTLINE = """\
G04 1mm-wide 10x10mm square outline*
%FSLAX34Y34*%
%MOMM*%
%ADD10C,1.000*%
D10*
X0Y0D02*
X90000Y0D01*
X100000Y100000D01*
X0Y100000D01*
X0Y0D01*
M02*
"""


@pytest.fixture()
def parsed_square(fc_app):
    gerber = Gerber(app=fc_app, steps_per_circle=64)
    warning = gerber.parse_lines(SQUARE_OUTLINE.splitlines())
    return gerber, warning


def test_accepts_a_clean_file(parsed_square):
    _, warning = parsed_square
    assert warning is None


def test_reads_units_and_apertures(parsed_square):
    gerber, _ = parsed_square
    assert gerber.units == "MM"
    assert list(gerber.tools) == [10]


def test_builds_the_stroked_outline(parsed_square):
    gerber, _ = parsed_square
    bounds = unary_union(gerber.solid_geometry).bounds
    # A 1 mm round aperture stroked along the 10x10 mm path, grown by half the aperture on
    # every side. The chorded circle leaves a sub-micron error, hence the tolerance.
    assert bounds == pytest.approx((-0.5, -0.5, 10.5, 10.5), abs=1e-3)
