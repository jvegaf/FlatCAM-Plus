"""Isolation: the minimum distance between geometry elements, and the worker that reads it.

``find_optim_mp`` feeds the "find optimal tool diameter" check, and it collects the solid
geometry of every aperture before measuring distances between the pieces. Aperture macros
can contribute a ``MultiPolygon`` as a single solid, which used to reach ``MultiPolygon()``
as a nested sequence and abort the check with
``"Sequences of multi-polygons are not valid arguments"``.

``find_optim_mp`` owns the trimming convention: it subtracts ``10 ** -decimals`` from the
measured distance. The single-process worker used to measure on its own and report the
untrimmed number, so the same button reported 2.0 through the worker and 1.99 through the
multiprocessing path for the same board. The worker now delegates to ``find_optim_mp``, and
the tests below drive its real ``job_thread`` closure to pin that it reports the trimmed
diameter and never converts a missing one.
"""

from types import SimpleNamespace

import numpy as np
import pytest
from shapely import MultiPolygon, Polygon, box

from flatcam_plus.appPlugins.ToolIsolation import ToolIsolation
from flatcam_plus.camlib import grace


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


def test_reports_a_layer_that_merges_into_one_polygon():
    # Two touching 1 mm squares merge into a single polygon, so there is no pair to
    # measure. The check must return the "one Polygon as geometry" report and no
    # distance, instead of dying inside `min()` on an empty dict. The message is the
    # caller's contract: it is emitted as-is and the caller stops before using the
    # distance, so a missing distance must never come back with an 'ok' status.
    msg, min_dist = ToolIsolation.find_optim_mp(
        aperture_storage(box(0, 0, 1, 1), box(1, 0, 2, 1)), 2
    )
    assert msg.startswith("[ERROR_NOTCL]")
    assert "one Polygon as geometry" in msg
    assert "no distances between geometry elements" in msg
    assert min_dist is None


def test_reports_a_layer_with_no_geometry_to_measure():
    # A layer that contributes no usable solid (here none at all) has no pair to
    # measure either. It used to borrow the one-Polygon report, which describes a layer
    # that does have a solid; the empty layer says what it is.
    msg, min_dist = ToolIsolation.find_optim_mp(aperture_storage(), 2)
    assert msg.startswith("[ERROR_NOTCL]")
    assert "no usable geometry to measure distances between" in msg
    assert min_dist is None


def test_reports_a_layer_with_a_single_solid():
    # One piece cannot be compared with anything: that is the one-Polygon report, and its
    # text is unchanged.
    msg, min_dist = ToolIsolation.find_optim_mp(aperture_storage(box(0, 0, 1, 1)), 2)
    assert msg.startswith("[ERROR_NOTCL]")
    assert "one Polygon as geometry" in msg
    assert "no distances between geometry elements" in msg
    assert min_dist is None


def test_ignores_invalid_solids():
    tolerance = Polygon([(0, 0), (1, 1), (0, 1), (1, 0)])  # self-intersecting bowtie
    msg, min_dist = ToolIsolation.find_optim_mp(
        aperture_storage(box(0, 0, 1, 1), tolerance, box(3, 0, 4, 1)), 2
    )
    assert msg == "ok"
    assert min_dist == pytest.approx(1.99)


def test_reports_progress_for_every_measured_pair():
    # The GUI worker drives its progress bar from `on_pair`, so this callback is the seam
    # the panel uses. Three pieces make three pairs, and the total arrives with each call.
    calls = []
    msg, min_dist = ToolIsolation.find_optim_mp(
        aperture_storage(box(0, 0, 1, 1), box(3, 0, 4, 1), box(6, 0, 7, 1)),
        2,
        on_pair=lambda processed, total: calls.append((processed, total)),
    )
    assert msg == "ok"
    assert min_dist == pytest.approx(1.99)
    assert [processed for processed, _ in calls] == [1, 2, 3]
    assert {total for _, total in calls} == {3}

    # The percentages the panel renders from these numbers start above 0 and reach 100.
    percentages = [int(np.interp(processed, [0, total], [0, 100])) for processed, total in calls]
    assert percentages == [33, 66, 100]


def test_aborts_before_measuring_the_pair_that_asks_for_it():
    # A user abort arrives between pairs; no distance is handed back afterwards.
    pairs = []
    result = None

    with pytest.raises(grace):
        result = ToolIsolation.find_optim_mp(
            aperture_storage(box(0, 0, 1, 1), box(3, 0, 4, 1), box(6, 0, 7, 1)),
            2,
            on_pair=lambda processed, total: pairs.append(processed),
            abort_check=lambda: len(pairs) == 1,
        )

    assert result is None
    assert pairs == [1]


def test_aborts_during_collection_before_measuring_anything():
    # The GUIs check the abort flag while the solids are still being collected, so an abort
    # requested up front must leave before the first distance is measured.
    pairs = []
    result = None

    with pytest.raises(grace):
        result = ToolIsolation.find_optim_mp(
            aperture_storage(box(0, 0, 1, 1), box(3, 0, 4, 1), box(6, 0, 7, 1)),
            2,
            on_pair=lambda processed, total: pairs.append(processed),
            abort_check=lambda: True,
        )

    assert result is None
    assert pairs == []


class Recorder:
    """Collects what the worker emits: the inform messages and the signal values."""

    def __init__(self):
        self.messages = []

    def emit(self, message):
        self.messages.append(message)


class ErrorLog:
    """The app log, where the worker's own ``except`` swallows an exception."""

    def __init__(self):
        self.errors = []

    def error(self, message):
        self.errors.append(message)


class ProcContainer:
    """The ``with app.proc_container.new(...)`` block and the progress text it shows."""

    def __init__(self):
        self.texts = []

    def new(self, *args, **kwargs):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def update_view_text(self, text):
        self.texts.append(text)


class WorkerTask:
    """Runs the job the app would hand to its worker thread, in place."""

    def __init__(self):
        self.results = []

    def emit(self, job):
        self.results.append(job['fcn'](*job['params']))


class Collection:
    """The three lookups ``_resolve_current_gerber_object`` makes, all on one layer."""

    def __init__(self, layer):
        self.layer = layer

    def get_by_name(self, name):
        return self.layer

    def get_active(self):
        return self.layer

    def get_list(self):
        return [self.layer]


def isolation_worker(*solids):
    """Build a ``ToolIsolation`` whose real worker closure runs against a duck-typed app.

    ``find_safe_tooldia_worker`` reaches the app for the collection (through
    ``_resolve_current_gerber_object``), the inform emitter, the progress container, the abort
    flag, the units, ``dec_format``, the log and the worker task, and it reads ``ui``,
    ``decimals`` and ``optimal_found_sig`` from the tool. Nothing of the measurement is
    mocked: the solids below are the layer's aperture geometry.
    """
    layer = SimpleNamespace(
        kind='gerber',
        obj_options={'name': 'layer'},
        tools={10: {'geometry': [{'solid': solid} for solid in solids]}},
    )
    app = SimpleNamespace(
        inform=Recorder(),
        proc_container=ProcContainer(),
        worker_task=WorkerTask(),
        log=ErrorLog(),
        collection=Collection(layer),
        abort_flag=False,
        app_units='MM',
        # The worker reads the rounding convention from the app; this mirrors
        # ``App.dec_format``, which formats and returns a float.
        dec_format=lambda value, decimals: float('%.*f' % (decimals, float(value))),
    )

    # ``AppTool`` is a QWidget, so an uninitialised instance raises on any attribute it does
    # not hold itself: every attribute the worker reads has to be set here.
    tool = ToolIsolation.__new__(ToolIsolation)
    tool.app = app
    tool.ui = SimpleNamespace(object_combo=SimpleNamespace(get_value=lambda: 'layer'))
    tool.decimals = 2
    tool.safe_tooldia = None
    tool.optimal_found_sig = Recorder()
    return tool, app


def test_worker_reports_the_same_trimmed_diameter_as_the_multiprocessing_path():
    # Two 1 mm squares, 2 mm apart along X: the same layer the multiprocessing path reports
    # as 1.99. The worker used to measure on its own and report the untrimmed 2.0, so one
    # button gave two different diameters depending on which path ran. It now runs
    # ``find_optim_mp``, which owns the trimming convention.
    tool, app = isolation_worker(box(0, 0, 1, 1), box(3, 0, 4, 1))

    tool.find_safe_tooldia_worker()

    assert tool.safe_tooldia == 1.99
    assert tool.optimal_found_sig.messages == [1.99]
    assert app.inform.messages == [
        "Checking tools for validity.",
        "[success] Optimal tool diameter found: 1.99 mm",
    ]
    assert app.log.errors == []


def test_worker_stops_on_a_layer_with_no_piece_without_converting_none():
    # A layer that contributes no usable solid hands back no distance at all. The worker has
    # to emit the report and return 'fail' before ``float(min_dist)``, which would turn None
    # into a TypeError the worker's own ``except`` swallows, leaving no diameter and no
    # message behind.
    tool, app = isolation_worker()

    tool.find_safe_tooldia_worker()

    assert app.worker_task.results == ['fail']
    assert tool.safe_tooldia is None
    assert tool.optimal_found_sig.messages == []
    assert app.inform.messages[0] == "Checking tools for validity."
    assert app.inform.messages[1].startswith("[ERROR_NOTCL]")
    assert "no usable geometry" in app.inform.messages[1]
    assert app.log.errors == []
