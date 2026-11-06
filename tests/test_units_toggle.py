"""Changing units converts the project, and never leaves it half converted.

Slice A refused to switch while objects existed. Now the switch asks for confirmation and converts
everything; what replaces the old refusal is an all-or-nothing guarantee, because a single object
that silently refuses conversion would leave a project half in millimetres while the application
reports inches.
"""

import pytest
from shapely.geometry import box

from flatcam_plus.appCommon import units
from flatcam_plus.appObjects.ObjectCollection import TreeItem


class _ConvertibleObject:
    """Stands in for a project object, with the parts the toggle actually touches."""

    def __init__(self, name, kind="gerber", refuses=False, side=25.4):
        self.kind = kind
        self.refuses = refuses
        self.obj_options = {"name": name, "plot": True}
        self.units = "MM"
        self._box = box(0.0, 0.0, side, side)
        self.solid_geometry = [self._box]

    def convert_units(self, target):
        if self.refuses:
            return
        factor = units.conversion_factor(self.units, target)
        from shapely import transform as rebase

        self._box = rebase(self._box, lambda coords: coords * factor)
        self.solid_geometry = [self._box]
        self.units = target

    def bounds(self):
        return self.solid_geometry[0].bounds


def _insert(fc_app, obj, kind=None):
    model = fc_app.collection
    group = model.group_items[kind or obj.kind]
    index = model.item_index(group)
    row = group.child_count()
    model.beginInsertRows(index, row, row)
    TreeItem(None, model.icons[kind or obj.kind], obj, group)
    model.endInsertRows()
    return group


def _remove_last(fc_app, group):
    model = fc_app.collection
    index = model.item_index(group)
    row = group.child_count() - 1
    model.beginRemoveRows(index, row, row)
    group.child_items.pop()
    model.endRemoveRows()


@pytest.fixture
def restore_units(fc_app):
    original = fc_app.app_units
    yield
    fc_app.app_units = original
    fc_app.options["units"] = original
    fc_app.defaults["units"] = original
    fc_app.ui.update_units_label()


def test_units_toggle_round_trip_without_objects(fc_app, restore_units):
    ui = fc_app.ui
    assert ui._project_object_count() == 0

    assert ui.on_toggle_units() is True
    assert fc_app.app_units == "IN"
    assert fc_app.options["units"] == "IN"
    assert ui.units_label.text() == "[in]"

    assert ui.on_toggle_units() is True
    assert fc_app.app_units == "MM"
    assert ui.units_label.text() == "[mm]"


def test_object_count_ignores_the_kind_groups(fc_app):
    """A fresh project holds six kind groups, and none of them is an object."""
    assert len(fc_app.collection.group_items) == 6
    assert fc_app.ui._project_object_count() == 0


def test_declining_the_confirmation_changes_nothing(fc_app, restore_units, monkeypatch):
    ui = fc_app.ui
    obj = _ConvertibleObject("top_copper")
    group = _insert(fc_app, obj)

    try:
        monkeypatch.setattr(ui, "_confirm_unit_conversion", lambda *a, **k: False)

        assert ui.on_toggle_units() is False
        assert fc_app.app_units == "MM"
        assert obj.units == "MM"
        assert obj.solid_geometry[0].bounds == pytest.approx((0.0, 0.0, 25.4, 25.4))
    finally:
        _remove_last(fc_app, group)


def test_accepting_the_confirmation_converts_the_object(fc_app, restore_units, monkeypatch):
    ui = fc_app.ui
    obj = _ConvertibleObject("top_copper")
    group = _insert(fc_app, obj)

    try:
        monkeypatch.setattr(ui, "_confirm_unit_conversion", lambda *a, **k: True)

        assert ui.on_toggle_units() is True
        assert fc_app.app_units == "IN"
        assert obj.units == "IN"
        assert obj.solid_geometry[0].bounds == pytest.approx((0.0, 0.0, 1.0, 1.0))
        # The cached bounds other panels read must agree with the new geometry.
        assert obj.obj_options["xmax"] == pytest.approx(1.0)
    finally:
        _remove_last(fc_app, group)


def test_a_refusing_object_aborts_the_whole_conversion(fc_app, restore_units, monkeypatch):
    """No half-converted project, and the application must not claim the new unit."""
    ui = fc_app.ui
    willing = _ConvertibleObject("top_copper")
    refusing = _ConvertibleObject("declared_units", kind="excellon", refuses=True)

    group_a = _insert(fc_app, willing)
    group_b = _insert(fc_app, refusing)

    try:
        monkeypatch.setattr(ui, "_confirm_unit_conversion", lambda *a, **k: True)

        assert ui.on_toggle_units() is False
        assert fc_app.app_units == "MM", "the application reported a unit it is not in"
        assert willing.units == "MM", "the converted object was not rolled back"
        assert willing.solid_geometry[0].bounds == pytest.approx((0.0, 0.0, 25.4, 25.4))
        assert ui.units_label.text() == "[mm]"
    finally:
        _remove_last(fc_app, group_b)
        _remove_last(fc_app, group_a)


class _CapturedDialog:
    """Stands in for the modal, recording what the user would have been told."""

    last_informative = None

    def __init__(self, *args, **kwargs):
        self._first = None

    def addButton(self, *args, **kwargs):
        token = object()
        if self._first is None:
            self._first = token
        return token

    def exec(self):
        return 0

    def clickedButton(self):
        # Decline, so nothing is converted and the call is pure observation.
        return None

    def setInformativeText(self, text):
        _CapturedDialog.last_informative = text

    def __getattr__(self, name):
        return lambda *a, **k: None


def test_the_confirmation_warns_about_cnc_jobs(fc_app, restore_units, monkeypatch):
    """Risky part surfaced where the decision is made, not in a log afterwards."""
    from flatcam_plus.appGUI import MainGUI as main_gui

    ui = fc_app.ui
    plain = _ConvertibleObject("top_copper")
    cnc = _ConvertibleObject("iso_top_cnc", kind="cncjob")

    group_a = _insert(fc_app, plain)
    group_b = _insert(fc_app, cnc)

    try:
        monkeypatch.setattr(main_gui, "FCMessageBox", _CapturedDialog)

        assert ui.on_toggle_units() is False

        text = _CapturedDialog.last_informative
        assert text is not None
        assert "CNC job" in text, "no warning about the lossy G-code rewrite: %r" % (text,)
    finally:
        _remove_last(fc_app, group_b)
        _remove_last(fc_app, group_a)


def test_the_confirmation_has_no_cnc_warning_without_cnc_jobs(fc_app, restore_units, monkeypatch):
    from flatcam_plus.appGUI import MainGUI as main_gui

    ui = fc_app.ui
    plain = _ConvertibleObject("top_copper")
    group = _insert(fc_app, plain)

    try:
        monkeypatch.setattr(main_gui, "FCMessageBox", _CapturedDialog)

        assert ui.on_toggle_units() is False

        text = _CapturedDialog.last_informative
        assert text is not None
        assert "CNC job" not in text, "the warning appeared without any CNC job: %r" % (text,)
    finally:
        _remove_last(fc_app, group)
