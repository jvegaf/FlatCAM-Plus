"""Switching units is only allowed while the geometry is not in the way.

This is slice A of the unit toggle: the control exists, but it refuses to switch while the
project holds objects. Changing ``app_units`` alone would reinterpret every existing
coordinate by 25.4x, because conversion is not implemented yet, so the refusal is the
feature here — not an accident to be removed later without the conversion behind it.
"""

from flatcam_plus.appObjects.ObjectCollection import TreeItem


class _StubObject:
    def __init__(self, name, kind):
        self.kind = kind
        self.obj_options = {"name": name, "plot": True}


def _add_object(fc_app, kind="gerber"):
    model = fc_app.collection
    group = model.group_items[kind]
    index = model.item_index(group)
    row = group.child_count()
    model.beginInsertRows(index, row, row)
    TreeItem(None, model.icons[kind], _StubObject("stub_object", kind), group)
    model.endInsertRows()
    return group


def _remove_last_object(fc_app, group):
    model = fc_app.collection
    index = model.item_index(group)
    row = group.child_count() - 1
    model.beginRemoveRows(index, row, row)
    group.child_items.pop()
    model.endRemoveRows()


def test_units_toggle_round_trip_without_objects(fc_app):
    ui = fc_app.ui
    original_units = fc_app.app_units
    original_label = ui.units_label.text()

    try:
        assert ui._project_object_count() == 0, "the test project should start empty"

        assert ui.on_toggle_units() is True
        flipped = "IN" if str(original_units).upper() == "MM" else "MM"
        assert fc_app.app_units == flipped
        assert fc_app.options["units"] == flipped
        assert ui.units_label.text() == "[%s]" % flipped.lower()

        assert ui.on_toggle_units() is True
        assert fc_app.app_units == original_units
        assert ui.units_label.text() == original_label
    finally:
        fc_app.app_units = original_units
        fc_app.options["units"] = original_units
        fc_app.defaults["units"] = original_units
        ui.update_units_label()


def test_units_toggle_is_refused_while_the_project_holds_objects(fc_app):
    """The whole point of slice A: no silent 25.4x reinterpretation of live geometry."""
    ui = fc_app.ui
    original_units = fc_app.app_units
    original_label = ui.units_label.text()

    group = _add_object(fc_app)
    try:
        assert ui._project_object_count() == 1

        assert ui.on_toggle_units() is False
        assert fc_app.app_units == original_units, "units changed while objects were present"
        assert ui.units_label.text() == original_label
    finally:
        _remove_last_object(fc_app, group)
        fc_app.app_units = original_units
        fc_app.options["units"] = original_units
        fc_app.defaults["units"] = original_units
        ui.update_units_label()


def test_object_count_ignores_the_kind_groups(fc_app):
    """A fresh project holds six kind groups, and none of them is an object."""
    collection = fc_app.collection
    assert len(collection.group_items) == 6
    assert fc_app.ui._project_object_count() == 0
