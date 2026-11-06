"""The project object tree must expose each object's kind as readable text.

Object rows are built as ``TreeItem(None, icon, obj, group)``, so their ``item_data``
is ``None``.  Anything that calls ``len()`` or indexes it blindly raises, which is why
the second column is covered here at model level.
"""

from PyQt6 import QtCore

import pytest

from flatcam_plus.appObjects.ObjectCollection import ObjectCollection, TreeItem

DISPLAY = QtCore.Qt.ItemDataRole.DisplayRole


@pytest.fixture(autouse=True)
def clean_collection(fc_app):
    """Put the shared project tree back after each test.

    These tests build stub rows by appending to the real group items, and the application is
    session-scoped: without this, every row they add stays in the tree for every later test file.
    """
    model = fc_app.collection
    before = {kind: group.child_count() for kind, group in model.group_items.items()}

    yield

    for kind, group in model.group_items.items():
        while group.child_count() > before[kind]:
            index = model.item_index(group)
            row = group.child_count() - 1
            model.beginRemoveRows(index, row, row)
            group.child_items.pop()
            model.endRemoveRows()


class _StubObject:
    """Minimal stand-in for a collection object row."""

    def __init__(self, name, kind):
        self.kind = kind
        self.obj_options = {"name": name, "plot": True}


def _row(model, kind, column=0):
    stub = _StubObject("%s_name" % kind, kind)
    item = TreeItem(None, None, stub, model.group_items[kind])
    return stub, model.createIndex(0, column, item)


def test_object_rows_have_two_columns(fc_app):
    _, index = _row(fc_app.collection, "gerber", column=0)
    assert fc_app.collection.columnCount() == ObjectCollection.COLUMN_COUNT == 2
    assert fc_app.collection.columnCount(index) == 2


def test_none_item_data_does_not_raise():
    item = TreeItem(None)
    assert item.column_count() == 2
    assert item.data(1) is None


def test_kind_column_returns_readable_kind_for_every_kind(fc_app):
    model = fc_app.collection
    for kind, title in ObjectCollection.groups:
        _, index = _row(model, kind, column=ObjectCollection.KIND_COLUMN)
        assert model.data(index, DISPLAY) == title


def test_name_column_still_returns_the_object_name(fc_app):
    stub, index = _row(fc_app.collection, "geometry", column=0)
    assert fc_app.collection.data(index, DISPLAY) == stub.obj_options["name"]


def test_out_of_range_column_returns_nothing(fc_app):
    _, index = _row(fc_app.collection, "excellon", column=7)
    assert fc_app.collection.data(index, DISPLAY) is None


def test_kind_column_is_not_editable(fc_app):
    model = fc_app.collection
    _, name_index = _row(model, "cncjob", column=0)
    _, kind_index = _row(model, "cncjob", column=ObjectCollection.KIND_COLUMN)

    name_flags = model.flags(name_index)
    kind_flags = model.flags(kind_index)

    assert name_flags & QtCore.Qt.ItemFlag.ItemIsEditable
    assert not (kind_flags & QtCore.Qt.ItemFlag.ItemIsEditable)


def test_editing_the_kind_column_never_renames_the_object(fc_app):
    model = fc_app.collection
    stub, kind_index = _row(model, "gerber", column=ObjectCollection.KIND_COLUMN)
    before = stub.obj_options["name"]

    model.setData(kind_index, "Something else", DISPLAY)

    assert stub.obj_options["name"] == before


def test_header_labels_the_two_columns(fc_app):
    model = fc_app.collection
    horizontal = QtCore.Qt.Orientation.Horizontal

    assert model.headerData(0, horizontal, DISPLAY) == "Object"
    assert model.headerData(ObjectCollection.KIND_COLUMN, horizontal, DISPLAY) == "Kind"


def test_child_rows_of_a_group_are_not_counted_on_the_kind_column(fc_app):
    model = fc_app.collection
    _, kind_index = _row(model, "geometry", column=ObjectCollection.KIND_COLUMN)
    assert model.rowCount(kind_index) == 0


def test_kind_column_uses_the_muted_token_and_the_name_column_does_not(fc_app):
    """The kind is annotation: it must not compete with the object name."""
    from flatcam_plus.appGUI.PanelStyles import modern_panel_colors

    foreground = QtCore.Qt.ItemDataRole.ForegroundRole
    model = fc_app.collection
    muted = modern_panel_colors(fc_app)["hint_strong"]

    _, name_index = _row(model, "gerber", column=0)
    _, kind_index = _row(model, "gerber", column=ObjectCollection.KIND_COLUMN)

    assert model.data(kind_index, foreground).color().name() == muted
    assert model.data(name_index, foreground).color().name() != muted
