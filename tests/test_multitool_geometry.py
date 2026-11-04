"""G-code from the legacy multitool geometry generator.

``CNCjob.generate_from_multitool_geometry`` takes its end-move and motion parameters from
the application defaults when a caller does not override them, so these tests drive a real
job through it and assert the emitted G-code. A default the application never defines stops
the generator before any G-code exists, which the first assertion would notice only as a
missing cut line, so the generator's return value is checked too.
"""

from shapely import LineString

from appObjects.CNCJobObject import CNCJobObject

SOURCE_BOUNDS = {"xmin": 0.0, "ymin": 0.0, "xmax": 20.0, "ymax": 10.0}
TOOL_DIAMETER = 0.2
PATH = LineString([(0.0, 0.0), (10.0, 5.0)])


def _job(fc_app):
    job = CNCJobObject(name="multitool_geometry", app=fc_app, units="MM", tooldia=TOOL_DIAMETER)
    # The header reads the source bounds from the job options, exactly as the Geometry
    # exporter copies them before asking for G-code.
    job.obj_options.update(SOURCE_BOUNDS)
    job.obj_options["tool_dia"] = TOOL_DIAMETER
    return job


def _generate(job, **overrides):
    kwargs = {
        "tooldia": TOOL_DIAMETER,
        "z_cut": -0.1,
        "z_move": 2.0,
    }
    kwargs.update(overrides)
    return job.generate_from_multitool_geometry([PATH], **kwargs)


def test_end_move_parameters_come_from_the_geometry_defaults(fc_app):
    job = _job(fc_app)

    gcode = _generate(
        job,
        feedrate=120.0,
        feedrate_z=60.0,
        feedrate_rapid=1500.0,
        depthpercut=0.8,
        toolchangez=15.0,
        toolchangexy="0.0, 0.0",
    )

    assert isinstance(gcode, str)
    assert gcode != "fail"
    assert "G01 X10.0000 Y5.0000" in gcode
    # Dwell time, start Z, end Z and the end X,Y are the four defaults the generator used to
    # read from options that did not exist; the header reports all of them back.
    assert "(Z Start: None mm)" in gcode
    assert "(Z End: 15.0 mm)" in gcode
    assert "(X,Y End: None mm)" in gcode


def test_motion_parameters_come_from_the_geometry_defaults(fc_app):
    job = _job(fc_app)

    gcode = _generate(job)

    assert gcode != "fail"
    assert "(Feedrate_XY: 120 mm/min)" in gcode
    assert "G01 X10.0000 Y5.0000" in gcode


def test_the_spindle_speed_may_be_left_at_its_default(fc_app):
    """The cut depth and travel Z are required; the spindle speed is not.

    ``spindlespeed`` defaulted to ``None`` while the line that stored it compared it to ``0``
    and then called ``int()``, so the method raised ``TypeError`` before reading a single
    option. Nothing else about the signature changed: a job that asks for a cut without
    mentioning the spindle must still produce G-code.
    """

    job = _job(fc_app)

    gcode = job.generate_from_multitool_geometry(
        [PATH], tooldia=TOOL_DIAMETER, z_cut=-0.1, z_move=2.0
    )

    assert gcode != "fail"
    assert "G01 X10.0000 Y5.0000" in gcode
