"""G-code output: a preprocessor turning a job into machine commands.

Covers the manufacturing output domain without a display: the preprocessor registry, the
job settings it reads and the emitted G-code text.
"""

import pytest

from appObjects.CNCJobObject import CNCJobObject


@pytest.fixture()
def grbl_job(fc_app):
    job = CNCJobObject(name="t3_smoke_cnc", app=fc_app, units="MM", tooldia=0.2)
    job.pp_geometry_name = "GRBL_11"
    job.pp_geometry = fc_app.preprocessors["GRBL_11"]
    job.xy_end = (0.0, 0.0)
    job.x, job.y = 5.0, 5.0
    job.oldx, job.oldy = 0.0, 0.0
    # The G-code generator copies the source bounds and tool diameter into the job options
    # before it asks for a header (appObjects/GeometryObject.py:765 and :839), so a job built
    # by hand has to carry them too.
    job.obj_options.update({"xmin": 0.0, "ymin": 0.0, "xmax": 20.0, "ymax": 10.0, "tool_dia": 0.2})
    return job


def test_header_selects_metric_absolute_machine_state(grbl_job):
    header = grbl_job.doformat(grbl_job.pp_geometry.start_code)
    assert "G21" in header
    assert "G90" in header
    assert "GRBL" in header


def test_emits_a_rapid_move_to_travel_height(grbl_job):
    assert grbl_job.doformat(grbl_job.pp_geometry.lift_code, x=5.0, y=5.0) == "G00 Z0.1000\n"


def test_emits_a_linear_cut_move(grbl_job):
    assert grbl_job.doformat(grbl_job.pp_geometry.linear_code, x=5.0, y=5.0) == "G01 X5.0000 Y5.0000 F3.00\n"
