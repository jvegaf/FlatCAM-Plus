"""Excellon input: a drilling file parsed into a tool table and drill hits.

Covers the manufacturing input domain without a display: header parsing, tool diameters and
the coordinates of every hit. The sample source lives in ``tests/data/two_drills.drl``.
"""

import pytest

from flatcam_plus.appParsers.ParseExcellon import Excellon


@pytest.fixture(scope="module")
def parsed_drills(fc_app, sample_input):
    excellon = Excellon(app=fc_app)
    # ``Excellon.parse_lines`` reports problems through ``app.inform`` and the log; its return
    # value is always ``None``, so there is no warning channel to assert here.
    excellon.parse_lines(sample_input("two_drills.drl"))
    return excellon


def test_reads_the_units(parsed_drills):
    assert parsed_drills.units == "MM"


def test_reads_the_tool_diameter(parsed_drills):
    assert list(parsed_drills.tools) == [1]
    assert parsed_drills.tools[1]["tooldia"] == pytest.approx(0.8)


def test_reads_every_drill_hit(parsed_drills):
    hits = [tuple(drill.coords[0]) for drill in parsed_drills.tools[1]["drills"]]
    assert hits == [(10.0, 10.0), (20.0, 20.0)]
