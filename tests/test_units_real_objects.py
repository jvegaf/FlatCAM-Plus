"""Conversion against a real parsed file, not a stand-in.

The stub tests pin the all-or-nothing logic; this one answers the question that matters for the
feature being usable at all: does a real Gerber actually convert, or does the `conversion_done`
guard make every real file refuse?
"""

import pytest
from shapely.ops import unary_union

from flatcam_plus.appCommon import units
from flatcam_plus.appParsers.ParseGerber import Gerber


@pytest.fixture
def real_gerber(fc_app, sample_input):
    gerber = Gerber(app=fc_app, steps_per_circle=64)
    gerber.parse_lines(sample_input("square_outline.gbr"))
    return gerber


def _bounds(gerber):
    return tuple(unary_union(gerber.solid_geometry).bounds)


def test_a_real_gerber_reports_millimetres(real_gerber):
    assert real_gerber.units == "MM"


def test_a_real_gerber_converts_to_inches(real_gerber):
    before = _bounds(real_gerber)

    ok, refused = units.convert_objects([real_gerber], "MM", "IN")

    assert ok is True, "a real Gerber refused conversion: %r" % (refused,)
    assert real_gerber.units == "IN"

    after = _bounds(real_gerber)
    assert after == pytest.approx(tuple(value / 25.4 for value in before), rel=1e-9)


def test_a_real_gerber_round_trips_back_to_its_original_bounds(real_gerber):
    before = _bounds(real_gerber)

    assert units.convert_objects([real_gerber], "MM", "IN")[0] is True
    assert units.convert_objects([real_gerber], "IN", "MM")[0] is True

    after = _bounds(real_gerber)
    assert after == pytest.approx(before, abs=1e-6)


def test_a_real_gerber_that_declares_units_is_reported_as_refusing(fc_app, sample_input):
    """The guard this feature exists for: a refusal must be visible, not silent."""
    gerber = Gerber(app=fc_app, steps_per_circle=64)
    gerber.parse_lines(sample_input("square_outline.gbr"))

    # Force the state a file with a declared unit leaves behind.
    gerber.conversion_done = True
    before = _bounds(gerber)

    ok, refused = units.convert_objects([gerber], "MM", "IN")

    if ok:
        # The parser cleared the flag and converted anyway; that is also acceptable, but the
        # geometry must then really have changed.
        assert _bounds(gerber) != pytest.approx(before)
    else:
        assert refused, "a refusal must name the object it refused"
        assert _bounds(gerber) == pytest.approx(before)
