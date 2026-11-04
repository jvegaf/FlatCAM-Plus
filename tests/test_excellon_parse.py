"""Excellon input: a drilling file parsed into a tool table and drill hits.

Covers the manufacturing input domain without a display: header parsing, tool diameters and
the coordinates of every hit.
"""

import pytest

from appParsers.ParseExcellon import Excellon

TWO_DRILLS = """\
M48
METRIC,TZ
T1C0.800
%
T1
X10.0Y10.0
X20.0Y20.0
M30
"""


@pytest.fixture()
def parsed_drills(fc_app):
    excellon = Excellon(app=fc_app)
    warning = excellon.parse_lines(TWO_DRILLS.splitlines())
    return excellon, warning


def test_reads_the_units(parsed_drills):
    excellon, _ = parsed_drills
    assert excellon.units == "MM"


def test_reads_the_tool_diameter(parsed_drills):
    excellon, _ = parsed_drills
    assert list(excellon.tools) == [1]
    assert excellon.tools[1]["tooldia"] == pytest.approx(0.8)


def test_reads_every_drill_hit(parsed_drills):
    excellon, _ = parsed_drills
    hits = [tuple(drill.coords[0]) for drill in excellon.tools[1]["drills"]]
    assert hits == [(10.0, 10.0), (20.0, 20.0)]
