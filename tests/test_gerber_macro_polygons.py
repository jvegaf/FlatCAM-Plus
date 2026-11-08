"""Gerber input: a macro that flashes a pad built from several polygons.

The ``THM_3SEG`` aperture macro below draws one thermal-relief pad out of two concentric
circles in opposing polarities plus three clear spokes. Parsing it accumulates nested
``MultiPolygon`` values in the union buffer, and the final geometry step used to abort on
that nesting with ``"Object is not Gerber file or empty"``.

Covers the reported failure from PR #19 and the guard it tripped, without a display.
"""

from collections import namedtuple

import pytest
from shapely.ops import unary_union

from flatcam_plus.appParsers.ParseGerber import Gerber

ParsedGerber = namedtuple("ParsedGerber", "gerber warning")


@pytest.fixture(scope="module")
def parsed_macro(fc_app, sample_input):
    gerber = Gerber(app=fc_app, steps_per_circle=64)
    warning = gerber.parse_lines(sample_input("thermal_pad_macro.gbr"))
    return ParsedGerber(gerber=gerber, warning=warning)


def test_parses_a_macro_that_emits_polygons(parsed_macro):
    # A nested MultiPolygon in the union buffer must not be mistaken for an empty file.
    assert parsed_macro.warning is None
    assert decoded_tools(parsed_macro.gerber) == [10]


def test_keeps_the_flashed_pad_extent(parsed_macro):
    pad = unary_union(parsed_macro.gerber.solid_geometry)
    # One 2.2 mm flash centred on (4, 4) mm, so the envelope is 2.9..5.1 mm on both axes.
    # The clear spokes trim arcs off that envelope, so assert containment in it and that the
    # pad still spans nearly all of it instead of a chord-exact extent.
    left, bottom, right, top = pad.bounds
    assert (left, bottom) > (2.9 - 1e-3, 2.9 - 1e-3)
    assert (right, top) < (5.1 + 1e-3, 5.1 + 1e-3)
    assert right - left > 2.0
    assert top - bottom > 2.0


def test_honours_the_clear_polarity_inside_the_macro(parsed_macro):
    pad = unary_union(parsed_macro.gerber.solid_geometry)
    # The full 2.2 mm disc would be 3.8 mm². The clear inner circle and the three 2/3 mm
    # clear spokes remove it, leaving a thin ring chopped into arcs.
    assert pad.area < 1.0
    assert not pad.is_empty


def decoded_tools(gerber):
    return sorted(gerber.tools)
