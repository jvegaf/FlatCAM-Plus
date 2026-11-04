"""Unit tests for the Milling plugin Excellon geometry builder.

These tests exercise ``ToolMilling._build_milled_tools`` without a Qt
application or a display: the polygon-clearing step is replaced with a fake
that returns the buffered input shape unchanged.
"""

import importlib

import pytest
from shapely.geometry import Point

milling = importlib.import_module("appPlugins.ToolMilling")


class _FakeLog:
    def debug(self, *args, **kwargs):
        pass


class _FakeProcContainer:
    def update_view_text(self, *args, **kwargs):
        pass


class _FakeApp:
    options = {
        "geometry_circle_steps": 64,
        "geometry_seg_x": 0,
        "geometry_seg_y": 0,
    }
    abort_flag = False
    log = _FakeLog()
    proc_container = _FakeProcContainer()


class _FakeResult:
    def __init__(self, geometry):
        self._geometry = geometry

    def get_objects(self):
        return [self._geometry]


class _FakeSelf:
    """Minimal stand-in for ToolMilling used by the extracted builder."""

    app = _FakeApp()

    def __init__(self):
        self.cleared = []

    def clear_polygon_seed(self, polygon, **kwargs):
        self.cleared.append((polygon, kwargs))
        return _FakeResult(polygon)


def _tool(milling_type="both", mill_dia=0.2, offset_type=0, offset_value=0.0):
    return {
        "tooldia": 0.8,
        "data": {
            "tools_mill_milling_type": milling_type,
            "tools_mill_milling_dia": mill_dia,
            "tools_mill_milling_overlap": 50,
            "tools_mill_milling_connect": True,
            "tools_mill_offset_type": offset_type,
            "tools_mill_offset_value": offset_value,
        },
        "drills": [Point(0, 0), Point(1, 1)],
        "slots": [((0, 0), (1, 1))],
    }


def test_build_milled_tools_both_includes_drills_and_slots():
    fake_self = _FakeSelf()

    result = milling.ToolMilling._build_milled_tools(
        fake_self, {1: _tool(milling_type="both")}
    )

    assert set(result) == {1}
    tool = result[1]
    assert tool["tooldia"] == pytest.approx(0.2)
    assert tool["data"]["tools_mill_tooldia"] == pytest.approx(0.2)
    assert tool["data"]["seg_x"] == 0
    assert tool["data"]["seg_y"] == 0
    # Two drills plus one slot.
    assert len(tool["solid_geometry"]) == 3
    assert len(fake_self.cleared) == 3


def test_build_milled_tools_slots_only_ignores_drills():
    fake_self = _FakeSelf()

    result = milling.ToolMilling._build_milled_tools(
        fake_self, {1: _tool(milling_type="slots")}
    )

    assert len(result[1]["solid_geometry"]) == 1
    assert len(fake_self.cleared) == 1
    buffered_slot = fake_self.cleared[0][0]
    # Path offset: tooldia / 2 == 0.4
    minx, miny, maxx, maxy = buffered_slot.bounds
    assert minx == pytest.approx(-0.4, abs=1e-6)
    assert miny == pytest.approx(-0.4, abs=1e-6)
    assert maxx == pytest.approx(1.4, abs=1e-6)
    assert maxy == pytest.approx(1.4, abs=1e-6)


def test_build_milled_tools_custom_offset_is_applied():
    fake_self = _FakeSelf()

    result = milling.ToolMilling._build_milled_tools(
        fake_self, {1: _tool(milling_type="drills", offset_type=3, offset_value=0.1)}
    )

    assert len(result[1]["solid_geometry"]) == 2
    # tooldia / 2 + custom offset == 0.4 + 0.1
    buffered_drill = fake_self.cleared[0][0]
    minx, miny, maxx, maxy = buffered_drill.bounds
    assert minx == pytest.approx(-0.5, abs=1e-6)
    assert miny == pytest.approx(-0.5, abs=1e-6)
    assert maxx == pytest.approx(0.5, abs=1e-6)
    assert maxy == pytest.approx(0.5, abs=1e-6)


def test_build_milled_tools_returns_empty_when_nothing_to_mill():
    fake_self = _FakeSelf()
    tool = _tool(milling_type="drills")
    tool["drills"] = []

    result = milling.ToolMilling._build_milled_tools(fake_self, {1: tool})

    assert result == {}
    assert fake_self.cleared == []
