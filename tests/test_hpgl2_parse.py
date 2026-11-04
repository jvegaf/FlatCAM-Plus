"""HPGL2 input: a pen-plotter program parsed into real geometry.

``ParseHPGL2.parse_file`` both reads the file and fills ``tools``/``solid_geometry``; the whole
class used to fail in ``__init__`` because its ``default_data`` dictionary read thirteen
``geometry_*`` options the shipped defaults never defined. The sample below therefore has to
reach the end of the parse and produce geometry, not merely construct the parser.

HPGL2 is written one command per line here because the parser matches a single statement per
line. ``PA``/``PD`` are the plotter's move and pen commands and the coordinates are plotter
units of 1/40 mm, so ``PA1000,1000`` is (25.0, 25.0) mm.
"""

import pytest
import shapely

from flatcam_plus.appParsers.ParseHPGL2 import HPGL2

# The options the parser copies into ``default_data``; each ``default_data`` key is the option
# name without its ``geometry_`` prefix.
GEOMETRY_OPTIONS = (
    "geometry_cutz",
    "geometry_travelz",
    "geometry_dwell",
    "geometry_multidepth",
    "geometry_ppname_g",
    "geometry_extracut",
    "geometry_extracut_length",
    "geometry_toolchange",
    "geometry_area_exclusion",
    "geometry_area_shape",
    "geometry_area_strategy",
    "geometry_area_overz",
    "geometry_spindlespeed",
)

HPGL2_SAMPLE = """IN;
SP1;
PU;
PA0,0;
PD;
PA1000,0;
PA1000,1000;
PU;
PA0,0;
"""


@pytest.fixture(scope="module")
def parsed_plot(fc_app, tmp_path_factory):
    """Parse the sample file written into a temporary directory."""
    path = tmp_path_factory.mktemp("hpgl2") / "sample.plt"
    path.write_text(HPGL2_SAMPLE, encoding="utf-8")

    parser = HPGL2(app=fc_app)
    parser.parse_file(str(path))
    return parser


def test_the_parser_is_constructible(fc_app):
    assert HPGL2(app=fc_app) is not None


def test_parsing_produces_geometry(parsed_plot):
    geometry = parsed_plot.solid_geometry

    assert isinstance(geometry, shapely.geometry.base.BaseGeometry)
    assert not geometry.is_empty
    assert geometry.geom_type in {"LineString", "MultiLineString", "GeometryCollection"}


def test_the_pen_path_is_in_millimetres(parsed_plot):
    minx, miny, maxx, maxy = parsed_plot.solid_geometry.bounds

    assert (minx, miny) == (pytest.approx(0.0), pytest.approx(0.0))
    assert (maxx, maxy) == (pytest.approx(25.0), pytest.approx(25.0))


def test_the_pen_becomes_a_tool(parsed_plot, fc_app):
    assert list(parsed_plot.tools) == ["1"]
    assert parsed_plot.tools["1"]["tooldia"] == pytest.approx(
        float(fc_app.options["tools_mill_tooldia"])
    )


@pytest.mark.parametrize("option", GEOMETRY_OPTIONS)
def test_default_data_carries_the_shipped_option(parsed_plot, fc_app, option):
    assert parsed_plot.default_data[option[len("geometry_"):]] == fc_app.options[option]


def test_the_chosen_preprocessor_exists(fc_app):
    assert fc_app.options["geometry_ppname_g"] in fc_app.preprocessors


def test_the_source_file_is_kept(parsed_plot):
    kept = parsed_plot.source_file.splitlines()
    assert kept == [line for line in HPGL2_SAMPLE.splitlines()]
